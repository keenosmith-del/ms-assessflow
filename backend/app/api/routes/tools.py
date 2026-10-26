"""Restricted employee tools. Approval, fulfilment and administration are never exposed."""

from typing import Annotated
from fastapi import APIRouter, Header, HTTPException, Request
from app.api.routes.requests import DB, Actor, create_request, detail, clarify
from app.services.policies import retrieve
from app.schemas.contracts import RequestInput, Clarification
from app.core.config import settings
from app.security.auth import validate_token

router = APIRouter(prefix="/v1/tools", tags=["employee-tools"])


def tool_scope(request, scope):
    cfg = settings()
    if cfg.assessflow_mode == "demo":
        return
    if not cfg.entra_copilot_client_id:
        raise HTTPException(503, "Copilot client is not configured")
    claims = validate_token(request.headers.get("Authorization", "")[7:])
    if (
        claims.get("azp") != cfg.entra_copilot_client_id
        or scope not in claims.get("scp", "").split()
    ):
        raise HTTPException(403, "Connector client or tool scope is not permitted")


@router.post("/requests", status_code=201, operation_id="CreateAccessRequest")
def create_tool(
    payload: RequestInput,
    request: Request,
    db: DB,
    user: Actor,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=100)],
) -> dict:
    tool_scope(request, "Requests.Create")
    item = create_request(payload, request, db, user, idempotency_key)
    return {"id": item["id"], "status": item["status"]}


@router.get("/requests/{request_id}", operation_id="GetRequestStatus")
def status_tool(request_id: str, request: Request, db: DB, user: Actor) -> dict:
    tool_scope(request, "Requests.Read")
    item = detail(request_id, db, user)
    return {
        "id": item["id"],
        "status": item["status"],
        "next_step": item["next_step"],
        "missing_fields": item["assessments"][0]["output"]["missing_fields"]
        if item["assessments"]
        else [],
    }


@router.patch("/requests/{request_id}/information", operation_id="SupplyRequestInformation")
def information_tool(
    request_id: str, payload: Clarification, request: Request, db: DB, user: Actor
) -> dict:
    tool_scope(request, "Requests.Create")
    item = clarify(request_id, payload, request, db, user)
    return {"id": item["id"], "status": item["status"]}


@router.get("/policies/search", operation_id="SearchPermittedPolicies")
def search_tool(request: Request, db: DB, user: Actor, q: str = "") -> dict:
    tool_scope(request, "Policies.Read")
    if len(q) > 500:
        raise HTTPException(422, "Query is too long")
    return {"items": retrieve(db, user, q)}
