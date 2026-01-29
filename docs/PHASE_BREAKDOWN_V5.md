# Zaoya v5 Phase Breakdown

**Version**: 5.2
**Status**: Draft - Ready for Implementation
**Updated**: 2026-01-29

---

## Overview

This document provides a comprehensive breakdown of Zaoya v5 into 6 sequential phases (weeks). Each phase builds on the previous ones, moving from foundational infrastructure through to production-ready polish.

**v5 Vision**: "Production-ready preview, version control, and A/B testing foundation."

---

## Phase Summary

| Phase | Focus | Duration | Complexity |
|-------|-------|----------|------------|
| [Phase 1: Foundation](./phases/v5-phase-1-foundation.md) | Code visibility, CSP compliance | Week 1 | Medium |
| [Phase 2: Version System](./phases/v5-phase-2-version-system.md) | Version control, history, rollback | Week 2 | Medium-High |
| [Phase 3: Reliability](./phases/v5-phase-3-reliability.md) | Preview-publish consistency, error handling | Week 3 | Medium |
| [Phase 4: Thumbnails + SEO](./phases/v5-phase-4-thumbnails-seo.md) | Image generation, social optimization | Week 4 | Medium |
| [Phase 5: Polish](./phases/v5-phase-5-polish.md) | UX improvements, examples, branching | Week 5 | Medium |
| [Phase 6: Completion](./phases/v5-phase-6-completion.md) | Testing, documentation, launch | Week 6 | Medium |

**Total Timeline**: 6 weeks

---

## Quick Reference

### Phase 1: Foundation
**Key Deliverables**:
- Code Tab with CodeMirror 6
- CSP vs Tailwind CDN resolution
- Preview/Publish template separation
- Code access control (owner only)

**Success Metrics**:
- Code Tab load time < 500ms
- CSP violation rate 0% in published pages
- Preview-publish consistency 100%

### Phase 2: Version System
**Key Deliverables**:
- Version data model with mixed storage (full + diff)
- Version summary cards in chat
- Version History Panel with tree visualization
- Page-level rollback functionality

**Success Metrics**:
- Version creation time < 200ms
- Storage efficiency > 70% reduction vs full snapshots
- Rollback success rate 100%

### Phase 3: Reliability
**Key Deliverables**:
- Publish Simulation Mode (`/p-sim` route)
- Enhanced ValidationCard with severity levels
- Single-page retry (no full rebuild)
- Failed version storage (separate from quota)

**Success Metrics**:
- Preview-publish consistency 100%
- CSP issues caught in simulation 100%
- Single-page retry success rate > 95%

### Phase 4: Thumbnails + SEO
**Key Deliverables**:
- Queue-based thumbnail generation (300x600)
- Separate OG Image generation (1200x630)
- Three-tier fallback strategy (Playwright → html2canvas → SVG)
- Basic SEO tags for social sharing

**Success Metrics**:
- Thumbnail success rate > 95%
- Thumbnail generation time < 30s
- Publish blocked by thumbnail 0%

### Phase 5: Polish
**Key Deliverables**:
- Examples gallery on homepage
- One-click project generation
- Chat UX improvements (no code, natural card flow)
- TaskBoardCard with cumulative tasks
- Virtual scrolling for chat history
- Branch creation and isolation

**Success Metrics**:
- Example usage rate > 30% of new users
- First-page time < 30 seconds
- Branch creation rate > 10% of power users

### Phase 6: Completion
**Key Deliverables**:
- Version pinning (max 3)
- Branch and version quota enforcement
- Comprehensive testing (unit, integration, E2E)
- Bug fixes and documentation
- Launch preparation

**Success Metrics**:
- Critical bugs 0
- Test coverage > 80%
- Documentation completeness 100%

---

## Dependencies

```
Phase 1 (Foundation)
    ↓
Phase 2 (Version System)
    ↓
Phase 3 (Reliability)
    ↓
Phase 4 (Thumbnails + SEO)
    ↓
Phase 5 (Polish)
    ↓
Phase 6 (Completion)
```

**Critical Path**:
- Phase 1 must be complete before Phase 2 (Code Tab needed for Version System)
- Phase 2 must be complete before Phase 3 (Version System needed for Failed Versions)
- Phase 1 must be complete before Phase 3 (CSP resolution needed for Simulation Mode)
- Phase 5 can overlap with Phase 4 (independent features)
- Phase 6 requires all previous phases complete

---

## Implementation Guidelines

