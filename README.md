# YAI — 拟人化 AI 对话平台

YAI 是一个拟人化 AI 对话平台，支持角色扮演式 AI 对话、场景设计、多模型梯度积分计费、自建 JWT 认证体系。

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | Python 3.10 + FastAPI |
| ORM | SQLAlchemy 2.0 + asyncpg |
| 数据库 | PostgreSQL + pgvector + pg_trgm |
| 缓存/限流 | Redis + aioredis |
| 认证 | JWT (HttpOnly Cookie) + bcrypt |
| AI 模型 | Google Gemini API (三档: Speed/Pro/Elite) |
| 前端 | Next.js 15 + React 19 + TypeScript + Tailwind CSS |
| 数据迁移 | Alembic |

## 项目结构

```
yai/
├── src/                          # 后端源码
│   ├── api/                      # FastAPI 路由层 (65 个端点)
│   │   ├── auth_routes.py        #   认证 (6 个端点)
│   │   ├── character_routes.py   #   角色 (7 个端点)
│   │   ├── scene_routes.py       #   场景 (9 个端点)
│   │   ├── credit_routes.py      #   积分 (4 个端点)
│   │   ├── chat_routes.py        #   对话 (15 个端点)
│   │   ├── admin_routes.py       #   管理 (18 个端点)
│   │   ├── deps.py               #   依赖注入
│   │   ├── chat_deps.py          #   对话依赖链
│   │   └── middleware.py         #   限流+日志中间件
│   ├── core/                     # 核心领域层
│   │   ├── models.py             #   9 张表 ORM 模型
│   │   ├── schemas.py            #   47+ Pydantic Schema
│   │   ├── credit_engine.py      #   梯度定价引擎
│   │   ├── memory_engine.py      #   5 层记忆引擎
│   │   ├── story_summary_engine.py # 故事梗概引擎
│   │   ├── yaml_parser.py        #   YAML 响应解析器
│   │   ├── prompt_builder.py     #   Prompt 构建器
│   │   ├── model_provider.py     #   AI 模型抽象层
│   │   ├── gemini_provider.py    #   Gemini 适配器
│   │   ├── embedding_provider.py #   向量嵌入层
│   │   └── exceptions.py         #   业务异常定义
│   ├── services/                 # 业务服务层
│   ├── repositories/             # 数据访问层
│   ├── utils/                    # 工具模块
│   └── config/                   # 配置管理
├── frontend/                     # 前端源码 (Next.js)
│   ├── src/
│   │   ├── app/                  #   App Router 页面
│   │   │   ├── (main)/           #     带布局的主页面
│   │   │   │   ├── page.tsx      #       首页
│   │   │   │   ├── explore/      #       发现页
│   │   │   │   ├── search/       #       搜索页
│   │   │   │   ├── chat/         #       对话页 (SSE)
│   │   │   │   ├── character/    #       角色详情页
│   │   │   │   ├── scene/        #       场景详情页
│   │   │   │   ├── create/       #       创建角色/场景
│   │   │   │   ├── profile/      #       个人中心
│   │   │   │   └── admin/        #       管理用户页
│   │   │   └── auth/             #     认证页面 (登录/注册)
│   │   ├── components/           #   共用组件
│   │   └── lib/                  #   工具库 (API/hooks/types)
│   └── package.json
├── tests/                        # 测试套件 (102 用例)
├── alembic/                      # 数据库迁移
├── docs/                         # 设计文档
├── main.py                       # 应用入口
├── requirements.txt              # Python 依赖
└── alembic.ini                   # Alembic 配置
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+ (前端)
- PostgreSQL 15+ (启用 pgvector + pg_trgm 扩展)
- Redis 7+

### 1. 克隆项目

```bash
git clone <repo-url> yai
cd yai
```

### 2. 后端部署

#### 2.1 创建 Python 虚拟环境

```bash
python3.10 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

#### 2.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必要配置：

```env
# 数据库 (必填)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/yai

# Redis (必填)
REDIS_URL=redis://localhost:6379/0

# JWT 密钥 (必填，生产环境请生成强随机字符串)
JWT_SECRET_KEY=your-secret-key-at-least-32-chars

# Google Gemini API (必填)
GEMINI_API_KEY=your-gemini-api-key

# 邮件发送 (注册邮箱验证)
# 方式一: SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 方式二: Resend API
# RESEND_API_KEY=re_xxxxx

# 管理员白名单 (邮箱验证后自动提权)
ADMIN_EMAIL_WHITELIST=admin@example.com

# CORS 允许的前端域名
CORS_ORIGINS=["http://localhost:3000"]

# 环境 (development / production)
ENVIRONMENT=development
```

