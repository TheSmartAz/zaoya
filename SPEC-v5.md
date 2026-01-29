# Zaoya (造鸭) - v5 Specification

> **"Production-ready preview, version control, and A/B testing foundation."**

v5 focuses on making preview reliable, adding version control with manual rollback, improving the chat UX with code in dedicated tabs, and laying the foundation for A/B testing through branching.

---

## Vision

**North Star**: "What you see is what you publish, with full traceability and instant rollback."

v5 addresses key issues from v4:

- **Preview = Publish可信** - Publish simulation mode to catch CSP/resource issues early
- **Failure Recovery** - Single-page retry + enhanced ValidationCard + page-level rollback
- **Code Experience** - No code in chat, but full traceability via Code Tab + Version history
- **Production Polish** - Landing page examples, one-click generation, SEO basics
- **Version Control** - Branching, manual rollback, and version jumping

---

## What Changed from v4

| v4 Feature | v5 Change | Rationale |
|------------|-----------|-----------|
| srcdoc iframe preview | **Publish Simulation Mode** | Preview now uses `/p-sim/{id}/{slug}` with real CSP |
| Static thumbnails | **Queued + Fallback thumbnails** | Queue-based generation with separate OG Image |
| Chat shows code blocks | **Code Tab only** | Clean chat, code in dedicated panel |
| Task items scroll away | **TaskBoardCard (sticky)** | Cumulative task state at fixed position |
| ValidationCard (basic) | **Enhanced ValidationCard** | Path/line info + one-click fix + page rollback |
| No version history | **Version Nodes + Branching** | Each message = version point, can branch |
| No rollback | **Manual page-level rollback** | User chooses when and what to rollback |
| Static landing page | **Examples Gallery** | One-click demo projects |
| No SEO | **Basic SEO tags + OG Image** | Shareable pages look good on social |

---

## Part A: High-Priority Issues Resolution

### A.1 CSP vs Tailwind CDN Conflict

**Problem**: Page templates may include `https://cdn.tailwindcss.com` (external script), but published CSP uses `script-src 'self'`. Published pages will be blocked.

**Solution**: Inline Tailwind CSS + Runtime Helpers

- AI prompt: "Use Tailwind classes but do NOT include CDN links"
- Build pipeline: Extract critical CSS, inline it
- Runtime helpers: Move from external to inlined script

### A.2 Zaoya.navigate Semantic

**Definition**:
- **Preview Mode**: Within editor, navigation uses `srcdoc` or `/p-sim` with page switching via query param or hash
- **Publish Mode**: Real multi-page routing with real URLs (`/p/{public_id}/{page_slug}`)

```javascript
// Zaoya Runtime API
Zaoya.navigate(path)      // Navigate to another page
Zaoya.switchPage(pageId)  // For preview mode
Zaoya.submitForm(formData) // Submit form data
```

### A.3 Runtime Capability Boundary

| Category | Allowed | Prohibited |
|----------|---------|------------|
| **User Generated JS** | Zaoya.* calls | fetch, XHR, eval, localStorage, sessionStorage, indexedDB |
| **Zaoya Runtime** | Controlled requests to backend API | Arbitrary external requests |
| **Inline Handlers** | Event handlers with Zaoya.* | Inline scripts with arbitrary code |

### A.4 Thumbnail Generation Execution Model

| Component | Implementation |
|-----------|----------------|
| **Where** | Server-side (worker queue) + Client-side fallback |
| **Engine** | Playwright headless browser |
| **Timeout** | 30s per page |
| **Concurrency** | 2 workers max |
| **Retry** | 3 attempts with exponential backoff |
| **Fallback** | Placeholder with page title + theme color |

### A.5 Preview vs Publish Template Separation

| Template | Purpose | CSP |
|----------|---------|-----|
| **Preview Template** | Editor iframe, `/p-sim` | Loose (allows dev tools) |
| **Publish Template** | Production, `/p/{id}` | Strict (CSP headers) |

### A.6 Code Traceability Foundation

Each version stores:
- File snapshots with checksums
- Unified diffs using `diff-match-patch` library
- Ready for future Diff Viewer/rollback

