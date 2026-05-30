import { DeleteOutlined, SettingOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Divider,
  Drawer,
  Input,
  InputNumber,
  Popconfirm,
  Row,
  Select,
  Slider,
  Space,
  Switch,
  Typography,
  message
} from "antd";
import { useEffect, useMemo, useState } from "react";

import type { KnowledgeBaseItem } from "../../api/kb";
import { fetchKnowledgeBases } from "../../api/kb";
import type {
  ChatSessionItem,
  ChatSessionSettings,
  CitationItem,
  ChatStreamEvent
} from "../../api/chat";
import {
  deleteChatSession,
  fetchChatMessages,
  fetchChatSessions,
  streamChat,
  updateChatSession
} from "../../api/chat";
import { CitationPanel } from "../../components/CitationPanel/CitationPanel";
import { ChatWindow, type ChatMessageView } from "../../components/ChatWindow/ChatWindow";
import { KnowledgeBaseSelector } from "../../components/KnowledgeBaseSelector/KnowledgeBaseSelector";

const { Title, Paragraph, Text } = Typography;
const SESSION_TITLE_LIMIT = 14;
const DEFAULT_SESSION_SETTINGS: ChatSessionSettings = {
  top_k: 8,
  rerank_enabled: false,
  temperature: 0.7,
  system_prompt: null
};

const formatSessionTitle = (title?: string | null) => {
  const normalizedTitle = title?.trim() || "未命名会话";
  const chars = Array.from(normalizedTitle);
  return chars.length > SESSION_TITLE_LIMIT
    ? `${chars.slice(0, SESSION_TITLE_LIMIT).join("")}...`
    : normalizedTitle;
};

const normalizeSessionSettings = (
  settings?: Partial<ChatSessionSettings> | null
): ChatSessionSettings => ({
  ...DEFAULT_SESSION_SETTINGS,
  ...settings,
  system_prompt: settings?.system_prompt ?? null
});

