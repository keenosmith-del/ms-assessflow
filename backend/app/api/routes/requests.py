from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import (
    AccessRequest,
    Application,
    Assessment,
    AuditEvent,
    User,
    Comment,
    Decision,
    Fulfilment,
)
from app.schemas.contracts import (
    RequestInput,
    Clarification,
    DecisionInput,
    CommentInput,
    FulfilInput,
)
from app.security.auth import current_user, require_role
from app.integrations.microsoft.providers import PrivacyProvider
from app.services.workflow import owned_request, assess, transition, audit, payload_hash, decide

router = APIRouter(prefix="/v1", tags=["requests"])
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]


def scope(statement, user):
    if user.role in {"admin", "operator"}:
        return statement
    if user.role == "approver":
        return statement.where(
            or_(
                AccessRequest.requester_id == user.id,
                AccessRequest.requester_id.in_(select(User.id).where(User.manager_id == user.id)),
            )
        )
    return statement.where(AccessRequest.requester_id == user.id)


def summary(item):
    return {
        "id": item.id,
        "requester_id": item.requester_id,
        "application_id": item.application_id,
        "justification": item.justification,
        "access_level": item.access_level,
        "status": item.status,
        "revision": item.revision,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


@router.get("/requests")
def list_requests(
    db: DB,
    user: Actor,
    q: str = Query("", max_length=120),
    status: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    statement = scope(select(AccessRequest), user)
    if status:
        statement = statement.where(AccessRequest.status == status)
    if q:
        statement = statement.where(
            or_(
                AccessRequest.id.contains(q, autoescape=True),
                AccessRequest.application_id.contains(q, autoescape=True),
                AccessRequest.justification.contains(q, autoescape=True),
            )
        )
    items = db.scalars(
        statement.order_by(AccessRequest.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return {"items": [summary(x) for x in items], "offset": offset, "limit": limit}


@router.post("/requests", status_code=201)
def create_request(
    payload: RequestInput,
    request: Request,
    db: DB,
    user: Actor,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=100)],
) -> dict:
    # Serialize creations for this identity in PostgreSQL, then enforce key uniqueness in DB.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    digest = payload_hash(payload.model_dump())
    existing = db.scalar(
        select(AccessRequest).where(
            AccessRequest.requester_id == user.id, AccessRequest.idempotency_key == idempotency_key
        )
    )
    if existing:
        if existing.payload_hash != digest:
            raise HTTPException(409, "Idempotency key was used for a different payload")
        return summary(existing)
    application = db.get(Application, payload.application_id)
    if not application:
        raise HTTPException(422, "Unknown application")
    if payload.access_level not in application.levels:
        raise HTTPException(422, "Unsupported entitlement")
    duplicate = db.scalar(
        select(AccessRequest.id).where(
            AccessRequest.requester_id == user.id,
            AccessRequest.payload_hash == digest,
            AccessRequest.status.not_in(["cancelled", "rejected", "fulfilled"]),
        )
    )
    if duplicate:
        raise HTTPException(409, "An identical active request already exists")
    values = payload.model_dump()
    values["justification"] = PrivacyProvider().redact(values["justification"]).text
    item = AccessRequest(
        **values, requester_id=user.id, idempotency_key=idempotency_key, payload_hash=digest
    )
    db.add(item)
    db.flush()
    audit(db, user.id, "request_created", item.id, correlation=request.state.correlation_id)
    assess(db, user, item, request.state.correlation_id)
    return summary(item)


@router.get("/requests/{request_id}")
def detail(request_id: str, db: DB, user: Actor) -> dict:
    item = owned_request(db, user, request_id)
    output = summary(item)
    assessments = db.scalars(
        select(Assessment)
        .where(Assessment.request_id == item.id)
        .order_by(Assessment.created_at.desc())
    ).all()
    output["assessments"] = [x.result for x in assessments]
    output["timeline"] = [
        {
            "id": x.id,
            "actor": x.actor_id,
            "action": x.action,
            "detail": x.detail,
            "at": x.created_at.isoformat(),
        }
        for x in db.scalars(
            select(AuditEvent)
            .where(AuditEvent.request_id == item.id)
            .order_by(AuditEvent.created_at)
        )
    ]
    output["comments"] = [
        {"actor": x.actor_id, "body": x.body, "at": x.created_at.isoformat()}
        for x in db.scalars(
            select(Comment).where(Comment.request_id == item.id).order_by(Comment.created_at)
        )
    ]
    decision = db.get(Decision, item.id)
    output["decision"] = (
        {"actor": decision.actor_id, "decision": decision.decision, "reason": decision.reason}
        if decision
        else None
    )
    task = db.get(Fulfilment, item.id)
    output["fulfilment"] = {"status": task.status, "reference": task.reference} if task else None
    output["next_step"] = {
        "awaiting_information": "Requester must supply missing details",
        "pending_approval": "Assigned manager must record a decision",
        "provisioning_pending": "Service operator must record verified fulfilment",
    }.get(item.status, "No employee action required")
    return output


@router.patch("/requests/{request_id}/information")
def clarify(request_id: str, payload: Clarification, request: Request, db: DB, user: Actor) -> dict:
    item = owned_request(db, user, request_id, lock=True)
    if item.requester_id != user.id:
        raise HTTPException(403, "Only the requester may supply clarification")
    if item.status != "awaiting_information":
        raise HTTPException(409, "Request is not awaiting information")
    item.justification = PrivacyProvider().redact(payload.justification).text
    assess(db, user, item, request.state.correlation_id)
    return summary(item)


@router.post("/requests/{request_id}/cancel")
def cancel(request_id: str, request: Request, db: DB, user: Actor) -> dict:
    item = owned_request(db, user, request_id, lock=True)
    if item.requester_id != user.id and user.role != "admin":
        raise HTTPException(403, "Only requester or administrator may cancel")
    transition(db, item, "cancelled", user.id, request.state.correlation_id)
    return summary(item)


@router.post("/requests/{request_id}/comments", status_code=201)
def comment(request_id: str, payload: CommentInput, request: Request, db: DB, user: Actor) -> dict:
    item = owned_request(db, user, request_id)
    body = PrivacyProvider().redact(payload.body).text
    db.add(Comment(request_id=item.id, actor_id=user.id, body=body))
    audit(db, user.id, "comment_added", item.id, correlation=request.state.correlation_id)
    return {"body": body}


@router.post("/requests/{request_id}/decision")
def decision(
    request_id: str, payload: DecisionInput, request: Request, db: DB, user: Actor
) -> dict:
    item = owned_request(db, user, request_id, lock=True)
    return summary(decide(db, user, item, payload, request.state.correlation_id))


@router.get("/approvals")
def approvals(db: DB, user: Actor) -> dict:
    require_role(user, "approver", "admin")
    statement = scope(
        select(AccessRequest).where(
            AccessRequest.status == "pending_approval", AccessRequest.requester_id != user.id
        ),
        user,
    )
    return {
        "items": [
            summary(x) for x in db.scalars(statement.order_by(AccessRequest.created_at).limit(100))
        ]
    }


@router.post("/requests/{request_id}/fulfil")
def fulfil(request_id: str, payload: FulfilInput, request: Request, db: DB, user: Actor) -> dict:
    require_role(user, "operator", "admin")
    item = owned_request(db, user, request_id, lock=True)
    task = db.get(Fulfilment, item.id)
    if not task or not db.get(Decision, item.id):
        raise HTTPException(409, "Approved fulfilment task required")
    transition(db, item, "fulfilled", user.id, request.state.correlation_id)
    task.status = "completed"
    task.reference = PrivacyProvider().redact(payload.reference).text
    audit(
        db,
        user.id,
        "fulfilment_recorded",
        item.id,
        {"reference": task.reference},
        request.state.correlation_id,
    )
    return summary(item)
