import hashlib
import json
from datetime import timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select
from app.models.entities import (
    AccessRequest,
    Assessment,
    Evidence,
    AuditEvent,
    Decision,
    Fulfilment,
    Workflow,
    User,
    now,
)
from app.security.auth import require_role
from app.agents.assessment import analyse
from app.integrations.microsoft.providers import PrivacyProvider

TRANSITIONS = {
    "submitted": {"under_assessment", "cancelled"},
    "under_assessment": {"awaiting_information", "pending_approval", "cancelled"},
    "awaiting_information": {"under_assessment", "cancelled"},
    "pending_approval": {"approved", "rejected", "cancelled"},
    "approved": {"provisioning_pending"},
    "provisioning_pending": {"fulfilled"},
    "rejected": set(),
    "fulfilled": set(),
    "cancelled": set(),
}


def audit(db, actor, action, request_id=None, detail=None, correlation="system"):
    db.add(
        AuditEvent(
            actor_id=actor,
            action=action,
            request_id=request_id,
            detail=detail or {},
            correlation_id=correlation,
        )
    )


def transition(db, item, target, actor, correlation):
    if target not in TRANSITIONS[item.status]:
        raise HTTPException(409, f"Invalid transition from {item.status} to {target}")
    old = item.status
    item.status = target
    db.flush()
    audit(db, actor, "state_changed", item.id, {"from": old, "to": target}, correlation)


def payload_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def owned_request(db, user, request_id, lock=False):
    statement = select(AccessRequest).where(AccessRequest.id == request_id)
    if lock:
        statement = statement.with_for_update()
    item = db.scalar(statement)
    owner = db.get(User, item.requester_id) if item else None
    if not item or not (
        item.requester_id == user.id
        or user.role in {"admin", "operator"}
        or (user.role == "approver" and owner.manager_id == user.id)
    ):
        raise HTTPException(404, "Request not found")
    return item


def assess(db, user, item, correlation):
    transition(db, item, "under_assessment", user.id, correlation)
    data = analyse(db, user, item)
    record = Assessment(
        request_id=item.id,
        result=data,
        provider=data["provider"],
        trace_id=data["trace_id"],
        latency_ms=data["latency_ms"],
    )
    db.add(record)
    db.flush()
    for citation in data["output"]["citations"]:
        db.add(
            Evidence(
                assessment_id=record.id,
                policy_version_id=citation["version_id"],
                chunk_index=citation["chunk_index"],
                quote=citation["quote"],
            )
        )
    target = "awaiting_information" if data["output"]["missing_fields"] else "pending_approval"
    transition(db, item, target, user.id, correlation)
    audit(
        db,
        user.id,
        "assessment_completed",
        item.id,
        {"provider": data["provider"], "trace_id": data["trace_id"]},
        correlation,
    )
    if target == "pending_approval":
        workflow = db.get(Workflow, item.id)
        if not workflow:
            db.add(
                Workflow(
                    request_id=item.id, status="local_pending", expires_at=now() + timedelta(days=3)
                )
            )
    return data


def decide(db, user, item, payload, correlation):
    require_role(user, "approver", "admin")
    if item.requester_id == user.id:
        raise HTTPException(403, "Self approval is forbidden")
    owner = db.get(User, item.requester_id)
    if user.id != owner.manager_id and user.role != "admin":
        raise HTTPException(403, "Not an assigned approver")
    existing = db.get(Decision, item.id)
    if existing:
        if (
            existing.actor_id == user.id
            and existing.decision == payload.decision
            and existing.reason == PrivacyProvider().redact(payload.reason).text
        ):
            return item
        raise HTTPException(409, "A decision already exists")
    workflow = db.get(Workflow, item.id)
    if workflow and workflow.expires_at.replace(tzinfo=timezone.utc) < now():
        raise HTTPException(409, "Approval workflow expired; administrator renewal required")
    transition(db, item, payload.decision, user.id, correlation)
    db.add(
        Decision(
            request_id=item.id,
            actor_id=user.id,
            decision=payload.decision,
            reason=PrivacyProvider().redact(payload.reason).text,
        )
    )
    workflow = db.get(Workflow, item.id)
    if workflow:
        workflow.status = "completed"
    if payload.decision == "approved":
        db.add(Fulfilment(request_id=item.id, status="pending"))
        transition(db, item, "provisioning_pending", user.id, correlation)
    return item
