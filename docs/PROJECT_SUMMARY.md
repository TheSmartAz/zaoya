# Zaoya (造鸭) 已完成功能清单

> 最后更新: 2026-01-27

## 一、前端实现 (frontend/)

### 1.1 页面 (Pages)

| 页面 | 路径 | 功能说明 |
|------|------|----------|
| DashboardPage | `/src/pages/DashboardPage.tsx` | 项目列表和创建入口 |
| EditorPage | `/src/pages/EditorPage.tsx` | 编辑器，集成聊天面板和预览面板 |
| SettingsPage | `/src/pages/SettingsPage.tsx` | 用户设置页面 |

### 1.2 组件 (Components)

#### 聊天组件 (chat/)
- `ChatPanel.tsx` - 核心聊天面板，支持自适应访谈流程
- `InputBar.tsx` - 消息输入栏，支持流式响应
- `MessageList.tsx` - 消息列表显示

#### 布局组件 (layout/)
- `EditorLayout.tsx` - 编辑器布局，可调整大小的面板
- `PageLayout.tsx` - 页面布局
- `Panel.tsx` - 面板容器
- `Sidebar.tsx` - 侧边栏导航
- `Header.tsx` - 顶部导航栏

#### 预览组件 (preview/)
- `PreviewPanel.tsx` - 移动端预览面板（沙盒 iframe）
- `DeviceFrame.tsx` - 设备框架（模拟手机）

#### 构建组件 (build/)
- `BuildTimeline.tsx` - 构建时间线可视化
- `TaskList.tsx` - 任务列表与状态
- `CurrentTaskCard.tsx` - 当前任务卡片
- `PatchSummary.tsx` - 代码变更摘要
- `VerificationStatus.tsx` - 验证结果状态
- `ReviewStatus.tsx` - 审核决策状态
- `BuildControls.tsx` - 构建控制按钮（步进/中止/重试）

#### 组合组件 (composed/)
- `AgentCallout.tsx` - 代理状态徽章（requirementsAgent, uxAgent, techAgent）
- `BuildPlanCard.tsx` - 构建计划卡片
- `QuickActionChip.tsx` - 快速操作芯片
- `InterviewCard.tsx` - 访谈问题卡片

#### 设置组件 (settings/)
- `LanguageSection.tsx` - 语言设置
- `ModelSection.tsx` - AI 模型选择设置
- `DesignSection.tsx` - 设计系统设置
- `NotificationSection.tsx` - 通知设置
- `AccountSection.tsx` - 账户设置
- `SettingsPage.tsx` - 设置页面

#### 项目组件 (project/)
- `ProjectActions.tsx` - 项目操作菜单

#### UI 基础组件 (ui/)
- `button.tsx` - 按钮
- `card.tsx` - 卡片
- `input.tsx` - 输入框
- `badge.tsx` - 徽章
- `select.tsx` - 选择器
- `switch.tsx` - 开关
- `tabs.tsx` - 标签页
- `resizable.tsx` - 可调整大小
- `scroll-area.tsx` - 滚动区域

> 基于 shadcn/ui 实现

### 1.3 状态管理 (Stores)

| Store | 文件 | 功能 |
|-------|------|------|
| buildStore | `/src/stores/buildStore.ts` | 构建阶段、任务、补丁、验证、审核状态 |
| chatStore | `/src/stores/chatStore.ts` | 聊天消息、加载、错误状态 |
| projectStore | `/src/stores/projectStore.ts` | 项目、页面、预览状态 |
| settingsStore | `/src/stores/settingsStore.ts` | 用户设置状态（localStorage 持久化） |

### 1.4 类型定义 (Types)

- `project.ts` - 项目、页面、设计系统类型
- `buildPlan.ts` - 构建计划类型
- `chat.ts` - ChatMessage、ChatState 类型
- `interview.ts` - InterviewQuestion、InterviewOption、InterviewGroup 类型

### 1.5 钩子 (Hooks)

- `useTheme.ts` - 主题切换

### 1.6 E2E 测试

| 测试文件 | 覆盖范围 |
|----------|----------|
| `chat-panel.spec.ts` | 聊天面板 |
| `editor-page.spec.ts` | 编辑器页面 |
| `flows.spec.ts` | 用户流程 |
| `preview-panel.spec.ts` | 预览面板 |
| `interview.spec.ts` | 访谈流程 |
| `stores.spec.ts` | 状态管理 |
| `ui-components.spec.ts` | UI 组件 |
| `build-plan.spec.ts` | 构建计划 |

---

## 二、后端实现 (backend/)

### 2.1 主应用

**文件**: `app/main.py`

集成:
- CORS 中间件
- 错误处理中间件
- 安全头中间件
- 请求大小限制中间件
- 速率限制中间件
- 功能门控中间件
- 自定义域名路由中间件

