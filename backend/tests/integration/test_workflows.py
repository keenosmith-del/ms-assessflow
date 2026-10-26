from uuid import uuid4
from app.models.entities import AccessRequest, User

PAYLOAD = {
    "application_id": "finance-reports",
    "access_level": "reader",
    "justification": "Quarterly finance reporting and reconciliation",
}


def create(client, user="employee", payload=None, key=None):
    return client.post(
        "/v1/requests",
        json=payload or PAYLOAD,
        headers={"X-Demo-User": user, "Idempotency-Key": key or str(uuid4())},
    )


def test_complete_persisted_lifecycle(client):
    response = create(client)
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["status"] == "pending_approval"
    rid = item["id"]
    decision = {"decision": "approved", "reason": "Reviewed appropriate finance duties"}
    approved = client.post(
        f"/v1/requests/{rid}/decision", json=decision, headers={"X-Demo-User": "manager"}
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "provisioning_pending"
    replay = client.post(
        f"/v1/requests/{rid}/decision", json=decision, headers={"X-Demo-User": "manager"}
    )
    assert replay.status_code == 200
    fulfil = client.post(
        f"/v1/requests/{rid}/fulfil",
        json={"reference": "MANUAL-IT-12345"},
        headers={"X-Demo-User": "operator"},
    )
    assert fulfil.status_code == 200
    detail = client.get(f"/v1/requests/{rid}", headers={"X-Demo-User": "employee"}).json()
    assert detail["status"] == "fulfilled"
    assert detail["assessments"][0]["output"]["citations"]
    assert detail["fulfilment"]["reference"] == "MANUAL-IT-12345"
    assert len(detail["timeline"]) >= 7
    with client.factory() as db:
        assert db.get(AccessRequest, rid).status == "fulfilled"


def test_missing_information_preserves_id(client):
    response = create(client, payload={**PAYLOAD, "justification": ""})
    assert response.json()["status"] == "awaiting_information"
    rid = response.json()["id"]
    result = client.patch(
        f"/v1/requests/{rid}/information",
        json={"justification": PAYLOAD["justification"]},
        headers={"X-Demo-User": "employee"},
    )
    assert result.status_code == 200
    assert result.json()["id"] == rid
    assert result.json()["status"] == "pending_approval"


def test_rejection_and_terminal_state(client):
    rid = create(client).json()["id"]
    result = client.post(
        f"/v1/requests/{rid}/decision",
        json={"decision": "rejected", "reason": "Business requirement not established"},
        headers={"X-Demo-User": "manager"},
    )
    assert result.json()["status"] == "rejected"
    assert (
        client.post(f"/v1/requests/{rid}/cancel", headers={"X-Demo-User": "employee"}).status_code
        == 409
    )


def test_idempotency_and_semantic_duplicate(client):
    key = str(uuid4())
    first = create(client, key=key)
    assert first.status_code == 201
    assert create(client, key=key).json()["id"] == first.json()["id"]
    assert create(client).status_code == 409
    assert (
        create(client, key=key, payload={**PAYLOAD, "access_level": "analyst"}).status_code == 409
    )


def test_policy_acl_exception(client):
    rid = create(client, user="other").json()["id"]
    detail = client.get(f"/v1/requests/{rid}", headers={"X-Demo-User": "other"}).json()
    result = detail["assessments"][0]
    assert result["output"]["recommendation"] == "manual_review"
    assert result["eligibility"]["eligible"] is False
    assert result["output"]["citations"] == []


def test_dashboard_and_audit_are_persisted(client):
    create(client)
    metrics = client.get("/v1/metrics", headers={"X-Demo-User": "admin"}).json()
    assert metrics["total"] == 1
    assert metrics["counts"]["pending_approval"] == 1
    events = client.get("/v1/audit", headers={"X-Demo-User": "admin"}).json()["items"]
    assert any(x["action"] == "assessment_completed" for x in events)


def test_comment_redaction(client):
    rid = create(client).json()["id"]
    response = client.post(
        f"/v1/requests/{rid}/comments",
        json={"body": "Contact fake@example.test"},
        headers={"X-Demo-User": "employee"},
    )
    assert "fake@example.test" not in response.text


def test_admin_cannot_self_approve(client):
    payload = {**PAYLOAD, "application_id": "service-desk"}
    rid = create(client, user="admin", payload=payload).json()["id"]
    result = client.post(
        f"/v1/requests/{rid}/decision",
        json={"decision": "approved", "reason": "I would approve myself"},
        headers={"X-Demo-User": "admin"},
    )
    assert result.status_code == 403


def test_unassigned_manager_cannot_read(client):
    with client.factory.begin() as db:
        db.add(User(id="stranger-manager", name="Synthetic", role="approver", department="finance"))
    rid = create(client).json()["id"]
    assert (
        client.get(f"/v1/requests/{rid}", headers={"X-Demo-User": "stranger-manager"}).status_code
        == 404
    )
