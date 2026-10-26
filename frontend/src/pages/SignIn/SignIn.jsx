import { useState } from "react";
import { Workflow, ArrowRight, ShieldCheck } from "lucide-react";
import { useSession } from "../../context/SessionContext";
import { signIn } from "../../services/auth";
import { Notice } from "../../components/ui/UI";
import "./SignIn.css";
const identities = [
  ["employee", "Jamie Ellis", "Finance employee"],
  ["manager", "Morgan Taylor", "Assigned approver"],
  ["admin", "Alex Rivers", "Administrator"],
  ["operator", "Sam Chen", "Service operator"],
  ["other", "Casey Jordan", "Sales employee / ACL test"],
];
export default function SignIn() {
  const { mode, choose, error, reload } = useSession(),
    [failure, setFailure] = useState("");
  return (
    <div className="signin">
      <section className="signin-story">
        <div className="signin-brand">
          <Workflow />
          AssessFlow
        </div>
        <span className="eyebrow">ENTERPRISE ACCESS GOVERNANCE</span>
        <h1>
          Good access starts
          <br />
          with a clear decision.
        </h1>
        <p>
          From the first request to the final audit trail.
          <br />
          Policy-grounded. Human-approved.
        </p>
        <div className="signin-assurance">
          <ShieldCheck size={20} />
          Evidence-backed workflows for accountable teams.
        </div>
      </section>
      <section className="signin-form">
        <div>
          <span className="eyebrow">
            {mode === "demo" ? "LOCAL DEMONSTRATION" : "WORKSPACE SIGN-IN"}
          </span>
          <h2>
            {mode === "demo"
              ? "Choose your perspective."
              : "Welcome to AssessFlow."}
          </h2>
          <p>
            {mode === "demo"
              ? "All identities and organisational data are synthetic. Your actions persist in the local database."
              : "Sign in with your organisation’s Microsoft account."}
          </p>
          {(error || failure) && <Notice>{error || failure}</Notice>}
          {mode === "demo" ? (
            <div className="identity-list">
              {identities.map(([id, name, role]) => (
                <button key={id} onClick={() => choose(id)}>
                  <span className="avatar">
                    {name
                      .split(" ")
                      .map((x) => x[0])
                      .join("")}
                  </span>
                  <span>
                    <strong>{name}</strong>
                    <small>{role}</small>
                  </span>
                  <ArrowRight size={16} />
                </button>
              ))}
            </div>
          ) : (
            <button
              className="primary"
              onClick={async () => {
                try {
                  await signIn();
                } catch (e) {
                  setFailure(e.message);
                }
              }}
            >
              Sign in with Microsoft <ArrowRight size={16} />
            </button>
          )}
          {error && <button onClick={reload}>Retry connection</button>}
          <small className="signin-footnote">
            AI assists with interpretation. People authorise access.
          </small>
        </div>
      </section>
    </div>
  );
}
