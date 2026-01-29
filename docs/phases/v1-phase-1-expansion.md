# Phase 1: Expansion (Zaoya v1)

> **Version**: v1
> **Timeline**: Months 1-2 (Post v0 Launch)
> **Complexity**: Large
> **Status**: Pending

---

## Phase Overview

Phase 1 transforms Zaoya from a single-page generator into a multi-page web app studio. This phase establishes the foundation for professional-grade web experiences by introducing project structures, personalized URLs, AI model flexibility, and full internationalization.

### Connection to Project Goals

This phase directly supports the North Star vision: *"Describe a product. Get a deployable, branded, measurable web experience—fast—without code."* By enabling multi-page projects with consistent design systems, users can create complete websites (home → about → contact → pricing) rather than isolated landing pages.

---

## Prerequisites

### From v0 (Must be validated)

- [ ] Core loop working reliably (< 5 min to publish)
- [ ] Generation quality proven (> 70% first-gen acceptance)
- [ ] Security architecture battle-tested
- [ ] User feedback collected on expansion priorities
- [ ] Basic analytics infrastructure operational
- [ ] Template system functional

### Technical Prerequisites

- [ ] Existing page schema supports extension to multi-page
- [ ] Editor component architecture allows sidebar additions
- [ ] Routing infrastructure can handle nested paths
- [ ] AI generation pipeline supports context passing (for design consistency)

---

## Detailed Tasks

### 1. Multi-Page Projects

#### 1.1 Database Schema Extensions

**Sequential: Must complete first**

```typescript
// New tables/columns needed
interface Project {
  id: string;
  public_id: string;        // For URLs like /p/{public_id}
  user_id: string;
  name: string;
  design_system: DesignSystem;  // Shared across pages
  navigation: NavigationConfig;
  created_at: Date;
  updated_at: Date;
}

interface Page {
  id: string;
  project_id: string;
  slug: string;             // 'about', 'contact', etc.
  title: string;
  content: GeneratedContent;
  order: number;            // For navigation ordering
  is_home: boolean;
  created_at: Date;
  updated_at: Date;
}

interface DesignSystem {
  colors: ColorPalette;
  typography: TypographyConfig;
  spacing: SpacingScale;
  components: ComponentStyles;
}

interface NavigationConfig {
  header: HeaderConfig;
  footer: FooterConfig;
  pages: NavigationItem[];
}
```

**Tasks**:
- [ ] Create migration for `projects` table
- [ ] Create migration for `pages` table with foreign key to projects
- [ ] Add `design_system` JSON column to projects
- [ ] Add `navigation` JSON column to projects
- [ ] Create indexes for `project_id` and `slug` lookups
- [ ] Update existing single-page data to new schema (migration script)

#### 1.2 API Endpoints

**Parallelizable after schema**

```typescript
// Project endpoints
POST   /api/projects                    // Create new project
GET    /api/projects                    // List user's projects
GET    /api/projects/:id                // Get project with pages
PUT    /api/projects/:id                // Update project settings
DELETE /api/projects/:id                // Delete project and all pages

// Page endpoints
POST   /api/projects/:id/pages          // Create page in project
GET    /api/projects/:id/pages/:slug    // Get specific page
PUT    /api/projects/:id/pages/:slug    // Update page content
DELETE /api/projects/:id/pages/:slug    // Delete page
PUT    /api/projects/:id/pages/reorder  // Reorder navigation

// Design system endpoints
GET    /api/projects/:id/design-system  // Get design tokens
PUT    /api/projects/:id/design-system  // Update design tokens
POST   /api/projects/:id/design-system/apply  // Apply to all pages
```

**Tasks**:
- [ ] Implement project CRUD endpoints
- [ ] Implement page CRUD endpoints within projects
- [ ] Implement design system sync endpoint
- [ ] Add validation for unique slugs within project
- [ ] Add authorization checks (user owns project)
- [ ] Write API tests for all endpoints

#### 1.3 AI Generation Updates

**Sequential: Depends on schema and API**

The AI must generate pages that share a consistent design system:

```typescript
interface MultiPageGenerationContext {
  project: Project;
  existingPages: Page[];
  designSystem: DesignSystem;
  targetPage: {
    type: 'home' | 'about' | 'contact' | 'pricing' | 'custom';
    userPrompt: string;
  };
}

// Updated system prompt additions
const designSystemPrompt = `
You are generating a page that is part of a multi-page website.
Maintain consistency with the established design system:
- Primary color: ${designSystem.colors.primary}
- Typography: ${designSystem.typography.fontFamily}
- Spacing scale: ${designSystem.spacing}

