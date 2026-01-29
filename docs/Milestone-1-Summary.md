# Milestone-1 功能实现总结

> 基于代码库实际实现整理，非规格文档

---

## 1. 技术栈概览

### 1.1 前端技术栈

| 技术 | 用途 |
|------|------|
| **Vite** | 构建工具 |
| **React 18** | UI 框架 |
| **TypeScript** | 类型安全 |
| **Tailwind CSS** | 样式框架 |
| **Zustand** | 状态管理 |
| **shadcn/ui** | UI 组件库 |
| **Lucide React** | 图标库 |
| **React Router** | 路由 |

### 1.2 后端技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架 |
| **Python 3.12** | 运行时 |
| **SQLAlchemy + Alembic** | ORM + 数据库迁移 |
| **SQLite** | 数据库 |
| **OpenAI SDK** | AI 集成 |
| **SSE (Server-Sent Events)** | 流式事件传输 |

### 1.3 AI 模型支持

- **GLM-4.7** (智谱 AI) - 默认
- **GLM-4.7-Flash**
- **DeepSeek V3**
- **Doubao** (字节跳动)
- **Qwen / Qwen-Flash** (阿里云)
- **Hunyuan** (腾讯)
- **Kimi K2** (月之暗面)
- **MiniMax M2.1**

---

## 2. 核心功能模块

### 2.1 项目创建流程

```
选择模板 → 自适应访谈 → 首次生成 → 快速操作优化 → 发布 → 分享链接
```

### 2.2 已实现功能

| 模块 | 功能 | 状态 |
|------|------|------|
| **模板选择** | 模板分类展示和选择 | 已实现 |
| **自适应访谈** | 根据模板动态生成问题 | 已实现 |
| **ProductDoc** | 产品需求文档生成和编辑 | 已实现 |
| **BuildPlan** | 页面构建计划生成和审批 | 已实现 |
| **多页面生成** | 单页面/多页面自动生成 | 已实现 |
| **页面预览** | 移动端设备框架预览 | 已实现 |
| **任务流** | 实时任务状态展示 | 已实现 |
| **验证系统** | HTML/JS 安全验证 | 已实现 |
| **代码审核** | ReviewerAgent 自动审核 | 已实现 |
| **草稿管理** | 多版本快照管理 | 已实现 |
| **发布系统** | 页面发布和分享 | 已实现 |
| **表单提交** | 用户数据收集 | 已实现 |
| **数据分析** | 页面访问和点击追踪 | 已实现 |
| **设置页面** | 用户配置管理 | 已实现 |

---

## 3. Product Page 布局详解

### 3.1 设备框架规格

**DeviceFrame 组件** (`frontend/src/components/preview/DeviceFrame.tsx`)

```
iPhone X/11/12/13/14 系列规格 (19.5:9 比例)
├── 整体框架: 44px 圆角边框
├── 屏幕容器: 360px × 780px
├── 屏幕圆角: 36px
└── 顶部刘海: 100px × 28px (动态岛样式)
```

### 3.2 页面结构

生成的页面遵循以下结构：

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>页面标题</title>
  <meta name="description" content="...">
  <meta name="zaoya-public-id" content="xxx">
  <meta name="zaoya-api-base" content="https://api.example.com">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* 设计系统 CSS 变量 */
    :root {
      --color-primary: #18181b;
      --color-secondary: #71717a;
      --color-accent: #2563eb;
      --color-background: #ffffff;
      --color-text: #18181b;
      --font-heading-family: Geist;
      --font-body-family: Geist;
      --spacing-base: 16px;
      --radius-base: 8px;
    }
  </style>
</head>
<body class="bg-white">
  <!-- 页面头部 -->
  <header class="border-b sticky top-0 bg-white z-10">
    ...
  </header>

  <!-- 主要内容区域 -->
  <main id="zaoya-content" class="min-h-screen">
    <!-- 用户生成的内容 -->
  </main>

  <!-- 页面底部 -->
  <footer class="border-t mt-12 py-8">
    ...
  </footer>

  <!-- 运行时脚本 -->
  <script src="/assets/zaoya-runtime.js" defer></script>
  <script src="./page.js" defer></script>
