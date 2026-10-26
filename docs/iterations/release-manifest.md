# Release manifest

Completed implementation iterations (all pushed to existing origin):

| Commit | Stage |
|---|---|
| `d1d1679b513b0984c7a22a517377ca428e299cba` | iteration-001: establish application architecture and tooling |
| `eafcaa396929b8e06659e049de396cd95b59174e` | iteration-002: implement relational persistence and migrations |
| `3a6c14ddd665243ec3efc0d95bddff28b4382940` | iteration-003: implement authorised request workflows and API |
| `7edc5e4c7bc1e354da21d336982a95aa6716924d` | iteration-004: deliver connected operational console and browser workflows |
| `8cea2634279889389ada1611b3648b14bb71bb0e` | iteration-005: harden Microsoft provider contracts and offline evaluations |
| `c579c12301bd681d3de63bee313095b1d585ff79` | iteration-006: prepare Microsoft solution assets and deployment tooling |

Final review implementation hash is added after its commit. This manifest is a verification
record, not a claim that unconfigured Microsoft services were deployed.

Observed GitHub CI: [all four jobs green at c579c12](https://github.com/keenosmith-del/ms-assessflow/actions/runs/40306168810).
Final local verification: backend 65 passed with PostgreSQL; SQLite 64 passed/1 skipped;
frontend 6 passed; browser 3 passed; offline simulation 13/13. Bicep and API/connector validation,
containers, limited secret scan, dependency audits and synthetic backup/restore succeeded.
Container runtime smoke: PostgreSQL readiness 200; unauthenticated session 401; scoped session
works; SPA deep-link 200; CSP header present; installed offline evaluation dataset 13/13;
backend container runs as unprivileged assessflow user. Temporary smoke containers were removed.

No Azure resources, real tenant flows or agent channels were deployed. Remaining configuration,
permissions, licence and live-verification work is in ../HANDOVER.md.
