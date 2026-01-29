# Phase 3: Reliability (Week 3)

**Focus**: Preview-publish consistency, error handling, and recovery mechanisms.

---

## Overview

This phase focuses on making the preview trustworthy and production-aligned. By implementing Publish Simulation Mode and enhanced validation, users can trust that what they see is what will be published. Single-page retry and better error handling reduce friction when issues occur.

**Key Goals**:
- Make preview equivalent to publish (catch CSP issues early)
- Provide detailed, actionable error information
- Enable targeted recovery (retry single page, not full rebuild)
- Store failed versions for debugging

---

## Prerequisites

- Phase 1 (Foundation) is complete - CSP conflicts resolved
- Phase 2 (Version System) is complete - can track failed versions
- Preview/Publish template separation is implemented

---

## Detailed Tasks

### 3.1 Publish Simulation Mode

**Priority**: Critical

**Problem**: Current `srcdoc` iframe preview doesn't use real CSP headers, so it can't reproduce production issues.

**Solution**: Use `/p-sim/{project_id}/{page_slug}` - a real route with near-production HTML and CSP.

**Tasks**:
1. Create new backend endpoint:
   ```
   GET /p-sim/{project_id}/{page_slug}
   - Returns HTML with real CSP headers
   - Content from draft or snapshot
   - Served from same origin as production
   - Allows iframe embedding (differs from real publish)
   ```
2. Update preview iframe to use simulation mode
3. Add simulation report endpoint:
   ```
   GET /p-sim-report/{project_id}
   - CSP violations list
   - Resource loading issues (404, blocked, timeout)
   - Pass/fail status
   ```
4. Capture CSP violations via `report-uri` directive
5. Store violations in database for reporting

**Simulation vs Production**:
| Aspect | Simulation | Production |
|--------|------------|------------|
| CSP Headers | Real | Real |
| Content | Draft/Snapshot | Published |
| Frame Ancestors | Allows embedding | Blocks embedding |
| Origin | Same as main app | pages.zaoya.app |

**Acceptance Criteria**:
- [ ] Simulation mode uses real CSP headers
- [ ] Can reproduce CSP issues (blocked scripts/styles)
- [ ] Resource loading errors are reported
- [ ] Visual appearance matches production
- [ ] Forces resolution of Tailwind CDN conflict

### 3.2 Enhanced ValidationCard

**Priority**: High

**Enhanced ValidationError Structure**:
```typescript
interface ValidationError {
  ruleId: string;              // e.g., "csp-no-external-script"
  ruleCategory: 'csp' | 'js-security' | 'html-whitelist' | 'resource' | 'runtime';
  path: string;                // File path
  line?: number;               // Line number if applicable
  excerpt: string;             // Code snippet
  message: string;             // Human-readable
  suggestedFix: string;        // One-sentence fix
  severity: 'critical' | 'warning' | 'info';
}
```

**Tasks**:
1. Enhance validation error structure with path, line, excerpt
2. Update ValidationCard UI:
   - Group errors by severity
   - Show code excerpt for context
   - Display suggested fix
   - Add action buttons:
     - [查看代码] → jumps to Code Tab (file/line)
     - [修复此页面] → creates fix task
     - [重试此页面] → retries only failed page
     - [页面回滚] → opens rollback dialog
3. Implement error-to-code navigation
4. Add severity-based sorting (critical first)

**ValidationCard UI**:
```
┌─────────────────────────────────────┐
│ ❌ Page validation failed           │
├─────────────────────────────────────┤
│ Critical (2)                        │
│ • CSP violation                     │
│   pages/index.html:12               │
│   External script blocked           │
│   [View Code] [Fix This Page]       │
│                                     │
│ Warning (1)                         │
│ • Performance issue                 │
│   Large image file                  │
├─────────────────────────────────────┤
│ [Retry Page] [Rollback Page]        │
└─────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] ValidationCard shows path + line info
- [ ] Errors grouped by severity
- [ ] Code excerpt shown for context
- [ ] Clicking error jumps to Code Tab
- [ ] Clicking fix creates iteration task
- [ ] Clicking rollback opens Version History

### 3.3 Single-Page Retry

**Priority**: High

**Problem**: Currently, any failure requires a full project rebuild, which is slow and wasteful.

**Solution**: Re-execute only the failed page's pipeline.

**Tasks**:
1. Implement retry API:
   ```
   POST /api/projects/{id}/pages/{page_id}/retry
   ```
2. Re-execute pipeline for single page:
   - page_generate → validate → secure → save → thumbnail
3. Skip: unaffected pages, shared state
4. Update TaskBoardCard to show retry status
5. Add retry count tracking

**Retry Logic**:
```python
async def retry_page(project_id: str, page_id: str):
    # Re-run generation
    generated = await generate_page(project_id, page_id)

    # Validate
    validation = await validate_page(generated)

    if validation.passed:
        # Save and create version
        await save_page(project_id, page_id, generated)
        await create_version(project_id, page_id)
    else:
        # Store failed version separately
        await store_failed_version(project_id, page_id, validation)

    return validation
