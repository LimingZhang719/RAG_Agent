import { Button, Card, Input, Space, Typography } from "antd";

const { Text } = Typography;

interface ChatWindowProps {
  placeholder?: string;
}

export function ChatWindow({ placeholder = "输入问题，开始对话" }: ChatWindowProps) {
  return (
    <Card className="chat-window">
      <div className="chat-messages">
        <div className="chat-message">
          <Text strong>系统</Text>
          <Text>欢迎使用知识库问答（占位）。</Text>
        </div>
      </div>
      <Space.Compact className="chat-input">
        <Input placeholder={placeholder} />
        <Button type="primary">发送</Button>
      </Space.Compact>
    </Card>
  );
}
