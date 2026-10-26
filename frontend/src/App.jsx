import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SessionProvider, useSession } from "./context/SessionContext";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard/Dashboard";
import Requests from "./pages/Requests/Requests";
import RequestDetail from "./pages/RequestDetail/RequestDetail";
import Approvals from "./pages/Approvals/Approvals";
import Policies from "./pages/Policies/Policies";
import AgentWorkspace from "./pages/AgentWorkspace/AgentWorkspace";
import Audit from "./pages/Audit/Audit";
import Settings from "./pages/Settings/Settings";
import SignIn from "./pages/SignIn/SignIn";
import { DataState } from "./components/ui/UI";
function Workspace() {
  const { user, loading } = useSession();
  if (loading) return <DataState loading />;
  if (!user) return <SignIn />;
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="requests" element={<Requests />} />
        <Route path="requests/:id" element={<RequestDetail />} />
        <Route path="approvals" element={<Approvals />} />
        <Route path="policies" element={<Policies />} />
        <Route path="agent" element={<AgentWorkspace />} />
        <Route path="audit" element={<Audit />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <Workspace />
      </SessionProvider>
    </BrowserRouter>
  );
}
