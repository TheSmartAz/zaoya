# v4 Phase 5: BuildPlan Fix (BuildPlan 修复)

**Timeline**: Weeks 5-6
**Status**: Pending
**Dependencies**: Phase 4 (Thumbnail Overview) complete

---

## Phase Overview

This phase ensures BuildPlan accuracy throughout the build process. The BuildPlan displayed in the BuildPlanCard should accurately reflect the actual tasks being executed, with real-time status updates as tasks complete.

### Connection to Project Goals

- **Transparency**: Users know exactly what will be built
- **Predictability**: Task estimates match reality
- **Trust**: Build progress matches plan

---

## Prerequisites

### Technical Prerequisites
- [ ] Phase 1-4 complete
- [ ] Live Task Feed streaming working
- [ ] BuildPlanCard component exists
- [ ] MultiTaskOrchestrator executing tasks

### Data Prerequisites
- [ ] Task naming conventions established
- [ ] Task categories defined
- [ ] Estimation heuristics validated

---

## Detailed Tasks

### Task 5.1: Define BuildPlan Data Model

**Priority**: P0 (Critical)
**Files**:
- `frontend/src/types/buildPlan.ts`
- `backend/app/models/build_plan.py`

```typescript
// frontend/src/types/buildPlan.ts

export interface BuildTask {
  id: string;
  name: string;
  description?: string;
  category: BuildTaskCategory;
  status: 'pending' | 'running' | 'done' | 'failed' | 'skipped';
  parent_id?: string;  // For sub-tasks
  page_id?: string;    // Which page this task belongs to
  started_at?: number;
  completed_at?: number;
  error?: string;
}

export type BuildTaskCategory =
  | 'planning'      // BuildPlan creation, page planning
  | 'generation'    // HTML/CSS/JS generation
  | 'validation'    // HTML validation, security checks
  | 'assets'        // Thumbnail generation, asset processing
  | 'storage'       // Saving to database
  | 'finalization'; // Final checks, publishing prep

export interface BuildPlan {
  id: string;
  project_id: string;
  created_at: string;

  // Pages to build
  pages: BuildPlanPage[];

  // All tasks (hierarchical)
  tasks: BuildTask[];

  // Summary
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;

  // Timing
  estimated_duration_ms?: number;
  actual_duration_ms?: number;
  started_at?: string;
  completed_at?: string;

  // Status
  status: 'draft' | 'approved' | 'running' | 'completed' | 'failed' | 'cancelled';
}

export interface BuildPlanPage {
  id: string;
  name: string;
  path: string;
  is_main: boolean;
  task_count: number;
}
```

```python
# backend/app/models/build_plan.py

from sqlalchemy import Column, String, JSON, DateTime, Integer, Enum
from datetime import datetime
from app.database import Base
import enum

class BuildStatus(enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BuildPlan(Base):
    __tablename__ = "build_plans"

    id = Column(String, primary_key=True)
    project_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Structure
    pages = Column(JSON, default=list)
    tasks = Column(JSON, default=list)

    # Counts
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)

    # Timing
    estimated_duration_ms = Column(Integer, nullable=True)
    actual_duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Status
    status = Column(Enum(BuildStatus), default=BuildStatus.DRAFT)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "pages": self.pages,
            "tasks": self.tasks,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "estimated_duration_ms": self.estimated_duration_ms,
            "actual_duration_ms": self.actual_duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value
        }
```

**Acceptance Criteria**:
- [ ] BuildTask captures all task states
- [ ] Categories cover all task types
- [ ] Timing fields for estimation vs actual
- [ ] Status tracks build lifecycle

---

### Task 5.2: Create BuildPlan Generator

**Priority**: P0 (Critical)
**Files**: `backend/app/services/build_runtime/plan_generator.py`

