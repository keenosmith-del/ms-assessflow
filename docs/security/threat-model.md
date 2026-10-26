# Threat model and permission matrix
Trust boundaries: browser/agent → API identity; API → database state; API → PII/Search/model;
external workflow → signed callback. Treat every free-text field, model result and retrieved
policy as untrusted. No model receives grant tools. Database authorisation remains independent
of model output or natural-language claims. Cross-user access returns 404 to reduce enumeration.

| Action | Employee | Assigned approver | Operator | Admin |
|---|---|---|---|---|
| Own request create/clarify/comment/cancel | yes | yes | yes | yes |
| View another request | no | assigned only | yes | yes |
| Decide another request | no | assigned only | no | yes |
| Self approval | no | no | no | no |
| Record approved fulfilment | no | no | yes | yes |
| Edit policy | no | no | no | yes |
| View policy | department/all | department/all | department/all | all |
| Agent diagnostic | no | yes (own policy ACL) | no | yes |
| Audit | no | own request timeline | yes | yes |

Threats/control/evidence:
- Identity spoofing: tenant JWT RS256 JWKS, audience/issuer/expiry/nbf/scope and onboarded oid;
  tests cover wrong signature/claims; real tenant JWKS/network tests remain gated.
- Privilege escalation: database role, manager relation and resource ownership checks. Dedicated
  Copilot azp is confined to tool endpoints; tools require individual delegated scopes.
- Duplicate/racing decisions: PostgreSQL row locks, optimistic revision and one decision PK.
- Prompt injection: no model tools, advisory schema, exact citation validation, deterministic
  requirement checks, instruction-like content flag and mandatory human approval. Pattern flags
  are heuristic; the architecture prevents model-initiated grant even when detection fails.
- PII exposure: redact free text before storage/inference; no request bodies in application logs;
  provider failures stop processing; no automatic raw-text fallback. Local regex can over-redact
  long numeric sequences and miss names/IDs. Azure detection is also imperfect. Titles and search
  queries should not contain sensitive information; they are not privacy-classified by the API.
- Untrusted upload: UTF-8 text only, bounded API bytes/content length, no archive/path/executable
  processing; React renders content as text and does not use raw HTML.
- Callback tampering: HMAC timestamp/exact body, replay digest, onboarded/assigned actor, workflow
  expiry, unique decision. The signer must itself authenticate the actual approval responder.
- Secret leakage: environment examples only, Key Vault references in IaC, limited tracked-file
  scanner; use repository secret scanning as a complementary external control.

Known limits before enterprise release: audit rows are append-only through API but database
administrators can alter them; no WORM archive or audit retention automation. Rate limiting is
per process/IP and must be replaced/supplemented by gateway controls for scale. HTTPS is an
edge deployment requirement; development server is HTTP. Provider calls inside transactions
limit concurrency. Shared-secret callbacks depend on secure signer/responder mapping and key
rotation. Conditional access, retention, DLP, tenant consent and penetration testing need the
organisation's security owner. No production security certification is claimed.

Browser CORS preflight OPTIONS requests are exempt from the local per-IP limiter; actual
application requests remain limited. Repeated full browser suites share a process/IP budget;
restart only AssessFlow's dedicated test server between runs when necessary.
