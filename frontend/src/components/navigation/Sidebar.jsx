import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Files,
  CheckCheck,
  BookOpen,
  Bot,
  Fingerprint,
  Settings2,
  Workflow,
  ArrowUpRight,
} from "lucide-react";
import { useSession } from "../../context/SessionContext";
import "./Sidebar.css";
const routes = [
  ["/", "Overview", LayoutDashboard],
  ["/requests", "Requests", Files],
  ["/approvals", "Approvals", CheckCheck],
  ["/policies", "Policy library", BookOpen],
  ["/agent", "Agent workspace", Bot],
  ["/audit", "Audit trail", Fingerprint],
  ["/settings", "Integrations", Settings2],
];
export default function Sidebar() {
  const { user, mode } = useSession();
  return (
    <aside className="sidebar">
      <NavLink to="/" className="brand">
        <span className="brand-mark">
          <Workflow size={23} />
        </span>
        AssessFlow<span className="brand-dot">®</span>
      </NavLink>
      <div className="workspace-label">ACCESS GOVERNANCE</div>
      <nav aria-label="Main navigation">
        {routes
          .filter(
            ([path]) =>
              !(
                path === "/audit" && !["admin", "operator"].includes(user.role)
              ) &&
              !(
                path === "/approvals" &&
                !["admin", "approver"].includes(user.role)
              ) &&
              !(
                path === "/agent" && !["admin", "approver"].includes(user.role)
              ),
          )
          .map(([path, label, Icon]) => (
            <NavLink end={path === "/"} key={path} to={path}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="guard-note">
          <span className="live-dot" />
          {mode === "demo"
            ? "Local demo environment"
            : "Microsoft cloud environment"}
          <p>
            Human decisions.
            <br />
            Accountable access.
          </p>
          <ArrowUpRight size={18} />
        </div>
        <small>AssessFlow / Engineering edition</small>
      </div>
    </aside>
  );
}
