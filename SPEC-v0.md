# Zaoya (造鸭) - v0 Specification

> Ship fast, prove the core loop: prompt → good-looking mobile page → share link in minutes

## Goal

A user can go from idea to published, shareable mobile page reliably and quickly. v0 validates the core value proposition before adding complexity.

**Tagline**: "Describe it. See it. Share it."

---

## Core Loop (v0)

```
[Choose Template] → [Adaptive Interview] → [First Generation] → [Quick Action Refinement] → [Publish] → [Share Link]
```

---

## Target Users

**Primary**: Individuals creating personal pages
- Profile cards, link-in-bio
- Event invitations (birthday, wedding RSVP)
- Simple product/project showcases
- Contact/lead capture forms

---

## Key Features (v0)

### 1. Template-First Start

Four template categories, each with structured input collection:

| Category | Examples | Key Inputs |
|----------|----------|------------|
| **Personal profile** | Link-in-bio, portfolio, about-me | Name, bio, links, photo |
| **Event invitation** | Birthday, wedding, party | Event name, date, location, RSVP |
| **Product landing** | Showcase, launch, pricing | Product name, CTA, features, price |
| **Contact/Lead form** | Contact, signup, survey | Form fields, notification email |

### 2. Adaptive Interview Questions

Before first generation, AI asks 2-6 dynamic questions based on:
- Detected intent (template choice)
- Missing high-impact information
- Already-known facts (don't re-ask)

**Question priorities**:
1. Primary goal + CTA (most important)
2. Audience + tone ("vibe")
3. Key content (date/location/links)
4. Visual preference (color/style)
5. Form requirements (fields + notification)

Users can skip: "Not sure—choose for me"

### 3. Chat-First Builder + Mobile Preview

- **Split-screen layout**: Chat panel (left) + Mobile preview (right)
- **Streaming responses**: See AI typing in real-time
- **Preview refresh**: Updates after each complete AI response
- **View-only code panel**: Expandable, read-only (trust + education)

### 4. Quick Action Chips

Pre-written refinement prompts shown after generation:

**Universal chips** (always available):
- Make it more premium / more playful
- Shorten copy / make copy more detailed
- Change primary color
- Add FAQ section
- Add testimonials
- Adjust CTA

**Contextual chips** (based on template):
- Add RSVP form (events)
- Add countdown timer (events/launches)
- Add pricing table (products)
- Add social links (profiles)

### 5. Form Submissions (Only Dynamic Feature)

- Forms submit to platform API
- Data stored in per-project table (SQLite)
- Owner can:
  - View submissions in dashboard
  - Export as CSV
  - Enable email notifications (optional)

### 6. Version History

- Every AI response creates a snapshot
- Unlimited snapshots during dev/beta
- Simple restore: "Revert to version X"
- Basic "what changed" summary
- **Published version is immutable** (separate from draft)

### 7. Draft vs Published

| State | Behavior |
|-------|----------|
| **Draft** | Live editing, private, `/draft/{project_id}` |
| **Published** | Immutable snapshot, public, `/p/{public_id}` |

Publishing creates a snapshot. Continued editing doesn't affect published version until re-publish.

### 8. Project Persistence

- **Guest projects**: Create without signup, stored in browser
- **Sign in to save**: Google/email auth to persist and publish
- **Auth bypass**: Available during development phase

### 9. Basic Analytics

Track per published page:
- Page views
- CTA clicks
- Form submissions

Simple dashboard for page owner. No advanced analytics in v0.

---

## Technical Architecture (v0)

### Frontend
- **Framework**: Vite + React + TypeScript
- **Styling**: Tailwind CSS
- **State**: React hooks / Zustand
- **i18n**: Architecture ready (react-i18next), English UI only for v0

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite
- **AI Integration**: OpenAI-compatible APIs (copy Bubu's .env config)
- **File Storage**: Local filesystem for images

### Generated Page Tech
- HTML5 + Tailwind CSS (CDN)
- Platform runtime (`zaoya-runtime.js`)
- AI-generated JS limited to DOM wiring + `Zaoya.*` calls

---

## Security Architecture (v0)

### Separate Origin for Published Pages

| Domain | Purpose |
|--------|---------|
| `zaoya.app` | Main application (editor, dashboard, auth) |
| `pages.zaoya.app` | Published user pages only |

No auth cookies on `pages.zaoya.app`. Isolates user-generated content.

### Runtime-First JavaScript

AI generates HTML + Tailwind + minimal JS that calls platform helpers only:

```javascript
// Allowed Zaoya.* helpers
Zaoya.submitForm(formData)
Zaoya.track('cta_click', { button: 'signup' })
Zaoya.toast('Thanks for signing up!')
Zaoya.navigate('/success')
```

**Blocked patterns** (enforced by AST validation):
- Dynamic code execution functions
- Browser storage APIs
- Direct network requests (must use Zaoya.*)
- Parent frame access

### HTML Sanitization

Reject or strip:
- External script tags
- Inline event handlers (`onclick=`, `onerror=`)
- `javascript:` URLs
- Iframes (except allowlist)

### JS Static Validation

Parse generated JS into AST and block dangerous patterns:
- Dynamic code execution
- Storage APIs (localStorage, sessionStorage, indexedDB, cookies)
- Network APIs (fetch, XHR) except via `Zaoya.*`
- Frame access (top, parent)

If validation fails → regenerate with stricter constraints.

### CSP Headers (Published Pages)

```
default-src 'none';
img-src 'self' data: blob: https:;
style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;
script-src 'self';
connect-src https://api.zaoya.app;
frame-ancestors 'none';
```

### Preview Sandbox

```html
<iframe sandbox="allow-scripts" src="...">
```

Communication via `postMessage` only. No `allow-same-origin`.

---

## Rendering Pipeline

```
1. Generate    → AI outputs { html, js, metadata }
2. Normalize   → Inject viewport meta, design tokens
3. Sanitize    → HTML sanitizer (DOMPurify or similar)
4. Validate    → JS AST validation
5. Wrap        → Inject zaoya-runtime.js
6. Store       → Save snapshot to SQLite
7. Publish     → Pin snapshot as immutable published version
```

---

## Code Generation Contract

AI must follow these rules (enforced by system prompt + validation):

**Allowed**:
- HTML5 semantic elements
- Tailwind CSS classes
- Inline styles (CSS only)
- JS that wires DOM events to `Zaoya.*` calls
- `<img>` with `src` from user uploads or allowed CDNs

**Blocked**:
- External `<script>` tags
- Inline event handlers in HTML
- Any JS beyond DOM event wiring + `Zaoya.*` calls
- `<iframe>`, `<object>`, `<embed>`
- `<form action="external-url">`

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

Vanity URLs (`/u/{username}/{slug}`) deferred to v1.

---

## Explicit Non-Goals (v0)

Do NOT implement in v0:

- Multi-page projects (linked pages)
- Custom domains
- A/B testing / experiments
- Model selector UI (use default model)
- AI image generation
- Full bilingual UI (i18n-ready only)
- Team collaboration
- Advanced analytics (funnels, cohorts)
- Component marketplace
- Integrations (Stripe, email marketing, etc.)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Idea to published | < 5 minutes |
| Conversation turns to success | < 3 turns |
| Mobile Lighthouse score | 90+ |
| XSS vulnerabilities | Zero |
| First-gen acceptance rate | > 70% |

---

## Timeline (8-10 weeks)

### Phase 1: Foundation (Weeks 1-3)
- Project scaffolding (Vite + React + FastAPI)
- Chat interface with streaming
- AI integration (Bubu backend config)
- Basic page generation + preview
- Sandbox iframe rendering

### Phase 2: Core Loop (Weeks 4-6)
- Template system (4 categories)
- Adaptive interview questions
- Quick action chips
- Version history + restore
- HTML/JS sanitization + validation

### Phase 3: Publishing (Weeks 7-8)
- User authentication (Google/email)
- Guest → signed-in conversion
- Draft vs published states
- Separate origin deployment
- Shareable links (`/p/{id}`)

### Phase 4: Forms + Analytics (Weeks 9-10)
- Form submission handling
- Submission dashboard + CSV export
- Basic analytics (views, clicks, submits)
- Email notifications (optional)
- Security hardening

---

## Reference

- **Bubu project** (`../Bubu/`): AI chat, streaming, model integration
- **Competitors**: Framer, Carrd, v0.dev, Durable

---

## Open Questions (v0)

1. Default AI model selection (which model for v0)?
2. Image upload size/format limits?
3. Rate limiting for free/guest users?
4. Analytics: self-hosted (Plausible) vs simple custom?
