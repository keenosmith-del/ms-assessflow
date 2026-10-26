# AssessFlow engineering conventions
Canonical checkout is ms-assesflow (historical spelling); product name is AssessFlow.
Use Python 3.12+, FastAPI, SQLAlchemy, React JSX, plain CSS, native Fetch.
Each page has a matching folder, JSX and CSS. Keep providers behind typed boundaries.
Never let model recommendations mutate permissions or approve requests. Enforce RBAC,
ownership, transitions and idempotency on the server. Cloud failures must fail explicitly.
Use only synthetic fixtures. Never commit secrets or call billable services without approval.
Run backend pytest and Ruff, frontend tests/lint/build, and relevant browser checks.
Record verified iterations in docs/iterations and commit each completed stage. Push only when the user has authorised it in the current work.
Keep implementation status and unverified external dependencies explicit in documentation.
