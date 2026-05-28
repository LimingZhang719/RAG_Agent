import { useEffect, useState } from "react";
import { Button, Card, Layout, Space, Tag, Typography } from "antd";
import {
  ApiOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  RobotOutlined
} from "@ant-design/icons";

import { getHealth } from "../../api/health";

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

type HealthState = "idle" | "checking" | "ok" | "failed";

export function HomePage() {
  const [healthState, setHealthState] = useState<HealthState>("idle");
  const [healthMessage, setHealthMessage] = useState("尚未检查");

  async function checkHealth() {
    setHealthState("checking");
    try {
      const data = await getHealth();
      setHealthMessage(`${data.service} ${data.version}：${data.status}`);
      setHealthState("ok");
    } catch (error) {
      setHealthMessage(error instanceof Error ? error.message : "健康检查失败");
      setHealthState("failed");
    }
  }

  useEffect(() => {
    void checkHealth();
  }, []);

  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <Space size={12}>
          <RobotOutlined className="brand-icon" />
          <Text className="brand-text">Agentic RAG Platform</Text>
        </Space>
        <Tag color={healthState === "ok" ? "green" : "default"}>{healthState}</Tag>
      </Header>
      <Content className="app-content">
        <section className="intro">
          <Title level={1}>v0 工程骨架</Title>
          <Paragraph>
            当前阶段用于验证 Windows 本地开发环境、FastAPI 后端、React 前端、
            PostgreSQL/pgvector、Redis 和 MinIO 的基础联通。
          </Paragraph>
          <Button type="primary" onClick={checkHealth} loading={healthState === "checking"}>
            检查后端健康状态
          </Button>
          <Paragraph className="health-message">{healthMessage}</Paragraph>
        </section>

        <section className="module-grid">
          <Card>
            <Space direction="vertical">
              <DatabaseOutlined className="module-icon" />
              <Title level={4}>知识库与向量存储</Title>
              <Text>PostgreSQL + pgvector 作为 v0 默认数据与向量存储。</Text>
            </Space>
          </Card>
          <Card>
            <Space direction="vertical">
              <ApiOutlined className="module-icon" />
              <Title level={4}>RAG 与模型适配层</Title>
              <Text>LlamaIndex 集成在后端，模型能力通过外部 API 适配。</Text>
            </Space>
          </Card>
          <Card>
            <Space direction="vertical">
              <CloudServerOutlined className="module-icon" />
              <Title level={4}>Agent 编排</Title>
              <Text>后续使用 LangGraph 实现报销和入职智能体流程。</Text>
            </Space>
          </Card>
        </section>
      </Content>
    </Layout>
  );
}