</body>
</html>
```

### 3.3 zaoya-runtime.js API

用户生成页面可通过 `Zaoya` 全局对象调用平台能力：

| API | 功能 | 预览模式 | 发布模式 |
|-----|------|---------|---------|
| `Zaoya.submitForm(formData)` | 提交表单数据 | postMessage 发送到父窗口 | 直接调用 API |
| `Zaoya.track(event, data)` | 追踪分析事件 | postMessage | navigator.sendBeacon |
| `Zaoya.toast(message, type)` | 显示提示消息 | postMessage | 内置 toast UI |
| `Zaoya.navigate(path)` | 页面导航 | postMessage | 仅预览模式 |

### 3.4 预览组件结构

```
PreviewPanel
├── PreviewToolbar
│   ├── 视图切换（预览/产品文档）
│   ├── 页面选择下拉框
│   └── 刷新按钮
├── MultiPageOverview (多页面概览)
│   └── 页面卡片（可拖拽排序）
├── ProductDocView (产品文档查看器)
└── PreviewIframe (沙箱 iframe)
    └── HTML 内容渲染
```

### 3.5 缩略图规格

```
Thumbnail
├── 宽度: 160px
├── 高度: 347px
├── 比例: 9:19.5 (iPhone 14 Pro Max)
└── 视口: 390px × 844px (iPhone 14)
```

---

## 4. Chat Panel 功能与逻辑

### 4.1 文件结构

```
frontend/src/components/chat/
├── ChatPanel.tsx          # 主聊天面板组件
├── MessageList.tsx        # 消息列表渲染
├── InputBar.tsx           # 用户输入组件
├── cards/
│   ├── BuildPlanCard.tsx  # 构建计划卡片
│   ├── InterviewCard.tsx  # 访谈卡片
│   ├── PageCard.tsx       # 页面卡片
│   ├── ProductDocCard.tsx # 产品文档卡片
│   └── ValidationCard.tsx # 验证失败卡片
```

### 4.2 聊天状态机

ChatPanel 使用三层状态机管理用户交互：

```
┌─────────────────────────────────────────────────────────┐
│                         idle                            │  ← 用户首次输入
│                      (初始状态)                           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                       interview                         │  ← 回答模板问题
│                    (自适应访谈模式)                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ 访谈完成 / 用户选择生成
                         ▼
┌─────────────────────────────────────────────────────────┐
│                        chat                             │  ← 自由对话/迭代修改
│                     (页面构建与迭代模式)                    │
└─────────────────────────────────────────────────────────┘
```

| 状态 | 输入框 | 响应行为 |
|------|--------|---------|
| `idle` | 启用 | 用户首条消息触发访谈开始 |
| `interview` | 禁用 | 显示 InterviewCard 收集答案 |
| `chat` | 启用 | 正常对话流，调用 streamChat() 渲染页面 |

### 4.3 访谈模式流程

**数据结构**:

```typescript
interface InterviewGroup {
  id: string;
  topic: string;              // 访谈主题
  topic_label: string;        // 显示标签
  questions: InterviewQuestion[];  // 问题列表
  is_completed: boolean;
}

