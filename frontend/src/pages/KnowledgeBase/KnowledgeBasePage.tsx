import {
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Drawer,
  Row,
  Select,
  Table,
  Tag,
  Typography,
  message
} from "antd";
import type { UploadProps } from "antd";
import { useEffect, useMemo, useState } from "react";

import {
  createKnowledgeBase,
  fetchKnowledgeBases,
  type ChunkMethod,
  type KnowledgeBaseItem,
  type VisibilityScope
} from "../../api/kb";
import {
  fetchDocuments,
  fetchDocumentChunks,
  retryDocument,
  updateDocumentChunking,
  uploadDocument,
  type ChunkItem,
  type DocumentItem
} from "../../api/documents";
import { FileUploader } from "../../components/FileUploader/FileUploader";
import { useUserStore } from "../../stores/userStore";

const { Title, Paragraph } = Typography;

const scopeOptions = [
  { label: "公司级", value: "company" },
  { label: "部门级", value: "department" },
  { label: "个人级", value: "personal" }
];

const statusColor: Record<DocumentItem["status"], string> = {
  pending: "default",
  parsing: "processing",
  chunking: "processing",
  embedding: "processing",
  ready: "success",
  failed: "error"
};

const chunkMethodOptions = [
  { label: "句子切块", value: "sentence" },
  { label: "Token 切块", value: "token" }
];

