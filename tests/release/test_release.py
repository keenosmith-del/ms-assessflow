"""Release safety tests with synthetic GitHub/Azure responses; no external calls."""

import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


guard = module("release_guard")
release = module("staging_release")
SHA = "a" * 40
DIGEST = "sha256:" + "b" * 64


def protection():
    return {
        "protection_rules": [
            {
                "type": "required_reviewers",
                "prevent_self_review": True,
                "reviewers": [{"type": "User", "reviewer": {"login": "reviewer"}}],
            }
        ],
        "deployment_branch_policy": {"custom_branch_policies": True},
    }


def branches():
    return {"total_count": 1, "branch_policies": [{"name": "main", "type": "branch"}]}


def environment():
    env = {key: "configured" for key in release.REQUIRED}
    for key in [
        "AZURE_CLIENT_ID",
        "AZURE_TENANT_ID",
        "AZURE_SUBSCRIPTION_ID",
        "VITE_ENTRA_TENANT_ID",
        "VITE_ENTRA_CLIENT_ID",
    ]:
        env[key] = "11111111-1111-1111-1111-111111111111"
    env.update(
        STAGING_ENABLED="true",
        STAGING_API_URL="https://api.example.test",
        STAGING_WEB_URL="https://web.example.test",
        AZURE_API_APP="api",
        AZURE_WEB_APP="web",
    )
    return env


def test_protected_environment_gate():
    guard.validate_environment(protection(), branches())


@pytest.mark.parametrize(
    "mutation", ["no_reviewers", "self_review", "no_branch_policy", "wildcard", "tag"]
)
def test_environment_protection_fails_closed(mutation):
    env, policies = protection(), branches()
    if mutation == "no_reviewers":
        env["protection_rules"][0]["reviewers"] = []
    if mutation == "self_review":
        env["protection_rules"][0]["prevent_self_review"] = False
    if mutation == "no_branch_policy":
        env["deployment_branch_policy"] = None
    if mutation == "wildcard":
        policies["branch_policies"][0]["name"] = "*"
    if mutation == "tag":
        policies["branch_policies"][0]["type"] = "tag"
    with pytest.raises(ValueError):
        guard.validate_environment(env, policies)


@pytest.mark.parametrize(
    "reviews",
    [
        [],
        [
            {
                "state": "approved",
                "user": {"login": "actor"},
                "environments": [{"name": "azure-staging"}],
            }
        ],
        [
            {
                "state": "rejected",
                "user": {"login": "reviewer"},
                "environments": [{"name": "azure-staging"}],
            }
        ],
    ],
)
def test_bypass_or_self_approval_is_not_consent(reviews):
    with pytest.raises(ValueError):
        guard.validate_approval(reviews, "actor")


def test_actual_independent_approval():
    guard.validate_approval(
        [
            {
                "state": "approved",
                "user": {"login": "reviewer"},
                "environments": [{"name": "azure-staging"}],
            }
        ],
        "actor",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"head_sha": "c" * 40},
        {"conclusion": "failure"},
        {"event": "pull_request"},
        {"status": "in_progress"},
        {"head_branch": "feature"},
    ],
)
def test_only_exact_successful_main_push_ci(change):
    run = {
        "head_sha": SHA,
        "conclusion": "success",
        "status": "completed",
        "event": "push",
        "head_branch": "main",
    }
    guard.validate_ci({"workflow_runs": [run]}, SHA)
    with pytest.raises(ValueError):
        guard.validate_ci({"workflow_runs": [{**run, **change}]}, SHA)


@pytest.mark.parametrize("value", ["", "false", "TRUE"])
def test_activation_requires_explicit_true(value):
    env = environment()
    env["STAGING_ENABLED"] = value
    with pytest.raises(ValueError):
        release.configuration(env)


@pytest.mark.parametrize(
    "key,value",
    [
        ("AZURE_CLIENT_ID", ""),
        ("STAGING_API_URL", "http://api.example.test"),
        ("STAGING_WEB_URL", "https://user:secret@web.example.test"),
        ("STAGING_WEB_URL", "https://web.example.test/path"),
    ],
)
def test_missing_or_unsafe_configuration(key, value):
    env = environment()
    env[key] = value
    with pytest.raises(ValueError):
        release.configuration(env)


@pytest.mark.parametrize(
    "reference",
    [
        "registry.example.test/assessflow-api:latest",
        "evil.example.test/assessflow-api@" + DIGEST,
        "registry.example.test/other@" + DIGEST,
    ],
)
def test_mutable_or_foreign_images_rejected(reference):
    with pytest.raises(ValueError):
        release.image_reference(reference, "registry.example.test", "assessflow-api")


def test_promotion_requires_approved_job(monkeypatch):
    monkeypatch.delenv("APPROVED_STAGING_JOB", raising=False)
    with pytest.raises(ValueError):
        release.apply({}, {}, {})


