# YAI 开发进度追踪

## Phase 0: 基础设施

### Phase 0.1 - 项目基础骨架 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ 目录结构完整（src/{api,config,core,repositories,services,utils}, tests/{unit,integration}）
- ✅ requirements.txt 含所有依赖（fastapi, sqlalchemy, asyncpg, alembic, pgvector, redis, pyyaml, cuid2 等）
- ✅ .env.example 完整配置模板（108 个配置项）
- ✅ Settings 配置类（分层设计：13 个 Mixin 基类）
- ✅ database.py（AsyncEngine + 连接池管理）
- ✅ redis_client.py（aioredis 连接池）
- ✅ logger.py（环境感知：dev 文本 / prod JSON 格式）
- ✅ main.py FastAPI 入口（lifespan 管理 + CORS + 健康检查）
- ✅ .gitignore 完善
- ✅ static/uploads 目录结构
- ✅ tests/conftest.py 框架

**测试验证：**
```bash
# ✅ 应用导入成功
python -c "from main import app; print('✓ FastAPI 应用创建成功')"

# ✅ 数据库连接池初始化成功
# Database engine initialized (pool_max=20)

# ✅ 代码格式检查通过
black --check main.py src/

# ✅ pytest 框架就绪
pytest tests/ -v
```

---

## Phase 0.2 - 数据库模型与迁移 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ 9 张表 ORM 模型（User, Character, Scene, SceneCharacter, Transaction, VerificationToken, Message, StorySummary, UserCharacterCustomization）
- ✅ Pydantic Schema 定义（47 个 DTO 类）
- ✅ Alembic 初始迁移（含 pgvector + pg_trgm 扩展）
- ✅ ID 生成器（cuid2 封装）
- ✅ 完整索引设计（普通索引 + 复合索引 + GIN 索引 + IVFFlat 向量索引）

**文件清单：**
- `src/core/models.py` (300 行) - 9 张表 ORM 模型
- `src/core/schemas.py` (470 行) - 请求/响应 DTO
- `src/core/__init__.py` - 核心模块导出
- `src/utils/id_generator.py` - CUID 生成器
- `alembic/env.py` - 异步迁移配置
- `alembic/versions/6446f29cdb1b_initial_schema.py` (380 行) - 初始迁移脚本

**测试验证：**
```bash
# ✅ ORM 模型导入成功
# ✅ Pydantic Schema 导入成功  
# ✅ ID 生成器测试: cx7am9xbc4vdt6nx90tm7mjk
# ✅ 所有 9 张表模型已就绪
```

**数据库架构：**
| # | 表名 | 字段数 | 索引数 | 说明 |
|---|------|--------|--------|------|
| 1 | users | 12 | 3 | 用户表（邮箱/用户名/积分/权限） |
| 2 | characters | 14 | 8 | 角色表（含 GIN 索引支持模糊搜索） |
| 3 | scenes | 18 | 7 | 场景表（含结构化元数据） |
| 4 | scene_characters | 7 | 3 | 场景-角色关联表 |
| 5 | transactions | 5 | 3 | 积分流水表（含复合索引） |
| 6 | verification_tokens | 5 | 2 | 邮箱验证令牌表 |
| 7 | messages | 13 | 8 | 对话消息表（含 vector(768) + IVFFlat 索引） |
| 8 | story_summaries | 10 | 4 | 故事梗概表（含向量索引） |
| 9 | user_character_customizations | 6 | 2 | 用户角色定制表 |

**Pydantic Schema 覆盖：**
- 用户相关：3 个（注册/登录/响应）
- 角色相关：7 个（定义/创建/更新/响应/公开响应 + 子结构）
- 场景相关：5 个（创建/更新/关联/响应）
- 对话相关：6 个（请求/指令/消息操作）
- 会话管理：2 个（会话/历史分页）
- 积分管理：2 个（余额/流水）
- 搜索/分页：2 个
- 管理相关：4 个（积分调整/权限/消耗统计）
- 其他：16 个

---

## Phase 1: 认证 + 角色/场景

### Phase 1.1 - 身份认证系统 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ 异常定义（src/core/exceptions.py）
- ✅ 安全工具（src/utils/security.py）
  - PasswordHasher（bcrypt 哈希 + 验证）
  - JwtTokenManager（Access/Refresh Token 生成 + 解析）
  - CookieHelper（HttpOnly Cookie 设置 + 清除）
- ✅ 邮件服务（src/services/email_service.py）
  - 支持 SMTP / Resend API 双模式
  - 异步发送验证邮件
