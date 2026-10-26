"""Run from repository root after installing backend. Emits real API and connector contracts."""

import json
from pathlib import Path

from app.main import app

schema = app.openapi()
Path("docs/api/openapi.json").write_text(json.dumps(schema, indent=2) + "\n")
# Power Platform custom connector requires Swagger 2.0, not a fabricated solution export.
schemas = schema["components"]["schemas"]


def convert(value):
    if isinstance(value, list):
        return [convert(x) for x in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key == "$ref":
            item = item.replace("#/components/schemas/", "#/definitions/")
        if key in {"anyOf", "const"}:
            continue
        result[key] = convert(item)
    return result


paths = {}
scopes = {
    "Requests.Create": "Submit and clarify own access requests",
    "Requests.Read": "Read permitted request status",
    "Policies.Read": "Search permitted policy evidence",
}
for path, methods in schema["paths"].items():
    if not path.startswith("/v1/tools/"):
        continue
    paths[path] = {}
    for method, operation in methods.items():
        params = []
        for parameter in operation.get("parameters", []):
            param = dict(parameter)
            shape = param.pop("schema", {})
            shape.pop("title", None)
            param.update(shape)
            params.append(convert(param))
        if "requestBody" in operation:
            params.append(
                {
                    "in": "body",
                    "name": "body",
                    "required": True,
                    "schema": convert(
                        operation["requestBody"]["content"]["application/json"][
                            "schema"
                        ]
                    ),
                }
            )
        scope = (
            "Policies.Read"
            if "policies" in path
            else "Requests.Read"
            if method == "get"
            else "Requests.Create"
        )
        paths[path][method] = {
            "operationId": operation["operationId"],
            "summary": operation.get("summary", operation["operationId"]),
            "description": "Delegated employee tool; the backend enforces identity and ownership.",
            "parameters": params,
            "responses": {
                "200" if method != "post" else "201": {
                    "description": "Persisted tool result",
                    "schema": convert(
                        operation["responses"]["200" if method != "post" else "201"][
                            "content"
                        ]["application/json"]["schema"]
                    ),
                }
            },
            "security": [{"entraOAuth": [scope]}],
        }
connector = {
    "swagger": "2.0",
    "info": {"title": "AssessFlow Employee Tools", "version": "1.0.0"},
    "host": "REPLACE_WITH_API_HOST",
    "basePath": "/",
    "schemes": ["https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "entraOAuth": {
            "type": "oauth2",
            "flow": "accessCode",
            "authorizationUrl": "https://login.microsoftonline.com/REPLACE_TENANT/oauth2/v2.0/authorize",
            "tokenUrl": "https://login.microsoftonline.com/REPLACE_TENANT/oauth2/v2.0/token",
            "scopes": scopes,
        }
    },
    "paths": paths,
    "definitions": convert(schemas),
}
Path("copilot/tools/connector.swagger.json").write_text(
    json.dumps(connector, indent=2) + "\n"
)
