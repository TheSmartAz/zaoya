# Phase 5: Frontend Timeline UI

**Duration**: Week 4-5
**Status**: Pending
**Depends On**: Phase 4 (Orchestrator)

---

## Phase Overview

This phase implements the Build Timeline UI - a panel in the editor that shows build progress and allows users to step through the build loop. This is the user-facing interface for the agentic build system.

The timeline panel shows:
- Current phase and progress
- Task list with status indicators
- Current task details and acceptance criteria
- Last patch summary (files touched, notes)
- Verification status (validation, checks)
- Reviewer decision
- Control buttons (step, abort, revert)

---

## Prerequisites

### Must Be Completed Before Starting
1. **Phase 4 complete** - API endpoints must work
2. **Editor page exists** - `frontend/src/pages/EditorPage.tsx`
3. **Store patterns established** - Zustand store pattern used elsewhere

### External Dependencies
- **shadcn/ui components** - Button, Card, Badge, Tabs, ScrollArea
- **Tailwind CSS** - Already in use

---

## Detailed Tasks

### Task 5.1: Create Build Store

**Description**: Implement Zustand store for build state management

**File: `frontend/src/stores/buildStore.ts`**

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// === Types ===

export type BuildPhase =
  | 'planning'
  | 'implementing'
  | 'verifying'
  | 'reviewing'
  | 'iterating'
  | 'ready'
  | 'aborted'
  | 'error';

export type TaskStatus = 'todo' | 'doing' | 'done' | 'blocked';

export type ReviewDecision = 'approve' | 'request_changes';

export interface Task {
  id: string;
  title: string;
  goal: string;
  acceptance: string[];
  depends_on: string[];
  files_expected: string[];
  status: TaskStatus;
  created_at: string;
  completed_at?: string;
}

export interface BuildGraph {
  tasks: Task[];
  notes: string;
  created_at: string;
}

export interface PatchSet {
  id: string;
  task_id: string;
  diff: string;
  touched_files: string[];
  notes: string;
  created_at: string;
}

export interface ValidationReport {
  ok: boolean;
  errors: string[];
  warnings: string[];
  js_valid: boolean;
}

export interface CheckReport {
  ok: boolean;
  typecheck_ok: boolean;
  lint_ok: boolean;
  unit_ok: boolean;
  logs: string;
}

export interface ReviewReport {
  decision: ReviewDecision;
  reasons: string[];
  required_fixes: string[];
}

export interface BuildHistoryEvent {
  ts: string;
  phase: BuildPhase;
  action: string;
  details: Record<string, unknown>;
}

export interface BuildState {
  // Identifiers
  buildId: string | null;
  projectId: string | null;

  // Phase tracking
  phase: BuildPhase | null;
  currentTaskId: string | null;

  // Artifacts
  buildGraph: BuildGraph | null;
  lastPatch: PatchSet | null;
  lastValidation: ValidationReport | null;
  lastChecks: CheckReport | null;
  lastReview: ReviewReport | null;
  history: BuildHistoryEvent[];

  // Loading states
  isLoading: boolean;
  isStepping: boolean;
  error: string | null;

  // Actions
  startBuild: (projectId: string, seed: BuildSeed) => Promise<void>;
  stepBuild: (userMessage?: string) => Promise<void>;
  abortBuild: () => Promise<void>;
  revertPatch: () => Promise<void>;
  checkPublishReady: () => Promise<boolean>;
  resetBuild: () => void;
}

export interface BuildSeed {
  brief: Record<string, unknown>;
  build_plan: Record<string, unknown>;
  product_doc: Record<string, unknown>;
}

// === Store Implementation ===

