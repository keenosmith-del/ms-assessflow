# AssessFlow

A working enterprise IT service desk and access governance application. Employees submit
application access requests; policy evidence informs a structured advisory assessment; an
authorised human approves or rejects; service operators record verified manual fulfilment.
AI cannot grant permissions or mark access fulfilled.

The local system includes a React operational console, FastAPI API, PostgreSQL persistence,
Alembic migrations, policy versions/retrieval, approvals, audit trails, an offline evaluation
suite and real Microsoft adapter code. Demo mode is explicitly synthetic. Azure mode fails
closed without Entra/provider configuration and never silently substitutes demo success.

**Status:** locally implemented and verified; cloud/tenant integration prepared, not deployed
or live verified. See [handover](docs/HANDOVER.md), [test results](docs/testing/results.md) and
[Microsoft setup](docs/microsoft/setup.md). No billable Azure resources were provisioned.

Canonical checkout: `/Users/keenosmith/Programming/Projects/ms-assesflow` (historical spelling).
Remote/project name is `ms-assessflow`. Only the existing repository was used.

## Start locally

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
.venv/bin/pip install --no-deps -e backend
docker compose up -d db
```

Backend terminal, from repository root:

```sh
cd backend
DATABASE_URL=postgresql+psycopg://assessflow:local-only@localhost:55432/assessflow ../.venv/bin/alembic upgrade head
DATABASE_URL=postgresql+psycopg://assessflow:local-only@localhost:55432/assessflow ../.venv/bin/python -m app.db.seed
DATABASE_URL=postgresql+psycopg://assessflow:local-only@localhost:55432/assessflow CORS_ORIGINS=http://127.0.0.1:5175 ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 5050 --no-access-log
```

Frontend terminal, from repository root:

```sh
cd frontend
npm ci
VITE_API_URL=http://127.0.0.1:5050 npm run dev -- --port 5175
```

Open [the console](http://127.0.0.1:5175) and select a synthetic identity. Jamie submits finance
requests; Morgan reviews; Sam fulfils; Alex administers; Casey demonstrates policy ACL limits.
API docs: [Swagger UI](http://127.0.0.1:5050/docs). If a port is occupied, choose another and update
the environment; do not stop unrelated applications. Explicit SQLite and full container setup
are described in the [deployment runbook](docs/deployment/runbook.md).

## Architecture and capabilities

React/Router/plain CSS/native Fetch → FastAPI/Pydantic → SQLAlchemy/Alembic/PostgreSQL. The
backend owns authorisation, transactional state, audit and idempotency. The specialist agent
redacts text, retrieves permitted evidence and produces a validated advisory assessment.
Copilot Studio is a separate employee agent integrated through a restricted OAuth connector;
it is not imitated by the web management interface.

- Nine connected pages: dashboard, requests, detail, approvals, policies, agent workspace,
  audit, integrations/settings and sign-in.
- Missing-information continuation, rejection/cancellation, unique decisions, self-approval
  prevention, expiring workflows, manual fulfilment evidence and persisted timelines.
- Versioned UTF-8 policy uploads, chunk/digest inspection, department ACLs and citation provenance.
- Azure adapters: Foundry Responses/Azure OpenAI, Language PII, AI Search keyword retrieval;
  Entra JWT validation/MSAL sign-in; Graph delegated read-only /me; signed workflow callbacks.
- Copilot implementation instructions, typed connector contract and human approval flow spec.
- Structured logs, correlation IDs, live/configured/local provider labels and explicit probes.

Actual live provider execution requires authorised credentials, service access and cost approval.
Hybrid vector retrieval, Azure Functions, external notifications and directory permission writes
are not represented as implemented. There is no live model quality score or published agent.

## Verification

```sh
.venv/bin/ruff check backend scripts
.venv/bin/ruff format --check backend scripts
cd backend
../.venv/bin/pytest -q
../.venv/bin/python -m app.agents.evaluate
cd ../frontend
npm run lint
npm test
npm run build
npm run test:e2e
```

For the PostgreSQL concurrency test, create a separate disposable assessflow_test database and
set TEST_DATABASE_URL; fixtures destroy/recreate mapped tables. Never target the operational DB.
See [test strategy](docs/testing/strategy.md) for exact commands and browser prerequisites.
CI runs migrations, tests, builds, contract validation, a limited secret scan and Bicep compile
without paid Azure credentials. Live tenant checks remain an explicit deployment gate.

## Repository

```text
frontend/src/       Page folders with matching JSX/CSS, shared components, session and Fetch API
backend/app/        API, schemas, models, workflow/policy services, security, agents and adapters
backend/migrations/ Versioned relational migrations
backend/tests/      Unit, integration, contract, security and evaluation checks
copilot/            Employee agent source assets, connector and approval flow specification
infra/              Compilable Azure Bicep staging foundation; nothing provisioned
scripts/            Contract generation/validation, runtime lock and limited secret checks
docs/               Product, architecture, decisions, security, tests, operations and iterations
.github/workflows/  CI verification, no automatic production deployment
```

Known engineering limits and exact remaining Azure/Copilot actions are in the
[handover](docs/HANDOVER.md) and [threat model](docs/security/threat-model.md).
