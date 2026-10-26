import { test, expect } from "@playwright/test";
async function choose(page, name) {
  await page.getByRole("button", { name: "Switch demo identity" }).click();
  await page.getByRole("button", { name }).click();
}
test("employee request, manager approval, service fulfilment, persisted audit", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Jamie Ellis" }).click();
  await expect(
    page.getByRole("heading", { name: "Access, with accountability." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "New request" }).click();
  await page
    .getByLabel("Business justification")
    .fill(`Quarterly reconciliation and financial reporting ${Date.now()}`);
  await page.getByRole("button", { name: "Submit request" }).click();
  await expect(
    page.getByRole("heading", { name: "Submit an access request" }),
  ).not.toBeVisible();
  await page.locator("tbody .request-title").first().click();
  await expect(
    page.getByText("Pending Approval", { exact: true }),
  ).toBeVisible();
  const requestURL = page.url();
  await choose(page, "Morgan Taylor");
  await page.goto(requestURL);
  await page
    .getByLabel("Decision reason")
    .fill("Policy evidence and business need reviewed by manager");
  await page.getByRole("button", { name: "Record decision" }).click();
  await expect(
    page.getByText("Provisioning Pending", { exact: true }).first(),
  ).toBeVisible();
  await choose(page, "Sam Chen");
  await page.goto(requestURL);
  await page
    .getByLabel("Service ticket / fulfilment evidence")
    .fill("SYNTHETIC-IT-98765");
  await page.getByRole("button", { name: "Record fulfilment" }).click();
  await expect(
    page.getByText("Fulfilled", { exact: true }).first(),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("SYNTHETIC-IT-98765", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Audit trail" }).click();
  await expect(
    page.getByRole("heading", { name: "An accountable history." }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell").filter({ hasText: "Fulfilment Recorded" }).first(),
  ).toBeVisible();
});
test("all administrator pages and mobile layout", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByRole("button", { name: "Alex Rivers" }).click();
  for (const [link, heading] of [
    ["Requests", "Request workspace"],
    ["Approvals", "Decisions need a human."],
    ["Policy library", "The evidence behind access."],
    ["Agent workspace", "Policy analysis workspace"],
    ["Audit trail", "An accountable history."],
    ["Integrations", "Connected with intention."],
  ]) {
    await page.getByRole("link", { name: link, exact: true }).click();
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
  }
  await page.getByRole("link", { name: "Agent workspace" }).click();
  await page.getByRole("button", { name: "Run assessment" }).click();
  await expect(page.locator(".json-output")).toContainText(
    "demo-deterministic",
  );
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await page.screenshot({
    path: "../docs/testing/dashboard-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Access, with accountability." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../docs/testing/dashboard-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("missing information and form validation", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Casey Jordan" }).click();
  await page.getByRole("link", { name: "New request" }).click();
  await page.getByLabel("Application").selectOption("service-desk");
  await page.getByLabel("Business justification").fill(String(Date.now()));
  await page.getByRole("button", { name: "Submit request" }).click();
  await page.locator("tbody .request-title").first().click();
  await expect(
    page.getByText("Awaiting Information", { exact: true }).first(),
  ).toBeVisible();
  await page.getByLabel("Business justification").fill("short");
  await page.getByRole("button", { name: "Continue assessment" }).click();
  await expect(page.getByLabel("Business justification")).toBeVisible();
  await page
    .getByLabel("Business justification")
    .fill(`Service desk reader for business collaboration ${Date.now()}`);
  await page.getByRole("button", { name: "Continue assessment" }).click();
  await expect(
    page.getByText("Pending Approval", { exact: true }).first(),
  ).toBeVisible();
});
