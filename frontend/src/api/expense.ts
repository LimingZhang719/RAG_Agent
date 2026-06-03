import apiClient from "./index";
import type {
  AttachmentType,
  ExpenseApprovalLog,
  ExpenseAttachment,
  ExpenseClaim,
  TravelExpenseStandard
} from "../types/expense";

export interface ExpenseClaimPayload {
  title?: string;
  description?: string;
  total_amount?: number;
  currency?: string;
  city_tier?: string;
}

export async function fetchExpenseClaims(): Promise<ExpenseClaim[]> {
  const response = await apiClient.get<ExpenseClaim[]>("/expense/claims");
  return response.data;
}

export async function createExpenseClaim(
  payload: ExpenseClaimPayload
): Promise<ExpenseClaim> {
  const response = await apiClient.post<ExpenseClaim>("/expense/claims", payload);
  return response.data;
}

export async function updateExpenseClaim(
  claimId: string,
  payload: ExpenseClaimPayload
): Promise<ExpenseClaim> {
  const response = await apiClient.patch<ExpenseClaim>(
    `/expense/claims/${claimId}`,
    payload
  );
  return response.data;
}

export async function uploadExpenseAttachment(
  claimId: string,
  file: File,
  attachmentType: AttachmentType
): Promise<ExpenseAttachment> {
  const formData = new FormData();
  formData.append("attachment_type", attachmentType);
  formData.append("file", file);
  const response = await apiClient.post<ExpenseAttachment>(
    `/expense/claims/${claimId}/attachments`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}

export async function fetchExpenseAttachmentSource(
  claimId: string,
  attachmentId: string
): Promise<Blob> {
  const response = await apiClient.get(
    `/expense/claims/${claimId}/attachments/${attachmentId}/source`,
    { responseType: "blob" }
  );
  return response.data;
}

export async function submitExpenseClaim(claimId: string): Promise<ExpenseClaim> {
  const response = await apiClient.post<ExpenseClaim>(
    `/expense/claims/${claimId}/submit`
  );
  return response.data;
}

export async function runExpenseAgent(claimId: string): Promise<ExpenseClaim> {
  const response = await apiClient.post<ExpenseClaim>(
    `/expense/claims/${claimId}/run-agent`
  );
  return response.data;
}

export async function fetchFinanceTasks(): Promise<ExpenseClaim[]> {
  const response = await apiClient.get<ExpenseClaim[]>("/expense/finance/tasks");
  return response.data;
}

export async function reviewFinanceTask(
  claimId: string,
  action: "approve" | "reject" | "request-supplement",
  comment?: string
): Promise<ExpenseClaim> {
  const response = await apiClient.post<ExpenseClaim>(
    `/expense/finance/tasks/${claimId}/${action}`,
    { comment }
  );
  return response.data;
}

export async function fetchApprovalLogs(
  claimId: string
): Promise<ExpenseApprovalLog[]> {
  const response = await apiClient.get<ExpenseApprovalLog[]>(
    `/expense/claims/${claimId}/approval-logs`
  );
  return response.data;
}

export async function fetchTravelStandards(): Promise<TravelExpenseStandard[]> {
  const response = await apiClient.get<TravelExpenseStandard[]>(
    "/expense/travel-standards"
  );
  return response.data;
}

export async function createTravelStandard(payload: {
  name: string;
  org_id?: string | null;
  city_tier?: string | null;
  daily_limit?: number | null;
  single_trip_limit?: number | null;
  currency?: string;
  is_active?: boolean;
}): Promise<TravelExpenseStandard> {
  const response = await apiClient.post<TravelExpenseStandard>(
    "/expense/travel-standards",
    payload
  );
  return response.data;
}