export const useBuildStore = create<BuildState>()(
  persist(
    (set, get) => ({
      // Initial state
      buildId: null,
      projectId: null,
      phase: null,
      currentTaskId: null,
      buildGraph: null,
      lastPatch: null,
      lastValidation: null,
      lastChecks: null,
      lastReview: null,
      history: [],
      isLoading: false,
      isStepping: false,
      error: null,

      // Actions
      async startBuild(projectId: string, seed: BuildSeed) {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch('/api/build/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId, seed })
          });

          if (!response.ok) {
            throw new Error(`Failed to start build: ${response.statusText}`);
          }

          const state = await response.json();
          set({
            buildId: state.build_id,
            projectId: state.project_id,
            phase: state.phase,
            currentTaskId: state.current_task_id,
            buildGraph: state.build_graph,
            lastPatch: state.last_patch,
            lastValidation: state.last_validation,
            lastChecks: state.last_checks,
            lastReview: state.last_review,
            history: state.history,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false
          });
        }
      },

      async stepBuild(userMessage?: string) {
        const { buildId } = get();
        if (!buildId) return;

        set({ isStepping: true, error: null });

        try {
          const response = await fetch('/api/build/step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              build_id: buildId,
              user_message: userMessage
            })
          });

          if (!response.ok) {
            throw new Error(`Failed to step build: ${response.statusText}`);
          }

          const state = await response.json();
          set({
            phase: state.phase,
            currentTaskId: state.current_task_id,
            buildGraph: state.build_graph,
            lastPatch: state.last_patch,
            lastValidation: state.last_validation,
            lastChecks: state.last_checks,
            lastReview: state.last_review,
            history: state.history,
            isStepping: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Unknown error',
            isStepping: false
          });
        }
      },

      async abortBuild() {
        const { buildId } = get();
        if (!buildId) return;

        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`/api/build/${buildId}/abort`, {
            method: 'POST'
          });

          if (!response.ok) {
            throw new Error(`Failed to abort build: ${response.statusText}`);
          }

          const state = await response.json();
          set({
            phase: state.phase,
            history: state.history,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false
          });
        }
      },

      async revertPatch() {
        // Implementation depends on snapshot system
        const { buildId, projectId } = get();
        if (!buildId || !projectId) return;

        // Get latest snapshot and restore
        try {
          const response = await fetch(`/api/snapshots/${projectId}/latest`);
          if (response.ok) {
            const snapshot = await response.json();
            await fetch(`/api/snapshots/${snapshot.id}/restore`, {
              method: 'POST'
            });
            // Refresh build state
            get().stepBuild();
          }
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to revert patch'
          });
        }
      },

      async checkPublishReady() {
        const { buildId } = get();
        if (!buildId) return false;

        try {
          const response = await fetch(`/api/build/${buildId}/can-publish`);
          if (response.ok) {
            const result = await response.json();
            return result.can_publish;
          }
        } catch {
          // Fallback to true if endpoint fails
          return true;
        }

        return false;
      },

      resetBuild() {
        set({
          buildId: null,
          projectId: null,
          phase: null,
          currentTaskId: null,
          buildGraph: null,
          lastPatch: null,
          lastValidation: null,
          lastChecks: null,
          lastReview: null,
          history: [],
          error: null
        });
      }
    }),
    {
      name: 'build-store',
      partialize: (state) => ({
        buildId: state.buildId,
        projectId: state.projectId,
        phase: state.phase
      })
    }
  )
);
```

**Dependencies**: None (self-contained)
**Parallelizable**: Yes (with Task 5.2)

---

### Task 5.2: Create Build Timeline Components

**Description**: Create all timeline panel components

**File: `frontend/src/components/build/BuildTimeline.tsx`**

```typescript
import React from 'react';
import { useBuildStore } from '@/stores/buildStore';
import { TaskList } from './TaskList';
import { CurrentTaskCard } from './CurrentTaskCard';
import { PatchSummary } from './PatchSummary';
import { VerificationStatus } from './VerificationStatus';
import { ReviewStatus } from './ReviewStatus';
import { BuildControls } from './BuildControls';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';

