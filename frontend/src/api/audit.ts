import { apiClient } from "./client";

export interface TaskRun {
  id: string;
  assistant_id: string;
  assistant_name?: string;
  status: "pending" | "running" | "waiting_approval" | "completed" | "failed" | "cancelled";
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  result_summary: Record<string, unknown> | null;
}

export interface ActionLog {
  id: string;
  task_run_id: string;
  action_type: string;
  status: string;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  executed_at: string | null;
  external_resource_id: string | null;
}

export interface PaginatedTaskRuns {
  items: TaskRun[];
  total: number;
  page: number;
  size: number;
}

export const auditApi = {
  listTaskRuns: (params?: { page?: number; size?: number; assistant_id?: string }) =>
    apiClient.get<PaginatedTaskRuns>("/audit/task-runs", { params }).then((r) => r.data),
  getTaskRun: (id: string) =>
    apiClient.get<TaskRun & { action_logs: ActionLog[] }>(`/audit/task-runs/${id}`).then((r) => r.data),
  listActionLogs: (params?: { task_run_id?: string }) =>
    apiClient.get<ActionLog[]>("/audit/action-logs", { params }).then((r) => r.data),
};
