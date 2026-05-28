import { Card, Typography } from "antd";

const { Title, Paragraph } = Typography;

export function KnowledgeBasePage() {
  return (
    <Card className="page-card">
      <Title level={3}>知识库管理</Title>
      <Paragraph type="secondary">
        在此管理公司级、部门级与个人级知识库（占位）。
      </Paragraph>
    </Card>
  );
}
