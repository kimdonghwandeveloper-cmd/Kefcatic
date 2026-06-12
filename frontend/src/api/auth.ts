import { apiClient } from "./client";

export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
}

export const authApi = {
  getMe: () => apiClient.get<User>("/auth/me").then((r) => r.data),
  logout: () => apiClient.post("/auth/logout"),
  googleLoginUrl: () => `${apiClient.defaults.baseURL}/auth/google`,
};
