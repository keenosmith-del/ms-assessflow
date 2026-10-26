# AssessFlow engineering evidence

AssessFlow demonstrates a complete local request-governance workflow and a source-controlled
CI/CD boundary for future Azure staging releases. The operational features are already implemented;
Iteration 008 adds release engineering without rebuilding the application.

| Competency | Concrete repository evidence | Verification boundary |
|---|---|---|
| GitHub Actions CI | `.github/workflows/verify.yml`, README live status badge | Real successful hosted runs; exact links in iteration records |
| PostgreSQL integration | PostgreSQL 17 service in CI; Alembic upgrade/seed/downgrade; backend workflow/security/concurrency tests | Real database suite, not a substituted SQLite compatibility claim |
| Browser automation | Playwright employee → approver → service operator flow, persisted reload, navigation/mobile checks | Actual Chrome locally and Chromium on GitHub runners |
| Docker | API/web Dockerfiles, runtime dependency lock, Compose; CI image builds | Local and CI builds/smoke; no Azure image publication claimed |
| Security | JWT signature/issuer/audience tests, RBAC/ownership, callback replay/expiry, body limits; secret scan and npm audit | Automated local/CI checks; no production penetration-test claim |
| Azure release engineering | Separate manual staging workflow, GitHub Environments, independent review checks, OIDC, SHA CI gate, locked digest images, rollback artifacts | Implemented and tested with synthetic adapter responses; deployment not executed |
| Infrastructure | Compiled Bicep foundation; release script checks existing staging configuration | Local/CI compilation is verified; Azure provisioning/target checks await credentials |

CI builds and tests ordinary pushes/PRs without Azure credentials. CD is a separate manual
operation that first requires the exact SHA's green CI, then an independently approved staging
environment. The approved job authenticates with short-lived OIDC, captures a rollback pair,
builds/publishes immutable images, updates only existing apps, runs limited smoke tests and
preserves release evidence. Failed releases require a fresh reviewed rollback; no database
migration or paid resource provisioning is hidden inside deployment.

See [CI/CD diagram and operator prerequisites](../deployment/staging-workflow.md),
[measured application tests](../testing/results.md), [Iteration 008](../iterations/iteration-008.md)
and [release history](../iterations/release-manifest.md). Copilot Studio, Foundry/Azure OpenAI,
Language, Search, Graph and real tenant authentication remain awaiting authorised activation
and live verification. A green CI badge says nothing about those services being deployed.