```

**Acceptance Criteria**:
- [ ] Failed page retry doesn't trigger full rebuild
- [ ] Unaffected pages are not modified
- [ ] Retry creates new version (for traceability)
- [ ] TaskBoardCard shows retry status

### 3.4 Failed Version Storage

**Priority**: Medium

**Requirement**: Failed versions must be stored separately (not counted toward quota) for debugging.

**Tasks**:
1. Create `failed_versions` table:
   ```sql
   CREATE TABLE failed_versions (
     id UUID PRIMARY KEY,
     project_id UUID REFERENCES projects(id),
     version_data JSONB,
     validation_errors JSONB,
     created_at TIMESTAMP DEFAULT NOW(),
     retry_of UUID REFERENCES failed_versions(id)
   );
   ```
2. Update version creation logic:
   - If validation fails, store in `failed_versions`
   - Link to original attempt if retry
3. Implement cleanup job (delete after 90 days)
4. Add UI to view failed versions (optional)

**Acceptance Criteria**:
- [ ] Failed versions stored separately
- [ ] Don't count toward user quota
- [ ] Can view retry chain
- [ ] Auto-cleanup after 90 days

---

## Technical Considerations

### CSP Violation Capture
```javascript
// In published/simulated pages
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; report-uri /api/csp-report">
```

Backend endpoint:
```python
@app.post("/api/csp-report")
async def receive_csp_report(report: CSPReport):
    # Parse and store violation
    await store_csp_violation(report)
    return {"status": "ok"}
```

### Simulation Report Structure
```typescript
interface SimulationReport {
  project_id: string;
  status: 'passed' | 'failed';
  csp_violations: CSPViolation[];
  resource_errors: ResourceError[];
  timestamp: string;
}
```

### Retry Idempotency
- Each retry creates new task_id
- Version history tracks `retry_of: original_task_id`
- Full audit trail maintained

---

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Simulation mode performance | Medium | Cache results, limit concurrent simulations |
| CSP report spam | Low | Rate limiting, deduplication |
| Retry loop (infinite failures) | Medium | Max retry limit (3), require manual intervention |
| Failed version storage growth | Low | 90-day auto-cleanup |

---

## Estimated Scope

**Complexity**: Medium

**Effort Drivers**:
- Publish simulation mode (2-3 days)
- Enhanced ValidationCard (2-3 days)
- Single-page retry (1-2 days)
- Failed version storage (1 day)

**Total Estimated Duration**: 1 week

---

## Dependencies

- **Internal**: Phase 1 (CSP resolution), Phase 2 (version system)
- **External**: None

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Preview-publish consistency | 100% visual match |
| CSP issues caught in simulation | 100% (before publish) |
| Single-page retry success rate | > 95% |
| Full rebuilds required | < 5% |

---

## API Endpoints

```
GET /p-sim/{project_id}/{page_slug}
GET /p-sim-report/{project_id}
POST /api/projects/{id}/pages/{page_id}/retry
POST /api/csp-report
```

---

## Preview Toolbar Enhancement

Add toggle between "Preview" and "Publish Simulation" mode:
- Preview: Fast, loose CSP (for development)
- Simulation: Real CSP, shows issues (for pre-publish check)

UI states:
- Preview mode: Normal badge
- Simulation mode: Warning badge + report panel

---

## Notes

- Publish Simulation Mode is the key to "Preview = Publish可信"
- Single-page retry dramatically improves UX for common failures
- Enhanced ValidationCard provides actionable error information
- Failed versions stored separately for debugging without penalizing users
- This phase significantly reduces friction in the build loop

---

**Next Phase**: Week 4 - Thumbnails + SEO
