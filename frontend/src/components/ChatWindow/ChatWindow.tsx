import { Button, Card, Input, Space, Typography } from "antd";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const { Text } = Typography;

export interface ChatMessageView {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

interface ChatWindowProps {
  placeholder?: string;
  messages: ChatMessageView[];
  onSend: (question: string) => void;
  isStreaming?: boolean;
}

const roleLabelMap: Record<ChatMessageView["role"], string> = {
  user: "你",
  assistant: "助手",
  system: "系统"
};

export function ChatWindow({
  placeholder = "输入问题，开始对话",
  messages,
  onSend,
  isStreaming = false
}: ChatWindowProps) {
  const [inputValue, setInputValue] = useState("");

  const handleSend = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) {
      return;
    }
    onSend(trimmed);
    setInputValue("");
  };

  return (
    <Card className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-message">
            <Text strong>系统</Text>
            <Text>选择知识库后开始提问。</Text>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="chat-message">
              <Text strong>{roleLabelMap[message.role]}</Text>
              <div className="chat-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          ))
        )}
      </div>
      <Space.Compact className="chat-input">
        <Input
          placeholder={placeholder}
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          onPressEnter={handleSend}
          disabled={isStreaming}
        />
        <Button type="primary" onClick={handleSend} disabled={isStreaming}>
          {isStreaming ? "生成中" : "发送"}
        </Button>
      </Space.Compact>
    </Card>
  );
}