### A.7 Code Access Control

**Access Level**: Code Tab is only visible to the project creator.

- File tree and content are restricted to owner only
- Share links show published page only, not source code
- This protects commercial/confidential projects

### A.8 Version Quota by Tier

| Tier | Version Limit | Snapshot Storage |
|------|---------------|------------------|
| Free | 5 versions | Mixed (full + diff) |
| Paid | 50 versions | Mixed (full + diff) |

**Notes**:
- Failed versions are stored separately (do not count toward quota)
- Branch versions count toward the branch's quota (each branch has independent quota)
- Versions beyond limit are deleted (no archive for free tier)

---

## Part B: Publish Simulation Mode

### B.1 Overview

Purpose: Make preview equivalent to publish, catching CSP and resource issues early.

**Core Idea**: Instead of `srcdoc` iframe, use `/p-sim/{project_id}/{page_slug}` - a real route with near-production HTML and CSP.

### B.2 New Endpoint

```
GET /p-sim/{project_id}/{page_slug}
- Returns HTML with real CSP headers
- Content from draft or snapshot
- Served from same origin as production
- Difference from real publish: allows iframe embedding
```

### B.3 Simulation Report

```
GET /p-sim-report/{project_id}
- CSP violations list (blocked URI, directive, excerpt)
- Resource loading issues (404, blocked, timeout)
- Pass/fail status
```

### B.4 Preview Toolbar Enhancement

- Toggle between "Preview" and "Publish Simulation" mode
- Simulation mode shows warning badge
- Report panel displays CSP/resource issues

### B.5 Acceptance Criteria

- [ ] Simulation mode can reproduce CSP issues (blocked external scripts/styles)
- [ ] Resource loading errors are reported with clear reasons
- [ ] Visual appearance matches production closely
- [ ] Forces resolution of Tailwind CDN conflict

---

## Part C: Thumbnail Generation - Queued + Fallback

### C.1 Queue Design

```
thumbnail_jobs table:
- id, project_id, page_id, type (thumbnail | og_image)
- status: queued / running / done / failed
- attempts, max_attempts (default 3)
- next_run_at (for exponential backoff)
- last_error, image_url
```

### C.2 Thumbnail vs OG Image

**Thumbnail**: Small image for dashboard/project list
- Size: 300x600 (mobile aspect ratio)
- Used in: Project list, editor thumbnail

**OG Image**: Large image for social sharing
- Size: 1200x630 (Open Graph standard)
- Used in: Twitter/X, Facebook, LinkedIn sharing
- Generated on-demand (not blocking publish)
- Higher quality rendering

### C.3 Worker Logic

**Main**: Headless screenshot via Playwright
**Fallback 1**: Client-side generation (html2canvas)
**Fallback 2**: SVG placeholder with title + theme color

Worker constraints:
- Max 2 concurrent jobs per type
- 30s timeout per page
- Exponential backoff on failure
- Deduplication (new job for same page cancels old)

### C.4 Frontend UI

Thumbnail states:
- **Pending**: Shows clock icon
- **Generating**: Shows spinner
- **Done**: Shows thumbnail image
- **Failed**: Shows error message + one-click retry button

OG Image states:
- **Pending/Generating**: Uses placeholder
- **Done**: Shows OG image
- **Failed**: Keeps placeholder, user can retry

### C.5 Acceptance Criteria

- [ ] Thumbnail failure does not block publish
- [ ] UI clearly shows: generating / failed / success
- [ ] Failed thumbnails can be retried with one click
- [ ] Multiple-page projects don't overwhelm server
- [ ] OG Image is separate from thumbnail
- [ ] OG Image generated on-demand

---

## Part D: Project Homepage - Examples + One-Click Generate

### D.1 Landing Page Structure

```
Hero Section:
- Value proposition: "Describe it. See it. Share it."
- CTA: "开始创建"

Examples Gallery:
- Personal Link-in-Bio
- Event RSVP
- Product Landing
- Contact Form
```

### D.2 Example Data Model

