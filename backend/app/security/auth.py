from functools import lru_cache
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
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
        if claims["tid"] != cfg.entra_tenant_id or not {
            "access_as_user",
            "Requests.Create",
            "Requests.Read",
            "Policies.Read",
        }.intersection(claims.get("scp", "").split()):
            raise ValueError("Invalid tenant or scope")
        return claims
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, "Invalid or expired access token") from None


bearer = HTTPBearer(auto_error=False)


def current_user(request: Request, db: Session = Depends(get_db), _credentials=Depends(bearer)):
    if settings().assessflow_mode == "demo":
        user_id = request.headers.get("X-Demo-User")
        if not user_id:
            raise HTTPException(401, "Select a synthetic demo identity")
    else:
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "Bearer token required")
        claims = validate_token(authorization[7:])
        if not request.url.path.startswith("/v1/tools/"):
            if "access_as_user" not in claims.get("scp", "").split():
                raise HTTPException(403, "Console scope required")
            if (
                settings().entra_copilot_client_id
                and claims.get("azp") == settings().entra_copilot_client_id
            ):
                raise HTTPException(403, "Copilot client is restricted to employee tools")
        user_id = claims["oid"]
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(403, "Identity is not onboarded")
    request.state.actor_id = user.id
    return user


def require_role(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, "Role is not permitted")