```python
# backend/app/services/build_runtime/plan_generator.py

from typing import List
from dataclasses import dataclass, field
import uuid
from app.models.build_plan import BuildPlan, BuildStatus

@dataclass
class TaskTemplate:
    """Template for generating build tasks."""
    name: str
    category: str
    estimated_ms: int
    description: str = ""

class BuildPlanGenerator:
    """
    Generate accurate BuildPlans from page specifications.

    Task templates are based on observed execution patterns.
    """

    # Per-page tasks
    PAGE_TASKS = [
        TaskTemplate("生成 HTML 结构", "generation", 5000, "AI 生成页面 HTML"),
        TaskTemplate("应用样式", "generation", 2000, "Tailwind CSS 样式应用"),
        TaskTemplate("HTML 验证", "validation", 1000, "检查 HTML 结构有效性"),
        TaskTemplate("安全检查", "validation", 1000, "检查 XSS 和注入风险"),
        TaskTemplate("保存页面", "storage", 500, "保存到数据库"),
        TaskTemplate("生成缩略图", "assets", 3000, "渲染页面截图"),
    ]

    # Project-level tasks
    PROJECT_TASKS_START = [
        TaskTemplate("创建构建计划", "planning", 500, "规划构建任务"),
        TaskTemplate("解析需求文档", "planning", 1000, "从 ProductDoc 提取信息"),
    ]

    PROJECT_TASKS_END = [
        TaskTemplate("验证跨页面链接", "validation", 1000, "检查页面间导航"),
        TaskTemplate("最终检查", "finalization", 500, "确认构建完成"),
    ]

    def generate(
        self,
        project_id: str,
        pages: List["PageSpec"],
        product_doc: "ProductDoc"
    ) -> BuildPlan:
        """
        Generate a complete BuildPlan.

        Args:
            project_id: Project identifier
            pages: List of pages to build
            product_doc: Project requirements

        Returns:
            BuildPlan with all tasks
        """
        plan_id = str(uuid.uuid4())
        tasks = []
        total_estimated_ms = 0

        # Project start tasks
        for template in self.PROJECT_TASKS_START:
            task = self._create_task(template, plan_id)
            tasks.append(task)
            total_estimated_ms += template.estimated_ms

        # Per-page tasks
        page_summaries = []
        for page in pages:
            page_tasks = []
            for template in self.PAGE_TASKS:
                task = self._create_task(
                    template,
                    plan_id,
                    page_id=page.id,
                    name_prefix=page.name
                )
                tasks.append(task)
                page_tasks.append(task)
                total_estimated_ms += template.estimated_ms

            page_summaries.append({
                "id": page.id,
                "name": page.name,
                "path": page.path,
                "is_main": page.is_main,
                "task_count": len(page_tasks)
            })

        # Project end tasks
        for template in self.PROJECT_TASKS_END:
            task = self._create_task(template, plan_id)
            tasks.append(task)
            total_estimated_ms += template.estimated_ms

        return BuildPlan(
            id=plan_id,
            project_id=project_id,
            pages=page_summaries,
            tasks=[t.__dict__ for t in tasks],
            total_tasks=len(tasks),
            completed_tasks=0,
            failed_tasks=0,
            estimated_duration_ms=total_estimated_ms,
            status=BuildStatus.DRAFT
        )

    def _create_task(
        self,
        template: TaskTemplate,
        plan_id: str,
        page_id: str = None,
        name_prefix: str = None
    ) -> "BuildTaskData":
        """Create a task from template."""
        name = template.name
        if name_prefix:
            name = f"{name_prefix}: {name}"

        return BuildTaskData(
            id=str(uuid.uuid4()),
            name=name,
            description=template.description,
            category=template.category,
            status="pending",
            page_id=page_id,
            estimated_ms=template.estimated_ms
        )

@dataclass
class BuildTaskData:
    id: str
    name: str
    description: str
    category: str
    status: str
    page_id: str = None
    estimated_ms: int = 0
    started_at: float = None
    completed_at: float = None
    error: str = None
```

**Acceptance Criteria**:
- [ ] All task types included
- [ ] Per-page tasks generated for each page
- [ ] Estimates based on templates
- [ ] Task IDs unique

---

### Task 5.3: Integrate Real-Time Status Updates

**Priority**: P0 (Critical)
**Files**: `backend/app/services/build_runtime/multi_task_orchestrator.py`

