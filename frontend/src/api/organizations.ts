import apiClient from "./index";

export interface OrganizationOption {
  id: string;
  name: string;
  parent_id: string | null;
  path: string | null;
}

export async function listOrganizations(): Promise<OrganizationOption[]> {
  const response = await apiClient.get<OrganizationOption[]>("/organizations");
  return response.data;
}
