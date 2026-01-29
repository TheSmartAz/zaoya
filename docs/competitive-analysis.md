# AI Web开发平台竞品分析报告

**项目**: Zaoya (造鸭)
**日期**: 2026-01-25
**目的**: 竞品调研与开源项目参考

---

## 目录

1. [四大竞品分析](#四大竞品分析)
2. [开源项目深度分析](#开源项目深度分析)
3. [Agent 与 Tools 实现模式](#agent-与-tools-实现模式)
4. [技术架构对比](#技术架构对比)
5. [Zaoya可参考内容](#zaoya可参考内容)
6. [附录：Agent 与 Tools 实现深度分析](#附录agent-与-tools-实现深度分析)

---

## 四大竞品分析

### 1. Lovable.dev

#### 主要功能
- **AI软件工程师**: 通过自然语言对话生成完整的应用程序
- **全栈生成**: 支持生成 Next.js 应用，包括前端和后端代码
- **GitHub集成**: 直接连接GitHub仓库进行代码备份、协作和部署
- **Supabase集成**: 内置数据库和认证支持，可描述数据结构让AI自动生成SQL
- **实时预览**: 边聊天边看到生成的代码效果
- **一键部署**: 支持部署到 Netlify、Vercel 等平台
- **自定义域名**: 支持添加自定义域名

#### 技术实现
- **前身**: GPT Engineer (开源CLI平台)
- **技术栈**: 基于 Next.js + React + Tailwind CSS + Supabase
- **架构**: 使用LLM (可能是GPT-4/Claude) 进行代码生成，通过专门优化的prompt engineering来生成高质量代码
- **部署**: 集成 Netlify、Vercel 等部署平台

#### 模板系统
- **提供模板**: 有专门的模板页面
- **模板类别**:
  - 电商网站 (Ecommerce store)
  - 作品集/Portfolio (Architect portfolio)
  - 个人博客 (Personal blog)
  - 活动平台 (Event platform)
  - 视觉落地页 (Visual landing page)
  - 时尚博客 (Fashion blog)
  - 生活方式博客 (Lifestyle Blog) 等
- **模板预览**: 每个模板都有预览截图，可以直接使用

#### Remix/二次开发
- **GitHub同步**: 项目可连接到GitHub，用户可以在GitHub上进行二次开发
- **代码导出**: 生成的是标准Next.js代码，可以导出后在本地继续开发
- **学习友好**: 用户通过观察AI生成的代码来学习前端开发最佳实践

#### 定位与目标用户
- **主要用户**: 创始人、产品经理、设计师、营销人员
- **适用场景**: 快速原型开发、MVP构建、内部工具

---

### 2. Replit Agent

#### 主要功能
- **AI编程助手**: 通过自然语言交互完成全流程开发
- **环境自动部署**: 自动下载、安装所需的包
- **智能代码生成**: 生成生产级代码，随着迭代不断进化
- **多语言支持**: 支持Python、JavaScript、TypeScript等多种语言
- **内置IDE**: 完整的浏览器内开发环境
- **协作功能**: 实时多人协作
- **数据库配置**: 自动配置数据库
- **社区生态**: 1500万+社区项目可供克隆

#### 技术实现
- **自研模型**: Replit-code-v1.5-3B (3B参数轻量级代码模型)
- **容器化技术**: 使用容器技术隔离开发环境
- **模型架构**: 专门针对代码生成优化的3B参数模型，在1T tokens数据上训练
- **Agent工作流**:
  1. 理解用户需求
  2. 规划开发步骤
  3. 自动安装依赖
  4. 编写代码
  5. 配置数据库
  6. 测试验证

#### 模板系统
- **首页模板区**: 提供大量模板如"Python计算器"、"HTML待办清单"等
- **模板类别**: Pygame游戏、Web应用等
- **快速启动**: 点击模板即可自动加载基础框架
- **社区分享**: 用户可以分享自己的代码，超过1500万个项目可供克隆和修改

#### Remix/Fork
- **社区分享**: 用户可以分享自己的代码
- **克隆功能**: 超过1500万个项目可供克隆和修改
- **从Bolt导入**: 支持从Bolt.new导入项目(通过导出到GitHub)
- **Fork机制**: 类似GitHub的fork功能，可以基于现有项目创建分支

#### 定位与目标用户
- **主要用户**: 开发者、初学者、非技术背景创业者
- **适用场景**: 全栈应用开发、学习编程、快速原型验证

---

### 3. Bolt.new (StackBlitz)

#### 主要功能
- **全栈开发**: 在浏览器中直接构建、运行、编辑、部署全栈应用
- **AI对话式开发**: 通过聊天界面描述需求，AI生成代码
- **实时运行**: 基于WebContainer技术，Node.js可在浏览器中直接运行
- **GitHub导入**: 支持导入GitHub仓库进行二次开发
- **一键部署**: 可直接部署到各种平台
- **版本历史**: 内置版本历史功能
- **终端支持**: 内置终端，可直接执行命令
- **自动安装包**: 动态安装npm包

#### 技术实现
- **核心专利技术**: WebContainer API - 基于WebAssembly的微操作系统
- **技术优势**: Node.js和npm可在客户端浏览器中运行
- **开源**: 部分开源 (代码库在GitHub上开源，但托管服务有商业限制)
- **AI模型**: 使用Claude Sonnet 3.5进行代码生成
- **架构**:
  - 前端: React + TypeScript
  - 框架: Remix
  - 包管理: 动态npm安装
  - 后端: 支持在浏览器中运行Node.js服务器

#### 模板系统
- **Starter Projects**: 内置starter projects系统
- **BoltStarter**: 第三方网站boltstarter.com提供预制的生产级模板
- **模板类别**: 仪表盘、聊天界面、全栈应用等
- **快速启动**: 可选择技术栈的starter模板

#### Remix/二次开发
- **GitHub导入**: `bolt.new/~/github/{username}/{repo}` 直接导入任何GitHub仓库
- **GitHub同步**: 可将项目连接到GitHub进行版本控制
- **代码导出**: 可导出到本地继续开发
- **可定制**: 生成的代码是标准React/Next.js代码，可自由修改

#### 定位与目标用户
- **主要用户**: 开发者、技术爱好者、快速原型开发者
- **适用场景**: 全栈应用原型、前端组件开发、快速演示

---

### 4. v0.dev (Vercel)

#### 主要功能
- **AI驱动UI生成**: 通过自然语言描述生成React组件和页面
- **全栈应用**: 从落地页到仪表盘、电商、AI应用
- **智能Agent**: 可搜索网页、检查网站、自动修复错误、集成外部工具
- **实时预览**: 实时预览应用，可视化进度指示
- **多模态**: 结合代码生成、网页浏览、调试、外部API交互
- **一键部署**: 部署到Vercel基础设施
- **Figma集成**: 可从Figma文件导入生成应用

#### 技术实现
- **AI SDK**: 基于Vercel AI SDK构建
- **技术栈**: Next.js + React + Tailwind CSS + shadcn/ui
- **模型架构**:
  - 使用Claude等大模型
  - Vercel AI SDK提供provider架构
  - Agentic loops实现自主代码生成
- **代码质量**: 生成符合最佳实践的代码

#### 模板系统
- **Templates页面**: `v0.app/templates` 提供社区模板
- **模板分类**:
  - Apps (完整应用)
  - Components (组件)
  - Starters (启动器)
- **Duplicate功能**: 可以一键复制/复刻任何模板
- **shadcn/ui集成**: 每个shadcn/ui组件都可以在v0中打开编辑

#### Remix/二次开发
- **复制代码**: 可以复制生成的代码到剪贴板
- **导出到GitHub**: 支持将项目导出到GitHub
- **本地开发**: 生成的Next.js代码可在本地继续开发
- **npx安装**: 提供npx命令快速使用生成的组件
- **社区分享**: 社区可以分享和发现模板

#### 定位与目标用户
- **主要用户**:
  - 产品经理 (快速原型验证)
  - 设计师 (将mockup转为高保真UI)
  - 工程师 (快速脚手架代码)
  - 数据科学家 (数据应用)
  - 营销团队 (营销页面)
  - 创始人 (快速MVP)
- **适用场景**: UI组件生成、全栈应用、营销页面、数据应用

---

## 综合对比表

| 维度 | Lovable.dev | Replit Agent | Bolt.new | v0.dev |
|------|-------------|--------------|----------|--------|
| **核心定位** | AI软件工程师 | AI编程助手+IDE | AI全栈Web开发 | AI UI生成器 |
| **主要输出** | Next.js全栈应用 | 多语言全栈应用 | 全栈Web应用 | React组件/全栈应用 |
| **开发环境** | 浏览器内 | 浏览器IDE | 浏览器内+终端 | 浏览器内 |
| **技术栈** | Next.js+Supabase | 多语言支持 | React/Node.js | Next.js+shadcn/ui |
| **模板系统** | ✅ 丰富模板 | ✅ 大量模板 | ✅ Starter项目 | ✅ 社区模板 |
| **GitHub集成** | ✅ 原生集成 | ✅ 支持 | ✅ 原生集成 | ✅ 可导出 |
| **Remix/Fork** | ✅ GitHub同步 | ✅ 1500万+项目 | ✅ GitHub导入 | ✅ Duplicate模板 |
| **一键部署** | ✅ Netlify/Vercel | ✅ Replit hosting | ✅ 多平台 | ✅ Vercel |
| **后端支持** | ✅ Supabase | ✅ 多种数据库 | ✅ Node.js运行 | ✅ 全栈 |
| **自定义域名** | ✅ | ✅ | ✅ | ✅ |
| **开源程度** | 闭源 | 部分开源 | 部分开源 | 闭源 |
| **学习曲线** | 低 | 中 | 中 | 低-中 |

---

## 关键差异与竞争优势

### Lovable.dev
- **优势**: 集成Supabase提供完整后端解决方案，适合快速构建完整应用
- **差异化**: 从GPT Engineer演进而来，代码质量较高
- **适合**: 需要快速上线的非技术创业者

### Replit Agent
- **优势**: 完整IDE体验，社区生态最丰富(1500万+项目)
- **差异化**: 自研轻量级代码模型，多语言支持
- **适合**: 学习者和需要完整开发环境的开发者

### Bolt.new
- **优势**: WebContainer技术让Node.js在浏览器中运行，真正的全栈开发
- **差异化**: 可直接导入GitHub仓库即时编辑
- **适合**: 需要快速原型和演示的技术用户

### v0.dev
- **优势**: 与Vercel生态深度集成，shadcn/ui原生支持
- **差异化**: 最强的UI生成能力，Agent能力(搜索、检查、修复)
- **适合**: UI/UX为主的项目，使用Next.js技术栈的团队

---

## 开源项目深度分析

### 1. Claude Code 开源分析

#### GitHub仓库: `anthropic/claude-code`

**开源程度**: 部分开源 (Apache 2.0 License)

#### 核心技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Node.js** | 18+ | 运行时环境 |
| **TypeScript** | 5.x | 类型安全 |
| **MCP SDK** | ^1.0.0 | Model Context Protocol |
| ** commander** | ^4.x | CLI 命令解析 |
| **Ink** | ^4.x | React CLI 界面 |

#### Agent 架构分析

Claude Code 采用 **Agent-First** 设计理念：

```typescript
// 核心 Agent Loop
interface AgentLoop {
  execute(input: UserInput): AsyncGenerator<AgentAction>;
  decide(context: Context): Promise<Decision>;
  callTool(name: string, args: any): Promise<ToolResult>;
  updateState(state: Partial<AgentState>): void;
}

// 复杂度分级系统
const COMPLEXITY_LEVELS = {
  NONE: '简单问答，无需工具',
  BASIC: '单轮工具调用',
  MIDDLE: '多轮工具调用 + 状态跟踪',
  HIGHEST: '多 Agent 协作 + 工具链'
};
```

#### 工具系统详解

```typescript
// Claude Code 核心工具集
const CORE_TOOLS = {
  // 文件操作
  Read: { description: '读取文件内容', concurrent: true },
  Write: { description: '创建/覆盖文件', concurrent: true },
  Edit: { description: '修改文件局部', concurrent: true },
  Glob: { description: '按模式查找文件', concurrent: true },
  Grep: { description: '文本搜索', concurrent: true },
  // 执行
  Bash: { description: '执行 Shell 命令', concurrent: false },
  // 网络
  WebFetch: { description: '获取 URL 内容', concurrent: true },
  WebSearch: { description: '网络搜索', concurrent: true },
  // 项目管理
  Task: { description: '子 Agent 任务', concurrent: true },
  TodoRead: { description: '读取任务列表', concurrent: true },
  TodoWrite: { description: '创建/更新任务', concurrent: true }
};
```

#### 三层记忆系统

```typescript
interface MemorySystem {
  // 短期记忆：当前会话
  shortTerm: { messages: Message[]; tokenCount: number; maxTokens: number; };
  // 中期记忆：Token ≥ 92% 时触发压缩
  midTerm: { filesModified: string[]; patternsFound: Pattern[]; currentFocus: string; decisions: Decision[]; };
  // 长期记忆：跨会话持久化
  longTerm: { userPreferences: UserPreferences; projectContext: ProjectContext; codingStandards: CodingStandards; };
}
```

#### 开源内容 vs 闭源内容

| 开源 (Apache 2.0) | 闭源/商业 |
|-------------------|-----------|
| ✅ CLI 框架和界面 | ✅ 核心 Agent 决策逻辑 |
| ✅ 工具定义和类型 | ✅ 提示词工程系统 |
| ✅ 插件系统框架 | ✅ 模型微调参数 |
| ✅ MCP SDK 实现 | ✅ 云端服务集成 |

### 2. Cline 开源分析

#### GitHub仓库: `cline/cline`

**开源程度**: 开源 (Apache 2.0 License)

#### 核心功能

| 功能 | 描述 |
|------|------|
| **文件编辑** | 创建/编辑文件，提供 diff view |
| **终端执行** | 执行 Shell 命令，支持长时间运行进程 |
| **浏览器控制** | 点击、输入、截图，基于 Claude Computer Use |
| **MCP 工具** | 动态创建和安装 MCP 工具 |
| **Checkpoint** | 版本快照和回滚 |

#### Human-in-the-loop 设计

```typescript
interface ApprovalRequest {
  diff: FileDiff;
  command?: string;
  preview?: string;
  userAction: 'approve' | 'edit' | 'reject';
}

interface WorkspaceSnapshot {
  id: string;
  timestamp: Date;
  files: Record<string, string>;
  commands: string[];
}
```

### 3. OpenCode 开源分析

#### GitHub仓库: `opencode-ai/opencode` (已归档，现为 "Crush")

**开源程度**: 开源 (MIT License)

#### 核心架构

OpenCode 采用独特的 **Client/Server 架构**，结合了现代 Web 技术与传统 CLI 体验：

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenCode 架构                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐         ┌─────────────────┐               │
│   │  Go TUI 客户端   │         │  Bun HTTP 服务  │               │
│   │ (Bubble Tea)    │ ←──→    │    (Hono)       │               │
│   └─────────────────┘  IPC    └─────────────────┘               │
│          │                                  │                   │
│          │                                  │                   │
│   ┌──────┴──────┐                   ┌───────┴───────┐           │
│   │  终端交互    │                   │  Agent 引擎    │           │
│   │  消息展示    │                   │  工具执行      │           │
│   └─────────────┘                   └───────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| 技术 | 版本/用途 |
|------|----------|
| **Go** | TUI 客户端 (Bubble Tea 框架) |
| **Bun** | HTTP 服务器 (Hono 框架) |
| **IPC** | 进程间通信 |
| **MCP** | Model Context Protocol 支持 |
| **LSP** | Language Server Protocol 集成 |

#### Agent 系统

OpenCode 定义了 **2 种主 Agent** 和 **2 种子 Agent**：

##### 主 Agent 类型

| Agent | 用途 | 特点 |
|-------|------|------|
| **Build Agent** | 代码构建和修改 | 专注于代码生成和编辑 |
| **Plan Agent** | 任务规划和分析 | 专注于理解和分解需求 |

##### 子 Agent 类型

| Subagent | 用途 | 触发条件 |
|----------|------|----------|
| **General Subagent** | 通用任务处理 | 简单任务委派 |
| **Explore Subagent** | 代码库探索 | 需要理解项目结构时 |

##### Agent 配置示例

```json
{
  "agents": {
    "build": {
      "description": "You are an expert software engineer...",
      "temperature": 0.3,
      "maxSteps": 100,
      "tools": ["bash", "read", "write", "edit", "glob"],
      "permissions": "auto"
    },
    "plan": {
      "description": "You are an expert project planner...",
      "temperature": 0.7,
      "maxSteps": 50,
      "tools": ["read", "grep", "list"],
      "permissions": "read-only"
    }
  }
}
```

#### 工具系统详解

OpenCode 提供了一套完整的内置工具集：

```typescript
// 内置工具常量定义
const BUILTIN_TOOLS = [
  {
    name: 'BashTool',
    description: 'Execute shell commands',
    category: 'execution'
  },
  {
    name: 'EditTool',
    description: 'Edit file contents with precision',
    category: 'file-operations'
  },
  {
    name: 'WebFetchTool',
    description: 'Fetch and parse web URL content',
    category: 'network'
  },
  {
    name: 'GlobTool',
    description: 'Find files by glob patterns',
    category: 'file-search'
  },
  {
    name: 'GrepTool',
    description: 'Search for patterns in files',
    category: 'file-search'
  },
  {
    name: 'ListTool',
    description: 'List directory contents',
    category: 'file-operations'
  },
  {
    name: 'ReadTool',
    description: 'Read file contents',
    category: 'file-operations'
  },
  {
    name: 'WriteTool',
    description: 'Create/overwrite files',
    category: 'file-operations'
  },
  {
    name: 'TodoWriteTool',
    description: 'Write task list',
    category: 'task-management'
  },
  {
    name: 'TodoReadTool',
    description: 'Read task list',
    category: 'task-management'
  },
  {
    name: 'TaskTool',
    description: 'Launch sub-agent for complex tasks',
    category: 'agent-orchestration'
  },
  {
    name: 'LSPTool',
    description: 'Language Server Protocol integration',
    category: 'code-intelligence'
  }
];
```

#### 核心工具实现示例

**1. BashTool 执行流程**
```go
type BashTool struct {
    timeout time.Duration
    workDir string
}

func (b *BashTool) Execute(command string) *ToolResult {
    // 执行 shell 命令
    // 支持超时控制
    // 返回 stdout/stderr
}
```

**2. TaskTool 子 Agent 调度**
```go
type TaskTool struct {
    sessions map[string]*AgentSession
}

func (t *TaskTool) Execute(subagentType string, task string) *ToolResult {
    // 创建新的会话
    session := NewAgentSession(subagentType)

    // 调度子 Agent
    result := session.Run(task)

    // 返回结果
    return &ToolResult{Output: result}
}
```

**3. LSPTool 集成示例**
```json
{
  "lsp": {
    "python": {
      "command": "pyright",
      "args": ["--stdio"],
      "workspaceRoot": "${workspace}"
    },
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    }
  }
}
```

#### 权限系统

OpenCode 实现了细粒度的权限控制：

| 权限级别 | 描述 | 适用场景 |
|----------|------|----------|
| **auto** | 自动执行，无需确认 | 快速开发 |
| **read-only** | 只读，禁止修改 | 代码审查 |
| **tool-specific** | 逐工具配置 | 精细控制 |

```json
{
  "permissions": {
    "bash": { "allow": ["npm install", "npm run dev"] },
    "write": { "allow": ["/src/**"] },
    "edit": { "allow": ["/src/**"] }
  }
}
```

#### MCP 集成

OpenCode 支持 MCP (Model Context Protocol) 工具扩展：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
      "env": { "DEBUG": "1" }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

#### 会话管理

OpenCode 实现了智能的会话管理机制：

```go
type Session struct {
    ID           string
    Messages     []Message
    Context      Context
    AutoCompact  bool
    TokenLimit   int
}

func (s *Session) AddMessage(msg Message) {
    s.Messages = append(s.Messages, msg)

    // 检查 token 限制
    if s.GetTokenCount() > s.TokenLimit * 0.9 {
        if s.AutoCompact {
            s.Compact()
        }
    }
}

func (s *Session) Compact() {
    // 压缩历史消息
    summary := Summarize(s.Messages)
    s.Messages = []Message{
        {Role: "system", Content: summary},
    }
}
```

#### 与其他工具对比

| 维度 | OpenCode | Claude Code | Cline |
|------|----------|-------------|-------|
| **架构** | Go+Bun TUI | Node.js CLI | VS Code 扩展 |
| **Agent** | 2+2 (主+子) | 多层记忆 | 单一 Agent |
| **工具数** | 12 内置 | 10+ | 8+ |
| **MCP** | ✅ 原生支持 | ✅ | ✅ |
| **LSP** | ✅ 原生集成 | ❌ | ✅ |
| **UI** | 终端 TUI | 终端 | VS Code |
| **许可证** | MIT | Apache 2.0 | Apache 2.0 |

#### 开源内容 vs 闭源内容

| 开源 (MIT License) | 闭源/商业 |
|-------------------|-----------|
| ✅ Agent 引擎实现 | ❌ 商业版托管服务 |
| ✅ 工具系统 | ❌ 云端 AI 集成 |
| ✅ TUI 客户端 | ❌ 高级分析功能 |
| ✅ 配置系统 | ❌ 企业版功能 |

#### 关键特点总结

1. **独特的架构设计**: Go TUI + Bun HTTP Server 的组合
2. **强大的工具集**: 12 种内置工具 + LSP + MCP 扩展
3. **子 Agent 机制**: TaskTool 支持动态调度子 Agent
4. **权限控制**: 细粒度的工具访问控制
5. **会话管理**: 自动压缩历史消息

#### 对 Zaoya 的参考价值

| 方面 | OpenCode 实践 | Zaoya 参考 |
|------|--------------|-----------|
| **工具设计** | 清晰的工具接口定义 | 可参考工具系统设计 |
| **子 Agent** | TaskTool 实现 | Interview Agent 模式 |
| **权限控制** | 细粒度权限 | 沙箱执行策略 |
| **会话管理** | 自动压缩 | 上下文管理 |

---

## Agent 与 Tools 实现模式

### 单 Agent 模式 (Bolt.new)

- **特点**：单一主 Agent，XML 格式输出，固定工具集
- **流程**：用户输入 → 上下文注入 → 主 Agent 决策 → XML 工具调用 → 执行 → 评估

### 多 Agent 协作模式 (Claude Code, Cline)

- **特点**：主 Agent 可启动子 Agent，独立工具集，适合复杂搜索
- **流程**：主 Agent 分析 → 简单任务直接处理 / 复杂任务启动子 Agent → 汇总结果

### Human-in-the-loop 模式 (Cline)

- **特点**：每次操作需要用户审核，提供 diff view，支持回滚
- **流程**：Agent 决策 → 生成变更 → 用户审核 (批准/修改/拒绝)

---

## 技术架构对比

### 执行环境对比

| 产品 | 环境 | 隔离级别 | 资源位置 |
|------|------|----------|----------|
| Bolt.new | WebContainer | 浏览器沙箱 | 本地浏览器 |
| Claude Code | 本地终端 | 主机访问 | 本地 |
| Cline | VS Code + 终端 | 混合 | 本地 |
| Codex | 云端沙盒 | 容器隔离 | 云端服务器 |

### 工具调用方式对比

| 产品 | 工具定义 | 调用方式 | 扩展性 |
|------|----------|----------|--------|
| Claude Code | 内置 Tool | Function Call | MCP 协议 |
| Cline | 内置 + MCP | Function Call | 动态创建 |
| Bolt.new | 内置 Action | XML 标签解析 | 固定 |

### 安全模型对比

| 产品 | 人工审核 | 沙箱隔离 | 权限控制 |
|------|----------|----------|----------|
| Claude Code | 可选 | 基础 | 多层 |
| Cline | 必须 | 基础 | 模式切换 |
| Bolt.new | 可选 | 强 (浏览器) | 基本 |

---

### 1. Bolt.new (StackBlitz) 开源分析

#### GitHub仓库: `stackblitz/bolt.new`

**开源程度**: 部分开源 (MIT License)

#### 目录结构
```
bolt.new/
├── app/
│   ├── components/        # UI组件
│   │   ├── chat/         # 聊天界面组件
│   │   ├── editor/       # 代码编辑器
│   │   ├── header/       # 头部导航
│   │   ├── sidebar/      # 侧边栏
│   │   ├── ui/           # 基础UI组件
│   │   └── workbench/    # 工作台
│   ├── routes/
│   │   ├── api.chat.ts   # AI聊天API路由
│   │   ├── api.enhancer.ts
│   │   └── chat.$id.tsx  # 聊天页面
│   ├── lib/.server/llm/  # LLM集成层
│   │   ├── constants.ts  # token限制等常量
│   │   ├── prompts.ts    # 系统提示词
│   │   └── stream-text.ts # 流式响应
│   ├── types/            # TypeScript类型定义
│   └── utils/            # 工具函数
├── functions/            # Cloudflare Functions
└── package.json
```

#### 核心技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Remix** | ^2.10.2 | 全栈框架 |
| **React** | ^18.2.0 | 前端UI |
| **CodeMirror** | ^6.x | 代码编辑器 |
| **@webcontainer/api** | 1.3.0-internal | 浏览器内Node.js运行环境 |
| **@ai-sdk/anthropic** | ^0.0.39 | Claude AI集成 |
| **ai** (Vercel AI SDK) | ^3.3.4 | AI SDK |
| **Cloudflare Pages/Workers** | - | 部署平台 |
| **xterm.js** | ^5.5.0 | 终端模拟器 |
| **UnoCSS** | ^0.61.3 | CSS框架 |
| **nanostores** | ^0.10.3 | 状态管理 |

#### 关键实现细节

**1. AI聊天API (`api.chat.ts`)**
```typescript
// 核心流程:
// 1. 接收消息数组
// 2. 创建SwitchableStream用于流式响应
// 3. 调用streamText生成AI响应
// 4. 当达到token限制时，自动继续生成
// 5. 返回流式响应

export async function action({ context, request }: ActionFunctionArgs) {
  const { messages } = await request.json<{ messages: Messages }>();
  const stream = new SwitchableStream();

  const options: StreamingOptions = {
    toolChoice: 'none',
    onFinish: async ({ text: content, finishReason }) => {
      // 处理token限制，自动继续生成
      if (finishReason === 'length') {
        messages.push({ role: 'assistant', content });
        messages.push({ role: 'user', content: CONTINUE_PROMPT });
        const result = await streamText(messages, context.cloudflare.env, options);
        return stream.switchSource(result.toAIStream());
      }
    }
  };

  const result = await streamText(messages, context.cloudflare.env, options);
  stream.switchSource(result.toAIStream());

  return new Response(stream.readable, {
    headers: { 'contentType': 'text/plain; charset=utf-8' }
  });
}
```

**2. WebContainer API**
- 这是StackBlitz的核心专利技术
- 允许Node.js和npm在浏览器中直接运行
- **商业限制**: 个人和开源免费，商业使用需要付费授权
- 官网: https://webcontainers.io/

**3. 开源内容 vs 闭源内容**

| 开源 (MIT License) | 闭源/商业 |
|-------------------|-----------|
| ✅ 前端UI界面 (React组件) | ❌ WebContainer核心实现 |
| ✅ 聊天API路由 (Remix) | ❌ AI prompt工程细节 |
| ✅ Remix应用结构 | ❌ 商业版托管的AI服务 |
| ✅ 部署配置 (Cloudflare) | ❌ 高级功能(如项目协作) |
| ✅ TypeScript类型定义 | ❌ WebContainer @internal版本 |

**4. 如何自建**
```bash
# 1. 克隆仓库
git clone https://github.com/stackblitz/bolt.new.git
cd bolt.new

# 2. 安装依赖
pnpm install

# 3. 配置.env.local
echo "ANTHROPIC_API_KEY=your_key_here" > .env.local

# 4. 运行开发服务器
pnpm run dev
```

**5. 关键限制**
- 无法复制完整的WebContainer体验（需要商业授权）
- 内部版本的`@webcontainer/api`包不可公开获取
- AI提示词工程细节未完全开源

---

### 2. Replit 开源分析

#### 主要开源项目

##### 1. **replit-code-v1-3b** (HuggingFace)

**模型规格:**
- 参数量: 2.7B
- 类型: Causal Language Model
- 专注: 代码补全 (Code Completion)
- 训练数据: Stack Dedup v1.2子集
- 训练tokens: 525B (原始数据集175B，20x Chinchilla)
- 支持语言: 20种编程语言
- 许可证: CC BY-SA 4.0 (可用于商业用途)
- 地址: https://huggingface.co/replit/replit-code-v1-3b

**性能:**
- 在HumanEval基准测试中超越所有开源代码模型
- 推理时间: 3-5秒 (NVIDIA A10G GPU)
- 超越OpenAI Codex

**最新版本: replit-code-v1.5-3b**
- 参数量: 3B
- 精度: bfloat16
- 训练数据: 1万亿tokens
- 也已开源在HuggingFace
- 许可证: 同样开放用于商业用途

##### 2. **Replit GitHub组织** (114个仓库)

主要开源类别:
- **开发工具**: Git集成、CLI工具
- **语言支持**: 多语言包和插件
- **模板和示例**: 各类项目模板
- **SDK和库**: Replit平台集成库
- 地址: https://github.com/replit

**重要说明**: Replit Agent的核心功能(聊天式AI编程助手)**并未开源**，仅作为商业产品提供。

#### 开源内容 vs 闭源内容

| 开源 | 闭源/商业 |
|------|-----------|
| ✅ replit-code-v1-3b/v1.5-3b模型 | ❌ Replit Agent核心逻辑 |
| ✅ 开发工具和插件 | ❌ IDE核心代码 |
| ✅ 项目模板 | ❌ AI Agent工作流 |
| ✅ 部署工具 | ❌ 协作功能 |
| ✅ 模型权重和配置 | ❌ 提示词工程系统 |

---

## 开源项目对比总结

| 维度 | Bolt.new | Replit |
|------|----------|--------|
| **开源仓库** | stackblitz/bolt.new (GitHub) | replit-code-v1-3b (HuggingFace) |
| **开源内容** | 前端UI + API路由 + 部署配置 | 代码生成模型 |
| **核心闭源** | WebContainer API技术 | Agent工作流 + IDE |
| **许可证** | MIT | CC BY-SA 4.0 (模型) |
| **自建难度** | 中等(需要WebContainer授权) | 高(需要自己实现Agent) |
| **AI模型** | 使用Claude API | 自研2.7B/3B模型 |
| **技术栈** | Remix + React + WebContainer | 多语言 + 容器化 |

### 关键启示

1. **开源策略**: 两者都采用"部分开源"策略 - 开源UI和框架，闭源核心技术
2. **WebContainer是关键**: Bolt.new的核心优势是WebContainer，这是需要商业授权的专利技术
3. **模型 vs 服务**: Replit开源了模型但闭源服务；Bolt.new开源了应用框架但闭源运行时
4. **自建可行但有限**: 可以基于Bolt.new开源代码搭建类似产品，但无法复制完整的WebContainer体验
5. **许可证选择**: MIT (Bolt) vs CC BY-SA (Replit模型)，MIT更宽松

---

## Zaoya可参考内容

基于对Bolt.new和Replit开源项目的分析，以下是Zaoya项目可以参考的内容：

### 1. UI/UX设计参考

#### 可直接复用的组件模式

| Bolt.new组件 | Zaoya参考价值 |
|-------------|--------------|
| ChatPanel组件 | 聊天界面布局、消息气泡样式 |
| Editor组件 (CodeMirror) | 代码预览面板实现 |
| Workbench组件 | 三栏布局（聊天-预览-代码） |
| Terminal组件 | 开发者调试面板 |
| Sidebar组件 | 项目历史/版本管理 |

#### 布局结构
```typescript
// 建议的三栏布局
┌─────────────────────────────────────────────────────┐
│                    Header                            │
├──────────────┬──────────────────┬───────────────────┤
│              │                  │                   │
│   ChatPanel  │   PreviewPanel   │   CodePanel       │
│   (聊天)     │   (预览)         │   (代码)          │
│              │                  │                   │
│              │                  │                   │
└──────────────┴──────────────────┴───────────────────┘
```

### 2. 技术栈参考

#### 推荐技术选型

| 技术 | Bolt.new使用 | Zaoya建议 |
|------|-------------|-----------|
| **前端框架** | Remix | Next.js (已有规划) |
| **UI组件** | Radix UI | shadcn/ui |
| **代码编辑器** | CodeMirror 6 | CodeMirror 6 或 Monaco |
| **状态管理** | nanostores | Zustand (已有) |
| **样式** | UnoCSS | Tailwind CSS (已有) |
| **AI SDK** | Vercel AI SDK | Vercel AI SDK |
| **流式响应** | Server-Sent Events | SSE (已有规划) |

### 3. 代码实现参考

#### 3.1 流式聊天API实现

**Bolt.new的做法 (`api.chat.ts`):**
```typescript
// 核心思路: 使用SwitchableStream处理流式响应
// 当token达到限制时，自动切换到新的流继续生成

import { streamText } from '~/lib/.server/llm/stream-text';
import SwitchableStream from '~/lib/.server/llm/switchable-stream';

export async function action({ context, request }: ActionFunctionArgs) {
  const { messages } = await request.json<{ messages: Messages }>();
  const stream = new SwitchableStream();

  const options: StreamingOptions = {
    toolChoice: 'none',
    onFinish: async ({ text: content, finishReason }) => {
      if (finishReason === 'length') {
        // 继续生成
        messages.push({ role: 'assistant', content });
        messages.push({ role: 'user', content: CONTINUE_PROMPT });
        const result = await streamText(messages, context.cloudflare.env, options);
        return stream.switchSource(result.toAIStream());
      }
      return stream.close();
    }
  };

  const result = await streamText(messages, context.cloudflare.env, options);
  stream.switchSource(result.toAIStream());

  return new Response(stream.readable, {
    status: 200,
    headers: { 'contentType': 'text/plain; charset=utf-8' }
  });
}
```

**Zaoya可参考:**
- 使用Vercel AI SDK的流式响应功能
- 实现自动继续生成机制
- 使用Server-Sent Events (SSE) 返回流式数据

#### 3.2 提示词工程

**Bolt.new的提示词结构 (可参考):**
```typescript
// app/lib/.server/llm/prompts.ts
const CONTINUE_PROMPT = `
Please continue the code generation where you left off.
DO NOT repeat the code you've already generated.
Continue from exactly where you stopped.
`;

const SYSTEM_PROMPT = `
You are an AI programming assistant...
`;
```

**Zaoya建议:**
- 建立专门的提示词模块 `backend/app/services/prompt_builder.py`
- 针对模板类型定制不同的系统提示词
- 实现上下文注入机制（项目历史、用户偏好等）

#### 3.3 工具函数参考

**Bolt.new提供的工具函数:**
```typescript
// app/utils/
- buffer.ts       # 缓冲区处理
- diff.ts         # 代码差异对比
- markdown.ts     # Markdown渲染
- shell.ts        # Shell命令处理
- terminal.ts     # 终端相关
```

**Zaoya可参考:**
- 代码diff展示（版本历史功能）
- Markdown渲染（聊天消息格式化）
- 终端日志输出（开发者调试）

### 4. 不建议参考的内容

| 内容 | 原因 |
|------|------|
| WebContainer API | 需要商业授权，且Zaoya不需要在浏览器中运行Node.js |
| CodeMirror高级功能 | Zaoya的代码面板是只读的，不需要编辑功能 |
| Cloudflare部署 | Zaoya有自己的部署架构 |
| 终端执行功能 | Zaoya面向非技术用户，不需要终端 |

### 5. 模板系统参考

**Bolt.new的模板结构:**
```
bolt.new/
└── starter-projects/
    ├── nextjs/
    ├── react/
    ├── vite/
    └── ...
```

**Zaoya建议的模板结构:**
```
zaoya/
└── templates/
    ├── personal-profile/      # 个人主页
    │   ├── prompt.yaml       # AI提示词配置
    │   ├── interview.json    # 采访问题模板
    │   └── preview.html      # 预览示例
    ├── event-invitation/      # 活动邀请
    ├── product-landing/       # 产品落地页
    └── contact-form/          # 联系表单
```

### 6. 项目结构建议

**参考Bolt.new的结构，Zaoya可以组织为:**

```
zaoya/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/          # 聊天面板
│   │   │   ├── preview/       # 预览面板
│   │   │   ├── code/          # 代码面板
│   │   │   └── editor/        # 编辑器
│   │   ├── hooks/
│   │   │   └── useChatStream.ts  # 流式聊天Hook
│   │   ├── stores/            # Zustand状态管理
│   │   └── types/             # TypeScript类型
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat.py        # 聊天API (参考api.chat.ts)
│   │   ├── services/
│   │   │   ├── ai_service.py  # AI服务
│   │   │   └── prompt_builder.py  # 提示词构建
│   │   └── models/
│   └── requirements.txt
│
└── docs/
    └── competitive-analysis.md  # 本文档
```

### 7. 具体实现建议

#### 7.1 流式聊天Hook (参考Bolt)

```typescript
// frontend/src/hooks/useChatStream.ts
import { useState, useCallback } from 'react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export function useChatStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMessage] })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';

      // 读取流式响应
      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);
        assistantContent += chunk;

        // 实时更新消息
        setMessages(prev => {
          const newMessages = [...prev];
          const lastMessage = newMessages[newMessages.length - 1];
          if (lastMessage?.role === 'assistant') {
            lastMessage.content = assistantContent;
          } else {
            newMessages.push({ role: 'assistant', content: assistantContent });
          }
          return newMessages;
        });
      }

      setIsStreaming(false);
    } catch (error) {
      console.error('Chat error:', error);
      setIsStreaming(false);
    }
  }, [messages]);

  return { messages, sendMessage, isStreaming };
}
```

#### 7.2 项目配置文件

**参考Bolt.new的package.json，Zaoya前端建议:**

```json
{
  "name": "zaoya-frontend",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@radix-ui/react-dialog": "^1.1.1",
    "@radix-ui/react-dropdown-menu": "^2.1.1",
    "@codemirror/lang-javascript": "^6.2.2",
    "@codemirror/lang-html": "^6.4.9",
    "@codemirror/lang-css": "^6.2.1",
    "@uiw/codemirror-theme-vscode": "^4.23.0",
    "@codemirror/view": "^6.28.4",
    "nanostores": "^0.10.3",
    "zustand": "^4.x",
    "tailwindcss": "^3.x",
    "react-markdown": "^9.0.1",
    "shiki": "^1.9.1"
  }
}
```

### 8. 开源许可证建议

参考Bolt.new的MIT许可证，Zaoya建议:

- **核心代码**: MIT License (宽松，便于社区贡献)
- **模板内容**: CC BY 4.0 (允许分享和修改)
- **AI提示词**: 专有 (不公开，作为核心竞争优势)

---

## 总结

### 关键行动项

1. **短期参考** (可直接复用)
   - 三栏布局设计 (Chat-Preview-Code)
   - 流式聊天实现模式
   - Markdown代码高亮渲染
   - Radix UI组件库

2. **中期参考** (需要适配)
   - 提示词工程模块
   - 模板系统结构
   - 版本历史机制
   - 项目导出功能

3. **不参考** (不适用)
   - WebContainer (过度设计)
   - 终端功能 (目标用户不需要)
   - 复杂的代码编辑 (只需只读预览)

### 差异化定位

相比竞品，Zaoya的差异化点:

| 竞品 | 缺失 | Zaoya优势 |
|------|------|-----------|
| v0.dev | 英文为主、面向开发者 | 中文优先、面向非技术用户 |
| Bolt.new | 需要技术背景 | 模板引导+自适应采访 |
| Lovable | 通用网站构建 | 专注移动端落地页 |
| Replit | IDE风格 | 简洁的对话式体验 |

---

# 附录D：四大产品 Agent 实现深度对比 (2025)

## D.1 Bolt.new Agent 架构详解

### 核心架构

Bolt.new 的架构简洁而高效，核心思想是：**"精心设计的提示词 + LLM = 代码生成"**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Bolt.new Agent 流程                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   用户请求 → 系统提示词 → Reasoning 思考 → 上下文注入 → 代码生成 │
│                     ↓                                           │
│              XML 格式输出                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ <boltAction type="file" filePath="/src/App.tsx">       │   │
│   │   // React code here                                    │   │
│   │ </boltAction>                                           │   │
│   │                                                          │   │
│   │ <boltAction type="command">                             │   │
│   │   npm install && npm run dev                            │   │
│   │ </boltAction>                                           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                     ↓                                           │
│              WebContainer 解析执行                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 技术特点

| 方面 | 实现方式 | 说明 |
|------|----------|------|
| **工具调用** | 隐式工具 | LLM 生成 XML 标签作为文本，解析器提取执行 |
| **执行环境** | WebContainer | 浏览器内 WebAssembly 沙箱，完全隔离 |
| **系统提示词** | 迭代优化 | 数千个用户反馈积累的规则 (ULTRA IMPORTANT 标记) |
| **错误处理** | 重试机制 | "attempt fix" 自动修复 |
| **安全性** | 沙箱隔离 | 无网络持久化，无本地文件访问 |

### 提示词演化 (来自开源代码)

```
v1: "You are Bolt, an AI assistant..."
     ↓ 用户反馈: 输出太冗长
v2: "DO NOT be verbose unless asked..."
     ↓ 仍有命名问题
v3: "IMPORTANT: Follow naming conventions..."
     ↓ 继续失败
v4: "ULTRA IMPORTANT: Think first, then generate..."
```

### 核心代码结构

```typescript
// Bolt.new 核心流程 (简化)
async function generateCode(userRequest: string) {
  // 1. 构建系统提示词
  const systemPrompt = buildSystemPrompt();

  // 2. 推理阶段 (Thinking)
  const reasoning = await llm.thinking(
    `分析用户需求: ${userRequest}`,
    systemPrompt
  );

  // 3. 生成阶段
  const response = await llm.complete(
    reasoning + userRequest,
    { format: 'xml' }
  );

  // 4. 解析 XML 标签
  const actions = parseXML(response);

  // 5. 执行
  for (const action of actions) {
    if (action.type === 'file') {
      await webContainer.writeFile(action.filePath, action.content);
    } else if (action.type === 'command') {
      await webContainer.runCommand(action.command);
    }
  }
}
```

### 为什么选择隐式工具？

| 对比项 | 显式工具 (Cursor) | 隐式工具 (Bolt) |
|--------|-------------------|-----------------|
| 可靠性 | 高 (类型检查) | 中 (依赖 LLM 格式) |
| 扩展性 | 需定义函数 | 直接生成文本 |
| 外部集成 | API 调用 | 有限 |
| 复杂度 | 高 | 低 |
| 适用场景 | 专业开发 | 快速原型 |

**Bolt 的权衡**：牺牲扩展性换取简单性和安全性

---

## D.2 v0 Agent 架构详解

### 架构演进

v0 从"描述 → 生成"发展为"Agentic Architecture"：

```
┌─────────────────────────────────────────────────────────────────┐
│                    v0 Agent 演进                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   v1 (2023): 描述 → 生成代码                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ 用户: "Build a dashboard with charts"                   │   │
│   │ v0: 生成 React + Tailwind 代码                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   v2 (2025): Agentic Architecture                               │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ 1. 自主规划任务清单                                      │   │
│   │ 2. 自动搜索和检查网站                                    │   │
│   │ 3. 自动修复错误                                          │   │
│   │ 4. 集成外部工具 (数据库、API)                            │   │
│   │ 5. 用户反馈循环                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心能力

根据 v0 官方文档，Agent 具备以下能力：

| 能力 | 描述 |
|------|------|
| **Web Search** | 搜索网页获取最新信息 |
| **Site Inspection** | 检查和读取网站内容 |
| **Error Fixing** | 自动诊断和修复代码错误 |
| **External Integration** | 集成第三方 API 和数据库 |
| **Task Planning** | 自主创建和管理任务清单 |

### 技术实现

```typescript
// v0 Agent 架构 (推测)
interface v0Agent {
  // 任务规划
  planTasks(userRequest: string): Task[];

  // 执行任务
  executeTask(task: Task): Promise<Result>;

  // 质量检查
  validateOutput(output: string): ValidationResult;

  // 用户交互
  requestFeedback(result: Result): Promise<UserFeedback>;
}

class v0AgentImpl implements v0Agent {
  async planTasks(request: string): Promise<Task[]> {
    // 使用 LLM 分解任务
    const plan = await this.llm.complete(`
      将以下请求分解为任务清单:
      ${request}

      返回 JSON 格式:
      [{ "task": "描述", "type": "frontend|backend|config" }]
    `);
    return JSON.parse(plan);
  }

  async executeTask(task: Task): Promise<Result> {
    switch (task.type) {
      case 'frontend':
        return this.generateUI(task);
      case 'backend':
        return this.generateAPI(task);
      case 'config':
        return this.generateConfig(task);
    }
  }
}
```

### v0 模型选择

v0 使用复合模型系列：

| 模型 | 用途 |
|------|------|
| **v0-1.5-sm** | 快速简单任务 |
| **v0-1.5-md** | 日常开发 |
| **v0-1.5-lg** | 复杂项目 |
| **GPT-5** | 最新高级任务 |

### 与 Bolt 的关键区别

| 方面 | Bolt.new | v0 |
|------|----------|-----|
| **工具调用** | 隐式 (XML) | 显式 (Tool Calling) |
| **任务规划** | 单一响应 | 自主分解多任务 |
| **外部集成** | 无 | 支持 API/数据库 |
| **目标用户** | 技术用户 | 所有人 (设计师/PM/创始人) |
| **部署** | 多平台 | Vercel 原生 |

---

## D.3 Lovable Agent 架构详解

### 产品定位

Lovable 专注于 **"AI 软件工程师"** 体验，强调快速构建完整应用。

```
┌─────────────────────────────────────────────────────────────────┐
│                      Lovable 核心特点                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Supabase 原生集成                                           │
│      - 自动创建数据库 schema                                     │
│      - 认证系统集成                                              │
│      - API 自动生成                                              │
│                                                                  │
│   2. 完整栈生成                                                  │
│      - 前端 (React/Next.js)                                      │
│      - 后端 (API Routes)                                         │
│      - 数据库 (PostgreSQL)                                       │
│      - 认证 (Supabase Auth)                                      │
│                                                                  │
│   3. 支付集成                                                    │
│      - Stripe 集成                                               │
│      - 订阅管理                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术 |
|------|------|
| **前端框架** | Next.js / React |
| **样式** | Tailwind CSS |
| **数据库/后端** | Supabase |
| **支付** | Stripe |
| **AI 模型** | GPT-4 / Claude |

### Agent 工作流程

```typescript
interface LovableAgent {
  // 需求理解
  understandRequest(userInput: string): UserIntent;

  // 数据库设计
  designDatabase(intent: UserIntent): DatabaseSchema;

  // 前端生成
  generateFrontend(schema: DatabaseSchema): FrontendCode;

  // 后端生成
  generateBackend(schema: DatabaseSchema): BackendCode;

  // 集成配置
  configureIntegrations(intent: UserIntent): IntegrationConfig;
}

class LovableAgentImpl implements LovableAgent {
  async designDatabase(intent: UserIntent): Promise<DatabaseSchema> {
    // 分析用户需求，生成数据库设计
    const schema = await this.llm.complete(`
      为以下应用设计 Supabase 数据库 schema:
      ${JSON.stringify(intent)}

      返回 PostgreSQL DDL 和 Row Level Security 规则
    `);

    // 自动执行数据库迁移
    await this.supabase.runMigrations(schema);
    return schema;
  }
}
```

### 与 Bolt 对比

| 方面 | Lovable | Bolt.new |
|------|---------|----------|
| **数据库** | 原生 Supabase | 无 |
| **认证** | 内置 | 无 |
| **部署** | 一键部署 | 多平台 |
| **代码导出** | 完整项目 | 完整项目 |
| **价格** | 订阅制 | 订阅制 |
| **复杂度** | 中 | 低 |

---

## D.4 Replit Agent 3 架构详解

### 架构演进

Replit Agent 经历了重大演进：

```
┌─────────────────────────────────────────────────────────────────┐
│                  Replit Agent 架构演进                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Agent V1: 单体 Agent                                           │
│   └── 单一 Agent 处理所有任务                                     │
│                                                                  │
│   Agent V2: ReAct 风格                                           │
│   └── 迭代循环，工具调用                                          │
│                                                                  │
│   Agent 3: 多 Agent 架构 (2025)                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Manager Agent: 工作流协调                               │   │
│   │  ├─→ Editor Agent: 代码编辑                             │   │
│   │  ├─→ Backend Agent: 后端开发                            │   │
│   │  └─→ Verifier Agent: 代码验证 + 用户反馈                │   │
│   │                                                          │   │
│   │  新增能力:                                               │   │
│   │  ├─ App Testing: 自动浏览器测试                         │   │
│   │  ├─ Max Autonomy: 200分钟自主运行                       │   │
│   │  └─ Agent Building: 生成其他 Agents                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 多 Agent 协作

根据 LangChain 官方分析，Replit 的多 Agent 设计：

```typescript
// Replit 多 Agent 架构
interface ReplitAgents {
  manager: ManagerAgent;
  editor: EditorAgent;
  verifier: VerifierAgent;
}

class ManagerAgent {
  async coordinate(goal: string): Promise<void> {
    // 1. 分解任务
    const tasks = await this.plan(goal);

    // 2. 分发任务
    for (const task of tasks) {
      const agent = this.selectAgent(task);
      const result = await agent.execute(task);

      // 3. 验证结果
      const verification = await this.verifier.check(result);

      if (!verification.passed) {
        // 4. 用户反馈循环
        const feedback = await this.requestUserInput(verification);
        await this.iterate(task, feedback);
      }
    }
  }
}

class VerifierAgent {
  // Verifier 独特之处：不只是检查，还会与用户沟通
  async check(output: AgentOutput): Promise<VerificationResult> {
    const issues = await this.findIssues(output);

    if (issues.length > 0) {
      // 不是盲目继续，而是询问用户
      return {
        passed: false,
        feedback: await this.formulateQuestions(issues),
        suggestions: await this.suggestFixes(issues)
      };
    }

    return { passed: true };
  }
}
```

### 核心技术特点

| 能力 | 实现方式 |
|------|----------|
| **自动测试** | 真实浏览器自动化 (非 Computer Use) |
| **自主级别** | 4 级 autonomy 控制 |
| **任务时长** | 最高 200 分钟 |
| **Agent 生成** | 可创建 Telegram/Slack bots |
| **集成** | Notion, Linear, Dropbox, SharePoint |

### 提示词工程

Replit 使用的高级技术：

```typescript
// 1. Few-shot 示例
const fewShotExamples = [
  {
    input: "Create a login page",
    output: "生成包含 email/password 表单的 React 组件..."
  },
  {
    input: "Add user authentication",
    output: "实现 Supabase Auth 集成..."
  }
];

// 2. 动态提示词构建
function buildDynamicPrompt(context: AgentContext): string {
  return `
    <system_role>你是 Replit Agent...</system_role>
    <current_state>${context.currentFiles}</current_state>
    <memory>${compressMemory(context.longMemory)}</memory>
    ${formatAsXML(context.tools)}
    ${fewShotExamples}
  `;
}

// 3. 记忆压缩
async function compressMemory(memory: Memory[]): Promise<string> {
  const summary = await llm.summarize(memory);
  return truncateToTokenLimit(summary, MAX_TOKENS);
}
```

### 工具调用创新

Replit 没有使用标准的 Function Calling，而是：

```python
# Replit 自定义 DSL
TOOL_INVOCATION = """
<tool_call>
  name: "create_file"
  args: {
    path: "/src/App.tsx",
    content: """
    import React from 'react';
    // ... code
    """
  }
</tool_call>
"""

# 相比 OpenAI Function Calling，Replit 选择生成代码调用工具
# 原因：30+ 工具需要复杂参数，自定义 DSL 更可靠
```

### App Testing 实现

```typescript
// Agent 3 的自动测试能力
class AppTester {
  async testApplication(): Promise<TestResult> {
    // 1. 启动真实浏览器
    const browser = await this.launchBrowser();

    // 2. 模拟用户操作
    await browser.click('#login-button');
    await browser.fill('#email', 'test@example.com');
    await browser.fill('#password', 'password123');
    await browser.click('#submit');

    // 3. 验证结果
    const consoleErrors = await browser.getConsoleErrors();
    const pageErrors = await browser.getPageErrors();

    if (consoleErrors.length > 0) {
      // 4. 自动修复
      await this.agent.fixErrors(consoleErrors);
    }

    return { passed: consoleErrors.length === 0 };
  }
}

// 优势对比
const COMPARISON = {
  "Computer Use": {
    speed: "1x",
    cost: "1x",
    reliability: "中"
  },
  "Replit App Testing": {
    speed: "3x faster",
    cost: "10x more cost-effective",
    reliability: "高"
  }
};
```

---

## D.5 四产品 Agent 对比总结

### Agent 架构模式

| 产品 | 架构模式 | Agent 数量 | 自主级别 |
|------|---------|------------|----------|
| **Bolt.new** | 单体 Agent | 1 | 低-中 |
| **v0** | Agentic | 1+ | 中 |
| **Lovable** | 单体 Agent | 1 | 中 |
| **Replit Agent 3** | 多 Agent | 4+ | 高 (200分钟) |

### 工具调用方式

| 产品 | 工具定义 | 调用方式 | 外部集成 |
|------|----------|----------|----------|
| **Bolt.new** | 隐式 (XML) | 文本生成 | 无 |
| **v0** | 显式 | Tool Calling | API/数据库 |
| **Lovable** | 显式 | 函数调用 | Supabase/Stripe |
| **Replit** | 混合 | DSL + Function | 多平台 |

### 执行环境

| 产品 | 环境 | 隔离级别 | 特点 |
|------|------|----------|------|
| **Bolt.new** | WebContainer | 强 (浏览器沙箱) | 安全但有限 |
| **v0** | Vercel Cloud | 中 | 依赖云端 |
| **Lovable** | 云端 | 中 | Supabase 生态 |
| **Replit** | 云端 VM | 强 (容器) | 完整 Linux |

### 独特能力

| 产品 | 独特能力 | 技术实现 |
|------|----------|----------|
| **Bolt.new** | 极速原型 | WebContainer + 简单架构 |
| **v0** | 多角色适用 | Designer/PM/工程师模板 |
| **Lovable** | 全栈集成 | Supabase 原生 |
| **Replit** | 自动测试 | 真实浏览器 + 200分钟 autonomy |

### 用户定位

| 产品 | 主要用户 | 技术要求 |
|------|----------|----------|
| **Bolt.new** | 开发者 | 中 |
| **v0** | 所有人 (Designer/PM/创始人) | 低 |
| **Lovable** | 创业者/产品经理 | 低-中 |
| **Replit** | 学习者/开发者 | 中 |

---

## D.6 对 Zaoya 的启示

### 推荐架构选择

基于分析，Zaoya 可以采用 **简化的 Agentic 架构**：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Zaoya 推荐 Agent 架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    用户输入层                            │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│   │  │ 模板选择    │→ │ 自然语言    │→ │ 截图/草图   │      │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 Interview Agent (可选)                   │   │
│   │  - 自适应提问                                            │   │
│   │  - 需求澄清                                              │   │
│   │  - 收集详细信息                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   主 Agent (Claude)                      │   │
│   │  ┌─────────────────────────────────────────────────┐    │   │
│   │  │ 1. 任务规划 → 代码生成 → 验证 → 修复            │    │   │
│   │  └─────────────────────────────────────────────────┘    │   │
│   │                                                          │   │
│   │  工具:                                                   │   │
│   │  - file_writer: 写入文件                                 │   │
│   │  - code_validator: 验证代码                              │   │
│   │  - preview_renderer: 渲染预览                            │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   输出层                                 │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│   │  │ Live Preview│→ │ 代码查看    │→ │ 部署        │      │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 关键技术决策

| 决策点 | 推荐方案 | 理由 |
|--------|----------|------|
| **工具调用** | 隐式 (XML/JSON) | 简单可靠，参考 Bolt |
| **执行环境** | 云端 Docker | 安全，支持全栈 |
| **任务规划** | 简单分解 | 不需要复杂多 Agent |
| **测试** | 基础验证 | 避免过度设计 |
| **上下文管理** | 三层记忆 | 参考 Claude Code |

### 差异化机会

| 竞品缺失 | Zaoya 机会 |
|----------|------------|
| **自适应访谈** | Interview Agent 收集需求 |
| **移动端优化** | 专注移动端落地页 |
| **中文体验** | 原生中文提示词和 UI |
| **模板引导** | 4 大类模板系统 |
| **轻量级** | 快速迭代，无需复杂架构 |

### 不建议复制的内容

| 产品 | 不建议复制的原因 |
|------|------------------|
| **Replit 多 Agent** | 过度设计，Zaoya 场景不需要 |
| **Bolt WebContainer** | 需要商业授权 |
| **v0 全功能** | 复杂度高，资源消耗大 |
| **Lovable Supabase** | 过度依赖单一服务 |

**特点**：
- 单一主 Agent 处理所有任务
- 通过提示词引导生成结构化输出 (XML 格式)
- 工具调用通过解析标签实现

**工作流程**：
```
用户输入 → 上下文注入 → 主 Agent 决策
                              ↓
                        工具调用 (XML 标签)
                              ↓
                        执行结果 → 评估 → 继续/完成
```

### A.2 多 Agent 协作模式 (Claude Code, Cline)

**特点**：
- 主 Agent 可启动子 Agent 处理特定任务
- 子 Agent 拥有独立工具集
- 适合复杂搜索和探索任务

**工作流程**：
```
用户输入 → 主 Agent 分析
                    ├── 简单任务 → 直接调用工具
                    └── 复杂搜索 → 启动子 Agent
                                        ↓
                              子 Agent 使用专项工具
                                        ↓
                              结果返回主 Agent
                                        ↓
                              继续处理或完成
```

### A.3 Human-in-the-loop 模式 (Cline)

**特点**：
- 每次操作需要用户审核
- 提供 diff view 预览
- 支持回滚和版本对比

**工作流程**：
```
Agent 决策 → 生成变更 → 用户审核
                          ├── 批准 → 执行
                          ├── 修改 → 重新生成
                          └── 拒绝 → 取消
```

---

## B. 工具系统设计模式

### B.1 内置工具 (固定工具集)

**代表**: Bolt.new

```typescript
// Bolt.new 工具定义
const AVAILABLE_SHELL_COMMANDS = [
  'cat', 'chmod', 'cp', 'echo', 'hostname', 'kill', 'ln',
  'ls', 'mkdir', 'mv', 'ps', 'pwd', 'rm', 'rmdir',
  'curl', 'env', 'head', 'tail', 'touch', 'node', 'npm', 'npx'
];

const FILE_OPERATIONS = ['read', 'write', 'edit', 'glob', 'grep'];
```

**优点**：
- 简单可靠
- 易于测试和调试
- 性能可预测

**缺点**：
- 扩展性差
- 需要版本更新才能增加新工具

### B.2 协议扩展工具 (MCP 协议)

**代表**: Cline, Claude Code

```typescript
// MCP 工具定义示例
interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
  };
}

interface MCPConnection {
  tools: MCPTool[];
  connect(): Promise<void>;
  disconnect(): Promise<void>;
}

// 动态工具创建
async function createCustomTool(spec: ToolSpec): Promise<MCPTool> {
  const serverCode = generateMCPServer(spec);
  await writeFile(`./mcp-servers/${spec.name}.ts`, serverCode);
  return {
    name: spec.name,
    description: spec.description,
    inputSchema: spec.parameters
  };
}
```

**优点**：
- 高度可扩展
- 社区共享工具
- 动态加载

**缺点**：
- 复杂性高
- 安全风险

### B.3 命令行工具 (Codex CLI)

**代表**: OpenAI Codex CLI

```bash
# Codex CLI 命令
/approvals    # 设置权限模式
/model        # 切换模型
/status       # 查看状态
/mcp          # 管理 MCP 工具
/init         # 初始化项目
/compact      # 压缩历史
```

**优点**：
- 开发者熟悉
- 易于集成
- 脚本化支持

**缺点**：
- 需要终端环境
- 学习曲线

---

## C. 上下文管理策略

### C.1 三层记忆系统 (Claude Code)

| 层级 | 载体 | 触发条件 | 数据结构 |
|------|------|----------|----------|
| 短期 | Array + Map | 实时 | 当前会话消息队列 |
| 中期 | 压缩摘要 | Token ≥ 92% | 结构化摘要 (8类) |
| 长期 | Markdown | 跨会话 | 用户偏好、项目配置 |

```typescript
// 上下文管理示例
class ContextManager {
  private shortTerm: Message[] = [];
  private midTerm: Summary = {};
  private longTerm: UserPreferences;

  async addMessage(msg: Message) {
    this.shortTerm.push(msg);
    if (this.getTokenCount() > 0.92 * MAX_TOKENS) {
      await this.compressToMidTerm();
    }
  }

  private async compressToMidTerm() {
    this.midTerm = {
      filesModified: extractFiles(this.shortTerm),
      patternsFound: identifyPatterns(this.shortTerm),
      currentFocus: determineFocus(this.shortTerm),
      decisions: extractDecisions(this.shortTerm)
    };
    this.shortTerm = [];
  }

  async getContext(): Promise<LLMContext> {
    return {
      system: SYSTEM_PROMPT,
      longTerm: this.longTerm,
      midTerm: this.midTerm,
      shortTerm: this.shortTerm
    };
  }
}
```

### C.2 AGENTS.md 模式 (Codex CLI)

```markdown
# AGENTS.md - 项目配置

## 项目概述
这是一个 Next.js 电商应用。

## 技术栈
- Next.js 14
- TypeScript
- Tailwind CSS
- Supabase

## 代码规范
- 使用 2 空格缩进
- 组件文件以 .tsx 结尾
- API 路由放在 app/api/ 目录

## 常用命令
- npm run dev
- npm run build
```

---

## D. 安全与权限控制

### D.1 权限级别

| 级别 | 描述 | 适用场景 |
|------|------|----------|
| Auto | 自动执行，无需确认 | 快速迭代开发 |
| Read Only | 只读，禁止文件修改 | 代码审查 |
| Full Access | 完全访问权限 | 自动化任务 |

### D.2 多层安全模型 (Claude Code)

```
┌─────────────────────────────────────────────────────────────┐
│                    安全层级                                   │
├─────────────────────────────────────────────────────────────┤
│  1. 授权层: 危险操作需要用户确认                               │
│     - 文件删除、修改                                        │
│     - 命令执行                                              │
│     - 网络请求                                              │
├─────────────────────────────────────────────────────────────┤
│  2. Hook 层: 插件拦截可疑操作                                 │
│     - 敏感路径检测                                          │
│     - 危险命令过滤                                          │
├─────────────────────────────────────────────────────────────┤
│  3. 沙箱层: 受控的执行环境                                    │
│     - WebContainer 浏览器沙箱                               │
│     - Docker 容器隔离                                       │
├─────────────────────────────────────────────────────────────┤
│  4. 审计层: 操作日志和回滚                                    │
│     - 操作记录                                              │
│     - 版本快照                                              │
│     - 回滚能力                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## E. 流式输出解析

### E.1 XML 标签解析 (Bolt.new)

```typescript
// StreamingMessageParser 实现
class StreamingMessageParser {
  private buffer: string = '';
  private currentAction: Action | null = null;
  private actions: Action[] = [];

  parse(chunk: string): void {
    this.buffer += chunk;

    // 提取完整的标签
    while (true) {
      const startTag = this.buffer.match(/<boltAction[^>]*>/);
      if (!startTag) break;

      const endTag = this.buffer.match(/<\/boltAction>/);
      if (!endTag) break;

      const actionContent = this.buffer.substring(
        startTag.index!,
        endTag.index! + endTag[0].length
      );

      const action = this.parseAction(actionContent);
      this.actions.push(action);

      // 移除已解析内容
      this.buffer = this.buffer.substring(endTag.index! + endTag[0].length);

      // 触发回调
      this.onActionComplete?.(action);
    }
  }

  private parseAction(xml: string): Action {
    const typeMatch = xml.match(/type="([^"]+)"/);
    const pathMatch = xml.match(/filePath="([^"]+)"/);

    return {
      type: typeMatch?.[1] as ActionType,
      filePath: pathMatch?.[1],
      content: xml.replace(/<\/?boltAction[^>]*>/g, '').trim()
    };
  }
}
```

### E.2 SSE 流式响应

```typescript
// 使用 Vercel AI SDK
import { streamText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = await streamText({
    model: anthropic('claude-sonnet-4-20250514'),
    messages,
    system: getSystemPrompt(),
    tools: {
      file_writer: {
        parameters: z.object({
          path: z.string(),
          content: z.string()
        })
      },
      shell_runner: {
        parameters: z.object({
          command: z.string()
        })
      }
    }
  });

  return result.toDataStreamResponse();
}
```

---

## F. 推荐架构参考

### F.1 Zaoya 推荐 Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Zaoya Agent 架构                          │
├─────────────────────────────────────────────────────────────┤
│  前端层 (React + Vite)                                       │
│  ├── ChatPanel (对话界面)                                    │
│  ├── PreviewPanel (iframe 预览)                              │
│  ├── TemplateSelector (模板选择)                             │
│  └── QuickActionChips (快捷操作)                             │
├─────────────────────────────────────────────────────────────┤
│  Agent 层                                                    │
│  ├── 主 Agent (需求理解 → 任务分解)                          │
│  │   ├── Interview Agent (自适应采访)                        │
│  │   ├── Generation Agent (代码生成)                         │
│  │   └── Refinement Agent (优化迭代)                         │
│  ├── 工具系统 (MCP 协议)                                     │
│  │   ├── file_tool (文件读写)                                │
│  │   ├── code_validator (代码验证)                           │
│  │   └── browser_tool (浏览器测试)                           │
│  └── 上下文管理 (三层记忆)                                    │
├─────────────────────────────────────────────────────────────┤
│  执行层                                                      │
│  ├── 沙箱执行 (Docker/云端)                                  │
│  ├── 预览服务 (iframe + HTTPS)                               │
│  └── 部署服务 (Netlify/Vercel)                               │
├─────────────────────────────────────────────────────────────┤
│  AI 层                                                       │
│  ├── 主模型: Claude Sonnet 4 (代码生成)                     │
│  └── 嵌入模型: 多模态理解 (截图 → 代码)                       │
└─────────────────────────────────────────────────────────────┘
```

### F.2 核心组件实现建议

| 组件 | 推荐方案 | 参考来源 |
|------|----------|----------|
| AI SDK | Vercel AI SDK | Bolt.new, v0 |
| 流式响应 | Server-Sent Events | Bolt.new api.chat.ts |
| 提示词管理 | 模块化提示词系统 | Claude Code |
| 上下文压缩 | 三层记忆系统 | Claude Code |
| 工具扩展 | MCP 协议 | Cline, Claude Code |
| 代码验证 | 沙箱执行 + 测试 | Cline |
| 浏览器自动化 | Playwright | Cline Computer Use |
| 部署 | Vercel/Netlify | v0, Bolt.new |

---

## G. 关键区别与差异化机会

| 竞品 | Agent 模式 | 工具系统 | 差异化点 | Zaoya 机会 |
|------|-----------|----------|----------|------------|
| **Bolt.new** | 单 Agent | 固定 | WebContainer | 自适应访谈 |
| **v0** | 单 Agent | 固定 | UI 生成质量 | 移动端优化 |
| **Claude Code** | 多 Agent | MCP | 终端集成 | 模板引导 |
| **Cline** | 多 Agent | MCP | VS Code 集成 | 非技术用户 |
| **Codex** | 云端 Agent | 插件 | 云端沙箱 | 轻量级 |
| **Lovable** | 单 Agent | 固定 | Supabase 集成 | 快速迭代 |
| **Replit** | 单 Agent | 固定 | 完整 IDE | 简化体验 |

---

## H. 实施建议

### H.1 第一阶段：基础架构

1. **实现 Vercel AI SDK 流式响应**
   - 参考 Bolt.new `api.chat.ts`
   - 实现 `streamText` 函数
   - 添加自动继续生成机制

2. **建立提示词系统**
   - 创建 `getSystemPrompt()` 函数
   - 实现模板化提示词
   - 添加上下文注入

3. **实现基础工具**
   - 文件读写工具
   - 代码验证工具
   - 预览渲染工具

### H.2 第二阶段：Agent 增强

1. **多 Agent 协作**
   - 实现主 Agent 协调器
   - 添加子 Agent 机制
   - 建立任务分发策略

2. **上下文管理**
   - 实现三层记忆系统
   - 添加上下文压缩
   - 建立长期记忆持久化

3. **工具扩展 (MCP)**
   - 实现 MCP 协议支持
   - 添加社区工具集成
   - 建立工具市场机制

### H.3 第三阶段：差异化功能

1. **自适应访谈**
   - 实现 Interview Agent
   - 建立问题模板系统
   - 添加意图识别

2. **质量保障**
   - 实现自动测试
   - 添加代码审查
   - 建立性能基准

3. **用户体验**
   - 实现 Human-in-the-loop 审核
   - 添加版本对比
   - 建立操作回滚
