# P4 LlamaIndex RAG 问答研发计划

> 目标：基于当前 v0 规划，完成 LlamaIndex RAG 问答的后端与前端闭环，支持引用、重排、流式输出、检索日志与权限过滤。

## 1. 目标与范围

### 1.1 目标

- 支持按知识库检索与问答，具备引用与日志。
- 支持 Rerank 可配置开关。
- 支持强规则命中后原文返回（不调用 LLM）。
- 保证检索顺序可按原文顺序恢复。

### 1.2 范围

- 后端：API、RAG 服务、模型适配层、检索日志。
- 前端：聊天 UI、引用展示、知识库选择与流式输出。

### 1.3 非范围

- 复杂 BI 看板与热点话题。
- 本地模型部署与 GPU 推理。

## 2. 依赖与前置条件

- P1：数据模型与迁移完成（包含 `chat_sessions`、`chat_messages`、`retrieval_logs`、`chunks`）。
- P3：知识库与文档入库流程可用（包含 `chunks` 向量）。
- 模型适配层基础可用：`LLMClient`、`EmbeddingClient`、`RerankClient`。
- pgvector 已启用。

## 3. 研发分解（后端）

### 3.1 API 设计

- `POST /api/chat/sessions`：创建会话。
- `GET /api/chat/sessions`：会话列表。
- `POST /api/chat/stream`：流式问答。
- `GET /api/chat/messages?session_id=`：会话消息。

### 3.2 服务层设计

- `LlamaIndexFactory`：根据知识库创建/获取索引或检索器。
- `RetrieverService`：
  - 构造 LlamaIndex metadata filter。
  - 执行向量检索并返回候选。
  - 关键词检索（基于 `tsvector/tsquery` 或分词后倒排）。
  - 多路召回融合（向量 + 关键词），统一去重与归一化评分。
  - 可选 Rerank。
- `CitationBuilder`：构造引用信息（文档名、页码、片段）。
- `AnswerGenerator`：
  - strong rule 命中后直接返回原文。
  - 否则调用 LLM 流式生成。
- `RetrievalLogService`：保存召回片段、评分、是否命中规则。

### 3.3 权限过滤

- SQL 层或 LlamaIndex metadata filter 约束：
  - `visibility_scope = company`
  - `visibility_scope = department AND org_id IN current_user_visible_orgs`
  - `visibility_scope = personal AND owner_id = current_user_id`

### 3.4 强规则命中

- `RuleMatcher`：
  - 支持标题/编号/关键词匹配。
  - 满足分数阈值后命中。
  - 命中后返回原文 chunk。

### 3.5 数据写入

- `chat_messages`：问题与回答。
- `retrieval_logs`：召回片段、分数、rerank 结果。

### 3.6 关键配置

- `RAG_TOP_K`、`RERANK_TOP_K`、`RERANK_ENABLED`。
- `RAG_SCORE_THRESHOLD`、`RULE_MATCH_THRESHOLD`。
- `KEYWORD_RECALL_ENABLED`、`KEYWORD_TOP_K`、`HYBRID_FUSION_METHOD`。
- `PROMPT_TEMPLATE_NAME`、`PROMPT_TEMPLATE_VERSION`。

### 3.7 提示词模板与配置位置

- 模板文件位置：`backend/app/rag/prompt_templates.py`。
- 配置位置：`backend/app/core/config.py`（读取环境变量并注入 settings）。
- 运行时选择模板：由 `AnswerGenerator` 读取 `PROMPT_TEMPLATE_NAME` 与 `PROMPT_TEMPLATE_VERSION`。

## 4. 研发分解（前端）

### 4.1 页面与组件

- `Chat` 页面：
  - 会话列表。
  - 对话区 + 输入区。
  - 引用卡片。
- `KnowledgeBaseSelector`：多选知识库。
- `ChatWindow`：流式消息展示。
- `CitationPanel`：引用列表与片段展开。

### 4.2 API 接入

- `/api/chat/stream`：SSE 或 fetch stream。
- `/api/chat/sessions`：会话创建与列表。

## 5. 接口与数据结构

### 5.1 流式返回结构（建议）

```json
{
  "type": "delta | citations | done",
  "content": "...",
  "citations": [
    {
      "document_id": "...",
      "document_name": "...",
      "page_no": 1,
      "chunk_id": "...",
      "snippet": "..."
    }
  ]
}
```

### 5.2 检索日志结构

```json
{
  "query": "...",
  "kb_ids": ["..."],
  "hits": [
    {
      "chunk_id": "...",
      "score": 0.82,
      "rerank_score": 0.76,
      "document_id": "..."
    }
  ],
  "rule_hit": true
}
```

## 6. 测试计划

- API 单测：检索、引用、强规则、权限过滤。
- E2E：
  - 选择知识库问答。
  - 无相关知识返回拒答。
  - 强规则原文返回。
- 性能：单次查询耗时与流式首 token 时间。

## 7. 里程碑与验收

- M1：后端基础检索与流式接口可用。
- M2：引用与检索日志完成。
- M3：强规则命中原文返回。
- M4：前端闭环与权限过滤。

### 验收标准

- 用户可选择知识库提问。
- 回答包含引用来源。
- Rerank 可通过配置开启或关闭。
- 无相关知识时能拒答。
- 检索日志能复盘召回片段和分数。
