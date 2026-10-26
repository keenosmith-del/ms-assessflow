import { accessToken } from "./auth";
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5050";
let demoIdentity = sessionStorage.getItem("assessflow-demo");
let operatingMode = "demo";
export function configureMode(mode) {
  operatingMode = mode;
}
export function selectIdentity(id) {
  demoIdentity = id;
  if (id) sessionStorage.setItem("assessflow-demo", id);
  else sessionStorage.removeItem("assessflow-demo");
}
export async function api(path, { method = "GET", body, key, signal } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (operatingMode === "demo" && demoIdentity)
    headers["X-Demo-User"] = demoIdentity;
  if (operatingMode === "azure") {
    const token = await accessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  if (key) headers["Idempotency-Key"] = key;
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      data.error?.message || `Request failed (${response.status})`,
    );
  return data;
}