```python
# backend/app/services/build_runtime/multi_task_orchestrator.py (additions)

class MultiTaskOrchestrator:
    def __init__(self, ...):
        # ...
        self.plan_generator = BuildPlanGenerator()

    async def create_build_plan(
        self,
        project_id: str,
        pages: List[PageSpec],
        product_doc: ProductDoc
    ) -> BuildPlan:
        """Create and store a BuildPlan."""
        plan = self.plan_generator.generate(
            project_id=project_id,
            pages=pages,
            product_doc=product_doc
        )

        # Store in database
        db.add(plan)
        db.commit()

        return plan

    async def update_task_status(
        self,
        plan_id: str,
        task_id: str,
        status: str,
        error: str = None
    ):
        """Update task status in BuildPlan."""
        plan = db.query(BuildPlan).filter(BuildPlan.id == plan_id).first()
        if not plan:
            return

        # Find and update task
        tasks = plan.tasks
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = status
                if status == "running":
                    task["started_at"] = datetime.utcnow().timestamp()
                elif status in ["done", "failed", "skipped"]:
                    task["completed_at"] = datetime.utcnow().timestamp()
                if error:
                    task["error"] = error
                break

        # Update counts
        plan.tasks = tasks
        plan.completed_tasks = sum(1 for t in tasks if t["status"] == "done")
        plan.failed_tasks = sum(1 for t in tasks if t["status"] == "failed")

        db.commit()

    async def stream_progress(self, session_id: str, product_doc: ProductDoc):
        """Stream with accurate task matching."""
        session = self.sessions.get(session_id)
        plan = session.build_plan

        # Map logical operations to plan tasks
        task_mapping = self._build_task_mapping(plan, session.pages)

        async for event in self._execute_build(session, product_doc):
            # Update plan task when orchestrator task updates
            if event.type in [BuildEventType.TASK_STARTED,
                              BuildEventType.TASK_DONE,
                              BuildEventType.TASK_FAILED]:
                plan_task_id = task_mapping.get(event.task_id)
                if plan_task_id:
                    await self.update_task_status(
                        plan.id,
                        plan_task_id,
                        event.status,
                        event.error
                    )

            yield event

    def _build_task_mapping(
        self,
        plan: BuildPlan,
        pages: List[PageSpec]
    ) -> dict:
        """
        Map orchestrator task IDs to BuildPlan task IDs.

        Orchestrator uses: page-{page_id}, thumb-{page_id}, validate-{page_id}
        BuildPlan uses: generated UUIDs with names like "{PageName}: 生成 HTML 结构"
        """
        mapping = {}
        plan_tasks = plan.tasks

        for page in pages:
            page_id = page.id

            # Find matching tasks in plan
            for plan_task in plan_tasks:
                if plan_task.get("page_id") != page_id:
                    continue

                if "HTML" in plan_task["name"] and "生成" in plan_task["name"]:
                    mapping[f"page-{page_id}"] = plan_task["id"]
                elif "缩略图" in plan_task["name"]:
                    mapping[f"thumb-{page_id}"] = plan_task["id"]
                elif "验证" in plan_task["name"]:
                    mapping[f"validate-{page_id}"] = plan_task["id"]

        return mapping
```

**Acceptance Criteria**:
- [ ] BuildPlan created before build starts
- [ ] Task statuses update in real-time
- [ ] Counts (completed, failed) accurate
- [ ] Task mapping connects orchestrator to plan

---

### Task 5.4: Update BuildPlanCard with Live Status

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/chat/cards/BuildPlanCard.tsx`

```typescript
// frontend/src/components/chat/cards/BuildPlanCard.tsx (additions)

interface BuildPlanCardProps {
  plan: BuildPlan;
  isRunning?: boolean;  // Show progress mode
  onApprove: (pages: BuildPlanPage[]) => void;
  onCancel: () => void;
}

export function BuildPlanCard({
  plan,
  isRunning = false,
  onApprove,
  onCancel
}: BuildPlanCardProps) {
  // ... existing editing logic for draft mode ...

  // Running mode: show progress
  if (isRunning) {
    return (
      <div className="border rounded-lg p-4 max-w-md bg-white">
        <h4 className="font-medium mb-2">📋 构建进度</h4>

        {/* Progress bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>
              {plan.completed_tasks} / {plan.total_tasks} 任务完成
            </span>
            <span>
              {Math.round((plan.completed_tasks / plan.total_tasks) * 100)}%
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{
                width: `${(plan.completed_tasks / plan.total_tasks) * 100}%`
              }}
            />
          </div>
        </div>

        {/* Task list by page */}
        <div className="space-y-3">
          {plan.pages.map((page) => (
            <PageTaskGroup
              key={page.id}
              page={page}
              tasks={plan.tasks.filter(t => t.page_id === page.id)}
            />
          ))}
        </div>

        {/* Failed tasks warning */}
        {plan.failed_tasks > 0 && (
          <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-600">
            {plan.failed_tasks} 个任务失败
          </div>
        )}
      </div>
    );
  }

  // Draft mode: show editable plan
  return (
    <div className="border rounded-lg p-4 max-w-md bg-white">
      {/* ... existing draft UI ... */}
    </div>
  );
}

