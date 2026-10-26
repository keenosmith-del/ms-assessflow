# Microsoft integration setup — not live verified
These are operator steps to perform later in an authorised subscription/tenant. They are not
claims of provisioning. SDK versions and official references are recorded in ADR 003.

## Entra ID and delegated sign-in
1. Register a single-tenant AssessFlow API application; set access token version 2. Expose
   `access_as_user`, `Requests.Create`, `Requests.Read` and `Policies.Read` delegated scopes.
2. Register a SPA client. Add exact local and HTTPS production SPA redirect URIs (origin
   only, matching auth.js). Grant API access_as_user delegated permission with required consent.
   Set ENTRA_TENANT_ID, ENTRA_CLIENT_ID (API registration), ENTRA_AUDIENCE (actual aud of API
   v2 tokens, normally API client UUID); set VITE_ENTRA_TENANT_ID, VITE_ENTRA_CLIENT_ID (SPA)
   and VITE_ENTRA_SCOPE=api://API_CLIENT_ID/access_as_user. Rebuild frontend for VITE changes.
3. Onboard object IDs and authorised roles through `python -m app.db.onboard`; manager_id must
   reference the assigned approver. Do not run demo seed against an Azure environment.
4. Production ignores X-Demo-User. Token roles are not trusted. Test expired tokens, wrong
   issuer/audience and cross-user reads with actual tenant tokens before release.
5. For Graph, acquire a separate delegated `User.Read` Graph token using MSAL consent. Supply
   it transiently as X-Graph-Token to /v1/directory/me over HTTPS alongside the API token. The
   returned object ID must match the API identity. It is not persisted. /me selects only ID,
   displayName and department. No directory-wide or group-write permission is required.
   The console does not yet offer a Graph token acquisition button; API boundary is available.

## Foundry and Azure OpenAI
1. After cost approval, create/select a Foundry project and a deployed Azure OpenAI model
   that supports Responses and strict structured outputs in the target region.
2. Set FOUNDRY_PROJECT_ENDPOINT to the project URL ending `/api/projects/PROJECT` and
   AZURE_OPENAI_DEPLOYMENT to its deployment name. Use managed identity on Azure and an
   explicitly authenticated DefaultAzureCredential locally. Grant Foundry project inference
   access at the narrowest supported project/resource scope, confirming current role requirements.
3. The backend creates an ephemeral advisory agent per Responses request; no portal agent
   definition is imported. Instructions and schema are source controlled in assessment.py and
   providers.py. Model receives redacted request text and permitted evidence only, with no tools.
4. In Azure mode, explicit workspace execution invokes real inference. Validate citations,
   refusals, schema handling, latency, usage and trace IDs. Do not label offline evaluation as
   live quality evidence. The stored trace UUID is the application invocation ID, not a claim
   that an Application Insights/Foundry distributed trace has been connected.

## Azure Language PII
Set AZURE_LANGUAGE_ENDPOINT. Grant the runtime identity the service's least required data-plane
role (Cognitive Services User where applicable). Configure PII_CATEGORIES (default Email,
PhoneNumber, USSocialSecurityNumber). recognize_pii_entities returns redacted_text and typed
entity categories. Service logging is disabled per request. Failures stop processing with 503;
no fallback sends raw text to inference. Policies are segmented at 4000 characters; detection
may miss boundary-spanning entities, unconfigured categories or unfamiliar formats. Test your
languages and regional identifiers; this is not a privacy guarantee.

## Azure AI Search
Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_INDEX. Create the schema using the reviewed
`search-index.json` or the configure_search CLI with --apply. Runtime identity needs Search
Index Data Contributor for policy uploads (use a separate indexing identity if split later);
read-only workloads should use Search Index Data Reader. Index administration needs Search
Service Contributor separately. No index is created automatically at application startup.
Fields: id key, version_id, application_id, department filterable, chunk_index integer, content
searchable. Policy ingest writes overlapping text chunks. Old versions can remain in Search,
but canonical DB version/ACL validation removes stale and unavailable content at retrieval.
Use `configure_search --reindex` to repair index drift after schema/ingestion failure. This
version uses keyword search, not hybrid embeddings; no vector claim is made.

## Copilot Studio and Power Platform custom solution
1. Obtain an environment, appropriate maker/solution privileges and a licensing plan that
   covers your intended channels, premium custom connector usage and agent capacity. Actual
   licensing terms/quotas must be checked with your tenant administrator before publishing.
2. Create custom solution AssessFlow with your publisher prefix, environment variables for API
   host/tenant/API application ID, and connection references. Set it as the preferred solution.
3. Register a separate confidential connector OAuth application. Grant only Requests.Create,
   Requests.Read and Policies.Read delegated scopes. Configure the exact redirect URL generated
   by the custom connector; store its client secret in the connector configuration, never Git.
   Set ENTRA_COPILOT_CLIENT_ID to this registration. It cannot call console/admin endpoints.
4. Import copilot/tools/connector.swagger.json as an OpenAPI custom connector definition. Replace
   REPLACE_WITH_API_HOST and REPLACE_TENANT; configure the resource/audience and fully qualified
   scope names (`api://API_CLIENT_ID/Requests.Create`, etc.) in OAuth settings. Validate the
   connector's tenant-specific OAuth settings with real delegated sign-in. Source uses logical
   scope names; the portal configuration must supply full scope URIs. Use end-user connections,
   not a shared maker identity. Ensure Idempotency-Key is a required tool input.
5. Add the four tools to the agent in this custom solution. Apply agent/instructions.md and
   implement topic behaviours in topics.json using the portal authoring model. Require sign-in.
   Policy knowledge is obtained through SearchPermittedPolicies to preserve caller ACLs; do not
   upload restricted policies into a broadly visible agent knowledge collection.
6. Run every prepared conversation in test-conversations.md and capture real tool outputs.
   Export the authentic unmanaged solution from development and managed solution for deployment
   only after portal creation. Store unpacked authentic source/exports in a new versioned folder.
   No native solution or flow export has been fabricated in this repository.
7. Import managed solution into test, bind environment variables and connection references,
   validate DLP policies and channels, obtain publishing approval, then publish and exercise it.

## Human approval flow
Create a solution-aware flow with a secured start boundary matching approval-contract.json.
Verify start HMAC and deduplicate request ID before creating the approval. Assign only the
provided approved manager object ID; obtain responder object ID from the authenticated approval
result (not free text). Require a reason and translate approved/rejected to the exact contract.
A trusted signing boundary must compute HMAC over timestamp + '.' + exact JSON bytes. Standard
flow expressions alone are not assumed to implement HMAC securely. Use approved custom connector
code or an independently secured Azure Function only if your environment needs that boundary;
its production signing implementation and authenticated responder mapping require tenant setup
and validation before external approval callbacks may be trusted. Keep WORKFLOW_CALLBACK_SECRET
in Key Vault/approved connection secrets and set WORKFLOW_START_URL to the approved HTTPS endpoint.
No flow invocation occurs automatically; an administrator explicitly POSTs /workflows/{id}/start.
Schedule an authorised maintenance call to /workflows/maintenance/expire and route escalation to
service administrators. Notifications are the flow's responsibility and have not been sent here.
The same shared-secret signing protocol must never be exposed to the conversational agent.

## Live verification checklist
Tenant token validation; two-user ACL checks; actual PII categories; index schema and reindex;
model schema/refusal/citation checks; actual flow identity/signature/replay/expiry; authentic
solution export/import; published channel transcript; diagnostics and cost alerts. All remain
unverified until performed with authorised cloud resources and licences.
