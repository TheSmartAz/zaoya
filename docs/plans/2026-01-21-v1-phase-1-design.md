# Zaoya v1 Phase 1: Expansion Design

**Date**: 2026-01-21
**Status**: Ready for Implementation
**Complexity**: Large

---

## Overview

Phase 1 transforms Zaoya from a single-page generator into a multi-page web app studio. This document details the technical design for implementing:

1. **Multi-Page Projects** - Projects with multiple pages sharing a design system
2. **Vanity URLs** - `/u/{username}/{slug}` URLs for published projects
3. **Model Selector UI** - User-selectable AI models with characteristics
4. **Full Bilingual UI** - Chinese + English with path-based locale routing

---

## Architecture Decisions

### Database
- **PostgreSQL** from the start (skip SQLite to avoid migration later)
- **SQLAlchemy 2.0** with async support (not Drizzle - it's TypeScript-only)
- **Alembic** for migrations

### Publishing Strategy
- **Static HTML per page** (not SPA) - preserves v0's Lighthouse performance
- Each page rendered as separate HTML file at publish time
- Multi-page navigation via standard anchor links
- Design system injected as CSS variables during render

### Storage
- **Dev**: Local filesystem at `backend/published_pages/`
- **Prod**: Object storage (S3/R2/GCS) + CDN
- Republish overwrites files at same paths

---

## Database Schema

```sql
-- Extension for case-insensitive unique usernames
CREATE EXTENSION IF NOT EXISTS citext;

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  name VARCHAR(255),
  avatar_url TEXT,
  provider VARCHAR(20) DEFAULT 'email',
  provider_id VARCHAR(255),
  username CITEXT UNIQUE,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT username_format
    CHECK (username ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
);

-- Projects table
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  public_id VARCHAR(8) UNIQUE,              -- Generated on publish
  slug VARCHAR(100),
  name VARCHAR(255) NOT NULL,
  template_id VARCHAR(50),
  template_inputs JSONB DEFAULT '{}',
  status VARCHAR(20) DEFAULT 'draft',
  current_draft_id UUID,                    -- Points to mutable draft
  published_snapshot_id UUID,               -- Points to published version
  notification_email VARCHAR(255),
  notification_enabled BOOLEAN DEFAULT false,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, slug),
  CONSTRAINT slug_format
    CHECK (slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
);

-- Snapshots table
CREATE TABLE snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  summary TEXT,                             -- AI-generated change summary
  design_system JSONB DEFAULT '{}',          -- Shared across pages
  navigation JSONB DEFAULT '{}',             -- Header/footer config
  is_draft BOOLEAN DEFAULT false,           -- true = mutable, false = immutable
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(project_id, version_number),
  CONSTRAINT at_most_one_draft_per_project
    EXCLUDE (project_id WITH =) WHERE (is_draft = true)
);

-- Pages table
CREATE TABLE pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
  slug VARCHAR(100) NOT NULL,
  title VARCHAR(255) NOT NULL,
  html TEXT NOT NULL,
  js TEXT,
  metadata JSONB DEFAULT '{}',
  is_home BOOLEAN DEFAULT false,
  display_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(snapshot_id, slug),
  CONSTRAINT slug_format
    CHECK (slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
);

-- Indexes
CREATE UNIQUE INDEX uniq_home_per_snapshot
ON pages(snapshot_id)
WHERE is_home = true;

CREATE INDEX idx_snapshots_project_created ON snapshots(project_id, created_at DESC);
CREATE INDEX idx_pages_snapshot_order ON pages(snapshot_id, display_order);
CREATE INDEX idx_projects_user_updated ON projects(user_id, updated_at DESC);
CREATE INDEX idx_projects_public_id ON projects(public_id) WHERE public_id IS NOT NULL;
```

### Key Semantics
- `is_draft=true` snapshot: Mutable, one per project, pages can be edited
- `is_draft=false` snapshot: Immutable, created on "version" action
- Publishing: Creates immutable snapshot, renders static HTML
- Draft editing: Edits pages in draft snapshot directly
- Version creation: Clones draft → new immutable snapshot

---

## API Endpoints

### Draft Operations (Mutable)
```
GET    /api/projects/:id/draft                  # Get current draft
POST   /api/projects/:id/draft                  # Create draft if none
PATCH  /api/projects/:id/draft                  # Update draft metadata
GET    /api/projects/:id/draft/pages            # List draft pages
POST   /api/projects/:id/draft/pages            # Add page to draft
PATCH  /api/projects/:id/draft/pages/:page_id   # Update draft page
DELETE /api/projects/:id/draft/pages/:page_id   # Delete draft page
POST   /api/projects/:id/draft/pages/reorder    # Reorder pages
```

### Snapshot Operations (Immutable)
```
GET    /api/projects/:id/snapshots              # List all snapshots
POST   /api/projects/:id/snapshots              # Create snapshot from draft
POST   /api/projects/:id/snapshots/:snap_id/restore  # Restore to draft
GET    /api/projects/:id/snapshots/:snap_id/diff    # Compare snapshots
```

### Design System
```
GET    /api/projects/:id/design-system          # Get design tokens
PUT    /api/projects/:id/design-system          # Update design tokens
POST   /api/projects/:id/design-system/apply    # Apply to all draft pages
```

### Publishing
```
POST   /api/projects/:id/publish                # Freeze draft → snapshot + render
```

### Public Read (Cacheable, Published Only)
```
GET    /api/public/projects/:public_id          # Published manifest
GET    /api/public/projects/:public_id/pages/:slug  # Published page HTML
```

### Username / Slug
```
GET    /api/auth/username/available/:username   # Check availability
PUT    /api/auth/username                       # Set/change username
GET    /api/projects/:id/slug/available/:slug   # Check project slug
```

### Model Selector
```
GET    /api/chat/models                         # List models + characteristics
POST   /api/chat                                # Add model_id parameter
```

---

## Frontend Architecture

### Routing with Locale
```tsx
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/create" element={<LocaleRedirect to="/:locale/create" />} />
  <Route path="/dashboard" element={<LocaleRedirect to="/:locale/dashboard" />} />
  <Route path="/:locale/*" element={<LocalApp />}>
    <Route path="create" element={<CreatePage />} />
    <Route path="editor/:projectId" element={<EditorPage />} />
    <Route path="dashboard" element={<DashboardPage />} />
  </Route>
</Routes>
```

### Editor Layout (3-Panel)
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo | ModelSelector | LanguageSwitcher | UserMenu  │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ 📄 Home  │         [Page Preview/Editor]                   │
│ 📄 About │                                                  │
│ 📄 Contact│  ┌──────────────────────────────────────────┐  │
│          │  │                                          │  │
│ [+ Add]  │  │        Chat Panel                        │  │
│          │  │                                          │  │
│ ──────── │  └──────────────────────────────────────────┘  │
│ 🎨 Design│                                                  │
│ ⚙️ Settings│                                                 │
└──────────┴──────────────────────────────────────────────────┘
```

### New Components
- `ProjectSidebar` - Page list with drag-reorder (dnd-kit)
- `ModelSelector` - Dropdown with speed/quality/cost badges
- `LanguageSwitcher` - Flag dropdown (🇺🇸/🇨🇳)
- `DesignSystemPanel` - Color picker, font selector
- `PageCreationModal` - Page type selection

### State Updates
- `projectStore` → Add `pages[]`, `designSystem`, `navigation`
- `chatStore` → Add `selectedModel`
- New `localeStore` → Current locale, translations

---

## Published Pages

### File Structure
```
/{public_id}/index.html          → Home page
/{public_id}/about/index.html    → About page
/{public_id}/contact/index.html  → Contact page
```

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --color-primary: #3b82f6;
      --font-family: system-ui, ...;
      /* Design tokens from design_system */
    }
  </style>
</head>
<body>
  <nav><!-- Generated header --></nav>
  <main><!-- Page content --></main>
  <footer><!-- Generated footer --></footer>
  <script src="/assets/zaoya-runtime.js"></script>
  <script>
    // Page-specific JS (validated, safe)
  </script>
</body>
</html>
```

### CSP Headers
```
default-src 'none';
img-src 'self' data: https:;
style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;
script-src 'self' https://cdn.zaoya.app;
connect-src https://api.zaoya.app;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

---

## Implementation Sequence

1. **Multi-Page Projects** (40% of effort)
   - Database + migrations
   - Draft/page CRUD APIs
   - Editor UI with sidebar
   - Design system sync
   - Static HTML publishing

2. **Vanity URLs** (20% of effort)
   - Username claiming
   - Project slugs
   - URL routing + redirects
   - Legacy URL preservation

3. **Model Selector** (15% of effort)
   - Model configuration
   - Selector UI component
   - Generation service updates
   - User preferences

4. **Bilingual UI** (25% of effort)
   - react-i18next setup
   - String extraction + translation
   - Locale routing
   - AI response localization
   - Template localization

---

## i18n Configuration

**Library**: react-i18next

**File structure**:
```
frontend/src/locales/
  en.json
  zh.json
```

**Usage**:
```tsx
import { useTranslation } from 'react-i18next';

function Component() {
  const { t } = useTranslation();
  return <button>{t('common.save')}</button>;
}
```

**Locale detection**: Accept-Language header → URL path → user preference

---

## Security Considerations

1. **Username/Slug validation**: Server-side regex, reserved words block
2. **Slug normalization**: Always lowercase before storage
3. **Authorization**: All project/page APIs check user ownership
4. **Rate limiting**: Username/slug changes limited
5. **CSP**: Published pages get strict CSP headers
6. **XSS prevention**: HTML sanitization (bleach) + JS validation

---

## Definition of Done

Phase 1 is complete when:

1. ✅ All acceptance criteria pass (from v1-phase-1-expansion.md)
2. ✅ Unit tests cover critical paths (>80% coverage)
3. ✅ Integration tests for multi-page publishing
4. ✅ E2E tests for complete user journeys
5. ✅ Performance benchmarks met (page load < 2s)
6. ✅ Security audit passed (no new vulnerabilities)
7. ✅ Documentation updated
8. ✅ Staging environment validated
