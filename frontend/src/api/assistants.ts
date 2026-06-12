import { apiClient } from "./client";

export interface Assistant {
  id: string;
  name: string;
  description: string | null;
  role_type: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AssistantCreate {
  name: string;
  description?: string;
  role_type?: string;
  system_prompt?: string;
}

export interface AssistantPatch {
  name?: string;
  description?: string;
  is_active?: boolean;
  system_prompt?: string;
}

export const assistantsApi = {
  list: () => apiClient.get<Assistant[]>("/assistants").then((r) => r.data),
  get: (id: string) => apiClient.get<Assistant>(`/assistants/${id}`).then((r) => r.data),
  create: (data: AssistantCreate) =>
    apiClient.post<Assistant>("/assistants", data).then((r) => r.data),
  patch: (id: string, data: AssistantPatch) =>
    apiClient.patch<Assistant>(`/assistants/${id}`, data).then((r) => r.data),
  trigger: (assistantId: string) =>
    apiClient.post(`/task-runs/${assistantId}/trigger`).then((r) => r.data),
};