- ✅ 数据访问层
  - UserRepository（用户 CRUD + 激活 + 权限管理）
  - VerificationTokenRepository（验证令牌 CRUD + 过期清理）
- ✅ 业务服务层
  - AuthService（注册/登录/验证/刷新 Token 完整流程编排）
- ✅ API 路由层
  - POST /api/v1/auth/register - 用户注册
  - GET /api/v1/auth/verify/{token} - 邮箱验证
  - POST /api/v1/auth/login - 登录
  - POST /api/v1/auth/logout - 登出
  - POST /api/v1/auth/refresh - 刷新 Token
  - GET /api/v1/auth/me - 获取当前用户
- ✅ 依赖注入（src/api/deps.py）
  - get_current_user（从 Cookie 提取 JWT）
  - get_current_admin（管理员权限校验）

**文件清单：**
- `src/core/exceptions.py` (120 行) - 业务异常定义
- `src/utils/security.py` (120 行) - 密码哈希 + JWT + Cookie
- `src/services/email_service.py` (110 行) - 异步邮件发送
- `src/repositories/user_repo.py` (90 行) - 用户数据访问
- `src/repositories/token_repo.py` (70 行) - 验证令牌数据访问
- `src/services/auth_service.py` (150 行) - 认证业务编排
- `src/api/deps.py` (120 行) - FastAPI 依赖注入
- `src/api/auth_routes.py` (140 行) - 认证路由
- `src/repositories/__init__.py` - 仓储层导出
- `src/services/__init__.py` - 服务层导出
- `src/api/__init__.py` - API 层导出

**测试验证：**
```bash
# ✅ 所有模块导入成功
python -c "from src.api.auth_routes import router; print('✓ AuthRouter 导入成功')"

# ✅ FastAPI 应用路由注册成功
python -c "from main import app; print(f'✓ 路由数量: {len(app.routes)}')"
# 输出: ✓ 路由数量: 12
# - POST /api/v1/auth/register
# - GET /api/v1/auth/verify/{token}
# - POST /api/v1/auth/login
# - POST /api/v1/auth/logout
# - POST /api/v1/auth/refresh
# - GET /api/v1/auth/me

# ✅ 密码哈希测试通过
python -c "from src.utils.security import PasswordHasher; ..."

# ✅ JWT Token 测试通过
python -c "from src.utils.security import JwtTokenManager; ..."
```

**安全特性：**
1. **bcrypt 密码哈希**：自动加盐，安全强度高
2. **JWT Token**：Access Token (7天) + Refresh Token (14天)
3. **HttpOnly Cookie**：防止 XSS 攻击
4. **SameSite=Lax**：防止 CSRF 攻击
5. **Refresh Token 路径限制**：`/api/v1/auth/refresh` 专用
6. **管理员白名单**：邮箱验证后自动提权
7. **一次性验证令牌**：使用后立即删除

---

### Phase 1.2 - 角色与场景系统 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ 异常定义补充（角色与场景相关，8 个新异常类）
- ✅ 数据访问层
  - CharacterRepository（CRUD + 搜索 + 软删除 + 公开列表 + 点赞计数）
  - SceneRepository（CRUD + 搜索 + 场景-角色关联管理 + 游玩计数）
- ✅ Prompt 构建工具（core 层）
  - CharacterPromptBuilder（角色定义 → system prompt）
  - ScenePromptBuilder（场景 + 角色合并 prompt，支持 {{char}}/{{user}} 变量替换）
- ✅ 业务服务层
  - CharacterService（创建/查询/搜索/更新/删除，权限校验，definition 校验）
  - SceneService（创建/查询/搜索/更新/删除，场景角色关联管理，权限校验）
- ✅ API 路由层
  - **角色路由** 7 个端点：
    - POST /api/v1/characters/ - 创建角色
    - GET /api/v1/characters/{id} - 角色详情（创建者看完整，其他人看精简）
    - GET /api/v1/characters/me/list - 我的角色列表
    - GET /api/v1/characters/public/list?sort=popular - 公开角色列表
    - GET /api/v1/characters/search?q=xxx&tag=xxx - 搜索角色
    - PUT /api/v1/characters/{id} - 更新角色
    - DELETE /api/v1/characters/{id} - 删除角色（软删除）
  - **场景路由** 9 个端点：
    - POST /api/v1/scenes/ - 创建场景
    - GET /api/v1/scenes/{id} - 场景详情
    - GET /api/v1/scenes/me/list - 我的场景列表
    - GET /api/v1/scenes/public/list?sort=popular - 公开场景列表
    - GET /api/v1/scenes/search?q=xxx&tag=xxx - 搜索场景
    - PUT /api/v1/scenes/{id} - 更新场景
    - DELETE /api/v1/scenes/{id} - 删除场景（软删除）
    - POST /api/v1/scenes/{id}/characters - 添加角色到场景
    - DELETE /api/v1/scenes/{id}/characters/{char_id} - 移除角色