export function KnowledgeBasePage() {
  const [kbs, setKbs] = useState<KnowledgeBaseItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedKb, setSelectedKb] = useState<KnowledgeBaseItem | null>(null);
  const [loadingKb, setLoadingKb] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [chunkDrawerOpen, setChunkDrawerOpen] = useState(false);
  const [chunkLoading, setChunkLoading] = useState(false);
  const [chunkItems, setChunkItems] = useState<ChunkItem[]>([]);
  const [activeDocument, setActiveDocument] = useState<DocumentItem | null>(null);
  const [chunkConfigOpen, setChunkConfigOpen] = useState(false);
  const [chunkConfigLoading, setChunkConfigLoading] = useState(false);

  const user = useUserStore((state) => state.user);

  const loadKnowledgeBases = async () => {
    setLoadingKb(true);
    try {
      const items = await fetchKnowledgeBases();
      if (Array.isArray(items)) {
        setKbs(items);
        if (items.length && !selectedKb) {
          setSelectedKb(items[0]);
        }
      } else {
        setKbs([]);
        message.error("知识库数据格式异常");
      }
    } catch (error) {
      message.error("知识库加载失败");
    } finally {
      setLoadingKb(false);
    }
  };

  const loadDocuments = async (kbId: string) => {
    setLoadingDocs(true);
    try {
      const items = await fetchDocuments(kbId);
      if (Array.isArray(items)) {
        setDocuments(items);
      } else {
        setDocuments([]);
        message.error("文档数据格式异常");
      }
    } catch (error) {
      message.error("文档列表加载失败");
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  useEffect(() => {
    if (selectedKb) {
      loadDocuments(selectedKb.id);
    } else {
      setDocuments([]);
    }
  }, [selectedKb?.id]);

  useEffect(() => {
    if (!selectedKb) {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const items = await fetchDocuments(selectedKb.id);
        if (Array.isArray(items)) {
          setDocuments(items);
        }
      } catch (error) {
        // Keep silent during polling to avoid noisy errors.
      }
    }, 5000);
    return () => window.clearInterval(timer);
  }, [selectedKb?.id]);

  const uploadProps: UploadProps = useMemo(
    () => ({
      multiple: false,
      showUploadList: false,
      customRequest: async (options) => {
        if (!selectedKb) {
          message.warning("请先选择知识库");
          return;
        }
        const file = options.file as File;
        try {
          await uploadDocument(selectedKb.id, file);
          message.success("上传成功，正在入库");
          await loadDocuments(selectedKb.id);
          options.onSuccess?.(null as never, options.file as never);
        } catch (error) {
          message.error("上传失败");
          options.onError?.(error as Error);
        }
      }
    }),
    [selectedKb]
  );

  const handleCreate = async (values: {
    name: string;
    description?: string;
    visibility_scope: VisibilityScope;
    org_id?: string;
    chunk_method?: ChunkMethod;
    chunk_size?: number;
    chunk_overlap?: number;
  }) => {
    setCreateLoading(true);
    try {
      await createKnowledgeBase({
        name: values.name,
        description: values.description,
        visibility_scope: values.visibility_scope,
        org_id: values.org_id || undefined,
        chunk_method: values.chunk_method,
        chunk_size: values.chunk_size,
        chunk_overlap: values.chunk_overlap
      });
      message.success("知识库已创建");
      setCreateOpen(false);
      await loadKnowledgeBases();
    } catch (error) {
      message.error("创建失败");
    } finally {
      setCreateLoading(false);
    }
  };

  const openChunks = async (doc: DocumentItem) => {
    setActiveDocument(doc);
    setChunkDrawerOpen(true);
    setChunkLoading(true);
    try {
      const items = await fetchDocumentChunks(doc.id);
      if (Array.isArray(items)) {
        setChunkItems(items);
      } else {
        setChunkItems([]);
        message.error("切片数据格式异常");
      }
    } catch (error) {
      message.error("切片加载失败");
    } finally {
      setChunkLoading(false);
    }
  };

  const openChunkConfig = (doc: DocumentItem) => {
    setActiveDocument(doc);
    setChunkConfigOpen(true);
  };

  const submitChunkConfig = async (values: {
    chunk_method: ChunkMethod;
    chunk_size: number;
    chunk_overlap: number;
  }) => {
    if (!activeDocument) {
      return;
    }
    setChunkConfigLoading(true);
    try {
      await updateDocumentChunking(activeDocument.id, values);
      message.success("切块配置已更新，已重新入库");
      setChunkConfigOpen(false);
      if (selectedKb) {
        await loadDocuments(selectedKb.id);
      }
    } catch (error) {
      message.error("切块配置更新失败");
    } finally {
      setChunkConfigLoading(false);
    }
  };

  return (
    <Card className="page-card">
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={3}>知识库管理</Title>
          <Paragraph type="secondary">
            管理知识库、上传文档并查看入库状态。
          </Paragraph>
        </Col>
        <Col>
          <Button type="primary" onClick={() => setCreateOpen(true)}>
            新建知识库
          </Button>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={10}>
          <Card size="small" title="知识库列表">
            <Table
              rowKey="id"
              loading={loadingKb}
              dataSource={kbs}
              pagination={false}
              onRow={(record) => ({
                onClick: () => setSelectedKb(record)
              })}
              rowClassName={(record) =>
                record.id === selectedKb?.id ? "table-row-active" : ""
              }
              columns={[
                {
                  title: "名称",
                  dataIndex: "name",
                  key: "name"
                },
                {
                  title: "级别",
                  dataIndex: "visibility_scope",
                  key: "visibility_scope",
                  render: (value: VisibilityScope) => {
                    const label =
                      value === "company"
                        ? "公司级"
                        : value === "department"
                        ? "部门级"
                        : "个人级";
                    return <Tag color="blue">{label}</Tag>;
                  }
                }
              ]}
            />
          </Card>
        </Col>
        <Col span={14}>
          <Card
            size="small"
            title={selectedKb ? `文档列表 - ${selectedKb.name}` : "文档列表"}
          >
            <FileUploader title="上传文档" props={uploadProps} />
            <Table
              rowKey="id"
              loading={loadingDocs}
              dataSource={documents}
              pagination={false}
              style={{ marginTop: 16 }}
              columns={[
                { title: "文件名", dataIndex: "file_name", key: "file_name" },
                {
                  title: "状态",
                  dataIndex: "status",
                  key: "status",
                  render: (value: DocumentItem["status"]) => (
                    <Tag color={statusColor[value]}>{value}</Tag>
                  )
                },
                {
                  title: "错误信息",
                  dataIndex: "error_message",
                  key: "error_message",
                  render: (value: string | null | undefined, record) =>
                    value ? (
                      <span>
                        {value}
                        <Button
                          type="link"
                          onClick={() => retryDocument(record.id)}
                        >
                          重试
                        </Button>
                      </span>
                    ) : (
                      "-"
                    )
                },
                {
                  title: "切片",
                  key: "chunks",
                  render: (_: unknown, record) => (
                    <>
                      <Button type="link" onClick={() => openChunks(record)}>
                        查看
                      </Button>
                      <Button type="link" onClick={() => openChunkConfig(record)}>
                        切块配置
                      </Button>
                    </>
                  )
                }
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Drawer
        title={
          activeDocument
            ? `切片详情 - ${activeDocument.file_name}`
            : "切片详情"
        }
        width={720}
        open={chunkDrawerOpen}
        onClose={() => setChunkDrawerOpen(false)}
      >
        <Table
          rowKey="id"
          loading={chunkLoading}
          dataSource={chunkItems}
          pagination={{ pageSize: 10 }}
          columns={[
            { title: "序号", dataIndex: "block_order", key: "block_order" },
            { title: "页码", dataIndex: "page_no", key: "page_no" },
            { title: "段落", dataIndex: "section_path", key: "section_path" },
            {
              title: "内容",
              dataIndex: "content",
              key: "content",
              render: (value: string) => (
                <span style={{ whiteSpace: "pre-wrap" }}>{value}</span>
              )
            }
          ]}
        />
      </Drawer>

      <Modal
        title="新建知识库"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form layout="vertical" onFinish={handleCreate}>
          <Form.Item
            label="名称"
            name="name"
            rules={[{ required: true, message: "请输入名称" }]}
          >
            <Input placeholder="例如：公司制度" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="可选" />
          </Form.Item>
          <Form.Item
            label="级别"
            name="visibility_scope"
            rules={[{ required: true, message: "请选择级别" }]}
            initialValue="company"
          >
            <Select options={scopeOptions} />
          </Form.Item>
          <Form.Item label="部门 ID" name="org_id" initialValue={user?.org_id}>
            <Input placeholder="部门级知识库必填" />
          </Form.Item>
          <Form.Item
            label="默认切块方式"
            name="chunk_method"
            initialValue="sentence"
          >
            <Select options={chunkMethodOptions} />
          </Form.Item>
          <Form.Item label="切块大小" name="chunk_size" initialValue={1024}>
            <InputNumber min={200} max={4000} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="切块重叠" name="chunk_overlap" initialValue={128}>
            <InputNumber min={0} max={1000} style={{ width: "100%" }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createLoading} block>
            创建
          </Button>
        </Form>
      </Modal>

      <Modal
        title="文档切块配置"
        open={chunkConfigOpen}
        onCancel={() => setChunkConfigOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          layout="vertical"
          onFinish={submitChunkConfig}
          initialValues={{
            chunk_method: activeDocument?.chunk_method || "sentence",
            chunk_size: activeDocument?.chunk_size || 1024,
            chunk_overlap: activeDocument?.chunk_overlap || 128
          }}
        >
          <Form.Item label="切块方式" name="chunk_method">
            <Select options={chunkMethodOptions} />
          </Form.Item>
          <Form.Item label="切块大小" name="chunk_size">
            <InputNumber min={200} max={4000} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="切块重叠" name="chunk_overlap">
            <InputNumber min={0} max={1000} style={{ width: "100%" }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={chunkConfigLoading} block>
            保存并重新入库
          </Button>
        </Form>
      </Modal>
    </Card>
  );
}