The navigation should include: ${pages.map(p => p.title).join(', ')}
`;
```

**Tasks**:
- [ ] Update generation service to accept project context
- [ ] Create design system extraction from first page
- [ ] Implement design token injection into subsequent generations
- [ ] Add navigation component generation with all project pages
- [ ] Create shared header/footer component templates
- [ ] Test cross-page design consistency
- [ ] Add regeneration option that preserves design system

#### 1.4 Editor UI Updates

**Parallelizable with API work**

```
┌─────────────────────────────────────────────────────────────┐
│ Project: My Startup                              [Settings] │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  📄 Home     │         [Page Preview/Editor]                │
│  📄 About    │                                              │
│  📄 Pricing  │                                              │
│  📄 Contact  │                                              │
│              │                                              │
│  [+ Add Page]│                                              │
│              │                                              │
│  ─────────── │                                              │
│  🎨 Design   │                                              │
│  ⚙️ Settings │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create page sidebar component with drag-reorder
- [ ] Implement page switching without full reload
- [ ] Add "New Page" dialog with page type selection
- [ ] Create design system panel (colors, fonts, spacing)
- [ ] Add page deletion with confirmation
- [ ] Implement page duplication feature
- [ ] Create project settings modal (name, default page)
- [ ] Add keyboard shortcuts (Cmd+1-9 for page switching)

#### 1.5 Client-Side Routing

**Sequential: Depends on URL structure decision**

```typescript
// Published page routing
/p/{public_id}           → Loads project home page
/p/{public_id}/about     → Loads about page
/p/{public_id}/contact   → Loads contact page

// Implementation approach: Client-side SPA routing in published pages
// Generated code includes:
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter basename="/p/abc123">
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactPage />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}
```

**Tasks**:
- [ ] Update published page template to include router
- [ ] Generate route configuration from project pages
- [ ] Implement shared layout wrapper (header/footer)
- [ ] Add 404 handling for unknown routes within project
- [ ] Ensure SEO-friendly rendering (meta tags per page)
- [ ] Test deep linking (direct navigation to /p/id/about)
- [ ] Add smooth page transitions (optional)

---

### 2. Vanity URLs

#### 2.1 Username System

**Sequential: Foundation for vanity URLs**

```typescript
interface User {
  // Existing fields...
  username: string;  // Unique, URL-safe
}

// Validation rules
const usernameRules = {
  minLength: 3,
  maxLength: 30,
  pattern: /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/,
  reserved: ['admin', 'api', 'www', 'app', 'help', 'support', ...],
};
```

**Tasks**:
- [ ] Add `username` column to users table (unique constraint)
- [ ] Create username claiming flow on signup
- [ ] Implement username validation (length, characters, reserved words)
- [ ] Add username change feature (with cooldown period)
- [ ] Create username availability check API
- [ ] Handle case-insensitivity (store lowercase, display original)

#### 2.2 Project Slugs

**Parallelizable with username system**

```typescript
interface Project {
  // Existing fields...
  slug: string;  // Unique per user
}

// URL: /u/{username}/{slug}
// Example: /u/johndoe/my-startup
```

**Tasks**:
- [ ] Add `slug` column to projects table
- [ ] Auto-generate slug from project name
- [ ] Allow custom slug editing
- [ ] Validate uniqueness within user's projects
- [ ] Create slug suggestion on name conflict

#### 2.3 URL Routing & Redirects

**Sequential: Depends on username and slug**

```typescript
// Route priorities:
// 1. /u/{username}/{slug} → Vanity URL (primary)
// 2. /p/{public_id}       → Legacy URL (redirect to vanity)

// Server-side routing
app.get('/u/:username/:slug', async (req, res) => {
  const { username, slug } = req.params;
  const project = await findProjectByUsernameAndSlug(username, slug);
  if (!project) return res.status(404);
  return renderProject(project, res);
});