interface InterviewQuestion {
  id: string;
  text: string;
  type: 'single_select' | 'multi_select' | 'text' | 'date';
  options?: InterviewOption[];
  allow_other?: boolean;
}
```

**访谈流程**:

```
1. 用户输入需求
2. 后端返回访谈问题组 (InterviewGroup)
3. UI 显示 InterviewCard 组件
4. 用户选择/输入答案
5. 收集答案，提交到后端
6. 后端返回下一组问题或完成访谈
7. 访谈完成后自动/手动触发生成
```

**跳过机制**:
- 用户可跳过当前问题（标记为 `skip`）
- 用户可选择"立即生成"跳过剩余问题
- 访谈结束时自动触发生成

### 4.4 SSE 流式事件处理

**useBuildStream Hook** (`frontend/src/hooks/useBuildStream.ts`)

**监听的事件类型**:

| 事件类型 | 处理函数 | 用途 |
|---------|---------|------|
| `task` | `handleTaskEvent()` | 任务状态更新 |
| `card` | `handleCardEvent()` | 卡片事件（页面、验证等） |
| `preview_update` | `handlePreviewUpdate()` | 预览更新 |
| `plan_update` | `handlePlanUpdate()` | 计划更新 |
| `error` | 重连逻辑 | 错误处理 |

**重试机制**:
- 使用指数退避策略：`1000 * 2^n`，最大 10 秒
- 自动重连，无需用户干预

### 4.5 用户输入触发构建

```
用户输入
    │
    ▼
┌─────────────┐
│ mode ===    │
│ idle?       │── 是 ──→ submitInterview('start')
└──────┬──────┘
       │否
       ▼
┌─────────────┐
│ mode ===    │
│ chat?       │── 是 ──→ tryProductDocEdit(content)
└──────┬──────┘       │
       │否            ├── 是 ──→ 更新 ProductDoc
       ▼              │
┌─────────────┐       否
│ interview?  │── 是 ──→ 禁用输入，显示 InterviewCard
└─────────────┘
```

### 4.6 消息卡片类型

| 类型 | 组件 | 用途 |
|------|------|------|
| `agent_thinking` | AgentThinkingItem | AI 思考中 |
| `task_started` | TaskItem | 任务开始 |
| `task_done` | TaskItem | 任务完成 |
| `task_failed` | TaskItem | 任务失败 |
| `page` | PageCard | 页面创建 |
| `build_plan` | BuildPlanCard | 构建计划展示/审批 |
| `interview` | InterviewCard | 访谈问题展示 |
| `validation` | ValidationCard | 验证失败展示 |
| `product_doc_ready` | ProductDocCard | ProductDoc 就绪通知 |
| `build_complete` | TaskItem | 构建完成 |

### 4.7 BuildPlanCard 功能

- 页面列表展示和编辑（添加、删除、重命名、设为主页）
- 设计系统信息展示（风格、颜色）
- 特性标签展示
- 任务列表展示
- **Start build** 按钮触发构建

### 4.8 状态管理

**ChatStore** (`frontend/src/stores/chatStore.ts`):
- 消息历史管理
- 加载状态管理
- 错误状态管理

**BuildStore** (`frontend/src/stores/buildStore.ts`):
- 构建阶段状态
- 任务图谱管理
- 实时任务消息
- SSE 流状态

---

## 5. Agent 系统详解

### 5.1 文件结构

```
backend/app/services/build_runtime/
├── agents.py              # Agent 定义
├── orchestrator.py        # 构建编排器
├── multi_task_orchestrator.py  # 多任务编排器
├── models.py              # Pydantic 模型
├── events.py              # 事件系统
├── tools.py               # 工具入口
├── repo_tools.py          # 文件操作工具
├── validate_tools.py      # 验证工具
├── check_tools.py         # 检查工具
└── snapshot_tools.py      # 快照工具
```

### 5.2 Agent 类型

#### 5.2.1 PlannerAgent

**文件**: `agents.py:148-177`

**职责**: 将需求brief转换为可执行的BuildGraph任务计划

| 属性 | 值 |
|------|-----|
| 输入 | `brief`, `build_plan`, `product_doc` |
| 输出 | `BuildGraph` (任务列表) |
| 任务限制 | 最多15个任务，每个任务最多5个文件 |

**输出格式**:
```json
{
  "tasks": [
    {
      "id": "task_001",
      "title": "...",
      "goal": "...",
      "acceptance": [...],
      "depends_on": [],
      "files_expected": [...],
      "status": "todo"
    }
  ],
  "notes": "..."
}
```

#### 5.2.2 ImplementerAgent

**文件**: `agents.py:180-218`

**职责**: 根据任务生成代码补丁（unified diff）

| 属性 | 值 |
|------|-----|
| 输入 | `task`, `relevant_files`, `state`, `context` |
| 输出 | `PatchSet` (统一diff格式) |
| temperature | 0.2 (确定性生成) |
| 文件限制 | 最多修改5个文件 |

**约束**:
- 必须使用 `Zaoya.*` 函数
- 禁止 `fetch`/`XHR`
- 禁止 `localStorage`/`sessionStorage`
- 禁止 `eval`

#### 5.2.3 ReviewerAgent

**文件**: `agents.py:221-251`

**职责**: 审核补丁是否满足验收标准

| 属性 | 值 |
|------|-----|
| 输入 | `task`, `patchset`, `validation_report`, `check_report` |
| 输出 | `ReviewReport` (审核决策) |

**决策类型**:
- `APPROVE`: 所有标准满足，验证通过，无安全问题
- `REQUEST_CHANGES`: 需要修复问题

### 5.3 Agent 通信机制

#### 5.3.1 BaseAgent 基础通信

```python
class BaseAgent(ABC):
    async def run(self, **inputs: Any) -> AgentResult:
        # 1. 构建用户消息
        user_msg = self._build_user_message(inputs)
        # 2. 调用LLM
        llm_response = await self._call_llm(user_message)
        # 3. 解析输出
        parsed = self._parse_output(content)
        # 4. 返回结构化结果
        return AgentResult(output=output, raw_response=content, tokens_used=...)
