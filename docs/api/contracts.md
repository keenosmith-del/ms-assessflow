# API contracts
Generated full contract: openapi.json; Swagger UI: /docs; versioned prefix /v1.
`python scripts/export_contracts.py` regenerates API and restricted connector contracts.

| Boundary | Operations | Authorisation |
|---|---|---|
| Session/catalog | session, applications, directory/me | Onboarded signed-in user |
| Requests | list/detail/create, information, comments, cancel | Owner; assigned manager; scoped operator/admin |
| Decisions | approvals, requests/{id}/decision | Assigned approver or admin, never self |
| Fulfilment | requests/{id}/fulfil | Operator/admin plus approved task |
| Policies | list/search/version history | Department/all ACL or admin |
| Policy ingest | POST policies | Admin |
| Diagnostics | POST agent/assess, integrations/probe | Admin/approver for assess, admin for probe |
| Operations | metrics, integrations | Signed-in; metrics scoped to visible requests |
| Audit/workflows | audit, workflows, start/expire/renew | Operator/admin reads; admin mutations |
| Signed callback | workflows/callback | HMAC plus real assigned approver identity, expiry and replay checks |
| Agent tools | tools/requests, status, information, policies/search | Dedicated OAuth client and per-tool delegated scopes |

Create body: application_id, access_level, justification. Idempotency-Key (8–100 chars) is
required. Reusing a key with different payload returns 409. Identical active requests with a
new key also return 409. Same key/body replays persisted status (201) without reassessment.
List request parameters: q, status, offset>=0, limit 1..100. Audit supports exact actor and
request_id filters and pagination. Approvals/workflows return at most 100 rows; cursor pagination
for these operational queues is a scaling enhancement, not implemented in this release.

Protected endpoints require Entra bearer token in Azure mode; demo uses X-Demo-User on the
explicit development instance. No default authenticated identity is assumed. Employee tools
expose no approval, fulfilment, role or policy editing operation. The caller identity is never
an input field. Connector statuses are reduced to ID/status/next_step/missing_fields.

Errors use {error:{code,message,correlation_id}} for handled application errors. Oversize ingress
rejection happens before correlation middleware and contains code/message only. 401 invalid/missing
auth; 403 insufficient permission; 404 missing or inaccessible resource; 409 invalid transition,
expiry or conflict; 422 schema/entitlement validation; 429 local rate limit; 503 unavailable
provider/database; 500 safe generic error. Body content and secrets are excluded from errors.
X-Correlation-ID accepts a short safe identifier or is generated; responses expose it via CORS.
Raw API endpoints use server-side validation regardless of UI restrictions.

Callbacks sign timestamp + '.' + exact body with SHA256 HMAC, hex digest header. Timestamps
outside 300s fail. Event ID/digest uniqueness blocks changed replays. A decision uniqueness
constraint and request row lock protect concurrent callbacks/console actions. Callbacks do not
fulfil access; they can only record a valid human decision and create the approved task.
