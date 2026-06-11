import { apiClient } from "./client";

export interface ActionLog {
  id: string;
  task_run_id: string;
  action_type: string;
  status: string;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  external_resource_id: string | null;
  executed_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
}

export interface ApprovalRequest {
  id: string;
  action_log_id: string;
  requested_at: string;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  reviewer_note: string | null;
  action_log: ActionLog | null;
}

export const approvalsApi = {
  list: (status = "pending") =>
    apiClient.get<ApprovalRequest[]>(`/approvals?status=${status}`).then((r) => r.data),

  approve: (actionLogId: string, note?: string, modifiedInput?: Record<string, unknown>) =>
    apiClient
      .post<ApprovalRequest>(`/approvals/${actionLogId}/approve`, {
        reviewer_note: note,
        modified_input: modifiedInput,
      })
      .then((r) => r.data),

  reject: (actionLogId: string, note?: string) =>
    apiClient
      .post<ApprovalRequest>(`/approvals/${actionLogId}/reject`, { reviewer_note: note })
      .then((r) => r.data),

  bulkApprove: (actionLogIds: string[]) =>
    apiClient.post("/approvals/bulk-approve", { action_log_ids: actionLogIds }).then((r) => r.data),

  rollback: (actionLogId: string) =>
    apiClient.post(`/approvals/${actionLogId}/rollback`).then((r) => r.data),
};
