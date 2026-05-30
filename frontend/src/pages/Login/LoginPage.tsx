import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Form, Input, Select, Tabs, Typography, message } from "antd";
import type { AxiosError } from "axios";
import { useLocation, useNavigate } from "react-router-dom";

import type { AppRole } from "../../app/menu";
import { getMe, login, register } from "../../api/auth";
import type { RegisterRequest, RegisterResponse } from "../../api/auth";
import { listOrganizations } from "../../api/organizations";
import type { OrganizationOption } from "../../api/organizations";
import { useAuthStore } from "../../stores/authStore";
import { useUserStore } from "../../stores/userStore";

const { Title, Paragraph, Text } = Typography;

interface LoginFormValues {
  username: string;
  password: string;
}

interface RegisterFormValues extends LoginFormValues {
  email?: string;
  full_name?: string;
  role: AppRole;
  org_id: string;
}

const roleOptions: Array<{ label: string; value: AppRole }> = [
  { label: "系统管理员", value: "admin" },
  { label: "部门管理员", value: "department_admin" },
  { label: "普通用户", value: "user" },
  { label: "财务用户", value: "finance" }
];

function getApiErrorMessage(error: unknown, fallback: string): string {
  const axiosError = error as AxiosError<{ message?: string }>;
  return axiosError.response?.data?.message ?? (error instanceof Error ? error.message : fallback);
}

function isTokenResponse(response: RegisterResponse): response is Exclude<RegisterResponse, { status: string }> {
  return "access_token" in response;
}

export function LoginPage() {
  const [activeTab, setActiveTab] = useState("login");
  const [loading, setLoading] = useState(false);
  const [organizationsLoading, setOrganizationsLoading] = useState(false);
  const [organizations, setOrganizations] = useState<OrganizationOption[]>([]);
  const [pendingApproval, setPendingApproval] = useState(false);
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useUserStore((state) => state.setUser);
  const navigate = useNavigate();
  const location = useLocation();

  const from = useMemo(() => {
    const state = location.state as { from?: string } | null;
    return state?.from || "/";
  }, [location.state]);

  useEffect(() => {
    if (activeTab !== "register" || organizations.length > 0) {
      return;
    }

    setOrganizationsLoading(true);
    listOrganizations()
      .then(setOrganizations)
      .catch((error) => {
        message.error(getApiErrorMessage(error, "组织列表加载失败"));
      })
      .finally(() => setOrganizationsLoading(false));
  }, [activeTab, organizations.length]);

  async function restoreSession(accessToken: string) {
    setToken(accessToken);
    const profile = await getMe();
    setUser(profile);
    navigate(from);
  }

  async function handleLogin(values: LoginFormValues) {
    setLoading(true);
    try {
      const tokenResponse = await login(values);
      await restoreSession(tokenResponse.access_token);
    } catch (error) {
      message.error(getApiErrorMessage(error, "登录失败"));
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(values: RegisterFormValues) {
    setLoading(true);
    setPendingApproval(false);
    try {
      const payload: RegisterRequest = {
        username: values.username,
        password: values.password,
        email: values.email?.trim() || null,
        full_name: values.full_name?.trim() || null,
        role: values.role,
        org_id: values.org_id
      };
      const response = await register(payload);
      if (!isTokenResponse(response)) {
        setPendingApproval(true);
        message.info("注册已提交，等待审核通过后可登录");
        return;
      }

      await restoreSession(response.access_token);
    } catch (error) {
      message.error(getApiErrorMessage(error, "注册失败"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <Card className="auth-card">
        <Title level={2}>账号入口</Title>
        <Paragraph type="secondary">
          登录或注册账号后访问知识库、业务智能体和财务流程。
        </Paragraph>

        {pendingApproval ? (
          <Alert
            className="auth-alert"
            type="info"
            showIcon
            message="注册申请待审核"
            description="部门管理员和普通用户需要审核通过后才能登录系统。"
          />
        ) : null}

        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key);
            setPendingApproval(false);
          }}
          items={[
            {
              key: "login",
              label: "登录",
              children: (
                <Form layout="vertical" onFinish={handleLogin} requiredMark={false}>
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
              )
            },
            {
              key: "register",
              label: "注册",
              children: (
                <Form layout="vertical" onFinish={handleRegister} requiredMark={false}>
                  <Form.Item
                    label="账号"
                    name="username"
                    rules={[
                      { required: true, message: "请输入账号" },
                      { min: 3, message: "账号至少 3 个字符" }
                    ]}
                  >
                    <Input placeholder="请输入用户名" />
                  </Form.Item>
                  <Form.Item
                    label="密码"
                    name="password"
                    rules={[
                      { required: true, message: "请输入密码" },
                      { min: 6, message: "密码至少 6 个字符" }
                    ]}
                  >
                    <Input.Password placeholder="请输入密码" />
                  </Form.Item>
                  <Form.Item label="邮箱" name="email">
                    <Input placeholder="可选" />
                  </Form.Item>
                  <Form.Item label="姓名" name="full_name">
                    <Input placeholder="可选" />
                  </Form.Item>
                  <Form.Item
                    label="角色"
                    name="role"
                    rules={[{ required: true, message: "请选择角色" }]}
                  >
                    <Select placeholder="请选择角色" options={roleOptions} />
                  </Form.Item>
                  <Form.Item
                    label="组织/部门"
                    name="org_id"
                    rules={[{ required: true, message: "请选择组织/部门" }]}
                  >
                    <Select
                      showSearch
                      loading={organizationsLoading}
                      placeholder="请选择组织/部门"
                      optionFilterProp="label"
                      options={organizations.map((organization) => ({
                        label: organization.name,
                        value: organization.id
                      }))}
                    />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block loading={loading}>
                    注册
                  </Button>
                </Form>
              )
            }
          ]}
        />
        <Text type="secondary" className="auth-hint">
          注册为部门管理员或普通用户时，账号会先进入待审核状态。
        </Text>
      </Card>
    </div>
  );
}