function PageTaskGroup({
  page,
  tasks
}: {
  page: BuildPlanPage;
  tasks: BuildTask[];
}) {
  const completedCount = tasks.filter(t => t.status === 'done').length;
  const isComplete = completedCount === tasks.length;

  return (
    <div className={cn(
      "p-2 rounded",
      page.is_main ? "bg-blue-50" : "bg-gray-50"
    )}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-sm">
          {page.name}
          {page.is_main && (
            <span className="text-xs text-blue-600 ml-1">(首页)</span>
          )}
        </span>
        <span className="text-xs text-gray-500">
          {completedCount}/{tasks.length}
        </span>
      </div>

      {/* Task status indicators */}
      <div className="flex gap-1">
        {tasks.map((task) => (
          <TaskDot key={task.id} status={task.status} title={task.name} />
        ))}
      </div>
    </div>
  );
}

function TaskDot({
  status,
  title
}: {
  status: BuildTask['status'];
  title: string;
}) {
  const colors = {
    pending: 'bg-gray-300',
    running: 'bg-blue-500 animate-pulse',
    done: 'bg-green-500',
    failed: 'bg-red-500',
    skipped: 'bg-gray-400'
  };

  return (
    <div
      className={cn("w-2 h-2 rounded-full", colors[status])}
      title={`${title}: ${status}`}
    />
  );
}
```

**Acceptance Criteria**:
- [ ] Draft mode shows editable pages
- [ ] Running mode shows progress bar
- [ ] Per-page task groups
- [ ] Task dots show status
- [ ] Failed tasks highlighted

---

### Task 5.5: Add BuildPlan Subscription

**Priority**: P1 (High)
**Files**: `frontend/src/hooks/useBuildPlan.ts`

```typescript
// frontend/src/hooks/useBuildPlan.ts

import { useEffect, useState } from 'react';
import { BuildPlan } from '@/types/buildPlan';

export function useBuildPlan(buildId: string | null) {
  const [plan, setPlan] = useState<BuildPlan | null>(null);

  useEffect(() => {
    if (!buildId) {
      setPlan(null);
      return;
    }

    // Initial fetch
    fetch(`/api/build/${buildId}/plan`)
      .then(res => res.json())
      .then(setPlan)
      .catch(console.error);

    // Subscribe to updates via SSE
    // Updates come through the main build stream
    const handleUpdate = (event: CustomEvent<Partial<BuildPlan>>) => {
      if (event.detail.id === buildId) {
        setPlan(prev => prev ? { ...prev, ...event.detail } : null);
      }
    };

    window.addEventListener('build-plan-update', handleUpdate as EventListener);

    return () => {
      window.removeEventListener('build-plan-update', handleUpdate as EventListener);
    };
  }, [buildId]);

  return plan;
}
```

**Acceptance Criteria**:
- [ ] Plan fetched on mount
- [ ] Updates received via events
- [ ] Cleanup on unmount

---

### Task 5.6: Add BuildPlan API Endpoint

**Priority**: P1 (High)
**Files**: `backend/app/api/build.py`

```python
# backend/app/api/build.py (additions)

