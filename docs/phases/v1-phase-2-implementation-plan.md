# Phase 2: Growth - Implementation Plan

> **Version**: v1
> **Created**: 2025-01-21
> **Status**: Complete (for now)

This document breaks down Phase 2 into actionable tasks with clear dependencies, acceptance criteria, and estimated complexity.

---

## Overview

**Total Estimated Effort**: 6-8 weeks

**Implementation Strategy**: Phased approach with database-first foundation

```
Foundation → Prerequisites → Experiments → Analytics → Images → Subscriptions
   (Week 1)     (Week 2)      (Week 3-4)     (Week 5)     (Week 6)    (Week 7)
```

---

## Task Legend

| Priority | Meaning |
|----------|---------|
| 🔴 P0 | Critical path, blocks other tasks |
| 🟡 P1 | High priority, significant feature |
| 🟢 P2 | Nice to have, can defer |

| Complexity | Meaning |
|------------|---------|
| S | Small (0.5-1 day) |
| M | Medium (1-2 days) |
| L | Large (3-5 days) |
| XL | Extra Large (1+ weeks) |

---

## Phase 0: Foundation (Week 1)

### Task 0.1: Database Migration - Analytics
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Backend

**Description**: Migrate analytics from in-memory to PostgreSQL with enhanced tracking

**Files to Create**:
- `backend/alembic/versions/YYYYMMDD_XXXX_analytics_tables.py`

**Tasks**:
- [ ] Create `analytics_events` table with time-series optimization
- [ ] Create `analytics_sessions` table
- [ ] Create `analytics_daily` aggregation table
- [ ] Create `analytics_funnels` table
- [ ] Create `analytics_cohorts` table
- [ ] Add indexes (BRIN for timestamp, GIN for JSONB)
- [ ] Run migration and verify

**Acceptance Criteria**:
- All 5 tables created successfully
- Indexes verified with `EXPLAIN ANALYZE`
- Can insert/query events via PostgreSQL

**Dependencies**: None

---

### Task 0.2: Database Migration - Experiments
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Backend

**Description**: Create A/B testing database schema

**Files to Create**:
- `backend/alembic/versions/YYYYMMDD_XXXX_experiments_tables.py`

**Tasks**:
- [ ] Create `experiments` table
- [ ] Create `experiment_variants` table
- [ ] Create `experiment_results` table
- [ ] Create `experiment_assignments` table
- [ ] Create `experiment_conversions` table
- [ ] Create `experiment_audit_log` table
- [ ] Add constraints (one control per experiment)
- [ ] Run migration and verify

**Acceptance Criteria**:
- All 6 tables created successfully
- Exclusion constraint ensures one control variant
- Foreign keys cascade correctly

**Dependencies**: Task 0.1 (analytics_events referenced)

---

### Task 0.3: Database Migration - Credits
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Backend

**Description**: Create credits system tables

**Files to Create**:
- `backend/alembic/versions/YYYYMMDD_XXXX_credits_tables.py`

**Tasks**:
- [ ] Create `user_credits` table
- [ ] Create `credit_transactions` table
- [ ] Create `credit_packages` table
- [ ] Seed initial credit packages
- [ ] Run migration and verify

**Acceptance Criteria**:
- All 3 tables created successfully
- One-to-one constraint on user_credits
- Initial packages seeded

**Dependencies**: None (uses existing users table)

---

### Task 0.4: Database Migration - Assets
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Backend

**Description**: Create asset library table

**Files to Create**:
- `backend/alembic/versions/YYYYMMDD_XXXX_assets_table.py`

**Tasks**:
- [ ] Create `assets` table
- [ ] Add indexes for user/project queries
- [ ] Add GIN index for tags
- [ ] Run migration and verify

**Acceptance Criteria**:
- Table created successfully
- Can query assets by user and tags

**Dependencies**: None

---

### Task 0.5: Database Migration - Subscriptions (Mock)
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Backend

**Description**: Create subscription tables with mock Stripe integration

**Files to Create**:
- `backend/alembic/versions/YYYYMMDD_XXXX_subscriptions_tables.py`

**Tasks**:
- [ ] Create `subscription_plans` table
- [ ] Create `user_subscriptions` table
- [ ] Create `subscription_events` table
- [ ] Seed initial plans (free, pro, team)
- [ ] Run migration and verify

**Acceptance Criteria**:
- All 3 tables created successfully
- Free, Pro, Team plans seeded
- Mock webhook handling works

**Dependencies**: None

---

### Task 0.6: ORM Models Creation
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Backend

**Description**: Create SQLAlchemy ORM models for all new tables

**Files to Create**:
- `backend/app/models/db/analytics.py`
- `backend/app/models/db/experiment.py`
- `backend/app/models/db/credit.py`
- `backend/app/models/db/asset.py`
- `backend/app/models/db/subscription.py`

**Tasks**:
- [ ] Create AnalyticsEvent model
- [ ] Create AnalyticsSession model
- [ ] Create AnalyticsDaily model
- [ ] Create Experiment model with variants relationship
- [ ] Create ExperimentVariant model
- [ ] Create UserCredits model
- [ ] Create Asset model
- [ ] Create UserSubscription model
- [ ] Add relationships and cascade rules

**Acceptance Criteria**:
- All models import successfully
- Relationships work (eager loading)
- Can query via SQLAlchemy session

**Dependencies**: Tasks 0.1-0.5

---

## Phase 1: Prerequisites (Week 2)

### Task 1.1: User Preferences API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Create API endpoints for user preferences

**Files to Modify**:
- `backend/app/api/users.py`
- `backend/app/models/user.py`

**Tasks**:
- [ ] Add GET /api/auth/preferences endpoint
- [ ] Add PUT /api/auth/preferences endpoint
- [ ] Implement preferences merge logic
- [ ] Add validation for allowed keys
- [ ] Test with auth token

**Acceptance Criteria**:
- GET returns user's preferences JSONB
- PUT merges new preferences with existing
- Invalid keys rejected with 400
- Auth required for both endpoints

**Dependencies**: Task 0.6

---

### Task 1.2: User Preferences Store
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Create Zustand store for user preferences

**Files to Create**:
- `frontend/src/stores/preferencesStore.ts`
- `frontend/src/types/preferences.ts`

