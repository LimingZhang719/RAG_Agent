import { useEffect, useState } from "react";
import { Button, Card, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";

import type { AppRole } from "../../app/menu";
import {
  approveRegistration,
  listApprovals,
  rejectRegistration
} from "../../api/auth";
import type { ApprovalUser } from "../../api/auth";
import { useUserStore } from "../../stores/userStore";

const { Title, Paragraph, Text } = Typography;

const roleLabels: Record<AppRole, string> = {
  admin: "系统管理员",
  department_admin: "部门管理员",
  user: "普通用户",
  finance: "财务用户"
};

export function AdminPage() {
  const [approvals, setApprovals] = useState<ApprovalUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [submittingId, setSubmittingId] = useState<string | null>(null);
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
      const data = await listApprovals();
      setApprovals(data);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "审核列表加载失败");
    } finally {
      setLoading(false);
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

  useEffect(() => {
    void loadApprovals();
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
    </div>
  );
}
