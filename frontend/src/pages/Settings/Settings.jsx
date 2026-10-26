import { useState } from "react";
import { Plug, Activity } from "lucide-react";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../context/SessionContext";
import { api } from "../../services/api";
import { PageHeading, Panel, DataState, Notice } from "../../components/ui/UI";
import "./Settings.css";
export default function Settings() {
  const state = useApi("/v1/integrations"),
    { user } = useSession(),
    [probe, setProbe] = useState(null),
    [error, setError] = useState("");
  async function check() {
    setError("");
    try {
      setProbe(await api("/v1/integrations/probe", { method: "POST" }));
    } catch (e) {
      setError(e.message);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="WORKSPACE / INTEGRATIONS"
        title="Connected with intention."
        description="Provider configuration, operating mode, and Microsoft deployment readiness."
      />
      <DataState loading={state.loading} error={state.error}>
        {state.data && (
          <>
            <div className="settings-summary">
              <div>
                <span>Operating mode</span>
                <strong>{state.data.mode}</strong>
              </div>
              <div>
                <span>Environment</span>
                <strong>{state.data.environment}</strong>
              </div>
              <div>
                <span>Persistence</span>
                <strong>{state.data.database}</strong>
              </div>
            </div>
            <div className="integration-grid">
              {state.data.providers.map((x) => (
                <Panel key={x.name} title={x.name} aside={<Plug size={16} />}>
                  <div className="panel-body">
                    <h3>{x.provider}</h3>
                    <span className="integration-status">{x.status}</span>
                    <p className="subtle">
                      {x.status === "local-only"
                        ? "Working locally with synthetic data. No cloud execution is represented."
                        : "Configuration is present. Use an explicit probe to check connectivity."}
                    </p>
                  </div>
                </Panel>
              ))}
            </div>
            <div className="settings-bottom">
              <Panel title="Microsoft solution readiness">
                <div className="panel-body">
                  <p className="body-copy">{state.data.copilot}</p>
                  <p className="subtle">Workflow: {state.data.workflow}</p>
                  <p className="subtle">
                    Foundry, Search, Language, Entra, and Copilot Studio require
                    your authorised Azure and Power Platform configuration.
                    Setup instructions are versioned in docs/microsoft.
                  </p>
                </div>
              </Panel>
              <Panel title="Connectivity probe">
                <div className="panel-body">
                  <p className="subtle">
                    Azure probes call Search and Language and may incur service
                    usage. Foundry is tested explicitly in the agent workspace.
                  </p>
                  {user.role === "admin" && (
                    <button className="secondary" onClick={check}>
                      <Activity size={15} />
                      Run explicit probe
                    </button>
                  )}
                  {error && <Notice>{error}</Notice>}
                  {probe && (
                    <pre className="json-output">
                      {JSON.stringify(probe, null, 2)}
                    </pre>
                  )}
                </div>
              </Panel>
            </div>
          </>
        )}
      </DataState>
    </>
  );
}
