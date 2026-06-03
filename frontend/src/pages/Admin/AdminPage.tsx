import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message
} from "antd";
import type { ColumnsType } from "antd/es/table";

import type { AppRole } from "../../app/menu";
import {
  approveRegistration,
  listApprovals,
  rejectRegistration
} from "../../api/auth";
import type { ApprovalUser } from "../../api/auth";
import { createTravelStandard, fetchTravelStandards } from "../../api/expense";
import { fetchSystemSettings, upsertSystemSetting } from "../../api/settings";
import { useUserStore } from "../../stores/userStore";
import type { TravelExpenseStandard } from "../../types/expense";
import type { SystemSetting } from "../../types/settings";

const { Title, Paragraph, Text } = Typography;

const roleLabels: Record<AppRole, string> = {
  admin: "系统管理员",
  department_admin: "部门管理员",
  user: "普通用户",
  finance: "财务用户"
};

export function AdminPage() {
  const [approvals, setApprovals] = useState<ApprovalUser[]>([]);
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [standards, setStandards] = useState<TravelExpenseStandard[]>([]);
  const [loading, setLoading] = useState(false);
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [settingsForm] = Form.useForm();
  const [standardForm] = Form.useForm();
  const currentUser = useUserStore((state) => state.user);

  const canReviewDepartmentAdmins = currentUser?.roles.includes("admin");
  const canReviewUsers = currentUser?.roles.includes("department_admin");
  const reviewScope = canReviewDepartmentAdmins
    ? "可审核部门管理员注册申请"
    : canReviewUsers
      ? "可审核本部门普通员工注册申请"
      : "当前账号没有注册审核权限";

  async function loadApprovals() {
    setLoading(true);
    try {
      setApprovals(await listApprovals());
    } catch (error) {
      message.error(error instanceof Error ? error.message : "审核列表加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadAdminConfig() {
    try {
      const [settingItems, standardItems] = await Promise.all([
        fetchSystemSettings(),
        fetchTravelStandards()
      ]);
      setSettings(settingItems);
      setStandards(standardItems);
    } catch {
      setSettings([]);
      setStandards([]);
    }
  }

  async function handleReview(userId: string, approved: boolean) {
    setSubmittingId(userId);
    try {
      if (approved) {
        await approveRegistration(userId);
        message.success("已通过注册申请");
      } else {
        await rejectRegistration(userId);
        message.success("已拒绝注册申请");
      }
      await loadApprovals();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "审核操作失败");
    } finally {
      setSubmittingId(null);
    }
  }

  async function handleSaveSetting(values: {
    key: string;
    value?: string;
    value_type: "string" | "number" | "boolean" | "json" | "secret";
    group_name: string;
    description?: string;
  }) {
    try {
      let parsedValue: unknown = values.value;
      if (values.value_type === "number") {
        parsedValue = Number(values.value);
      } else if (values.value_type === "boolean") {
        parsedValue = values.value === "true";
      } else if (values.value_type === "json") {
        parsedValue = values.value ? JSON.parse(values.value) : {};
      }
      await upsertSystemSetting({
        ...values,
        value: parsedValue,
        is_secret: values.value_type === "secret"
      });
      message.success("系统配置已保存");
      settingsForm.resetFields();
      await loadAdminConfig();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "配置保存失败");
    }
  }

  async function handleCreateStandard(values: {
    name: string;
    city_tier?: string;
    daily_limit?: number;
    single_trip_limit?: number;
  }) {
    try {
      await createTravelStandard({ ...values, currency: "CNY", is_active: true });
      message.success("差旅标准已保存");
      standardForm.resetFields();
      await loadAdminConfig();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "差旅标准保存失败");
    }
  }

  useEffect(() => {
    void loadApprovals();
    void loadAdminConfig();
  }, []);

  const columns: ColumnsType<ApprovalUser> = [
    {
      title: "账号",
      dataIndex: "username",
      key: "username",
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.full_name || record.username}</Text>
          <Text type="secondary">{record.username}</Text>
        </Space>
      )
    },
    {
      title: "邮箱",
      dataIndex: "email",
      key: "email",
      render: (email) => email || "-"
    },
    {
      title: "角色",
      dataIndex: "roles",
      key: "roles",
      render: (roles: AppRole[]) => (
        <Space wrap>
          {roles.map((role) => (
            <Tag key={role}>{roleLabels[role] ?? role}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: "组织/部门",
      dataIndex: "org_name",
      key: "org_name",
      render: (orgName) => orgName || "-"
    },
    {
      title: "提交时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (value) => new Date(value).toLocaleString()
    },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            loading={submittingId === record.id}
            onClick={() => void handleReview(record.id, true)}
          >
            通过
          </Button>
          <Button
            danger
            size="small"
            loading={submittingId === record.id}
            onClick={() => void handleReview(record.id, false)}
          >
            拒绝
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div className="page-stack">
      <Tabs
        items={[
          {
            key: "approvals",
            label: "注册审核",
            children: (
              <Card className="page-card">
                <Title level={3}>注册审核</Title>
                <Paragraph type="secondary">{reviewScope}</Paragraph>
                <Table
                  rowKey="id"
                  loading={loading}
                  columns={columns}
                  dataSource={approvals}
                  pagination={{ pageSize: 10 }}
                  locale={{ emptyText: "暂无待审核注册申请" }}
                />
              </Card>
            )
          },
          {
            key: "settings",
            label: "系统配置",
            children: (
              <Card className="page-card">
                <Title level={3}>运行配置</Title>
                <Paragraph type="secondary">
                  维护模型、OCR、RAG、系统提示词和报销规则等运行时配置。
                </Paragraph>
                <Form
                  form={settingsForm}
                  layout="inline"
                  initialValues={{ value_type: "string", group_name: "expense" }}
                  onFinish={handleSaveSetting}
                >
                  <Form.Item name="key" rules={[{ required: true }]}>
                    <Input placeholder="配置键，如 expense.invoice_title" />
                  </Form.Item>
                  <Form.Item name="value_type">
                    <Select
                      style={{ width: 120 }}
                      options={["string", "number", "boolean", "json", "secret"].map(
                        (item) => ({ label: item, value: item })
                      )}
                    />
                  </Form.Item>
                  <Form.Item name="group_name">
                    <Input placeholder="分组" />
                  </Form.Item>
                  <Form.Item name="value">
                    <Input placeholder="配置值" />
                  </Form.Item>
                  <Form.Item name="description">
                    <Input placeholder="说明" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit">
                    保存配置
                  </Button>
                </Form>
                <Table
                  style={{ marginTop: 20 }}
                  rowKey="id"
                  dataSource={settings}
                  pagination={{ pageSize: 8 }}
                  columns={[
                    { title: "键", dataIndex: "key" },
                    { title: "分组", dataIndex: "group_name" },
                    { title: "类型", dataIndex: "value_type" },
                    {
                      title: "值",
                      dataIndex: "value",
                      render: (value) => JSON.stringify(value)
                    },
                    { title: "说明", dataIndex: "description" }
                  ]}
                />
              </Card>
            )
          },
          {
            key: "travel",
            label: "差旅标准",
            children: (
              <Card className="page-card">
                <Title level={3}>差旅金额标准</Title>
                <Form form={standardForm} layout="inline" onFinish={handleCreateStandard}>
                  <Form.Item name="name" rules={[{ required: true }]}>
                    <Input placeholder="标准名称" />
                  </Form.Item>
                  <Form.Item name="city_tier">
                    <Select
                      placeholder="城市级别"
                      style={{ width: 140 }}
                      options={[
                        { label: "一线城市", value: "tier1" },
                        { label: "二线城市", value: "tier2" },
                        { label: "其他", value: "other" }
                      ]}
                    />
                  </Form.Item>
                  <Form.Item name="daily_limit">
                    <InputNumber min={0} precision={2} placeholder="每日限额" />
                  </Form.Item>
                  <Form.Item name="single_trip_limit">
                    <InputNumber min={0} precision={2} placeholder="单次限额" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit">
                    保存标准
                  </Button>
                </Form>
                <Table
                  style={{ marginTop: 20 }}
                  rowKey="id"
                  dataSource={standards}
                  pagination={{ pageSize: 8 }}
                  columns={[
                    { title: "名称", dataIndex: "name" },
                    { title: "城市级别", dataIndex: "city_tier" },
                    { title: "每日限额", dataIndex: "daily_limit" },
                    { title: "单次限额", dataIndex: "single_trip_limit" },
                    { title: "币种", dataIndex: "currency" },
                    {
                      title: "状态",
                      dataIndex: "is_active",
                      render: (value) => (
                        <Tag color={value ? "green" : "default"}>
                          {value ? "启用" : "停用"}
                        </Tag>
                      )
                    }
                  ]}
                />
              </Card>
            )
          }
        ]}
      />
    </div>
  );
}
