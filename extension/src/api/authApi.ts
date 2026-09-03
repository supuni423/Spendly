import { apiClient } from "./apiClient";
import type { TokenResponse } from "@/types/user";

export function register(email: string, password: string, name: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/api/auth/register", { email, password, name }, false);
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/api/auth/login", { email, password }, false);
}
