# Phase 2: Growth (Zaoya v1)

> **Version**: v1
> **Timeline**: Months 3-4 (Post v0 Launch)
> **Complexity**: Large
> **Status**: Pending

---

## Phase Overview

Phase 2 transforms Zaoya from a page builder into a growth optimization platform. By introducing A/B testing, advanced analytics, and AI image generation, users gain the tools to iterate rapidly and measure success. This phase also launches the premium tier, establishing the monetization foundation.

### Connection to Project Goals

This phase directly supports measurability in the North Star vision. Users don't just create pages—they optimize them with data-driven decisions. The premium tier validates product-market fit and establishes sustainable revenue.

---

## Prerequisites

### From Phase 1 (Must be completed)

- [ ] Multi-page projects functional
- [ ] Vanity URLs working
- [ ] Model selector operational
- [ ] Bilingual UI complete
- [ ] User preferences system in place

### Technical Prerequisites

- [ ] Analytics event infrastructure from v0 stable
- [ ] Page versioning possible (for A/B variants)
- [ ] Image storage/CDN solution identified
- [ ] Payment provider selected (Stripe recommended)

---

## Detailed Tasks

### 1. A/B Testing & Experiments

#### 1.1 Database Schema

**Sequential: Foundation for all A/B features**

```typescript
interface Experiment {
  id: string;
  project_id: string;
  name: string;
  status: 'draft' | 'running' | 'paused' | 'completed';
  traffic_split: number[];  // [50, 50] or [70, 30]
  conversion_goal: ConversionGoal;
  start_date: Date;
  end_date?: Date;
  winner_variant_id?: string;
  created_at: Date;
}

interface Variant {
  id: string;
  experiment_id: string;
  name: string;           // 'Control', 'Variant A', 'Variant B'
  page_content: GeneratedContent;
  is_control: boolean;
  created_at: Date;
}

interface ConversionGoal {
  type: 'form_submit' | 'cta_click' | 'page_scroll' | 'time_on_page' | 'custom';
  target_element?: string;  // CSS selector for click goals
  threshold?: number;       // Scroll %, seconds, etc.
  custom_event?: string;    // For custom tracking
}

interface ExperimentResult {
  id: string;
  experiment_id: string;
  variant_id: string;
  visitors: number;
  conversions: number;
  conversion_rate: number;
  confidence: number;       // Statistical confidence %
  updated_at: Date;
}
```

**Tasks**:
- [ ] Create `experiments` table migration
- [ ] Create `variants` table with foreign key to experiments
- [ ] Create `experiment_results` table for aggregated data
- [ ] Add indexes for efficient queries
- [ ] Create experiment audit log table (status changes)

#### 1.2 Traffic Splitting

**Sequential: Core A/B functionality**

```typescript
// Traffic allocation algorithm
function allocateVisitor(
  experiment: Experiment,
  visitorId: string
): Variant {
  // Deterministic allocation based on visitor ID
  // Ensures same visitor always sees same variant
  const hash = hashString(visitorId + experiment.id);
  const bucket = hash % 100;

  let cumulative = 0;
  for (let i = 0; i < experiment.traffic_split.length; i++) {
    cumulative += experiment.traffic_split[i];
    if (bucket < cumulative) {
      return experiment.variants[i];
    }
  }
  return experiment.variants[0]; // Fallback to control
}

// Cookie-based visitor identification
function getVisitorId(req: Request): string {
  let visitorId = req.cookies.get('zaoya_visitor');
  if (!visitorId) {
    visitorId = generateUUID();
    // Set cookie in response
  }
  return visitorId;
}
```

**Tasks**:
- [ ] Implement deterministic traffic splitting algorithm
- [ ] Create visitor identification system (cookie-based)
- [ ] Build variant serving logic in page renderer
- [ ] Add experiment assignment to analytics events
- [ ] Handle experiment changes (new visitors only)
- [ ] Create traffic split configuration UI

#### 1.3 Conversion Tracking

**Parallelizable with traffic splitting**

