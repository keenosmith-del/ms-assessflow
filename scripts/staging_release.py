"""Existing-resource staging validation, rollback snapshot, digest release and smoke checks.

Never creates resources, changes database schemas, grants roles or calls model APIs.
Azure-mutating phases are invoked only by the independently approved deployment job.
"""

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

REQUIRED = [
    "AZURE_CLIENT_ID",
    "AZURE_TENANT_ID",
    "AZURE_SUBSCRIPTION_ID",
    "AZURE_RESOURCE_GROUP",
    "AZURE_ACR_NAME",
    "AZURE_API_APP",
    "AZURE_WEB_APP",
    "STAGING_API_URL",
    "STAGING_WEB_URL",
    "VITE_ENTRA_TENANT_ID",
    "VITE_ENTRA_CLIENT_ID",
    "VITE_ENTRA_SCOPE",
    "STAGING_ENABLED",
]


def configuration(env):
    if any(not env.get(key) for key in REQUIRED) or env["STAGING_ENABLED"] != "true":
        raise ValueError(
            "All staging environment values and STAGING_ENABLED=true are required"
        )
    for key in [
        "AZURE_CLIENT_ID",
        "AZURE_TENANT_ID",
        "AZURE_SUBSCRIPTION_ID",
        "VITE_ENTRA_TENANT_ID",
        "VITE_ENTRA_CLIENT_ID",
    ]:
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", env[key]):
            raise ValueError(f"Invalid UUID configuration: {key}")
    for key in ["STAGING_API_URL", "STAGING_WEB_URL"]:
        parsed = urlparse(env[key])
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.port
        ):
            raise ValueError("Staging URLs must be HTTPS origins")
    if env["AZURE_API_APP"] == env["AZURE_WEB_APP"]:
        raise ValueError("API and web staging apps must be distinct")


