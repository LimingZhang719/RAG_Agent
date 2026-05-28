import { Card, Typography } from "antd";

import { FileUploader } from "../../components/FileUploader/FileUploader";

const { Title, Paragraph } = Typography;

export function ExpensePage() {
  return (
    <div className="page-stack">
      <Card className="page-card">
        <Title level={3}>报销助手</Title>
        <Paragraph type="secondary">
          上传发票、水单与审批单，智能体将完成材料校验（占位）。
        </Paragraph>
      </Card>
      <FileUploader title="上传报销材料" />
    </div>
  );
}
