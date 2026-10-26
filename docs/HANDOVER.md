# AssessFlow engineering handover — 26 October 2026

## Executive outcome
AssessFlow is a persisted access-governance workflow system with a connected operational
console, an advisory assessment boundary, restricted employee agent tools and deployment
preparation. Requests survive clarification, decisions are human and unique, and fulfilment
requires an approved task plus a recorded operator reference. No permission-grant API exists.

Locally implemented: React/JSX/Router/Vite/plain CSS/Fetch; Python 3.12/FastAPI/Pydantic;
SQLAlchemy/Alembic/PostgreSQL; explicit SQLite demo; Entra JWT checks and MSAL configuration;
Foundry/Azure OpenAI, Language PII, Search, read-only Graph and workflow adapters; Docker,
GitHub Actions, Bicep, tests, synthetic fixtures and substantial operating documentation.

The web console has all nine requested page areas. Dashboard and queues use persisted scoped
records. Policies are versioned UTF-8 text documents with chunks/digests/expiry/department ACL.
Assessment citations reference immutable versions; inaccessible evidence is withheld even when
a service operator can view the request. The agent workspace shows actual structured provider
results/errors and invocation IDs, not a pretend Copilot chat.

## Final architecture
The React console and Copilot custom connector call distinct API boundaries. FastAPI enforces
authentication, roles, ownership, valid states, idempotency and human decisions. PostgreSQL is
the source of truth. Advisory assessment runs redaction → ACL-aware retrieval → model/demo
analysis → schema/citation validation → deterministic override. Approvals create manual service
tasks. Graph only reads the signed-in user's profile. Workflow callbacks authenticate exact
bytes, timestamp, event replay and assigned approver identity. See architecture diagrams.

## Verification and Git history
Exact commands and measured results are in testing/results.md. Iteration history and full
commit hashes are in iterations/release-manifest.md; each completed implementation stage was
committed and pushed to the existing origin with user authorisation. Remote CI execution is
linked in the result record. Canonical existing folder is ms-assesflow; remote is ms-assessflow.
No sibling repository was modified and Git was not reinitialised.

## Microsoft status
| Component | Implemented | Tested locally | Configured/deployed/live verified |
|---|---|---|---|
| Foundry/Azure OpenAI | Stable SDK Responses + strict advisory schema, usage/citations | Mocked contract/refusal/forged-citation tests | No |
| Language PII | Configurable categories, typed redaction, segmentation/fail closed | Adapter and regex tests | No |
| AI Search | Index schema, chunk upload, keyword search, ACL/current-version checks/reindex CLI | Mocked contract/ACL/stale-index tests | No |
| Entra/MSAL | SPA sign-in configuration, JWT/JWKS claims and DB RBAC | Real local RSA token/claim tests; scopes/client restrictions | No real tenant sign-in |
| Graph | Delegated /me typed adapter, identity match, throttling errors | Mocked profile/throttling tests | No |
| Copilot Studio | Instructions/topics/tests and valid Swagger 2 restricted connector | Contract validation | No native solution or published agent |
| Power Automate | Start/callback contracts, signing adapter, replay/expiry/escalation APIs | Synthetic HMAC/duplicate/expiry tests | No actual flow/signing boundary |
| Azure Functions | Deliberately omitted from main architecture | Not applicable | Optional future isolated signer only |
| Azure monitoring | Structured logs and deployment guidance | Local metadata checks | No connected Application Insights or exporter |

## Exact remaining operator actions
1. Approve subscription/region/budgets and obtain necessary tenant maker, consent, solution and
   publishing permissions/licences; select the intended channels and capacities with your admin.
2. Register API/SPA/separate connector applications, delegated scopes and exact redirect URIs;
   configure tenant/audience/client values; onboard actual authorised oids/roles/manager relations
   using the reviewed CLI. Use no demo seed in Azure mode.
3. Create/select Foundry project and supported structured-output Azure OpenAI deployment,
   Language resource and Search service. Configure endpoints and narrow managed-identity roles.
4. Create Search schema/reindex current approved policies; configure actual policy/catalog content.
   Current deterministic rules cover supported entitlement, justification length, evidence/expiry
   and the finance department restriction. Broader policy rules require reviewed application logic,
   not instructions uploaded in natural language.
5. Build immutable production images with actual API and SPA identity values. Review Bicep,
   identity/Key Vault/registry grants, DB firewall/networking, and migrate through a controlled job.
   Actual deployment requires approval and regional what-if validation; no deployment was performed.
6. Create a custom Power Platform solution; import/configure the source connector, end-user OAuth
   connections and agent behaviours; run prepared conversations. Export only authentic solution
   artifacts from the tenant. Import into a test environment and bind connection references.
7. Implement the trusted flow signing/responder-mapping boundary in the authorised environment,
   configure callback secret/start URL, assign real manager approvals, schedule expiry escalation
   and test spoofing/replay. No shared secret may be exposed to the employee agent.
8. Exercise live PII/retrieval/model and tenant JWT paths; evaluate actual model groundedness,
   escalation, latency/token/cost; connect approved Azure diagnostics and alert budgets; complete
   privacy/retention/penetration/load/accessibility review. Publish the agent only after approval.

## Deployment assessment and limitations
Ready for local demonstration, interview walkthrough and an authorised staging integration.
Not certified production-ready: no live tenant/service/channel validation or production load,
failover, penetration or accessibility audit. Infrastructure compiles and images build; those
checks do not establish subscription deployability. Staging foundation uses public service
endpoints with scoped DB firewall, a single low-cost plan and no HA. Private endpoints/HA are
organisation-specific production decisions. Shared-secret callbacks depend on a trustworthy
signer authenticating the real approver. Model/policy calls inside DB transactions constrain
throughput; use outbox/workers before large-scale traffic. Audit is API-append-only, not WORM.
Rate limiting is per process/IP; privacy redaction is imperfect; exact citations do not prove
semantic groundedness. Search is keyword, not hybrid/vector. The console exposes configuration
and diagnostic output, not a completed production monitoring pipeline.

Outstanding external work is listed above. Optional future enhancements include broader catalog
administration, richer configurable deterministic eligibility, paginated large approval queues,
managed async orchestration, hybrid retrieval justified by measured misses, and certified
accessibility/load targets. No real organisational communications or directory writes occurred.

Local startup commands are copied in the repository README and deployment/runbook.md. Cost
controls, rollback, backup and cleanup procedures are in deployment/runbook.md and
operations/operations.md. Keep local synthetic data separate from any future real tenant data.

## Iteration 008 release-engineering update
A separate manually dispatched staging workflow now prepares GitHub Environment approval,
OIDC, exact-SHA CI verification, locked image digests, existing-resource validation, smoke checks
and reviewed rollback. It has not been dispatched; no Azure environment or credential was
configured. The README badge reports actual CI only. See iterations/iteration-008.md and
deployment/staging-workflow.md for measured checks, activation prerequisites and limits.
