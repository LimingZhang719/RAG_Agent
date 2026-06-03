import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Input,
  Space,
  Table,
  Tag,
  Timeline,
  Typography,
  message
} from "antd";
import type { ColumnsType } from "antd/es/table";

import {
  fetchApprovalLogs,
  fetchExpenseAttachmentSource,
  fetchFinanceTasks,
  reviewFinanceTask
} from "../../api/expense";
import type { ExpenseApprovalLog, ExpenseClaim } from "../../types/expense";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const resultColors: Record<string, string> = {
  pass: "green",
  attention: "gold",
  risk: "red"
};

export function FinancePage() {
  const [tasks, setTasks] = useState<ExpenseClaim[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [logs, setLogs] = useState<ExpenseApprovalLog[]>([]);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const activeTask = useMemo(
    () => tasks.find((item) => item.id === activeId) ?? null,
    [tasks, activeId]
  );

  async function loadTasks() {
    setLoading(true);
    try {
      const data = await fetchFinanceTasks();
      setTasks(data);
      setActiveId((current) => current ?? data[0]?.id ?? null);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "财务待办加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadLogs(claimId: string) {
    try {
      setLogs(await fetchApprovalLogs(claimId));
    } catch {
      setLogs([]);
    }
  }

  async function handleReview(action: "approve" | "reject" | "request-supplement") {
    if (!activeTask) {
      return;
    }
    setSubmitting(true);
    try {
      await reviewFinanceTask(activeTask.id, action, comment);
      message.success("审批操作已记录");
      setComment("");
      await loadTasks();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "审批操作失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleOpenAttachment(attachmentId: string) {
    if (!activeTask) {
      return;
    }
    try {
      const blob = await fetchExpenseAttachmentSource(activeTask.id, attachmentId);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "附件打开失败");
    }
  }

  useEffect(() => {
    void loadTasks();
  }, []);

  useEffect(() => {
    if (activeId) {
      void loadLogs(activeId);
    }
  }, [activeId]);

  const columns: ColumnsType<ExpenseClaim> = [
    {
      title: "报销单",
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.title || record.claim_no}</Text>
          <Text type="secondary">{record.claim_no}</Text>
        </Space>
      )
    },
    {
      title: "金额",
      render: (_, record) =>
        record.total_amount ? `${record.total_amount} ${record.currency}` : "-"
    },
    {
      title: "状态",
      dataIndex: "status",
      render: (value: ExpenseClaim["status"]) => <Tag>{value}</Tag>
    },
    {
      title: "风险等级",
      render: (_, record) => {
        const level = record.audit_summary?.level;
        return level ? <Tag color={resultColors[level]}>{level}</Tag> : "-";
      }
    },
    {
      title: "提交时间",
      dataIndex: "submitted_at",
      render: (value) => (value ? new Date(value).toLocaleString() : "-")
    }
  ];

  return (
    <div className="page-stack">
      <Card className="page-card">
        <Title level={3}>财务审批</Title>
        <Paragraph type="secondary">
          查看 AI 初审建议、附件 OCR 字段和审批操作日志。
        </Paragraph>
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={tasks}
          rowClassName={(record) => (record.id === activeId ? "table-row-active" : "")}
          onRow={(record) => ({ onClick: () => setActiveId(record.id) })}
          pagination={{ pageSize: 8 }}
        />
      </Card>

      {activeTask ? (
        <Card className="page-card" title={activeTask.title || activeTask.claim_no}>
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <Paragraph>{activeTask.audit_summary?.summary || "暂无审核摘要"}</Paragraph>
            <Table
              rowKey="id"
              columns={[
                { title: "审核项", dataIndex: "name" },
                {
                  title: "结果",
                  dataIndex: "result",
                  render: (value) => <Tag color={resultColors[value]}>{value}</Tag>
                },
                { title: "证据", dataIndex: "evidence" }
              ]}
              dataSource={activeTask.audit_items}
              pagination={false}
            />

            <div>
              <Title level={5}>附件与 OCR 字段</Title>
              <Space direction="vertical">
                {activeTask.attachments.map((item) => (
                  <Space key={item.id} direction="vertical" size={0}>
                    <Button
                      type="link"
                      className="expense-attachment-link"
                      onClick={() => void handleOpenAttachment(item.id)}
                    >
                      {item.file_name}
                    </Button>
                    <Text type="secondary">
                      {JSON.stringify(item.extracted_fields || {})}
                    </Text>
                  </Space>
                ))}
              </Space>
            </div>

            <div>
              <Title level={5}>审批意见</Title>
              <TextArea
                rows={3}
                value={comment}
                onChange={(event) => setComment(event.target.value)}
              />
              <Space style={{ marginTop: 12 }}>
                <Button
                  type="primary"
                  loading={submitting}
                  disabled={activeTask.status !== "finance_review"}
                  onClick={() => void handleReview("approve")}
                >
                  通过
                </Button>
                <Button
                  loading={submitting}
                  disabled={activeTask.status !== "finance_review"}
                  onClick={() => void handleReview("request-supplement")}
                >
                  要求补充
                </Button>
                <Button
                  danger
                  loading={submitting}
                  disabled={activeTask.status !== "finance_review"}
                  onClick={() => void handleReview("reject")}
                >
                  驳回
                </Button>
              </Space>
            </div>

            <div>
              <Title level={5}>审批日志</Title>
              <Timeline
                items={logs.map((item) => ({
                  children: `${new Date(item.created_at).toLocaleString()} ${item.action}：${
                    item.comment || "-"
                  }`
                }))}
              />
            </div>
          </Space>
        </Card>
      ) : null}
    </div>
  );
}