**文件清单：**
- `src/core/exceptions.py` (+80 行) - 8 个角色与场景异常类
- `src/repositories/character_repo.py` (240 行) - 角色数据访问
- `src/repositories/scene_repo.py` (270 行) - 场景数据访问
- `src/core/prompt_builder.py` (180 行) - CharacterPromptBuilder + ScenePromptBuilder
- `src/services/character_service.py` (220 行) - 角色业务编排
- `src/services/scene_service.py` (200 行) - 场景业务编排
- `src/api/character_routes.py` (160 行) - 角色路由（7 个端点）
- `src/api/scene_routes.py` (180 行) - 场景路由（9 个端点）
- `src/repositories/__init__.py` - 新增 CharacterRepository / SceneRepository 导出
- `src/services/__init__.py` - 新增 CharacterService / SceneService 导出
- `src/core/__init__.py` - 新增异常类和 PromptBuilder 导出

**测试验证：**
```bash
# ✅ 所有模块导入成功
python -c "from src.api.character_routes import router; print('✓')"
python -c "from src.api.scene_routes import router; print('✓')"

# ✅ FastAPI 应用路由注册成功
python -c "from main import app; print(f'✓ 路由总数: {len(app.routes)}')"
# 输出: ✓ 路由总数: 28

# 角色路由: 7 个
#   - POST /api/v1/characters/
#   - GET /api/v1/characters/{character_id}
#   - GET /api/v1/characters/me/list
#   - GET /api/v1/characters/public/list
#   - GET /api/v1/characters/search
#   - PUT /api/v1/characters/{character_id}
#   - DELETE /api/v1/characters/{character_id}

# 场景路由: 9 个
#   - POST /api/v1/scenes/
#   - GET /api/v1/scenes/{scene_id}
#   - GET /api/v1/scenes/me/list
#   - GET /api/v1/scenes/public/list
#   - GET /api/v1/scenes/search
#   - PUT /api/v1/scenes/{scene_id}
#   - DELETE /api/v1/scenes/{scene_id}
#   - POST /api/v1/scenes/{scene_id}/characters
#   - DELETE /api/v1/scenes/{scene_id}/characters/{character_id}

# ✅ 代码格式化通过
black src/ main.py
# 输出: 6 files reformatted, 24 files left unchanged.
```

**核心特性：**
1. **角色定义校验**：通过 Pydantic `CharacterDefinition` 校验 JSON 结构
2. **Definition 可见性控制**：非创建者仅看到 `personality` 列表，完整 definition 对创建者/管理员可见
3. **搜索支持**：pg_trgm 模糊匹配（name / tagline / description / 元数据），支持 tag 过滤
4. **软删除**：角色/场景删除采用软删除（`is_deleted=true`），保留历史引用
5. **权限校验**：创建时校验 `can_create_character/can_create_scene`，编辑/删除时校验所有权
6. **场景-角色关联**：支持添加/移除角色，校验角色可访问性（公开或自己创建的）
7. **Prompt 构建**：
   - `CharacterPromptBuilder`: 角色定义 → system prompt
   - `ScenePromptBuilder`: 场景 + 角色合并 prompt，支持 `{{char}}`/`{{user}}` 变量替换
8. **分页查询**：统一使用 `PaginatedResponse` 格式（items / total / page / size / pages）
9. **排序支持**：公开列表支持 `popular`（按 chat_count/play_count DESC）和 `newest`（按 created_at DESC）

---

### Phase 2 - 积分系统与计费引擎 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ 异常定义补充（积分相关，3 个新异常类）
- ✅ 核心计算引擎（core 层）
  - CreditEngine（梯度定价计算 + Token 费用估算 + 余额校验）
  - TierPricing / CreditHold / CreditSettlement 数据类
- ✅ 数据访问层
  - TransactionRepository（流水 CRUD + 按时间范围查询 + 消耗统计）
  - UserRepository 增强（增量更新积分 + 行级锁查询支持）
- ✅ 业务服务层
  - CreditService（预扣-结算-回滚三阶段流程 + 管理员调整）