```

#### 5.3.2 通过 BuildOrchestrator 协调

**BuildOrchestrator** 是核心编排器，管理整个构建流程：

```python
class BuildOrchestrator:
    def __init__(self, storage, planner, implementer, reviewer,
                 repo_tools, validate_tools, check_tools, snapshot_tools)
```

### 5.4 构建阶段状态机

```
┌─────────────────────────────────────────────────────────┐
│                    BuildOrchestrator                     │
│                 Deterministic State Machine              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │       PLANNING        │ ◄──────────────────┐
              │    (PlannerAgent)     │                   │
              └───────────┬───────────┘                   │
                          │ 生成BuildGraph                │
                          ▼                               │
              ┌───────────────────────┐                   │
              │     IMPLEMENTING      │ ◄────────────┐    │
              │  (ImplementerAgent)   │              │    │
              └───────────┬───────────┘              │    │
                          │ 生成PatchSet              │    │
                          ▼                           │    │
              ┌───────────────────────┐               │    │
              │       VERIFYING       │               │    │
              │  (Validate+CheckTools)│               │    │
              └───────────┬───────────┘               │    │
                          │ 生成报告                   │    │
                          ▼                           │    │
              ┌───────────────────────┐               │    │
              │       REVIEWING       │               │    │
              │   (ReviewerAgent)     │               │    │
              └───────────┬───────────┘               │    │
                          │                           │    │
          ┌───────────────┴───────────────┐           │    │
          │                               │           │    │
    APPROVE ▼                       REQUEST_CHANGES  │    │
          │                               │           │    │
          ▼                               ▼           │    │
  ┌─────────────────┐           ┌──────────────────┐  │    │
  │   Task DONE     │           │    ITERATING     │──┘    │
  │  (下一个任务/结束) │           │  (带反馈重新实现)  │       │
  └─────────────────┘           └──────────────────┘
```

### 5.5 Agent 触发条件

| 阶段 | 触发条件 | 调用的Agent/工具 |
|------|---------|-----------------|
| `PLANNING` | `state.phase == BuildPhase.PLANNING` 且无build_graph | PlannerAgent |
| `IMPLEMENTING` | `state.phase == BuildPhase.IMPLEMENTING` | ImplementerAgent |
| `VERIFYING` | 补丁应用成功后 | ValidateTools + CheckTools |
| `REVIEWING` | 验证和检查完成后 | ReviewerAgent |
| `ITERATING` | Reviewer要求修改时 | ImplementerAgent（带反馈） |

### 5.6 任务选择算法

```python
def _pick_next_task(self, state: BuildState) -> Optional[Task]:
    done_ids = {t.id for t in state.build_graph.tasks if t.status == TaskStatus.DONE}
    for task in state.build_graph.tasks:
        if task.status == TaskStatus.TODO:
            # 检查依赖是否都已完成
            if all(dep in done_ids for dep in task.depends_on):
                return task
    return None