export function ChatPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseItem[]>([]);
  const [selectedKbIds, setSelectedKbIds] = useState<string[]>([]);
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageView[]>([]);
  const [citations, setCitations] = useState<CitationItem[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionSettings, setSessionSettings] = useState<ChatSessionSettings>(
    DEFAULT_SESSION_SETTINGS
  );
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [isDeletingSession, setIsDeletingSession] = useState(false);

  const sessionOptions = useMemo(
    () =>
      sessions.map((session) => ({
        value: session.id,
        label: formatSessionTitle(session.title)
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
          setSessionSettings(normalizeSessionSettings(sessionItems[0].settings));
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
    setSessionSettings(normalizeSessionSettings(target?.settings));
    await loadMessages(sessionId);
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
    setMessages([]);
    setCitations([]);
    setSessionSettings(DEFAULT_SESSION_SETTINGS);
  };

  const handleSaveSettings = async () => {
    if (!activeSessionId) {
      message.info("设置将在发送首个问题后保存到新会话");
      setIsSettingsOpen(false);
      return;
    }
    setIsSavingSettings(true);
    try {
      const updated = await updateChatSession(activeSessionId, {
        settings: sessionSettings
      });
      setSessions((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item))
      );
      setSessionSettings(normalizeSessionSettings(updated.settings));
      message.success("会话设置已保存");
      setIsSettingsOpen(false);
    } catch (error) {
      message.error("会话设置保存失败");
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!activeSessionId) {
      return;
    }
    setIsDeletingSession(true);
    try {
      await deleteChatSession(activeSessionId);
      const remainingSessions = sessions.filter(
        (item) => item.id !== activeSessionId
      );
      setSessions(remainingSessions);
      setIsSettingsOpen(false);
      setMessages([]);
      setCitations([]);

      if (remainingSessions.length > 0) {
        const nextSession = remainingSessions[0];
        setActiveSessionId(nextSession.id);
        setSelectedKbIds(nextSession.kb_ids ?? []);
        setSessionSettings(normalizeSessionSettings(nextSession.settings));
        await loadMessages(nextSession.id);
      } else {
        setActiveSessionId(null);
        setSelectedKbIds([]);
        setSessionSettings(DEFAULT_SESSION_SETTINGS);
      }
      message.success("会话已删除");
    } catch (error) {
      message.error("会话删除失败");
    } finally {
      setIsDeletingSession(false);
    }
  };

  const handleResetSettings = () => {
    setSessionSettings(DEFAULT_SESSION_SETTINGS);
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
      kb_ids: selectedKbIds,
      top_k: sessionSettings.top_k,
      rerank_enabled: sessionSettings.rerank_enabled,
      temperature: sessionSettings.temperature,
      system_prompt: sessionSettings.system_prompt
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
          .then((items) => {
            setSessions(items);
            const currentSession = items.find(
              (item) => item.id === event.session_id
            );
            if (currentSession) {
              setSessionSettings(
                normalizeSessionSettings(currentSession.settings)
              );
            }
          })
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
            <div className="chat-session-field">
              <Text type="secondary">会话</Text>
              <Select
                placeholder="选择会话"
                value={activeSessionId ?? undefined}
                onChange={handleSessionChange}
                options={sessionOptions}
                style={{ width: "100%" }}
              />
            </div>
            <Button onClick={handleNewSession}>新建会话</Button>
            <Button
              icon={<SettingOutlined />}
              onClick={() => setIsSettingsOpen(true)}
            >
              设置
            </Button>
          </Space>
        </div>
      </Card>
      <Drawer
        title="会话设置"
        open={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        width={420}
        destroyOnClose
        extra={
          <Space>
            <Button onClick={handleResetSettings} disabled={isStreaming}>
              恢复默认
            </Button>
            <Button
              type="primary"
              onClick={handleSaveSettings}
              loading={isSavingSettings}
              disabled={isStreaming}
            >
              保存
            </Button>
          </Space>
        }
      >
        <div className="chat-settings">
          <div className="chat-settings-field">
            <Text strong>Top K</Text>
            <InputNumber
              min={1}
              max={50}
              value={sessionSettings.top_k}
              onChange={(value) =>
                setSessionSettings((prev) => ({
                  ...prev,
                  top_k: value ?? DEFAULT_SESSION_SETTINGS.top_k
                }))
              }
              style={{ width: "100%" }}
              disabled={isStreaming}
            />
          </div>
          <div className="chat-settings-row">
            <div>
              <Text strong>启用 Rerank</Text>
              <Text type="secondary">对召回结果进行重排</Text>
            </div>
            <Switch
              checked={sessionSettings.rerank_enabled}
              onChange={(checked) =>
                setSessionSettings((prev) => ({
                  ...prev,
                  rerank_enabled: checked
                }))
              }
              disabled={isStreaming}
            />
          </div>
          <div className="chat-settings-field">
            <Text strong>Temperature</Text>
            <Space.Compact className="chat-settings-temperature">
              <Slider
                min={0}
                max={2}
                step={0.1}
                value={sessionSettings.temperature}
                onChange={(value) =>
                  setSessionSettings((prev) => ({
                    ...prev,
                    temperature: value
                  }))
                }
                disabled={isStreaming}
              />
              <InputNumber
                min={0}
                max={2}
                step={0.1}
                value={sessionSettings.temperature}
                onChange={(value) =>
                  setSessionSettings((prev) => ({
                    ...prev,
                    temperature: value ?? DEFAULT_SESSION_SETTINGS.temperature
                  }))
                }
                disabled={isStreaming}
              />
            </Space.Compact>
          </div>
          <div className="chat-settings-field">
            <Text strong>系统提示词</Text>
            <Input.TextArea
              rows={8}
              maxLength={4000}
              showCount
              value={sessionSettings.system_prompt ?? ""}
              onChange={(event) =>
                setSessionSettings((prev) => ({
                  ...prev,
                  system_prompt: event.target.value || null
                }))
              }
              disabled={isStreaming}
            />
          </div>
          <Divider />
          <div className="chat-settings-danger">
            <Text strong>危险操作</Text>
            <Popconfirm
              title="确认删除当前会话？"
              description="该操作会删除当前会话及其消息记录。"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={handleDeleteSession}
              disabled={!activeSessionId || isStreaming}
            >
              <Button
                danger
                icon={<DeleteOutlined />}
                loading={isDeletingSession}
                disabled={!activeSessionId || isStreaming}
              >
                删除当前会话
              </Button>
            </Popconfirm>
          </div>
        </div>
      </Drawer>
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