#### 2.3 初始化数据库

```bash
# 确保 PostgreSQL 中已创建数据库并启用扩展
psql -U postgres -c "CREATE DATABASE yai;"
psql -U postgres -d yai -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -d yai -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# 运行迁移
alembic upgrade head
```

#### 2.4 启动后端

```bash
# 开发模式 (热重载)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

后端启动后可访问:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 3. 前端部署

#### 3.1 安装依赖

```bash
cd frontend
npm install
```

#### 3.2 配置环境变量

```bash
cp .env.local.example .env.local
```

编辑 `.env.local`：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3.3 启动前端

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build
npm start
```

前端默认运行在 http://localhost:3000

## 生产部署

### 使用 Docker Compose (推荐)

```yaml
# docker-compose.yml
version: "3.8"

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: yai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: yai
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      DATABASE_URL: postgresql+asyncpg://yai:${DB_PASSWORD}@db:5432/yai
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      ENVIRONMENT: production
      CORS_ORIGINS: '["https://your-domain.com"]'
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

### 后端 Dockerfile

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 前端 Dockerfile

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["npm", "start"]
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # SSE 需要关闭 buffering
    location /api/v1/chat/stream {
        proxy_pass http://localhost:8000;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## 常用命令

```bash
# 后端
source venv/bin/activate
uvicorn main:app --reload                    # 开发启动
alembic upgrade head                         # 数据库迁移
alembic revision --autogenerate -m "desc"    # 生成迁移
pytest tests/                                # 运行测试 (102 用例)
pytest tests/unit/                           # 仅单元测试
pytest tests/integration/                    # 仅集成测试

# 前端
cd frontend
npm run dev                                  # 开发启动
npm run build                                # 生产构建
npm run lint                                 # 代码检查
```

## 核心功能

### AI 对话

- **SSE 流式输出**: 打字机效果实时渲染
- **YAML 结构化交互**: speech/action/emotion 分离渲染，节省 ~30% Token
- **5 层记忆架构**: system prompt → 故事梗概 → 固定消息 → 长期向量检索 → 短期 20 条
- **故事梗概**: 每 10 轮自动生成 YAML 格式摘要
- **消息操作**: 编辑/重新生成/删除/回退/分叉/反馈/固定

### 积分系统

- **三档定价**: Speed (10/1K) / Pro (50/1K) / Elite (150/1K)
- **预扣-结算模式**: 行级锁保证并发安全，AI 失败自动回滚

### 管理后台

- **融合式布局**: 左侧栏入口，管理员专属
- **用户管理**: 权限控制 / 积分调整 / 消耗分析 / 资源管理
- **Redis 限流**: 滑动窗口，对话 10/60s，认证 5/60s/IP

## API 总览

| 模块 | 端点数 | 前缀 |
|------|--------|------|
| 认证 | 6 | `/api/v1/auth` |
| 角色 | 7 | `/api/v1/characters` |
| 场景 | 9 | `/api/v1/scenes` |
| 积分 | 4 | `/api/v1/credits` |
| 对话 | 15 | `/api/v1/chat` |
| 管理 | 18 | `/api/v1/admin` |
| **合计** | **65** | |

完整 API 文档: 启动后端后访问 http://localhost:8000/docs

## 前端页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 首页 | `/` | For You 推荐 + 热门角色/场景 |
| 发现页 | `/explore` | 角色/场景浏览 + 标签过滤 + 排序 |
| 搜索页 | `/search?q=xxx` | 全局搜索结果 |
| 角色详情 | `/character/{id}` | 角色介绍 + 开始对话 |
| 场景详情 | `/scene/{id}` | 场景描述 + 选角 + 开启 |
| 对话页 | `/chat/{sessionId}` | SSE 打字机 + YAML 渲染 + 导演面板 |
| 创建角色 | `/create/character` | 表单式创建 |
| 创建场景 | `/create/scene` | 引导式两步创建 |
| 个人中心 | `/profile` | 我的角色/场景/积分记录 |
| 管理用户 | `/admin/users` | 用户管理 (管理员) |
| 登录 | `/auth/login` | 邮箱 + 密码 |
| 注册 | `/auth/register` | 注册 + 邮箱验证 |
