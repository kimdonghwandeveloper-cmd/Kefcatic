import { apiClient } from "./client";

export interface Memory {
  id: string;
  memory_type: "preference" | "instruction" | "context";
  key: string;
  value: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryCreate {
  memory_type: Memory["memory_type"];
  key: string;
  value: string;
}

export const memoriesApi = {
  list: (assistantId: string) =>
    apiClient.get<Memory[]>(`/assistants/${assistantId}/memories`).then((r) => r.data),
  create: (assistantId: string, data: MemoryCreate) =>
    apiClient.post<Memory>(`/assistants/${assistantId}/memories`, data).then((r) => r.data),
  update: (assistantId: string, key: string, value: string) =>
    apiClient.put<Memory>(`/assistants/${assistantId}/memories/${key}`, { value }).then((r) => r.data),
  delete: (assistantId: string, key: string) =>
    apiClient.delete(`/assistants/${assistantId}/memories/${key}`),
};