### 2.2 API 路由

| 模块 | 文件 | 功能 |
|------|------|------|
| 聊天 | `api/chat.py` | AI 聊天 SSE 流式接口、模型列表 |
| 项目聊天 | `api/project_chat.py` | 项目聊天（自适应访谈 + 意图检测） |
| 访谈 | `api/interview.py` | 访谈流程 API |
| 认证 | `api/auth.py` | 认证接口（Auth0、Google、Dev） |
| 项目 | `api/projects.py` | 项目 CRUD、发布、导出/导入 |
| 页面 | `api/pages.py` | 页面 CRUD |
| 草稿 | `api/draft.py` | 草稿管理 |
| 快照 | `api/snapshots.py` | 快照管理、恢复 |
| 构建 | `api/build.py` | 构建流程 API（启动/步进/中止/状态） |
| 设置 | `api/settings.py` | 用户设置 |
| 提交 | `api/submissions.py` | 表单提交 |
| 分析 | `api/analytics.py` | 基础分析数据 |
| 高级分析 | `api/advanced_analytics.py` | 漏斗、留存、群组分析 |
| 版本 | `api/versions.py` | 版本管理 |
| 静态 | `api/static.py` | 静态文件服务 |
| 发布 | `api/public.py` | 发布页面服务 |
| 用户 | `api/users.py` | 用户 API |
| 资源 | `api/assets.py` | 资源管理、CDN |
| 积分 | `api/credits.py` | 积分系统 |
| 订阅 | `api/subscriptions.py` | 订阅管理 |
| 域名 | `api/domains.py` | 自定义域名 |
| 自定义页面 | `api/custom_pages.py` | 自定义域名页面路由 |
| 实验 | `api/experiments.py` | A/B 测试 |
| 下载 | `api/downloads.py` | 下载功能 |
| 设计系统 | `api/design_system.py` | 设计系统 |
| 内部 | `api/internal.py` | 内部 API |

### 2.3 服务层

| 服务 | 文件 | 功能 |
|------|------|------|
| AI 服务 | `services/ai_service.py` | 多模型 AI 集成（SSE 流式） |
| 意图检测 | `services/intent_detection.py` | 关键词 + AI 双重检测（8 种意图） |
| 访谈编排 | `services/interview_orchestrator.py` | 自适应访谈流程编排 (v2) |
| 访谈存储 | `services/interview_storage.py` | 访谈状态存储 |
| 提示构建 | `services/prompt_builder.py` | 系统提示词构建 |
| 验证器 | `services/validator.py` | HTML/JS 内容验证 |
| 发布服务 | `services/publish_service.py` | 发布服务 |
| 快照服务 | `services/snapshot_service.py` | 快照服务 |
| 草稿服务 | `services/draft_service.py` | 草稿服务 |
| 分析服务 | `services/analytics_service.py` | 分析服务 |
| 高级分析 | `services/advanced_analytics_service.py` | 高级分析服务 |
| 实验服务 | `services/experiment_service.py` | A/B 测试服务 |
| 订阅服务 | `services/subscription_service.py` | 订阅服务 |
| 用户服务 | `services/user_service.py` | 用户服务 |
| 域名服务 | `services/domain_service.py` | 域名服务 |
| 域名验证 | `services/domain_verification_job.py` | 域名验证后台作业 |
| 邮件服务 | `services/email_service.py` | 邮件服务 |
| 通知队列 | `services/notification_queue.py` | 异步通知队列 |
| 缓存 | `services/cache.py` | 缓存服务 |
| 存储 | `services/storage_service.py` | 存储服务 |
| 图片生成 | `services/image_generation_service.py` | 图片生成 |
| 下载服务 | `services/download_service.py` | 下载服务 |
| 导出服务 | `services/export_service.py` | 导出服务 |
| 访问控制 | `services/access_control.py` | 访问控制 |
| 审计服务 | `services/audit_service.py` | 审计服务 |
| 速率限制 | `services/rate_limiter.py` | 速率限制 |
| 认证服务 | `services/auth_service.py` | 认证服务 |
| Stripe Webhook | `services/stripe_webhook_service.py` | Stripe Webhook |

#### 构建运行时服务 (build_runtime/)

| 服务 | 文件 | 功能 |
|------|------|------|
| 编排器 | `build_runtime/orchestrator.py` | 构建状态机、多阶段编排 |
| 模型 | `build_runtime/models.py` | 构建阶段/任务模型、状态 |
| 存储 | `build_runtime/storage.py` | 构建状态持久化 |
| 代理 | `build_runtime/agents.py` | Planner/Implementer/Reviewer 代理 |
| 工具 | `build_runtime/tools.py` | 通用工具函数 |
| 仓库工具 | `build_runtime/repo_tools.py` | 仓库操作工具 |
| 验证工具 | `build_runtime/validate_tools.py` | 代码验证工具 |
| 检查工具 | `build_runtime/check_tools.py` | 测试、Lint 检查工具 |
| 快照工具 | `build_runtime/snapshot_tools.py` | 快照管理工具 |
| 策略 | `build_runtime/policies.py` | 构建策略配置 |

