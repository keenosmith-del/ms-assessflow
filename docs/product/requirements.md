# Product requirements and acceptance
AssessFlow unifies application access intake, policy interpretation, human approval and
service-team fulfilment. It is an internal access governance system, not a directory writer.

| Role | Journey | Acceptance |
|---|---|---|
| Employee | Submit → clarify → track → comment/cancel | Own records only; clarification preserves request ID |
| Approver | Assigned queue → inspect evidence → approve/reject | Reason required; no self-approval; one decision |
| Operator | Approved queue → manual service task → record reference | No fulfilment without an approved task |
| Administrator | Policies, audit, diagnostics, workflow maintenance | Server checks role; model cannot obtain role |

Nine console screens: dashboard, requests, detail, approvals, policy library, agent diagnostics,
audit, integrations/settings and sign-in. Dashboard values derive from visible persisted records.
Recent activity is the request list and audit/timeline, not generated sample counters.

Workflow A: valid request obtains current permitted policy evidence, assessment and manager review.
Workflow B: short/empty justification preserves a request in awaiting_information; requester
supplies clarification through the same ID. Workflow C: unavailable/expired/department-ineligible
policy produces manual_review, requiring a human exception decision. Workflow D: assigned manager
or administrator decides with a reason. Workflow E: status tools read persisted state. Workflow F:
negative authorisation, replay, injection, privacy and transition checks run automatically.

Functional requirements are implemented in API and web pages; employee tool contracts expose
only create/status/clarify/search. Policies support UTF-8 plain text upload, version history,
chunk inspection and ACL-controlled retrieval. Unsupported file types are explicitly rejected
by the upload interface; the API accepts text content, not arbitrary file blobs.

Nonfunctional requirements: schema-validated inputs; bounded bodies; transactional state and
audit records; idempotency; optimistic concurrency; page-scoped files; reproducible environments;
cloud calls fail explicitly; production cannot enable demo authentication. Local measurements
are in docs/testing. There is no production availability or throughput SLA yet.

Acceptance excludes tenant publishing until authorised tenant configuration exists. Remote
service connectivity, live model groundedness, target-region capacity, accessibility certification,
load capacity and organisation-specific retention rules remain release validation tasks.