**Tasks**:
- [ ] Create preferences TypeScript interface
- [ ] Create preferencesStore with persist
- [ ] Add loadPreferences action
- [ ] Add updatePreferences action
- [ ] Add setLanguage action
- [ ] Add setModel action

**Acceptance Criteria**:
- Preferences load from API on auth
- Changes persist to localStorage and API
- Language/model changes reflect immediately

**Dependencies**: Task 1.1

---

### Task 1.3: Vanity URL Routing
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Implement /u/:username/:slug routing

**Files to Modify**:
- `backend/app/main.py`
- `backend/app/api/public.py`

**Tasks**:
- [ ] Add /u/{username}/{slug} route handler
- [ ] Query user by username
- [ ] Query project by user_id + slug
- [ ] Return published page content
- [ ] Return 404 for not found
- [ ] Add 301 redirect from /p/:id to vanity URL

**Acceptance Criteria**:
- /u/john/my-project loads project
- Invalid username returns 404
- /p/abc123 redirects to /u/john/my-project
- Existing /p/:public_id/:slug still works

**Dependencies**: Task 0.6

---

### Task 1.4: Language Switcher Component
**Priority**: 🟡 P1 | **Complexity**: S | **Owner**: Frontend

**Description**: Create language switcher UI component

**Files to Create**:
- `frontend/src/components/common/LanguageSwitcher.tsx`

**Tasks**:
- [ ] Create dropdown with EN/中文 options
- [ ] Switch language changes URL prefix
- [ ] Persist choice to preferences
- [ ] Add to editor header and main nav

**Acceptance Criteria**:
- Clicking language switches URL (en ↔ zh)
- Choice saved and persists on reload
- i18n keys render correctly

**Dependencies**: Task 1.2

---

### Task 1.5: Apply i18n to Components
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Frontend

**Description**: Replace hardcoded strings with translation keys

**Files to Modify**:
- `frontend/src/components/chat/ChatPanel.tsx`
- `frontend/src/components/editor/PublishButton.tsx`
- `frontend/src/pages/EditorPage.tsx`
- `frontend/src/pages/CreatePage.tsx`

**Tasks**:
- [ ] Replace hardcoded strings in ChatPanel
- [ ] Replace hardcoded strings in PublishButton
- [ ] Replace hardcoded strings in EditorPage
- [ ] Replace hardcoded strings in CreatePage
- [ ] Test both languages render correctly

**Acceptance Criteria**:
- No hardcoded English strings in UI
- Chinese translations display correctly
- Missing keys show fallback

**Dependencies**: Task 1.4

---

## Phase 2: A/B Testing (Weeks 3-4)

### Task 2.1: Experiments Pydantic Models
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Create Pydantic schemas for experiment API

**Files to Create**:
- `backend/app/models/experiment.py`

**Tasks**:
- [ ] Create ConversionGoal model
- [ ] Create VariantCreate/Response models
- [ ] Create ExperimentCreate/Response models
- [ ] Create ExperimentResult model
- [ ] Add validation (traffic split sums to 100)
- [ ] Add validation (exactly one control variant)

**Acceptance Criteria**:
- Pydantic validates all constraints
- Invalid traffic split raises ValidationError
- Serialization works for API responses

**Dependencies**: Task 0.6

---

### Task 2.2: Traffic Splitting Service
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Implement deterministic visitor-to-variant allocation

**Files to Create**:
- `backend/app/services/experiment_service.py`

**Tasks**:
- [ ] Implement hash-based allocation
- [ ] Ensure same visitor gets same variant
- [ ] Handle traffic split percentages
- [ ] Add unit tests for determinism
- [ ] Document algorithm

**Acceptance Criteria**:
- Same visitor_id always gets same variant
- Traffic splits match percentages
- Unit tests pass 100% determinism

**Dependencies**: Task 0.6

---

### Task 2.3: Experiments CRUD API
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Backend

**Description**: Create experiments API endpoints

**Files to Create**:
- `backend/app/api/experiments.py`

**Tasks**:
- [ ] POST /api/projects/{project_id}/experiments
- [ ] GET /api/projects/{project_id}/experiments
- [ ] GET /api/experiments/{experiment_id}
- [ ] PATCH /api/experiments/{experiment_id}
- [ ] DELETE /api/experiments/{experiment_id}
- [ ] Add ownership verification to all endpoints
- [ ] Add audit logging for status changes

**Acceptance Criteria**:
- All CRUD operations work
- Only project owner can access
- Audit log records all changes
- 404 for non-existent experiments

**Dependencies**: Tasks 2.1, 2.2

---

### Task 2.4: Experiment Control API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Add start/pause/end endpoints

**Files to Modify**:
- `backend/app/api/experiments.py`

**Tasks**:
- [ ] POST /api/experiments/{experiment_id}/start
- [ ] POST /api/experiments/{experiment_id}/pause
- [ ] POST /api/experiments/{experiment_id}/complete
- [ ] Validate status transitions
- [ ] Set start_date/end_date appropriately
- [ ] Trigger audit log entries

**Acceptance Criteria**:
- Can only start from draft
- Can pause/resume running experiments
- Can complete running/paused experiments
- Invalid transitions return 400

**Dependencies**: Task 2.3

---

### Task 2.5: Variant Assignment API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Public endpoint for variant assignment

**Files to Modify**:
- `backend/app/api/experiments.py`

**Tasks**:
- [ ] POST /api/experiments/{experiment_id}/assign (no auth)
- [ ] Generate visitor_id if not provided
- [ ] Check if existing assignment exists
- [ ] Return deterministic variant if not
- [ ] Store assignment in database
- [ ] Rate limit (10 req/min per IP)
- [ ] Return 404 for non-running experiments

**Acceptance Criteria**:
- Same visitor always gets same variant
- Assignments persist across requests
- Rate limiting enforced
- Silent fail for invalid experiments (security)

**Dependencies**: Tasks 2.2, 2.4

---

### Task 2.6: Statistical Analysis Service
**Priority**: 🟡 P1 | **Complexity**: L | **Owner**: Backend

**Description**: Implement Z-test for conversion rates

**Files to Create**:
- `backend/app/services/statistics_service.py`

**Tasks**:
- [ ] Implement Z-test for proportions
- [ ] Calculate confidence interval
- [ ] Calculate required sample size
- [ ] Determine statistical significance
- [ ] Add tests with known values

