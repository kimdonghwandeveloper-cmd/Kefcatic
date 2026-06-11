import { apiClient } from "./client";
import type { ActionLog } from "./approvals";

export interface TaskRunListItem {
  id: string;
  assistant_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  result_summary: Record<string, unknown> | null;
}

export interface TaskRunDetail extends TaskRunListItem {
  trigger_id: string | null;
  error_message: string | null;
  action_logs: ActionLog[];
}

export interface PaginatedTaskRuns {
  items: TaskRunListItem[];
  total: number;
  page: number;
  page_size: number;
}

export const auditApi = {
  listTaskRuns: (params?: { assistant_id?: string; status?: string; page?: number }) =>
    apiClient.get<PaginatedTaskRuns>("/audit/task-runs", { params }).then((r) => r.data),

  getTaskRunDetail: (id: string) =>
    apiClient.get<TaskRunDetail>(`/audit/task-runs/${id}`).then((r) => r.data),

  listActionLogs: (params?: { action_type?: string; status?: string; page?: number }) =>
    apiClient.get<ActionLog[]>("/audit/action-logs", { params }).then((r) => r.data),
};