```
ExampleProject:
- id, title, template, description
- thumbnailUrl
- seedPrompt (AI prompt to generate)
- defaultPages: [{name, path}]
- defaultDesignSystem: {style, colors, fonts}
```

### D.3 One-Click Generation Flow

1. User clicks example card
2. System creates project with example data
3. Optionally auto-start build (skip interview)
4. User lands in editor with pre-generated content

### D.4 Acceptance Criteria

- [ ] First-time users can get a previewable page with one click
- [ ] Example projects can be published with working SEO/thumbnails
- [ ] One-click skips unnecessary interview steps

---

## Part E: Enhanced ValidationCard + Single-Page Retry

### E.1 Enhanced ValidationError Structure

```
ValidationError:
- ruleId (e.g., "csp-no-external-script")
- ruleCategory: csp / js-security / html-whitelist / resource / runtime
- path (file path)
- line (line number, if applicable)
- excerpt (code snippet)
- message (human-readable)
- suggestedFix (one-sentence fix)
```

### E.2 ValidationCard UI

```
Page validation failure card shows:
- Each error with category, path, line, message
- Code excerpt for context
- Suggested fix
- [查看代码] button → jumps to Code Tab
- [修复此页面] button → creates fix task
- [重试此页面] button → retries only failed page
- [页面回滚] button → opens rollback dialog
```

### E.3 Single-Page Retry

- Re-executes: page_generate → validate → secure → save → thumbnail
- Skips: unaffected pages, shared state
- No full rebuild required

### E.4 Acceptance Criteria

- [ ] Failed page retry doesn't trigger full build
- [ ] ValidationCard shows path + line info
- [ ] Clicking error jumps to Code Tab
- [ ] Clicking fix creates iteration task and retries
- [ ] Clicking rollback opens Version History for page selection
- [ ] Page-level rollback preserves other pages

---

## Part F: Basic SEO for Published Pages

### F.1 SEO Tags

```html
<title>{pageTitle} | {projectName}</title>
<meta name="description" content="{pageDescription}">

<!-- Canonical -->
<link rel="canonical" href="https://pages.zaoya.app/p/{public_id}/{page_slug}">

<!-- Open Graph -->
<meta property="og:title" content="{pageTitle}">
<meta property="og:description" content="{pageDescription}">
<meta property="og:image" content="{thumbnailUrl}">
<meta property="og:url" content="...">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{pageTitle}">
<meta name="twitter:description" content="{pageDescription}">
<meta name="twitter:image" content="{thumbnailUrl}">

<!-- Favicon -->
<link rel="icon" href="{faviconUrl}">

<!-- Robots -->
<meta name="robots" content="index, follow">
```

### F.2 Data Sources

| Tag | Source |
|-----|--------|
| title | Page title or ProductDoc.project_name |
| description | ProductDoc.overview or page.summary |
| og:image | Page OG Image (separate from thumbnail) |
| canonical | Generated from public_id + page_slug |
| favicon | Project settings |

### F.3 OG Image Generation

- **Trigger**: On-demand (first social share access)
- **Size**: 1200x630 (Open Graph standard)
- **Quality**: Higher quality than thumbnail
- **Fallback**: SVG placeholder with page title if generation fails
- **Cache**: Generated image is cached after first creation

### F.4 Acceptance Criteria

- [ ] Shared links show title/description/thumbnail
- [ ] Multi-page canonical URLs are correct
- [ ] OG Image is generated on first social share
- [ ] Social platforms show correct preview (title + OG Image)

---

## Part G: PreviewPanel - Code Tab

### G.1 Tab Structure

```
PreviewPanel tabs: [Preview] [ProductDoc] [Code]

Code Tab layout:
- Left: File tree (pages/, components/, assets/)
- Right: Code viewer (read-only, syntax highlight, line numbers, find)
```

### G.2 File Operations

```
GET /api/projects/{id}/files?scope=draft|snapshot|published
- Returns file tree structure

GET /api/projects/{id}/files/content?path=...&scope=...
- Returns file content
- Security: prevents directory traversal
```

### G.3 Code Viewer Features

- Syntax highlighting (Monaco/CodeMirror)
- Line numbers
- Find with highlight
- Copy button
- Click error → jump to file/line

