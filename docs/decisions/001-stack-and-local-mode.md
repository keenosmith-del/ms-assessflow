# ADR 001 — stack, local execution and naming
Keep the existing ms-assesflow checkout and Git root; product and remote repository name are
AssessFlow/ms-assessflow. No sibling project was touched. Use FastAPI/Pydantic and SQLAlchemy
with Alembic; PostgreSQL primary. Explicit SQLite offers portable demonstrations. The integration
suite can target a disposable real PostgreSQL database and includes concurrency checks.
React JSX/Vite/Router, plain CSS and native Fetch implement the operational console. No chat
screen impersonates Copilot Studio. Local assessment is deterministic and labelled offline.
Database state, decisions and fulfilment always remain independent from model recommendations.

# ADR 002 — security and deployment boundary
Entra delegated tokens establish identity; database roles and resource ownership enforce access.
Provisioning is manual and recorded by operators. No Graph directory modification permission is
requested. Production requires Azure mode, PostgreSQL, complete provider/Entra configuration and
HTTPS CORS origins. Azure Functions adds no useful independent event boundary in this version:
the signed workflow callback is in FastAPI. Add Functions only when independently scaling or
isolating ingress becomes an actual requirement.
