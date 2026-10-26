# Operations, monitoring and recovery
Structured application logs include method, route template, status, latency, correlation ID and
provider mode. Safe errors omit raw exception text and request bodies. Audit records preserve
business transitions and actor IDs; assessments preserve provider, invocation UUID, latency,
returned model token usage and citations. Security denials are visible as structured HTTP status
logs; they are not separate persisted business audit rows. Avoid enabling verbose provider or
access logs containing query strings or signed URLs. Uvicorn startup examples disable access logs.

/health is process liveness; /ready checks DB availability. integrations returns configuration
status, not invented connectivity. Explicit admin probe checks DB, Search and Language in Azure
mode and may incur service usage. Agent workspace is the explicit model invocation probe.
Workflow history is available through /v1/workflows; scheduled expiry is an external operator job.

Azure monitoring path: configure App Service diagnostic settings to an approved Log Analytics
workspace; enable Application Insights/OpenTelemetry with your tenant-approved exporter and
scrubbing rules after review. Correlate application invocation IDs with provider diagnostics as
available. This release does not install an exporter or claim connected distributed traces.
Define alerts for 401/403 bursts, 5xx/provider failures, long assessment durations, expired
workflows and database availability. Review privacy, sampling and log retention before enablement.

Troubleshooting:
- 401: no synthetic identity, wrong token audience/issuer/expiry or missing delegated scope.
- 403: unonboarded oid, wrong DB role, connector client restrictions or missing tool scopes.
- 404 request/policy: record missing or inaccessible; do not infer cross-user existence.
- 409: stale revision, duplicate body/key, terminal state, existing decision or expired approval.
- 503: configured provider/database unavailable; restore integration rather than switching to
  demo in production. Existing committed requests remain intact; failed creations roll back.
- Model refusal/forged citation: entire assessment transaction fails explicitly; fix evidence or
  retry after review. No unvalidated recommendation advances the workflow.
- Incomplete Search ingest: DB may have rolled back while some remote chunks exist; canonical
  validation excludes them. Reindex the committed current versions after repair.
- Lost workflow response: use the same request ID when restarting; remote boundary must deduplicate.

Backup local PostgreSQL with `docker compose exec -T db pg_dump -U assessflow -Fc assessflow >
/path/to/secure-backup.dump` (choose an approved protected path). Restore into a separate empty
DB with pg_restore and validate counts, decisions, policy digests and audit ordering before
switching connections. Azure PostgreSQL point-in-time recovery retention in the foundation is
seven days; test restoration and choose retention/RPO/RTO with the business. No restore drill
against a live cloud backup has occurred. Archive/export retention and WORM audit storage are
organisation-specific enhancements still requiring decisions.
