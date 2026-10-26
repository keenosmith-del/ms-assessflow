import hashlib
import hmac
import time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select
from app.api.routes.requests import DB, Actor, scope
from app.models.entities import (
    Application,
    User,
    Policy,
    AccessRequest,
    AuditEvent,
    Workflow,
    IntegrationEvent,
    Assessment,
)
from app.schemas.contracts import PolicyInput, RequestInput, CallbackInput, DecisionInput
from app.services.policies import permitted, latest, retrieve, ingest
from app.services.workflow import audit, owned_request, decide
from app.agents.assessment import analyse
from app.security.auth import require_role
from app.core.config import settings
from app.integrations.microsoft.providers import GraphProvider

router = APIRouter(prefix="/v1", tags=["operations"])


@router.get("/session")
def session(user: Actor) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "department": user.department,
        "mode": settings().assessflow_mode,
    }


@router.get("/applications")
def applications(db: DB, user: Actor) -> dict:
    return {
        "items": [
            {"id": x.id, "name": x.name, "levels": x.levels}
            for x in db.scalars(select(Application))
        ]
    }


@router.get("/policies")
def policies(db: DB, user: Actor) -> dict:
    result = []
    for policy in db.scalars(select(Policy).order_by(Policy.title)):
        if permitted(user, policy):
            version = latest(db, policy.id)
            result.append(
                {
                    "id": policy.id,
                    "title": policy.title,
                    "application_id": policy.application_id,
                    "department": policy.department,
                    "version": version.version,
                    "version_id": version.id,
                    "content": version.content,
                    "chunks": version.chunks,
                    "expires_at": version.expires_at,
                    "digest": version.digest,
                }
            )
    return {"items": result}


@router.get("/policies/search")
def search(db: DB, user: Actor, q: str = Query("", max_length=500)) -> dict:
    return {
        "items": retrieve(db, user, q),
        "provider": "azure-ai-search" if settings().assessflow_mode == "azure" else "local-keyword",
    }


@router.get("/policies/{policy_id}/versions")
def policy_versions(policy_id: str, db: DB, user: Actor) -> dict:
    from app.models.entities import PolicyVersion

    policy = db.get(Policy, policy_id)
    if not policy or not permitted(user, policy):
        raise HTTPException(404, "Policy not found")
    return {
        "items": [
            {
                "id": x.id,
                "version": x.version,
                "content": x.content,
                "digest": x.digest,
                "expires_at": x.expires_at,
            }
            for x in db.scalars(
                select(PolicyVersion)
                .where(PolicyVersion.policy_id == policy.id)
                .order_by(PolicyVersion.version.desc())
            )
        ]
    }


@router.post("/policies", status_code=201)
def upload_policy(payload: PolicyInput, request: Request, db: DB, user: Actor) -> dict:
    require_role(user, "admin")
    if not db.get(Application, payload.application_id):
        raise HTTPException(422, "Unknown application")
    policy, version = ingest(db, payload)
    audit(
        db,
        user.id,
        "policy_version_created",
        detail={"policy": policy.id, "version": version.version},
        correlation=request.state.correlation_id,
    )
    return {"id": policy.id, "version": version.version}


@router.post("/agent/assess")
def agent_assess(payload: RequestInput, db: DB, user: Actor) -> dict:
    # Stateless diagnostic endpoint cannot create a request or grant permissions.
    require_role(user, "admin", "approver")
    return analyse(db, user, payload)


@router.get("/audit")
def audit_events(
    db: DB,
    user: Actor,
    request_id: str = "",
    actor: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    require_role(user, "admin", "operator")
    statement = select(AuditEvent)
    if request_id:
        statement = statement.where(AuditEvent.request_id == request_id)
    if actor:
        statement = statement.where(AuditEvent.actor_id == actor)
    items = db.scalars(statement.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit))
    return {
        "items": [
            {
                "id": x.id,
                "request_id": x.request_id,
                "actor": x.actor_id,
                "action": x.action,
                "detail": x.detail,
                "at": x.created_at.isoformat(),
                "correlation_id": x.correlation_id,
            }
            for x in items
        ],
        "offset": offset,
        "limit": limit,
    }