@router.get("/api/build/{build_id}/plan")
async def get_build_plan(
    build_id: str,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
) -> BuildPlanResponse:
    """Get current build plan with task statuses."""
    plan = db.query(BuildPlan).filter(BuildPlan.id == build_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Build plan not found")

    # Verify ownership via project
    project = db.query(Project).filter(Project.id == plan.project_id).first()
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return BuildPlanResponse(**plan.to_dict())
```

**Acceptance Criteria**:
- [ ] Returns full BuildPlan
- [ ] Ownership verified
- [ ] 404 for missing plans

---

### Task 5.7: Emit BuildPlan Updates in Stream

**Priority**: P1 (High)
**Files**: `backend/app/services/build_runtime/multi_task_orchestrator.py`

```python
# backend/app/services/build_runtime/multi_task_orchestrator.py (additions)

async def stream_progress(self, session_id: str, product_doc: ProductDoc):
    # ... existing code ...

    # After each task update, emit plan update event
    if plan_task_id:
        await self.update_task_status(...)

        # Emit plan snapshot
        yield BuildEvent(
            type=BuildEventType.PLAN_UPDATE,
            plan_data={
                "completed_tasks": plan.completed_tasks,
                "failed_tasks": plan.failed_tasks,
                "tasks": plan.tasks
            }
        )
```

```typescript
// frontend/src/stores/buildStore.ts (additions)

handlePlanUpdate: (data: Partial<BuildPlan>) => {
  // Dispatch event for useBuildPlan hook
  window.dispatchEvent(new CustomEvent('build-plan-update', {
    detail: { id: get().buildId, ...data }
  }));
}
```

**Acceptance Criteria**:
- [ ] Plan updates emitted after task changes
- [ ] Frontend receives and applies updates
- [ ] UI reflects current progress

---

### Task 5.8: Validate Estimate Accuracy

**Priority**: P2 (Medium)
**Files**: `backend/app/services/build_runtime/plan_generator.py`

Add telemetry to improve estimates:

```python
# backend/app/services/build_runtime/telemetry.py

class BuildTelemetry:
    """Collect data to improve task estimates."""

    async def record_task_duration(
        self,
        task_category: str,
        actual_ms: int,
        page_complexity: str = "medium"
    ):
        """
        Record actual task duration for analysis.

        Use this data to calibrate TaskTemplate estimates.
        """
        # Store in database or analytics
        await self.analytics.record({
            "event": "task_duration",
            "category": task_category,
            "actual_ms": actual_ms,
            "complexity": page_complexity,
            "timestamp": datetime.utcnow()
        })

    def get_calibrated_estimate(
        self,
        category: str,
        complexity: str = "medium"
    ) -> int:
        """Get estimate based on historical data."""
        # Future: Query historical averages
        # For now, return template defaults
        return TEMPLATE_ESTIMATES.get(category, 2000)
```

**Acceptance Criteria**:
- [ ] Task durations recorded
- [ ] Historical data accessible
- [ ] Estimates improve over time

---

## Technical Considerations

### Task Granularity

**Current**: One task per major operation (generate, validate, save)

**Alternative**: More granular tasks (per-section generation)
- Pro: More progress visibility
- Con: Overhead, complex mapping

**Decision**: Keep current granularity, add sub-tasks in v5 if needed

### Estimate Accuracy Targets

| Metric | Target |
|--------|--------|
| Estimate within 20% of actual | > 80% of builds |
| No estimate > 2x actual | > 95% of builds |
| Total build time predictable | ±30% |

### BuildPlan Persistence

Options:
1. **Ephemeral**: Only in memory during build
2. **Persisted**: Saved to database

**Decision**: Persist for:
- Post-build review
- Analytics
- Resume after failure

---

## Acceptance Criteria

### Functional

- [ ] BuildPlan shows accurate task list
- [ ] Task count matches executed tasks
- [ ] Statuses update in real-time
- [ ] Progress percentage accurate
- [ ] Failed tasks identified
- [ ] Estimates shown (optional)

### Accuracy

- [ ] Every executed task appears in plan
- [ ] No phantom tasks (in plan but not executed)
- [ ] Task names match between plan and execution
- [ ] Page association correct

### UX

- [ ] Progress visible at a glance
- [ ] Per-page progress shown
- [ ] Failures clearly indicated
- [ ] Duration estimates helpful

---

## Risk Factors

### Risk 1: Task Mapping Complexity
- **Impact**: Medium - Tasks don't match plan
- **Mitigation**: Standardized task IDs
- **Mitigation**: Mapping table validated on startup

### Risk 2: Estimate Drift
- **Impact**: Low - Estimates become inaccurate
- **Mitigation**: Telemetry and calibration
- **Mitigation**: Show actual time, not just estimate

### Risk 3: Plan-Execution Mismatch
- **Impact**: Medium - Confusing UX
- **Mitigation**: Plan generated from same source as execution
- **Mitigation**: Validate consistency in tests

---

## Estimated Scope

**Complexity**: Medium

**Key Effort Drivers**:
- BuildPlan data model (20%)
- Task mapping and synchronization (35%)
- Real-time UI updates (25%)
- Testing and validation (20%)

---

## Testing Checklist

- [ ] Unit: BuildPlanGenerator creates correct tasks
- [ ] Unit: Task mapping covers all task types
- [ ] Integration: Status updates flow to UI
- [ ] Integration: Progress bar matches task completion
- [ ] E2E: Full build shows accurate progress
- [ ] E2E: Failed task appears in plan
- [ ] Accuracy: Task count matches execution

---

**Document Version**: 1.0
**Created**: 2026-01-27
**Status**: Ready for Implementation
