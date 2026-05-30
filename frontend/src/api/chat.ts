import { message } from "antd";

import { useAuthStore } from "../stores/authStore";

export type ChatRole = "user" | "assistant" | "system";

export interface ChatSessionSettings {
  top_k: number;
  rerank_enabled: boolean;
  temperature: number;
  system_prompt?: string | null;
}

export interface ChatSessionItem {
  id: string;
  user_id: string;
  title?: string | null;
  kb_ids?: string[] | null;
  settings: ChatSessionSettings;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionUpdatePayload {
  title?: string | null;
  kb_ids?: string[] | null;
  settings?: ChatSessionSettings;
}

export interface ChatMessageItem {
  id: string;
  session_id: string;
  role: ChatRole;
  content: string;
  citations?: CitationItem[] | null;
  created_at: string;
}

export interface CitationItem {
  document_id: string;
  document_name: string;
  page_no?: number | null;
  chunk_id: string;
  snippet: string;
}

export interface ChatStreamEvent {
  type: "delta" | "citations" | "done" | "error";
  content?: string;
  citations?: CitationItem[];
  session_id?: string;
  message_id?: string;
}

export interface ChatStreamPayload {
  session_id?: string | null;
  question: string;
  kb_ids: string[];
  top_k?: number;
  rerank_enabled?: boolean;
  temperature?: number;
  system_prompt?: string | null;
}

const getApiBaseUrl = () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
  return baseUrl.replace(/\/$/, "");
};

export async function fetchChatSessions(): Promise<ChatSessionItem[]> {
  const response = await fetch(`${getApiBaseUrl()}/chat/sessions`, {
    headers: buildAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to load sessions");
  }
  return response.json();
}

export async function updateChatSession(
  sessionId: string,
  payload: ChatSessionUpdatePayload
): Promise<ChatSessionItem> {
  const response = await fetch(`${getApiBaseUrl()}/chat/sessions/${sessionId}`, {
    method: "PATCH",
    headers: {
      ...buildAuthHeaders(),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to update session");
  }
  return response.json();
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: buildAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to delete session");
  }
}

export async function fetchChatMessages(
  sessionId: string
): Promise<ChatMessageItem[]> {
  const response = await fetch(
    `${getApiBaseUrl()}/chat/messages?session_id=${sessionId}`,
    {
      headers: buildAuthHeaders()
    }
  );
  if (!response.ok) {
    throw new Error("Failed to load messages");
  }
  const data = await response.json();
  return data.items ?? [];
}

export async function streamChat(
  payload: ChatStreamPayload,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/chat/stream`, {
    method: "POST",
    headers: {
      ...buildAuthHeaders(),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok || !response.body) {
    const errorText = await response.text();
    message.error(errorText || "请求失败");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) {
        continue;
      }
      const payloadText = line.slice(5).trim();
      if (!payloadText) {
        continue;
      }
      try {
        const event = JSON.parse(payloadText) as ChatStreamEvent;
        onEvent(event);
      } catch {
        message.error("流式数据解析失败");
      }
    }
  }
}

const buildAuthHeaders = (): Record<string, string> => {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
};
