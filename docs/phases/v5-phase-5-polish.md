# Phase 5: Polish (Week 5)

**Focus**: User experience improvements, homepage examples, and branching foundation.

---

## Overview

This phase focuses on user-facing polish and experience improvements. It includes an examples gallery for first-time users, one-click project generation, chat UX improvements, and the foundation for A/B testing through branching.

**Key Goals**:
- Lower friction for new users with examples
- Improve chat readability (no code, better scrolling)
- Enable branching for variant testing
- Display line counts in tasks

---

## Prerequisites

- Phase 1-4 are complete
- Version system is functional
- Code generation pipeline is stable

---

## Detailed Tasks

### 5.1 Examples Gallery on Homepage

**Priority**: High

**Landing Page Structure**:
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

**Example Data Model**:
```typescript
interface ExampleProject {
  id: string;
  title: string;
  template: string;
  description: string;
  thumbnailUrl: string;
  seedPrompt: string;  // AI prompt to generate
  defaultPages: Array<{
    name: string;
    path: string;
  }>;
  defaultDesignSystem: {
    style: string;
    colors: string[];
    fonts: string[];
  };
}
```

**Tasks**:
1. Create `examples` table in database
2. Seed with 4-6 example projects
3. Design example cards UI
4. Implement example click handler
5. Add thumbnail generation for examples

**UI Layout**:
```
┌─────────────────────────────────────┐
│  Describe it. See it. Share it.     │
│  [开始创建]                          │
├─────────────────────────────────────┤
│  Explore Examples                   │
│  ┌──────┐ ┌──────┐ ┌──────┐        │
│  │Link  │ │Event │ │Product│       │
│  │in Bio│ │RSVP  │ │Landing│       │
│  └──────┘ └──────┘ └──────┘        │
└─────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] Examples gallery visible on homepage
- [ ] 4-6 example projects available
- [ ] Example cards show thumbnails
- [ ] Clicking example navigates correctly

### 5.2 One-Click Generation Flow

**Priority**: High

**Flow**:
1. User clicks example card
2. System creates project with example data
3. Optionally auto-start build (skip interview)
4. User lands in editor with pre-generated content

**Tasks**:
1. Implement example clone API:
   ```
   POST /api/examples/{id}/clone
   → Creates new project from example
   ```
2. Add option to skip interview
3. Auto-trigger first build
4. Redirect to editor with preloaded content

**Acceptance Criteria**:
- [ ] Clicking example creates new project
- [ ] Interview can be skipped for examples
- [ ] First build starts automatically
- [ ] User lands in editor with generated content

### 5.3 Chat UX Improvements

**Priority**: High

**Improvements**:

**A. Cards Flow Naturally (Not Fixed)**
- All cards are message items in chat flow
- BuildPlanCard, PageCard, ValidationCard, VersionSummaryCard, TaskBoardCard
- No sticky positioning

**B. Auto-Scroll Behavior**
- Only auto-scroll when user is near bottom (within 100px)
- Show "跳到最新" button when far from bottom
- No scrolling while user is reading history

**C. No Code in Chat**
- Replace code blocks with summary:
  ```
  "已更新首页 Hero 区块：
  - 新增标题动画效果
  - 优化 CTA 按钮视觉层级
  - 调整移动端响应式布局

  3 个文件，+48 -12 行"

  [查看代码] [查看预览]
  ```

**Tasks**:
1. Remove fixed positioning from cards
2. Implement auto-scroll logic with distance detection
3. Add "跳到最新" button
4. Update chat message formatting (no code)
5. Add action buttons to summaries

**Acceptance Criteria**:
- [ ] Cards flow naturally in chat
- [ ] Auto-scroll only when near bottom
- [ ] "跳到最新" appears when scrolling
- [ ] No source code shown in chat
- [ ] Summary shows file/line counts

### 5.4 TaskBoardCard - Cumulative Task Display

**Priority**: Medium

**One Card Per Build Session**:
- Shows all tasks in fixed order
- Status icon: spinner 🔄 / check ✓ / alert ⚠ / clock ⏱
- Line changes: +X / -Y
- Retry button for failed tasks

**Tasks**:
1. Create `TaskBoardCard` component
2. Implement task state persistence
3. Add task status tracking
4. Calculate line changes from diffs
5. Add retry functionality

**Task Board Layout**:
```
┌─────────────────────────────────────┐
│ Build Progress                      │
├─────────────────────────────────────┤
│ ✓ Home 页面 HTML          +127 -23  │
│ ✓ About 页面 HTML         +45  -12  │
│ 🔄 Contact 表单逻辑                │
│ ⚠️ Thumbnail 生成    [重试]        │
│ ⏱️ SEO 优化                        │
└─────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] One card per build session
- [ ] Tasks shown in fixed order
- [ ] Status icons update correctly
- [ ] Line changes displayed
- [ ] Retry button works for failed tasks

