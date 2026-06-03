export type ExpenseStatus =
  | "draft"
  | "submitted"
  | "need_supplement"
  | "finance_review"
  | "approved"
  | "rejected";

export type AttachmentType = "invoice" | "payment" | "approval" | "other";

export type AuditResult = "pass" | "attention" | "risk";

export interface ExpenseAttachment {
  id: string;
  claim_id: string;
  file_uri: string;
  file_name: string;
  file_type: string;
  size?: number | null;
  attachment_type: AttachmentType;
  ocr_result?: Record<string, unknown> | null;
  extracted_fields?: Record<string, unknown> | null;
  ocr_confidence?: string | number | null;
  classification_source?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpenseAuditItem {
  id: string;
  claim_id: string;
  name: string;
  result: AuditResult;
  evidence?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpenseClaim {
  id: string;
  user_id: string;
  status: ExpenseStatus;
  claim_no?: string | null;
  expense_type: string;
  title?: string | null;
  description?: string | null;
  total_amount?: string | number | null;
  currency: string;
  submitted_at?: string | null;
  approved_at?: string | null;
  audit_summary?: {
    level?: AuditResult;
    summary?: string;
    missing_materials?: string[];
    next_action?: string;
    metadata?: Record<string, unknown>;
  } | null;
  reviewer_id?: string | null;
  reviewed_at?: string | null;
  review_comment?: string | null;
  created_at: string;
  updated_at: string;
  attachments: ExpenseAttachment[];
  audit_items: ExpenseAuditItem[];
}

export interface ExpenseApprovalLog {
  id: string;
  claim_id: string;
  actor_id: string;
  action: "submit" | "resubmit" | "approve" | "reject" | "request_supplement";
  from_status?: string | null;
  to_status?: string | null;
  comment?: string | null;
  snapshot?: Record<string, unknown> | null;
  created_at: string;
}

export interface TravelExpenseStandard {
  id: string;
  name: string;
  org_id?: string | null;
  city_tier?: string | null;
  daily_limit?: string | number | null;
  single_trip_limit?: string | number | null;
  currency: string;
  effective_from?: string | null;
  effective_to?: string | null;
  is_active: boolean;
  metadata_?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}
