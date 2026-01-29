# Phase 6: Completion (Week 6)

**Focus**: Final features, quota enforcement, testing, and documentation.

---

## Overview

This phase completes the v5 implementation by adding version pinning, enforcing branch quotas, comprehensive testing, bug fixes, and documentation. It's the final sprint to ensure production readiness.

**Key Goals**:
- Complete version control features (pinning)
- Enforce system quotas (branches, versions)
- Comprehensive testing and quality assurance
- Production-ready documentation

---

## Prerequisites

- Phase 1-5 are complete
- All core features are implemented
- Beta testing has identified issues

---

## Detailed Tasks

### 6.1 Version Pinning (Max 3)

**Priority**: Medium

**Purpose**: Allow users to mark important versions as "pinned" to preserve full snapshots permanently.

**Pinning Rules**:
- Max 3 pinned versions per project
- Pinned versions always store full snapshot (never diff)
- Pins don't count toward normal version storage strategy
- Use cases: Milestone versions, published versions, key checkpoints

**Tasks**:
1. Add `is_pinned` column to versions table (already exists)
2. Implement pin API:
   ```
   POST /api/projects/{id}/versions/{version_id}/pin
   DELETE /api/projects/{id}/versions/{version_id}/pin
   ```
3. Enforce max 3 pinned limit
4. Update snapshot storage logic (pinned = always full)
5. Add pin UI (📌 icon in Version History)

**UI Changes**:
- Version History Panel shows 📌 for pinned versions
- Click 📌 to toggle pin status
- Warning when attempting to pin 4th version
- Pinned versions highlighted in UI

**Acceptance Criteria**:
- [ ] Can pin up to 3 versions
- [ ] Pinned versions store full snapshot
- [ ] Cannot pin more than 3 versions
- [ ] UI shows pin status clearly
- [ ] Pin/unpin API works correctly

### 6.2 Branch Quota Enforcement

**Priority**: High

**Quota Limits**:
| Tier | Max Branches per Project |
|------|--------------------------|
| Free | 3 |
| Paid | 3 (configurable) |

**Notes**:
- "main" branch is always included in the 3
- Each branch has independent version quota
- Cannot create new branch if quota reached
- Must delete branch before creating new one

**Tasks**:
1. Implement branch quota checking:
   ```
   GET /api/projects/{id}/branches/quota-status
   → Returns { used: 3, limit: 3, can_create: false }
   ```
2. Add quota enforcement in branch creation API
3. Update branch UI to show quota status
4. Add upgrade prompt when quota reached
5. Implement branch deletion (soft delete with 30-day retention)

**Branch Deletion** (from Phase 5 decisions):
- Move to trash (30-day retention)
- Can restore within 30 days
- Trashed branches don't count toward quota
- UI shows "Will be permanently deleted in X days"

**Acceptance Criteria**:
- [ ] Branch quota enforced at creation time
- [ ] Cannot exceed 3 branches
- [ ] Quota status visible in UI
- [ ] Upgrade prompt shown when at limit
- [ ] Branch deletion works with 30-day retention

### 6.3 Version Quota Enforcement

**Priority**: High

**Quota Limits**:
| Tier | Version Limit |
|------|---------------|
| Free | 5 versions |
| Paid | 50 versions |

**Soft Quota Strategy**:
- Allow continuation beyond quota with warning
- Mark as "soft quota exceeded"
- Auto-delete oldest non-pinned versions at 2x quota
- UI shows warning and guides cleanup

**Tasks**:
1. Implement version quota checking:
   ```
   GET /api/projects/{id}/versions/quota-status
   → Returns { used: 7, limit: 5, soft_limit: 10, status: 'warning' }
   ```
2. Add quota enforcement in version creation
3. Implement cleanup job for old versions
4. Update UI to show quota warnings
5. Add manual version deletion option

**Cleanup Logic**:
```python
if version_count > quota * 2:
    # Delete oldest non-pinned, non-full-snapshot versions
    candidates = versions.filter(
        is_pinned=False,
        snapshot_type='diff'
    ).order_by('created_at')
    delete_count = version_count - (quota * 2)
    candidates[:delete_count].delete()
```

**Acceptance Criteria**:
- [ ] Version quota enforced (soft limit)
- [ ] Warning shown when approaching limit
- [ ] Oldest versions auto-deleted at 2x limit
- [ ] Pinned versions never auto-deleted
- [ ] UI shows quota status clearly

### 6.4 Comprehensive Testing

**Priority**: Critical

**Testing Areas**:

**A. Unit Tests**
- Version system (creation, restoration, rollback)
- Branch isolation and switching
- Thumbnail generation (all 3 fallback tiers)
- CSP validation and simulation
- Quota enforcement logic

**B. Integration Tests**
- Full build pipeline (generate → validate → save → version)
- Publish simulation mode
- Chat streaming with SSE
- File API access control
- Version history navigation

**C. End-to-End Tests**
- New user onboarding flow
- Example project one-click generation
- Page-level rollback flow
- Branch creation and switching
- Publish with SEO/OG Image

