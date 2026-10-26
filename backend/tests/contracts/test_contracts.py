from app.main import app
from app.schemas.contracts import AssessmentOutput
from app.integrations.microsoft.providers import PrivacyProvider


def test_openapi_unique_operations_and_protected_paths():
    schema = app.openapi()
    operations = [
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operations) == len(set(operations))
    assert "/v1/requests/{request_id}/decision" in schema["paths"]
    assert "idempotency-key" in [
        p["name"] for p in schema["paths"]["/v1/requests"]["post"]["parameters"]
    ]


def test_privacy_contract():
    result = PrivacyProvider().redact("Contact synthetic@example.test or +27 82 555 0123")
    assert "synthetic@example.test" not in result.text
    assert "555" not in result.text
    assert result.provider == "local-regex"


def test_assessment_rejects_arbitrary_state():
    import pytest

    with pytest.raises(ValueError):
        AssessmentOutput(
            recommendation="fulfilled",
            explanation="",
            missing_fields=[],
            uncertainty="",
            citations=[],
        )
