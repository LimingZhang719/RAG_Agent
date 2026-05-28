import { Card, Typography } from "antd";

const { Title, Paragraph } = Typography;

export function FinancePage() {
  return (
    <Card className="page-card">
      <Title level={3}>财务审批</Title>
      <Paragraph type="secondary">
        查看 AI 审核建议与风险项（占位）。
      </Paragraph>
    </Card>
  );
}
