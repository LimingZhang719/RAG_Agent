import { Button, Card, Typography } from "antd";
import { useNavigate } from "react-router-dom";

const { Title, Paragraph } = Typography;

export function ForbiddenPage() {
  const navigate = useNavigate();

  return (
    <div className="state-shell">
      <Card className="state-card">
        <Title level={2}>403 无权限</Title>
        <Paragraph>当前账号暂无访问权限，请联系管理员授权。</Paragraph>
        <Button type="primary" onClick={() => navigate("/")}>返回首页</Button>
      </Card>
    </div>
  );
}
