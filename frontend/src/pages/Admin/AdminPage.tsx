import { Card, Typography } from "antd";

const { Title, Paragraph } = Typography;

export function AdminPage() {
  return (
    <Card className="page-card">
      <Title level={3}>管理</Title>
      <Paragraph type="secondary">
        管理员配置组织、权限与知识库策略（占位）。
      </Paragraph>
    </Card>
  );
}
