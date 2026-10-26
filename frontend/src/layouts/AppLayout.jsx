import { Outlet } from "react-router-dom";
import { ShieldCheck, ChevronDown } from "lucide-react";
import Sidebar from "../components/navigation/Sidebar";
import { useSession } from "../context/SessionContext";
import "./AppLayout.css";
export default function AppLayout() {
  const { user, mode, choose } = useSession();
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>Access operations</strong>
          </div>
          <div className="topbar-right">
            <span className="environment">
              <ShieldCheck size={14} />
              {mode === "demo" ? "DEMO · SYNTHETIC DATA" : "AZURE MODE"}
            </span>
            <div className="identity">
              <span className="avatar">
                {user.name
                  .split(" ")
                  .map((x) => x[0])
                  .join("")}
              </span>
              <div>
                <strong>{user.name}</strong>
                <small>
                  {user.role} · {user.department}
                </small>
              </div>
              {mode === "demo" && (
                <button
                  className="icon-button"
                  title="Switch demo identity"
                  aria-label="Switch demo identity"
                  onClick={() => choose(null)}
                >
                  <ChevronDown size={16} />
                </button>
              )}
            </div>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
        <footer className="footer">
          AssessFlow <span>Policy-led decisions. Human-controlled access.</span>
          <span>
            v0.1 /{" "}
            {mode === "demo" ? "Local demonstration" : "Cloud configured"}
          </span>
        </footer>
      </div>
    </div>
  );
}
