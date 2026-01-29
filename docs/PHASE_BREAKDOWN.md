# Zaoya v0 - Phase Breakdown

> Comprehensive breakdown of the 4 development phases (8-10 weeks total)

---

## Overview

```
Phase 1: Foundation     [Weeks 1-3]  → Basic generation working end-to-end
Phase 2: Core Loop      [Weeks 4-6]  → Complete creation experience
Phase 3: Publishing     [Weeks 7-8]  → Enable publish and share
Phase 4: Forms+Analytics [Weeks 9-10] → Dynamic features and insights
```

**Core Loop to Validate**:
```
[Choose Template] → [Adaptive Interview] → [First Generation] → [Quick Action Refinement] → [Publish] → [Share Link]
```

---

# Phase 1: Foundation

**Timeline**: Weeks 1-3
**Complexity**: Large
**Goal**: Get a user from prompt to rendered mobile page preview in a working prototype

## Phase Overview

Establish the technical foundation for the entire product. By the end of Phase 1, a developer can:
1. Enter a prompt in the chat interface
2. See AI stream a response in real-time
3. View the generated mobile page in a sandboxed preview

This phase is about **proving the technical approach works** before adding user-facing polish.

## Prerequisites

- Development environment setup (Node.js, Python, etc.)
- Access to AI API keys (copy from Bubu's .env)
- Domain/hosting decisions finalized (local dev for now)

## Detailed Tasks

### 1.1 Project Scaffolding
- [ ] Initialize Vite + React + TypeScript frontend
- [ ] Initialize FastAPI backend with project structure
- [ ] Set up Tailwind CSS configuration
- [ ] Configure development proxy (Vite → FastAPI)
- [ ] Set up linting and formatting (ESLint, Prettier, Black)
- [ ] Create basic folder structure for both frontend/backend

### 1.2 Chat Interface
- [ ] Build ChatPanel component (message list + input)
- [ ] Implement message state management (Zustand or React state)
- [ ] Add streaming display (typewriter effect for AI responses)
- [ ] Style chat UI for mobile-first experience
- [ ] Handle loading states and errors gracefully

### 1.3 AI Integration
- [ ] Copy Bubu's AI service configuration (.env, model configs)
- [ ] Create FastAPI `/api/chat` endpoint with SSE streaming
- [ ] Implement system prompt for mobile page generation
- [ ] Add code extraction from AI responses (parse HTML/JS blocks)
- [ ] Handle API errors and rate limits

### 1.4 Page Generation + Preview
- [ ] Create PreviewPanel component with mobile frame
- [ ] Implement sandboxed iframe rendering
- [ ] Build page assembly logic (inject viewport, Tailwind CDN)
- [ ] Add preview refresh on generation complete
- [ ] Create view-only code panel (collapsible)

### 1.5 Sandbox Security (Basic)
- [ ] Configure iframe sandbox attributes
- [ ] Set up postMessage communication
- [ ] Create zaoya-runtime.js stub (basic helpers)
- [ ] Test isolation (preview can't access parent)

## Technical Considerations

**Frontend Architecture**:
```
src/
├── components/
│   ├── ChatPanel/
│   ├── PreviewPanel/
│   └── CodePanel/
├── hooks/
│   └── useChatStream.ts
├── stores/
│   └── chatStore.ts
└── lib/
    └── pageAssembler.ts
```

**Backend Architecture**:
```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── chat.py
│   └── services/
│       └── ai_service.py
└── requirements.txt
```

**Key Dependencies**:
- Frontend: React, Zustand, Tailwind CSS
- Backend: FastAPI, httpx (for AI API calls), python-dotenv

## Acceptance Criteria

- [ ] User can type a prompt and see AI response stream in real-time
- [ ] Generated HTML renders in sandboxed iframe
- [ ] Preview shows mobile viewport (375px width)
- [ ] Code panel shows generated HTML/JS
- [ ] Iframe cannot access parent window or cookies
- [ ] Works on localhost with hot reload

## Risk Factors

| Risk | Mitigation |
|------|------------|
| AI response quality varies | Start with simple prompts, refine system prompt iteratively |
| Streaming complexity | Reference Bubu's implementation, use SSE pattern |
| Iframe sandbox too restrictive | Test early, document what's allowed |

## Estimated Scope

- **Frontend**: ~40 hours (chat, preview, code panel, styling)
- **Backend**: ~20 hours (API, AI service, streaming)
- **Integration**: ~10 hours (testing, debugging, polish)

---

# Phase 2: Core Loop

**Timeline**: Weeks 4-6
**Complexity**: Large
**Goal**: Complete the user-facing creation experience with templates, refinement, and security

## Phase Overview

Transform the basic prototype into a usable product. Users can:
1. Start from a template category
2. Answer adaptive interview questions
3. Get a high-quality first generation
4. Refine with quick action chips
5. Revert to previous versions if needed

This phase makes the product **feel like a real tool** rather than a tech demo.

## Prerequisites

- Phase 1 complete (chat + preview working)
- System prompt refined based on Phase 1 testing
- Design decisions for template categories finalized

## Detailed Tasks

### 2.1 Template System
- [ ] Create template selection page (`/create`)
- [ ] Design 4 template category cards with descriptions
- [ ] Build template data structure (prompts, key inputs, chips)
- [ ] Implement template → system prompt injection
- [ ] Add template-specific example generations

### 2.2 Adaptive Interview Questions
- [ ] Design question flow logic (what to ask based on template)
- [ ] Create question UI component (chat-like but structured)
- [ ] Implement "Not sure—choose for me" skip option
- [ ] Build context accumulator (track known facts)
- [ ] Limit to 2-6 questions maximum

### 2.3 Quick Action Chips
- [ ] Create ChipBar component (horizontal scrollable)
- [ ] Define universal chips (10 common refinements)
- [ ] Define contextual chips per template type
- [ ] Implement chip → prompt injection
- [ ] Show chips after each generation (not during streaming)

### 2.4 Version History
- [ ] Design snapshot data structure
- [ ] Create version list UI in sidebar/panel
- [ ] Implement "Revert to version X" functionality
- [ ] Add basic "what changed" diff summary
- [ ] Store snapshots in memory (SQLite in Phase 3)

### 2.5 HTML/JS Sanitization + Validation
- [ ] Integrate DOMPurify for HTML sanitization
- [ ] Build JS AST validator (block dangerous patterns)
- [ ] Create validation pipeline (sanitize → validate → wrap)
- [ ] Add regeneration trigger on validation failure
- [ ] Log validation failures for debugging

## Technical Considerations

**Template Data Structure**:
```typescript
interface Template {
  id: string;
  name: string;
  description: string;
  icon: string;
  systemPromptAddition: string;
  interviewQuestions: Question[];
  universalChips: Chip[];
  contextualChips: Chip[];
}
```

**Validation Pipeline**:
```
Raw AI Output → DOMPurify(html) → validateJS(js) → assemblePageassemblePage(html, js) → Render
```

**Key Dependencies**:
- DOMPurify (HTML sanitization)
- acorn or esprima (JS AST parsing)

## Acceptance Criteria

- [ ] User can select from 4 template categories
- [ ] AI asks 2-6 relevant questions before generating
- [ ] Quick action chips appear after generation
- [ ] Clicking a chip triggers refinement
- [ ] Version history shows previous generations
- [ ] User can revert to any previous version
- [ ] Malicious HTML/JS is blocked or sanitized

## Risk Factors

| Risk | Mitigation |
|------|------------|
| Interview questions feel robotic | Test with real users, allow skipping |
| Quick actions don't match user intent | Start with broad actions, refine based on usage |
| Validation too strict (blocks valid code) | Allowlist approach, test extensively |
| Validation too loose (security holes) | Security audit, penetration testing |

## Estimated Scope

- **Templates + Interview**: ~25 hours
- **Quick Actions**: ~15 hours
- **Version History**: ~15 hours
- **Sanitization + Validation**: ~25 hours

---

# Phase 3: Publishing

**Timeline**: Weeks 7-8
**Complexity**: Medium
**Goal**: Enable users to publish pages and share them with the world

## Phase Overview

Add persistence and sharing capabilities. Users can:
1. Create as guest (stored in browser)
2. Sign in to save projects to server
3. Publish a draft to get a shareable link
4. View their published pages on a separate domain

This phase makes the product **shareable** — the key to virality.

## Prerequisites

- Phase 2 complete (full creation loop working)
- Database schema designed
- Hosting/domain decisions finalized
- OAuth credentials obtained (Google, email provider)

## Detailed Tasks

### 3.1 User Authentication
- [ ] Set up OAuth with Google
- [ ] Add email/password authentication option
- [ ] Create auth API endpoints (login, logout, session)
- [ ] Build login/signup UI components
- [ ] Implement auth state management (frontend)
- [ ] Add auth bypass flag for development

### 3.2 Project Persistence
- [ ] Design SQLite schema (users, projects, snapshots)
- [ ] Create project CRUD API endpoints
- [ ] Implement guest → localStorage project storage
- [ ] Build "Sign in to save" conversion flow
- [ ] Migrate guest projects on sign-in

### 3.3 Draft vs Published States
- [ ] Add project state field (draft/published)
- [ ] Create publish button and confirmation
- [ ] Generate public_id on publish
- [ ] Implement re-publish (update published snapshot)
- [ ] Show publish status in editor

### 3.4 Separate Origin Deployment
- [ ] Set up pages.zaoya.app subdomain (or equivalent)
- [ ] Configure CORS for API calls from published pages
- [ ] Implement CSP headers for published pages
- [ ] Create published page serving endpoint
- [ ] Test cookie isolation between origins

### 3.5 Shareable Links
- [ ] Create `/p/{public_id}` route on pages domain
- [ ] Build share UI (copy link button)
- [ ] Add social sharing meta tags (OG image, title, description)
- [ ] Generate preview images for sharing (optional)

## Technical Considerations

**Database Schema**:
```sql
users (id, email, name, auth_provider, created_at)
projects (id, user_id, title, template_type, status, created_at, updated_at)
snapshots (id, project_id, html, js, metadata, version, created_at)
published_pages (id, project_id, public_id, snapshot_id, published_at)
```

**Auth Flow**:
```
Guest → Create project (localStorage)
     → Sign in (Google/email)
     → Migrate project to server
     → Publish → Get shareable link
```

## Acceptance Criteria

- [ ] User can sign in with Google or email
- [ ] Guest projects persist in localStorage
- [ ] Signed-in user projects persist to database
- [ ] User can publish draft to get `/p/{id}` link
- [ ] Published page loads on pages.zaoya.app
- [ ] Published page is isolated (no auth cookies)
- [ ] Share link copies to clipboard

## Risk Factors

| Risk | Mitigation |
|------|------------|
| OAuth setup complexity | Use established libraries (authlib, etc.) |
| Guest → signed-in migration data loss | Thorough testing, backup before migrate |
| CORS/CSP configuration errors | Test in staging environment first |

## Estimated Scope

- **Authentication**: ~20 hours
- **Project Persistence**: ~15 hours
- **Draft/Published**: ~10 hours
- **Deployment + Links**: ~15 hours

---

# Phase 4: Forms + Analytics

**Timeline**: Weeks 9-10
**Complexity**: Medium
**Goal**: Add the "dynamic" features that make pages useful beyond static content

## Phase Overview

Enable interactive pages and provide insights. Users can:
1. Create pages with working forms
2. View form submissions in a dashboard
3. Export submissions as CSV
4. See basic page analytics (views, clicks)
5. Optionally receive email notifications

This phase makes pages **functional** — forms actually work, data is captured.

## Prerequisites

- Phase 3 complete (publishing working)
- Form submission API designed
- Analytics tracking approach decided
- Email service configured (optional)

## Detailed Tasks

### 4.1 Form Submission Handling
- [ ] Create form submission API endpoint
- [ ] Design submissions table schema
- [ ] Implement Zaoya.submitForm() in runtime
- [ ] Add form validation (basic)
- [ ] Return success/error responses to form
- [ ] Handle spam protection (basic rate limiting)

### 4.2 Submission Dashboard
- [ ] Create submissions list view in dashboard
- [ ] Add project selector (filter by project)
- [ ] Display submission data in table format
- [ ] Add pagination for large datasets
- [ ] Implement CSV export functionality

### 4.3 Basic Analytics
- [ ] Design analytics events table
- [ ] Implement Zaoya.track() in runtime
- [ ] Track page views automatically
- [ ] Track CTA clicks (via data attributes)
- [ ] Track form submissions
- [ ] Create simple analytics dashboard (counts, charts)

### 4.4 Email Notifications (Optional)
- [ ] Integrate email service (Resend, SendGrid, etc.)
- [ ] Create notification settings UI
- [ ] Implement submission → email trigger
- [ ] Design email template for notifications
- [ ] Add enable/disable toggle per project

### 4.5 Security Hardening
- [ ] Review and tighten CSP headers
- [ ] Add rate limiting to all endpoints
- [ ] Implement input validation everywhere
- [ ] Security audit of sanitization pipeline
- [ ] Add logging for suspicious activity
- [ ] Test for common vulnerabilities (XSS, CSRF, injection)

## Technical Considerations

**Runtime API (zaoya-runtime.js)**:
```javascript
window.Zaoya = {
  submitForm: async (formData) => { /* POST to API */ },
  track: (event, data) => { /* POST to analytics API */ },
  toast: (message) => { /* Show toast notification */ },
  navigate: (path) => { /* Client-side navigation */ }
};
```

**Analytics Schema**:
```sql
analytics_events (
  id, page_id, event_type, event_data,
  session_id, user_agent, ip_hash, created_at
)
```

## Acceptance Criteria

- [ ] Forms on published pages submit to API
- [ ] Submissions appear in dashboard
- [ ] User can export submissions as CSV
- [ ] Page views are tracked and displayed
- [ ] CTA clicks are tracked
- [ ] Email notifications work (if enabled)
- [ ] Rate limiting prevents abuse
- [ ] No XSS vulnerabilities in generated pages

## Risk Factors

| Risk | Mitigation |
|------|------------|
| Form spam | Rate limiting, honeypot fields, CAPTCHA (later) |
| Analytics data volume | Aggregate data, limit retention period |
| Email deliverability | Use established service, verify domain |
| Security vulnerabilities | Thorough testing, security audit |

## Estimated Scope

- **Form Handling**: ~20 hours
- **Dashboard + Export**: ~15 hours
- **Analytics**: ~20 hours
- **Email Notifications**: ~10 hours
- **Security Hardening**: ~15 hours

---

# Phase Dependencies

```
Phase 1: Foundation
    ↓
Phase 2: Core Loop
    ↓
Phase 3: Publishing
    ↓
Phase 4: Forms + Analytics
```

All phases are sequential — each builds on the previous.

---

# Success Criteria (Full v0)

| Metric | Target | Measured After |
|--------|--------|----------------|
| Idea to published | < 5 minutes | Phase 3 |
| Conversation turns | < 3 turns | Phase 2 |
| Mobile Lighthouse score | 90+ | Phase 1 |
| XSS vulnerabilities | Zero | Phase 4 |
| First-gen acceptance | > 70% | Phase 2 |

---

# Open Questions

1. **Default AI model**: Which model from Bubu's config should be default?
2. **Image uploads**: Size limits? Allowed formats? Storage location?
3. **Rate limiting**: Requests per minute for guests vs signed-in?
4. **Analytics approach**: Self-hosted (Plausible) vs custom tables?
5. **Email service**: Resend, SendGrid, or custom SMTP?
