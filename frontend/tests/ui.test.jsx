import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import RequestTable from "../src/components/requests/RequestTable";
import { DataState, Badge } from "../src/components/ui/UI";
import { api, selectIdentity, configureMode } from "../src/services/api";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("operational components", () => {
  it("labels persisted states", () => {
    render(<Badge status="pending_approval" />);
    expect(screen.getByText("Pending Approval")).toBeVisible();
  });
  it("shows loading and error states", () => {
    const r = render(<DataState loading />);
    expect(screen.getByRole("status")).toBeVisible();
    r.rerender(<DataState error="Provider unavailable" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Provider unavailable");
  });
  it("renders an honest empty request queue", () => {
    render(<RequestTable items={[]} />);
    expect(screen.getByText("Your request queue is clear")).toBeVisible();
  });
  it("links to persisted request detail", () => {
    render(
      <MemoryRouter>
        <RequestTable
          items={[
            {
              id: "test-id",
              application_id: "finance-reports",
              requester_id: "employee",
              access_level: "reader",
              status: "pending_approval",
              created_at: "2026-01-01",
            },
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("Finance Reports").closest("a")).toHaveAttribute(
      "href",
      "/requests/test-id",
    );
  });
  it("sends demo identity and idempotency key through native fetch", async () => {
    configureMode("demo");
    selectIdentity("employee");
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ id: "persisted" }) });
    vi.stubGlobal("fetch", fetch);
    await api("/v1/requests", {
      method: "POST",
      body: { application_id: "x" },
      key: "unique-key",
    });
    expect(fetch.mock.calls[0][1].headers).toMatchObject({
      "X-Demo-User": "employee",
      "Idempotency-Key": "unique-key",
    });
  });
  it("surfaces backend errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ error: { message: "Not permitted" } }),
      }),
    );
    await expect(api("/v1/audit")).rejects.toThrow("Not permitted");
  });
});