```typescript
// Goal types and tracking
interface ConversionEvent {
  experiment_id: string;
  variant_id: string;
  visitor_id: string;
  goal_type: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

// Client-side tracking snippet (injected into published pages)
const trackingScript = `
  window.zaoyaExperiment = {
    experimentId: '${experimentId}',
    variantId: '${variantId}',
    visitorId: '${visitorId}'
  };

  // Track form submissions
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      zaoyaTrack('form_submit', { formId: form.id });
    });
  });

  // Track CTA clicks
  document.querySelectorAll('[data-zaoya-cta]').forEach(el => {
    el.addEventListener('click', () => {
      zaoyaTrack('cta_click', { element: el.dataset.zaoyaCta });
    });
  });

  // Track scroll depth
  let maxScroll = 0;
  window.addEventListener('scroll', () => {
    const scrollPercent = (window.scrollY / document.body.scrollHeight) * 100;
    if (scrollPercent > maxScroll) {
      maxScroll = scrollPercent;
      if (maxScroll >= 50) zaoyaTrack('scroll_50');
      if (maxScroll >= 75) zaoyaTrack('scroll_75');
      if (maxScroll >= 90) zaoyaTrack('scroll_90');
    }
  });
`;
```

**Tasks**:
- [ ] Create conversion events API endpoint
- [ ] Build client-side tracking library
- [ ] Implement form submission tracking
- [ ] Implement CTA click tracking
- [ ] Implement scroll depth tracking
- [ ] Implement time-on-page tracking
- [ ] Add custom event tracking API
- [ ] Create goal configuration UI

#### 1.4 Statistical Analysis

**Sequential: Depends on data collection**

```typescript
// Statistical significance calculation
interface StatisticalResult {
  winner: Variant | null;
  confidence: number;
  sampleSizeNeeded: number;
  currentSampleSize: number;
  isSignificant: boolean;
}

function calculateSignificance(
  controlConversions: number,
  controlVisitors: number,
  variantConversions: number,
  variantVisitors: number
): StatisticalResult {
  const controlRate = controlConversions / controlVisitors;
  const variantRate = variantConversions / variantVisitors;

  // Z-test for proportions
  const pooledRate = (controlConversions + variantConversions) /
                     (controlVisitors + variantVisitors);
  const se = Math.sqrt(pooledRate * (1 - pooledRate) *
             (1/controlVisitors + 1/variantVisitors));
  const zScore = (variantRate - controlRate) / se;

  // Convert to confidence
  const confidence = normalCDF(Math.abs(zScore)) * 2 - 1;

  return {
    winner: confidence >= 0.95 ?
            (variantRate > controlRate ? variant : control) : null,
    confidence,
    isSignificant: confidence >= 0.95,
    sampleSizeNeeded: calculateRequiredSampleSize(controlRate),
    currentSampleSize: controlVisitors + variantVisitors
  };
}
```

**Tasks**:
- [ ] Implement Z-test for conversion rate comparison
- [ ] Calculate required sample size for significance
- [ ] Build confidence interval calculations
- [ ] Create real-time results aggregation
- [ ] Add minimum sample size warnings
- [ ] Implement early stopping rules (optional)

#### 1.5 Experiment Management UI

**Parallelizable after schema**

```
┌────────────────────────────────────────────────────────────────────┐
│ Experiment: Homepage CTA Test                      [Pause] [End]   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Traffic Split: ████████████████░░░░ 70% Control / 30% Variant A    │
│                                                                    │
│ ┌─────────────────────┬─────────────────────┐                     │
│ │     Control         │     Variant A       │                     │
│ │                     │                     │                     │
│ │   [Preview]         │   [Preview]         │                     │
│ │                     │                     │                     │
│ │ Visitors: 1,247     │ Visitors: 534       │                     │
│ │ Conversions: 89     │ Conversions: 52     │                     │
│ │ Rate: 7.1%          │ Rate: 9.7%          │                     │
│ │                     │                     │                     │
│ └─────────────────────┴─────────────────────┘                     │
│                                                                    │
│ 📊 Statistical Confidence: 87.3%                                   │
│ ⚠️ Need ~400 more visitors for 95% confidence                      │
│                                                                    │
│ Conversion Goal: CTA Button Click ("Get Started")                  │
│ Running Since: Jan 15, 2025                                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create experiment list view
- [ ] Build experiment creation wizard
- [ ] Implement variant editor (side-by-side)
- [ ] Create traffic split slider component
- [ ] Build goal configuration UI
- [ ] Implement real-time results dashboard
- [ ] Add confidence indicator with explanation
- [ ] Create winner declaration flow
- [ ] Build experiment archive view

---

### 2. Advanced Analytics

#### 2.1 Event Collection Enhancement

**Foundation for all advanced analytics**

```typescript
// Enhanced event schema
interface AnalyticsEvent {
  id: string;
  project_id: string;
  page_slug: string;
  visitor_id: string;
  session_id: string;
  event_type: string;
  event_name: string;
  properties: Record<string, any>;
  timestamp: Date;