```

### 5.7 事件驱动架构

#### 5.7.1 事件类型

```python
class BuildEventType(Enum):
    TASK_STARTED = "task_started"      # 任务开始
    TASK_DONE = "task_done"            # 任务完成
    TASK_FAILED = "task_failed"        # 任务失败
    AGENT_THINKING = "agent_thinking"  # Agent思考中
    TOOL_CALL = "tool_call"            # 工具调用
    CARD = "card"                      # UI卡片
    PREVIEW_UPDATE = "preview_update"  # 预览更新
    PLAN_UPDATE = "plan_update"        # 计划更新
    BUILD_COMPLETE = "build_complete"  # 构建完成
```

#### 5.7.2 事件发射

```python
class BuildEventEmitter:
    def task_started(self, task_id: str, title: str) -> BuildEvent
    def task_done(self, task_id: str, title: str) -> BuildEvent
    def task_failed(self, task_id: str, title: str, error: str) -> BuildEvent
    def agent_thinking(self, task_id: str, title: str) -> BuildEvent
    def build_plan_card(self, pages, tasks, estimated_tasks, ...) -> BuildEvent
    def validation_card(self, errors, suggestions, page_id) -> BuildEvent
    def preview_update(self, page_id: str) -> BuildEvent
    def build_complete(self, message: str) -> BuildEvent
```

#### 5.7.3 SSE 事件格式

```python
def to_sse_event(self) -> Dict[str, Any]:
    if self.type == BuildEventType.TASK_STARTED:
        return {
            "event": "task",
            "data": {"id": self.task_id, "type": "task_started",
                     "title": self.title, "status": "running"}
        }
    if self.type == BuildEventType.CARD:
        return {"event": "card", "data": {"type": self.card_type,
                                         "data": self.card_data}}
    # ...
```

### 5.8 工具层

#### 5.8.1 RepoTools

| 方法 | 用途 |
|------|------|
| `read(path)` | 读取文件内容 |
| `search(query)` | 搜索文件 |
| `apply_patch(patchset)` | 应用 diff 补丁 |

#### 5.8.2 ValidateTools

| 方法 | 用途 |
|------|------|
| `run(html, js)` | 验证 HTML/JS |

#### 5.8.3 CheckTools

| 方法 | 用途 |
|------|------|
| `typecheck()` | 前端类型检查 |
| `lint()` | 代码规范检查 |
| `unit()` | 后端单元测试 |
| `all()` | 汇总所有检查 |

#### 5.8.4 SnapshotTools

| 方法 | 用途 |
|------|------|
| `create()` | 创建版本快照 |
| `restore()` | 恢复版本快照 |

### 5.9 Pydantic 数据模型

| 模型 | 描述 |
|------|------|
| **Task** | 单个可执行任务单元（id, title, goal, acceptance, depends_on, files_expected） |
| **BuildGraph** | 任务计划图（最多15个任务，验证依赖关系） |
| **PatchSet** | 代码补丁（diff, touched_files） |
| **ValidationReport** | 验证结果（errors, warnings, normalized_html, js_valid） |
| **CheckReport** | 检查结果（typecheck_ok, lint_ok, unit_ok） |
| **ReviewReport** | 审核报告（decision, reasons, required_fixes） |
| **BuildState** | 完整构建状态（phase, current_task, history, agent_usage） |

### 5.10 MultiTaskOrchestrator

与 BuildOrchestrator 并行的多页面编排器：

```python
page_task_keys = [
    "page-{page_id}",    # 生成HTML
    "style-{page_id}",   # 应用样式
    "validate-{page_id}", # 验证HTML
    "secure-{page_id}",   # 安全检查(JS验证)
    "save-{page_id}",    # 保存页面
    "thumb-{page_id}",   # 生成缩略图
]
```

### 5.11 Interview Orchestrator

管理需求收集流程的独立编排器：

```
Interview Orchestrator
├── RequirementsAgent: 提取需求和约束
├── UXAgent: 用最少的问题减少歧义
└── TechAgent: 标记技术约束和风险
```

---

## 6. 核心数据流

```
用户输入
    │
    ▼