**Acceptance Criteria**:
- Z-test matches standard calculators
- Confidence >= 95% marked as significant
- Sample size warning when < minimum

**Dependencies**: None (pure math)

---

### Task 2.7: Experiment Results API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Add results calculation endpoint

**Files to Modify**:
- `backend/app/api/experiments.py`

**Tasks**:
- [ ] GET /api/experiments/{experiment_id}/results
- [ ] Aggregate visitor counts by variant
- [ ] Aggregate conversion counts by variant
- [ ] Calculate conversion rates
- [ ] Call statistical service for confidence
- [ ] Return winner if significant

**Acceptance Criteria**:
- Results match raw event counts
- Confidence calculated correctly
- Winner declared when p < 0.05
- Cached for performance (5min TTL)

**Dependencies**: Tasks 2.5, 2.6

---

### Task 2.8: Conversion Tracking Integration
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Track experiment conversions in analytics

**Files to Modify**:
- `backend/app/api/analytics.py`
- `backend/app/api/analytics_advanced.py`

**Tasks**:
- [ ] Extend TrackEventRequest with experiment fields
- [ ] Store experiment_id, variant_id with events
- [ ] Update experiment_results on conversion
- [ ] Add conversion goal validation
- [ ] Deduplicate conversions per visitor

**Acceptance Criteria**:
- Conversions attributed to correct variant
- One visitor = one conversion per experiment
- Goals match experiment configuration

**Dependencies**: Tasks 2.5, 2.7

---

### Task 2.9: Experiment Types
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Create TypeScript types for experiments

**Files to Create**:
- `frontend/src/types/experiment.ts`

**Tasks**:
- [ ] Define Experiment interface
- [ ] Define Variant interface
- [ ] Define ConversionGoal interface
- [ ] Define ExperimentResult interface
- [ ] Define CreateExperimentRequest interface
- [ ] Export all types

**Acceptance Criteria**:
- Types match backend Pydantic models
- No implicit 'any' types
- Used by components without errors

**Dependencies**: Task 2.1

---

### Task 2.10: Experiment Store
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Create Zustand store for experiments

**Files to Create**:
- `frontend/src/stores/experimentStore.ts`

**Tasks**:
- [ ] Define ExperimentState interface
- [ ] Add experiments array
- [ ] Add currentExperiment state
- [ ] Implement loadExperiments action
- [ ] Implement createExperiment action
- [ ] Implement updateExperiment action
- [ ] Implement deleteExperiment action
- [ ] Implement start/pause/end actions
- [ ] Implement loadResults action
- [ ] Handle errors gracefully

**Acceptance Criteria**:
- Can list experiments for project
- Can create new experiment
- Can start/pause/end experiments
- Results load and display
- Errors stored in state

**Dependencies**: Task 2.9

---

### Task 2.11: Experiment List Component
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Create experiment list UI

**Files to Create**:
- `frontend/src/components/experiment/ExperimentList.tsx`
- `frontend/src/components/experiment/ExperimentCard.tsx`

**Tasks**:
- [ ] Create list view with cards
- [ ] Show status badge (draft/running/paused/completed)
- [ ] Show variant count and traffic split
- [ ] Show conversion goal summary
- [ ] Add quick action buttons
- [ ] Add "New Experiment" button
- [ ] Handle empty state

**Acceptance Criteria**:
- All experiments for project displayed
- Status badges use correct colors
- Clicking card navigates to detail
- Empty state shows helpful message

**Dependencies**: Task 2.10

---

### Task 2.12: Experiment Wizard
**Priority**: 🔴 P0 | **Complexity**: XL | **Owner**: Frontend

**Description**: Multi-step experiment creation wizard

**Files to Create**:
- `frontend/src/components/experiment/ExperimentWizard.tsx`
- `frontend/src/components/experiment/StepVariants.tsx`
- `frontend/src/components/experiment/StepTrafficSplit.tsx`
- `frontend/src/components/experiment/StepGoal.tsx`
- `frontend/src/components/experiment/StepReview.tsx`

**Tasks**:
- [ ] Create wizard with 4 steps
- [ ] Step 1: Define variants (control + treatments)
- [ ] Step 2: Set traffic split with sliders
- [ ] Step 3: Configure conversion goal
- [ ] Step 4: Review and launch
- [ ] Add progress indicator
- [ ] Validate each step before proceeding
- [ ] Create experiment on submit

**Acceptance Criteria**:
- Can select existing snapshot for each variant
- Traffic split sliders sum to 100%
- Goal type determines available fields
- Review shows all configuration
- Creates experiment on final submit

**Dependencies**: Tasks 2.10, 2.11

---

### Task 2.13: Experiment Detail View
**Priority**: 🔴 P0 | **Complexity**: XL | **Owner**: Frontend

**Description**: Detailed experiment view with results

**Files to Create**:
- `frontend/src/components/experiment/ExperimentDetail.tsx`
- `frontend/src/components/experiment/VariantComparison.tsx`
- `frontend/src/components/experiment/ResultsDashboard.tsx`
- `frontend/src/components/experiment/TrafficSplitDisplay.tsx`

**Tasks**:
- [ ] Show experiment header with controls
- [ ] Side-by-side variant comparison
- [ ] Results table with metrics
- [ ] Statistical confidence indicator
- [ ] Sample size progress bar
- [ ] Declare winner button
- [ ] Real-time results refresh

**Acceptance Criteria**:
- Variant content previews side-by-side
- Conversion rates display with %
- Confidence shows as progress bar
- Sample size warning when < required
- Can declare winner when significant

**Dependencies**: Tasks 2.10, 2.12

---

### Task 2.14: Published Page Experiment Integration
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Inject experiment variant into published pages

**Files to Modify**:
- `backend/app/services/publish_service.py`

**Tasks**:
- [ ] Add experiment variant lookup in publish flow
- [ ] Inject variant content based on assignment
- [ ] Add experiment metadata to page
- [ ] Update zaoya-runtime.js with variant tracking
- [ ] Test variant serving

**Acceptance Criteria**:
- Published pages show correct variant
- Visitor cookie set for consistency
- zaoya-runtime.js tracks variant
- Conversion events include variant data

**Dependencies**: Tasks 2.5, 2.8