  // Context
  referrer: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  device_type: 'desktop' | 'mobile' | 'tablet';
  browser: string;
  country: string;
  city?: string;
}

// Session tracking
interface Session {
  id: string;
  visitor_id: string;
  project_id: string;
  started_at: Date;
  ended_at?: Date;
  page_views: number;
  events: number;
  entry_page: string;
  exit_page?: string;
  duration_seconds: number;
}
```

**Tasks**:
- [ ] Enhance event collection with session tracking
- [ ] Add UTM parameter extraction
- [ ] Implement device/browser detection
- [ ] Add geolocation (country/city) via IP
- [ ] Create event batching for performance
- [ ] Build event validation and sanitization
- [ ] Implement data retention policies

#### 2.2 Funnel Visualization

**Parallelizable after event enhancement**

```typescript
interface Funnel {
  id: string;
  project_id: string;
  name: string;
  steps: FunnelStep[];
  created_at: Date;
}

interface FunnelStep {
  name: string;
  event_type: string;
  event_name?: string;
  filters?: Record<string, any>;
}

// Example: Signup funnel
const signupFunnel: Funnel = {
  name: 'Signup Flow',
  steps: [
    { name: 'Landing Page', event_type: 'page_view', event_name: 'home' },
    { name: 'Pricing Click', event_type: 'cta_click', event_name: 'view_pricing' },
    { name: 'Plan Select', event_type: 'cta_click', event_name: 'select_plan' },
    { name: 'Form Submit', event_type: 'form_submit', event_name: 'signup' },
  ]
};

// Funnel analysis query
interface FunnelResult {
  steps: {
    name: string;
    visitors: number;
    conversion_rate: number;  // From previous step
    drop_off_rate: number;
  }[];
  overall_conversion: number;
}
```

**Tasks**:
- [ ] Design funnel data model
- [ ] Implement funnel calculation query
- [ ] Build funnel visualization component (horizontal flow)
- [ ] Add step-by-step drop-off analysis
- [ ] Create funnel builder UI
- [ ] Support date range filtering
- [ ] Add comparison view (period over period)

#### 2.3 Cohort Analysis

**Sequential: More complex analysis**

```typescript
interface CohortConfig {
  cohort_type: 'first_visit' | 'first_conversion' | 'custom';
  cohort_interval: 'day' | 'week' | 'month';
  metric: 'retention' | 'conversion' | 'revenue';
  date_range: { start: Date; end: Date };
}

// Cohort result: rows = cohorts, columns = time periods
interface CohortResult {
  cohorts: {
    label: string;        // "Jan 1-7", "Week 1", etc.
    initial_size: number;
    periods: {
      period_num: number;
      value: number;      // % retained, # conversions, $ revenue
    }[];
  }[];
}

// Example: Weekly retention cohorts
// Shows what % of users who first visited in Week X returned in Week X+1, X+2, etc.
```

**Tasks**:
- [ ] Design cohort analysis queries
- [ ] Implement retention cohort calculation
- [ ] Build cohort table visualization
- [ ] Add cohort comparison (this month vs last month)
- [ ] Create cohort configuration UI
- [ ] Support custom cohort definitions

#### 2.4 Conversion Attribution

**Parallelizable with cohorts**

```typescript
// Attribution models
type AttributionModel =
  | 'first_touch'      // Credit first interaction
  | 'last_touch'       // Credit last interaction
  | 'linear'           // Equal credit to all
  | 'time_decay'       // More credit to recent
  | 'position_based';  // 40% first, 40% last, 20% middle