def az(*args):
    # Capture diagnostics, not app configuration/secrets, in logs.
    result = subprocess.run(
        ["az", *args, "--only-show-errors", "--output", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "Azure command failed; inspect the approved runner privately: "
            + " ".join(args[:3])
        )
    return json.loads(result.stdout) if result.stdout.strip() else None


def image_reference(value, server, repository):
    if not re.fullmatch(
        re.escape(server + "/" + repository + "@sha256:") + r"[0-9a-f]{64}", value
    ):
        raise ValueError(
            "Container reference must use the configured repository and an immutable SHA256 digest"
        )
    return value


def resource_state(env):
    configuration(env)
    account = az("account", "show")
    if (
        account["id"].lower() != env["AZURE_SUBSCRIPTION_ID"].lower()
        or account["tenantId"].lower() != env["AZURE_TENANT_ID"].lower()
    ):
        raise ValueError("Unexpected Azure subscription or tenant")
    group = env["AZURE_RESOURCE_GROUP"]
    registry = az(
        "acr", "show", "--name", env["AZURE_ACR_NAME"], "--resource-group", group
    )
    server = registry["loginServer"]
    snapshot = {"registry": server, "resource_group": group, "applications": {}}
    for component in ["api", "web"]:
        name = env[f"AZURE_{component.upper()}_APP"]
        app = az("webapp", "show", "--resource-group", group, "--name", name)
        if (
            app.get("tags", {}).get("environment") != "staging"
            or not app.get("httpsOnly")
            or not app.get("identity", {}).get("principalId")
        ):
            raise ValueError(
                "Existing HTTPS staging-tagged app with managed identity is required"
            )
        if (
            env[f"STAGING_{component.upper()}_URL"].rstrip("/")
            != "https://" + app["defaultHostName"]
        ):
            raise ValueError(
                "Configured smoke origin must match the existing staging app hostname"
            )
        config = az(
            "webapp", "config", "show", "--resource-group", group, "--name", name
        )
        if config.get("acrUseManagedIdentityCreds") is not True:
            raise ValueError(
                "Managed identity registry pull must already be configured"
            )
        previous = config.get("linuxFxVersion", "").removeprefix("DOCKER|")
        image_reference(previous, server, "assessflow-" + component)
        values = {
            x["name"]: x["value"]
            for x in az(
                "webapp",
                "config",
                "appsettings",
                "list",
                "--resource-group",
                group,
                "--name",
                name,
            )
        }
        if component == "api":
            expected = {
                "ASSESSFLOW_MODE": "azure",
                "ASSESSFLOW_ENV": "production",
                "WEBSITES_PORT": "5050",
            }
            if any(values.get(k) != v for k, v in expected.items()):
                raise ValueError(
                    "Staging API must already enforce Azure production configuration"
                )
            if not values.get("DATABASE_URL", "").startswith("@Microsoft.KeyVault("):
                raise ValueError(
                    "Database configuration must use an existing Key Vault reference"
                )
            for key in [
                "ENTRA_TENANT_ID",
                "ENTRA_CLIENT_ID",
                "ENTRA_AUDIENCE",
                "FOUNDRY_PROJECT_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
                "AZURE_LANGUAGE_ENDPOINT",
                "AZURE_SEARCH_ENDPOINT",
            ]:
                if not values.get(key):
                    raise ValueError(
                        "Staging API has incomplete Microsoft configuration"
                    )
            if env["STAGING_WEB_URL"].rstrip("/") not in values.get(
                "CORS_ORIGINS", ""
            ).split(","):
                raise ValueError(
                    "Configured web origin must already be allowed by the API"
                )
        elif values.get("WEBSITES_PORT") != "8080":
            raise ValueError("Staging web container port must be 8080")
        snapshot["applications"][component] = {"name": name, "image": previous}
    return snapshot


def apply(env, snapshot, images):
    if os.environ.get("APPROVED_STAGING_JOB") != "true":
        raise ValueError("Digest promotion requires the approved staging job")
    for component in ["api", "web"]:
        image_reference(
            images[component], snapshot["registry"], "assessflow-" + component
        )
    for component in ["api", "web"]:
        az(
            "webapp",
            "config",
            "container",
            "set",
            "--resource-group",
            env["AZURE_RESOURCE_GROUP"],
            "--name",
            env[f"AZURE_{component.upper()}_APP"],
            "--container-image-name",
            images[component],
        )
    print("Submitted digest-only configuration updates to existing staging apps.")


def request_status(url):
    try:
        with urlopen(url, timeout=15) as response:
            return response.status, response.read(100000), dict(response.headers)
    except HTTPError as error:
        return error.code, b"", {}


def smoke(api_url, web_url):
    for _ in range(24):
        try:
            ready, body, _headers = request_status(api_url + "/ready")
            health, data, _headers = request_status(api_url + "/health")
            if (
                ready == health == 200
                and json.loads(body)["status"] == "ready"
                and json.loads(data)["mode"] == "azure"
            ):
                break
        except (URLError, TimeoutError, ValueError, KeyError):
            pass
        time.sleep(5)
    else:
        raise RuntimeError("Staging API did not become ready in Azure mode")
    if request_status(api_url + "/v1/session")[0] != 401:
        raise RuntimeError(
            "Protected session did not reject an unauthenticated request"
        )
    for path in ["/", "/requests"]:
        status, body, headers = request_status(web_url + path)
        if (
            status != 200
            or b'<div id="root">' not in body
            or not any(k.lower() == "content-security-policy" for k in headers)
        ):
            raise RuntimeError("Staging SPA deep-link/CSP smoke failed")
    print(
        "Staging smoke passed: DB readiness, Azure mode, anonymous 401, SPA and CSP. No model calls made."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["config", "snapshot", "deploy", "smoke"])
    args = parser.parse_args()
    env = os.environ
    configuration(env)
    if args.phase == "config":
        return
    if args.phase == "snapshot":
        Path("staging-before.json").write_text(
            json.dumps(resource_state(env), indent=2) + "\n"
        )
    elif args.phase == "deploy":
        # Revalidate just before mutation; preserve the original recovery snapshot.
        snapshot = resource_state(env)
        if snapshot != json.loads(Path("staging-before.json").read_text()):
            raise ValueError(
                "Staging baseline changed after the recovery snapshot; abort and review"
            )
        images = {"api": env["API_IMAGE"], "web": env["WEB_IMAGE"]}
        apply(env, snapshot, images)
        Path("staging-release.json").write_text(
            json.dumps({"revision": env["RELEASE_SHA"], "images": images}, indent=2)
            + "\n"
        )
    else:
        smoke(env["STAGING_API_URL"].rstrip("/"), env["STAGING_WEB_URL"].rstrip("/"))


if __name__ == "__main__":
    main()
