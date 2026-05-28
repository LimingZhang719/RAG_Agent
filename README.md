# 智能 Agentic-RAG 平台

本仓库当前处于 v0 P0 阶段，已完成本地开发工程骨架：

- FastAPI 后端骨架。
- React + TypeScript + Vite 前端骨架。
- PostgreSQL + pgvector、Redis、MinIO 的 Docker Compose 配置。
- Alembic 基础配置。
- 统一 `.env.example`。

## 本地开发前置条件

- Git
- Python 3.11
- Node.js 20 LTS
- Docker Desktop

## 启动基础设施

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f deploy/docker-compose.dev.yml up -d
```

服务端口：

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO API: `localhost:9000`
- MinIO Console: `http://localhost:9001`

## 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/health/db`

## 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问：

- `http://127.0.0.1:5173`

## 当前阶段边界

P0 只提供环境与工程骨架。用户、知识库、RAG、Agent、报销助手等业务功能会在后续 P1-P7 阶段逐步实现。