### Reading Order
For implementers, read phases in this order:
1. This overview document
2. Individual phase documents (in sequence)
3. [SPEC-v5.md](../../SPEC-v5.md) for full specification details
4. Implementation Decisions section (Part O in SPEC-v5.md)

### Status Tracking
- Each phase has acceptance criteria marked with `[ ]`
- Update these as tasks are completed
- Track blockers and risks in each phase document
- Update success metrics as you go

### Risk Management
- Each phase documents risk factors and mitigations
- Review risks before starting each phase
- Escalate critical risks immediately
- Update mitigation strategies as needed

---

## Key Technical Decisions

From SPEC-v5.md Part O (Implementation Decisions):

### Infrastructure
- **Version Storage**: PostgreSQL JSONB + diff table (not external object storage)
- **Real-time Communication**: sse-starlette (SSE) for chat streaming
- **Virtual Scrolling**: react-window for chat history
- **Code Viewer**: CodeMirror 6 (lightweight, < 500KB)

### Architecture
- **CSP Detection**: `/p-sim` route with real HTTP headers (not meta tags)
- **Thumbnail Queue**: Global FIFO queue with Semaphore(2) concurrency limit
- **Version Quota**: Soft quota with grace period (2x limit before deletion)
- **Code Access**: Owner-only in v5 (collaborators in future versions)

### Strategy
- **OG Image Generation**: Mixed strategy (proactive + on-demand)
- **Example Projects**: One-time clone (independent projects)
- **Branch Switching**: Independent draft state (simple approach)
- **Page Rollback**: Database transaction (ACID compliance)

---

## Success Metrics (v5 Overall)

| Metric | v4 | v5 Target |
|--------|----|-----------|
| Preview-Publish consistency | N/A | 100% match |
| Single-page retry rate | N/A | < 5% need full rebuild |
| Code visibility in chat | Yes | No (all in Code Tab) |
| Version navigation | N/A | > 50% users view previous |
| First-page time | N/A | < 30 seconds |
| Example usage rate | N/A | > 30% of new users |
| Page-level rollback usage | N/A | Measured via analytics |
| Branch creation rate | N/A | > 10% of power users |

---

## Launch Checklist

Before launching v5:

### Feature Completeness
- [ ] All 6 phases complete
- [ ] All acceptance criteria met
- [ ] Success metrics achieved

### Quality Assurance
- [ ] Unit test coverage > 80%
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Security audit passed
- [ ] Performance benchmarks met

### Documentation
- [ ] User guides complete
- [ ] API documentation accurate
- [ ] Architecture diagrams created
- [ ] Deployment guide tested
- [ ] Troubleshooting guide ready

### Operations
- [ ] Monitoring configured
- [ ] Alerting set up
- [ ] Backup/restore tested
- [ ] Incident response runbook ready
- [ ] Support team trained

### Communication
- [ ] Marketing materials ready
- [ ] Release notes drafted
- [ ] User announcement prepared
- [ ] In-app notifications configured

---

## Post-Launch Monitoring

After launching v5, monitor these metrics for 2 weeks:

### Technical Metrics
- Version creation success rate
- Thumbnail generation success rate
- CSP violation frequency
- Preview load times
- Chat streaming performance

### User Metrics
- Example usage rate
- Branch creation rate
- Version history views
- Page rollback usage
- Code Tab usage

### Business Metrics
- Time to first published page
- User retention (7-day, 30-day)
- Support ticket volume
- Feature adoption rates

---

## Maintenance Schedule

### Week 1 Post-Launch
- Daily monitoring of critical metrics
- Quick response to bugs
- User feedback collection

### Week 2-4 Post-Launch
- Bug fix releases as needed
- Performance optimization
- Documentation improvements

### Month 2-3 Post-Launch
- Feature refinements based on usage
- Performance tuning
- Planning for v6

---

## Resources

### Documentation
- [SPEC-v5.md](../../SPEC-v5.md) - Full specification
- [CLAUDE.md](../../CLAUDE.md) - Project overview
- Phase documents (linked above) - Detailed implementation guides

### Reference Implementation
- See `../Bubu/` for working prototype with similar features

### Tools & Libraries
- **Backend**: FastAPI, PostgreSQL, sse-starlette, diff-match-patch, Playwright
- **Frontend**: React, react-window, CodeMirror 6
- **Testing**: pytest, Playwright E2E

---

## Questions?

For implementation questions:
1. Check SPEC-v5.md Part O (Implementation Decisions)
2. Review individual phase documents
3. Consult reference implementation in `../Bubu/`
4. Follow up with product team

---

**Document Version**: 1.0
**Last Updated**: 2026-01-29
**Status**: Ready for Implementation