app.get('/p/:publicId', async (req, res) => {
  const project = await findProjectByPublicId(req.params.publicId);
  if (!project) return res.status(404);
  // Redirect to vanity URL if available
  if (project.user.username && project.slug) {
    return res.redirect(301, `/u/${project.user.username}/${project.slug}`);
  }
  return renderProject(project, res);
});
```

**Tasks**:
- [ ] Implement /u/:username/:slug route handler
- [ ] Add 301 redirect from /p/:id to vanity URL
- [ ] Preserve deep links in redirect (/p/id/about → /u/user/slug/about)
- [ ] Update all internal links to use vanity URLs
- [ ] Add canonical URL meta tags
- [ ] Create URL copy feature in editor (vanity URL)
- [ ] Handle username/slug changes (update links, consider redirect period)

---

### 3. Model Selector UI

#### 3.1 Model Configuration

**Foundation task**

```typescript
interface AIModel {
  id: string;
  name: string;
  displayName: string;
  provider: string;
  description: string;
  characteristics: {
    speed: 'fast' | 'medium' | 'slow';
    quality: 'standard' | 'high' | 'premium';
    costTier: 'low' | 'medium' | 'high';
  };
  available: boolean;
  endpoint: string;
  apiKeyEnvVar: string;
}

const availableModels: AIModel[] = [
  {
    id: 'glm-4.7',
    name: 'GLM-4.7',
    displayName: 'GLM-4.7 (智谱 AI)',
    provider: 'zhipu',
    description: 'Balanced speed and quality, good for most use cases',
    characteristics: { speed: 'fast', quality: 'high', costTier: 'medium' },
    available: true,
    endpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    apiKeyEnvVar: 'ZHIPU_API_KEY',
  },
  {
    id: 'deepseek-v3',
    name: 'DeepSeek V3',
    displayName: 'DeepSeek V3',
    provider: 'deepseek',
    description: 'Excellent code generation, very cost-effective',
    characteristics: { speed: 'fast', quality: 'high', costTier: 'low' },
    available: true,
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    apiKeyEnvVar: 'DEEPSEEK_API_KEY',
  },
  {
    id: 'doubao',
    name: 'Doubao',
    displayName: 'Doubao (字节跳动)',
    provider: 'bytedance',
    description: 'Strong Chinese language understanding',
    characteristics: { speed: 'fast', quality: 'standard', costTier: 'low' },
    available: true,
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    apiKeyEnvVar: 'DOUBAO_API_KEY',
  },
  {
    id: 'qwen',
    name: 'Qwen',
    displayName: 'Qwen (阿里云)',
    provider: 'alibaba',
    description: 'Versatile model with good reasoning',
    characteristics: { speed: 'medium', quality: 'high', costTier: 'medium' },
    available: true,
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    apiKeyEnvVar: 'DASHSCOPE_API_KEY',
  },
  {
    id: 'hunyuan',
    name: 'Hunyuan',
    displayName: 'Hunyuan (腾讯)',
    provider: 'tencent',
    description: 'Strong multi-modal capabilities',
    characteristics: { speed: 'medium', quality: 'high', costTier: 'medium' },
    available: true,
    endpoint: 'https://hunyuan.tencentcloudapi.com/',
    apiKeyEnvVar: 'HUNYUAN_API_KEY',
  },
  {
    id: 'kimi-k2',
    name: 'Kimi K2',
    displayName: 'Kimi K2 (月之暗面)',
    provider: 'moonshot',
    description: 'Excellent long-context handling',
    characteristics: { speed: 'medium', quality: 'premium', costTier: 'high' },
    available: true,
    endpoint: 'https://api.moonshot.cn/v1/chat/completions',
    apiKeyEnvVar: 'MOONSHOT_API_KEY',
  },
  {
    id: 'minimax-m2.1',
    name: 'MiniMax M2.1',
    displayName: 'MiniMax M2.1',
    provider: 'minimax',
    description: 'Fast responses, good for iteration',
    characteristics: { speed: 'fast', quality: 'standard', costTier: 'low' },
    available: true,
    endpoint: 'https://api.minimax.chat/v1/text/chatcompletion_v2',
    apiKeyEnvVar: 'MINIMAX_API_KEY',
  },
];
```

**Tasks**:
- [ ] Create model configuration file with all supported models
- [ ] Implement model availability check (API key presence)
- [ ] Create model adapter interface for unified API calls
- [ ] Add fallback logic when selected model unavailable
- [ ] Write tests for each model adapter

#### 3.2 User Preferences Storage

**Parallelizable with configuration**

```typescript
interface UserPreferences {
  preferredModel: string;
  language: 'en' | 'zh';
  // Future preferences...
}

