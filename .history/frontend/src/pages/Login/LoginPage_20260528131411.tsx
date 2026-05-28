import { useState } from "react";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { useNavigate } from "react-router-dom";

import { login, getMe } from "../../api/auth";
import { useAuthStore } from "../../stores/authStore";
import { useUserStore } from "../../stores/userStore";

const { Title, Paragraph, Text } = Typography;

interface LoginFormValues {
  username: string;
  password: string;
}

export function LoginPage() {
  const [loading, setLoading] = useState(false);
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useUserStore((state) => state.setUser);
  const navigate = useNavigate();

  async function handleSubmit(values: LoginFormValues) {
    setLoading(true);
    try {
      const tokenResponse = await login(values);
      setToken(tokenResponse.access_token);
      const profile = await getMe();
      setUser(profile);
      navigate("/");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <Card className="auth-card">
        <Title level={2}>登录</Title>
        <Paragraph type="secondary">
          使用本地账号登录以访问知识库与业务智能体。
        </Paragraph>
        <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
          <Form.Item
            label="账号"
            name="username"
            rules={[{ required: true, message: "请输入账号" }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={loading}>
            登录
          </Button>
        </Form>
        <Text type="secondary" className="auth-hint">
          v0 阶段默认本地账号密码，后续可扩展企业 SSO/OIDC。
        </Text>
      </Card>
    </div>
  );
}