### G.4 Integration with ValidationCard

When validation error has path + line:
- Switch to Code Tab
- Open file and scroll to line
- Highlight error snippet

### G.5 Acceptance Criteria

- [ ] Can view project file list
- [ ] Clicking file opens content (stable)
- [ ] Syntax highlight and line numbers work
- [ ] Search with highlight works
- [ ] ValidationCard can jump to specific file/line

---

## Part H: Chat UX Improvements

### H.1 Cards Flow Naturally (Not Fixed)

All cards are message items, flowing naturally in chat:
- BuildPlanCard
- PageCard
- ValidationCard
- VersionSummaryCard
- TaskBoardCard

### H.2 Auto-Scroll Behavior

- Only auto-scroll when user is near bottom (within 100px)
- Show "跳到最新" button when user is far from bottom
- No scrolling while user is reading history

### H.3 TaskBoardCard - Cumulative Task Display

One card per build session, showing:
- All tasks in fixed order
- Status icon: spinner / check / alert / clock
- Line changes: +X / -Y
- Retry button for failed tasks

### H.4 No Code in Chat

Chat messages after code generation:
```
"已更新首页 Hero 区块：
- 新增标题动画效果
- 优化 CTA 按钮视觉层级
- 调整移动端响应式布局

3 个文件，+48 -12 行"

[查看代码] [查看预览]
```

### H.5 Chat History - Virtual Scrolling

**Strategy**: Virtual scrolling with dynamic loading

- **Initial Load**: Shows last 10 user messages + corresponding AI responses
- **Scrolling Up**: Dynamically loads older messages (pagination)
- **Performance**: Virtual scroll DOM nodes for smooth experience
- **Jump to New**: "跳到最新" button when user is far from bottom

### H.6 Acceptance Criteria

- [ ] Cards flow naturally, not fixed at bottom
- [ ] Auto-scroll only when near bottom
- [ ] TaskBoardCard shows all tasks in fixed positions
- [ ] No source code shown in chat
- [ ] Chat history loads older messages on scroll up
- [ ] Smooth scrolling with 10+ messages visible

---

## Part I: Version System

### I.1 Version Data Model

```
Version:
- id, project_id
- parent_version_id (for branching)
- branch_id, branch_label (main / a / b)
- created_at
- trigger_message_id (which user message)
- snapshot_id (point-in-time snapshot)
- change_summary:
  - files_changed, lines_added, lines_deleted
  - tasks_completed, description
- validation_status: passed / failed / pending
- is_pinned (user marked as important)
```

### I.2 Snapshot Storage Strategy (Mixed)

**Storage Model**: Hybrid of full snapshots and diffs

- **Full Snapshots**: Last 3 versions + user-pinned versions
- **Diff Storage**: All other versions (apply diff to nearest full snapshot)
- **Library**: `diff-match-patch` for diff generation and application
- **Recovery**: Full snapshot + apply N diffs = any version

**Pinned Versions**:
- User can manually pin any version as "important"
- Max 3 pinned versions allowed
- Pinned versions always store full snapshot
- Use case: Milestone versions, published versions, key checkpoints

### I.3 Version Node in Chat

After each user message/AI iteration:
- Version card appears in chat
- Shows: description, files changed, line counts
- Actions: [查看预览] [查看代码]
- All versions persisted for history

### I.4 Version History Panel

```
Version History:
v3 ────● 2026-01-28 14:30 [预览] [代码] [📌]
     │  新增联系表单 (3 文件, +127 -23)

v2 ────● 2026-01-28 14:15 [预览] [代码]
     │  优化移动端布局
           │
           └── Branch B ───● 2026-01-28 14:20 [预览] [代码]
                  │  蓝色主题变体 (2 文件, +34 -12)

v1 ────● 2026-01-28 14:00 [预览] [代码]
     │  初始版本 (1 文件, +156)
```

**Actions per version**:
- [预览] - View this version's preview
- [代码] - View files at this version
- [📌] - Pin (mark as important)
- [...] - More actions: 页面回滚, 创建分支, 删除

### I.5 Page-Level Rollback

