# 企业知识库问答 Agent

这是一个可本地运行的企业知识库问答 Agent MVP，技术栈是 Python + FastAPI + 本地轻量 RAG + 可选 OpenAI Responses API + 原生前端。

## 功能

- 上传企业文本资料：`txt`、`md`、`csv`、`json`、`log`
- 自动清洗、切分并建立本地知识索引
- 根据问题检索最相关知识片段
- 配置 `OPENAI_API_KEY` 后使用大模型生成答案
- 未配置模型时自动使用本地检索摘要
- 返回来源片段，方便追溯答案依据
- 浏览器端上传、问答、查看文档、清空索引

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

如果你有 OpenAI API Key，编辑 `.env`：

```env
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4.1-mini"
```

## API

```http
GET /api/health
GET /api/documents
POST /api/documents
DELETE /api/documents
POST /api/ask
```

问答请求示例：

```json
{
  "question": "员工报销需要哪些材料？",
  "top_k": 5
}
```

## 目录结构

```text
app/
  api/          FastAPI 路由和请求响应模型
  core/         配置
  rag/          文档切分、索引、检索
  services/     Agent 与 LLM 调用
  static/       前端页面
data/
  documents/    上传的原始文档
tests/          单元测试
```

## 下一步可扩展

- 接入 PDF、Word、网页解析
- 将本地 TF-IDF 检索替换为 Qdrant、Milvus、pgvector 或 Chroma
- 增加用户、部门、文档权限和审计日志
- 增加流式输出和 WebSocket
- 加入 rerank、hybrid search 和答案引用编号
- 用 PostgreSQL 保存会话、任务和反馈

# 1. 进入项目 + 激活环境
cd D:\code\codex\codex_aidiancan
.\.venv\Scripts\Activate.ps1

# 2. 调试用（不带 reload）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 3. 端口报错就执行
taskkill /IM python.exe /F

<img width="980" height="3363" alt="image" src="https://github.com/user-attachments/assets/d6ec45d7-7772-492a-8945-2d9a09fcdfbe" />