interface AttributionResult {
  channels: {
    source: string;
    medium: string;
    conversions: number;
    attributed_value: number;  // % of conversions attributed
  }[];
}

// Multi-touch journey tracking
interface ConversionJourney {
  visitor_id: string;
  touchpoints: {
    timestamp: Date;
    source: string;
    medium: string;
    page: string;
  }[];
  converted_at: Date;
  conversion_type: string;
}
```

**Tasks**:
- [ ] Implement first-touch attribution
- [ ] Implement last-touch attribution
- [ ] Implement linear attribution
- [ ] Build attribution comparison view
- [ ] Create channel performance dashboard
- [ ] Add campaign ROI calculation (if cost data available)

#### 2.5 Heatmaps & Click Tracking

**Parallelizable with other analytics**

```typescript
// Click data collection
interface ClickEvent {
  page_slug: string;
  x: number;           // Percentage of viewport width
  y: number;           // Percentage of document height
  element_tag: string;
  element_text?: string;
  element_class?: string;
  timestamp: Date;
}

// Heatmap generation
interface HeatmapData {
  page_slug: string;
  resolution: { width: number; height: number };
  data_points: {
    x: number;
    y: number;
    intensity: number;  // Click count
  }[];
}
```

**Tasks**:
- [ ] Create click tracking script
- [ ] Store click coordinates efficiently
- [ ] Build heatmap rendering component
- [ ] Add element-level click aggregation
- [ ] Create scroll depth visualization
- [ ] Implement attention heatmap (time spent)
- [ ] Add device-specific heatmaps (mobile vs desktop)

#### 2.6 Analytics Dashboard

**Sequential: Brings all analytics together**

```
┌────────────────────────────────────────────────────────────────────┐
│ Analytics Dashboard: My Startup                    [Date Range ▼]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│ │   Visitors  │ │ Page Views  │ │ Bounce Rate │ │ Conversions │   │
│ │    12,458   │ │   34,892    │ │    42.3%    │ │     847     │   │
│ │   ↑ 23.4%   │ │   ↑ 18.2%   │ │   ↓ 5.1%   │ │   ↑ 31.2%   │   │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────┐    │
│ │                     Traffic Over Time                       │    │
│ │  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁                            │    │
│ └────────────────────────────────────────────────────────────┘    │
│                                                                    │
│ ┌──────────────────────┐  ┌──────────────────────┐                │
│ │   Top Pages          │  │   Traffic Sources    │                │
│ │ 1. Home (45%)        │  │ 1. Organic (38%)     │                │
│ │ 2. Pricing (23%)     │  │ 2. Direct (29%)      │                │
│ │ 3. About (18%)       │  │ 3. Social (21%)      │                │
│ │ 4. Contact (14%)     │  │ 4. Referral (12%)    │                │
│ └──────────────────────┘  └──────────────────────┘                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create dashboard layout with widget grid
- [ ] Build KPI summary cards
- [ ] Implement traffic timeline chart
- [ ] Create top pages table
- [ ] Build traffic sources breakdown
- [ ] Add geographic distribution map
- [ ] Implement device breakdown chart
- [ ] Create real-time visitors widget
- [ ] Add date range selector with presets
- [ ] Support dashboard export (PDF/CSV)

---

### 3. AI Image Generation

#### 3.1 Provider Integration

**Foundation for image generation**

```typescript
interface ImageGenerationProvider {
  id: string;
  name: string;
  endpoint: string;
  supportedSizes: string[];
  maxPromptLength: number;
  costPerImage: number;
}

const imageProviders = {
  'dalle-3': {
    name: 'DALL-E 3',
    endpoint: 'https://api.openai.com/v1/images/generations',
    supportedSizes: ['1024x1024', '1792x1024', '1024x1792'],
    maxPromptLength: 4000,
    costPerImage: 0.04,  // $0.04 per image
  },
  'stable-diffusion': {
    name: 'Stable Diffusion XL',
    endpoint: 'https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image',
    supportedSizes: ['1024x1024', '1152x896', '896x1152'],
    maxPromptLength: 2000,
    costPerImage: 0.02,
  },
};

// Generation request
interface ImageGenerationRequest {
  prompt: string;
  style?: 'photorealistic' | 'illustration' | 'abstract' | 'minimal';
  size: string;
  provider?: string;
}

// Response
interface GeneratedImage {
  id: string;
  url: string;
  prompt: string;
  provider: string;
  size: string;
  created_at: Date;
}
```