Users can rollback individual pages to previous versions:

**Entry Point**: Version History Panel > [...] > 页面回滚

**UI Flow**:
1. User clicks "页面回滚" on a version
2. Panel shows all pages with their versions at this point
3. User selects page(s) to rollback
4. Confirm rollback (shows what will change)
5. Draft updated, new version created

**Page Version Identification**:
- Each page has independent version: `index.html v5`
- Rollback shows: "Rollback index.html from v7 to v5"
- Multiple pages can be selected for batch rollback

### I.6 Version API

```
GET /api/projects/{id}/versions?branch_id=...
GET /api/projects/{id}/versions/{version_id}
POST /api/projects/{id}/versions/{version_id}/restore
POST /api/projects/{id}/versions/{version_id}/branch
POST /api/projects/{id}/versions/{version_id}/pin
DELETE /api/projects/{id}/versions/{version_id}/pin
```

### I.7 Acceptance Criteria

- [ ] Each user message creates a version point
- [ ] Can navigate to any version's preview
- [ ] Version summary shows files changed and line counts
- [ ] Branching creates separate version history
- [ ] Can restore from any previous version
- [ ] Can pin up to 3 versions (full snapshot preserved)
- [ ] Page-level rollback works via Version History Panel
- [ ] Failed versions stored separately (not in quota)

---

## Part J: Auto-Rollback

> **STATUS**: REMOVED from v5 scope
>
> Manual page-level rollback is implemented instead (see Part I.5).

**Rationale for Removal**:
- Auto-rollback can cause confusion when multiple users/devices edit same project
- Manual rollback gives users more control over when and what to rollback
- Single-page retry provides sufficient recovery for most failure cases
- Can be re-evaluated for future versions based on user feedback

**Alternative Implemented**:
- Single-page retry (Part E.3)
- Page-level rollback (Part I.5)
- Failed versions preserved for debugging (stored separately)

---

## Part K: Branching & A/B Testing Foundation

### K.1 Branch Data Model

```
Branch:
- id, project_id, name (main / a / b)
- label (display name: Control / Variant B)
- parent_branch_id
- created_at
- created_from_version_id
- is_default
```

### K.2 Branch Quota

| Tier | Max Branches per Project |
|------|--------------------------|
| Free | 3 |
| Paid | 3 (configurable) |

**Notes**:
- Each branch has independent version quota
- "main" branch is always included in the 3
- Cannot create new branch if quota reached (delete first)

### K.3 Create Branch

From any version card:
- Click "创建分支"
- Enter branch name/label
- New branch created from that version
- Continue development independently

### K.4 Branch Isolation

- Each branch has separate preview URL
- Each branch has separate share link
- Each branch has separate published snapshot
- Branch switching in editor loads branch-specific state

### K.5 Light A/B Testing (Read-Only View)

Each branch gets:
- Separate preview URL
- Separate share link with variant param
- Separate published snapshot

Analytics tracking includes variant ID:
```javascript
Zaoya.track('cta_click', { variant: 'b' })
```

### K.6 A/B Share Links

| Branch | Share URL |
|--------|-----------|
| Main (Control) | `https://pages.zaoya.app/p/{public_id}` |
| Variant A | `https://pages.zaoya.app/p/{public_id}?variant=a` |
| Variant B | `https://pages.zaoya.app/p/{public_id}?variant=b` |

### K.7 Merge Strategy (Deferred)

> **STATUS**: Merge functionality deferred to future version
>
> v5 supports branch creation and independent development. Merging branches back to main is not implemented.

**Workaround for v5**:
- Use branch as reference/snapshot
- Manually apply changes by describing them in chat
- "Use variant B as reference" for AI to regenerate in main

### K.8 Acceptance Criteria

- [ ] Can branch from any version
- [ ] Branch quota enforced (3 per project)
- [ ] Each branch has separate preview and share link
- [ ] Analytics events can be tagged with variant ID
- [ ] Branches can be developed independently
- [ ] Branch switching works correctly

---

## Part L: Task Line Count Display

### L.1 In TaskBoardCard

