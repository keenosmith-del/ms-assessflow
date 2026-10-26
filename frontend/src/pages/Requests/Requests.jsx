import { useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, Search, X } from "lucide-react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../services/api";
import {
  PageHeading,
  Panel,
  Field,
  DataState,
  Notice,
} from "../../components/ui/UI";
import RequestTable from "../../components/requests/RequestTable";
import "./Requests.css";
export default function Requests() {
  const [params, setParams] = useSearchParams(),
    [query, setQuery] = useState(""),
    [status, setStatus] = useState(""),
    [offset, setOffset] = useState(0),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [appId, setAppId] = useState("finance-reports");
  const key = useRef(null);
  const apps = useApi("/v1/applications"),
    requests = useApi(
      `/v1/requests?q=${encodeURIComponent(query)}&status=${status}&offset=${offset}&limit=20`,
    );
  const opened = params.has("new");
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    key.current ||= crypto.randomUUID();
    try {
      await api("/v1/requests", {
        method: "POST",
        body: Object.fromEntries(form),
        key: key.current,
      });
      key.current = null;
      setParams({});
      requests.refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="OPERATIONS / REQUESTS"
        title="Request workspace"
        description="Submit, review, and track application access in one place."
      >
        <button
          className="primary"
          onClick={() => {
            setParams({ new: "1" });
            key.current = null;
          }}
        >
          <Plus size={16} />
          New request
        </button>
      </PageHeading>
      {opened && (
        <Panel
          title="Submit an access request"
          aside={
            <button
              className="icon-button"
              aria-label="Close form"
              onClick={() => setParams({})}
            >
              <X size={18} />
            </button>
          }
        >
          <form
            className="panel-body form-grid"
            onSubmit={submit}
            onChange={() => {
              key.current = null;
            }}
          >
            <Field label="Application">
              <select
                name="application_id"
                value={appId}
                onChange={(e) => setAppId(e.target.value)}
              >
                {apps.data?.items.map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Access level">
              <select name="access_level">
                {apps.data?.items
                  .find((x) => x.id === appId)
                  ?.levels.map((x) => (
                    <option key={x}>{x}</option>
                  ))}
              </select>
            </Field>
            <div className="full-width">
              <Field label="Business justification">
                <textarea
                  name="justification"
                  rows={3}
                  maxLength={4000}
                  placeholder="Explain why this access is needed. Missing details can be supplied later."
                />
              </Field>
            </div>
            <p className="subtle full-width">
              Your request is saved before clarification. A human decision is
              always required.
            </p>
            {error && (
              <div className="full-width">
                <Notice>{error}</Notice>
              </div>
            )}
            <div>
              <button className="primary" disabled={busy || !apps.data}>
                {busy ? "Submitting…" : "Submit request"}
              </button>
            </div>
          </form>
        </Panel>
      )}
      <section className="request-list">
        <div className="filter-bar">
          <label className="search-box">
            <Search size={16} />
            <input
              aria-label="Search requests"
              placeholder="Search requests, applications…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <select
            aria-label="Filter request status"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All statuses</option>
            {[
              "awaiting_information",
              "pending_approval",
              "provisioning_pending",
              "fulfilled",
              "rejected",
              "cancelled",
            ].map((x) => (
              <option key={x} value={x}>
                {x.replaceAll("_", " ")}
              </option>
            ))}
          </select>
          <span className="subtle">
            {requests.data?.items.length || 0} on this page
          </span>
        </div>
        <Panel title="Requests">
          <DataState loading={requests.loading} error={requests.error}>
            <RequestTable items={requests.data?.items} />
          </DataState>
        </Panel>
        <div className="pagination">
          <button disabled={!offset} onClick={() => setOffset((v) => v - 20)}>
            Previous
          </button>
          <button
            disabled={(requests.data?.items.length || 0) < 20}
            onClick={() => setOffset((v) => v + 20)}
          >
            Next
          </button>
        </div>
      </section>
    </>
  );
}
