import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Upload,
  message
} from "antd";
import type { ColumnsType } from "antd/es/table";

import {
  createExpenseClaim,
  fetchExpenseClaims,
  runExpenseAgent,
  uploadExpenseAttachment
} from "../../api/expense";
import type {
  AttachmentType,
  ExpenseAuditItem,
  ExpenseClaim
} from "../../types/expense";

const { Title, Paragraph, Text } = Typography;

const statusLabels: Record<ExpenseClaim["status"], string> = {
  draft: "草稿",
  submitted: "已提交",
  need_supplement: "需补充",
  finance_review: "财务复核",
  approved: "已通过",
  rejected: "已驳回"
};

const resultColors: Record<string, string> = {
  pass: "green",
  attention: "gold",
  risk: "red"
};

const attachmentLabels: Record<AttachmentType, string> = {
  invoice: "发票",
  payment: "水单/支付凭证",
  approval: "审批单",
  other: "其他"
};

export function ExpensePage() {
  const [claims, setClaims] = useState<ExpenseClaim[]>([]);
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const activeClaim = useMemo(
    () => claims.find((item) => item.id === activeClaimId) ?? null,
    [claims, activeClaimId]
  );

  async function loadClaims() {
    setLoading(true);
    try {
      const data = await fetchExpenseClaims();
      setClaims(data);
      setActiveClaimId((current) => current ?? data[0]?.id ?? null);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "报销单加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(values: {
    title?: string;
    description?: string;
    total_amount?: number;
    city_tier?: string;
  }) {
    setSubmitting(true);
    try {
      const claim = await createExpenseClaim({
        ...values,
        currency: "CNY"
      });
      message.success("已创建差旅报销单");
      form.resetFields();
      await loadClaims();
      setActiveClaimId(claim.id);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpload(file: File, attachmentType: AttachmentType) {
    if (!activeClaim) {
      message.warning("请先选择或创建报销单");
      return;
    }
    try {
      await uploadExpenseAttachment(activeClaim.id, file, attachmentType);
      message.success("附件已上传并完成默认 OCR 处理");
      await loadClaims();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "附件上传失败");
    }
  }

  async function handleRunAgent() {
    if (!activeClaim) {
      return;
    }
    setSubmitting(true);
    try {
      const updated = await runExpenseAgent(activeClaim.id);
      message.success("AI 初审已完成");
      await loadClaims();
      setActiveClaimId(updated.id);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "初审失败");
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    void loadClaims();
  }, []);

  const columns: ColumnsType<ExpenseClaim> = [
    {
      title: "报销单",
      dataIndex: "title",
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.title || record.claim_no || "未命名差旅报销"}</Text>
          <Text type="secondary">{record.claim_no}</Text>
        </Space>
      )
    },
    {
      title: "金额",
      dataIndex: "total_amount",
      render: (value, record) => (value ? `${value} ${record.currency}` : "-")
    },
    {
      title: "状态",
      dataIndex: "status",
      render: (status: ExpenseClaim["status"]) => (
        <Tag>{statusLabels[status]}</Tag>
      )
    },
    {
      title: "风险",
      render: (_, record) => {
        const level = record.audit_summary?.level;
        return level ? <Tag color={resultColors[level]}>{level}</Tag> : "-";
      }
    }
  ];

  const attachmentTypes = Object.keys(attachmentLabels) as AttachmentType[];

  return (
    <div className="page-stack">
      <Card className="page-card">
        <Title level={3}>差旅报销助手</Title>
        <Paragraph type="secondary">
          创建差旅报销单，上传发票、水单或支付凭证、审批单后执行 AI 初审。
        </Paragraph>
        <Form form={form} layout="inline" onFinish={handleCreate}>
          <Form.Item name="title" rules={[{ required: true, message: "请输入标题" }]}>
            <Input placeholder="报销标题" />
          </Form.Item>
          <Form.Item name="total_amount" rules={[{ required: true, message: "请输入金额" }]}>
            <InputNumber min={0} precision={2} placeholder="申报金额" />
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
          <Form.Item name="description">
            <Input placeholder="说明" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={submitting}>
            新建
          </Button>
        </Form>
      </Card>

      <Card className="page-card" title="我的报销单">
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={claims}
          pagination={{ pageSize: 6 }}
          rowClassName={(record) =>
            record.id === activeClaimId ? "table-row-active" : ""
          }
          onRow={(record) => ({
            onClick: () => setActiveClaimId(record.id)
          })}
        />
      </Card>

      {activeClaim ? (
        <Card
          className="page-card"
          title={activeClaim.title || activeClaim.claim_no}
          extra={
            <Button type="primary" loading={submitting} onClick={() => void handleRunAgent()}>
              执行 AI 初审
            </Button>
          }
        >
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <Space wrap>
              {attachmentTypes.map((type) => (
                <Upload
                  key={type}
                  showUploadList={false}
                  customRequest={({ file, onSuccess }) => {
                    void handleUpload(file as File, type).then(() => onSuccess?.("ok"));
                  }}
                >
                  <Button>{attachmentLabels[type]}</Button>
                </Upload>
              ))}
            </Space>

            <Space wrap>
              {attachmentTypes.slice(0, 3).map((type) => {
                const uploaded = activeClaim.attachments.some(
                  (item) => item.attachment_type === type
                );
                return (
                  <Tag key={type} color={uploaded ? "green" : "red"}>
                    {attachmentLabels[type]}：{uploaded ? "已上传" : "缺少"}
                  </Tag>
                );
              })}
            </Space>

            <div>
              <Title level={5}>附件</Title>
              <Space direction="vertical" style={{ width: "100%" }}>
                {activeClaim.attachments.map((item) => (
                  <Text key={item.id}>
                    {attachmentLabels[item.attachment_type]}：{item.file_name}
                  </Text>
                ))}
              </Space>
            </div>

            <div>
              <Title level={5}>AI 初审建议</Title>
              <Paragraph>{activeClaim.audit_summary?.summary || "尚未初审"}</Paragraph>
              <Table<ExpenseAuditItem>
                rowKey="id"
                columns={[
                  { title: "项目", dataIndex: "name" },
                  {
                    title: "结果",
                    dataIndex: "result",
                    render: (value) => <Tag color={resultColors[value]}>{value}</Tag>
                  },
                  { title: "证据", dataIndex: "evidence" }
                ]}
                dataSource={activeClaim.audit_items}
                pagination={false}
              />
            </div>
          </Space>
        </Card>
      ) : null}
    </div>
  );
}
