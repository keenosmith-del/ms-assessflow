from types import SimpleNamespace
from unittest.mock import MagicMock
import httpx
import pytest
from sqlalchemy import select
from app.core.config import settings
from app.integrations.microsoft import providers as p
from app.integrations.microsoft.automation import AutomationProvider
from app.models.entities import AccessRequest, User, PolicyVersion
from app.schemas.contracts import RequestInput, AssessmentOutput
from app.agents.assessment import analyse


@pytest.fixture
def azure(monkeypatch):
    monkeypatch.setattr(settings(), "assessflow_mode", "azure")
    for key in ["foundry_project_endpoint", "azure_language_endpoint", "azure_search_endpoint"]:
        monkeypatch.setattr(settings(), key, "https://synthetic.example.test")
    monkeypatch.setattr(settings(), "azure_openai_deployment", "synthetic-model")
    credential = MagicMock()
    credential.__enter__.return_value = credential
    monkeypatch.setattr(p, "DefaultAzureCredential", lambda: credential)
    return credential


def context_client(monkeypatch, name, client):
    client.__enter__.return_value = client
    monkeypatch.setattr(p, name, MagicMock(return_value=client))


def test_language_uses_supported_pii_contract(azure, monkeypatch):
    client = MagicMock()
    client.recognize_pii_entities.return_value = [
        SimpleNamespace(
            is_error=False, redacted_text="[REDACTED]", entities=[SimpleNamespace(category="Email")]
        )
    ]
    context_client(monkeypatch, "TextAnalyticsClient", client)
    result = p.PrivacyProvider().redact("synthetic@example.test")
    assert result.text == "[REDACTED]"
    assert result.provider == "azure-language"
    assert client.recognize_pii_entities.call_args.kwargs["disable_service_logs"] is True


def test_language_failure_stops_processing(azure, monkeypatch):
    client = MagicMock()
    client.recognize_pii_entities.side_effect = RuntimeError("private provider diagnostics")
    context_client(monkeypatch, "TextAnalyticsClient", client)
    with pytest.raises(p.ProviderError, match="analysis stopped"):
        p.PrivacyProvider().redact("sensitive")


def test_foundry_parses_structured_advisory_output(azure, monkeypatch):
    expected = AssessmentOutput(
        recommendation="manual_review",
        explanation="Missing evidence",
        missing_fields=[],
        uncertainty="High",
        citations=[],
    )
    client = MagicMock()
    client.responses.parse.return_value = SimpleNamespace(output_parsed=expected, usage=None)
    client.__enter__.return_value = client
    project = MagicMock()
    project.get_openai_client.return_value = client
    context_client(monkeypatch, "AIProjectClient", project)
    assert p.FoundryProvider().assess({"application_id": "service-desk"}, []) == expected
    assert client.responses.parse.call_args.kwargs["text_format"] is AssessmentOutput
    assert client.responses.parse.call_args.kwargs["store"] is False
    assert "tools" not in client.responses.parse.call_args.kwargs


def test_foundry_refusal_has_no_fallback(azure, monkeypatch):
    project = MagicMock()
    project.get_openai_client.side_effect = RuntimeError("provider down")
    context_client(monkeypatch, "AIProjectClient", project)
    with pytest.raises(p.ProviderError):
        p.FoundryProvider().assess({}, [])


def test_search_acl_is_server_filter(azure, monkeypatch):
    client = MagicMock()
    client.search.return_value = []
    context_client(monkeypatch, "SearchClient", client)
    p.SearchProvider().search("reader", "finance", "finance-reports")
    assert (
        client.search.call_args.kwargs["filter"]
        == "(department eq 'all' or department eq 'finance') and application_id eq 'finance-reports'"
    )


def test_search_index_failure_is_explicit(azure, monkeypatch):
    client = MagicMock()
    client.upload_documents.return_value = [SimpleNamespace(succeeded=False)]
    context_client(monkeypatch, "SearchClient", client)
    with pytest.raises(p.ProviderError):
        p.SearchProvider().index([{"id": "test"}])


def test_graph_read_only_and_throttling(monkeypatch):
    def mock_get(_self, url, **kwargs):
        assert url == "https://graph.microsoft.com/v1.0/me"
        assert kwargs["params"]["$select"] == "id,displayName,department"
        return httpx.Response(429, headers={"Retry-After": "17"}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", mock_get)
    with pytest.raises(p.ProviderError, match="17"):
        p.GraphProvider().profile("synthetic-token")


def test_graph_typed_profile(monkeypatch):
    monkeypatch.setattr(
        httpx.Client,
        "get",
        lambda _s, url, **_kw: httpx.Response(
            200,
            json={"id": "synthetic", "displayName": "Synthetic Employee", "department": "finance"},
            request=httpx.Request("GET", url),
        ),
    )
    assert p.GraphProvider().profile("synthetic-token").department == "finance"


def test_forged_model_citation_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings(), "assessflow_mode", "azure")
    monkeypatch.setattr(
        p.PrivacyProvider, "redact", lambda _s, value: p.Redaction(value, (), "test")
    )
    monkeypatch.setattr(p.SearchProvider, "search", lambda *_a, **_k: [])
    monkeypatch.setattr(
        p.FoundryProvider,
        "assess",
        lambda *_a: AssessmentOutput(
            recommendation="approve",
            explanation="Fabricated",
            missing_fields=[],
            uncertainty="",
            citations=[{"version_id": "fake", "chunk_index": 0, "quote": "fake"}],
        ),
    )
    with client.factory() as db:
        with pytest.raises(p.ProviderError, match="citation"):
            analyse(
                db,
                db.get(User, "employee"),
                RequestInput(
                    application_id="finance-reports",
                    access_level="reader",
                    justification="Valid business justification",
                ),
            )


def test_stale_search_results_are_filtered(client, monkeypatch):
    monkeypatch.setattr(settings(), "assessflow_mode", "azure")
    from app.services.policies import retrieve

    with client.factory.begin() as db:
        old = db.scalar(select(PolicyVersion).where(PolicyVersion.policy_id == "finance-policy"))
        db.add(
            PolicyVersion(
                policy_id="finance-policy",
                version=2,
                content="Updated policy",
                chunks=["Updated policy"],
                digest="0" * 64,
                expires_at="2030-12-31",
            )
        )
        monkeypatch.setattr(
            p.SearchProvider, "search", lambda *_a, **_k: [{"version_id": old.id, "chunk_index": 0}]
        )
        assert retrieve(db, db.get(User, "employee"), application_id="finance-reports") == []


def test_automation_requires_secure_configuration():
    with pytest.raises(p.ProviderError, match="HTTPS"):
        AutomationProvider().start("request-id", "manager")


def test_provider_failure_rolls_back_request(client, monkeypatch):
    from tests.integration.test_workflows import create

    monkeypatch.setattr(
        p.PrivacyProvider,
        "redact",
        lambda *_a: (_ for _ in ()).throw(p.ProviderError("PII unavailable")),
    )
    assert create(client).status_code == 503
    with client.factory() as db:
        assert db.scalar(select(AccessRequest)) is None
