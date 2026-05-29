import { Button, Card, Col, Row, Select, Space, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";

import type { KnowledgeBaseItem } from "../../api/kb";
import { fetchKnowledgeBases } from "../../api/kb";
import type {
  ChatSessionItem,
  CitationItem,
  ChatStreamEvent
} from "../../api/chat";
import { fetchChatMessages, fetchChatSessions, streamChat } from "../../api/chat";
import { CitationPanel } from "../../components/CitationPanel/CitationPanel";
import { ChatWindow, type ChatMessageView } from "../../components/ChatWindow/ChatWindow";
import { KnowledgeBaseSelector } from "../../components/KnowledgeBaseSelector/KnowledgeBaseSelector";

const { Title, Paragraph, Text } = Typography;

export function ChatPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseItem[]>([]);
  const [selectedKbIds, setSelectedKbIds] = useState<string[]>([]);
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageView[]>([]);
  const [citations, setCitations] = useState<CitationItem[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sessionOptions = useMemo(
    () =>
      sessions.map((session) => ({
        value: session.id,
        label: session.title || "未命名会话"
      })),
    [sessions]
  );

  useEffect(() => {
    const loadInitial = async () => {
      try {
        const [kbItems, sessionItems] = await Promise.all([
          fetchKnowledgeBases(),
          fetchChatSessions()
        ]);
        setKnowledgeBases(kbItems);
        setSessions(sessionItems);
        if (sessionItems.length > 0) {
          const sessionId = sessionItems[0].id;
          setActiveSessionId(sessionId);
          await loadMessages(sessionId);
          setSelectedKbIds(sessionItems[0].kb_ids ?? []);
        }
      } catch (error) {
        message.error("加载知识库或会话失败");
      }
    };
    loadInitial();
  }, []);

  const loadMessages = async (sessionId: string) => {
    const items = await fetchChatMessages(sessionId);
    const viewMessages: ChatMessageView[] = items.map((item) => ({
      id: item.id,
      role: item.role,
      content: item.content
    }));
    setMessages(viewMessages);
    const lastAssistant = items.filter((item) => item.role === "assistant").pop();
    setCitations((lastAssistant?.citations ?? []) as CitationItem[]);
  };

  const handleSessionChange = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    const target = sessions.find((item) => item.id === sessionId);
    setSelectedKbIds(target?.kb_ids ?? []);
    await loadMessages(sessionId);
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
    setMessages([]);
    setCitations([]);
  };

  const handleSend = async (question: string) => {
    if (selectedKbIds.length === 0) {
      message.warning("请先选择知识库");
      return;
    }

    const userMessage: ChatMessageView = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question
    };
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: ChatMessageView = {
      id: assistantMessageId,
      role: "assistant",
      content: ""
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsStreaming(true);
    setCitations([]);

    const payload = {
      session_id: activeSessionId,
      question,
      kb_ids: selectedKbIds
    };

    await streamChat(payload, (event: ChatStreamEvent) => {
      if (event.type === "citations" && event.citations) {
        setCitations(event.citations as CitationItem[]);
      }

      if (event.type === "error") {
        message.error(event.content || "生成失败");
        setIsStreaming(false);
        return;
      }

      if (event.type === "delta" && event.content) {
        setMessages((prev) =>
          prev.map((item) =>
            item.id === assistantMessageId
              ? { ...item, content: item.content + event.content }
              : item
          )
        );
      }

      if (event.type === "done") {
        if (event.session_id) {
          setActiveSessionId(event.session_id);
        }
        setIsStreaming(false);
        fetchChatSessions()
          .then((items) => setSessions(items))
          .catch(() => null);
      }
    });
  };

  return (
    <div className="page-stack">
      <Card className="page-card">
        <Title level={3}>知识问答</Title>
        <Paragraph type="secondary">选择知识库后进行问答。</Paragraph>
        <div className="chat-toolbar">
          <KnowledgeBaseSelector
            items={knowledgeBases}
            value={selectedKbIds}
            onChange={setSelectedKbIds}
          />
          <Space size="middle" className="chat-session-actions">
            <Text type="secondary">会话</Text>
            <Select
              placeholder="选择会话"
              value={activeSessionId ?? undefined}
              onChange={handleSessionChange}
              options={sessionOptions}
              style={{ minWidth: 200 }}
            />
            <Button onClick={handleNewSession}>新建会话</Button>
          </Space>
        </div>
      </Card>
      <Row gutter={24}>
        <Col xs={24} lg={16}>
          <ChatWindow
            messages={messages}
            onSend={handleSend}
            isStreaming={isStreaming}
          />
        </Col>
        <Col xs={24} lg={8}>
          <CitationPanel items={citations} />
        </Col>
      </Row>
    </div>
  );
}
