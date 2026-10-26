import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import {
  PageHeading,
  Panel,
  DataState,
  Empty,
  titleCase,
} from "../../components/ui/UI";
import "./Audit.css";
export default function Audit() {
  const [actor, setActor] = useState(""),
    [request, setRequest] = useState(""),
    [offset, setOffset] = useState(0),
    state = useApi(
      `/v1/audit?actor=${encodeURIComponent(actor)}&request_id=${encodeURIComponent(request)}&offset=${offset}&limit=30`,
    );
  return (
    <>
      <PageHeading
        eyebrow="GOVERNANCE / AUDIT"
        title="An accountable history."
        description="Persisted events across requests, assessments, decisions, and fulfilment."
      />
      <div className="audit-filters">
        <input
          aria-label="Filter actor"
          placeholder="Filter by exact actor ID"
          value={actor}
          onChange={(e) => {
            setActor(e.target.value);
            setOffset(0);
          }}
        />
        <input
          aria-label="Filter request ID"
          placeholder="Filter by exact request ID"
          value={request}
          onChange={(e) => {
            setRequest(e.target.value);
            setOffset(0);
          }}
        />
      </div>
      <Panel title="Event ledger">
        <DataState loading={state.loading} error={state.error}>
          {state.data?.items.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Actor / request</th>
                    <th>Detail</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.items.map((x) => (
                    <tr key={x.id}>
                      <td>
                        {titleCase(x.action)}
                        <small className="audit-correlation">
                          {x.correlation_id}
                        </small>
                      </td>
                      <td>
                        {x.actor}
                        <small className="audit-correlation">
                          {x.request_id?.slice(0, 8) || "System"}
                        </small>
                      </td>
                      <td className="audit-detail">
                        {JSON.stringify(x.detail)}
                      </td>
                      <td>{new Date(x.at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty title="No matching events">
              Activity appears as workflows run.
            </Empty>
          )}
        </DataState>
      </Panel>
      <div className="pagination">
        <button disabled={!offset} onClick={() => setOffset((v) => v - 30)}>
          Previous
        </button>
        <button
          disabled={(state.data?.items.length || 0) < 30}
          onClick={() => setOffset((v) => v + 30)}
        >
          Next
        </button>
      </div>
    </>
  );
}