Each task row shows:
- Status icon
- Task title
- +X / -Y (line changes)
- Retry button for failed tasks

### L.2 Backend Calculation

When task completes:
- Parse unified diff
- Count added lines (lines starting with +)
- Count deleted lines (lines starting with -)
- Exclude diff headers (+++ / ---)

### L.3 SSE Event

```json
{
  "event": "task_done",
  "data": {
    "task_id": "page-home-html",
    "title": "Home 页面 HTML",
    "status": "done",
    "lines_added": 127,
    "lines_deleted": 45
  }
}
```

### L.4 Acceptance Criteria

- [ ] Each completed task shows line change count
- [ ] Counts are +X / -Y format
- [ ] Tasks with no code changes show 0 lines
- [ ] Counts are reasonably accurate

---

## Part M: Implementation Roadmap

### Priority Order

1. **Week 1: Foundation**
   - Code Tab implementation
   - CSP vs Tailwind CDN resolution
   - Preview/Publish template separation
   - Code access control (owner only)

2. **Week 2: Version System**
   - Version data model
   - Version summary in chat
   - Version history panel
   - Mixed snapshot storage (full + diff)
   - Page-level rollback

3. **Week 3: Reliability**
   - Publish simulation mode
   - Enhanced ValidationCard
   - Single-page retry
   - Failed version storage (separate from quota)

4. **Week 4: Thumbnails + SEO**
   - Thumbnail queue worker
   - Fallback strategies
   - Separate OG Image generation
   - Basic SEO tags

5. **Week 5: Polish**
   - Examples gallery on homepage
   - One-click generation flow
   - Task line count display
   - Chat UX improvements
   - Virtual scrolling for chat history
   - Branch creation and isolation

6. **Week 6: Completion**
   - Version pinning (max 3)
   - Branch quota enforcement
   - Testing and bug fixes
   - Documentation

---

## Part N: Success Metrics (v5)

| Metric | v4 | v5 Target |
|--------|----|-----------|
| Preview-Publish consistency | N/A | 100% match |
| Single-page retry rate | N/A | < 5% need full rebuild |
| Code visibility in chat | Yes | No (all in Code Tab) |
| Version navigation | N/A | > 50% users view previous |
| Auto-rollback triggers | N/A | Removed (manual rollback) |
| First-page time | N/A | < 30 seconds |
| Example usage rate | N/A | > 30% of new users |
| Page-level rollback usage | N/A | Measured via analytics |
| Branch creation rate | N/A | > 10% of power users |

---

## Part O: Implementation Decisions (Q&A Outcomes)

This section documents key technical decisions made during the specification interview process.

### O.1 CSP 违规检测机制

**决策**: 采用 `/p-sim` 路由（真实 HTTP 头级 CSP）

**实现细节**:
- 使用真实 FastAPI 路由 `/p-sim/{project_id}/{page_slug}` 返回带 CSP HTTP 头的 HTML
- iframe src 指向该路由以完全复现生产环境
- 通过 CSP 的 `report-uri` 指令捕获违规报告到后端 API
- 后端接收并解析 CSP 报告，实时展示在预览面板

**理由**: 完全复现 HTTP 头级 CSP（而非仅 meta 标签），可捕获 iframe embedding 相关问题，与生产环境一致性最高。

### O.2 缩略图生成队列管理

**决策**: 全局 FIFO 队列

**实现细节**:
- 所有页面的缩略图任务在单一队列中按创建时间排序
- Playwright worker 使用 `asyncio.Semaphore(2)` 硬限制并发数
- 超时策略：指数退避（30s → 45s → 60s）
- 失败后降级：客户端实时生成（html2canvas），用户无需等待

**理由**: 简单直接，避免复杂的优先级逻辑，配合硬编码并发控制易于理解和维护。

### O.3 版本存储策略

**决策**: PostgreSQL JSONB + diff table

**实现细节**:
- 完整快照存储为 JSONB 类型（利用 PostgreSQL 的压缩和索引能力）
- diff 存储在独立的 `version_diffs` 表
- 使用 `diff-match-patch` 库生成和应用 diff
- 失败版本永久保留但单独存储，不计入版本配额，定期清理（90 天后删除）

