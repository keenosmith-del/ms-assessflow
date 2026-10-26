import { useState } from "react";
import { BookOpen, Upload, Search } from "lucide-react";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../context/SessionContext";
import { api } from "../../services/api";
import {
  PageHeading,
  Panel,
  DataState,
  Field,
  Notice,
  Empty,
} from "../../components/ui/UI";
import "./Policies.css";
export default function Policies() {
  const { user } = useSession(),
    [query, setQuery] = useState(""),
    [upload, setUpload] = useState(false),
    [content, setContent] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [history, setHistory] = useState(null);
  const state = useApi("/v1/policies"),
    apps = useApi("/v1/applications");
  const policies = state.data?.items.filter((x) =>
    `${x.title} ${x.content}`.toLowerCase().includes(query.toLowerCase()),
  );
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/v1/policies", {
        method: "POST",
        body: { ...Object.fromEntries(new FormData(e.currentTarget)), content },
      });
      setUpload(false);
      state.refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function file(e) {
    const f = e.target.files[0];
    if (!f) return;
    if (f.size > 100000 || !f.name.toLowerCase().endsWith(".txt")) {
      setError("Upload a UTF-8 .txt file up to 100KB.");
      return;
    }
    setContent(await f.text());
  }
  return (
    <>
      <PageHeading
        eyebrow="KNOWLEDGE / POLICIES"
        title="The evidence behind access."
        description="Versioned policy content, controlled visibility, and traceable sources."
      >
        {user.role === "admin" && (
          <button className="primary" onClick={() => setUpload(!upload)}>
            <Upload size={15} />
            Upload policy version
          </button>
        )}
      </PageHeading>
      {error && <Notice>{error}</Notice>}
      {upload && (
        <Panel title="New policy version">
          <form className="form-grid panel-body" onSubmit={submit}>
            <Field label="Application">
              <select name="application_id">
                {apps.data?.items.map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Policy title">
              <input name="title" required minLength={5} />
            </Field>
            <Field label="Department visibility">
              <select name="department">
                {["all", "finance", "it", "sales"].map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
            </Field>
            <Field label="Expires on">
              <input name="expires_at" type="date" required />
            </Field>
            <div className="full-width">
              <Field label="Plain text document (.txt, max 100KB)">
                <input type="file" accept=".txt,text/plain" onChange={file} />
              </Field>
            </div>
            <div className="full-width">
              <Field label="Policy content">
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={5}
                  minLength={40}
                  maxLength={100000}
                  required
                />
              </Field>
            </div>
            <button className="primary" disabled={busy}>
              {busy ? "Saving…" : "Save policy version"}
            </button>
          </form>
        </Panel>
      )}
      <label className="policy-search search-box">
        <Search size={16} />
        <input
          aria-label="Search policies"
          placeholder="Search your policy library…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </label>
      <DataState loading={state.loading} error={state.error}>
        <div className="policy-grid">
          {policies?.map((policy) => (
            <Panel
              key={policy.id}
              title={policy.title}
              aside={<BookOpen size={17} />}
            >
              <div className="panel-body">
                <div className="policy-tags">
                  <span>VERSION {policy.version}</span>
                  <span>{policy.department.toUpperCase()}</span>
                </div>
                <p className="policy-text">{policy.content}</p>
                <div className="policy-footer">
                  <span>Expires {policy.expires_at}</span>
                  <button
                    className="text-button"
                    onClick={async () => {
                      try {
                        setHistory(
                          await api(`/v1/policies/${policy.id}/versions`),
                        );
                      } catch (e) {
                        setError(e.message);
                      }
                    }}
                  >
                    Version history
                  </button>
                </div>
                <details>
                  <summary>
                    Inspect indexed chunks ({policy.chunks.length})
                  </summary>
                  <p className="subtle mono">SHA256 {policy.digest}</p>
                  {policy.chunks.map((x, i) => (
                    <blockquote key={i}>
                      Chunk {i + 1}: {x}
                    </blockquote>
                  ))}
                </details>
              </div>
            </Panel>
          ))}
        </div>
        {!policies?.length && (
          <Empty title="No matching policies">
            Only policies visible to your identity appear here.
          </Empty>
        )}
      </DataState>
      {history && (
        <Panel
          title="Version history"
          aside={<button onClick={() => setHistory(null)}>Close</button>}
        >
          <div className="panel-body">
            {history.items.map((x) => (
              <details key={x.id}>
                <summary>
                  Version {x.version} · expires {x.expires_at}
                </summary>
                <p className="body-copy">{x.content}</p>
              </details>
            ))}
          </div>
        </Panel>
      )}
    </>
  );
}
