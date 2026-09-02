const AUTH_TOKEN_KEY = "spendly_auth_token";

export async function getAuthToken(): Promise<string | null> {
  const result = await chrome.storage.local.get(AUTH_TOKEN_KEY);
  return (result[AUTH_TOKEN_KEY] as string | undefined) ?? null;
}

export async function setAuthToken(token: string): Promise<void> {
  await chrome.storage.local.set({ [AUTH_TOKEN_KEY]: token });
}

export async function clearAuthToken(): Promise<void> {
  await chrome.storage.local.remove(AUTH_TOKEN_KEY);
}