**理由**: 适合中小规模（< 10 万版本），恢复速度快，查询灵活，无需额外的对象存储依赖。

### O.4 版本配额管理

**决策**: 软配额 + 宽限期

**实现细节**:
- 免费用户：5 个版本配额
- 付费用户：50 个版本配额
- 超过配额时允许继续创建，标记为「软配额」
- 超过软配额 2 倍后才开始自动删除最旧的未完整快照版本
- UI 中显示配额警告，引导用户升级或手动清理

**理由**: 给用户缓冲期，避免工作流中断，同时控制存储成本。

### O.5 Code Tab 访问控制

**决策**: 协作者只读访问（预留扩展）

**实现细节**:
- v5 阶段：仅项目创建者可以查看代码
- 数据模型预留 `collaborators` 表和权限字段
- 未来可通过 `role: owner | collaborator` 扩展只读访问
- 共享链接仅显示预览页面，不暴露源代码

**理由**: 符合 v5 范围（保护商业机密），为未来协作功能预留扩展点。

### O.6 实时通信技术

**决策**: sse-starlette（SSE）

**实现细节**:
- 使用 `sse-starlette` 库（Starlette 官方推荐）
- 自动重连 + 消息重放：后端缓存最近 100 条消息，断线重连后从最后一条消息开始重放
- 聊天消息和构建进度通过 SSE 流式传输
- 心跳检测：每 15 秒发送 `:ping` 保持连接

**理由**: API 简洁，支持自动重连和心跳，生产就绪，适合单向流式传输。

### O.7 聊天历史虚拟滚动

**决策**: react-window

**实现细节**:
- 使用成熟的 `react-window` 库
- 初始加载：显示最后 10 条用户消息 + 对应的 AI 响应
- 向上滚动时动态加载更老的消息（分页：每页 20 条）
- 「跳到最新」按钮：当用户距离底部超过 100px 时显示

**理由**: 成熟稳定，性能优秀，社区支持好。

### O.8 Code Tab 代码查看器

**决策**: CodeMirror 6（轻量）

**实现细节**:
- 使用 CodeMirror 6 而非 Monaco Editor
- 包体积 < 500KB，初始化快
- 功能：语法高亮、行号、搜索、点击错误跳转到文件/行
- 只读模式，不支持编辑

**理由**: 轻量级，适合只读场景，加载速度快。

### O.9 分支切换数据加载

**决策**: 独立 draft 状态（简单）

**实现细节**:
- 每个分支有独立的 draft 状态（`branch_drafts` 表）
- 切换分支时前端重新加载整个项目状态
- 加载期间显示骨架屏或 loading 状态
- 切换完成后更新预览 iframe 和代码查看器

**理由**: 实现简单，逻辑清晰，避免内存占用过大。

### O.10 单页重试幂等性

**决策**: 新任务 + 新版本记录

**实现细节**:
- 每次重试都创建新的 `task_id`
- 版本历史中标记 `retry_of: original_task_id`
- 完整的历史追踪，可查看所有重试尝试
- UI 中显示重试次数和最后结果

**理由**: 保留完整审计日志，便于调试和问题追踪。

### O.11 版本回滚确认 UI

**决策**: 渐进式披露（默认简单，可展开）

**实现细节**:
- 默认显示：将被回滚的页面名称列表（如「将首页回滚到 v3」）
- 「预览变更」按钮：点击后展开显示详细的文件列表和 diff 统计（如 index.html: +45 / -128）
- 确认对话框清晰标注：此操作创建新版本，可撤销

**理由**: 平衡简单性和信息完整性，避免 UI 过于复杂。

### O.12 Analytics 事件去重

**决策**: 后端去重（时间窗口）

**实现细节**:
- 后端基于 `user_id + event_id + 时间窗口` 去重
- 1 分钟内相同事件只记录一次
- 使用 Redis 或数据库去重表实现
- 支持跨设备去重

**理由**: 更准确，可靠性强，前端防抖作为辅助优化。

### O.13 ValidationCard 错误分类

**决策**: 3 级严重度（严重/警告/提示）