---

## Phase 3: Advanced Analytics (Week 5)

### Task 3.1: Enhanced Event Tracking
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Add session tracking, UTM, device, geo to events

**Files to Modify**:
- `backend/app/api/analytics.py`
- `backend/app/api/analytics_advanced.py` (new)

**Tasks**:
- [ ] Extend TrackEventRequest with context fields
- [ ] Add session_id generation
- [ ] Extract UTM parameters
- [ ] Detect device/browser from user-agent
- [ ] Add geolocation (country from IP)
- [ ] Create or update analytics_sessions
- [ ] Batch event inserts for performance

**Acceptance Criteria**:
- Sessions created on first event
- UTM params captured and stored
- Device detection works (mobile/desktop)
- Country detected from IP
- Events query efficiently

**Dependencies**: Task 0.1, 0.6

---

### Task 3.2: Funnel API
**Priority**: 🟡 P1 | **Complexity**: L | **Owner**: Backend

**Description**: Funnel creation and calculation

**Files to Create**:
- `backend/app/api/analytics_advanced.py`

**Tasks**:
- [ ] POST /api/projects/{project_id}/funnels
- [ ] GET /api/projects/{project_id}/funnels
- [ ] GET /api/funnels/{funnel_id}/results
- [ ] Implement funnel calculation query
- [ ] Calculate drop-off between steps
- [ ] Support date range filtering

**Acceptance Criteria**:
- Can create funnel with multiple steps
- Results show visitors per step
- Drop-off % calculated correctly
- Overall conversion rate accurate

**Dependencies**: Task 3.1

---

### Task 3.3: Cohort Analysis API
**Priority**: 🟡 P1 | **Complexity**: XL | **Owner**: Backend

**Description**: Retention cohort calculation

**Files to Modify**:
- `backend/app/api/analytics_advanced.py`
- `backend/app/services/cohort_service.py` (new)

**Tasks**:
- [ ] GET /api/projects/{project_id}/cohorts/retention
- [ ] Implement cohort grouping logic
- [ ] Calculate period-over-period retention
- [ ] Return cohort table data
- [ ] Support day/week/month intervals

**Acceptance Criteria**:
- Cohorts grouped by first visit date
- Retention % calculated per period
- Table format matches spec
- Performance acceptable (<5s for 10K cohorts)

**Dependencies**: Task 3.1

---

### Task 3.4: Attribution API
**Priority**: 🟢 P2 | **Complexity**: M | **Owner**: Backend

**Description**: Multi-touch attribution calculation

**Files to Modify**:
- `backend/app/api/analytics_advanced.py`

**Tasks**:
- [ ] GET /api/projects/{project_id}/attribution
- [ ] Implement first-touch attribution
- [ ] Implement last-touch attribution
- [ ] Implement linear attribution
- [ ] Return channel breakdown

**Acceptance Criteria**:
- First touch credits first source
- Last touch credits last source
- Linear splits equally
- Results sum to 100%

**Dependencies**: Task 3.1

---

### Task 3.5: Heatmap Tracking
**Priority**: 🟢 P2 | **Complexity**: M | **Owner**: Backend

**Description**: Click coordinate tracking for heatmaps

**Files to Create**:
- `backend/app/api/analytics_advanced.py`

**Tasks**:
- [ ] POST /api/track/{public_id}/click (no auth)
- [ ] Store x, y as % of viewport
- [ ] Store element tag and text
- [ ] Aggregate clicks by coordinate
- [ ] Return aggregated heatmap data

**Acceptance Criteria**:
- Click coordinates stored accurately
- Query returns heat map grid
- Performance acceptable (<3s for 10K clicks)

**Dependencies**: Task 0.1

---

### Task 3.6: Analytics Dashboard API
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Backend

**Description**: Enhanced dashboard with KPIs and breakdowns

**Files to Modify**:
- `backend/app/api/analytics.py`

**Tasks**:
- [ ] Extend GET /api/projects/{project_id}/analytics
- [ ] Add KPIs (bounce rate, avg duration)
- [ ] Add top pages breakdown
- [ ] Add traffic sources breakdown
- [ ] Add device breakdown
- [ ] Add geographic breakdown
- [ ] Add real-time visitors count

**Acceptance Criteria**:
- All KPIs calculated from raw events
- Breakdowns return top 10 items
- Real-time count accurate within 5min
- Query performance <3s for 30-day range

**Dependencies**: Task 3.1

---

### Task 3.7: Analytics Types
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Extended analytics TypeScript types

**Files to Modify**:
- `frontend/src/types/analytics.ts`

**Tasks**:
- [ ] Define AnalyticsDashboard interface
- [ ] Define Funnel interface
- [ ] Define FunnelResult interface
- [ ] Define CohortResult interface
- [ ] Define HeatmapData interface
- [ ] Define AttributionResult interface

**Acceptance Criteria**:
- Types match API responses
- No 'any' types
- Used by components

**Dependencies**: Task 3.6

---

### Task 3.8: Analytics Store
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Enhanced analytics state management

**Files to Create**:
- `frontend/src/stores/analyticsStore.ts`

**Tasks**:
- [ ] Extend with dashboard data
- [ ] Add funnels state
- [ ] Add cohort state
- [ ] Add heatmap state
- [ ] Add attribution state
- [ ] Add date range state
- [ ] Implement loadDashboard action
- [ ] Implement createFunnel action
- [ ] Implement calculateFunnel action
- [ ] Implement loadCohorts action

**Acceptance Criteria**:
- Dashboard loads with trends
- Can create and calculate funnels
- Cohort data renders
- Date range changes reload data

**Dependencies**: Task 3.7

---

### Task 3.9: Advanced Analytics Dashboard
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Frontend

**Description**: Enhanced analytics dashboard UI

**Files to Create**:
- `frontend/src/components/analytics/AdvancedAnalyticsDashboard.tsx`
- `frontend/src/components/analytics/KPICard.tsx` (enhanced)
- `frontend/src/components/analytics/TrafficChart.tsx` (new)
- `frontend/src/components/analytics/DateRangePicker.tsx` (new)
- `frontend/src/components/analytics/TopPages.tsx` (new)
- `frontend/src/components/analytics/TrafficSources.tsx` (new)

