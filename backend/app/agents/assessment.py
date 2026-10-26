from time import perf_counter
from uuid import uuid4
from app.core.config import settings
from app.schemas.contracts import AssessmentOutput, Citation
from app.models.entities import Application
from app.services.policies import retrieve
from app.integrations.microsoft.providers import PrivacyProvider, FoundryProvider, ProviderError


def analyse(db, user, item):
    started = perf_counter()
    privacy = PrivacyProvider().redact(item.justification)
    evidence = retrieve(db, user, application_id=item.application_id)
    application = db.get(Application, item.application_id)
    missing = ["justification"] if len(item.justification.strip()) < 20 else []
    failures = []
    if not application or item.access_level not in application.levels:
        failures.append("Unsupported entitlement")
    if not evidence:
        failures.append("No accessible policy evidence")
    if any(x["expired"] for x in evidence):
        failures.append("Expired policy requires review")
    if len({x["policy_id"] for x in evidence}) > 1:
        failures.append("Conflicting policy sources require review")
    if item.application_id == "finance-reports" and user.department != "finance":
        failures.append("Finance department requirement is not satisfied")
    if "ignore previous" in item.justification.lower() or any(
        "ignore previous" in x["quote"].lower() for x in evidence
    ):
        failures.append("Instruction-like content requires manual review")
    if settings().assessflow_mode == "azure":
        result = FoundryProvider().assess(
            {
                "application_id": item.application_id,
                "access_level": item.access_level,
                "justification": privacy.text,
            },
            evidence,
        )
        for citation in result.citations:
            if not any(
                citation.version_id == x["version_id"]
                and citation.chunk_index == x["chunk_index"]
                and citation.quote in x["quote"]
                and citation.quote.strip()
                for x in evidence
            ):
                raise ProviderError("Model citation failed evidence validation")
        if not result.citations and result.recommendation == "approve":
            failures.append("Model supplied no citations")
    else:
        result = AssessmentOutput(
            recommendation="manual_review" if missing or failures else "approve",
            explanation="; ".join(failures)
            or "Evidence supports a human approval review. No access has been granted.",
            missing_fields=missing,
            uncertainty="Deterministic offline simulation; no live model invoked.",
            citations=[
                Citation(**{k: x[k] for k in ["version_id", "chunk_index", "quote"]})
                for x in evidence
            ],
        )
    if failures or missing:
        result.recommendation = "manual_review"
        result.explanation += " Deterministic checks: " + "; ".join(failures + missing)
    result.missing_fields = sorted(set(result.missing_fields + missing))
    return {
        "output": result.model_dump(),
        "eligibility": {"eligible": not failures and not missing, "failures": failures},
        "provider": "foundry" if settings().assessflow_mode == "azure" else "demo-deterministic",
        "trace_id": str(uuid4()),
        "latency_ms": round((perf_counter() - started) * 1000),
        "pii_provider": privacy.provider,
    }