- ✅ API 路由层
  - **积分路由** 4 个端点：
    - GET /api/v1/credits/balance - 查询余额（含档位定价）
    - GET /api/v1/credits/transactions - 流水记录（分页）
    - GET /api/v1/credits/pricing - 获取定价信息
    - POST /api/v1/credits/admin/adjust - 管理员调整（需管理员权限）

**文件清单：**
- `src/core/credit_engine.py` (180 行) - 积分计算引擎（纯函数）
- `src/core/exceptions.py` (+24 行) - CreditHoldNotFoundError / CreditTransactionError
- `src/repositories/transaction_repo.py` (165 行) - 积分流水数据访问
- `src/repositories/user_repo.py` (修改) - 积分增量更新支持
- `src/services/credit_service.py` (240 行) - 积分业务编排
- `src/api/credit_routes.py` (145 行) - 积分路由（4 个端点）
- `src/core/schemas.py` (修改) - PaginatedResponse 泛型化 + AdminCreditAdjustRequest 补充 user_id
- `src/repositories/__init__.py` - 新增 TransactionRepository 导出
- `src/services/__init__.py` - 新增 CreditService 导出
- `src/core/__init__.py` - 新增积分异常类导出

**测试验证：**
```bash
# ✅ 所有模块导入成功
python -c "from src.api.credit_routes import router; print('✓')"

# ✅ FastAPI 应用路由注册成功
python -c "from main import app; print(f'✓ 路由总数: {len(app.routes)}')"
# 输出: ✓ 路由总数: 32

# 积分路由: 4 个
#   - GET /api/v1/credits/balance
#   - GET /api/v1/credits/transactions
#   - GET /api/v1/credits/pricing
#   - POST /api/v1/credits/admin/adjust

# ✅ 代码格式化通过
black src/ main.py
# 输出: 2 files reformatted, 32 files left unchanged.
```

**核心特性：**
1. **梯度定价模型**：
   - Speed: 10 积分/1K tokens（Gemini 3 Flash）
   - Pro: 50 积分/1K tokens（Gemini 2.5 Pro）
   - Elite: 150 积分/1K tokens（Gemini 3.1 Pro）
   - 所有定价可通过 `.env` 配置热更新（需重启服务）

2. **预扣-结算模式**（两阶段提交）：
   - **预扣阶段**：
     - 行级锁（`SELECT ... FOR UPDATE`）保证并发安全
     - 预扣金额 = 预估 tokens * 单价 * 1.5 倍率（可配置）
     - 扣减预估金额 + 写入流水（"Credit Hold"）
   - **结算阶段**（AI 调用完成后）：
     - 计算实际消耗 = ceil(实际 tokens / 1000) * 单价
     - 退还差额（如果有多扣）
     - 写入结算流水（"Credit Settlement Refund"）
   - **回滚阶段**（AI 调用失败）：
     - 全额退还预扣金额
     - 写入回滚流水（"Credit Rollback - AI Error"）

3. **并发安全保证**：
   - PostgreSQL 行级锁（`FOR UPDATE`）串行化同一用户的并发请求
   - 事务边界清晰：预扣/结算/回滚分属不同事务
   - 预扣事务精简（仅积分读写），不包含耗时的 AI 调用

4. **积分流水审计**：
   - 所有积分变动（预扣/结算/回滚/管理员调整）均写入 Transaction 表
   - 支持按时间范围查询 + 消耗统计（consumed / refunded / net）
   - 流水记录包含 reason（变动原因）+ operator_id（管理员操作时记录）

5. **管理功能**：
   - 管理员可手动调整积分（增加或扣减）
   - 调整前校验余额（防止负积分）
   - 调整操作记入流水，包含操作者 ID

6. **Token 计费规则**：
   - 按 1K tokens 向上取整计费（`math.ceil(tokens / 1000)`）
   - 预扣倍率默认 1.5 倍（可配置），确保流式调用超出预估时有缓冲
   - 默认预估 1000 tokens（无明确估算时使用）

---

### Phase 2.2 - 流式对话核心 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ YAML 交互协议
  - YamlResponseParser（流式渐进解析 + 最终解析 + 降级纯文本）
  - YamlResponse 数据类（schema_version / speech / action / emotion / inner_thought）
- ✅ AI 模型抽象层
  - ModelProvider ABC（stream_chat + count_tokens）
  - GeminiProvider（google-genai SDK，支持 SPEED/PRO/ELITE 三档模型）
  - ModelProviderFactory（注册/获取 Provider）
  - StreamChunk / ModelConfig 数据类