export function BuildTimeline() {
  const {
    phase,
    isLoading,
    isStepping,
    error,
    startBuild,
    stepBuild,
    abortBuild,
    projectId,
    buildId
  } = useBuildStore();

  const [showPanel, setShowPanel] = React.useState(true);

  if (!showPanel) {
    return (
      <button
        className="fixed bottom-4 right-4 z-50 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg"
        onClick={() => setShowPanel(true)}
      >
        Build Timeline
      </button>
    );
  }

  const getPhaseColor = (p: string | null) => {
    switch (p) {
      case 'planning': return 'bg-blue-100 text-blue-800';
      case 'implementing': return 'bg-yellow-100 text-yellow-800';
      case 'verifying': return 'bg-purple-100 text-purple-800';
      case 'reviewing': return 'bg-indigo-100 text-indigo-800';
      case 'iterating': return 'bg-orange-100 text-orange-800';
      case 'ready': return 'bg-green-100 text-green-800';
      case 'aborted': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPhaseLabel = (p: string | null) => {
    const labels: Record<string, string> = {
      planning: 'Planning',
      implementing: 'Implementing',
      verifying: 'Verifying',
      reviewing: 'Reviewing',
      iterating: 'Iterating',
      ready: 'Ready to Publish',
      aborted: 'Aborted',
      error: 'Error'
    };
    return labels[p || 'unknown'] || p;
  };

  if (!buildId) {
    return (
      <Card className="w-80 h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Build Timeline</CardTitle>
            <button
              onClick={() => setShowPanel(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              −
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No build in progress</p>
            <p className="text-xs mt-1">Complete the interview to start building</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="pb-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Build Timeline</CardTitle>
          <button
            onClick={() => setShowPanel(false)}
            className="text-muted-foreground hover:text-foreground"
          >
            −
          </button>
        </div>
        <div className="flex items-center gap-2 mt-2">
          <Badge className={getPhaseColor(phase)}>
            {getPhaseLabel(phase)}
          </Badge>
          {(isLoading || isStepping) && (
            <Loader2 className="h-4 w-4 animate-spin" />
          )}
        </div>
        {error && (
          <div className="mt-2 p-2 bg-red-50 text-red-700 text-xs rounded">
            {error}
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden pt-0">
        <ScrollArea className="h-[calc(100vh-250px)]">
          <div className="space-y-4 pr-4">
            {/* Current Task */}
            <CurrentTaskCard />

            {/* Task List */}
            <TaskList />

            {/* Last Patch */}
            <PatchSummary />

            {/* Verification */}
            <VerificationStatus />

            {/* Review */}
            <ReviewStatus />
          </div>
        </ScrollArea>

        {/* Controls */}
        <div className="mt-4 pt-4 border-t">
          <BuildControls
            onStep={() => stepBuild()}
            onAbort={() => abortBuild()}
            disabled={isLoading || isStepping}
          />
        </div>
      </CardContent>
    </Card>
  );
}
```

**Dependencies**: Task 5.1
**Parallelizable**: No

---

### Task 5.3: Create Supporting Components

**Description**: Create TaskList, CurrentTaskCard, PatchSummary, VerificationStatus, ReviewStatus, BuildControls

**File: `frontend/src/components/build/TaskList.tsx`**

```typescript
import React from 'react';
import { useBuildStore } from '@/stores/buildStore';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

export function TaskList() {
  const { buildGraph } = useBuildStore();

  if (!buildGraph?.tasks) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done': return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'doing': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div>
      <h4 className="text-sm font-medium mb-2">Tasks</h4>
      <div className="space-y-1">
        {buildGraph.tasks.map((task) => (
          <div
            key={task.id}
            className={`flex items-center gap-2 p-2 rounded text-sm ${
              task.status === 'doing' ? 'bg-yellow-50' : ''
            }`}
          >
            {getStatusIcon(task.status)}
            <span className="truncate flex-1">{task.title}</span>
            <Badge variant="outline" className="text-xs">
              {task.status}
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**File: `frontend/src/components/build/CurrentTaskCard.tsx`**

```typescript
import React from 'react';
import { useBuildStore } from '@/stores/buildStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2 } from 'lucide-react';

export function CurrentTaskCard() {
  const { buildGraph, currentTaskId } = useBuildStore();

  if (!buildGraph?.tasks || !currentTaskId) return null;

  const currentTask = buildGraph.tasks.find(t => t.id === currentTaskId);
  if (!currentTask) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">
          Current: {currentTask.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-2">{currentTask.goal}</p>
        <div className="space-y-1">
          {currentTask.acceptance.map((criterion, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <CheckCircle2 className="h-3 w-3 mt-0.5 text-green-500 flex-shrink-0" />
              <span>{criterion}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

**File: `frontend/src/components/build/PatchSummary.tsx`**

```typescript
import React from 'react';
import { useBuildStore } from '@/stores/buildStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileDiff } from 'lucide-react';

export function PatchSummary() {
  const { lastPatch } = useBuildStore();

  if (!lastPatch) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <FileDiff className="h-4 w-4" />
          Last Patch
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-2">
          {lastPatch.touched_files.length} file(s) changed
        </p>
        <div className="space-y-1">
          {lastPatch.touched_files.slice(0, 5).map((file) => (
            <div key={file} className="text-xs font-mono truncate">
              {file}
            </div>
          ))}
        </div>
        {lastPatch.notes && (
          <p className="text-xs mt-2 text-muted-foreground">
            {lastPatch.notes}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

**File: `frontend/src/components/build/VerificationStatus.tsx`**

```typescript
import React from 'react';
import { useBuildStore } from '@/stores/buildStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export function VerificationStatus() {
  const { lastValidation, lastChecks, phase } = useBuildStore();

  const isVerifying = phase === 'verifying';
  const hasResults = lastValidation || lastChecks;

  if (!hasResults && !isVerifying) return null;

  const getStatusIcon = (ok?: boolean) => {
    if (ok === true) return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (ok === false) return <XCircle className="h-4 w-4 text-red-500" />;
    return <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />;
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Verification</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span>Validator</span>
          {getStatusIcon(lastValidation?.ok)}
        </div>
        <div className="flex items-center justify-between text-sm">
          <span>Typecheck</span>
          {getStatusIcon(lastChecks?.typecheck_ok)}
        </div>
        <div className="flex items-center justify-between text-sm">
          <span>Lint</span>
          {getStatusIcon(lastChecks?.lint_ok)}
        </div>
        <div className="flex items-center justify-between text-sm">
          <span>Unit Tests</span>
          {getStatusIcon(lastChecks?.unit_ok)}
        </div>

        {isVerifying && (
          <div className="text-xs text-muted-foreground mt-2">
            Running verification...
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

**File: `frontend/src/components/build/ReviewStatus.tsx`**

```typescript
import React from 'react';
import { useBuildStore } from '@/stores/buildStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ThumbsUp, MessageSquare, AlertCircle } from 'lucide-react';

export function ReviewStatus() {
  const { lastReview, phase } = useBuildStore();

  if (!lastReview && phase !== 'reviewing') return null;

  const isReviewing = phase === 'reviewing';

  if (isReviewing) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Review
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            Waiting for reviewer...
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!lastReview) return null;

  const isApproved = lastReview.decision === 'approve';

  return (
    <Card className={isApproved ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {isApproved ? (
            <ThumbsUp className="h-4 w-4 text-green-600" />
          ) : (
            <AlertCircle className="h-4 w-4 text-yellow-600" />
          )}
          Review
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Badge variant={isApproved ? 'default' : 'secondary'} className="mb-2">
          {lastReview.decision === 'approve' ? 'Approved' : 'Changes Requested'}
        </Badge>

        {lastReview.reasons.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium">Reasons:</p>
            {lastReview.reasons.map((reason, i) => (
              <p key={i} className="text-xs text-muted-foreground">
                • {reason}
              </p>
            ))}
          </div>
        )}

        {lastReview.required_fixes.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs font-medium">Required fixes:</p>
            {lastReview.required_fixes.map((fix, i) => (
              <p key={i} className="text-xs text-muted-foreground">
                • {fix}
              </p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

**File: `frontend/src/components/build/BuildControls.tsx`**

```typescript
import React from 'react';
import { Button } from '@/components/ui/button';
import { Play, RotateCcw, Square } from 'lucide-react';

interface BuildControlsProps {
  onStep: () => void;
  onAbort: () => void;
  disabled?: boolean;
}

export function BuildControls({ onStep, onAbort, disabled }: BuildControlsProps) {
  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        onClick={onStep}
        disabled={disabled}
        className="flex-1"
      >
        <Play className="h-4 w-4 mr-1" />
        Run Step
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={onStep}
        disabled={disabled}
        title="Retry current step"
      >
        <RotateCcw className="h-4 w-4" />
      </Button>
      <Button
        size="sm"
        variant="destructive"
        onClick={onAbort}
        disabled={disabled}
      >
        <Square className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

**Dependencies**: Task 5.2
**Parallelizable**: No

---

### Task 5.4: Integrate Timeline into Editor

**Description**: Add BuildTimeline to EditorPage layout

**File: `frontend/src/pages/EditorPage.tsx` (additions)**

```typescript
import { BuildTimeline } from '@/components/build/BuildTimeline';

// Inside EditorPage component, add timeline panel:
<div className="flex">
  <main className="flex-1">
    {/* Existing editor content */}
  </main>
  {shouldShowTimeline && (
    <aside className="w-80 border-l">
      <BuildTimeline />
    </aside>
  )}
</div>
```

**Dependencies**: Tasks 5.2, 5.3
**Parallelizable**: No

---

## Technical Considerations

### Key Dependencies
- **shadcn/ui** - Card, Button, Badge, ScrollArea, etc.
- **lucide-react** - Icons
- **zustand** - Already in use

### Architecture Decisions
1. **Collapsible panel** - Users can hide/show timeline
2. **Store persistence** - Persist buildId for refresh recovery
3. **Component decomposition** - Small focused components

### State Management
- BuildStore handles all API calls
- Components are purely presentational
- Loading states handle async operations

### UI/UX
- Phase badges use color coding
- Icons indicate status (done/todo/doing)
- Error states are visible but not blocking

---

## Acceptance Criteria

- [ ] BuildStore manages all build API calls
- [ ] BuildTimeline panel shows current phase
- [ ] TaskList shows all tasks with status
- [ ] CurrentTaskCard shows task details and acceptance criteria
- [ ] PatchSummary shows touched files and notes
- [ ] VerificationStatus shows validation and check results
- [ ] ReviewStatus shows reviewer decision
- [ ] BuildControls allow stepping, retrying, aborting
- [ ] Timeline can be collapsed/expanded
- [ ] Loading states show during API calls
- [ ] Error messages are displayed
- [ ] Panel integrates with EditorPage layout
- [ ] Tests cover store and components

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API latency affects UX | Medium | Low | Loading states and optimistic updates |
| Panel takes too much space | Low | Low | Collapsible design |
| State sync issues | Medium | Medium | React Query or SWR for data fetching |

---

## Estimated Scope

**Complexity**: Medium

**Key Effort Drivers**:
- Creating multiple UI components
- Integrating with existing EditorPage
- Handling loading and error states

**Estimated Lines of Code**: ~700-1000 (all components)

---

## Testing Strategy

### Unit Tests
- Test BuildStore actions
- Test component rendering with mock state
- Test button click handlers

### Integration Tests
- Test timeline panel in editor context
- Test API integration (mock server)

### Test Files
- `frontend/tests/unit/stores/buildStore.test.ts`
- `frontend/tests/unit/components/build/BuildTimeline.test.tsx`
