import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../services/api";
import { useSession } from "../../context/SessionContext";
import {
  PageHeading,
  Panel,
  DataState,
  Field,
  Notice,
  Badge,
  titleCase,
} from "../../components/ui/UI";
import "./RequestDetail.css";
export default function RequestDetail() {
  const { id } = useParams(),
    { user } = useSession(),
    state = useApi(`/v1/requests/${id}`),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const item = state.data;
  async function action(path, body, method = "POST") {
    setBusy(true);
    setError("");
    try {
      await api(`/v1/requests/${id}/${path}`, { method, body });
      state.refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function decision(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    action("decision", data);
  }
  return (
    <>
      <Link className="back-link" to="/requests">
        <ArrowLeft size={14} />
        All requests
      </Link>
      <PageHeading
        eyebrow={`REQUEST / AF–${id.slice(0, 8).toUpperCase()}`}
        title={
          item
            ? titleCase(item.application_id.replaceAll("-", " "))
            : "Request details"
        }
        description="Evidence, decisions, and a complete history of this request."
      >
        {item && <Badge status={item.status} />}
      </PageHeading>
      <DataState loading={state.loading} error={state.error}>
        {item && (
          <div className="detail-columns">
            <div className="stack">
              <Panel title="Request information">
                <div className="panel-body">
                  <dl className="detail-grid">
                    <div>
                      <dt>Requester</dt>
                      <dd>{titleCase(item.requester_id)}</dd>
                    </div>
                    <div>
                      <dt>Requested access</dt>
                      <dd>{titleCase(item.access_level)}</dd>
                    </div>
                    <div>
                      <dt>Submitted</dt>
                      <dd>{new Date(item.created_at).toLocaleString()}</dd>
                    </div>
                    <div>
                      <dt>Revision</dt>
                      <dd>{item.revision}</dd>
                    </div>
                  </dl>
                  <h3 className="small-heading">Business justification</h3>
                  <p className="body-copy">
                    {item.justification || "Not yet supplied"}
                  </p>
                  <div className="next-step">
                    <ShieldCheck size={17} />
                    {item.next_step}
                  </div>
                </div>
              </Panel>
              <Panel title="Policy assessment">
                {item.assessments.map((assessment, i) => (
                  <div className="panel-body assessment" key={i}>
                    <div className="assessment-meta">
                      <Badge status={assessment.output.recommendation} />
                      <span>
                        {assessment.provider} · {assessment.latency_ms}ms
                      </span>
                    </div>
                    <p className="body-copy">{assessment.output.explanation}</p>
                    <p className="subtle">{assessment.output.uncertainty}</p>
                    <p className="subtle">
                      Eligibility checks:{" "}
                      {assessment.eligibility.eligible
                        ? "Satisfied"
                        : "Review required"}
                    </p>
                    {assessment.eligibility.failures.map((x) => (
                      <Notice key={x}>{x}</Notice>
                    ))}
                    <h3 className="small-heading">Supporting evidence</h3>
                    {assessment.output.citations.length ? (
                      assessment.output.citations.map((citation, j) => (
                        <blockquote key={j}>
                          {citation.quote}
                          <cite>
                            Version {citation.version_id.slice(0, 8)} · Chunk{" "}
                            {citation.chunk_index + 1}
                          </cite>
                        </blockquote>
                      ))
                    ) : (
                      <p className="subtle">
                        No accessible evidence; manual review required.
                      </p>
                    )}
                    <p className="subtle mono">Trace: {assessment.trace_id}</p>
                  </div>
                ))}
              </Panel>
              <Panel title="Comments">
                <div className="panel-body">
                  {item.comments.map((x, i) => (
                    <div className="comment" key={i}>
                      <strong>{x.actor}</strong>
                      <p>{x.body}</p>
                    </div>
                  ))}
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      action("comments", {
                        body: new FormData(e.currentTarget).get("body"),
                      });
                      e.currentTarget.reset();
                    }}
                  >
                    <Field label="Add a comment">
                      <textarea
                        required
                        name="body"
                        maxLength={2000}
                        rows={2}
                      />
                    </Field>
                    <button className="secondary spaced-button" disabled={busy}>
                      Add comment
                    </button>
                  </form>
                </div>
              </Panel>
            </div>
            <div className="stack">
              {error && <Notice>{error}</Notice>}
              {item.status === "awaiting_information" &&
                item.requester_id === user.id && (
                  <Panel title="Supply missing information">
                    <form
                      className="panel-body stack"
                      onSubmit={(e) => {
                        e.preventDefault();
                        action(
                          "information",
                          {
                            justification: new FormData(e.currentTarget).get(
                              "justification",
                            ),
                          },
                          "PATCH",
                        );
                      }}
                    >
                      <Field label="Business justification">
                        <textarea
                          required
                          minLength={20}
                          name="justification"
                          rows={4}
                        />
                      </Field>
                      <button className="primary" disabled={busy}>
                        Continue assessment
                      </button>
                    </form>
                  </Panel>
                )}
              {item.status === "pending_approval" &&
                ["admin", "approver"].includes(user.role) &&
                item.requester_id !== user.id && (
                  <Panel title="Record a human decision">
                    <form className="panel-body stack" onSubmit={decision}>
                      <Field label="Decision">
                        <select name="decision">
                          <option value="approved">Approve</option>
                          <option value="rejected">Reject</option>
                        </select>
                      </Field>
                      <Field label="Decision reason">
                        <textarea
                          name="reason"
                          required
                          minLength={10}
                          maxLength={2000}
                          rows={3}
                        />
                      </Field>
                      <p className="subtle">
                        Review all evidence and exceptions before deciding.
                        Approval creates a fulfilment task.
                      </p>
                      <button className="primary" disabled={busy}>
                        Record decision
                      </button>
                    </form>
                  </Panel>
                )}
              {item.decision && (
                <Panel title="Approval decision">
                  <div className="panel-body">
                    <Badge status={item.decision.decision} />
                    <p className="body-copy">{item.decision.reason}</p>
                    <span className="subtle">
                      Recorded by {item.decision.actor}
                    </span>
                  </div>
                </Panel>
              )}
              {item.status === "provisioning_pending" &&
                ["admin", "operator"].includes(user.role) && (
                  <Panel title="Record verified fulfilment">
                    <form
                      className="panel-body stack"
                      onSubmit={(e) => {
                        e.preventDefault();
                        action("fulfil", {
                          reference: new FormData(e.currentTarget).get(
                            "reference",
                          ),
                        });
                      }}
                    >
                      <Field label="Service ticket / fulfilment evidence">
                        <input name="reference" required minLength={5} />
                      </Field>
                      <p className="subtle">
                        Confirm the manual service task was completed. This
                        action does not change directory permissions.
                      </p>
                      <button className="primary" disabled={busy}>
                        Record fulfilment
                      </button>
                    </form>
                  </Panel>
                )}
              {item.fulfilment?.reference && (
                <Panel title="Fulfilment record">
                  <p className="panel-body mono">{item.fulfilment.reference}</p>
                </Panel>
              )}
              <Panel title="Request timeline">
                <ol className="timeline">
                  {item.timeline.map((x) => (
                    <li key={x.id}>
                      <strong>
                        {x.detail.to
                          ? titleCase(x.detail.to)
                          : titleCase(x.action)}
                      </strong>
                      <p>{x.actor}</p>
                      <time>{new Date(x.at).toLocaleString()}</time>
                    </li>
                  ))}
                </ol>
              </Panel>
              {[
                "submitted",
                "under_assessment",
                "awaiting_information",
                "pending_approval",
              ].includes(item.status) &&
                (item.requester_id === user.id || user.role === "admin") && (
                  <button
                    className="danger"
                    disabled={busy}
                    onClick={() => action("cancel")}
                  >
                    Cancel request
                  </button>
                )}
            </div>
          </div>
        )}
      </DataState>
    </>
  );
}