- ✅ 向量嵌入层
  - EmbeddingProvider ABC（embed + embed_batch）
  - GeminiEmbeddingProvider（text-embedding-004 模型）
- ✅ 记忆引擎（core 层）
  - MemoryContext 数据类（5 层消息合并：system → summaries → pinned → long-term → short-term）
  - MemoryContextBuilder（场景感知，YAML 格式指令注入）
- ✅ 故事梗概引擎（core 层）
  - StorySummaryEngine（触发判断 + YAML 格式梗概 prompt 构建）
- ✅ 数据访问层
  - MemoryRepository（消息 CRUD + pgvector 余弦相似度检索 + 游标分页 + 消息操作 7 种）
  - StorySummaryRepository（CRUD + 最后梗概轮次 + 跨会话语义检索）
- ✅ 业务服务层
  - MemoryService（并发加载上下文 + 异步嵌入生成）
  - StorySummaryService（触发检查 + AI 生成 + YAML 解析 + 嵌入存储）
  - ChatService（15 步流式对话编排 + 7 种消息操作）
- ✅ API 路由层
  - **15 个对话端点**：
    - POST /api/v1/chat/stream - SSE 流式对话
    - GET /api/v1/chat/history/{character_id} - 对话历史（游标分页）
    - GET /api/v1/chat/sessions/{character_id} - 会话列表
    - DELETE /api/v1/chat/sessions/{session_id} - 删除会话
    - GET /api/v1/chat/summaries/{session_id} - 故事梗概
    - GET /api/v1/chat/recent-characters - 最近对话角色
    - PUT /api/v1/chat/messages/{message_id}/edit - 编辑消息
    - POST /api/v1/chat/messages/{message_id}/regenerate - 重新生成
    - DELETE /api/v1/chat/messages/{message_id} - 删除消息
    - POST /api/v1/chat/messages/{message_id}/rewind - 回退到消息
    - POST /api/v1/chat/messages/{message_id}/fork - 分叉会话
    - PUT /api/v1/chat/messages/{message_id}/feedback - 消息反馈
    - PUT /api/v1/chat/messages/{message_id}/pin - 固定消息
    - GET /api/v1/chat/customization/{character_id} - 获取自定义
    - PUT /api/v1/chat/customization/{character_id} - 更新自定义
- ✅ 依赖注入工厂
  - chat_deps.py（完整依赖链组装：Providers → Repos → Engines → Services → ChatService）

**文件清单（15 个新文件 + 6 个修改文件）：**
- `src/core/yaml_parser.py` (165 行) - YAML 响应解析器
- `src/core/model_provider.py` (90 行) - 模型抽象层
- `src/core/gemini_provider.py` (152 行) - Gemini 适配器
- `src/core/embedding_provider.py` (80 行) - 嵌入抽象层
- `src/core/memory_engine.py` (195 行) - 记忆引擎
- `src/core/story_summary_engine.py` (88 行) - 梗概引擎
- `src/repositories/memory_repo.py` (413 行) - 消息数据访问
- `src/repositories/story_summary_repo.py` (131 行) - 梗概数据访问
- `src/services/memory_service.py` (195 行) - 记忆服务
- `src/services/story_summary_service.py` (185 行) - 梗概服务
- `src/services/chat_service.py` (419 行) - 对话编排服务
- `src/api/chat_routes.py` (397 行) - 对话路由（15 个端点）
- `src/api/chat_deps.py` (130 行) - 依赖注入工厂
- `src/core/exceptions.py` (+80 行) - 8 个对话异常类
- `src/core/__init__.py` (修改) - 新增异常 + __all__ 导出
- `src/repositories/__init__.py` (修改) - 新增 MemoryRepository / StorySummaryRepository
- `src/services/__init__.py` (修改) - 新增 MemoryService / StorySummaryService / ChatService
- `main.py` (修改) - 挂载 chat_router

**测试验证：**
```bash
# ✅ 所有 Python 文件语法检查通过
python -c "import ast, os; ..." # 46 个文件全部 OK

# ✅ 核心模块导入成功
python -c "from src.core.yaml_parser import YamlResponseParser; print('✓')"
python -c "from src.core.gemini_provider import GeminiProvider; print('✓')"
python -c "from src.core.embedding_provider import GeminiEmbeddingProvider; print('✓')"
python -c "from src.core.memory_engine import MemoryContextBuilder; print('✓')"
python -c "from src.services.chat_service import ChatService; print('✓')"

# ✅ FastAPI 应用路由注册成功
python -c "from main import app; routes = [r for r in app.routes if hasattr(r, 'methods')]; print(f'✓ 路由总数: {len(routes)}')"
# 输出: ✓ 路由总数: 47
# - Auth: 6 | Character: 7 | Scene: 9 | Credit: 4 | Chat: 15 | Base: 2 | Docs: 4
```

