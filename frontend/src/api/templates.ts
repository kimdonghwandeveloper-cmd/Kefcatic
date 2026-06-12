import { apiClient } from "./client";

export interface Template {
  id: string;
  name: string;
  description: string | null;
  role_type: string | null;
  is_official: boolean;
  install_count: number;
  required_connectors: string[];
  created_at: string;
}

export const templatesApi = {
  list: (params?: { q?: string; connector?: string }) =>
    apiClient.get<Template[]>("/assistants/templates", { params }).then((r) => r.data),
  get: (id: string) =>
    apiClient.get<Template>(`/assistants/templates/${id}`).then((r) => r.data),
  install: (templateId: string) =>
    apiClient.post(`/assistants/from-template/${templateId}`).then((r) => r.data),
  saveAsTemplate: (assistantId: string) =>
    apiClient.post(`/assistants/${assistantId}/save-as-template`).then((r) => r.data),
};
