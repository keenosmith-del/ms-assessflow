# Iteration 002 — relational persistence
Objective: reproducible schema and synthetic organisational fixtures.
Implemented: 17 relational tables, versioned migrations, ownership links, unique decisions,
optimistic concurrency version, seed command and environment validation.
Relevant files: backend/app/{core,db,models}, backend/migrations, backend/pyproject.toml.
Decision: PostgreSQL primary; explicit SQLite development database while Docker is unavailable.
Executed: Alembic autogenerate, upgrade, seed, downgrade to base, upgrade, seed on SQLite;
Ruff formatting and lint checks. Results: all succeeded. No PostgreSQL test claim.
Limitations: PostgreSQL verification outstanding; API/lifecycle implementation next.
Commit: see `git log --grep='iteration-002'`; release manifest records hash.