**Tasks**:
- [ ] KPI cards with trend indicators
- [ ] Traffic over time chart
- [ ] Top pages table with %
- [ ] Traffic sources with visual bars
- [ ] Device breakdown pie chart
- [ ] Date range picker with presets
- [ ] Real-time visitors widget

**Acceptance Criteria**:
- All KPIs display with trends
- Chart renders time-series data
- Breakdowns show % of total
- Date range changes refresh data
- Real-time count updates

**Dependencies**: Tasks 3.8

---

### Task 3.10: Funnel Builder UI
**Priority**: 🟡 P1 | **Complexity**: XL | **Owner**: Frontend

**Description**: Funnel creation and visualization

**Files to Create**:
- `frontend/src/components/analytics/FunnelBuilder.tsx`
- `frontend/src/components/analytics/FunnelVisualization.tsx`

**Tasks**:
- [ ] Funnel builder with step wizard
- [ ] Select event type per step
- [ ] Add filters per step
- [ ] Reorder steps with drag-drop
- [ ] Funnel visualization component
- [ ] Show visitor counts per step
- [ ] Show drop-off % between steps
- [ ] Highlight biggest drop-off

**Acceptance Criteria**:
- Can create multi-step funnel
- Steps reorder correctly
- Visualization shows conversion flow
- Drop-off clearly visible

**Dependencies**: Tasks 3.8, 3.9

---

### Task 3.11: Client-Side Analytics Integration
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Enhanced tracking in published pages

**Files to Modify**:
- `frontend/src/components/preview/PhoneFrame.tsx` (for preview)
- `backend/app/services/publish_service.py` (for published)

**Tasks**:
- [ ] Inject enhanced tracking script
- [ ] Track page views with context
- [ ] Track clicks with element data
- [ ] Track scroll depth milestones
- [ ] Track time on page
- [ ] Batch events before sending
- [ ] Handle experiment variants

**Acceptance Criteria**:
- All event types tracked
- Context included (UTM, device)
- Batch sending reduces requests
- Experiment data included

**Dependencies**: Tasks 2.14, 3.1

---

## Phase 4: AI Image Generation (Week 6)

### Task 4.1: Image Service
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Backend

**Description**: DALL-E integration for image generation

**Files to Create**:
- `backend/app/services/image_service.py`

**Tasks**:
- [ ] Implement DALL-E 3 API client
- [ ] Add prompt optimization
- [ ] Implement retry logic (3 attempts)
- [ ] Add error handling
- [ ] Add style prompt templates
- [ ] Implement async generation
- [ ] Store generated image metadata

**Acceptance Criteria**:
- DALL-E API integration works
- Styles apply correct prompts
- Retries on transient failures
- Images stored with metadata

**Dependencies**: Task 0.4

---

### Task 4.2: Asset Storage
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Configure CDN for image storage

**Tasks**:
- [ ] Set up Cloudflare R2 or S3 bucket
- [ ] Add upload handler
- [ ] Generate thumbnails on upload
- [ ] Return public URLs
- [ ] Implement cleanup for deleted assets
- [ ] Add storage usage tracking

**Acceptance Criteria**:
- Images upload successfully
- Thumbnails generated automatically
- Public URLs accessible
- Storage tracked per user

**Dependencies**: Task 0.4

---

### Task 4.3: Credits Service
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Credit balance checking and deduction

**Files to Create**:
- `backend/app/services/credit_service.py`

**Tasks**:
- [ ] Implement check_balance function
- [ ] Implement deduct_credit function
- [ ] Add transaction logging
- [ ] Handle race conditions
- [ ] Add monthly reset job
- [ ] Calculate plan limits

**Acceptance Criteria**:
- Balance checked before generation
- Credits deducted atomically
- Transactions logged
- Monthly reset works

**Dependencies**: Task 0.3

---

### Task 4.4: Images API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Image generation and asset management endpoints

**Files to Create**:
- `backend/app/api/images.py`

**Tasks**:
- [ ] POST /api/images/generate
- [ ] GET /api/images/providers
- [ ] GET /api/assets
- [ ] POST /api/assets/upload
- [ ] DELETE /api/assets/{asset_id}
- [ ] GET /api/projects/{project_id}/assets
- [ ] Add credit checks to generation
- [ ] Rate limit generation (5/min)

**Acceptance Criteria**:
- Generation requires credits
- Insufficient credits returns 402
- Assets list user's images
- Upload stores file correctly
- Rate limiting enforced

**Dependencies**: Tasks 4.1, 4.2, 4.3

---

### Task 4.5: Asset Types
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Asset and image generation types

**Files to Create**:
- `frontend/src/types/asset.ts`

**Tasks**:
- [ ] Define Asset interface
- [ ] Define ImageGenerationRequest interface
- [ ] Define GeneratedImage interface
- [ ] Define UserCredits interface
- [ ] Define CreditTransaction interface

**Acceptance Criteria**:
- Types match API responses
- Used by components

**Dependencies**: Task 4.4

---

### Task 4.6: Asset Store
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Asset library state management

**Files to Create**:
- `frontend/src/stores/assetStore.ts`

**Tasks**:
- [ ] Define AssetState interface
- [ ] Add assets array
- [ ] Add credits state
- [ ] Implement loadAssets action
- [ ] Implement uploadAsset action
- [ ] Implement generateImage action
- [ ] Implement loadCredits action
- [ ] Implement deleteAsset action
- [ ] Add search/filter logic

**Acceptance Criteria**:
- Assets load from API
- Uploads work with progress
- Generation checks credits first
- Search filters assets correctly

**Dependencies**: Task 4.5

---

### Task 4.7: Image Generator Modal
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Frontend

**Description**: AI image generation UI

**Files to Create**:
- `frontend/src/components/asset/ImageGeneratorModal.tsx`
- `frontend/src/components/asset/StyleSelector.tsx`
- `frontend/src/components/asset/CreditDisplay.tsx`

**Tasks**:
- [ ] Prompt textarea with examples
- [ ] Style selector (photo, illustration, abstract)
- [ ] Size selector with costs
- [ ] Credit balance display
- [ ] Generate button with loading state
- [ ] Generated image preview
- [ ] Use/Regenerate buttons
- [ ] Upgrade prompt when insufficient credits