**核心架构特性：**
1. **SSE 流式输出**：speech/action/done/error 四类事件，实时推送解析后的 YAML 结构
2. **YAML 交互协议**：AI 响应统一为 YAML 格式（speech/action/emotion/inner_thought），~30% token 节省
3. **5 层记忆架构**：system prompt → 故事梗概 → 固定消息 → 长期向量检索 → 短期 20 条
4. **场景感知对话**：ScenePromptBuilder 自动注入场景世界观、`{{char}}`/`{{user}}` 变量替换
5. **pgvector 语义检索**：余弦相似度搜索长期记忆 (Top-5) 和故事梗概 (Top-3)
6. **异步嵌入生成**：`asyncio.create_task()` 非阻塞生成消息向量嵌入
7. **故事梗概自动触发**：每 N 轮（默认 10，可配置）使用 Speed 模型生成 YAML 格式梗概
8. **完整消息操作**：编辑/重新生成/删除/回退/分叉/反馈/固定 — 各含权限校验与积分处理
9. **预扣-结算集成**：对话流中集成积分预扣，AI 失败自动回滚
10. **依赖注入工厂**：chat_deps.py 组装 15+ 个依赖对象，避免路由层复杂度

---

### Phase 3 - 管理后台与限流 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ Redis 滑动窗口限流器
  - SlidingWindowRateLimiter（Pipeline 原子操作：ZREMRANGEBYSCORE + ZCARD + ZADD + EXPIRE）
  - 支持多维度限流 key（user_id / IP）
- ✅ 限流中间件
  - RateLimitMiddleware（路由匹配限流规则 + 响应头注入 X-RateLimit-*）
  - 对话接口 10/60s、认证接口 5/60s/IP、通用 60/60s（均可配置）
  - 管理接口跳过限流
- ✅ 请求日志中间件
  - RequestLogMiddleware（method / path / status / duration_ms）
- ✅ 异常定义补充
  - RateLimitExceededError（含 retry_after）
  - ModelDisabledError
- ✅ 管理后台服务（拆分为两个类，遵守 300 行限制）
  - AdminService（用户列表/详情/积分调整/权限管理/近期消耗查询）
  - AdminResourceService（角色/场景管理 + 用户资源管理 + 对话日志 + 模型开关）
- ✅ Schema 补充
  - UserDetailResponse（含 character_count / scene_count / 权限字段）
  - ModelToggleRequest / ModelStatusResponse
- ✅ API 路由层
  - **18 个管理端点**：
    - GET /api/v1/admin/users - 用户列表（搜索 + 分页）
    - GET /api/v1/admin/users/{id} - 用户详情
    - PUT /api/v1/admin/users/{id}/credits - 积分调整
    - PUT /api/v1/admin/users/{id}/permissions - 权限管理
    - GET /api/v1/admin/users/{id}/consumption - 近期消耗（7/30 天）
    - GET /api/v1/admin/users/{id}/characters - 用户角色列表
    - DELETE /api/v1/admin/users/{id}/characters/{char_id} - 删除用户角色
    - GET /api/v1/admin/users/{id}/scenes - 用户场景列表
    - DELETE /api/v1/admin/users/{id}/scenes/{scene_id} - 删除用户场景
    - GET /api/v1/admin/users/{id}/logs - 对话日志
    - GET /api/v1/admin/characters - 角色列表（搜索 + creator 过滤）
    - GET /api/v1/admin/characters/{id} - 角色详情
    - DELETE /api/v1/admin/characters/{id} - 删除角色
    - GET /api/v1/admin/scenes - 场景列表（搜索 + creator 过滤）
    - GET /api/v1/admin/scenes/{id} - 场景详情
    - DELETE /api/v1/admin/scenes/{id} - 删除场景
    - GET /api/v1/admin/models - 模型开关状态
    - PUT /api/v1/admin/models/{tier}/toggle - 切换模型启用

