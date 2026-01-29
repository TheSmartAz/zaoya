# Zaoya (造鸭) - v1 Specification

> Evolve from single pages to the "vibe-native" web app studio

## Vision

**North Star**: "Describe a product. Get a deployable, branded, measurable web experience—fast—without code."

v1 builds on v0's proven core loop to expand into multi-page experiences, team collaboration, and growth optimization.

---

## Prerequisites

v1 begins after v0 success metrics are validated:
- Core loop working reliably (< 5 min to publish)
- Generation quality proven (> 70% first-gen acceptance)
- Security architecture battle-tested
- User feedback collected on expansion priorities

---

## v1 Features (Deferred from v0)

### 1. Multi-Page Projects

**What**: Users create linked pages within a single project (home → about → contact → pricing)

**Implementation**:
- Project contains multiple pages with shared navigation
- AI generates consistent design system across pages
- Client-side routing between pages
- Shared header/footer components
- Page management UI in editor sidebar

**URL Structure**:
```
/p/{public_id}           → project home
/p/{public_id}/about     → about page
/p/{public_id}/contact   → contact page
```

### 2. Vanity URLs

**What**: Custom URL paths for published pages

**Implementation**:
- `/u/{username}/{slug}` format
- Username claimed on signup
- Slug customizable per project
- Redirect from `/p/{id}` to vanity URL

### 3. Custom Domains

**What**: Users connect their own domains to published pages

**Implementation**:
- Domain verification via DNS TXT record
- SSL certificate provisioning (Let's Encrypt)
- CNAME pointing to `pages.zaoya.app`
- Premium feature (paid tier)

### 4. AI Image Generation

**What**: Generate custom images from text descriptions within the editor

**Implementation**:
- Integration with DALL-E / Stable Diffusion API
- "Generate image" button in chat or quick actions
- Image appears in asset library
- Usage quota per user (credits system)

### 5. Model Selector UI

**What**: Users choose which AI model generates their pages

**Implementation**:
- Dropdown in editor settings
- Available models (from Bubu config):
  - GLM-4.7 (智谱 AI)
  - DeepSeek V3
  - Doubao (字节跳动)
  - Qwen (阿里云)
  - Hunyuan (腾讯)
  - Kimi K2 (月之暗面)
  - MiniMax M2.1
- Model comparison info (speed vs quality)
- Remember user preference

### 6. Full Bilingual UI

**What**: Complete Chinese + English interface

**Implementation**:
- All UI strings translated
- Language switcher in settings
- Locale detection on first visit
- AI responses in user's preferred language
- Template content localized

### 7. A/B Testing & Experiments

**What**: Test variations of pages to optimize conversion

**Implementation**:
- Create page variants (A, B, C...)
- Traffic splitting (50/50, 70/30, etc.)
- Conversion goal definition (form submit, CTA click)
- Statistical significance calculation
- Winner selection and deployment

### 8. Advanced Analytics

**What**: Deep insights into page performance

**Implementation**:
- Funnel visualization
- Cohort analysis
- Conversion attribution
- Heatmaps (click tracking)
- Session recordings (optional)
- Custom event tracking
- Dashboard with charts

---

## v1+ Features (Future Roadmap)

### Team Collaboration

- Team workspaces with member management
- Role-based permissions (owner, editor, viewer)
- Comments and feedback on pages
- Approval workflows before publish
- Activity feed and notifications
- Version branching and merging

### Integrations Hub

- **Payments**: Stripe, PayPal
- **Email**: Mailchimp, ConvertKit, Resend
- **CRM**: HubSpot, Salesforce
- **Automation**: Zapier, Make, webhooks
- **Analytics**: Google Analytics, Mixpanel
- **Chat**: Intercom, Crisp

### Component Marketplace

- Community-created components
- Premium component packs
- Custom component submission
- Component versioning
- One-click installation

### Brand Intelligence

- Brand kit (colors, fonts, logo, voice)
- Asset library management
- Consistent generation across projects
- Brand guidelines enforcement
- Style presets

### Design System Features

- Accessibility compliance (WCAG)
- Performance guarantees (Core Web Vitals)
- Responsive breakpoint control
- Animation library
- Dark mode support

### Full-Stack Evolution

- Proper database per project (PostgreSQL)
- User authentication in generated pages
- Role-based access in generated apps
- Admin dashboards
- API endpoint generation

### Deployment & Infrastructure

- Edge rendering (Cloudflare Workers)
- CDN caching with instant purge
- Staging environments
- Rollback capability
- Uptime monitoring

### Compliance & Security

- Audit logs
- Data residency options
- GDPR compliance tools
- SOC 2 preparation
- Rate limiting tiers
- Abuse detection

### Model Orchestration

- Automatic model routing (quality/cost/latency)
- Fallback chains
- Generation quality evaluation
- Safety guardrails
- Template constraints enforcement

---

## Monetization (v1)

### Freemium Model

| Tier | Price | Limits |
|------|-------|--------|
| **Free** | $0 | 3 projects, 1 page each, basic analytics, zaoya.app subdomain |
| **Pro** | $12/mo | Unlimited projects, multi-page, custom domain, advanced analytics |
| **Team** | $29/mo | Everything in Pro + 5 seats, collaboration, approval workflows |
| **Business** | $79/mo | Everything in Team + unlimited seats, integrations, priority support |

### Usage-Based Add-ons

- AI image generation credits
- Form submission overages
- Analytics data retention
- Custom domain SSL

---

## Technical Evolution (v1)

### Database Migration

- SQLite → PostgreSQL for production
- Connection pooling
- Read replicas for analytics

### Infrastructure

- Container orchestration (Kubernetes)
- Multi-region deployment
- CDN for static assets
- Separate services:
  - Editor service
  - Generation service
  - Analytics service
  - Publishing service

### API

- Public API for integrations
- Webhook system
- OAuth provider for third-party apps

---

## v1 Timeline (Post v0 Launch)

### Phase 1: Expansion (Months 1-2)
- Multi-page projects
- Vanity URLs
- Model selector UI
- Full bilingual UI

### Phase 2: Growth (Months 3-4)
- A/B testing
- Advanced analytics
- AI image generation
- Premium tier launch

### Phase 3: Scale (Months 5-6)
- Custom domains
- Team collaboration (basic)
- First integrations (Stripe, email)
- PostgreSQL migration

### Phase 4: Platform (Months 7+)
- Component marketplace
- Brand intelligence
- Full integration hub
- Enterprise features

---

## Success Metrics (v1)

| Metric | Target |
|--------|--------|
| Monthly active projects | 10,000+ |
| Paid conversion rate | 5%+ |
| Multi-page adoption | 40% of projects |
| A/B test engagement | 20% of Pro users |
| Team workspace creation | 15% of Pro users |
| MRR | $50k+ |

---

## Migration Path

### v0 → v1 User Experience

- All v0 projects preserved
- Free tier matches v0 capabilities
- Upgrade prompts for v1 features
- No breaking changes to published pages
- Gradual feature rollout with feature flags

### Technical Migration

- Database schema versioned migrations
- API versioning (v1, v2...)
- Backward-compatible URL structure
- Published page permalinks maintained

---

## Reference

- **SPEC-v0.md**: Foundation specification
- **Bubu project**: AI integration patterns
- **Competitors**: Framer (design), Carrd (simplicity), v0.dev (AI-first), Webflow (power)
