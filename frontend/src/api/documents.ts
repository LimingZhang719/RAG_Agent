import apiClient from "./index";

export interface DocumentItem {
  id: string;
  kb_id: string;
  file_name: string;
  file_uri: string;
  file_type: string;
  size: number;
  status: "pending" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
  error_message?: string | null;
  created_by?: string | null;
  chunk_method?: "sentence" | "token" | null;
  chunk_size?: number | null;
  chunk_overlap?: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
}

export interface ChunkItem {
  id: string;
  document_id: string;
  content: string;
  content_hash: string;
  page_no?: number | null;
  block_order?: number | null;
  section_path?: string | null;
  is_deterministic_rule: boolean;
  rule_name?: string | null;
}

export interface ChunkListResponse {
  items: ChunkItem[];
}

export async function fetchDocuments(kbId: string): Promise<DocumentItem[]> {
  const response = await apiClient.get<DocumentListResponse>("/documents", {
    params: { kb_id: kbId }
  });
  return response.data.items;
}

export async function uploadDocument(
  kbId: string,
  file: File,
  title?: string
): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("kb_id", kbId);
  formData.append("file", file);
  if (title) {
    formData.append("title", title);
  }
  const response = await apiClient.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}

export async function retryDocument(docId: string): Promise<void> {
  await apiClient.post(`/documents/${docId}/retry`);
}

export async function fetchDocumentChunks(docId: string): Promise<ChunkItem[]> {
  const response = await apiClient.get<ChunkListResponse>(
    `/documents/${docId}/chunks`
  );
  return response.data.items;
}

export async function updateDocumentChunking(
  docId: string,
  payload: {
    chunk_method: "sentence" | "token";
    chunk_size: number;
    chunk_overlap: number;
  }
): Promise<DocumentItem> {
  const response = await apiClient.patch(`/documents/${docId}/chunking`, payload);
  return response.data;
}