**Tasks**:
- [ ] Implement DALL-E 3 adapter
- [ ] Implement Stable Diffusion adapter (optional)
- [ ] Create unified image generation service
- [ ] Add prompt enhancement/optimization
- [ ] Implement error handling and retries
- [ ] Add content moderation check on prompts

#### 3.2 Credits System

**Sequential: Needed for usage control**

```typescript
interface UserCredits {
  user_id: string;
  image_credits: number;
  credits_used_this_month: number;
  plan_monthly_credits: number;  // From subscription
  purchased_credits: number;     // One-time purchases
}

// Credit transactions
interface CreditTransaction {
  id: string;
  user_id: string;
  amount: number;            // Positive = add, negative = use
  type: 'monthly_refresh' | 'purchase' | 'usage' | 'bonus';
  description: string;
  created_at: Date;
}

// Credit costs
const creditCosts = {
  'image_1024': 1,
  'image_1792': 2,
  'image_hd': 3,
};
```

**Tasks**:
- [ ] Create credits table and transaction log
- [ ] Implement credit check before generation
- [ ] Add credit deduction on successful generation
- [ ] Create monthly credit refresh job
- [ ] Build credit purchase flow
- [ ] Add low-credit warnings
- [ ] Implement credit usage dashboard

#### 3.3 Asset Library

**Parallelizable with credits system**

```typescript
interface Asset {
  id: string;
  user_id: string;
  project_id?: string;  // Optional: can be user-wide or project-specific
  type: 'generated' | 'uploaded';
  url: string;
  thumbnail_url: string;
  prompt?: string;       // For generated images
  filename: string;
  file_size: number;
  mime_type: string;
  dimensions: { width: number; height: number };
  tags: string[];
  created_at: Date;
}
```

**Tasks**:
- [ ] Create assets table
- [ ] Implement image upload to CDN (Cloudflare R2 or S3)
- [ ] Generate thumbnails for library view
- [ ] Build asset library UI (grid view)
- [ ] Add search by prompt/tags
- [ ] Implement drag-drop into editor
- [ ] Create asset deletion with confirmation
- [ ] Add storage usage tracking

#### 3.4 Editor Integration

**Sequential: Brings image gen into workflow**

```tsx
// Image generation modal in editor
function ImageGeneratorModal({ onSelect }) {
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const credits = useUserCredits();

  const handleGenerate = async () => {
    if (credits.available < 1) {
      toast.error('Insufficient credits');
      return;
    }
    setGenerating(true);
    const image = await generateImage({ prompt });
    setResult(image);
    setGenerating(false);
  };

  return (
    <Dialog>
      <DialogContent>
        <h2>Generate Image</h2>
        <Textarea
          placeholder="Describe the image you want..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        />
        <div className="flex justify-between items-center">
          <span>Credits: {credits.available}</span>
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? 'Generating...' : 'Generate (1 credit)'}
          </Button>
        </div>
        {result && (
          <div>
            <img src={result.url} alt={prompt} />
            <Button onClick={() => onSelect(result)}>Use Image</Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

**Tasks**:
- [ ] Create "Generate Image" button in editor toolbar
- [ ] Build generation modal with prompt input
- [ ] Show credit balance and cost
- [ ] Add style presets (photo, illustration, etc.)
- [ ] Implement image preview before use
- [ ] Add "Use in page" action
- [ ] Create regenerate option
- [ ] Show generation history
- [ ] Add prompt suggestions/examples

---

### 4. Premium Tier Launch

#### 4.1 Payment Integration

**Foundation for monetization**

```typescript
// Using Stripe
interface SubscriptionPlan {
  id: string;
  stripe_price_id: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  limits: {
    projects: number;
    pages_per_project: number;
    image_credits: number;
    custom_domain: boolean;
    analytics_retention_days: number;
  };
}

