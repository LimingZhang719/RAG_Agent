import { Card, Col, Row, Typography } from "antd";

import { ChatWindow } from "../../components/ChatWindow/ChatWindow";
import { CitationPanel } from "../../components/CitationPanel/CitationPanel";

const { Title, Paragraph } = Typography;

export function ChatPage() {
  return (
    <div className="page-stack">
      <Card className="page-card">
        <Title level={3}>知识问答</Title>
        <Paragraph type="secondary">选择知识库后进行问答（占位）。</Paragraph>
      </Card>
      <Row gutter={24}>
        <Col xs={24} lg={16}>
          <ChatWindow />
        </Col>
        <Col xs={24} lg={8}>
          <CitationPanel />
        </Col>
      </Row>
    </div>
  );
}
