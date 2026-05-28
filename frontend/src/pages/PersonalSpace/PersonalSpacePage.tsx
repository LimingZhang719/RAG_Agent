import { Card, Typography } from "antd";

import { FileUploader } from "../../components/FileUploader/FileUploader";

const { Title, Paragraph } = Typography;

export function PersonalSpacePage() {
  return (
    <div className="page-stack">
      <Card className="page-card">
        <Title level={3}>个人空间</Title>
        <Paragraph type="secondary">
          管理个人知识库与私有文档（占位）。
        </Paragraph>
      </Card>
      <FileUploader title="上传个人知识文档" />
    </div>
  );
}
