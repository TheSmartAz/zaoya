# Phase 2: Version System (Week 2)

**Focus**: Version control, history tracking, and rollback capabilities.

---

## Overview

This phase implements the core version control system, enabling users to track changes, view history, and rollback to previous versions. Each user message creates a version point, with efficient storage using mixed full snapshots and diffs.

**Key Goals**:
- Create a version for every user message/AI iteration
- Store versions efficiently (full snapshot + diffs)
- Enable version history browsing
- Support page-level rollback

---

## Prerequisites

- Phase 1 (Foundation) is complete
- Code Tab is functional
- Database schema is set up
- `diff-match-patch` library is available

---

## Detailed Tasks

### 2.1 Version Data Model

**Priority**: High

**Tasks**:
1. Create database tables:
   ```sql
   CREATE TABLE versions (
     id UUID PRIMARY KEY,
     project_id UUID REFERENCES projects(id),
     parent_version_id UUID REFERENCES versions(id),
     branch_id UUID REFERENCES branches(id),
     branch_label VARCHAR(50),  -- 'main', 'a', 'b'
     created_at TIMESTAMP DEFAULT NOW(),
     trigger_message_id UUID REFERENCES chat_messages(id),
     snapshot_id UUID REFERENCES snapshots(id),
     change_summary JSONB,
     validation_status VARCHAR(20),  -- 'passed', 'failed', 'pending'
     is_pinned BOOLEAN DEFAULT FALSE
   );
   ```
2. Create `version_diffs` table for diff storage
3. Create `snapshots` table for full snapshots
4. Add indexes for performance

**Acceptance Criteria**:
- [ ] Tables created with proper constraints
- [ ] Indexes optimize common queries
- [ ] Foreign key relationships work correctly

### 2.2 Version Summary in Chat

**Priority**: High

**Tasks**:
1. Create `VersionSummaryCard` component
2. Integrate with chat message flow
3. Calculate and display:
   - Files changed count
   - Lines added/deleted
   - Tasks completed
   - Brief description
4. Add action buttons: [查看预览] [查看代码]

**Change Summary Structure**:
```typescript
interface ChangeSummary {
  files_changed: number;
  lines_added: number;
  lines_deleted: number;
  tasks_completed: string[];
  description: string;
}
```

**Acceptance Criteria**:
- [ ] Each user message creates a version card
- [ ] Version card shows file/line counts
- [ ] Action buttons navigate correctly
- [ ] Cards flow naturally in chat

### 2.3 Version History Panel

**Priority**: High

**Tasks**:
1. Create `VersionHistoryPanel` component
2. Display version tree visualization:
   ```
   v3 ────● 2026-01-28 14:30 [预览] [代码] [📌]
         │  新增联系表单 (3 文件, +127 -23)

   v2 ────● 2026-01-28 14:15 [预览] [代码]
         │  优化移动端布局
               │
               └── Branch B ───● 2026-01-28 14:20
                      │  蓝色主题变体 (2 文件, +34 -12)
   ```
3. Implement actions per version:
   - [预览] - View version preview
   - [代码] - View files at version
   - [📌] - Pin version
   - [...] - More: rollback, branch, delete
4. Add filtering and search

**Acceptance Criteria**:
- [ ] Version history displays in tree structure
- [ ] Can navigate to any version's preview
- [ ] Can view code at any version
- [ ] Branch visualization works correctly

### 2.4 Mixed Snapshot Storage (Full + Diff)

**Priority**: High

**Storage Strategy**: Hybrid approach
- Full snapshots: Last 3 versions + user-pinned versions
- Diff storage: All other versions
- Library: `diff-match-patch`

**Tasks**:
1. Implement snapshot service:
   - Determine if version needs full snapshot or diff
   - Generate diffs using `diff-match-patch`
   - Store full snapshot or diff accordingly
2. Implement version restoration:
   - Find nearest full snapshot
   - Apply diffs sequentially
   - Return complete file set