┌────────────────────────────────────────────────────────────────┐
│                      ChatPanel.handleSend                       │
└────────────────────────────┬───────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        submitInterview   streamChat   tryProductDocEdit
        (访谈模式)        (聊天模式)      (编辑产品文档)
              │              │
              ▼              ▼
        POST /api/projects/{id}/chat   POST /api/chat
              │              │
              ▼              ▼
        ┌─────────────────────────────────────────────────────┐
        │              SSE 流式响应处理                        │
        │  - event: task     → handleTaskEvent()              │
        │  - event: card     → handleCardEvent()              │
        │  - event: preview  → handlePreviewUpdate()          │
        │  - event: message  → handleOrchestratorResponse()   │
        └─────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        MessageList      buildStore      previewStore
        渲染卡片          更新任务状态      更新预览
```

---

## 7. API 端点

### 7.1 构建相关

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/build/start` | POST | 开始构建 |
| `/api/build/step` | POST | 单步执行 |
| `/api/build/{build_id}` | GET | 获取构建状态 |
| `/api/build/{build_id}/stream` | GET | SSE 流式事件 |
| `/api/build/{build_id}/abort` | POST | 中止构建 |
| `/api/build/{build_id}/can-publish` | GET | 检查是否可发布 |
| `/api/build/{build_id}/retry/{page_id}` | GET | 重试失败页面 |

### 7.2 产品文档 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/projects/{id}/product-doc` | GET | 获取 ProductDoc |
| `/api/projects/{id}/product-doc/edit` | POST | 编辑 ProductDoc |

### 7.3 项目相关

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/projects` | GET/POST | 项目 CRUD |
| `/api/projects/{id}/draft` | GET/POST | 草稿管理 |
| `/api/projects/{id}/pages` | GET/POST | 页面管理 |
| `/api/projects/{id}/snapshots` | GET | 快照历史 |

---

## 8. 安全机制

### 8.1 禁止的 JavaScript 模式

```python
BLOCKED_JS_PATTERNS = [
    (r'eva\w*\s*\(', '代码执行不允许'),
    (r'Function\s*\(', 'Function 构造函数不允许'),
    (r'fetch\s*\(', '网络请求不允许'),
    (r'localStorage', '本地存储不允许'),
    (r'sessionStorage', '会话存储不允许'),
    (r'window\.(top|parent|opener)', '框架访问不允许'),
]
```

### 8.2 允许的 HTML 标签

```python
ALLOWED_TAGS = [
    'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'img', 'ul', 'ol', 'li', 'button', 'form', 'input',
    'textarea', 'label', 'select', 'option', 'section', 'article',
    'header', 'footer', 'nav', 'main', 'table', 'tr', 'td', 'th',
    'thead', 'tbody', 'strong', 'em', 'br', 'hr', 'small', 'sub', 'sup',
]
```

### 8.3 CSP 头部（发布页面）

```
default-src 'none'
img-src 'self' data: blob: https:
script-src 'self'
style-src 'self' 'unsafe-inline'
connect-src https://api.zaoya.app
frame-ancestors 'none'
```

---

## 9. 开发状态

| 模块 | 状态 |
|------|------|
| 前端框架 | 已完成 |
| 后端 API | 已完成 |
| AI 集成 | 已完成 |
| 构建运行时 | 已完成 |
| Agent 系统 | 已完成 |
| 流式事件 | 已完成 |
| E2E 测试 | 已完成 |
| 文档 | 进行中 |
