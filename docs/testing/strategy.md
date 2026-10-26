# Verification strategy
Run checks from repository root unless shown otherwise. Python environment: .venv, Python 3.12.

```sh
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
cd backend
../.venv/bin/pytest -q
../.venv/bin/python -m app.agents.evaluate
cd ../frontend
npm run lint
npm test
npm run build
npm run test:e2e
```

For PostgreSQL, start `docker compose up -d db` then set
TEST_DATABASE_URL=postgresql+psycopg://assessflow:local-only@localhost:55432/assessflow for pytest.
THIS DATABASE IS DESTRUCTIVE TEST STORAGE: fixtures drop and recreate mapped tables. Never
point TEST_DATABASE_URL at a real operational database. The isolated evaluation runner uses
SQLite deliberately and never calls Azure, including during the PostgreSQL suite.

Browser tests require API on 5050 and console on 5175, with CORS permitting
http://127.0.0.1:5175 and VITE_API_URL=http://127.0.0.1:5050. On local macOS Playwright uses
installed Chrome; CI installs Chromium. E2E_URL overrides base URL. Run with synthetic seeded
data. Requests are real persisted fixtures created through the browser. Screenshots in this
folder are captured from real pages; mobile checks enforce no document-level horizontal overflow.

Offline evaluation dataset: backend/tests/evaluations/cases.json. Critical criteria: no automatic
fulfilment, no unauthorised requester, missing evidence/expired/conflict/injection routes to
manual review, valid evidence citation present, missing fields preserve state, duplicate keys
preserve ID. Report is offline-evaluation.json. This measures deterministic contracts and
exact citations, not semantic model groundedness. Live model quality must measure evidence
relevance, groundedness, citation fidelity, escalation, refusal, latency, returned token usage
and deployment-specific estimated cost separately. No live quality score is invented.

Tests cover unit adapters, real SDK interface invocation with mocks, API contracts, persistence,
RBAC, callback signing, expiry/replay, body limits, token cryptography, state transitions and
PostgreSQL concurrency. Tests do not establish cloud connectivity or real OAuth redirects.
Final observed results and unexecuted checks are recorded in results.md.