**D. Performance Tests**
- Version creation with large projects
- Virtual scrolling with 100+ messages
- Thumbnail queue under load
- Concurrent branch editing

**E. Security Tests**
- Code access control (non-owner blocked)
- Directory traversal prevention
- CSP violation handling
- XSS prevention in generated code

**Tasks**:
1. Write unit tests (target: 80% coverage)
2. Create integration test suite
3. Set up E2E testing with Playwright
4. Run performance benchmarks
5. Conduct security audit
6. Fix identified bugs

**Acceptance Criteria**:
- [ ] Unit test coverage > 80%
- [ ] All integration tests pass
- [ ] E2E tests cover critical flows
- [ ] Performance benchmarks meet targets
- [ ] Security audit passed
- [ ] All critical bugs fixed

### 6.5 Bug Fixes

**Priority**: High

**Process**:
1. Collect bugs from beta testing
2. Triage by severity (critical/high/medium/low)
3. Fix critical bugs first
4. Create regression tests for fixes
5. Verify fixes in staging environment

**Common Bug Categories**:
- Edge cases in version restoration
- CSP violations in templates
- Thumbnail generation timeouts
- Chat scrolling issues
- Branch switching glitches

**Acceptance Criteria**:
- [ ] All critical bugs resolved
- [ ] High-priority bugs resolved
- [ ] Regression tests added
- [ ] No known blockers

### 6.6 Documentation

**Priority**: High

**Documentation Types**:

**A. User Documentation**
- Getting started guide
- Version control how-to
- Branch creation and management
- Troubleshooting common issues

**B. Developer Documentation**
- Architecture overview
- API documentation
- Database schema
- Deployment guide
- Contributing guidelines

**C. Operations Documentation**
- Monitoring setup
- Alert configuration
- Backup/restore procedures
- Incident response runbook

**Tasks**:
1. Write user guides for new features
2. Update API documentation
3. Create architecture diagrams
4. Document deployment process
5. Write troubleshooting guides
6. Create video tutorials (optional)

**Acceptance Criteria**:
- [ ] All new features documented
- [ ] API docs complete and accurate
- [ ] Deployment guide tested
- [ ] User guides reviewed by non-technical users
- [ ] Troubleshooting guide covers common issues

---

## Technical Considerations

### Pinned Version Storage
```sql
-- Pinned versions always store full snapshot
CREATE OR REPLACE FUNCTION should_store_full_snapshot(version) RETURNS boolean AS $$
BEGIN
  RETURN version.is_pinned OR
         version.is_one_of_last_3 OR
         version.validation_status = 'failed';
END;
$$ LANGUAGE plpgsql;
```

### Branch Quota Check
```python
async def can_create_branch(project_id: str) -> bool:
    tier = await get_user_tier(project_id)
    used = await count_branches(project_id)
    limit = BRANCH_LIMITS[tier]
    return used < limit
```

### Version Cleanup Job
```python
@app.scheduler(cron="0 2 * * *")  # 2 AM daily
async def cleanup_old_versions():
    for project in await get_all_projects():
        quota = get_version_quota(project)
        versions = await get_versions(project.id)
        if len(versions) > quota * 2:
            await delete_oldest_versions(versions, quota * 2)
```

---

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bug fixes introduce new issues | High | Comprehensive regression tests, code review |
| Quota enforcement frustrates users | Medium | Clear UI, upgrade prompts, soft limits |
| Documentation incomplete | Low | Technical writer review, user testing |
| Performance issues discovered | Medium | Load testing, optimization sprint |

---

## Estimated Scope

**Complexity**: Medium

**Effort Drivers**:
- Version pinning (1 day)
- Branch quota enforcement (1-2 days)
- Version quota enforcement (1-2 days)
- Comprehensive testing (3-4 days)
- Bug fixes (2-3 days)
- Documentation (2-3 days)

**Total Estimated Duration**: 1 week

---

## Dependencies

- **Internal**: Phase 1-5 complete
- **External**: None

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Critical bugs | 0 |
| Test coverage | > 80% |
| Documentation completeness | 100% of features |
| Performance regression | 0% |
| User-reported issues | < 5 per week |

---

## API Endpoints

```
POST /api/projects/{id}/versions/{version_id}/pin
DELETE /api/projects/{id}/versions/{version_id}/pin
GET /api/projects/{id}/branches/quota-status
GET /api/projects/{id}/versions/quota-status
POST /api/projects/{id}/branches/{branch_id}/delete
```

---

## Launch Checklist

- [ ] All features implemented and tested
- [ ] Documentation complete and reviewed
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Beta feedback incorporated
- [ ] Known issues documented
- [ ] Rollback plan prepared
- [ ] Monitoring and alerting configured
- [ ] Support team trained
- [ ] Marketing materials ready

---

## Notes

- This is the final phase of v5
- Focus on quality and stability
- Comprehensive testing is critical
- Documentation enables user success
- Quota enforcement requires clear communication
- Plan for post-launch monitoring and quick fixes

---

**Next Phase**: v5 Complete - Launch and Monitor