**Acceptance Criteria**:
- Prompt accepts text input
- Styles apply visual selection
- Sizes show correct costs
- Loading state during generation
- Generated image displays
- Insufficient credits shows upgrade

**Dependencies**: Tasks 4.6

---

### Task 4.8: Asset Library UI
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Asset grid and management interface

**Files to Create**:
- `frontend/src/components/asset/AssetLibrary.tsx`
- `frontend/src/components/asset/AssetGrid.tsx`
- `frontend/src/components/asset/AssetCard.tsx`
- `frontend/src/components/asset/UploadZone.tsx`

**Tasks**:
- [ ] Responsive grid layout
- [ ] Asset cards with thumbnails
- [ ] Search by filename/prompt
- [ ] Filter by tags
- [ ] Drag-drop upload zone
- [ ] Delete confirmation
- [ ] Copy URL to clipboard
- [ ] Insert into page action

**Acceptance Criteria**:
- Assets display in grid
- Search filters in real-time
- Upload works with drag-drop
- Delete requires confirmation
- Copy URL works

**Dependencies**: Task 4.6

---

### Task 4.9: Editor Integration
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Frontend

**Description**: Add image generation to editor

**Files to Modify**:
- `frontend/src/pages/EditorPage.tsx`
- `frontend/src/components/preview/PreviewPanel.tsx`

**Tasks**:
- [ ] Add "Generate Image" button to toolbar
- [ ] Open ImageGeneratorModal on click
- [ ] Insert selected image into page
- [ ] Add image to recent assets
- [ ] Show credit usage

**Acceptance Criteria**:
- Button visible in editor
- Generation modal opens
- Generated image inserts into page
- Credits update after generation

**Dependencies**: Tasks 4.7, 4.8

---

## Phase 5: Premium Tier (Week 7)

### Task 5.1: Subscription Plans Seed
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Backend

**Description**: Seed subscription plans in database

**Files to Modify**:
- `backend/alembic/versions/YYYYMMDD_XXXX_subscriptions_tables.py`

**Tasks**:
- [ ] Define Free plan limits
- [ ] Define Pro plan limits
- [ ] Define Team plan limits (inactive)
- [ ] Add Stripe price IDs (optional)
- [ ] Seed data in migration

**Acceptance Criteria**:
- All 3 plans exist in database
- Limits match spec
- Can query plans via API

**Dependencies**: Task 0.5

---

### Task 5.2: Feature Gate Middleware
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Server-side feature limit enforcement

**Files to Create**:
- `backend/app/middleware/feature_gate.py`

**Tasks**:
- [ ] Create require_feature decorator
- [ ] Check user's subscription plan
- [ ] Enforce usage limits
- [ ] Return 403 when exceeded
- [ ] Include upgrade URL in response
- [ ] Add tests for all features

**Acceptance Criteria**:
- Free users blocked from Pro features
- Limit checks work (projects, pages, etc.)
- 403 includes helpful message
- Admin bypass works

**Dependencies**: Task 5.1

---

### Task 5.3: Subscription API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Subscription management endpoints

**Files to Create**:
- `backend/app/api/subscriptions.py`

**Tasks**:
- [ ] GET /api/subscription (current)
- [ ] GET /api/subscription/plans (public)
- [ ] POST /api/subscription/checkout (mock)
- [ ] POST /api/subscription/cancel (mock)
- [ ] POST /api/subscription/portal (mock)
- [ ] POST /api/webhooks/stripe (mock)

**Acceptance Criteria**:
- Current subscription returns plan
- Plans list all 3 tiers
- Checkout returns mock URL
- Webhook accepts test events
- All endpoints require auth except plans/webhook

**Dependencies**: Tasks 5.1, 5.2

---

### Task 5.4: Credits API
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Credit balance and history endpoints

**Files to Create**:
- `backend/app/api/credits.py`

**Tasks**:
- [ ] GET /api/credits/balance
- [ ] GET /api/credits/history
- [ ] POST /api/credits/purchase (mock)
- [ ] Add monthly refresh logic
- [ ] Add transaction logging

**Acceptance Criteria**:
- Balance returns current credits
- History shows all transactions
- Purchase returns mock checkout
- Monthly refresh adds plan credits

**Dependencies**: Tasks 4.3, 5.3

---

### Task 5.5: Subscription Types
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Subscription TypeScript types

**Files to Create**:
- `frontend/src/types/subscription.ts`

**Tasks**:
- [ ] Define SubscriptionPlan interface
- [ ] Define Subscription interface
- [ ] Define PlanLimits interface
- [ ] Define FeatureCheckResult interface
- [ ] Define Invoice interface

**Acceptance Criteria**:
- Types match backend models
- Used by components

**Dependencies**: Task 5.3

---

### Task 5.6: Subscription Store
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Subscription state management

**Files to Create**:
- `frontend/src/stores/subscriptionStore.ts`

**Tasks**:
- [ ] Define SubscriptionState interface
- [ ] Add subscription state
- [ ] Add plans state
- [ ] Implement loadSubscription action
- [ ] Implement loadPlans action
- [ ] Implement checkFeature function
- [ ] Implement createCheckoutSession action
- [ ] Add upgrade modal state

**Acceptance Criteria**:
- Subscription loads on auth
- Plans cached locally
- Feature check returns correct result
- Checkout session created

**Dependencies**: Task 5.5

---

### Task 5.7: Feature Gate Hook
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Client-side feature gating

**Files to Create**:
- `frontend/src/hooks/useFeatureGate.ts`

**Tasks**:
- [ ] Create useFeatureGate hook
- [ ] Check feature against subscription
- [ ] Return allowed/upgradeRequired
- [ ] Provide upgrade trigger
- [ ] Test with all features

**Acceptance Criteria**:
- Hook returns correct gate status
- Free users see upgrade prompts
- Pro users access features
- Limits enforced correctly

**Dependencies**: Task 5.6

---

### Task 5.8: Upgrade Prompt Component
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Contextual upgrade prompts

**Files to Create**:
- `frontend/src/components/subscription/UpgradePrompt.tsx`
- `frontend/src/components/subscription/UpgradeModal.tsx`

**Tasks**:
- [ ] Create inline upgrade prompt
- [ ] Create modal upgrade flow
- [ ] Show feature being unlocked
- [ ] Link to pricing page
- [ ] Handle plan selection
- [ ] Close on upgrade complete

