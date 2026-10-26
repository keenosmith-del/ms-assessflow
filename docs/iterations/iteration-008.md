# Iteration 008 — focused staging release engineering

## Objective and scope
Add separately approved Azure staging release automation, real CI visibility and portfolio
engineering evidence. Keep the implemented application, UI and Microsoft provider boundaries
unchanged. Work in the existing ms-assesflow checkout / ms-assessflow remote.

## Implemented changes and relevant files
- `.github/workflows/deploy-staging.yml`: manual dispatch only, exact successful-main-CI SHA,
  explicit consent/schema confirmations, protected azure-staging environment, actual independent
  approval-history check, job-scoped Azure OIDC, existing-resource validation, unique build tags,
  locked digest-pinned image promotion, smoke checks, serial releases and recovery artifacts.
- `scripts/release_guard.py`: read-only GitHub preflight and independent approval verification.
- `scripts/staging_release.py`: fail-closed environment checks, existing staging app/identity/DB
  reference validation, secret-free rollback snapshot, baseline drift rejection, digest-only
  existing-app updates and limited HTTP smoke. No Azure resource creation or migrations.
- `tests/release/test_release.py`: 33 safety-focused tests with synthetic GitHub/Azure data;
  existing verify.yml executes these in addition to its unchanged four CI job areas.
- `infra/main.bicep`: matching staging environment tag on the existing web-app declaration,
  allowing release validation to distinguish staging targets consistently. Template not deployed.
- `README.md`: actual verify.yml/main status badge, explicit CI versus deployment versus cloud
  activation status, PostgreSQL/Playwright/Docker/security/CI/CD evidence.
- `docs/deployment/staging-workflow.md`: full operator variables, environment protection, OIDC
  subject/audience, narrow permission guidance, release/rollback/partial-failure instructions,
  limitations and official source references. Existing runbook/handover now link this boundary.
- `docs/portfolio/engineering.md`: repository evidence and CI/CD architecture with truthful
  verification boundaries. Release manifest updated for this stage.

## Architecture decisions
The workflow promotes to **existing** staging apps and registry; it never applies the paid
foundation template. Infrastructure validation is Bicep compilation plus authenticated target
configuration inspection, not a falsely claimed live ARM validation/deployment. Foundation
bootstrap, RBAC grants, database migrations, tenant activation and agent publishing remain
separate approvals. Release images are identified by content digest, not a mutable tag. Rollback
uses a prior manifest pair and a new approved dispatch, never a rebuild or automatic DB downgrade.

GitHub preflight has no Azure identity permission. The environment job cannot log in until
protection, actual independent review and configuration checks pass. GitHub environment setup
is a genuine external prerequisite: read-only inspection found **zero environments**; none was
created or configured. Do not dispatch the staging workflow merely to test missing prerequisites.

## Executed checks and actual results
- Existing hosted `verify.yml` at `7fa651fe0ae94b0b4cb12f842960f8b6f8e4a00a`: **success**, all four jobs.
  https://github.com/keenosmith-del/ms-assessflow/actions/runs/40307827111
- `.venv/bin/pytest -q tests/release`: **33 passed**, all cloud/GitHub responses synthetic.
- `cd backend; ../.venv/bin/pytest -q`: **64 passed, 1 PostgreSQL-only check skipped** on SQLite.
- `TEST_DATABASE_URL=postgresql+psycopg://assessflow:local-only@localhost:55432/assessflow_test ../.venv/bin/pytest -q`
  from backend: **65 passed**, using the separate real PostgreSQL 17 test database.
- `npm run lint`, `npm test`, `npm run build`: **passed**, **6 tests passed**, production build passed.
- `npm run test:e2e`: **3 passed** against the local application, including complete persisted
  request/approval/fulfilment and responsive navigation. Existing evidence images retained;
  no UI changes or unrelated generated screenshots included in this iteration.
- Ruff check/format for backend/scripts/release tests: **passed**.
- Official actionlint **1.7.12** (download checksum verified), both workflow files: **passed**.
- Bicep compiler on `infra/main.bicep`: **passed**, no Azure authentication/provisioning.
- API/connector contract validators and limited tracked-file accidental-secret scan: **passed**.
- The pushed Iteration 008 CI result is recorded in the release manifest after completion;
  no unexecuted hosted job is counted as passed here.

## Not executed / external prerequisites
No staging workflow dispatch, Azure login, OIDC token exchange, ACR publish/lock, authenticated
Azure resource validation, container promotion, staging smoke, rollback or cloud model invocation
was executed. No paid resources, environment variables, GitHub protection rules, identity grants,
credentials or tenant services were created/activated. These require operator configuration,
permissions and independent approval described in the staging runbook.

Local release tests and actionlint establish contract/gate behaviour and workflow syntax, not
live Azure correctness or active environment enforcement. Basic staging smoke does not certify
model quality, employee authentication, Copilot publishing or every worker's running image.
Container updates are sequential; partial failure requires reviewed recovery of the prior pair.

## Git record and outstanding work
Implementation commit: recorded in `release-manifest.md` after commit. All requested local
Iteration 008 work is complete; only environment activation and live staging execution remain
externally gated. No application functionality was rebuilt; no interface redesign or unrelated technology introduced.
