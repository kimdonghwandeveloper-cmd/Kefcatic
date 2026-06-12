import { apiClient } from "./client";

export interface ApprovalRequest {
  id: string;
  action_log_id: string;
  requested_at: string;
  status: "pending" | "approved" | "rejected";
  reviewer_note: string | null;
  action: {
    action_type: string;
    input_data: Record<string, unknown> | null;
    output_data: Record<string, unknown> | null;
    assistant_name?: string;
  };
}

export const approvalsApi = {
  list: (status = "pending") =>
    apiClient.get<ApprovalRequest[]>(`/approvals?status=${status}`).then((r) => r.data),
  approve: (actionLogId: string, modifiedInput?: Record<string, unknown>) =>
    apiClient
      .post<ApprovalRequest>(`/approvals/${actionLogId}/approve`, { modified_input: modifiedInput })
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