**Acceptance Criteria**:
- Prompts show at limit points
- Modal shows plans comparison
- Checkout redirects to pricing
- State updates after upgrade

**Dependencies**: Tasks 5.6, 5.7

---

### Task 5.9: Pricing Page
**Priority**: 🔴 P0 | **Complexity**: L | **Owner**: Frontend

**Description**: Full pricing/upgrade page

**Files to Create**:
- `frontend/src/pages/PricingPage.tsx`
- `frontend/src/components/subscription/PricingPage.tsx`
- `frontend/src/components/subscription/PricingCard.tsx`
- `frontend/src/components/subscription/PlanComparison.tsx`

**Tasks**:
- [ ] Three plan cards (Free, Pro, Team)
- [ ] Monthly/yearly toggle with savings
- [ ] Feature comparison table
- [ ] Current plan indicator
- [ ] Upgrade CTA buttons
- [ ] FAQ section
- [ ] Enterprise contact CTA

**Acceptance Criteria**:
- All 3 plans display correctly
- Toggle switches prices
- Comparison shows features
- Upgrade buttons work
- Current plan highlighted
- FAQ expands/collapses

**Dependencies**: Tasks 5.6, 5.8

---

### Task 5.10: Apply Feature Gates
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Frontend

**Description**: Add gates to Pro features

**Files to Modify**:
- `frontend/src/pages/EditorPage.tsx`
- `frontend/src/pages/ExperimentsPage.tsx`
- `frontend/src/components/asset/ImageGeneratorModal.tsx`
- `frontend/src/components/analytics/AdvancedAnalyticsDashboard.tsx`

**Tasks**:
- [ ] Gate A/B testing (Pro+)
- [ ] Gate advanced analytics (Pro+)
- [ ] Gate custom domains (Pro+)
- [ ] Gate image generation (with credits)
- [ ] Gate project limits (3 for free)
- [ ] Show upgrade prompts at gates
- [ ] Allow access after upgrade

**Acceptance Criteria**:
- Free users blocked from Pro features
- Upgrade prompt shows context
- Pro users access features
- Limits count correctly

**Dependencies**: Tasks 5.7, 5.8

---

## Phase 6: Integration & Polish (Week 8)

### Task 6.1: Route Integration
**Priority**: 🔴 P0 | **Complexity**: S | **Owner**: Frontend

**Description**: Add all new routes to App.tsx

**Files to Modify**:
- `frontend/src/App.tsx`

**Tasks**:
- [ ] Add /editor/:projectId/experiments routes
- [ ] Add /pricing route
- [ ] Add /assets route
- [ ] Add experiments routes to locale wrapper
- [ ] Test navigation

**Acceptance Criteria**:
- All new routes accessible
- Locale prefix applied correctly
- 404 for invalid routes

**Dependencies**: All frontend tasks

---

### Task 6.2: i18n Keys Addition
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Frontend

**Description**: Add translation keys for all new features

**Files to Modify**:
- `frontend/src/i18n/locales/en.json`
- `frontend/src/i18n/locales/zh.json`

**Tasks**:
- [ ] Add experiments keys (en + zh)
- [ ] Add analytics keys (en + zh)
- [ ] Add assets keys (en + zh)
- [ ] Add subscription keys (en + zh)
- [ ] Verify all keys used

**Acceptance Criteria**:
- All new UI text translatable
- No hardcoded strings
- Chinese translations complete
- Missing keys show fallback

**Dependencies**: All frontend tasks

---

### Task 6.3: Error Handling
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Both

**Description**: Comprehensive error states

**Tasks**:
- [ ] Add error boundaries to React
- [ ] Show user-friendly error messages
- [ ] Add retry buttons where appropriate
- [ ] Log errors to console
- [ ] Handle network failures
- [ ] Handle rate limit errors

**Acceptance Criteria**:
- All errors have user-friendly messages
- Retry options available
- No unhandled exceptions
- Rate limits show countdown

**Dependencies**: All implementation tasks

---

### Task 6.4: Loading States
**Priority**: 🟡 P1 | **Complexity**: M | **Owner**: Frontend

**Description**: Loading indicators and skeletons

**Tasks**:
- [ ] Add skeletons for dashboard
- [ ] Add skeletons for experiment list
- [ ] Add skeletons for asset grid
- [ ] Add spinners for actions
- [ ] Show progress for uploads

**Acceptance Criteria**:
- Skeletons match content layout
- Spinners show for async actions
- Upload shows progress %
- No janky transitions

**Dependencies**: All frontend tasks

---

### Task 6.5: Performance Optimization
**Priority**: 🟡 P1 | **Complexity**: L | **Owner**: Both

**Description**: Optimize for performance

**Backend Tasks**:
- [ ] Add database query indexes
- [ ] Implement response caching
- [ ] Add pagination to lists
- [ ] Optimize analytics queries
- [ ] Add background aggregation

**Frontend Tasks**:
- [ ] Lazy load heavy components
- [ ] Virtualize long lists
- [ ] Debounce search inputs
- [ ] Cache API responses
- [ ] Optimize re-renders

**Acceptance Criteria**:
- Dashboard loads in <3s
- Experiment list loads in <1s
- Asset grid handles 1000+ items
- Analytics queries <5s for 30 days

**Dependencies**: All implementation tasks

---

### Task 6.6: Security Audit
**Priority**: 🔴 P0 | **Complexity**: M | **Owner**: Backend

**Description**: Security review and hardening

**Tasks**:
- [ ] Review all auth checks
- [ ] Verify ownership checks
- [ ] Test rate limiting
- [ ] Validate all inputs
- [ ] Check for XSS vulnerabilities
- [ ] Verify CSRF protection
- [ ] Audit webhook security

**Acceptance Criteria**:
- All endpoints require auth (except public)
- Ownership verified on mutations
- Rate limits enforced
- No XSS vectors found
- Webhook signatures verified

**Dependencies**: All backend tasks

---

### Task 6.7: End-to-End Testing
**Priority**: 🟡 P1 | **Complexity**: XL | **Owner**: QA

**Description**: E2E tests for critical paths

**Tasks**:
- [ ] Test experiment creation flow
- [ ] Test image generation flow
- [ ] Test upgrade flow
- [ ] Test analytics dashboard
- [ ] Test funnel creation
- [ ] Cross-browser testing