const plans: SubscriptionPlan[] = [
  {
    id: 'free',
    stripe_price_id: null,
    name: 'Free',
    price_monthly: 0,
    price_yearly: 0,
    features: ['3 projects', '1 page each', 'Basic analytics', 'Zaoya subdomain'],
    limits: {
      projects: 3,
      pages_per_project: 1,
      image_credits: 5,
      custom_domain: false,
      analytics_retention_days: 7,
    },
  },
  {
    id: 'pro',
    stripe_price_id: 'price_xxx_pro_monthly',
    name: 'Pro',
    price_monthly: 12,
    price_yearly: 120,  // 2 months free
    features: [
      'Unlimited projects',
      'Unlimited pages',
      'Advanced analytics',
      'Custom domain',
      'A/B testing',
      '50 image credits/mo',
    ],
    limits: {
      projects: -1,  // Unlimited
      pages_per_project: -1,
      image_credits: 50,
      custom_domain: true,
      analytics_retention_days: 365,
    },
  },
];
```

**Tasks**:
- [ ] Set up Stripe account and API keys
- [ ] Create Stripe products and prices
- [ ] Implement Stripe checkout session
- [ ] Handle webhook events (subscription created, cancelled, etc.)
- [ ] Create subscription status in database
- [ ] Implement plan limit checks
- [ ] Build subscription management portal link
- [ ] Add invoice history view

#### 4.2 Pricing Page

**Parallelizable with Stripe setup**

```
┌────────────────────────────────────────────────────────────────────┐
│                         Choose Your Plan                           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │     Free     │  │     Pro      │  │    Team      │             │
│  │              │  │  ⭐ Popular  │  │              │             │
│  │    $0/mo     │  │   $12/mo     │  │   $29/mo     │             │
│  │              │  │              │  │              │             │
│  │ ✓ 3 projects │  │ ✓ Unlimited  │  │ ✓ Everything │             │
│  │ ✓ 1 page ea  │  │ ✓ Unlimited  │  │   in Pro     │             │
│  │ ✓ Basic      │  │ ✓ Advanced   │  │ ✓ 5 seats    │             │
│  │   analytics  │  │   analytics  │  │ ✓ Collab     │             │
│  │              │  │ ✓ A/B test   │  │ ✓ Workflows  │             │
│  │              │  │ ✓ Custom     │  │              │             │
│  │              │  │   domain     │  │              │             │
│  │              │  │ ✓ 50 img     │  │              │             │
│  │              │  │   credits    │  │              │             │
│  │              │  │              │  │              │             │
│  │ [Current]    │  │ [Upgrade]    │  │ [Contact]    │             │
│  │              │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                    │
│                    [Annual billing: Save 17%]                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create pricing page design
- [ ] Build plan comparison component
- [ ] Add monthly/annual toggle
- [ ] Implement upgrade CTA buttons
- [ ] Show current plan indicator
- [ ] Add FAQ section
- [ ] Create enterprise contact form

#### 4.3 Feature Gating

**Sequential: Depends on subscription status**