// Store in user profile or localStorage for anonymous users
```

**Tasks**:
- [ ] Add `preferences` JSON column to users table
- [ ] Create preferences API endpoints (GET/PUT)
- [ ] Implement localStorage fallback for anonymous users
- [ ] Sync localStorage to database on login

#### 3.3 Model Selector Component

**Depends on configuration and preferences**

```tsx
function ModelSelector() {
  const [selectedModel, setSelectedModel] = useState(userPreference);

  return (
    <Select value={selectedModel} onValueChange={handleModelChange}>
      <SelectTrigger>
        <SelectValue placeholder="Select AI Model" />
      </SelectTrigger>
      <SelectContent>
        {availableModels.map(model => (
          <SelectItem key={model.id} value={model.id}>
            <div className="flex items-center gap-2">
              <span>{model.displayName}</span>
              <Badge variant={model.characteristics.speed}>
                {model.characteristics.speed}
              </Badge>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```

**Tasks**:
- [ ] Create ModelSelector dropdown component
- [ ] Add model comparison tooltip/info panel
- [ ] Show speed/quality/cost indicators
- [ ] Implement model switching without page reload
- [ ] Add "Recommended" badge for default model
- [ ] Remember selection across sessions
- [ ] Show current generation queue/status per model (optional)

#### 3.4 Generation Service Updates

**Sequential: Must integrate with selectors**

**Tasks**:
- [ ] Update generation endpoint to accept model parameter
- [ ] Implement model routing in backend
- [ ] Add model-specific prompt adjustments if needed
- [ ] Log model usage for analytics
- [ ] Handle model-specific rate limits
- [ ] Implement graceful fallback on model errors

---

### 4. Full Bilingual UI (Chinese + English)

#### 4.1 i18n Infrastructure

**Foundation: Must complete first**

```typescript
// Using next-intl or similar
// File structure:
// locales/
//   en.json
//   zh.json

// en.json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "create": "Create",
    "edit": "Edit"
  },
  "editor": {
    "newPage": "New Page",
    "pageTitle": "Page Title",
    "generateContent": "Generate Content",
    "publishing": "Publishing..."
  },
  "models": {
    "selectModel": "Select AI Model",
    "speed": "Speed",
    "quality": "Quality"
  }
}

// zh.json
{
  "common": {
    "save": "保存",
    "cancel": "取消",
    "delete": "删除",
    "create": "创建",
    "edit": "编辑"
  },
  "editor": {
    "newPage": "新建页面",
    "pageTitle": "页面标题",
    "generateContent": "生成内容",
    "publishing": "发布中..."
  },
  "models": {
    "selectModel": "选择 AI 模型",
    "speed": "速度",
    "quality": "质量"
  }
}
```

**Tasks**:
- [ ] Install and configure i18n library (next-intl recommended)
- [ ] Create locale files structure
- [ ] Set up middleware for locale detection
- [ ] Create translation hook/component wrapper
- [ ] Configure build for locale bundling

#### 4.2 UI String Extraction

**Parallelizable after infrastructure**

**Tasks**:
- [ ] Audit all hardcoded strings in components
- [ ] Extract strings to locale files
- [ ] Replace hardcoded strings with translation calls
- [ ] Handle pluralization rules
- [ ] Handle date/number formatting per locale

#### 4.3 Language Switcher

**Parallelizable with extraction**

```tsx
function LanguageSwitcher() {
  const { locale, setLocale } = useLocale();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        {locale === 'en' ? '🇺🇸 English' : '🇨🇳 中文'}
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => setLocale('en')}>
          🇺🇸 English
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setLocale('zh')}>
          🇨🇳 中文
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

**Tasks**:
- [ ] Create language switcher component
- [ ] Add to header/settings menu
- [ ] Store preference in user profile/localStorage
- [ ] Implement locale detection on first visit (Accept-Language header)
- [ ] Handle URL-based locale (optional: /en/editor, /zh/editor)

#### 4.4 AI Response Localization

**Sequential: Depends on preferences**

```typescript
// System prompt addition
const localizedSystemPrompt = locale === 'zh'
  ? '请使用中文回复用户，生成的内容也应该是中文。'
  : 'Respond in English. Generated content should be in English.';

// Content locale can differ from UI locale
interface GenerationRequest {
  prompt: string;
  uiLocale: 'en' | 'zh';      // For AI's response language
  contentLocale: 'en' | 'zh';  // For generated page content
}
```

**Tasks**:
- [ ] Add locale parameter to generation requests
- [ ] Update system prompts with locale instructions
- [ ] Allow separate UI locale and content locale
- [ ] Test generation quality in both languages
- [ ] Add language indicator in generated content

#### 4.5 Template Localization

**Parallelizable with AI localization**

**Tasks**:
- [ ] Create Chinese versions of all templates
- [ ] Localize template names and descriptions
- [ ] Add locale tag to templates
- [ ] Show templates in user's preferred language
- [ ] Handle template search in both languages

---

## Technical Considerations

### Database

- **Choice**: Continue with SQLite for Phase 1, plan PostgreSQL migration for Phase 3
- **Migrations**: Use Drizzle migrations with reversibility
- **Indexes**: Add composite index on (user_id, slug) for vanity URL lookups

### State Management

- Consider Zustand or Jotai for editor state (multi-page context)
- Implement optimistic updates for page operations
- Cache design system to avoid refetching

### Performance

- Lazy load page content in editor sidebar
- Implement virtual scrolling for projects with many pages
- Consider ISR (Incremental Static Regeneration) for published pages

### Security

- Validate all slugs and usernames server-side
- Rate limit username/slug changes
- Sanitize all user input in URLs

---

## Acceptance Criteria

### Multi-Page Projects
- [ ] User can create a project with multiple pages
- [ ] Pages share consistent navigation (header/footer)
- [ ] Design system (colors, fonts) consistent across pages
- [ ] Pages can be reordered via drag-and-drop
- [ ] Published project has working client-side routing
- [ ] Deep links work (direct navigation to /p/id/about)

### Vanity URLs
- [ ] User can claim a unique username
- [ ] User can set custom slugs for projects
- [ ] /u/username/slug URLs resolve correctly
- [ ] Legacy /p/id URLs redirect to vanity URLs
- [ ] Multi-page routes work with vanity URLs

### Model Selector
- [ ] All 7 models available in selector
- [ ] Model characteristics displayed (speed/quality)
- [ ] Selection persists across sessions
- [ ] Generation uses selected model
- [ ] Graceful fallback on model errors

### Bilingual UI
- [ ] All UI strings translated to Chinese
- [ ] Language switcher accessible in settings
- [ ] Locale detected on first visit
- [ ] AI responds in user's preferred language
- [ ] Templates available in both languages

---

## Risk Factors

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Design system inconsistency across pages | Medium | High | Strong prompt engineering, visual regression tests |
| Model API instability | High | Medium | Fallback chains, health checks, circuit breakers |
| Username squatting | Low | Medium | Reserved words list, abuse reporting |
| i18n string coverage gaps | Low | High | Automated string extraction, CI checks |
| Performance degradation with many pages | Medium | Low | Pagination, lazy loading, virtualization |

---

## Estimated Scope

**Overall**: Large

| Feature | Complexity | Effort |
|---------|------------|--------|
| Multi-Page Projects | Large | 40% of phase |
| Vanity URLs | Medium | 20% of phase |
| Model Selector | Medium | 15% of phase |
| Bilingual UI | Large | 25% of phase |

**Key Effort Drivers**:
1. AI prompt engineering for design consistency
2. Database schema design for flexibility
3. Complete i18n coverage
4. Editor UI complexity

---

## Dependencies

### External
- AI model APIs (GLM, DeepSeek, Doubao, Qwen, Hunyuan, Kimi, MiniMax)
- i18n library (next-intl or react-i18next)

### Internal (from v0)
- Existing editor component architecture
- Template system
- Analytics infrastructure
- User authentication

---

## Definition of Done

Phase 1 is complete when:

1. ✅ All acceptance criteria pass
2. ✅ Unit tests cover critical paths (>80% coverage on new code)
3. ✅ Integration tests for multi-page publishing flow
4. ✅ E2E tests for complete user journeys
5. ✅ Performance benchmarks met (page load < 2s)
6. ✅ Security audit passed (no new vulnerabilities)
7. ✅ Documentation updated (API docs, user guides)
8. ✅ Staging environment validated
9. ✅ Product team sign-off