### 2.4 数据库模型

| 模型 | 文件 | 说明 |
|------|------|------|
| 用户 | `models/db/user.py` | 用户模型 |
| 项目 | `models/db/project.py` | 项目模型 |
| 项目页面 | `models/db/project_page.py` | 项目页面关联 |
| 页面 | `models/db/page.py` | 页面模型 |
| 快照 | `models/db/snapshot.py` | 快照模型 |
| 分析 | `models/db/analytics.py` | 分析模型 |
| 资源 | `models/db/asset.py` | 资源模型 |
| 积分 | `models/db/credit.py` | 积分模型 |
| 订阅 | `models/db/subscription.py` | 订阅模型 |
| 自定义域名 | `models/db/custom_domain.py` | 自定义域名模型 |
| 实验 | `models/db/experiment.py` | 实验模型 |
| 审计事件 | `models/db/audit_event.py` | 审计事件模型 |
| 访谈状态 | `models/db/interview_state.py` | 访谈状态模型 |
| 构建运行 | `models/db/build_run.py` | 构建运行模型 |

### 2.5 中间件

| 中间件 | 文件 | 功能 |
|--------|------|------|
| 错误处理 | `middleware/error_handler.py` | 全局错误处理 |
| 安全头 | `middleware/security_headers.py` | CSP、X-Frame-Options 等 |
| 速率限制 | `middleware/rate_limit.py` | API 速率限制 |
| 验证 | `middleware/validation.py` | 请求大小限制 |
| 功能门控 | `middleware/feature_gates.py` | 功能门控/特性开关 |
| 自定义域名 | `middleware/custom_domain.py` | 自定义域名路由 |

### 2.6 数据库迁移 (Alembic)

| 版本 | 迁移文件 | 说明 |
|------|----------|------|
| 001 | `078173891b20_initial_schema.py` | 初始模式 |
| 002 | `20250121_0001_add_analytics_tables.py` | 分析表 |
| 003 | `20250121_0002_add_experiments_tables.py` | 实验表 |
| 004 | `20250121_0003_add_credits_tables.py` | 积分表 |
| 005 | `20250121_0004_add_assets_table.py` | 资源表 |
| 006 | `20250121_0005_add_subscriptions_tables.py` | 订阅表 |
| 007 | `20260121_0006_fix_draft_constraint.py` | 草稿约束修复 |
| 008 | `20260122_0007_add_custom_domains_table.py` | 自定义域名表 |
| 009 | `20260122_0008_add_audit_events_table.py` | 审计事件表 |
| 010 | `20260123_0009_add_interview_state.py` | 访谈状态表 |
| 011 | `20260125_0010_create_build_runs_table.py` | 构建运行表 |
| 012 | `20260125_0011_add_build_run_agent_usage.py` | 构建代理使用表 |
| 013 | `20260126_0012_add_interview_states_table.py` | 访谈状态表 |
| 014 | `20260126_0013_add_project_pages_table.py` | 项目页面表 |
| 015 | `20260126_0014_normalize_project_pages_indexes.py` | 项目页面索引优化 |

### 2.7 配置

**文件**: `app/config.py`
- 环境配置
- 数据库配置
- 安全配置
- AI API 配置（多模型支持）
- OAuth 配置
- 邮件配置
- 速率限制配置

---

## 三、测试覆盖

### 3.1 后端测试 (backend/tests/)

| 测试文件 | 覆盖范围 |
|----------|----------|
| `test_chat_intent.py` | 聊天意图 |
| `test_project_chat_flow.py` | 项目聊天流程 |
| `test_intent_detection.py` | 意图检测 |
| `test_intent_detection_accuracy.py` | 意图检测准确性 |
| `test_experiment_service.py` | 实验服务 |
| `test_build_runtime_tools.py` | 构建运行时工具 |
| `test_build_runtime_orchestrator.py` | 构建编排器 |
| `test_build_runtime_models.py` | 构建模型 |
| `test_build_runtime_agents.py` | 构建代理 |

### 3.2 前端 E2E 测试

覆盖范围：
- 聊天面板
- 编辑器页面
- 预览面板
- 访谈流程
- 构建计划
- 状态管理
- UI 组件

---

## 四、已实现的核心功能清单

### 4.1 核心功能

