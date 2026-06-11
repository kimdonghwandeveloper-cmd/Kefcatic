import { apiClient } from "./client";

export interface Assistant {
  id: string;
  name: string;
  description: string | null;
  role_type: string | null;
  is_active: boolean;
  is_template: boolean;
}

export interface CreateAssistantInput {
  name: string;
  description?: string;
  role_type: string;
  system_prompt?: string;
  config?: Record<string, unknown>;
}

export const assistantsApi = {
  list: () => apiClient.get<Assistant[]>("/assistants").then((r) => r.data),
  get: (id: string) => apiClient.get<Assistant>(`/assistants/${id}`).then((r) => r.data),
  create: (data: CreateAssistantInput) =>
    apiClient.post<Assistant>("/assistants", data).then((r) => r.data),
  update: (id: string, data: Partial<CreateAssistantInput & { is_active: boolean }>) =>
    apiClient.patch<Assistant>(`/assistants/${id}`, data).then((r) => r.data),
  trigger: (id: string) =>
    apiClient.post(`/task-runs/${id}/trigger`).then((r) => r.data),
  getState: (id: string) =>
    apiClient.get(`/stream/assistants/${id}/state`).then((r) => r.data),
};
