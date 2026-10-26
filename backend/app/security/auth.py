from functools import lru_cache
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User


@lru_cache
def jwks_client():
    return jwt.PyJWKClient(
        f"https://login.microsoftonline.com/{settings().entra_tenant_id}/discovery/v2.0/keys",
        timeout=10,
    )


def validate_token(token):
    cfg = settings()
    try:
        key = jwks_client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=cfg.entra_audience,
            issuer=f"https://login.microsoftonline.com/{cfg.entra_tenant_id}/v2.0",
            options={"require": ["exp", "iat", "nbf", "iss", "aud", "oid", "tid"]},
        )
        if (
            claims["tid"] != cfg.entra_tenant_id
            or "access_as_user" not in claims.get("scp", "").split()
        ):
            raise ValueError("Invalid tenant or scope")
        return claims
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, "Invalid or expired access token") from None


def current_user(request: Request, db: Session = Depends(get_db)):
    if settings().assessflow_mode == "demo":
        user_id = request.headers.get("X-Demo-User")
        if not user_id:
            raise HTTPException(401, "Select a synthetic demo identity")
    else:
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "Bearer token required")
        user_id = validate_token(authorization[7:])["oid"]
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(403, "Identity is not onboarded")
    request.state.actor_id = user.id
    return user


def require_role(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, "Role is not permitted")


def can_read(user, item):
    return (
        item.requester_id == user.id
        or user.role in {"admin", "operator"}
        or (user.role == "approver")
    )
