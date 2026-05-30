import apiClient from "./index";
import type { AppRole } from "../app/menu";
import type { UserProfile } from "../types/user";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string | null;
  full_name?: string | null;
  role: AppRole;
  org_id: string;
}

export interface PendingApprovalResponse {
  status: "pending_approval";
}

export interface ApprovalUser {
  id: string;
  username: string;
  email: string | null;
  full_name: string | null;
  org_id: string | null;
  org_name: string | null;
  roles: AppRole[];
  approval_status: "approved" | "pending" | "rejected";
  created_at: string;
}

export type RegisterResponse = TokenResponse | PendingApprovalResponse;

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>("/auth/register", payload);
  return response.data;
}

export async function getMe(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>("/auth/me");
  return response.data;
}

export async function listApprovals(): Promise<ApprovalUser[]> {
  const response = await apiClient.get<ApprovalUser[]>("/auth/approvals");
  return response.data;
}

export async function approveRegistration(userId: string): Promise<ApprovalUser> {
  const response = await apiClient.post<ApprovalUser>(
    `/auth/approvals/${userId}/approve`
  );
  return response.data;
}

export async function rejectRegistration(userId: string): Promise<ApprovalUser> {
  const response = await apiClient.post<ApprovalUser>(
    `/auth/approvals/${userId}/reject`
  );
  return response.data;
}
