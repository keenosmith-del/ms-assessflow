import { createContext, useContext, useEffect, useState } from "react";
import { api, configureMode, selectIdentity } from "../services/api";
const SessionContext = createContext(null);
export function SessionProvider({ children }) {
  const [user, setUser] = useState(null),
    [mode, setMode] = useState(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true);
    setError("");
    try {
      const health = await api("/health");
      configureMode(health.mode);
      setMode(health.mode);
      try {
        setUser(await api("/v1/session"));
      } catch {
        setUser(null);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);
  async function choose(id) {
    selectIdentity(id);
    await load();
  }
  return (
    <SessionContext.Provider
      value={{ user, mode, error, loading, choose, reload: load }}
    >
      {children}
    </SessionContext.Provider>
  );
}
export function useSession() {
  return useContext(SessionContext);
}