**Acceptance Criteria**:
- All critical paths pass
- Works in Chrome, Firefox, Safari
- Mobile responsive verified
- No console errors

**Dependencies**: All implementation tasks

---

## Task Dependencies Graph

```
Foundation (Week 1)
├── Task 0.1: Analytics Migration
├── Task 0.2: Experiments Migration
├── Task 0.3: Credits Migration
├── Task 0.4: Assets Migration
├── Task 0.5: Subscriptions Migration
└── Task 0.6: ORM Models (depends on 0.1-0.5)

Prerequisites (Week 2)
├── Task 1.1: Preferences API (depends on 0.6)
├── Task 1.2: Preferences Store (depends on 1.1)
├── Task 1.3: Vanity URLs (depends on 0.6)
├── Task 1.4: Language Switcher (depends on 1.2)
└── Task 1.5: Apply i18n (depends on 1.4)

Experiments (Weeks 3-4)
├── Task 2.1: Experiment Models (depends on 0.6)
├── Task 2.2: Traffic Service (depends on 0.6)
├── Task 2.3: Experiments API (depends on 2.1, 2.2)
├── Task 2.4: Control API (depends on 2.3)
├── Task 2.5: Assignment API (depends on 2.2, 2.4)
├── Task 2.6: Statistics Service
├── Task 2.7: Results API (depends on 2.5, 2.6)
├── Task 2.8: Conversion Tracking (depends on 2.5, 2.7)
├── Task 2.9: Experiment Types (depends on 2.1)
├── Task 2.10: Experiment Store (depends on 2.9)
├── Task 2.11: Experiment List (depends on 2.10)
├── Task 2.12: Experiment Wizard (depends on 2.10, 2.11)
├── Task 2.13: Experiment Detail (depends on 2.10, 2.12)
└── Task 2.14: Publish Integration (depends on 2.5, 2.8)

Analytics (Week 5)
├── Task 3.1: Enhanced Tracking (depends on 0.1, 0.6)
├── Task 3.2: Funnel API (depends on 3.1)
├── Task 3.3: Cohort API (depends on 3.1)
├── Task 3.4: Attribution API (depends on 3.1)
├── Task 3.5: Heatmap Tracking (depends on 0.1)
├── Task 3.6: Dashboard API (depends on 3.1)
├── Task 3.7: Analytics Types (depends on 3.6)
├── Task 3.8: Analytics Store (depends on 3.7)
├── Task 3.9: Dashboard UI (depends on 3.8)
├── Task 3.10: Funnel UI (depends on 3.8, 3.9)
└── Task 3.11: Client Integration (depends on 2.14, 3.1)

Images (Week 6)
├── Task 4.1: Image Service (depends on 0.4)
├── Task 4.2: Asset Storage (depends on 0.4)
├── Task 4.3: Credits Service (depends on 0.3)
├── Task 4.4: Images API (depends on 4.1, 4.2, 4.3)
├── Task 4.5: Asset Types (depends on 4.4)
├── Task 4.6: Asset Store (depends on 4.5)
├── Task 4.7: Generator Modal (depends on 4.6)
├── Task 4.8: Asset Library (depends on 4.6)
└── Task 4.9: Editor Integration (depends on 4.7, 4.8)

Subscriptions (Week 7)
├── Task 5.1: Plan Seed (depends on 0.5)
├── Task 5.2: Feature Gate (depends on 5.1)
├── Task 5.3: Subscription API (depends on 5.1, 5.2)
├── Task 5.4: Credits API (depends on 4.3, 5.3)
├── Task 5.5: Subscription Types (depends on 5.3)
├── Task 5.6: Subscription Store (depends on 5.5)
├── Task 5.7: Feature Gate Hook (depends on 5.6)
├── Task 5.8: Upgrade Prompt (depends on 5.6, 5.7)
├── Task 5.9: Pricing Page (depends on 5.6, 5.8)
└── Task 5.10: Apply Gates (depends on 5.7, 5.8)

Polish (Week 8)
├── Task 6.1: Routes (depends on all frontend)
├── Task 6.2: i18n (depends on all frontend)
├── Task 6.3: Error Handling (depends on all)
├── Task 6.4: Loading States (depends on all frontend)
├── Task 6.5: Performance (depends on all)
├── Task 6.6: Security (depends on all backend)
└── Task 6.7: E2E Tests (depends on all)
```

---

## Progress Tracking

Use this checklist to track overall progress:

### Foundation
- [ ] Task 0.1: Analytics Migration
- [ ] Task 0.2: Experiments Migration
- [ ] Task 0.3: Credits Migration
- [ ] Task 0.4: Assets Migration
- [ ] Task 0.5: Subscriptions Migration
- [ ] Task 0.6: ORM Models

### Prerequisites
- [ ] Task 1.1: Preferences API
- [ ] Task 1.2: Preferences Store
- [ ] Task 1.3: Vanity URLs
- [ ] Task 1.4: Language Switcher
- [ ] Task 1.5: Apply i18n

### Experiments
- [ ] Task 2.1-2.8: Backend
- [ ] Task 2.9-2.14: Frontend

### Analytics
- [ ] Task 3.1-3.6: Backend
- [ ] Task 3.7-3.11: Frontend

### Images
- [ ] Task 4.1-4.4: Backend
- [ ] Task 4.5-4.9: Frontend

### Subscriptions
- [ ] Task 5.1-5.4: Backend
- [ ] Task 5.5-5.10: Frontend

### Polish
- [ ] Task 6.1: Routes
- [ ] Task 6.2: i18n
- [ ] Task 6.3: Error Handling
- [ ] Task 6.4: Loading States
- [ ] Task 6.5: Performance
- [ ] Task 6.6: Security
- [ ] Task 6.7: E2E Tests

---

## Notes

1. **Weeks are estimates** - Actual duration may vary based on team size and experience
2. **Tasks can be parallelized** - Backend and frontend tasks can often run in parallel
3. **Dependencies matter** - Don't skip foundation tasks or later work will be blocked
4. **Test as you go** - Each task should include its own testing
5. **Document changes** - Update relevant docs as features are implemented

---

**Ready to start implementation! Begin with Task 0.1: Analytics Migration.**
