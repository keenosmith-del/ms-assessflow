# Iteration 005 — provider contracts, evaluation and security
Objective: validate Microsoft boundaries and harden deterministic controls.
Implemented: Foundry structured outputs with model usage, Azure Language PII, Search ACL and
version checks, read-only Graph, workflow start/expiry/renewal, restricted employee tools,
JWT checks, body limits and a 13-case isolated offline evaluation runner.
Relevant files: backend/app/{agents,integrations,security,api}, backend/tests, ADR 003.
Decisions: stable SDKs verified against Microsoft references; no cloud fallback; keyword
retrieval initially; no preview connector or unnecessary Azure Functions dependency.
Executed: 60 backend tests passed against real PostgreSQL (including concurrent duplicate
creation and decision). Of these, 13 evaluation cases deliberately use isolated SQLite.
SQLite-only run: 59 passed, 1 PostgreSQL concurrency check skipped. Ruff passed.
PostgreSQL: clean Alembic upgrade/seed/downgrade/upgrade passed before expanded suite.
Results: simulated dataset 13/13; provider failure, forged evidence, expired approval,
invalid issuer/audience/signature/scope and PII handling covered. No live model evaluation.
Limitations: cloud services/tenant unavailable; native Power Platform solution creation pending.
Outstanding: connector assets, full operating documentation, containers/CI/IaC and final review.
Commit: see `git log --grep='iteration-005'`; release manifest records hash.
