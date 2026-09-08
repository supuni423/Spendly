import { getAuthToken } from "@/storage/chromeStorage";

// Defaults to localhost for development. For a deployed backend, build with
// VITE_API_BASE_URL=https://your-deployed-url — vite.config.ts reads the same
// variable to set manifest.json's host_permissions, so the two never drift
// apart (see backend/README.md's Deploy section).
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const { method = "GET", body, auth = true } = options;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) {
    const token = await getAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new ApiError(response.status, detail?.detail ?? response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, auth = true) => request<T>(path, { method: "GET", auth }),
  post: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: "POST", body, auth }),
  delete: <T>(path: string, auth = true) => request<T>(path, { method: "DELETE", auth }),
};
