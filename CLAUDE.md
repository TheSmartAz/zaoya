# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Zaoya (造鸭)** is a specification-stage project for an AI-powered no-code web application platform. Users describe what they want in natural language, and AI generates mobile-first web pages that can be published and shared.

**Tagline**: "Describe it. See it. Share it."

**Current Status**: Pre-implementation. This repository contains only specification documents. No code has been written yet.

**Reference Implementation**: See `../Bubu/` for a working prototype with similar AI chat, streaming, and code generation features.

---

## Development Commands

This project is not yet implemented. When development begins, the planned commands (based on the Bubu reference) will be:

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev       # Development server
npm run build     # Production build
npm run preview   # Preview production build
```

---

## Architecture Overview

### v0 Core Loop
```
[Choose Template] → [Adaptive Interview] → [First Generation]
→ [Quick Action Refinement] → [Publish] → [Share Link]
```

### Planned Structure
```
zaoya/
├── frontend/              # Vite + React + TypeScript
│   └── src/
│       ├── components/
│       │   ├── ChatPanel/         # Chat interface with streaming
│       │   ├── PreviewPanel/      # Mobile preview (sandboxed iframe)
│       │   ├── CodePanel/         # Read-only code viewer
│       │   ├── TemplateSelector/  # Template category selection
│       │   └── QuickActionChips/  # Pre-written refinement prompts
│       ├── hooks/                 # useChatStream, useProject
│       ├── stores/                # Zustand stores (chat, project)
│       └── types/                 # TypeScript types
│
├── backend/              # FastAPI (Python)
│   └── app/
│       ├── api/
│       │   ├── chat.py            # POST /api/chat (SSE streaming)
│       │   ├── projects.py        # CRUD for projects
│       │   └── analytics.py       # Views, clicks, submissions
│       └── services/
│           └── ai_service.py      # Multi-model AI integration
│
└── pages-domain/         # Separate origin for published pages
```

---

## Two-Domain Security Model (Critical)

Published user pages MUST be served from a separate domain for security isolation:

| Domain | Purpose |
|--------|---------|
| `zaoya.app` | Main app (editor, dashboard, auth) |
| `pages.zaoya.app` | Published user pages (no auth cookies) |

This prevents XSS attacks from user-generated pages accessing admin sessions.

---

## Security-First Code Generation

### Runtime-First JavaScript

AI generates minimal JS that ONLY calls platform helpers:

```javascript
// Allowed
Zaoya.submitForm(formData)
Zaoya.track('cta_click', { button: 'signup' })
Zaoya.toast('Thanks for signing up!')

// Blocked (via AST validation)
- localStorage, sessionStorage, indexedDB
- fetch, XHR (must use Zaoya.*)
- eval(), new Function()
- Parent frame access (top, parent, window.opener)
```

### Rendering Pipeline

```
1. Generate    → AI outputs { html, js, metadata }
2. Normalize   → Inject viewport meta, design tokens
3. Sanitize    → HTML sanitizer (DOMPurify)
4. Validate    → JS AST validation (block dangerous patterns)
5. Wrap        → Inject zaoya-runtime.js
6. Store       → Save snapshot to SQLite
7. Publish     → Pin snapshot as immutable version
```

### CSP Headers (Published Pages)

```
default-src 'none';
img-src 'self' data: blob: https:;
style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;
script-src 'self';
connect-src https://api.zaoya.app;
frame-ancestors 'none';
```

---

## Template System

Four template categories guide the AI and collect structured inputs:

| Category | Examples | Key Inputs |
|----------|----------|------------|
| **Personal profile** | Link-in-bio, portfolio | Name, bio, links, photo |
| **Event invitation** | Birthday, wedding RSVP | Event name, date, location, RSVP |
| **Product landing** | Showcase, launch, pricing | Product name, CTA, features, price |
| **Contact/Lead form** | Contact, signup, survey | Form fields, notification email |

Each template has:
- Specific system prompt additions
- Adaptive interview questions (2-6 max)
- Universal quick action chips (e.g., "Make it more premium")
- Contextual quick action chips (e.g., "Add RSVP form" for events)

---

## AI Integration (Copy from Bubu)

The backend will copy Bubu's AI service pattern from `../Bubu/backend/app/services/ai_service.py`:

**Supported Models** (OpenAI-compatible API):
- GLM-4.7 (智谱 AI) - **default**
- DeepSeek V3
- Doubao (字节跳动)
- Qwen (阿里云)
- Hunyuan (腾讯)
- Kimi K2 (月之暗面)
- MiniMax M2.1

**Streaming**: Uses Server-Sent Events (SSE) via `sse-starlette` or manual response generation.

---

## Key Specification Documents

| File | Purpose |
|------|---------|
| `SPEC-v0.md` | MVP specification (8-10 weeks) - read first |
| `SPEC-v1.md` | v1 roadmap (post-MVP features) |
| `docs/PHASE_BREAKDOWN.md` | Detailed 4-phase task breakdown |
| `docs/phases/v0-phase-*.md` | Individual phase task lists |

---

## Explicit Non-Goals (v0)

Do NOT implement these in v0:
- Multi-page projects (linked pages)
- Custom domains
- A/B testing / experiments
- Model selector UI (use default model only)
- AI image generation
- Full bilingual UI (i18n-ready architecture, English only)
- Team collaboration
- Advanced analytics (funnels, cohorts)
- Component marketplace
- Third-party integrations (Stripe, email marketing)

---

## URL Structure

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/create` | Template selection |
| `/editor/{project_id}` | Chat builder + preview |
| `/draft/{project_id}` | Draft preview |
| `/p/{public_id}` | Published page (on pages.zaoya.app) |
| `/dashboard` | User's projects + analytics |

Vanity URLs (`/u/{username}/{slug}`) are deferred to v1.

---

## Version History Model

- Every AI response creates a snapshot
- Unlimited snapshots during development
- Simple revert: "Restore to version X"
- Published version is **immutable** (separate from draft)
- Publishing pins the current draft as a new published version

---

## Success Metrics (v0)

| Metric | Target |
|--------|--------|
| Idea to published | < 5 minutes |
| Conversation turns to success | < 3 turns |
| Mobile Lighthouse score | 90+ |
| XSS vulnerabilities | Zero |
| First-gen acceptance rate | > 70% |

---

## Implementation Phases

See `docs/PHASE_BREAKDOWN.md` for the complete breakdown:

1. **Phase 1 (Weeks 1-3)**: Foundation - scaffolding, chat, basic generation
2. **Phase 2 (Weeks 4-6)**: Core Loop - templates, interview, quick actions, versions
3. **Phase 3 (Weeks 7-8)**: Publishing - auth, persistence, sharing
4. **Phase 4 (Weeks 9-10)**: Forms + Analytics - dynamic features, insights

Phases are sequential - each builds on the previous.
