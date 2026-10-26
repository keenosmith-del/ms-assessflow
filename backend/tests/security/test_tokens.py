import time
from types import SimpleNamespace
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from app.security import auth
from app.core.config import settings


@pytest.fixture
def signing(monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(settings(), "entra_tenant_id", "synthetic-tenant")
    monkeypatch.setattr(settings(), "entra_audience", "api://synthetic-api")
    client = SimpleNamespace(
        get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=private.public_key())
    )
    monkeypatch.setattr(auth, "jwks_client", lambda: client)
    claims = {
        "exp": int(time.time()) + 300,
        "iat": int(time.time()) - 1,
        "nbf": int(time.time()) - 1,
        "iss": "https://login.microsoftonline.com/synthetic-tenant/v2.0",
        "aud": "api://synthetic-api",
        "oid": "synthetic-user",
        "tid": "synthetic-tenant",
        "scp": "access_as_user",
    }
    return private, claims


def test_valid_signed_token(signing):
    private, claims = signing
    assert (
        auth.validate_token(jwt.encode(claims, private, algorithm="RS256"))["oid"]
        == "synthetic-user"
    )


@pytest.mark.parametrize(
    "change", [{"exp": 1}, {"aud": "wrong"}, {"iss": "wrong"}, {"tid": "wrong"}, {"scp": "other"}]
)
def test_invalid_token_claims(signing, change):
    private, claims = signing
    with pytest.raises(HTTPException) as error:
        auth.validate_token(jwt.encode({**claims, **change}, private, algorithm="RS256"))
    assert error.value.status_code == 401


def test_invalid_signature(signing):
    _, claims = signing
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(HTTPException):
        auth.validate_token(jwt.encode(claims, other, algorithm="RS256"))
