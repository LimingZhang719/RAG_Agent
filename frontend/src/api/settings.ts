import apiClient from "./index";
import type { SettingValueType, SystemSetting } from "../types/settings";

export async function fetchSystemSettings(): Promise<SystemSetting[]> {
  const response = await apiClient.get<SystemSetting[]>("/settings");
  return response.data;
}

export async function upsertSystemSetting(payload: {
  key: string;
  value: unknown;
  value_type: SettingValueType;
  group_name: string;
  description?: string;
  is_secret?: boolean;
  is_runtime_editable?: boolean;
}): Promise<SystemSetting> {
  const response = await apiClient.put<SystemSetting>("/settings", payload);
  return response.data;
}
