import apiClient from "./index";

export type VisibilityScope = "company" | "department" | "personal";
export type ChunkMethod = "sentence" | "token";

export interface KnowledgeBaseItem {
  id: string;
  name: string;
  description?: string | null;
  visibility_scope: VisibilityScope;
  org_id?: string | null;
  owner_id?: string | null;
  is_active: boolean;
  chunk_method: ChunkMethod;
  chunk_size: number;
  chunk_overlap: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseCreatePayload {
  name: string;
  description?: string | null;
  visibility_scope: VisibilityScope;
  org_id?: string | null;
  chunk_method?: ChunkMethod;
  chunk_size?: number;
  chunk_overlap?: number;
}

export async function fetchKnowledgeBases(): Promise<KnowledgeBaseItem[]> {
  const response = await apiClient.get("/knowledge-bases");
  return response.data;
}

export async function createKnowledgeBase(
  payload: KnowledgeBaseCreatePayload
): Promise<KnowledgeBaseItem> {
  const response = await apiClient.post("/knowledge-bases", payload);
  return response.data;
}