**文件清单（5 个新文件 + 5 个修改文件）：**
- `src/utils/rate_limiter.py` (80 行) - Redis 滑动窗口限流器
- `src/api/middleware.py` (140 行) - 限流 + 请求日志中间件
- `src/services/admin_service.py` (230 行) - 用户管理服务
- `src/services/admin_resource_service.py` (300 行) - 资源管理 + 模型开关服务
- `src/api/admin_routes.py` (300 行) - 管理路由（18 个端点）
- `src/core/exceptions.py` (+20 行) - RateLimitExceededError / ModelDisabledError
- `src/core/schemas.py` (+30 行) - UserDetailResponse / ModelToggleRequest / ModelStatusResponse
- `src/core/__init__.py` (修改) - 新增异常 + Schema 导出
- `src/services/__init__.py` (修改) - 新增 AdminService / AdminResourceService
- `main.py` (修改) - 挂载 admin_router + 注册中间件

**测试验证：**
```bash
# ✅ 所有 Python 文件语法检查通过
# ✅ 所有模块导入成功
python -c "from src.utils.rate_limiter import SlidingWindowRateLimiter; print('✓')"
python -c "from src.services.admin_service import AdminService; print('✓')"
python -c "from src.services.admin_resource_service import AdminResourceService; print('✓')"
python -c "from src.api.admin_routes import router; print('✓')"
python -c "from src.api.middleware import RateLimitMiddleware, RequestLogMiddleware; print('✓')"

# ✅ FastAPI 应用路由注册成功
python -c "from main import app; routes = [r for r in app.routes if hasattr(r, 'methods')]; print(f'✓ 路由总数: {len(routes)}')"
# 输出: ✓ 路由总数: 65
# - Auth: 6 | Character: 7 | Scene: 9 | Credit: 4 | Chat: 15 | Admin: 18 | Base: 2 | Docs: 4
```

**核心特性：**
1. **Redis 滑动窗口限流**：Pipeline 原子操作，支持 user_id/IP 双维度
2. **路由级限流规则**：对话/认证/通用各有独立限额，管理接口免限流
3. **429 响应规范**：含 Retry-After / X-RateLimit-* 响应头
4. **用户管理**：搜索/详情/积分调整（行级锁）/权限控制/近期消耗聚合
5. **资源管理**：角色/场景全局搜索 + 软删除（清除 SceneCharacter 关联、设为非公开）
6. **消耗分析**：按天聚合趋势 + 总消耗/总退款/净消耗 + 近期流水明细
7. **模型开关**：Redis Hash 存储，支持动态启停模型档位
8. **审计合规**：所有管理操作记录 operator_id，积分调整写入 Transaction 流水
9. **服务拆分**：AdminService + AdminResourceService 两个类各不超过 300 行

---

### Phase 4 - 测试套件 ✅ 已完成 (2026-02-28)

**交付清单：**
- ✅ 测试配置
  - `pyproject.toml` — pytest 配置（asyncio_mode=auto, testpaths, markers）
  - `tests/conftest.py` — 完整 fixtures（db_engine, db_session, redis_client mock, client, user_factory, character_factory, test_settings）
- ✅ 单元测试（4 个文件，76 个用例）
  - `test_credit_engine.py` — 梯度定价、预扣倍率、退还差额、余额校验、定价查询
  - `test_yaml_parser.py` — 完整/流式/降级解析、speech 提取、存储格式化、往返一致性
  - `test_memory_engine.py` — 5 层合并顺序、截断逻辑（短期20/长效5/梗概3）、场景/角色 prompt 分支
  - `test_security.py` — bcrypt 哈希/验证、JWT 生成/解码/过期/篡改/类型校验
- ✅ 集成测试（2 个文件，26 个用例）
  - `test_auth_api.py` — 注册/登录/登出/获取用户/邮箱验证（9 用例）
  - `test_admin_api.py` — 非管理员 403 拒绝 + 用户/资源/模型管理（17 用例）

**文件清单（7 个新文件 + 1 个修改文件）：**
- `pyproject.toml` (新建) — pytest 配置
- `tests/conftest.py` (重写) — 全局 fixtures
- `tests/unit/test_credit_engine.py` — 积分引擎 22 用例
- `tests/unit/test_yaml_parser.py` — YAML 解析器 19 用例
- `tests/unit/test_memory_engine.py` — 记忆引擎 16 用例
- `tests/unit/test_security.py` — 安全工具 19 用例
- `tests/integration/test_auth_api.py` — 认证 API 9 用例
- `tests/integration/test_admin_api.py` — 管理 API 17 用例

**测试验证：**
```bash
# ✅ 全部 102 个用例通过
python -m pytest tests/ -v
# 102 passed in 3.28s

# 单元测试: 76 passed
# 集成测试: 26 passed
```

