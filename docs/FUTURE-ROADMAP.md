# Zaoya Future Roadmap

> Features that have been discussed but not yet scheduled for implementation.

This document tracks features that were considered but deferred. When a feature is adopted by a specific version, it will be marked as such.

---

## How to Read This Document

- **Status** column shows: `Pending` (not scheduled), `Adopted in vX` (included in that version)
- **Priority**: High / Medium / Low
- **Notes**: Brief context on why deferred or what's needed

---

## Features List

### Core Features

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Auto-rollback | Medium | Pending | v5 removed auto-rollback, manual rollback implemented instead |
| Branch merge | Medium | Pending | v5 supports branch creation, merge deferred |
| Multi-page projects | High | Pending | Linked pages with navigation |
| Custom domains | Low | Pending | Users can use their own domain |
| Team collaboration | Low | Pending | Multiple users per workspace |

### AI & Generation

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| AI image generation | Medium | Pending | Generate images from prompts |
| Model selector UI | Low | Pending | Let users choose AI model |
| Custom AI prompts | Low | Pending | Advanced users can customize prompts |

### Analytics & SEO

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Performance monitoring | Low | Pending | Lighthouse-style audits |
| Advanced analytics | Low | Pending | Funnels, cohorts, retention |
| A/B testing (full) | Medium | Pending | v5 has basic branching support |
| Real-time analytics dashboard | Low | Pending | Live visitor counts |

### User Experience

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Diff Viewer | Low | Pending | Visual code comparison |
| Multi-device sync conflict UI | Medium | Pending | Manual resolution in v5 |
| Real-time collaborative editing | Low | Pending | Live editing with others |
| Keyboard shortcuts | Low | Pending | Power user shortcuts |
| Bulk operations | Low | Pending | Bulk publish, delete, export |

### Publishing & Sharing

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Password protection | Medium | Pending | Password-protected pages |
| Scheduled publish | Low | Pending | Publish at specific time |
| Scheduled unpublish | Low | Pending | Auto-unpublish at specific time |
| Vanity URLs | Medium | Pending | `/u/username/project-slug` |

### Integrations

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Stripe integration | Medium | Pending | Accept payments |
| Email marketing | Medium | Pending | Mailchimp, etc. integration |
| Webhook notifications | Low | Pending | Trigger external services |
| Zapier/Make integration | Low | Pending | No-code automation |

### Advanced Features

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Component marketplace | Low | Pending | Share/reuse components |
| Template marketplace | Low | Pending | Community templates |
| API access | Low | Pending | Public API for developers |
| Webhooks API | Low | Pending | Inbound webhooks |

---

## Version History

### Features Adopted by v5

The following features were deferred from earlier versions and adopted in v5:

| Feature | Original Deferral | Adopted in v5 | Notes |
|---------|-------------------|---------------|-------|
| Version system | v4 | v5 | Full version history with branching |
| Code Tab | v4 | v5 | Dedicated code viewer |
| Publish Simulation | v4 | v5 | CSP-aware preview mode |
| Separate OG Image | v4 | v5 | High-quality social sharing images |

### Features Adopted by v4

| Feature | Original Deferral | Adopted in v4 | Notes |
|---------|-------------------|---------------|-------|
| Dynamic form handling | v3 | v4 | Runtime form submission |
| Analytics tracking | v3 | v4 | View, click, submission tracking |

### Features Adopted by v3

| Feature | Original Deferral | Adopted in v3 | Notes |
|---------|-------------------|---------------|-------|
| Templates (4 categories) | v2 | v3 | Personal, Event, Product, Contact |
| Quick actions | v2 | v3 | Pre-written refinement prompts |
| Adaptive interview | v2 | v3 | Dynamic question flow |

---

## Decision Log

### Auto-rollback (v5 Deferral)

- **Original**: Planned for v5 with automatic version restoration on failure
- **Deferred**: 2026-01-29, during spec interview
- **Reason**: Manual rollback gives users more control; auto-rollback can cause confusion with multiple devices
- **Alternative Implemented**: Manual page-level rollback (Part I.5)

### Branch Merge (v5 Deferral)

- **Original**: Planned for v5 as part of branching feature
- **Deferred**: 2026-01-29, during spec interview
- **Reason**: Complexity of conflict resolution; low immediate user need
- **Alternative Implemented**: Use branch as reference, manually apply changes in main

---

## Contributing to Future Roadmap

To propose a new feature for future consideration:

1. Add it to the appropriate category above
2. Set priority (High/Medium/Low)
3. Add brief description and rationale
4. Link to any relevant spec discussions or issues

---

**Document Version**: 1.0
**Created**: 2026-01-29
**Last Updated**: 2026-01-29
