from app.core.config import settings
from app.security import auth
from app.api.routes import tools
from tests.integration.test_workflows import create


def test_tool_boundary_returns_only_permitted_status(client):
    rid = create(client).json()["id"]
    result = client.get(f"/v1/tools/requests/{rid}", headers={"X-Demo-User": "employee"})
    assert result.status_code == 200
    assert set(result.json()) == {"id", "status", "next_step", "missing_fields"}
    assert (
        client.get(f"/v1/tools/requests/{rid}", headers={"X-Demo-User": "other"}).status_code == 404
    )


def test_connector_client_and_tool_scope(client, monkeypatch):
    monkeypatch.setattr(settings(), "assessflow_mode", "azure")
    monkeypatch.setattr(settings(), "entra_copilot_client_id", "connector-client")
    claims = {"oid": "employee", "scp": "Requests.Read", "azp": "connector-client"}
    monkeypatch.setattr(auth, "validate_token", lambda _token: claims)
    monkeypatch.setattr(tools, "validate_token", lambda _token: claims)
    headers = {"Authorization": "Bearer synthetic-only"}
    assert client.get("/v1/session", headers=headers).status_code == 403
    assert client.get("/v1/tools/policies/search", headers=headers).status_code == 403
    claims["scp"] = "Policies.Read"
    claims["azp"] = "wrong-client"
    assert client.get("/v1/tools/policies/search", headers=headers).status_code == 403
    claims.update(scp="access_as_user", azp="connector-client")
    assert client.get("/v1/session", headers=headers).status_code == 403