3. Add cleanup job for old snapshots

**Algorithm**:
```
On version create:
  IF (is_pinned OR is_one_of_last_3_versions):
    store_full_snapshot()
  ELSE:
    diff = compute_diff(nearest_full_snapshot, current_state)
    store_diff(diff)
```

**Acceptance Criteria**:
- [ ] Full snapshots stored for last 3 versions
- [ ] Full snapshots stored for pinned versions
- [ ] Diffs stored for all other versions
- [ ] Version restoration works correctly
- [ ] Storage is efficient (< 50% of full snapshots)

### 2.5 Page-Level Rollback

**Priority**: High

**Tasks**:
1. Implement rollback API:
   ```
   POST /api/projects/{id}/versions/{version_id}/rollback
   Body: { page_ids: string[] }
   ```
2. Create rollback confirmation UI:
   - Show pages to be rolled back
   - Show change preview (diff stats)
   - Clear warning that new version will be created
3. Execute rollback in database transaction
4. Create new version after rollback

**Rollback Flow**:
1. User clicks "页面回滚" on version
2. Panel shows all pages with their versions
3. User selects page(s) to rollback
4. Confirm shows: "Rollback index.html from v7 to v5"
5. Draft updated, new version created

**Acceptance Criteria**:
- [ ] Can rollback individual pages
- [ ] Can rollback multiple pages at once
- [ ] Rollback creates new version
- [ ] Rollback is transactional (all-or-nothing)
- [ ] Other pages are preserved

---

## Technical Considerations

### Diff Generation
- Library: `diff-match-patch` (Python)
- Character-level diffs for accuracy
- Performance: < 100ms for typical files

### Storage Optimization
- JSONB compression in PostgreSQL
- Full snapshots: ~100KB per version
- Diffs: ~10KB per version
- Estimated storage: 1000 versions ≈ 50MB

### Version Quota Enforcement
- Free tier: 5 versions
- Paid tier: 50 versions
- Failed versions stored separately (don't count)
- Soft quota with warning before hard limit

### Database Performance
```sql
-- Indexes for common queries
CREATE INDEX idx_versions_project_created ON versions(project_id, created_at DESC);
CREATE INDEX idx_versions_branch ON versions(branch_id, created_at DESC);
CREATE INDEX idx_versions_trigger ON versions(trigger_message_id);
```

---

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Diff application fails | High | Test with edge cases, fallback to full snapshot |
| Storage growth unbounded | Medium | Implement cleanup job, enforce quotas |
| Rollback breaks project | High | Transactional updates, confirm UI |
| Performance with many versions | Medium | Indexes, pagination, lazy loading |

---

## Estimated Scope

**Complexity**: Medium-High

**Effort Drivers**:
- Data model design (1-2 days)
- Version summary integration (2-3 days)
- Version history panel (3-4 days)
- Mixed storage implementation (2-3 days)
- Rollback functionality (2-3 days)

**Total Estimated Duration**: 1 week

---

## Dependencies

- **Internal**: Phase 1 (Foundation)
- **Libraries**: `diff-match-patch`
- **Database**: PostgreSQL with JSONB support

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Version creation time | < 200ms |
| Version restoration time | < 500ms |
| Storage efficiency | > 70% reduction vs full snapshots |
| Rollback success rate | 100% (transactional) |

---

## API Endpoints

```
GET /api/projects/{id}/versions?branch_id=...
GET /api/projects/{id}/versions/{version_id}
POST /api/projects/{id}/versions/{version_id}/rollback
POST /api/projects/{id}/versions/{version_id}/pin
DELETE /api/projects/{id}/versions/{version_id}/pin
```

---

## Notes

- Failed versions are stored separately (don't count toward quota)
- Version creation is automatic after each user message
- Pinned versions always store full snapshot (max 3 pinned)
- Page-level rollback preserves other pages
- Branch isolation: each branch has independent version history

---

**Next Phase**: Week 3 - Reliability
