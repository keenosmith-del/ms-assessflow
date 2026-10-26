# Deployment and rollback runbook
## Local setup (PostgreSQL primary)
From the canonical repository root:
```sh
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
.venv/bin/pip install --no-deps -e backend
docker compose up -d db
cp .env.example backend/.env
```
The example database uses localhost:55432, user assessflow, password local-only; development
only. backend/.env is ignored. Set its CORS_ORIGINS to http://127.0.0.1:5175. Then:
```sh
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.db.seed
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 5050 --no-access-log
```
In a separate terminal:
```sh
cd frontend
npm ci
VITE_API_URL=http://127.0.0.1:5050 npm run dev -- --port 5175
```
Open http://127.0.0.1:5175. Select Jamie → create; Morgan → decide; Sam → fulfil; Alex → audit,
policies and diagnostics. Casey demonstrates finance-policy visibility restrictions. Do not kill
unrelated processes; select another port and update CORS_ORIGINS/VITE_API_URL/E2E_URL together.

Explicit SQLite demo: omit backend/.env or set DATABASE_URL=sqlite:///./assessflow.db. Run the
same Alembic and seed commands. This mode is labelled sqlite-explicit-development in settings.
Full local containers: `docker compose --profile app up --build`. Compose API startup migrates
and seeds demo only; it intentionally binds ports on loopback. Run this after stopping your own
dev servers if those ports are occupied. `docker compose down` retains DB data; `down -v` deletes
only this project's Docker volumes and is reserved for deliberate synthetic-data cleanup.

## Azure foundation (prepared, not deployed)
infra/main.bicep prepares two Linux App Service containers sharing a B1 plan, PostgreSQL flexible
server, Key Vault and app-specific PostgreSQL egress firewall rules. Existing Foundry/model,
Language and Search services are supplied as endpoints rather than duplicated automatically.
Build and publish immutable container tags to an approved registry only after authorisation.
Build frontend with production VITE_API_URL and Entra values; they are public configuration,
not secrets. Configure its CSP connect-src to the intended API/identity domains before production.

1. Obtain approval for costs, region, networking, subscription, licences and tenant permissions.
2. Review infra parameters, unique naming and minimum SKUs. Template compiles locally; compilation
   does not prove resource availability or deployability in a subscription. Use ARM what-if only
   in an authorised environment. The separate manually approved staging workflow updates existing apps only; it does not
   apply this foundation. See [staging workflow](staging-workflow.md).
3. Supply secure postgresPassword from a secret source and deploy reviewed template later.
   API intentionally fails startup until Key Vault secret access and required configuration work.
4. Grant API managed identity Key Vault Secrets User on the vault and AcrPull on private registry;
   web identity gets AcrPull only. Grant narrow provider data-plane permissions per Microsoft setup.
   Identity role assignments are deliberately an explicit operator step, not guessed broad roles.
5. Database firewall allows API outbound addresses only. Use a temporary approved operator address
   or controlled runner to migrate and onboard users; remove temporary access afterwards. For
   enterprise private networking, add VNet/private endpoints and DNS before release; this template
   is a cost-conscious staging foundation with public endpoints and restricted firewall access.
6. Run Alembic as a one-off controlled job with approved DB secret access. Do not run demo seed.
   Bootstrap authorised reference data/users with onboard CLI, create legitimate applications/policies
   via approved catalog management/database change procedure, and index through admin ingest.
7. Configure real Entra redirect/scopes, provider endpoints, model deployment, Search index, runtime
   identities and optional workflow signing boundary. Integrations remain unverified until probes
   and actual workflows are exercised. Follow docs/microsoft/setup.md for Copilot solution creation.
8. Validate /ready, authenticated owner/approver tests, CORS/HTTPS/CSP, real Search/PII/model and
   actual flow callbacks; publish agent only after approval. Record results and monitoring evidence.

## CI/CD
The separate [staging deployment workflow](staging-workflow.md) requires manual dispatch,
a protected environment, independent approval, exact-SHA successful CI and Azure OIDC.
It is implemented but has not been executed or activated.

verify.yml runs backend formatting/lint, tests with PostgreSQL, clean migrations, generated
contract drift, limited secret scan, frontend lint/tests/build/audit, browser workflows, container
builds and Bicep compile. Ordinary CI uses no paid Azure credentials. Live cloud validation is a
separate manual operator gate, not falsely reported by mocks. GitHub-hosted workflow execution
must be observed separately; local equivalents alone do not prove remote CI success.

## Rollback and recovery
Tag immutable release images and retain previous versions. Back up DB before migrations. Redeploy
previous image only if schema-compatible; restore a tested snapshot into a new database when
rollback crosses destructive schema changes. Do not downgrade production without a reviewed
recovery plan. Stop writes during consistency-sensitive restore, verify row counts/decisions,
reindex current policies, reconcile external workflow IDs and then reopen traffic.

## Costs and cleanup
App Service B1 and PostgreSQL incur standing cost; model tokens, Language text, Search service,
registry storage and network/log ingestion add usage charges. No numeric quote is asserted;
use current regional calculators and budget alerts with your actual model/traffic assumptions.
Prefer demo until needed, small initial SKUs, capped model quotas and short log retention. After
an authorised experiment, export necessary DB/solution artifacts, then remove only the dedicated
AssessFlow resource group after approval. Retain required backups and disable flow/channel endpoints
and rotate credentials. No Azure provisioning or paid-service activation was performed here.
