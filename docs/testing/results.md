# Measured verification — 26 October 2026

| Check | Actual observed result |
|---|---|
| Backend suite, explicit SQLite | 64 passed; 1 PostgreSQL concurrency check skipped |
| Backend suite, real PostgreSQL 17 | 65 passed, including concurrent duplicate creation/decisions |
| Offline assessment/workflow evaluation | 13/13 passed; no live model invoked |
| Frontend Vitest | 6 passed |
| Browser Chrome/Playwright | 3 passed against PostgreSQL-backed API; desktop + 390px mobile |
| Backend Ruff check/format | Passed |
| Frontend ESLint + Vite production build | Passed |
| Full OpenAPI 3.1 and connector Swagger 2 validation | Both passed |
| Alembic clean upgrade → seed → downgrade → upgrade | Passed on SQLite and PostgreSQL |
| Python environment consistency | pip check: no broken requirements |
| npm dependency advisory scan | 0 reported vulnerabilities after test-tool updates |
| Python pip-audit | No known vulnerabilities found; report python-audit.json |
| Limited tracked-file secret scan | Passed; not a comprehensive secret-detection guarantee |
| Bicep local compile | Passed, no errors/warnings; no Azure deployment |
| API + web container builds | Both passed locally; readiness/auth/SPA/CSP smoke and packaged 13-case evaluation passed |
| Synthetic PostgreSQL backup/restore | pg_dump/pg_restore succeeded; requests/decisions/audit counts matched: 6/2/41 |
| GitHub Actions at 2b93b5f | All four jobs succeeded: backend, frontend, browser, containers |

Remote run: https://github.com/keenosmith-del/ms-assessflow/actions/runs/40307549004
This result refers to implementation commit 2b93b5f; the subsequent documentation-only commit
records its hashes and results without changing executable source.

Executed backend commands from backend:
```sh
../.venv/bin/pytest -q
TEST_DATABASE_URL=postgresql+psycopg://assessflow:local-only@localhost:55432/assessflow_test ../.venv/bin/pytest -q
../.venv/bin/python -m app.agents.evaluate
```
The PostgreSQL run includes 13 intentionally isolated SQLite evaluation cases plus the remaining
unit/API/security/integration tests. It is not a claim that every test performs a PostgreSQL query.
Concurrency tests specifically require PostgreSQL and are skipped in the SQLite-only run.

Frontend: npm run lint, npm test, npm run build, npm run test:e2e. Browser coverage includes
create/approve/fulfil/reload/audit, administrator navigation, actual deterministic agent output,
missing-information continuation and HTML form validation. Screenshot assets reflect real
local pages. Discovered overflow, ambiguous test locators and preflight rate-limit accounting
were corrected and the suite rerun successfully. Repeated test runs should use a clean dedicated
API process so they do not share an already-consumed per-IP limit.

Not executed live: Microsoft tenant sign-in/JWKS, Foundry/Azure OpenAI inference, Azure Language,
Azure Search, Graph, Power Automate, Copilot solution import/export/publish, Azure resource
provisioning, Application Insights. Adapter mocks and local RSA tests do not establish live
provider connectivity. No cloud model groundedness, production capacity, penetration test or
certified accessibility score is claimed. Current official references and installed SDK versions
are recorded in docs/decisions/003-microsoft-contracts.md.