@router.get("/metrics")
def metrics(db: DB, user: Actor) -> dict:
    items = db.scalars(scope(select(AccessRequest), user)).all()
    counts = {}
    elapsed = []
    exceptions = 0
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
        if item.status == "fulfilled":
            elapsed.append((item.updated_at - item.created_at).total_seconds())
        assessment = db.scalar(
            select(Assessment)
            .where(Assessment.request_id == item.id)
            .order_by(Assessment.created_at.desc())
            .limit(1)
        )
        if (
            assessment
            and assessment.result["output"]["recommendation"] == "manual_review"
            and item.status not in {"fulfilled", "rejected", "cancelled"}
        ):
            exceptions += 1
    return {
        "total": len(items),
        "counts": counts,
        "exceptions": exceptions,
        "average_processing_seconds": round(sum(elapsed) / len(elapsed), 1) if elapsed else None,
        "ai_evaluation": {
            "live_runs": None,
            "status": "Run offline evaluation CLI; live evaluation not verified",
        },
    }


@router.get("/integrations")
def integrations(user: Actor) -> dict:
    cfg = settings()
    cloud = cfg.assessflow_mode == "azure"
    return {
        "mode": cfg.assessflow_mode,
        "environment": cfg.assessflow_env,
        "database": "postgresql"
        if cfg.database_url.startswith("postgresql")
        else "sqlite-explicit-development",
        "providers": [
            {
                "name": name,
                "provider": provider if cloud else local,
                "status": "configured-not-probed" if cloud else "local-only",
            }
            for name, provider, local in [
                ("Assessment", "Microsoft Foundry / Azure OpenAI", "Deterministic simulation"),
                ("Retrieval", "Azure AI Search keyword", "Local keyword retrieval"),
                ("Privacy", "Azure AI Language", "Local regex redaction"),
                ("Identity", "Microsoft Entra ID", "Synthetic identity selection"),
            ]
        ],
        "copilot": "Implementation assets prepared; tenant import/publishing unverified",
        "workflow": "signed-callback-configured"
        if cfg.workflow_callback_secret
        else "local approvals only",
    }


@router.post("/integrations/probe")
def probe(db: DB, user: Actor) -> dict:
    require_role(user, "admin")
    db.execute(select(User.id).limit(1))
    if settings().assessflow_mode == "demo":
        return {"database": "reachable", "retrieval": "local", "live_cloud_call": False}
    from app.integrations.microsoft.providers import SearchProvider, PrivacyProvider

    SearchProvider().search("health", user.department)
    PrivacyProvider().redact("Synthetic service health probe")
    return {
        "database": "reachable",
        "search": "reachable",
        "language": "reachable",
        "foundry": "not probed; use workspace explicitly",
        "live_cloud_call": True,
    }


@router.get("/directory/me")
def directory_me(request: Request, user: Actor) -> dict:
    if settings().assessflow_mode == "demo":
        return {
            "id": user.id,
            "display_name": user.name,
            "department": user.department,
            "provider": "synthetic",
        }
    token = request.headers.get("X-Graph-Token", "")
    if not token:
        raise HTTPException(
            400, "A separately acquired delegated Graph User.Read token is required"
        )
    profile = GraphProvider().profile(token)
    if profile.id != user.id:
        raise HTTPException(403, "Graph identity must match API identity")
    return {
        "id": profile.id,
        "display_name": profile.display_name,
        "department": profile.department,
        "provider": "graph",
    }


@router.get("/workflows")
def workflows(db: DB, user: Actor) -> dict:
    require_role(user, "admin", "operator")
    return {
        "items": [
            {
                "request_id": x.request_id,
                "status": x.status,
                "external_id": x.external_id,
                "expires_at": x.expires_at.isoformat(),
            }
            for x in db.scalars(select(Workflow).limit(100))
        ]
    }


