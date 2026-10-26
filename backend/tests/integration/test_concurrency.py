from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import os
import pytest
from sqlalchemy import select, func
from app.models.entities import Decision
from tests.integration.test_workflows import create


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="Requires real PostgreSQL row locks",
)
def test_concurrent_duplicate_creations_and_decisions(client):
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: create(client, key=key), range(2)))
    assert all(x.status_code == 201 for x in responses)
    assert responses[0].json()["id"] == responses[1].json()["id"]
    rid = responses[0].json()["id"]

    def approve(_):
        return client.post(
            f"/v1/requests/{rid}/decision",
            json={"decision": "approved", "reason": "Reviewed finance access requirement"},
            headers={"X-Demo-User": "manager"},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = list(pool.map(approve, range(2)))
    assert all(x.status_code == 200 for x in decisions)
    with client.factory() as db:
        assert db.scalar(select(func.count()).select_from(Decision)) == 1
