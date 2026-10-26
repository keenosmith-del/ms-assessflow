# Iteration 003 — transactional workflows and API
Objective: complete persisted request/approval/fulfilment loop.
Implemented: request APIs, clarification, scoped listing/detail, manual decisions, fulfilment,
comments, policy versioning/search, metrics, audit, callback HMAC and provider boundaries.
Relevant files: backend/app/{api,services,schemas,security,agents,integrations}, backend/tests.
Decisions: advisory AI only; immutable decisions; optimistic revisions plus row locks; server ACLs.
Executed: Pytest (25 passed); Ruff check/format; SQLite migration cycle in previous stage.
Results: complete lifecycle, missing information, duplicate keys, cross-user access, self-approval,
policy ACL, injection flagging, privacy redaction, signed replay-safe callbacks verified offline.
Limitations: cloud adapters present but not live verified; PostgreSQL concurrency still requires verification.
Outstanding: UI, expanded provider/evaluation tests, Microsoft setup and deployment assets.
Git commit hash: `3a6c14d` (implementation stage; this record receives later verification updates).
