import type { AppRole } from "../app/menu";

export interface UserProfile {
  id: string;
  username: string;
  email: string | null;
  full_name: string | null;
  org_id: string | null;
  roles: AppRole[];
  is_active: boolean;
  last_login_at: string | null;
}
