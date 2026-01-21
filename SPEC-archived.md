# Zaoya (造鸭) - Product Specification

> AI-powered no-code platform for creating mobile-first web pages through natural conversation

## Overview

Zaoya is a web-based vibe coding platform that enables users to generate professional mobile web pages through natural language conversation and templates. Unlike traditional no-code tools, Zaoya focuses on the "vibe" - users describe what they want conversationally, and AI generates complete, functional mobile pages.

**Tagline**: "Describe it. See it. Share it."

---

## Core Concept

### What It Is
- A web application where users create mobile web pages by chatting with AI
- Template-guided creation with conversational refinement
- Full-stack dynamic pages with form submissions and data persistence
- One-click publishing with shareable links

### What It's Not
- Not a drag-and-drop visual builder
- Not a code editor (though code is viewable)
- Not limited to static pages

---

## Target Users (MVP Priority Order)

1. **Individuals (Primary)** - Personal profiles, event invitations, hobby projects
2. **Small businesses/creators** - Marketing pages, product launches, lead capture
3. **Educators/students** - Learning web concepts through AI-assisted creation
4. **Teams/enterprises** - Future expansion

---

## Key Features

### 1. Interaction Model
- **Chat-first**: Natural language is the primary interface
- **Template + Chat**: Curated templates as starting points, refined via conversation
- **Chat-only refinement**: All iterations happen through conversation (no visual editor)

### 2. Page Capabilities
- **Full-stack dynamic**: Forms, data storage, backend logic
- **Multi-page projects**: Linked pages within a project (home → about → contact)
- **Backend**: Managed API + KV store (simple JSON blob storage per project)
  - Migration path to proper databases later

### 3. Media & Assets
- User image uploads
- AI image generation (DALL-E, etc.)
- Icon library (Lucide/Heroicons)

### 4. Preview & Editing
- Split-screen layout: Chat panel + Mobile preview
- Preview refreshes on each AI response
- Full version history (revert to any previous generation)
- View-only code panel (builds trust, educational value, secure)

### 5. Publishing & Distribution
- Subdomain under platform: `zaoya.app/u/{username}/{pagename}`
- Generated shareable links
- No custom domain support in MVP

### 6. User Authentication
- Full auth system (Google/GitHub/email OAuth)
- Bypass auth during development phase
- Cross-device sync and account features

### 7. AI Models
- Multi-model support (matching Bubu's backend):
  - GLM-4.7 (智谱 AI)
  - DeepSeek V3
  - Doubao (字节跳动)
  - Qwen (阿里云)
  - Hunyuan (腾讯)
  - Kimi K2 (月之暗面)
  - MiniMax M2.1
- User-selectable in UI

### 8. Localization
- Bilingual support (Chinese + English) from start
- i18n system built into architecture

---

## Template Categories (MVP)

1. **Personal profiles** - Profile cards, link-in-bio, portfolios, about-me
2. **Event invitations** - Birthday, wedding RSVP, party announcements
3. **Product landing** - Showcase, pricing, countdown, features
4. **Forms & interactive** - Contact forms, surveys, quizzes, polls

---

## Unique Value Proposition

1. **Mobile-native UX focus** - WeChat/WhatsApp mini-app feel, lightweight, fast, native-like interactions
2. **Built-in analytics & optimization** - A/B testing, conversion tracking for landing pages

---

## Technical Architecture

### Frontend
- **Framework**: Vite + React + TypeScript
- **Styling**: Tailwind CSS
- **State**: React hooks / Zustand
- **i18n**: react-i18next or similar

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (MVP), migration path to PostgreSQL
- **AI Integration**: OpenAI-compatible APIs (reuse Bubu's .env config)
- **File Storage**: Local filesystem / S3-compatible for images

### Page Hosting
- **Dynamic rendering**: Page code stored in SQLite, served via FastAPI
- **Caching**: Add CDN layer later for performance

### Generated Page Tech
- HTML5 + Tailwind CSS (CDN)
- Vanilla JavaScript for interactivity
- Client-side routing for multi-page projects
- Sandboxed iframe for preview

---

## Security Considerations

### Code Generation Safety
- AI-generated code is sanitized before storage
- XSS prevention through content security policies
- User content rendered in sandboxed iframes
- No user-editable code (view-only panel)

### Data Isolation
- Per-project KV store namespacing
- User authentication required for data persistence

### Preview Sandboxing
- Generated pages run in sandboxed iframes
- Restricted JavaScript capabilities in preview

---

## Quality Concerns to Address

### Generation Quality
- Mobile-first prompt engineering
- Consistent design system enforcement
- Template-guided generation for consistency
- Iterative refinement through conversation

### Preview Fidelity
- Accurate mobile viewport simulation
- Cross-browser testing of generated output
- Device frame preview options

---

## Monetization

- **Free for now** - Focus on user acquisition and product-market fit
- Future options: Freemium, usage-based credits, or premium features

---

## Timeline

**Target**: 2-3 months for full MVP

### Phase 1: Foundation (Weeks 1-3)
- Project scaffolding (Vite + React + FastAPI)
- Basic chat interface with streaming
- AI integration (copy Bubu's backend)
- Simple page generation and preview

### Phase 2: Core Features (Weeks 4-6)
- Template system
- Multi-page project support
- Version history
- Image upload and AI generation

### Phase 3: Publishing (Weeks 7-8)
- User authentication
- Project persistence (SQLite)
- Shareable links / subdomain routing
- KV store for dynamic pages

### Phase 4: Polish (Weeks 9-12)
- i18n (Chinese + English)
- Analytics foundation
- Template library expansion
- Performance optimization
- Security hardening

---

## Reference

- **Bubu project** (`../Bubu/`): Reference implementation for AI chat, streaming, model integration
- **Competitors**: Framer, Carrd, v0.dev, Durable

---

## Open Questions

1. How to handle AI image generation quota/costs?
2. Rate limiting strategy for free tier?
3. Analytics implementation details (self-hosted vs third-party)?
4. SEO strategy for dynamically rendered pages?

---

## Success Metrics

- User can go from idea to published page in < 5 minutes
- Generated pages score 90+ on mobile Lighthouse
- < 3 conversation turns to achieve user intent
- Zero XSS vulnerabilities in generated output