**测试策略：**
1. 单元测试：纯逻辑类直接测试，依赖类使用 MagicMock
2. 集成测试：dependency_overrides 替换 DB/Auth 依赖，验证路由可达性和 HTTP 状态码
3. AI 调用全部 Mock，不依赖外部服务
4. 权限验证：覆盖非管理员 403 拒绝场景

---

### Phase 5 - 前端页面 + 部署文档 ✅ 已完成 (2026-03-02)

**交付清单：**
- ✅ Next.js 15 项目初始化（App Router + TypeScript + Tailwind CSS）
- ✅ 全局布局（TopBar + Sidebar + AppShell 响应式设计）
- ✅ API 客户端（完整封装 65 个后端端点 + SSE 流式读取）
- ✅ 全局 Hooks（useUser/useDarkMode/useDebounce/useIntersection）
- ✅ 共用组件（CharacterCard/SceneCard/ChatBubble/Skeleton）
- ✅ 12 个页面：
  1. 首页 `/` — 继续对话 + 热门角色/场景 + 分类浏览
  2. 发现页 `/explore` — 角色/场景 Tab + 标签过滤 + 排序 + 无限滚动
  3. 搜索页 `/search` — 全局搜索结果 + Tab 切换
  4. 对话页 `/chat/[sessionId]` — SSE 打字机 + YAML 渲染 + 导演指令面板
  5. 新对话页 `/chat/new` — 角色/场景开聊入口
  6. 角色详情 `/character/[id]` — 角色介绍 + 性格/说话风格/示例对话
  7. 场景详情 `/scene/[id]` — 场景描述 + 目标 + 选角弹窗（三 Tab）
  8. 创建角色 `/create/character` — 完整表单（身份/性格/说话风格/示例对话）
  9. 创建场景 `/create/scene` — 引导式两步（设置 → 完善细节）
  10. 个人中心 `/profile` — 我的角色/场景/积分记录
  11. 管理用户 `/admin/users` — 用户列表 + 详情侧板（权限/积分/消耗/资源）
  12. 登录/注册/验证 `/auth/*` — 完整认证流程
- ✅ README.md 完整部署文档（快速开始 + Docker Compose + Nginx 配置）

**文件清单（30+ 个新文件）：**
- `frontend/package.json` — 项目依赖
- `frontend/tsconfig.json` / `tailwind.config.ts` / `postcss.config.mjs` — 配置
- `frontend/next.config.ts` — API 代理 rewrite
- `frontend/src/lib/types.ts` (190 行) — 全量类型定义
- `frontend/src/lib/api.ts` (170 行) — API 客户端封装
- `frontend/src/lib/hooks.ts` (80 行) — 全局 hooks
- `frontend/src/lib/utils.ts` (60 行) — 工具函数
- `frontend/src/app/globals.css` — Tailwind + 自定义样式
- `frontend/src/app/layout.tsx` — 根布局
- `frontend/src/app/(main)/layout.tsx` — 主布局 (AppShell)
- `frontend/src/components/TopBar.tsx` — 顶栏
- `frontend/src/components/Sidebar.tsx` — 侧边栏
- `frontend/src/components/AppShell.tsx` — 壳组件
- `frontend/src/components/CharacterCard.tsx` — 角色卡片
- `frontend/src/components/SceneCard.tsx` — 场景卡片
- `frontend/src/components/ChatBubble.tsx` — 对话气泡（YAML 结构化渲染）
- `frontend/src/components/Skeleton.tsx` — 骨架屏
- 12 个页面文件（`page.tsx`）
- `README.md` (重写) — 完整项目文档 + 部署指南

**前端特性：**
1. SSE 打字机效果：ReadableStream 逐字渲染 speech 字段
2. YAML 结构化渲染：action 斜体灰底、speech 正文、emotion 标签
3. 导演指令面板：旁白/OOC/内心/摄像机视角/描写画面/详细描写/继续
4. 深色模式：系统级 + 手动切换
5. 响应式设计：桌面/平板/移动端自适应
6. 无限滚动：IntersectionObserver 分页加载
7. 搜索防抖：300ms debounce
8. 骨架屏：首屏加载占位
9. 场景选角弹窗：三 Tab（发现/我的/最近）+ 搜索 + Suggested 标签
10. 管理融合式布局：左侧栏入口 + 用户详情侧板

---

## 项目完成

**所有 Phase 0-5 已完成。** 项目交付完毕。
