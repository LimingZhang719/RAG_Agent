import { Button, Card, Input, Space, Typography } from "antd";
import { useEffect, useRef, useState } from "react";
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

export function ChatWindow({
  placeholder = "输入问题，开始对话",
  messages,
  onSend,
  isStreaming = false
}: ChatWindowProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const messagesElement = messagesRef.current;
    if (!messagesElement) {
      return;
    }
    messagesElement.scrollTo({
      top: messagesElement.scrollHeight,
      behavior: "smooth"
    });
  }, [messages]);

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
      <div className="chat-messages" ref={messagesRef}>
        {messages.length === 0 ? (
          <div className="chat-message chat-message-system">
            <div className="chat-bubble">
              <Text strong>系统</Text>
              <Text>选择知识库后开始提问。</Text>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`chat-message chat-message-${message.role}`}
            >
              <div className="chat-bubble">
                <div className="chat-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
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
