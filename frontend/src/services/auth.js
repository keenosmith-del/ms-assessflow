import { PublicClientApplication } from "@azure/msal-browser";
let client;
export async function identityClient() {
  if (!import.meta.env.VITE_ENTRA_CLIENT_ID)
    throw new Error("Entra sign-in has not been configured.");
  if (!client) {
    client = new PublicClientApplication({
      auth: {
        clientId: import.meta.env.VITE_ENTRA_CLIENT_ID,
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID}`,
        redirectUri: window.location.origin,
      },
      cache: { cacheLocation: "sessionStorage" },
    });
    await client.initialize();
    const result = await client.handleRedirectPromise();
    if (result?.account) client.setActiveAccount(result.account);
  }
  return client;
}
export async function signIn() {
  const c = await identityClient();
  await c.loginRedirect({ scopes: [import.meta.env.VITE_ENTRA_SCOPE] });
}
export async function accessToken() {
  const c = await identityClient();
  const account = c.getActiveAccount() || c.getAllAccounts()[0];
  if (!account) return null;
  return (
    await c.acquireTokenSilent({
      account,
      scopes: [import.meta.env.VITE_ENTRA_SCOPE],
    })
  ).accessToken;
}