### 5.5 Virtual Scrolling for Chat History

**Priority**: Medium

**Strategy**: Virtual scrolling with dynamic loading

**Tasks**:
1. Integrate `react-window` library
2. Implement initial load (last 10 messages)
3. Add dynamic loading on scroll up (pagination: 20 per page)
4. Add "跳到最新" button logic
5. Optimize rendering performance

**Loading Logic**:
```
Initial Load: Last 10 user messages + AI responses
Scroll Up: Load 20 more messages
Show "跳到最新" when > 100px from bottom
```

**Acceptance Criteria**:
- [ ] Initial load shows last 10 messages
- [ ] Scroll up loads older messages
- [ ] Smooth scrolling with 10+ messages
- [ ] "跳到最新" button appears correctly

### 5.6 Branch Creation and Isolation

**Priority**: High

**Branch Data Model**:
```sql
CREATE TABLE branches (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  name VARCHAR(50),  -- 'main', 'a', 'b'
  label VARCHAR(100),  -- 'Control', 'Variant B'
  parent_branch_id UUID REFERENCES branches(id),
  created_at TIMESTAMP DEFAULT NOW(),
  created_from_version_id UUID REFERENCES versions(id),
  is_default BOOLEAN
);
```

**Tasks**:
1. Implement branch creation API:
   ```
   POST /api/projects/{id}/versions/{version_id}/branch
   Body: { name, label }
   ```
2. Create separate draft storage per branch
3. Implement branch switching in editor
4. Add branch selector UI
5. Create separate preview URLs per branch

**Branch Isolation**:
- Each branch has separate preview URL
- Each branch has separate share link
- Each branch has separate published snapshot
- Branch switching loads branch-specific state

**Acceptance Criteria**:
- [ ] Can create branch from any version
- [ ] Branch quota enforced (3 per project)
- [ ] Each branch has separate preview
- [ ] Branch switching works correctly
- [ ] Independent draft state per branch

---

## Technical Considerations

### Example Storage
- Examples stored in database
- Thumbnail pre-generated
- Seed prompts for AI generation
- Default design systems

### Virtual Scrolling
```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={100}
  onItemsRendered={({ visibleStopIndex }) => {
    // Load more if near top
    if (visibleStopIndex < 10) {
      loadOlderMessages();
    }
  }}
>
  {Message}
</FixedSizeList>
```

### Branch Quota
| Tier | Max Branches |
|------|--------------|
| Free | 3 |
| Paid | 3 (configurable) |

### Branch URL Structure
```
Preview: /editor/{project_id}?branch=a
Share: https://pages.zaoya.app/p/{public_id}?variant=a
```

---

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Example projects become outdated | Medium | Version examples, periodic reviews |
| Virtual scrolling performance | Medium | Use mature library (react-window) |
| Branch quota confusion | Low | Clear UI indicators, upgrade prompts |
| One-click flow skips important steps | Low | Make interview skippable, not mandatory |

---

## Estimated Scope

**Complexity**: Medium

**Effort Drivers**:
- Examples gallery (2 days)
- One-click flow (1-2 days)
- Chat UX improvements (2-3 days)
- TaskBoardCard (1-2 days)
- Virtual scrolling (2 days)
- Branching (2-3 days)

**Total Estimated Duration**: 1 week

---

## Dependencies

- **Internal**: Phase 1-4
- **Libraries**: `react-window`
- **Database**: PostgreSQL

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Example usage rate | > 30% of new users |
| First-page time | < 30 seconds |
| Chat scrolling smooth | No jank with 100+ messages |
| Branch creation rate | > 10% of power users |
| Task completion visibility | 100% (all tasks visible) |

---

## API Endpoints

```
GET /api/examples
POST /api/examples/{id}/clone
POST /api/projects/{id}/versions/{version_id}/branch
GET /api/projects/{id}/branches
PUT /api/projects/{id}/branches/{branch_id}/default
```

---

## Notes

- Examples gallery reduces first-time user friction
- One-click flow demonstrates product value immediately
- Chat UX improvements make conversations more readable
- Virtual scrolling enables long chat histories
- Branching enables A/B testing foundation (merge deferred)
- TaskBoardCard provides build progress visibility

---

**Next Phase**: Week 6 - Completion
