import { Card, Typography } from "antd";

const { Title, Paragraph } = Typography;

export function AgentsPage() {
  return (
    <Card className="page-card">
      <Title level={3}>智能体中心</Title>
      <Paragraph type="secondary">管理入职智能体与报销助手（占位）。</Paragraph>
    </Card>
  );
}
