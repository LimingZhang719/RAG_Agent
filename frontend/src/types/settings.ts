export type SettingValueType = "string" | "number" | "boolean" | "json" | "secret";

export interface SystemSetting {
  id: string;
  key: string;
  value: unknown;
  value_type: SettingValueType;
  group_name: string;
  description?: string | null;
  is_secret: boolean;
  is_runtime_editable: boolean;
  updated_by?: string | null;
  created_at: string;
  updated_at: string;
}
