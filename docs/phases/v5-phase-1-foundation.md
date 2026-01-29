# Phase 1: Foundation (Week 1)

**Focus**: Code visibility, CSP compliance, and architectural foundations for version control.

---

## Overview

This phase establishes the foundational infrastructure for v5's core features. It focuses on giving users visibility into their code while maintaining security, resolving critical technical debt around CSP compliance, and separating preview/publish rendering contexts.

**Key Goals**:
- Provide code visibility (read-only) to project owners
- Resolve Tailwind CDN vs CSP conflicts
- Establish separate rendering contexts for preview vs publish
- Set up access control boundaries

---

## Prerequisites

- v4 codebase is stable and deployed
- PostgreSQL database is available
- FastAPI backend is running
- Basic understanding of CSP (Content Security Policy)

---

## Detailed Tasks

### 1.1 Code Tab Implementation (Frontend)

**Priority**: High

**Tasks**:
1. Create `CodeTab` component in PreviewPanel
2. Integrate CodeMirror 6 for read-only code viewing
   - Syntax highlighting
   - Line numbers
   - Search functionality
3. Implement file tree component
   - Display pages/, components/, assets/ structure
   - Expandable/collapsible folders
4. Connect to backend file APIs

**API Endpoints Required**:
- `GET /api/projects/{id}/files?scope=draft|snapshot|published`
- `GET /api/projects/{id}/files/content?path=...&scope=...`

**Acceptance Criteria**:
- [ ] Can view project file list
- [ ] Clicking file opens content (stable)
- [ ] Syntax highlighting and line numbers work
- [ ] Search with highlight works

### 1.2 CSP vs Tailwind CDN Conflict Resolution

**Priority**: Critical

**Problem**: Page templates may include `https://cdn.tailwindcss.com` (external script), but published CSP uses `script-src 'self'`. Published pages will be blocked.

**Solution**: Inline Tailwind CSS + Runtime Helpers

**Tasks**:
1. Update AI system prompt to prohibit CDN links
2. Implement build pipeline changes:
   - Extract critical CSS from generated HTML
   - Inline CSS in `<style>` tags
   - Move runtime helpers to inlined script
3. Update validation rules to detect external Tailwind CDN
4. Add migration script for existing projects

**Acceptance Criteria**:
- [ ] AI no longer generates Tailwind CDN links
- [ ] Build pipeline inlines critical CSS
- [ ] Validation blocks external script references
- [ ] Existing projects are migrated

### 1.3 Preview/Publish Template Separation

**Priority**: High

**Context**: Different CSP requirements for editor preview vs production publish.

**Tasks**:
1. Create two separate HTML templates:
   - `preview_template.html` (loose CSP, allows dev tools)
   - `publish_template.html` (strict CSP headers)
2. Update rendering pipeline to use appropriate template
3. Add template metadata to database schema
4. Update preview iframe to use correct template

**Acceptance Criteria**:
- [ ] Preview uses loose CSP (allows development)
- [ ] Publish uses strict CSP (production-ready)
- [ ] Templates are version-controlled
- [ ] Preview-pubish consistency is maintained

### 1.4 Code Access Control (Owner Only)

**Priority**: High

**Security Requirement**: Code Tab is only visible to the project creator. Share links show published page only.

**Tasks**:
1. Implement ownership check in API:
   - `GET /api/projects/{id}/files` - verify `user_id == owner_id`
2. Add authentication middleware for code endpoints
3. Update frontend to hide Code Tab for non-owners
4. Add test cases for access control

**Data Model Updates**:
```sql
ALTER TABLE projects ADD COLUMN owner_id UUID NOT NULL;
```

**Acceptance Criteria**:
- [ ] Only project owner can view code
- [ ] Share links don't expose source code
- [ ] API returns 403 for unauthorized access
- [ ] Frontend hides Code Tab appropriately

---

## Technical Considerations

### CodeMirror 6 Integration
- Package size < 500KB
- Read-only mode configuration
- Performance with large files (>1000 lines)

### CSP Header Management
- Preview: `script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com`
- Publish: `script-src 'self'`
- FastAPI response headers configuration

### File Security
- Directory traversal prevention
- Path sanitization
- File size limits

### Database Schema
```sql
-- Code access control
ALTER TABLE projects ADD COLUMN owner_id UUID NOT NULL REFERENCES users(id);

-- File metadata (optional, for caching)
CREATE TABLE file_metadata (
  project_id UUID REFERENCES projects(id),
  file_path VARCHAR(500) PRIMARY KEY,
  checksum VARCHAR(64),
  updated_at TIMESTAMP
);
```

---

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| CodeMirror performance issues | Medium | Lazy loading, virtual scrolling for large files |
| CSP breaking existing projects | High | Migration script, validation warnings |
| Access control bypass | Critical | Comprehensive testing, security audit |
| Tailwind inlining increases size | Low | CSS minification, critical CSS extraction |

---

## Estimated Scope

**Complexity**: Medium

**Effort Drivers**:
- CodeMirror integration (2-3 days)
- CSP resolution (2-3 days)
- Template separation (1-2 days)
- Access control (1-2 days)

**Total Estimated Duration**: 1 week

---

## Dependencies

- Frontend: React, CodeMirror 6
- Backend: FastAPI, PostgreSQL
- External: None

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Code Tab load time | < 500ms for typical files |
| CSP violation rate | 0% in published pages |
| Access control failures | 0 (no unauthorized access) |
| Preview-publish consistency | 100% visual match |

---

## Notes

- This phase resolves the foundational technical debt that blocks other features
- Code Tab is a prerequisite for enhanced ValidationCard (can't jump to code otherwise)
- CSP resolution is required for Publish Simulation Mode (Phase 3)
- Access control protects commercial/confidential projects

---

**Next Phase**: Week 2 - Version System