**实现细节**:
- **严重（Critical）**: 阻止发布（如 CSP 违规、XSS 风险）
- **警告（Warning）**: 不阻止但建议修复（如性能问题、可访问性）
- **提示（Info）**: 信息提示（如优化建议）
- 按严重度分组显示，严重错误优先展示

**理由**: 减少用户焦虑，突出关键问题，UI 清晰。

### O.14 缩略图重试 UI

**决策**: 内联重试按钮（直接）

**实现细节**:
- 在项目列表中缩略图位置显示「重新生成」按钮
- 点击后立即显示 loading 状态
- 成功后自动刷新缩略图显示
- 失败后显示错误消息和再次重试按钮

**理由**: 直接快速，用户无需额外交互步骤。

### O.15 页面回滚事务性

**决策**: 数据库事务（ACID）

**实现细节**:
- 使用 PostgreSQL 数据库事务保证原子性
- 要么所有页面回滚成功，要么全部回滚
- 失败时向用户显示明确错误信息
- 支持重试操作

**理由**: 数据一致性最优先，避免部分更新导致的不一致状态。

### O.16 TaskBoardCard 持久化

**决策**: 持久化到数据库（永久）

**实现细节**:
- 任务状态持久化到 `task_states` 表
- 重新进入编辑器时恢复显示
- 每个项目的任务历史保留 30 天
- 定期清理过期任务记录

**理由**: 保留完整上下文，用户体验好，存储成本可控。

### O.17 OG Image 生成时机

**决策**: 混合策略

**实现细节**:
- 发布完成后立即在后台队列中生成（低优先级）
- 首次社交分享时检测，如果未完成则立即升级为高优先级任务
- 使用 302 重定向到生成端点（`/og-image/{project_id}/{page_id}`）
- 生成的 OG Image 缓存到 CDN

**理由**: 平衡 proactive 和 reactive，大部分用户分享时已有 OG Image，首次分享也不会等太久。

### O.18 示例项目创建机制

**决策**: 一次性克隆（独立）

**实现细节**:
- 示例项目作为模板存储在数据库
- 用户点击后创建全新的独立项目
- 不保留与模板的关联
- 模板更新不影响已创建的项目
- 可选：跳过面试流程，直接生成初始内容

**理由**: 简单直接，用户有完全控制权，避免复杂的模板更新逻辑。

### O.19 发布前验证流程

**决策**: 警告 + 允许强制发布

**实现细节**:
- 发布前自动运行完整验证（CSP/JS/HTML/资源）
- 严重错误显示警告对话框
- 提供「强制发布」按钮（需二次确认）
- 强制发布的项目在列表中标记为「有警告」
- 用户可以稍后修复问题并重新发布

**理由**: 平衡安全性和用户控制权，避免阻塞用户工作流。

### O.20 分支删除策略

**决策**: 回收站（30 天保留）

**实现细节**:
- 删除分支后数据移动到「回收站」
- 保留 30 天后永久删除
- 用户可在回收站中恢复分支
- 回收站中的分支不计入分支配额
- UI 中显示「将在 X 天后永久删除」

**理由**: 提供撤销窗口，防止误操作，存储成本可控。

---

## Summary

v5 transforms Zaoya into a production-ready platform:

| What's New | What It Solves |
|------------|----------------|
| Publish Simulation | Preview = Publish trust |
| Version System | Traceability + manual rollback + branching |
| Code Tab | Clean chat, full code access (owner only) |
| Enhanced ValidationCard | Faster error diagnosis + page rollback |
| Thumbnail Queue | Reliable thumbnails + separate OG Image |
| Examples Gallery | Lower friction for first-time users |
| Manual Page Rollback | User controls when/what to rollback |
| Branching | A/B testing foundation (no merge) |

**Result**: Users can trust what they see, easily trace changes, control their rollback decisions, and optionally experiment with variants.

---

See also: [Future Roadmap](../docs/FUTURE-ROADMAP.md) for features deferred from v5 and beyond.

---

**Document Version**: 5.2
**Updated**: 2026-01-29
**Status**: Draft - Ready for Implementation with Implementation Decisions