| # | 功能 | 说明 |
|---|------|------|
| 1 | 自适应访谈流程 | AI 引导式需求收集，支持跳过和提前结束 |
| 2 | 意图检测 | 关键词 + AI 双重检测，8 种意图类别 |
| 3 | 构建编排系统 | Agentic 构建流程（规划→实施→验证→审核→迭代→就绪） |
| 4 | 多模型 AI 支持 | GLM-4.7、DeepSeek、Qwen、Hunyuan、Kimi、Doubao、MiniMax |
| 5 | 项目 CRUD | 完整项目管理 |
| 6 | 多页面支持 | 项目内多页面管理 |
| 7 | 发布系统 | 项目发布为公开页面 |
| 8 | 导出/导入 | 项目 JSON 格式导出导入 |
| 9 | 设计系统 | 可自定义的颜色、字体、间距、动画等 |
| 10 | 移动端预览 | 沙盒 iframe 实时预览 |
| 11 | 构建时间线 | 可视化构建进度 |
| 12 | 用户认证 | JWT + OAuth 支持（Auth0、Google） |
| 13 | 表单提交 | 发布页面的表单功能 |
| 14 | 分析追踪 | 页面视图和转化追踪 |
| 15 | 高级分析 | 漏斗、群组、留存分析 |
| 16 | 订阅系统 | Stripe 集成 |
| 17 | 积分系统 | 用户积分管理 |
| 18 | 自定义域名 | 域名绑定支持 + 验证 |
| 19 | A/B 测试 | 实验功能 |
| 20 | 速率限制 | API 访问控制 |
| 21 | 审计日志 | 操作记录 |
| 22 | 安全头 | CSP、X-Frame-Options 等 |
| 23 | 功能门控 | 特性开关 |

### 4.2 构建运行时系统

**多阶段编排**:
- Planning（规划）→ Implementing（实施）→ Verifying（验证）→ Reviewing（审核）→ Iterating（迭代）→ Ready（就绪）

**三个专业代理**:
- Planner Agent - 任务规划
- Implementer Agent - 代码实施
- Reviewer Agent - 代码审核

**验证工具**:
- TypeCheck（类型检查）
- Lint（代码规范）
- Unit tests（单元测试）
- JS AST validation（JS 语法树验证）

**补丁管理**:
- Diff-based changes（基于差异的变更）
- Revert capability（回滚能力）
- Token tracking（Token 使用追踪）

### 4.3 技术栈

**前端:**
- React 18 + TypeScript
- Vite 5
- Tailwind CSS + shadcn/ui + Radix UI
- Zustand (状态管理)
- React Router DOM
- React Resizable Panels
- DOMPurify (HTML 消毒)
- Acorn (JS AST 解析)
- Playwright (E2E 测试)

**后端:**
- FastAPI + Uvicorn
- SQLAlchemy 2.0 + asyncpg (PostgreSQL)
- Alembic (数据库迁移)
- Pydantic + pydantic-settings
- SSE-Starlette (Server-Sent Events) 流式响应
- python-jose (JWT)

**数据库:** PostgreSQL (15 个数据表)

---

## 五、Shared 目录

| 文件 | 说明 |
|------|------|
| `/shared/types.ts` | 共享类型定义（Message、Project、GenerationResponse） |

---

## 六、配置文件

| 文件 | 说明 |
|------|------|
| `frontend/package.json` | 依赖和脚本 |
| `backend/requirements.txt` | Python 依赖 |
| `frontend/vite.config.ts` | Vite 配置 |
| `frontend/playwright.config.ts` | Playwright 配置 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/tailwind.config.js` | Tailwind 配置 |
| `backend/alembic.ini` | 数据库迁移配置 |
| `conftest.py` | pytest 配置 |
| `pytest.ini` | pytest 设置 |

---

## 七、项目架构

### 7.1 核心流程

```
[选择模板] → [自适应访谈] → [首次生成]
→ [快速操作优化] → [发布] → [分享链接]
```

### 7.2 两域安全模型

| 域名 | 用途 |
|------|------|
| `zaoya.app` | 主应用（编辑器、仪表板、认证） |
| `pages.zaoya.app` | 发布的用户页面（无认证 Cookie） |

### 7.3 代码生成安全

**运行时 JavaScript 白名单 API**:
- `Zaoya.submitForm(formData)` - 表单提交
- `Zaoya.track('event', data)` - 事件追踪
- `Zaoya.toast('message')` - 提示消息

**通过 AST 验证阻止的危险模式**:
- Web Storage API 访问
- 原生 fetch/XHR (必须使用 Zaoya.* 封装)
- 动态代码执行
- 父框架访问

**CSP 安全头配置**:
```
default-src 'none';
img-src 'self' data: blob: https:;
style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;
script-src 'self';
connect-src https://api.zaoya.app;
frame-ancestors 'none';
```