```typescript
// Feature gate hook
function useFeatureGate(feature: string): {
  allowed: boolean;
  limit?: number;
  current?: number;
  upgradeRequired: boolean;
} {
  const user = useUser();
  const plan = user.subscription?.plan || 'free';
  const limits = plans.find(p => p.id === plan)?.limits;

  // Check specific feature
  switch (feature) {
    case 'custom_domain':
      return { allowed: limits.custom_domain, upgradeRequired: !limits.custom_domain };
    case 'projects':
      return {
        allowed: limits.projects === -1 || user.projectCount < limits.projects,
        limit: limits.projects,
        current: user.projectCount,
        upgradeRequired: limits.projects !== -1 && user.projectCount >= limits.projects,
      };
    // ... more features
  }
}

// Usage in component
function CreateProjectButton() {
  const { allowed, limit, current, upgradeRequired } = useFeatureGate('projects');

  if (upgradeRequired) {
    return <UpgradePrompt message={`You've used ${current}/${limit} projects`} />;
  }
  return <Button onClick={createProject}>New Project</Button>;
}
```

**Tasks**:
- [ ] Create feature gate utility/hook
- [ ] Implement project limit check
- [ ] Implement page-per-project limit
- [ ] Gate A/B testing to Pro+
- [ ] Gate advanced analytics to Pro+
- [ ] Gate custom domains to Pro+
- [ ] Create upgrade prompts at limit points
- [ ] Add usage meters in settings

#### 4.4 Upgrade Prompts

**Parallelizable with feature gating**

**Tasks**:
- [ ] Design upgrade prompt component
- [ ] Add prompts at feature limit points
- [ ] Create contextual upgrade messaging
- [ ] Implement trial offer (7-day Pro trial)
- [ ] Add in-app upgrade notifications
- [ ] Track upgrade prompt impressions and conversions

---

## Technical Considerations

### Database

- Consider time-series optimization for analytics data
- Implement data archival for old analytics (move to cold storage)
- Add read replicas for analytics queries (heavy reads)

### Performance

- Use background jobs for analytics aggregation
- Implement caching for dashboard data
- Consider ClickHouse or TimescaleDB for analytics (future)

### Security

- Secure Stripe webhook endpoints
- Validate all payment data server-side
- Implement rate limiting on generation endpoints
- Add abuse detection for free tier

### Scalability

- Design for horizontal scaling of analytics ingestion
- Plan for high-volume event processing
- Consider event streaming (Kafka/Redis Streams) for analytics

---

## Acceptance Criteria

### A/B Testing
- [ ] User can create experiment with control + variant
- [ ] Traffic splits correctly based on configuration
- [ ] Conversion goals track accurately
- [ ] Statistical significance calculated and displayed
- [ ] Winner can be declared and deployed

### Advanced Analytics
- [ ] Dashboard shows key metrics with trends
- [ ] Funnel builder creates multi-step funnels
- [ ] Cohort retention tables render correctly
- [ ] Heatmaps visualize click data accurately
- [ ] All analytics respect date range filters

### AI Image Generation
- [ ] Images generate from text prompts
- [ ] Credits deducted on successful generation
- [ ] Generated images appear in asset library
- [ ] Images insertable into pages from library
- [ ] Credit balance visible and accurate

### Premium Tier
- [ ] Stripe checkout completes successfully
- [ ] Subscription status updates in real-time
- [ ] Feature gates enforce plan limits
- [ ] Upgrade prompts appear at correct points
- [ ] Billing management accessible

---

## Risk Factors

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low A/B test adoption | Medium | High | Pre-built experiment templates, guided setup |
| Analytics query performance | High | Medium | Query optimization, caching, background aggregation |
| Image generation costs | Medium | Medium | Strict credit limits, usage monitoring |
| Payment integration issues | High | Low | Thorough testing, Stripe test mode |
| Statistical misinterpretation | Medium | Medium | Clear explanations, minimum sample warnings |

---

## Estimated Scope

**Overall**: Large

| Feature | Complexity | Effort |
|---------|------------|--------|
| A/B Testing | Large | 35% of phase |
| Advanced Analytics | Large | 35% of phase |
| AI Image Generation | Medium | 15% of phase |
| Premium Tier | Medium | 15% of phase |

**Key Effort Drivers**:
1. Analytics query complexity and performance
2. Statistical analysis implementation
3. Stripe integration and testing
4. Dashboard UI/UX polish

---

## Dependencies

### External
- Stripe (payments)
- OpenAI DALL-E or Stability AI (image generation)
- CDN/Object storage for generated images

### Internal (from Phase 1)
- User preferences system
- Project/page architecture
- Analytics event infrastructure

---

## Definition of Done

Phase 2 is complete when:

1. ✅ All acceptance criteria pass
2. ✅ A/B test with 1000+ visitors runs without issues
3. ✅ Analytics dashboard loads in < 3s
4. ✅ Payment flow tested end-to-end (Stripe test mode)
5. ✅ Image generation success rate > 95%
6. ✅ Feature gates prevent unauthorized access
7. ✅ Revenue tracking in place
8. ✅ Documentation updated
9. ✅ Product and finance team sign-off