def cloud_response(env):
    def call(*args):
        if args[:2] == ("account", "show"):
            return {
                "id": env["AZURE_SUBSCRIPTION_ID"],
                "tenantId": env["AZURE_TENANT_ID"],
            }
        if args[:2] == ("acr", "show"):
            return {"loginServer": "registry.example.test"}
        name = args[args.index("--name") + 1]
        if args[:2] == ("webapp", "show"):
            return {
                "tags": {"environment": "staging"},
                "httpsOnly": True,
                "identity": {"principalId": "synthetic"},
                "defaultHostName": name + ".example.test",
            }
        if args[:3] == ("webapp", "config", "show"):
            return {
                "acrUseManagedIdentityCreds": True,
                "linuxFxVersion": "DOCKER|registry.example.test/assessflow-"
                + name
                + "@"
                + DIGEST,
            }
        values = {"WEBSITES_PORT": "8080"}
        if name == "api":
            values = {
                key: "configured"
                for key in [
                    "ENTRA_TENANT_ID",
                    "ENTRA_CLIENT_ID",
                    "ENTRA_AUDIENCE",
                    "FOUNDRY_PROJECT_ENDPOINT",
                    "AZURE_OPENAI_DEPLOYMENT",
                    "AZURE_LANGUAGE_ENDPOINT",
                    "AZURE_SEARCH_ENDPOINT",
                ]
            }
            values.update(
                WEBSITES_PORT="5050",
                ASSESSFLOW_MODE="azure",
                ASSESSFLOW_ENV="production",
                DATABASE_URL="@Microsoft.KeyVault(SecretUri=synthetic)",
                CORS_ORIGINS=env["STAGING_WEB_URL"],
            )
        return [{"name": k, "value": v} for k, v in values.items()]

    return call


def test_snapshot_contains_only_rollback_images_not_secrets():
    env = environment()
    with patch.object(release, "az", side_effect=cloud_response(env)):
        result = release.resource_state(env)
    assert set(result) == {"registry", "resource_group", "applications"}
    assert "DATABASE_URL" not in json.dumps(result)
    assert result["applications"]["api"]["image"].endswith(DIGEST)


def test_production_target_is_rejected():
    env = environment()
    original = cloud_response(env)

    def call(*args):
        result = copy.deepcopy(original(*args))
        if args[:2] == ("webapp", "show"):
            result["tags"]["environment"] = "production"
        return result

    with (
        patch.object(release, "az", side_effect=call),
        pytest.raises(ValueError, match="staging-tagged"),
    ):
        release.resource_state(env)


def test_digest_only_updates_existing_apps(monkeypatch):
    monkeypatch.setenv("APPROVED_STAGING_JOB", "true")
    env = environment()
    images = {
        x: "registry.example.test/assessflow-" + x + "@" + DIGEST
        for x in ["api", "web"]
    }
    with patch.object(release, "az") as azure:
        release.apply(env, {"registry": "registry.example.test"}, images)
    assert azure.call_count == 2
    for call in azure.call_args_list:
        assert call.args[:4] == ("webapp", "config", "container", "set")
        assert "--container-image-name" in call.args
        assert not any(
            x in call.args for x in ["create", "deployment", "group", "delete"]
        )


def test_smoke_rejects_demo_or_public_session():
    responses = [
        (200, b'{"status":"ready"}', {}),
        (200, b'{"mode":"azure"}', {}),
        (200, b"{}", {}),
    ]
    with (
        patch.object(release, "request_status", side_effect=responses),
        pytest.raises(RuntimeError, match="unauthenticated"),
    ):
        release.smoke("https://api.example.test", "https://web.example.test")


def test_basic_smoke_contract():
    responses = [
        (200, b'{"status":"ready"}', {}),
        (200, b'{"mode":"azure"}', {}),
        (401, b"", {}),
        (
            200,
            b'<div id="root"></div>',
            {"Content-Security-Policy": "default-src self"},
        ),
        (
            200,
            b'<div id="root"></div>',
            {"Content-Security-Policy": "default-src self"},
        ),
    ]
    with patch.object(release, "request_status", side_effect=responses):
        release.smoke("https://api.example.test", "https://web.example.test")


def test_workflow_is_manual_only_and_oidc_is_job_scoped():
    # PyYAML's YAML 1.1 parser represents the GitHub 'on' key as True.
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/deploy-staging.yml").read_text()
    )
    assert set(workflow.get("on", workflow.get(True))) == {"workflow_dispatch"}
    assert "id-token" not in workflow["permissions"]
    assert "environment" not in workflow["jobs"]["preflight"]
    staging = workflow["jobs"]["staging"]
    assert staging["environment"]["name"] == "azure-staging"
    assert staging["permissions"]["id-token"] == "write"
    names = [x.get("name", "") for x in staging["steps"]]
    assert names.index(
        "Recheck protection and actual independent approval before obtaining Azure credentials"
    ) < names.index("Azure OIDC login (no stored client secret or publish profile)")
    assert workflow["concurrency"]["cancel-in-progress"] is False


def test_mutation_is_not_reached_when_staging_baseline_drifts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key, value in environment().items():
        monkeypatch.setenv(key, value)
    Path("staging-before.json").write_text(json.dumps({"registry": "previous"}))
    with (
        patch("sys.argv", ["staging_release.py", "deploy"]),
        patch.object(release, "resource_state", return_value={"registry": "changed"}),
        patch.object(release, "apply") as apply,
    ):
        with pytest.raises(ValueError, match="baseline changed"):
            release.main()
        apply.assert_not_called()