@router.post("/workflows/callback", tags=["integration-callback"])
async def callback(request: Request, db: DB) -> dict:
    secret = settings().workflow_callback_secret
    if not secret:
        raise HTTPException(503, "Workflow callback not configured")
    raw = await request.body()
    timestamp = request.headers.get("X-Workflow-Timestamp", "")
    try:
        if abs(time.time() - int(timestamp)) > 300:
            raise ValueError()
    except ValueError:
        raise HTTPException(401, "Expired callback") from None
    expected = hmac.new(
        secret.encode(), timestamp.encode() + b"." + raw, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get("X-Workflow-Signature", "")):
        raise HTTPException(401, "Invalid callback signature")
    try:
        payload = CallbackInput.model_validate_json(raw)
    except ValueError:
        raise HTTPException(422, "Invalid callback contract") from None
    digest = hashlib.sha256(raw).hexdigest()
    previous = db.get(IntegrationEvent, payload.event_id)
    if previous:
        if previous.digest != digest:
            raise HTTPException(409, "Event ID reused with different payload")
        return {"status": "already_processed"}
    user = db.get(User, payload.actor_id)
    if not user:
        raise HTTPException(403, "Approver is not onboarded")
    item = owned_request(db, user, payload.request_id, lock=True)
    workflow = db.get(Workflow, item.id)
    if not workflow or workflow.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise HTTPException(409, "Approval workflow expired")
    decide(
        db,
        user,
        item,
        DecisionInput(decision=payload.decision, reason=payload.reason),
        request.state.correlation_id,
    )
    db.add(
        IntegrationEvent(
            id=payload.event_id, kind="approval_callback", request_id=item.id, digest=digest
        )
    )
    audit(
        db,
        user.id,
        "workflow_callback",
        item.id,
        {"event_id": payload.event_id},
        request.state.correlation_id,
    )
    return {"status": "recorded", "request_status": item.status}


@router.post("/workflows/{request_id}/start")
def start_workflow(request_id: str, request: Request, db: DB, user: Actor) -> dict:
    from app.integrations.microsoft.automation import AutomationProvider

    require_role(user, "admin")
    item = owned_request(db, user, request_id, lock=True)
    workflow = db.get(Workflow, item.id)
    if item.status != "pending_approval" or not workflow:
        raise HTTPException(409, "Pending approval workflow required")
    if workflow.external_id:
        return {"status": workflow.status, "execution_id": workflow.external_id}
    owner = db.get(User, item.requester_id)
    if not owner.manager_id:
        raise HTTPException(409, "Assigned manager required")
    external_id = AutomationProvider().start(item.id, owner.manager_id)
    workflow.external_id = external_id
    workflow.status = "external_pending"
    audit(
        db,
        user.id,
        "workflow_started",
        item.id,
        {"execution_id": external_id},
        request.state.correlation_id,
    )
    return {"status": workflow.status, "execution_id": external_id}


@router.post("/workflows/maintenance/expire")
def expire_workflows(request: Request, db: DB, user: Actor) -> dict:
    require_role(user, "admin")
    expired = []
    for workflow in db.scalars(
        select(Workflow)
        .where(Workflow.status.in_(["local_pending", "external_pending"]))
        .with_for_update()
    ):
        if workflow.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            workflow.status = "expired_escalation_required"
            expired.append(workflow.request_id)
            audit(
                db,
                user.id,
                "workflow_expired",
                workflow.request_id,
                {"next_step": "administrator review and renewal required"},
                request.state.correlation_id,
            )
    return {"expired_request_ids": expired}


@router.post("/workflows/{request_id}/renew")
def renew_workflow(request_id: str, request: Request, db: DB, user: Actor) -> dict:
    from datetime import timedelta

    require_role(user, "admin")
    item = owned_request(db, user, request_id, lock=True)
    workflow = db.get(Workflow, item.id)
    if item.status != "pending_approval" or not workflow:
        raise HTTPException(409, "Pending approval required")
    workflow.expires_at = datetime.now(timezone.utc) + timedelta(days=3)
    workflow.status = "local_pending"
    workflow.external_id = None
    audit(db, user.id, "workflow_renewed", item.id, correlation=request.state.correlation_id)
    return {"status": workflow.status, "expires_at": workflow.expires_at.isoformat()}
