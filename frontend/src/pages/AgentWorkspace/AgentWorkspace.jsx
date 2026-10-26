import { useState } from "react";
import { Play } from "lucide-react";
import { api } from "../../services/api";
import {
  PageHeading,
  Panel,
  Field,
  Notice,
  Badge,
} from "../../components/ui/UI";
import "./AgentWorkspace.css";
export default function AgentWorkspace() {
  const [result, setResult] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function run(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await api("/v1/agent/assess", {
          method: "POST",
          body: Object.fromEntries(new FormData(e.currentTarget)),
        }),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="AI ENGINEERING / INSPECT"
        title="Policy analysis workspace"
        description="Inspect structured advisory output. This diagnostic tool cannot grant access."
      />
      <div className="agent-columns">
        <Panel title="Assessment input">
          <form className="panel-body stack" onSubmit={run}>
            <Field label="Application">
              <select name="application_id">
                <option value="finance-reports">Financial Reporting</option>
                <option value="service-desk">Service Desk</option>
              </select>
            </Field>
            <Field label="Requested access">
              <select name="access_level">
                <option>reader</option>
                <option>analyst</option>
              </select>
            </Field>
            <Field label="Business justification">
              <textarea
                name="justification"
                rows={6}
                maxLength={4000}
                defaultValue="Quarterly finance reporting and reconciliation"
              />
            </Field>
            <button className="primary" disabled={busy}>
              <Play size={15} />
              {busy ? "Analysing…" : "Run assessment"}
            </button>
            <p className="subtle">
              Uses the signed-in identity and the configured provider. Azure
              mode invokes live services.
            </p>
          </form>
        </Panel>
        <Panel title="Actual execution output">
          <div className="panel-body">
            {error && <Notice>{error}</Notice>}
            {result ? (
              <>
                <div className="assessment-meta">
                  <Badge status={result.output.recommendation} />
                  <span>
                    {result.provider} · {result.latency_ms}ms
                  </span>
                </div>
                <p className="body-copy">{result.output.explanation}</p>
                <p className="subtle">{result.output.uncertainty}</p>
                <pre className="json-output">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </>
            ) : (
              <div className="agent-empty">
                Run an assessment to inspect evidence, validation results,
                provider mode and trace ID.
              </div>
            )}
          </div>
        </Panel>
      </div>
    </>
  );
}
