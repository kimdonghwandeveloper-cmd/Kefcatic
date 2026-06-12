import { apiClient } from "./client";

export interface ConnectorCredential {
  id: string;
  connector_type: string;
  scopes: string[] | null;
  expires_at: string | null;
  created_at: string;
}

export const connectorsApi = {
  list: () => apiClient.get<ConnectorCredential[]>("/connectors").then((r) => r.data),
  disconnect: (credentialId: string) =>
    apiClient.delete(`/connectors/${credentialId}`).then((r) => r.data),
  youtubeAuthUrl: () =>
    apiClient.get<{ url: string }>("/connectors/youtube/auth-url").then((r) => r.data),
  gmailAuthUrl: () =>
    apiClient.get<{ url: string }>("/connectors/gmail/auth-url").then((r) => r.data),
  googleDriveAuthUrl: () =>
    apiClient.get<{ url: string }>("/connectors/google-drive/auth-url").then((r) => r.data),
};
