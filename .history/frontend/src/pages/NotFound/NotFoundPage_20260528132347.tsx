import { Button, Card, Typography } from "antd";
import { useNavigate } from "react-router-dom";

const { Title, Paragraph } = Typography;

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="state-shell">
      <Card className="state-card">
        <Title level={2}>页面未找到</Title>
        <Paragraph>页面不存在或已被移动。</Paragraph>
        <Button type="primary" onClick={() => navigate("/")}>返回首页</Button>
      </Card>
    </div>
  );
}
