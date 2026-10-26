# ADR 003 — Microsoft API boundaries (checked 2026-10-26)

Use the stable `azure-ai-projects` package (installed 2.9.0) and its
`AIProjectClient.get_openai_client()` Responses interface. The advisory agent definition
ships in application instructions; no persisted Foundry agent resource is required.
OpenAI SDK installed 3.37.0 supports `responses.parse(text_format=PydanticModel)`.
No tool definitions are supplied to this specialist. Output is validated, citations are
checked against supplied evidence and deterministic failures override recommendations.
Usage metadata is recorded when returned. Cost is unmeasured without deployment pricing.

References reviewed:
- https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
- https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview
- https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-mar-2026/

The stable 2.x SDK targets the v1 project surface; no beta-only dependency is selected.
Use the authenticated backend connector instead of depending on direct Copilot-to-Foundry
agent interoperability. Recheck release support in the target region before deployment.

Language uses stable `azure-ai-textanalytics` 5.4.0, synchronous TextAnalyticsClient
recognize_pii_entities, configured categories and disable_service_logs. Empty strings skip
the cloud call. Long policies are split into 4000 character segments; boundary-spanning
PII and missed entity types remain privacy limitations.
- https://learn.microsoft.com/en-us/azure/ai-services/language-service/personally-identifiable-information/overview
- https://learn.microsoft.com/en-us/python/api/azure-ai-textanalytics/azure.ai.textanalytics.textanalyticsclient

Search uses stable `azure-search-documents` 11.6.0, SearchClient upload/search with a
server-built department filter and a second canonical-version/ACL check. Keyword search
is selected for the small corpus to avoid an unnecessary embedding dependency and cost.
Hybrid retrieval is supported by Azure but is not implemented or claimed here. Introduce
vectors only after measuring retrieval misses and choosing one embedding model/index schema.
- https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview

Graph uses the documented v1.0 REST interface through httpx, only delegated /me User.Read.
Caller acquires a separate Graph token through MSAL; API access tokens are never reused.
- https://learn.microsoft.com/en-us/graph/best-practices-graph-permission

Copilot uses a custom Power Platform solution and OAuth custom connector. The four
restricted tools are source contracts, not native solution exports. Connector knowledge
as preview is not a dependency; policy questions use the authenticated search tool.
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-solutions-overview
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-connectors
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/generative-orchestration

Contract tests use mocks and SDK signature inspection. None of these cloud calls have
been exercised with real tenant credentials in this checkout.
