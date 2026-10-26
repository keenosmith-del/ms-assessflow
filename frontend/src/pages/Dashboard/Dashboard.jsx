import { Link } from "react-router-dom";
import {
  Plus,
  ArrowRight,
  Files,
  Clock3,
  ShieldAlert,
  Timer,
  CircleCheck,
  ShieldCheck,
} from "lucide-react";
import { useApi } from "../../hooks/useApi";
import { PageHeading, DataState, Panel } from "../../components/ui/UI";
import RequestTable from "../../components/requests/RequestTable";
import "./Dashboard.css";
export default function Dashboard() {
  const metrics = useApi("/v1/metrics"),
    requests = useApi("/v1/requests?limit=5"),
    integrations = useApi("/v1/integrations");
  const m = metrics.data;
  return (
    <>
      <PageHeading
        eyebrow="OPERATIONS / OVERVIEW"
        title="Access, with accountability."
        description="A clear view of your requests, decisions, and the policies behind them."
      >
        <Link className="button primary" to="/requests?new=1">
          <Plus size={16} />
          New request
        </Link>
      </PageHeading>
      <div className="overview-banner">
        <div className="banner-symbol">
          <ShieldCheck size={24} />
        </div>
        <div>
          <strong>Every decision has a paper trail.</strong>
          <p>
            AI brings the evidence. People make the call. Your access stays
            governed.
          </p>
        </div>
        <span className="banner-label">HUMAN APPROVAL REQUIRED</span>
      </div>
      <DataState loading={metrics.loading} error={metrics.error}>
        {m && (
          <div className="metrics-grid">
            {[
              [
                Files,
                "Total requests",
                m.total,
                "Across your visible workspace",
              ],
              [
                Clock3,
                "Awaiting approval",
                m.counts.pending_approval || 0,
                "Ready for a human decision",
              ],
              [
                ShieldAlert,
                "Open exceptions",
                m.exceptions,
                "Require additional review",
              ],
              [
                Timer,
                "Avg. processing",
                m.average_processing_seconds === null
                  ? "—"
                  : `${Math.round(m.average_processing_seconds / 60)}m`,
                "Created to recorded fulfilment",
              ],
            ].map(([Icon, label, value, note]) => (
              <div className="metric" key={label}>
                <div className="metric-label">
                  {label}
                  <Icon size={16} />
                </div>
                <strong>{value}</strong>
                <small>{note}</small>
              </div>
            ))}
          </div>
        )}
      </DataState>
      <div className="dashboard-columns">
        <div className="stack">
          <Panel
            title="Recent requests"
            aside={
              <Link className="text-link" to="/requests">
                View all <ArrowRight size={13} />
              </Link>
            }
          >
            <DataState loading={requests.loading} error={requests.error}>
              <RequestTable items={requests.data?.items} />
            </DataState>
          </Panel>
          <div className="governance-strip">
            <CircleCheck size={20} />
            <div>
              <strong>Controlled from request to fulfilment</strong>
              <p>
                Identity checks · Policy evidence · Human approval · Complete
                audit history
              </p>
            </div>
          </div>
        </div>
        <div className="stack">
          <Panel
            title="Provider status"
            aside={<span className="mini-label">CURRENT MODE</span>}
          >
            <DataState
              loading={integrations.loading}
              error={integrations.error}
            >
              <div className="provider-list">
                {integrations.data?.providers.map((provider) => (
                  <div key={provider.name}>
                    <span className="provider-dot" />
                    <div>
                      <strong>{provider.name}</strong>
                      <small>{provider.provider}</small>
                    </div>
                    <span className="local-tag">
                      {provider.status === "local-only" ? "LOCAL" : "CONFIG"}
                    </span>
                  </div>
                ))}
              </div>
              <Link className="panel-bottom-link" to="/settings">
                Integration details <ArrowUpRightIcon />
              </Link>
            </DataState>
          </Panel>
          <section className="note-card">
            <span className="eyebrow">ENGINEERING NOTE</span>
            <h3>
              Evidence first.
              <br />
              Always.
            </h3>
            <p>
              Inspect the policy citations and deterministic checks behind every
              assessment.
            </p>
            <Link to="/policies">
              Explore policy library <ArrowRight size={14} />
            </Link>
          </section>
        </div>
      </div>
    </>
  );
}
function ArrowUpRightIcon() {
  return <ArrowRight size={14} />;
}
