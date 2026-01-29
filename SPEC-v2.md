# Zaoya (造鸭) - v2 Specification

> **"Describe it. See it. Share it." — Evolved**
>
> v2 refines the core experience with **adaptive interview flow**, **chat-first creation**, and **single orchestrator architecture**.

---

## Vision v2

**North Star**: "Just describe what you want—in plain language—and get a polished, mobile-first web page."

v2 focuses on:
1. **Adaptive Interview** - AI generates custom questions based on project complexity (2-50 questions)
2. **Dynamic Question Planning** - Questions adapt to what user mentions, not a fixed template
3. **Product Document** - Show build plan before generating code
4. **User Control** - Always-visible "Generate now" button, skip anytime

---

## Core Loop (v2)

```
[User Input] → [Complexity Analysis] → [Adaptive Interview] → [Build Plan] → [Generate Code]
     ↓                ↓                      ↓                    ↓              ↓
  First message   AI assesses        Questions grouped      Pages/sections   Final HTML
                  complexity &       by topic (1-3 per      shown to user
                  generates plan     message), adaptive
```

---

## Interview Flow (v2 Core Feature)

### Design Philosophy

**Key insight from research**: Wix asks 4-5 questions; v0.dev and Framer ask zero (generate-first). Zaoya takes the interview-first approach but with **adaptive complexity**:

- **Simple project** (birthday invite): 2-3 questions
- **Medium project** (landing page): 4-8 questions
- **Complex project** (SaaS tool): 15-50 questions

The 6 "reference categories" (scope, audience, goals, features, brand, constraints) are guidance for the LLM, **not a fixed template**.

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Adaptive Interview User Journey                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User sends first message                                                │
│     "I want to build a search engine website for high school students"      │
│                                  ↓                                          │
│  2. AI Complexity Analysis (internal, 1 LLM call)                           │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  Complexity: HIGH                                                │     │
│     │  Already known: audience (high school students), type (search)   │     │
│     │  Questions needed: ~12-15 (grouped into 5-6 messages)            │     │
│     │  Topics to cover: scope, content, business model, tech, design   │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                  ↓                                          │
│  3. Agent Callout (UI decoration)                                           │
│     "RequirementsAgent, UXAgent, TechAgent consulting..."                   │
│                                  ↓                                          │
│  4. Adaptive Interview (grouped questions, 1 LLM call per turn)             │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  Message 1 (Product Scope):                                      │     │
│     │  "Let me understand what you're building:                        │     │
│     │   1. What kind of search engine are you trying to build?         │     │
│     │      ○ Academic resources  ○ General web  ○ Specific topic       │     │
│     │   2. What content will students search through?                  │     │
│     │      ○ Textbooks  ○ Research papers  ○ Custom database           │     │
│     │   3. Will this be web-only or also mobile?"                      │     │
│     │      ○ Web only  ○ Mobile app  ○ Both                            │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│     User answers (may answer 2 of 3)...                                     │
│                                  ↓                                          │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  Message 2 (Business Model):                                     │     │
│     │  "Now about the business side:                                   │     │
│     │   1. What is your business model for this tool?                  │     │
│     │      ○ Free  ○ Subscription  ○ Freemium  ○ Ad-supported          │     │
│     │   2. Do you need user accounts/authentication?"                  │     │
│     │      ○ Yes  ○ No  ○ Optional                                     │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│     User answers...                                                         │
│                                  ↓                                          │
│     ... (AI adjusts remaining questions based on answers) ...               │
│                                  ↓                                          │
│  5. Build Plan (user-facing)                                                │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  📋 Build Plan                                                   │     │
│     │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │     │
│     │                                                                  │     │
│     │  Pages:                                                          │     │
│     │  ├── Home (search interface, hero, features)                     │     │
│     │  ├── Results (search results, filters, pagination)               │     │
│     │  ├── Pricing (freemium tiers, CTA)                               │     │
│     │  └── About (team, mission)                                       │     │
│     │                                                                  │     │
│     │  Features: User auth, Search API, Analytics                      │     │
│     │  Design: Modern, professional, blue palette                      │     │
│     │                                                                  │     │
│     │  [Generate] [Edit via chat]                                      │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                  ↓                                          │
│  6. Generate pages sequentially                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Simple Project Example (Birthday Invite)

```
User: "我要给女儿办5岁生日派对邀请函"

AI Analysis:
- Complexity: LOW
- Already known: event type (birthday), audience (daughter, 5 years old)
- Questions needed: 3 (in 1-2 messages)

Message 1:
"让我帮你创建一个漂亮的邀请函！几个快速问题：
 1. 派对什么时候举办？
    ○ 这周末  ○ 下周末  ○ 具体日期：____
 2. 在哪里举办？
    ○ 家里  ○ 餐厅/酒店  ○ 户外  ○ 其他：____
 3. 大概多少人参加？
    ○ 10人以下  ○ 10-20人  ○ 20-30人  ○ 30人以上"

User answers...

→ Brief generated → Build Plan shown → Generate
```

### Interview State Machine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Interview Orchestrator States                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   [not_started]                                                         │
│        ↓  (user sends first message)                                    │
│   [analyzing]  → AI assesses complexity, generates initial plan         │
│        ↓                                                                │
│   [in_progress]                                                         │
│        │                                                                │
│        ├──→ User answers → Extract info → Update brief                  │
│        │         ↓                                                      │
│        │    AI decides:                                                 │
│        │    - Follow-up on unanswered? (if partial answer)              │
│        │    - Next topic group?                                         │
│        │    - Enough info? → [finishing]                                │
│        │    - User impatient? → [finishing]                             │
│        │         ↓                                                      │
│        ├──→ User clicks "Skip" → Use defaults, continue                 │
│        │                                                                │
│        ├──→ User clicks "Generate now" → [finishing]                    │
│        │                                                                │
│        └──→ User sends off-topic → Pause, handle, return to question    │
│                                                                         │
│   [finishing]                                                           │
│        ↓                                                                │
│   Generate Brief (internal) → Product Document → Build Plan (shown)     │
│        ↓                                                                │
│   [done]                                                                │
│        ↓                                                                │
│   Generate code (pages sequentially)                                    │
│                                                                         │
│   [skipped] ← User clicks "Skip all" at any point                       │
│        ↓                                                                │
│   Use defaults → Generate immediately                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### User Controls (Always Visible)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Question 7                              [Skip] [Generate now]          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Now about the technical requirements:                                  │
│                                                                         │
│  1. Do you need user authentication?                                    │
│     ○ Yes, required  ○ Optional  ○ No                                   │
│                                                                         │
│  2. Any third-party integrations needed?                                │
│     ☐ Payment (Stripe)  ☐ Analytics  ☐ Email  ☐ Social login           │
│     ☐ None  ☐ Other: ____                                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Type your answers or select options above...                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Send]                                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Question Data Structure

```typescript
// Interview State (stored on draft.interview_state)
interface InterviewState {
  status: 'not_started' | 'in_progress' | 'finishing' | 'done' | 'skipped';
  complexity: 'low' | 'medium' | 'high';

  // Dynamic question plan (generated by AI, can be modified mid-interview)
  question_plan: QuestionGroup[];
  current_group_index: number;

  // Collected data
  asked: AskedQuestion[];
  answers: CollectedAnswer[];

  // Brief (internal, structured data)
  brief: ProjectBrief;
}

// Questions grouped by topic (up to 3 questions per group)
interface QuestionGroup {
  id: string;
  topic: string;  // e.g., "product_scope", "business_model", "technical"
  topic_label: string;  // e.g., "Product Scope", "Business Model"
  questions: Question[];
  is_completed: boolean;
}

// Individual question with multiple choice options
interface Question {
  id: string;
  text: string;
  type: 'single_select' | 'multi_select' | 'text' | 'date';  // AI decides per question
  options?: QuestionOption[];  // All questions have options + free text
  allow_other: boolean;  // Always true - user can type custom response
  slot: string;  // Brief field this fills, e.g., "primary_goal"
  default_value?: any;
}

interface QuestionOption {
  value: string;
  label: string;
  description?: string;  // Optional explanation
}

interface AskedQuestion {
  question_id: string;
  group_id: string;
  text: string;
  asked_at: number;
}

interface CollectedAnswer {
  question_id: string;
  raw_text: string;  // User's actual input
  selected_options?: string[];  // If options were selected
  extracted: Record<string, any>;  // Structured data extracted by AI
  answered_at: number;
  is_partial: boolean;  // True if only some questions in group answered
}

// Project Brief (internal, feeds into Product Document)
interface ProjectBrief {
  project_type: string | null;
  complexity: 'low' | 'medium' | 'high';

  // Core slots (reference categories)
  scope: {
    type: string | null;  // e.g., "search engine", "landing page"
    pages: string[];
    features: string[];
  };
  audience: {
    who: string | null;
    context: string | null;
    size: string | null;
  };
  goals: {
    primary_goal: string | null;
    success_criteria: string | null;
    cta: string | null;
  };
  content: {
    sections: string[];
    assets: {
      logo: string | null;  // URL or "generate"
      images: string[];
      copy: string | null;
    };
  };
  design: {
    style: string | null;
    colors: string[];
    mood: string | null;
  };
  technical: {
    auth_required: boolean | null;
    integrations: string[];
    constraints: string[];
  };

  // Metadata
  language: string;  // Auto-detected from user input
  created_at: number;
  interview_duration_seconds: number;
  questions_asked: number;
  questions_skipped: number;
}
```

### LLM Response Schema (Per Turn)

The orchestrator makes **1 LLM call per user turn** with this output schema:

```typescript
interface OrchestratorResponse {
  // What mode we're in
  mode: 'interview' | 'off_topic' | 'finish';

  // Agent callouts (UI decoration)
  agent_callouts: AgentCallout[];

  // Updates to brief based on user's answer
  brief_patch: Partial<ProjectBrief>;

  // Next action
  next_action: NextAction;

  // Confidence and reasoning
  confidence: number;  // 0-1, used for follow-up decisions
  reason_codes: string[];  // e.g., ["missing_slot:audience", "ambiguous_answer"]

  // User sentiment (for early exit detection)
  user_sentiment: 'engaged' | 'neutral' | 'impatient' | 'frustrated';
}

interface AgentCallout {
  agent: 'RequirementsAgent' | 'UXAgent' | 'TechAgent' | 'PlannerAgent';
  content: string;  // e.g., "Extracting constraints and goals..."
}

type NextAction =
  | { type: 'ask_group'; group: QuestionGroup }
  | { type: 'ask_followup'; questions: Question[]; reason: string }
  | { type: 'finish'; brief: ProjectBrief; plan: BuildPlan }
  | { type: 'handle_offtopic'; response: string; return_to: string }
  | { type: 'suggest_early_finish'; message: string };

interface BuildPlan {
  pages: PageSpec[];
  design_system: Partial<DesignSystem>;
  features: string[];
  estimated_complexity: string;
}

interface PageSpec {
  id: string;
  name: string;
  path: string;
  sections: string[];
  is_main: boolean;
}
```

### Reference Question Categories

These 6 categories guide the LLM in generating contextual questions. They are **not a fixed template**—the LLM selects and adapts based on project complexity:

| Category | When to Ask | Example Questions |
|----------|-------------|-------------------|
| **Scope** | Always (first) | "What kind of X are you building?", "Web-only or mobile?" |
| **Audience** | Complex projects | "Who's the target user?", "B2B or B2C?" |
| **Goals** | Medium+ complexity | "What's the primary goal?", "How will you measure success?" |
| **Features** | Medium+ complexity | "What features are must-have?", "Need user accounts?" |
| **Brand/Design** | If not mentioned | "Any brand colors?", "What style/mood?" |
| **Technical** | High complexity | "Any integrations needed?", "Hosting preferences?" |

For a **birthday invite** (low complexity): Only Scope + basic logistics (when, where, who).
For a **SaaS tool** (high complexity): All 6 categories, potentially 15-30 questions.

### Example Question Plans

#### Birthday Invitation Plan

```typescript
{
  project_type: "event-invitation",
  estimated_questions: 6,
  questions: [
    {
      id: "q1_timing",
      text: "派对计划在什么时候举办？",
      type: "text",
      required: true,
      category: "timing",
      follow_up_questions: [
        {
          id: "q1_1_location",
          text: "地点定了吗？在哪里举办？",
          type: "text",
          required: false,
          category: "timing",
        },
        {
          id: "q1_2_duration",
          text: "计划办多长时间？",
          type: "choice",
          required: false,
          category: "timing",
          choices: ["2小时", "3小时", "半天", "全天"],
        }
      ],
      default_value: "近期"
    },
    {
      id: "q2_guests",
      text: "大概有多少人参加？",
      type: "text",
      required: true,
      category: "logistics",
      follow_up_questions: [
        {
          id: "q2_1_audience",
          text: "主要是哪些人群？",
          type: "choice",
          required: false,
          category: "logistics",
          choices: ["小朋友为主", "大人为主", "大人小孩都有"],
        }
      ],
      default_value: "20人左右"
    },
    {
      id: "q3_theme",
      text: "有什么特定的主题风格吗？",
      type: "text",
      required: true,
      category: "design",
      follow_up_questions: [
        {
          id: "q3_1_colors",
          text: "有偏好的颜色吗？",
          type: "text",
          required: false,
          category: "design",
        }
      ],
      default_value: "温馨可爱风"
    },
    {
      id: "q4_content",
      text: "邀请函上需要包含哪些信息？",
      type: "choice",
      required: false,
      category: "content",
      choices: ["活动详情", "RSVP表单", "地图导航", "照片展示", "全部都要"],
      default_value: ["活动详情", "RSVP表单"]
    },
    {
      id: "q5_contact",
      text: "客人怎么联系你确认参加？",
      type: "text",
      required: false,
      category: "contact",
      default_value: "通过RSVP表单"
    },
    {
      id: "q6_special",
      text: "还有什么特殊要求吗？",
      type: "text",
      required: false,
      category: "other",
      default_value: null
    }
  ]
}
```

#### Personal Profile Plan

```typescript
{
  project_type: "personal-profile",
  estimated_questions: 5,
  questions: [
    {
      id: "q1_name",
      text: "你的名字是？",
      type: "text",
      required: true,
      category: "basic",
      default_value: "神秘朋友"
    },
    {
      id: "q2_identity",
      text: "用一句话介绍你自己",
      type: "text",
      required: true,
      category: "basic",
      follow_up_questions: [
        {
          id: "q2_1_details",
          text: "具体从事什么行业？",
          type: "text",
          required: false,
          category: "basic",
        }
      ],
      default_value: "一个有趣的灵魂"
    },
    {
      id: "q3_links",
      text: "想展示哪些链接？",
      type: "text",
      required: true,
      category: "content",
      follow_up_questions: [
        {
          id: "q3_1_count",
          text: "大概有多少个链接？",
          type: "number",
          required: false,
          category: "content",
        }
      ],
      default_value: "社交媒体链接"
    },
    {
      id: "q4_style",
      text: "希望什么风格的页面？",
      type: "choice",
      required: false,
      category: "design",
      choices: ["简约专业", "活泼有趣", "艺术创意", "科技感"],
      default_value: "简约专业"
    },
    {
      id: "q5_avatar",
      text: "有头像或照片吗？",
      type: "text",
      required: false,
      category: "media",
      default_value: null
    }
  ]
}
```

---

## Product Document Format

### Display Format

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📄 需求文档                                                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                           │
│  🎯 项目概览                                                            │
│  ├─ 类型: 生日派对邀请函                                                │
│  ├─ 主题: Emma的5岁粉色公主生日派对                                      │
│  └─ 受众: 约20人 (5-8岁女孩及其家长)                                    │
│                                                                           │
│  📅 时间地点                                                            │
│  ├─ 日期: 2025年3月15日 (周六)                                          │
│  ├─ 时间: 14:00 - 17:00 (3小时)                                         │
│  └─ 地点: 阳光酒店3楼宴会厅                                             │
│                                                                           │
│  🎨 设计风格                                                            │
│  ├─ 主题色: 粉色 (#FFC0CB + #FF69B4)                                     │
│  ├─ 风格: 公主主题、可爱、温馨                                           │
│  └─ 氛围: 梦幻、童趣                                                     │
│                                                                           │
│  📝 包含内容                                                            │
│  ├─ ✅ 派对详情 (时间、地点、着装要求)                                    │
│  ├─ ✅ RSVP表单 (参加人数、联系方式)                                      │
│  ├─ ✅ 地图导航                                                         │
│  └─ ✅ 照片展示区 (用于分享派对照片)                                      │
│                                                                           │
│  📞 联系信息                                                            │
│  └─ 通过RSVP表单或电话联系                                              │
│                                                                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                           │
│  [🎨 生成] [✏️ 编辑需求] [⏭️ 跳过确认，直接生成]                            │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Document Data Structure

```typescript
interface ProductDocument {
  project_type: string;
  overview: {
    name: string;
    description: string;
    target_audience: string;
  };
  timing?: {
    date: string;
    time: string;
    duration?: string;
    location?: string;
  };
  design: {
    theme: string;
    color_palette: string[];
    style_keywords: string[];
  };
  content: {
    sections: string[];
    features: string[];
    requirements: string[];
  };
  contact?: {
    methods: string[];
    info: string;
  };
  metadata: {
    created_at: number;
    interview_duration: number;
    questions_asked: number;
    questions_skipped: number;
  };
}
```

---

## Agent Architecture (Simplified)

### Design Decision: Single Orchestrator

**Previous design**: 8 separate agents (Router, Planner, Question, Answer, Decision, Document, Designer, Developer) = 15-30 LLM calls per interview.

**New design**: 1 orchestrator with agent "roles" as prompt context = **1 LLM call per user turn**.

The agent callouts (RequirementsAgent, UXAgent, TechAgent) are **UI decoration**, not separate processes.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Single Orchestrator Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User Message                                                              │
│       ↓                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  Interview Orchestrator (1 LLM call per turn)                         │  │
│   │                                                                        │  │
│   │  System prompt includes:                                               │  │
│   │  - RequirementsAgent role: extract constraints, goals                  │  │
│   │  - UXAgent role: decide what questions reduce ambiguity fastest        │  │
│   │  - TechAgent role: flag technical constraints and risks                │  │
│   │                                                                        │  │
│   │  Returns structured JSON:                                              │  │
│   │  - agent_callouts (UI decoration)                                      │  │
│   │  - brief_patch (data extracted from answer)                            │  │
│   │  - next_action (what to do next)                                       │  │
│   │  - confidence, reason_codes, user_sentiment                            │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│       ↓                                                                     │
│   Backend validates JSON with Pydantic                                      │
│   Updates draft.interview_state                                             │
│       ↓                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  Next Action Router (deterministic, no LLM)                           │  │
│   │                                                                        │  │
│   │  if next_action.type == 'ask_group':                                   │  │
│   │      → Show question group to user                                     │  │
│   │  if next_action.type == 'ask_followup':                                │  │
│   │      → Show follow-up questions (partial answer handling)              │  │
│   │  if next_action.type == 'finish':                                      │  │
│   │      → Generate Product Document → Show Build Plan                     │  │
│   │  if next_action.type == 'handle_offtopic':                             │  │
│   │      → Send response, return to current question                       │  │
│   │  if next_action.type == 'suggest_early_finish':                        │  │
│   │      → Offer "Ready to generate?" prompt                               │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│       ↓                                                                     │
│   When interview done:                                                      │
│       ↓                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  Product Document Generator (1 LLM call)                              │  │
│   │  Input: brief → Output: structured Product Document                    │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│       ↓                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  Code Generator (1 LLM call per page)                                 │  │
│   │  Input: Product Document + page_spec → Output: HTML/JS                 │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Total LLM calls for 10-question interview:                                │
│   - Interview: ~4-5 calls (1 per user turn)                                 │
│   - Product Doc: 1 call                                                     │
│   - Code Gen: 1-4 calls (per page)                                          │
│   = 6-10 total (vs. 30-50 in multi-agent design)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Callouts (UI Decoration)

Agent callouts appear in the chat as visual "pills" to create the feeling of an AI team, but they're just message types rendered by frontend:

```typescript
// Response payload includes:
{
  "agent_callouts": [
    {"agent": "RequirementsAgent", "content": "Extracting project scope and goals..."},
    {"agent": "UXAgent", "content": "This is a complex product. I'll ask about user flows."}
  ],
  // ... rest of response
}

// Frontend renders as:
// ┌──────────────────────────────────────────────────────────────┐
// │ 🤖 RequirementsAgent: Extracting project scope and goals... │
// │ 🎨 UXAgent: This is a complex product. I'll ask about flows │
// └──────────────────────────────────────────────────────────────┘
```

**Callout display rules**:
- **First message**: Show all 3-4 agents briefly ("consulting...")
- **Per turn**: Show only relevant agent(s) with meaningful content

### Orchestrator System Prompt

```python
ORCHESTRATOR_SYSTEM_PROMPT = """
You are an interview orchestrator for Zaoya, an AI website builder.

You have access to three specialist perspectives:
- **RequirementsAgent**: Focuses on extracting requirements, constraints, and goals
- **UXAgent**: Focuses on reducing ambiguity with the fewest questions
- **TechAgent**: Flags technical constraints (auth, DB, integrations) and risks

## Your Task

Given the user's message and current interview state:
1. Extract any new information into brief_patch
2. Decide what to do next (ask more questions, follow-up, or finish)
3. Generate agent callouts for UI
4. Assess user sentiment (are they impatient?)

## Question Generation Rules

- Group related questions (up to 3 per message) by topic
- Every question MUST have multiple choice options + allow free text
- Option count varies: 2 for yes/no, 3-6 for features/preferences
- AI decides single-select vs multi-select per question
- Prioritize topics by importance to this specific project
- Skip questions if info already provided in earlier messages

## Complexity Assessment

- LOW (1-5 questions): Simple pages like invites, profiles, portfolios
- MEDIUM (5-15 questions): Landing pages, small business sites
- HIGH (15-50 questions): SaaS tools, complex apps, multi-feature products

## Early Finish Triggers

Suggest finishing if:
- Brief has: project_type + audience + primary_goal + (features OR sections)
- User shows impatience (terse answers, "just do it", multiple skips)
- User clicks "Generate now"

## Output Format

Return valid JSON matching OrchestratorResponse schema.
"""
```

### Error Handling

```python
async def handle_interview_turn(project_id: str, user_message: str) -> dict:
    """Process one turn of the interview."""

    # Get current state
    draft = await get_draft(project_id)
    interview_state = draft.interview_state

    # Build prompt with context
    prompt = build_orchestrator_prompt(user_message, interview_state)

    # Call LLM with retry logic
    for attempt in range(3):
        try:
            response = await llm_call(prompt, ORCHESTRATOR_SYSTEM_PROMPT)
            validated = OrchestratorResponse.model_validate_json(response)
            break
        except (JSONDecodeError, ValidationError) as e:
            if attempt == 2:
                # Graceful fallback: generic next question
                validated = generate_fallback_response(interview_state)
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    # Update state
    interview_state = apply_brief_patch(interview_state, validated.brief_patch)
    interview_state = update_state(interview_state, validated.next_action)

    # Save and return
    await save_draft(project_id, interview_state=interview_state)
    return format_response(validated)
```

---

## API Design (Interview Flow)

### Endpoints

```python
# Main chat endpoint - handles all interview interactions
# POST /api/projects/{project_id}/chat/messages

# Request
{
  "role": "user",
  "content": "I want to build a search engine for students",
  "selected_options": ["option_a", "option_c"],  # If user selected from choices
  "action": null  # or "skip" | "generate_now" | "skip_all"
}

# Response (varies by interview state)
{
  "assistant_messages": [
    {
      "type": "agent_callout",
      "agent": "RequirementsAgent",
      "content": "Analyzing your project requirements..."
    },
    {
      "type": "agent_callout",
      "agent": "UXAgent",
      "content": "This looks like a complex project. I'll ask detailed questions."
    },
    {
      "type": "question_group",
      "group_id": "g1_scope",
      "topic": "Product Scope",
      "questions": [
        {
          "id": "q1",
          "text": "What kind of search engine are you building?",
          "type": "single_select",
          "options": [
            {"value": "academic", "label": "Academic resources"},
            {"value": "general", "label": "General web search"},
            {"value": "topic", "label": "Specific topic/domain"}
          ],
          "allow_other": true
        },
        {
          "id": "q2",
          "text": "What content will students search through?",
          "type": "multi_select",
          "options": [
            {"value": "textbooks", "label": "Textbooks"},
            {"value": "papers", "label": "Research papers"},
            {"value": "notes", "label": "Study notes"},
            {"value": "custom", "label": "Custom database"}
          ],
          "allow_other": true
        }
      ]
    }
  ],
  "interview_state": {
    "status": "in_progress",
    "complexity": "high",
    "current_question_number": 1,
    "brief_coverage": 0.15  # 15% of brief filled
  },
  "controls": {
    "can_skip": true,
    "can_generate_now": true,
    "can_go_back": false  # First question
  }
}
```

### Interview State Responses by Status

```python
# Status: not_started (first message)
{
  "assistant_messages": [
    {"type": "text", "content": "I'll help you build that! Let me ask a few questions first."},
    {"type": "agent_callout", "agent": "RequirementsAgent", "content": "..."},
    {"type": "question_group", ...}
  ],
  "interview_state": {"status": "in_progress", ...}
}

# Status: in_progress (mid-interview)
{
  "assistant_messages": [
    {"type": "agent_callout", "agent": "TechAgent", "content": "Noted: you'll need auth."},
    {"type": "question_group", ...}  # Next group of questions
  ],
  "interview_state": {"status": "in_progress", "current_question_number": 5, ...}
}

# Status: in_progress (partial answer, needs follow-up)
{
  "assistant_messages": [
    {"type": "text", "content": "Got it. Just to clarify:"},
    {"type": "followup_questions", "questions": [...]}  # Only unanswered ones
  ],
  "interview_state": {"status": "in_progress", ...}
}

# Status: finishing (interview complete)
{
  "assistant_messages": [
    {"type": "text", "content": "Great! Here's what I'll build for you:"},
    {"type": "build_plan", "plan": {
      "pages": [
        {"name": "Home", "path": "/", "sections": ["Hero", "Search", "Features"]},
        {"name": "Results", "path": "/results", "sections": ["SearchResults", "Filters"]},
        {"name": "Pricing", "path": "/pricing", "sections": ["Plans", "FAQ", "CTA"]}
      ],
      "design": {"style": "modern", "colors": ["#2563eb", "#1e40af"], "mood": "professional"},
      "features": ["User auth", "Search API", "Analytics"]
    }}
  ],
  "interview_state": {"status": "done", ...},
  "controls": {
    "can_edit_via_chat": true,
    "can_generate": true
  }
}

# Status: done (user clicked Generate)
{
  "assistant_messages": [
    {"type": "generating", "progress": 25, "current_page": "Home"}
  ],
  "interview_state": {"status": "done", ...}
}
```

### Interview Control Endpoints

```python
# Skip current question group
POST /api/projects/{project_id}/interview/skip
→ Uses defaults, moves to next group

# Skip all remaining questions and generate
POST /api/projects/{project_id}/interview/generate-now
→ Completes interview with current brief, shows Build Plan

# Reset interview (start over)
POST /api/projects/{project_id}/interview/reset
→ Clears interview_state, returns to not_started

# Get current interview state (for resuming)
GET /api/projects/{project_id}/interview
→ Returns full interview_state for UI to render
```

### Resume Interview Flow

When user returns after leaving mid-interview:

```python
# GET /api/projects/{project_id}/interview
{
  "interview_state": {
    "status": "in_progress",
    "current_question_number": 7,
    "brief_coverage": 0.45,
    ...
  },
  "resume_message": "Welcome back! You were answering questions about technical requirements.",
  "current_questions": {...}  # The questions they were on
}
```

---

## Behavioral Decisions Summary

These decisions were made through detailed interview process:

| Aspect | Decision |
|--------|----------|
| **Architecture** | Single orchestrator + structured JSON (not 8 agents) |
| **Questions per turn** | Up to 3 related questions grouped by topic |
| **Question count** | Adaptive: 2-5 (simple) to 15-50 (complex) |
| **Question format** | Every question has options + free text |
| **Option count** | Variable by question type (2 for yes/no, 3-6 for features) |
| **Single/multi-select** | AI decides per question |
| **Topic order** | AI prioritizes based on project importance |
| **Follow-up scoring** | LLM confidence field in response |
| **Partial answers** | Extract + follow-up; if ignored again, use defaults |
| **Progress display** | Current question number only, no total |
| **User controls** | Always visible "Generate now" and "Skip" buttons |
| **Agent callouts** | Intro splash + per-turn relevant agent (UI decoration) |
| **Brief display** | Internal only; Build Plan shown to user |
| **Product Document** | Structured sections, generated after brief |
| **Edit flow** | Chat-based edits ("change audience to students") |
| **Language** | Auto-detect from user's first message |
| **Off-topic handling** | Pause interview, handle request, return to question |
| **Impatience detection** | AI sentiment detection triggers early finish |
| **Resume behavior** | Exact resume + progress reminder |
| **Skip defaults** | Silent (no warning about defaults used) |
| **LLM failure** | Retry + graceful fallback after 3 attempts |
| **Missing assets** | AI-generated placeholders |
| **Design tokens** | Extract from brief + AI complement |
| **Multi-page** | Plan all, generate sequentially |

---

## Frontend Components (Interview)

### Component Structure

```
frontend/src/components/
├── interview/
│   ├── InterviewContainer.tsx     # Main interview flow container
│   ├── QuestionGroup.tsx          # Renders grouped questions (up to 3)
│   ├── QuestionOption.tsx         # Single/multi-select option
│   ├── FreeTextInput.tsx          # "Other" text input
│   ├── AgentCallout.tsx           # Agent pill/card (UI decoration)
│   ├── InterviewControls.tsx      # Skip, Generate now buttons
│   ├── BuildPlanViewer.tsx        # Shows pages/sections plan
│   └── ProgressIndicator.tsx      # "Question 7" (no total)
```

### InterviewContainer (Updated)

```typescript
// frontend/src/components/interview/InterviewContainer.tsx

interface InterviewContainerProps {
  projectId: string;
  onGenerationStart: () => void;
}

export function InterviewContainer({ projectId, onGenerationStart }: InterviewContainerProps) {
  const [state, setState] = useState<InterviewState | null>(null);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);

  // Fetch interview state on mount (for resume)
  useEffect(() => {
    fetchInterviewState(projectId).then(setState);
  }, [projectId]);

  const handleAnswer = async (answers: Record<string, string | string[]>) => {
    const response = await sendChatMessage(projectId, {
      role: 'user',
      content: formatAnswers(answers),
      selected_options: extractSelectedOptions(answers),
    });

    setMessages(response.assistant_messages);
    setState(response.interview_state);

    if (response.interview_state.status === 'done') {
      onGenerationStart();
    }
  };

  const handleSkip = () => sendChatMessage(projectId, { action: 'skip' });
  const handleGenerateNow = () => sendChatMessage(projectId, { action: 'generate_now' });

  return (
    <div className="interview-container">
      {/* Agent callouts */}
      {messages.filter(m => m.type === 'agent_callout').map(callout => (
        <AgentCallout key={callout.agent} agent={callout.agent} content={callout.content} />
      ))}

      {/* Question groups */}
      {messages.filter(m => m.type === 'question_group').map(group => (
        <QuestionGroup
          key={group.group_id}
          group={group}
          onAnswer={handleAnswer}
        />
      ))}

      {/* Build plan (when interview done) */}
      {messages.find(m => m.type === 'build_plan') && (
        <BuildPlanViewer plan={messages.find(m => m.type === 'build_plan').plan} />
      )}

      {/* Always visible controls */}
      <InterviewControls
        currentQuestion={state?.current_question_number}
        canSkip={state?.controls?.can_skip}
        canGenerateNow={state?.controls?.can_generate_now}
        onSkip={handleSkip}
        onGenerateNow={handleGenerateNow}
      />
    </div>
  );
}
```

### QuestionGroup Component

```typescript
// frontend/src/components/interview/QuestionGroup.tsx

interface QuestionGroupProps {
  group: {
    group_id: string;
    topic: string;
    questions: Question[];
  };
  onAnswer: (answers: Record<string, string | string[]>) => void;
}

export function QuestionGroup({ group, onAnswer }: QuestionGroupProps) {
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});

  const handleOptionSelect = (questionId: string, value: string | string[]) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = () => {
    onAnswer(answers);
  };

  return (
    <div className="question-group bg-white rounded-xl p-6 shadow-sm">
      {/* Topic header */}
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
        {group.topic}
      </h3>

      {/* Questions */}
      <div className="space-y-6">
        {group.questions.map((question, index) => (
          <div key={question.id} className="question">
            <p className="text-lg font-medium text-gray-800 mb-3">
              {index + 1}. {question.text}
            </p>

            {/* Options */}
            <div className="space-y-2">
              {question.options?.map(option => (
                <QuestionOption
                  key={option.value}
                  option={option}
                  type={question.type}
                  selected={
                    question.type === 'multi_select'
                      ? (answers[question.id] as string[] || []).includes(option.value)
                      : answers[question.id] === option.value
                  }
                  onSelect={() => handleOptionSelect(question.id, option.value)}
                />
              ))}

              {/* Free text option */}
              {question.allow_other && (
                <FreeTextInput
                  placeholder="Other (type your own)..."
                  value={typeof answers[question.id] === 'string' && !question.options?.find(o => o.value === answers[question.id])
                    ? answers[question.id] as string
                    : ''}
                  onChange={(text) => handleOptionSelect(question.id, text)}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700"
      >
        Continue
      </button>
    </div>
  );
}
```

### AgentCallout Component

```typescript
// frontend/src/components/interview/AgentCallout.tsx

const AGENT_CONFIG = {
  RequirementsAgent: { icon: '🤖', color: 'bg-blue-50 text-blue-700' },
  UXAgent: { icon: '🎨', color: 'bg-purple-50 text-purple-700' },
  TechAgent: { icon: '⚙️', color: 'bg-green-50 text-green-700' },
  PlannerAgent: { icon: '📋', color: 'bg-orange-50 text-orange-700' },
};

export function AgentCallout({ agent, content }: { agent: string; content: string }) {
  const config = AGENT_CONFIG[agent] || { icon: '🤖', color: 'bg-gray-50 text-gray-700' };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${config.color}`}>
      <span>{config.icon}</span>
      <span className="font-medium">{agent}:</span>
      <span>{content}</span>
    </div>
  );
}
```

---

## UI States (Interview Flow)

### State 1: Analyzing (First Message)

```
┌─────────────────────────────────────────┐
│  💭 AI 正在分析你的需求...              │
│                                         │
│           [Loading Spinner]             │
│                                         │
│  🤖 RequirementsAgent: 分析项目类型...  │
│  🎨 UXAgent: 评估复杂度...              │
│  ⚙️ TechAgent: 检查技术需求...          │
└─────────────────────────────────────────┘
```

### State 2: Asking Questions (Grouped)

```
┌─────────────────────────────────────────┐
│  问题 3                [Skip] [Generate now] │
├─────────────────────────────────────────┤
│                                         │
│  📋 产品范围                            │
│                                         │
│  1. 你想搭建什么类型的搜索引擎？        │
│     ○ 学术资源搜索  ○ 通用网页  ○ 特定领域 │
│     ○ Other: ____                       │
│                                         │
│  2. 学生会搜索什么内容？                │
│     ☐ 教科书  ☐ 论文  ☐ 笔记  ☐ 自定义   │
│     ☐ Other: ____                       │
│                                         │
│  3. 网页端还是移动端？                  │
│     ○ 仅网页  ○ 仅移动  ○ 两者都要      │
│                                         │
│  [发送]                                 │
│                                         │
└─────────────────────────────────────────┘
```

### State 3: Build Plan Review

```
┌─────────────────────────────────────────┐
│  📋 Build Plan                          │
├─────────────────────────────────────────┤
│                                         │
│  Pages:                                 │
│  ├── Home (搜索界面, Hero, 功能介绍)    │
│  ├── Results (搜索结果, 筛选, 分页)     │
│  └── Pricing (套餐, FAQ, CTA)           │
│                                         │
│  Features: 用户认证, 搜索API, 数据分析  │
│  Design: 现代, 专业, 蓝色系             │
│                                         │
│  [🎨 Generate] [✏️ Edit via chat]       │
└─────────────────────────────────────────┘
```

### State 4: Generating

```
┌─────────────────────────────────────────┐
│  🚀 正在生成你的页面...                  │
│                                         │
│  ████████████████░░░░░  75%             │
│                                         │
│  • Generating: Home page...             │
│  • Next: Results page...                │
│  • Pending: Pricing page...             │
└─────────────────────────────────────────┘
```

---

## Quick Actions During Interview

Users can use quick actions at any point during the interview:

```
┌─────────────────────────────────────────┐
│  Quick Actions                          │
├─────────────────────────────────────────┤
│  [Skip all → Generate now]              │
│  [View collected info so far]           │
│  [Start over]                           │
└─────────────────────────────────────────┘
```

These actions are also available via the always-visible control bar at the bottom of the interview screen.

---

## Success Metrics (Interview Flow)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Adaptive question count | 2-5 (simple), 5-15 (medium), 15-50 (complex) | Per project complexity |
| Interview completion rate | > 80% | Users who finish vs skip all |
| Interview duration | < 3 min (simple), < 8 min (complex) | Time to Build Plan |
| "Generate now" usage | < 20% | Users who skip remaining questions |
| Build Plan confirmation rate | > 90% | Users who confirm vs edit |
| First-gen acceptance rate | > 70% | Users satisfied with first generation |
| LLM calls per interview | 4-6 (simple), 6-12 (complex) | API efficiency |

---

## Summary

v2 Interview Flow 核心特点：

1. **Single Orchestrator** - 1 LLM call per turn, not 8 agents
2. **Adaptive Complexity** - 2-50 questions based on project complexity
3. **Grouped Questions** - Up to 3 related questions per message by topic
4. **Dynamic Planning** - AI generates and adjusts question plan mid-interview
5. **Always-visible Controls** - "Generate now" and "Skip" buttons visible throughout
6. **Build Plan** - User sees pages/sections before generation (not internal brief)
7. **Chat-based Edits** - Users can modify Build Plan via natural language

---

## Additional Core Features (v2)

### 1. Design System Editor

可视化编辑设计系统，让用户精确控制页面外观。

#### UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🎨 Design System                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  🎨 Colors                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Primary         │  Secondary      │  Background      │  Text      │  │
│  │ ┌──────────┐   │  ┌──────────┐   │  ┌──────────┐   │  ┌──────┐  │  │
│  │ │ #FF6B6B   │   │  │ #4ECDC4   │   │  │ #FFFFFF   │   │  │ #333 │  │  │
│  │ └──────────┘   │  └──────────┘   │  └──────────┘   │  └──────┘  │  │
│  │ [Custom]        │  [Custom]        │  [Custom]        │  [Custom]   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  🔤 Typography                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Heading Font:    [Inter ▼]  Size: [Large ▼]  Weight: [600 ▼]     │  │
│  │ Body Font:       [Inter ▼]  Size: [Medium ▼]  Weight: [400 ▼]     │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  📏 Spacing                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ ◉ Compact  ○ Comfortable  ○ Spacious                                │  │
│  │ 描述: 舒适的间距，适合大多数场景                                     │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  🔲 Border Radius                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ ○ None  ○ Small (4px)  ◉ Medium (8px)  ● Large (16px)  ⬭ Full    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ✨ Animations                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Level: ━━━━━━━━━━━━━━━━━━━━━━━━━━ 50%                            │  │
│  │ ◉ None  ○ Subtle  ● Moderate  ○ Energetic                          │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  🎭 Preset Themes                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ [Pink Princess]  [Blue Ocean]  [Forest Green]  [Sunset]  [Custom+] │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  [Reset to Default]              [Apply Changes]                     │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Data Structure

```typescript
interface DesignSystem {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
    text_light: string;
    border: string;
  };
  typography: {
    heading: {
      family: string;
      size: 'small' | 'medium' | 'large' | 'xlarge';
      weight: number;
      line_height: number;
    };
    body: {
      family: string;
      size: 'small' | 'medium' | 'large';
      weight: number;
      line_height: number;
    };
  };
  spacing: 'compact' | 'comfortable' | 'spacious';
  border_radius: 'none' | 'small' | 'medium' | 'large' | 'full';
  animation_level: 'none' | 'subtle' | 'moderate' | 'energetic';
  preset_theme?: string;
}

// Preset Themes
const PRESET_THEMES: Record<string, Partial<DesignSystem>> = {
  'pink-princess': {
    colors: { primary: '#FF69B4', secondary: '#FFC0CB', accent: '#FF1493' },
    animation_level: 'moderate',
  },
  'blue-ocean': {
    colors: { primary: '#0077B6', secondary: '#00B4D8', accent: '#90E0EF' },
    animation_level: 'subtle',
  },
  'forest-green': {
    colors: { primary: '#2D6A4F', secondary: '#40916C', accent: '#52B788' },
    animation_level: 'subtle',
  },
  'sunset': {
    colors: { primary: '#F77F00', secondary: '#FCBF49', accent: '#FDE68A' },
    animation_level: 'energetic',
  },
  'minimal-black': {
    colors: { primary: '#1A1A1A', secondary: '#4A4A4A', accent: '#7A7A7A' },
    animation_level: 'none',
  },
};
```

#### API

```python
# GET /api/projects/{project_id}/design-system
→ DesignSystem

# PUT /api/projects/{project_id}/design-system
{
  "colors": {...},
  "typography": {...},
  "spacing": "comfortable",
  "border_radius": "medium",
  "animation_level": "moderate"
}
→ DesignSystem (updated)

# POST /api/projects/{project_id}/design-system/apply-preset
{
  "preset": "pink-princess"
}
→ DesignSystem (applied preset)
```

#### Real-time Preview

设计系统更改后，预览面板实时更新（无需重新生成代码）。

---

### 2. Version History & Diff

查看和对比不同版本之间的变化。

#### UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📜 Version History                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ v3 (Current)  • 2 minutes ago  [View] [Restore] [Publish]            │ │
│  ├─────────────────────────────────────────────────────────────────────┤ │
│  │ v2            • 1 hour ago    [View Diff] [Restore] [Publish]        │ │
│  ├─────────────────────────────────────────────────────────────────────┤ │
│  │ v1            • 3 hours ago   [View Diff] [Restore] [Publish]        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  v2 → v3 Changes                                                      │ │
│  ├─────────────────────────────────────────────────────────────────────┤ │
│  │  📝 Content                                                            │ │
│  │  • Changed hero text from "欢迎" to "欢迎参加Emma的5岁生日派对"    │ │
│  │  • Updated time from "14:00" to "14:30"                          │ │
│  │  • Added location info: "阳光酒店3楼"                               │ │
│  │                                                                       │ │
│  │  🎨 Design                                                             │ │
│  │  • Changed primary color from #4ECDC4 to #FF69B4                      │ │
│  │  • Added gradient background                                         │ │
│  │                                                                       │ │
│  │  ➕ Added                                                              │ │
│  │  • Countdown timer component                                          │ │
│  │  • Photo gallery section                                             │ │
│  │                                                                       │ │
│  │  ➖ Removed                                                            │ │
│  │  • Original hero image (replaced with gradient)                       │ │
│  │                                                                       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  [View Side by Side]    [Restore v2]    [Download Diff]                    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Side-by-Side Diff View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  v2 → v3 Comparison                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────┬─────────────────────┐                         │
│  │ v2 (Before)          │ v3 (After)           │                         │
│  ├─────────────────────┼─────────────────────┤                         │
│  │                     │                     │                         │
│  │ <div class="hero">   │ <div class="hero">   │                         │
│  │   <h1>欢迎</h1>       │   <h1>欢迎参加...     │  🔴 Changed             │
│  │ </div>             │ </div>              │                         │
│  │                     │                     │                         │
│  │ bg-blue-500         │ bg-gradient-pink    │  🔴 Changed             │
│  │                     │                     │                         │
│  └─────────────────────┴─────────────────────┘                         │
│                                                                           │
│  Legend: 🔴 Changed  ➕ Added  ➖ Removed                               │
│                                                                           │
│  [Next Change ↑]    [Previous Change ↓]    [Close]                        │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Data Structure

```typescript
interface Snapshot {
  id: string;
  project_id: string;
  version_number: number;
  is_draft: boolean;
  is_published: boolean;
  content: {
    html: string;
    javascript: string;
    css?: string;
  };
  design_system: DesignSystem;
  metadata: {
    created_at: number;
    created_by: string;
    message_count: number;
  };
}

interface VersionDiff {
  from_version: number;
  to_version: number;
  changes: {
    content: DiffChange[];
    design: DiffChange[];
    summary: string[];
  };
}

type DiffChange =
  | { type: 'changed'; path: string; from: string; to: string }
  | { type: 'added'; path: string; content: string }
  | { type: 'removed'; path: string; content: string };
```

#### API

```python
# GET /api/projects/{project_id}/versions
→ List<Snapshot>

# GET /api/projects/{project_id}/versions/{version_id}/diff
# Query params: compare_with={version_id}
→ VersionDiff

# POST /api/projects/{project_id}/versions/{version_id}/restore
→ Snapshot (restored)

# DELETE /api/projects/{project_id}/versions/{version_id}
→ { "deleted": true }
```

---

### 3. Undo / Redo

编辑操作历史回退和重做。

#### Keyboard Shortcuts

| 快捷键 | 功能 |
|--------|------|
| `Cmd/Ctrl + Z` | Undo |
| `Cmd/Ctrl + Shift + Z` | Redo |
| `Cmd/Ctrl + /` | 查看历史 |

#### UI Indicator

```
┌─────────────────────────────────────────┐
│  ↩️ Undo  ↪️ Redo    History (23)         │
└─────────────────────────────────────────┘

Hover:
┌─────────────────────────────────────────┐
│  ↩️ Undo "Change to pink theme"            │
│  ↪️ Redo "Add countdown timer"            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Recent Actions:                          │
│  • 5 min ago  Change to pink theme        │
│  • 8 min ago  Add countdown timer          │
│  • 12 min ago Update hero text            │
│  • 15 min ago Initial generation          │
└─────────────────────────────────────────┘
```

#### Data Structure

```typescript
interface HistoryEntry {
  id: string;
  timestamp: number;
  action: string;
  description: string;
  snapshot_id: string;  // Points to the snapshot after this action
  can_undo: boolean;
  can_redo: boolean;
}

interface HistoryState {
  past: HistoryEntry[];
  present: HistoryEntry;
  future: HistoryEntry[];
  max_size: number;  // Limit history size (default: 50)
}
```

#### Tracked Actions

可撤销的操作：
- AI 生成代码 (每次 AI 响应创建新版本)
- 设计系统更改
- 快捷操作应用
- 手动编辑内容
- 问题回答修改

不可撤销的操作：
- 发布项目
- 删除项目
- 恢复旧版本（创建新的恢复点）

#### API

```python
# GET /api/projects/{project_id}/history
→ { past: [...], present: {...}, future: [...] }

# POST /api/projects/{project_id}/history/undo
→ HistoryEntry (the new present)

# POST /api/projects/{project_id}/history/redo
→ HistoryEntry (the new present)
```

---

### 4. Code Download

将生成的页面代码导出为多种格式。

#### Download Modal

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⬇️ Download Code                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Choose format:                                                           │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📄 HTML Single File                                    [Recommended]   │   │
│  │                                                                           │   │
│  │ Self-contained HTML file with embedded CSS/JS.                        │   │
│  │ Ready to open in any browser. No setup required.                       │   │
│  │                                                                    │   │
│  │                            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━  │   │
│  │ <!DOCTYPE html>                                                      │   │
│  │ <html lang="zh-CN">                                                  │   │
│  │ <head>                                                              │   │
│  │   <meta charset="UTF-8">                                           │   │
│  │   <script src="https://cdn.tailwindcss.com"></script>          │   │
│  │   <style>/* ... */</style>                                        │   │
│  │ </head>                                                             │   │
│  │ <body>                                                              │   │
│  │   <!-- Your page content -->                                       │   │
│  │   <script src="https://pages.zaoya.app/runtime.js"></script>     │   │
│  │ </body>                                                             │   │
│  │ </html>                                                             │   │
│  │                                                                    │   │
│  │                                    [Download HTML ~12KB]                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📦 ZIP Package                                                              │   │
│  │                                                                           │   │
│  │ Complete project package with separate files.                          │   │
│  │                                                                    │   │
│  │ 📂 emmas-birthday/                                                     │   │
│  │   ├── index.html                                                      │   │
│  │   ├── zaoya-runtime.js                                               │   │
│  │   └── assets/                                                         │   │
│  │       └── (user images if any)                                         │   │
│  │                                                                    │   │
│  │                                    [Download ZIP ~45KB]                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔧 Source Code (Readable)                                               │   │
│  │                                                                           │   │
│  │ Formatted source code with comments for developers.                      │   │
│  │                                                                    │   │
│  │ ├── index.html  (with structure comments)                           │   │
│  │ └── styles.css   (extracted Tailwind classes)                         │   │
│  │                                                                    │   │
│  │                                    [Download Source]                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Include options:                                                          │
│  ☑ Include Zaoya runtime script                                          │
│  ☑ Include generation comments                                           │
│  ☑ Include metadata (project info, generated date)                        │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Cancel]                                           [Download Selected] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Download API

```python
# GET /api/projects/{project_id}/download

# Query params:
#   format: "html" | "zip" | "source"
#   include_runtime: boolean (default: true)
#   include_comments: boolean (default: false)
#   include_metadata: boolean (default: false)

# Response:
# format=html: text/html file download
# format=zip: application/zip file download
# format=source: application/zip (with separate files)

@router.get("/api/projects/{project_id}/download")
async def download_project(
    project_id: str,
    format: str = "html",
    include_runtime: bool = True,
    include_comments: bool = False,
    include_metadata: bool = False,
    db: AsyncSession = Depends(get_db)
):
    # Get project and draft snapshot
    # Generate file based on format
    # Return file response with appropriate headers
    pass
```

#### HTML Template Generator

```python
def generate_html(snapshot: Snapshot, options: DownloadOptions) -> str:
    """Generate standalone HTML file"""

    html_template = """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {metadata if include_metadata else ""}
    <script src="https://cdn.tailwindcss.com"></script>
    {runtime_script if include_runtime else ""}
    <style>
        /* {comments if include_comments else "Tailwind CSS classes"} */
    </style>
</head>
<body class="bg-white min-h-screen">
    {content}

    {runtime_script if include_runtime else ""}
</body>
</html>"""

    return html_template.format(**{
        lang=snapshot.design_system.get('language', 'zh-CN'),
        title=snapshot.name,
        metadata=_generate_metadata(snapshot) if options.include_metadata else "",
        runtime_script='<script src="https://pages.zaoya.app/zaoya-runtime.js"></script>' if options.include_runtime else '',
        content=snapshot.content.html,
        comments=_generate_comments(snapshot) if options.include_comments else '',
    })
```

---

## Component Library Research (Mobile-First)

### Recommendation: shadcn/ui

For a **mobile-first page generation** tool like Zaoya, **shadcn/ui** remains the best choice.

### Why shadcn/ui for Mobile?

| Feature | shadcn/ui | Arco Mobile | Ant Design Mobile |
|---------|-----------|-------------|-------------------|
| **Copy-to-project** | ✅ Source code ownership | ❌ NPM package | ❌ NPM package |
| **Tailwind Native** | ✅ Built-in | ❌ Custom CSS | ❌ Custom CSS |
| **Mobile Components** | ✅ Responsive by design | ✅ Mobile focused | ✅ Mobile focused |
| **AI-Friendly** | ✅ Used by v0.dev | ❌ Not AI-targeted | ❌ Not AI-targeted |
| **Customization** | ✅ Full control | ⚠️ Limited | ⚠️ Limited |
| **Bundle Size** | ✅ Only what you use | ❌ Full library | ❌ Full library |
| **Accessibility** | ✅ Radix UI foundation | ✅ Good | ✅ Good |

### Key Components for Zaoya (Mobile)

| Component | shadcn/ui | Mobile Use Case |
|----------|-----------|------------------|
| **Dialog** | ✅ | Modals, confirmations |
| **Dropdown Menu** | ✅ | Compact menus, actions |
| **Sheet** | ✅ | Bottom sheets (very mobile-friendly) |
| **Toast** | ✅ (Sonner) | Notifications |
| **Tabs** | ✅ | Content switching |
| **Slider** | ✅ | Range inputs, adjustments |
| **Switch** | ✅ | Toggles, settings |
| **Select** | ✅ | Dropdown choices |
| **Accordion** | ✅ | Expandable content |
| **Card** | ✅ | Content containers |
| **Button** | ✅ | Touch-friendly actions |
| **Input** | ✅ | Form fields |

### Additional Mobile Libraries

For mobile-specific interactions:

```
# Gesture/Swipe (if needed for editor UI)
npm install @use-gesture/react

# Touch-friendly components
npm install @radix-ui/react-scroll-area
npm install @radix-ui/react-slider
```

### Installation Commands

```bash
# shadcn/ui CLI
npx shadcn@latest init

# Core components for Zaoya
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add popover
npx shadcn@latest add sheet
npx shadcn@latest add toast
npx shadcn@latest add tooltip
npx shadcn@latest add select
npx shadcn@latest add switch
npx shadcn@latest add slider
npx shadcn@latest add tabs
npx shadcn@latest add accordion
npx shadcn@latest add scroll-area
npx shadcn@latest add separator
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add label
npx shadcn@latest add textarea
npx shadcn@latest add checkbox
npx shadcn@latest add radio-group

# Animation (for polished UX)
npm install framer-motion

# Icons (mobile-friendly)
npm install lucide-react
```

### Generated Pages: Plain HTML + Tailwind

Important: The **generated pages** are NOT React - they use plain HTML with Tailwind CSS.
shadcn/ui is only used for the **editor UI**, not the generated content.

```html
<!-- Generated page (no React, no component library) -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="max-w-md mx-auto bg-white">
  <!-- Plain HTML + Tailwind classes -->
  <div class="p-6 bg-pink-50 text-center">
    <h1 class="text-2xl font-bold text-pink-600">
      Emma的5岁生日派对
    </h1>
  </div>
  <script src="https://pages.zaoya.app/zaoya-runtime.js"></script>
</body>
</html>
```

---

## Learnings from Claude Code's AskUserQuestion

This section documents insights from studying Claude Code's question-asking UX patterns to inform Zaoya's interview flow design.

### Purpose: Learning, Not Copying

**Important**: Zaoya's interview flow serves a different purpose than Claude Code's tool:
- **Claude Code**: Asks questions DURING task execution (mid-stream)
- **Zaoya**: Asks questions BEFORE code generation (pre-generation)

We study Claude Code to understand UX patterns, not to copy implementation.

### Observed UX Patterns

#### 1. Question Format Structure

Claude Code uses a structured question format:

```typescript
interface ClaudeQuestion {
  question: string;      // Clear question text
  header: string;        // Short category label (max 12 chars)
  options: Option[];     // 2-4 predefined choices
  multiSelect?: boolean; // Allow multiple selections
}

interface Option {
  label: string;        // Short display name (1-5 words)
  description: string;  // Explanation of implications
}
```

**Key Learnings**:
- Clear question text is essential - users should understand immediately
- Short headers/categorization helps mental grouping
- Options have descriptions that explain trade-offs
- Always includes an "Other" option for free-text input

#### 2. Constraints for User Experience

| Constraint | Claude Code | Zaoya Adaptation |
|-----------|-------------|------------------|
| **Questions per batch** | 1-4 questions | 1 question at a time (sequential) |
| **Options per question** | 2-4 options | 2-6 choices + "Other" |
| **Timeout** | 60 seconds | No timeout (pre-generation) |
| **Multi-select** | Supported | Use for "content selection" questions |

#### 3. "Other" Option Pattern

Claude Code always provides an "Other" option:

```typescript
{
  label: "Other",
  description: "Provide custom text input"
}
```

**Zaoya Application**:
- For choice questions, always allow free-text alternative
- Example: "What theme?" → [Princess] [Superhero] [Other: _____]

#### 4. Progress Indication

Claude Code shows progress through multi-step processes:

```
Question 2 of 5  •  Planning directory structure
```

**Zaoya Application**:
```
问题 2 / 6  •  ████████░░░░  33%  •  预计还需 1 分钟
```

### Design Principles for Zaoya

#### Principle 1: Sequential Questioning

**Claude Code**: May show multiple questions at once
**Zaoya**: Show ONE question at a time

**Reasoning**:
- Reduces cognitive load for non-technical users
- Allows adaptive follow-ups based on previous answers
- Creates conversational flow

#### Principle 2: Clear Options with Explanations

```typescript
// Bad
"Choose a theme: [A] [B] [C]"

// Good (Claude-style)
"What style fits your party?

  🎀 Pink Princess
  Dreamy and cute, perfect for little girls

  🦸 Superhero Adventure
  Bold and energetic, great for active kids

  🌈 Rainbow Fun
  Colorful and cheerful, works for any theme

  Other... (type your own)"
```

#### Principle 3: Skip with Graceful Defaults

**Claude Code**: If user skips, makes informed choice
**Zaoya**: If user skips, use sensible default + mention it in Product Document

```typescript
// When showing Product Document
{
  question: "派对计划在什么时候举办？",
  answer: "近期", // Default used
  note: "⚠️ 使用默认值，你可以修改"
}
```

#### Principle 4: Category Headers

Claude Code uses short headers (max 12 chars):

```
┌─────────────────────────────┐
│  📅 DATE & TIME             │  ← Header (category)
├─────────────────────────────┤
│  When is the party?         │
│  ...                        │
└─────────────────────────────┘
```

**Zaoya Categories**:
- 📅 TIME - 日期时间
- 👥 PEOPLE - 受众人数
- 🎨 STYLE - 设计风格
- 📝 CONTENT - 包含内容
- 📞 CONTACT - 联系方式

### Technical Differences

| Aspect | Claude Code | Zaoya |
|--------|-------------|-------|
| **When questions appear** | During task execution | Before generation |
| **State persistence** | In-memory session | Database-backed project |
| **User can return** | No (linear) | Yes (edit previous answers) |
| **Timeout needed** | Yes (60s) | No (pre-generation phase) |
| **Validation** | Immediate | During Document generation |

### Zaoya's Adapted Question Format

```typescript
interface ZaoyaQuestion {
  // Basic structure (Claude-inspired)
  id: string;
  text: string;           // Clear question text
  category: string;       // Short emoji + label (e.g., "📅 TIME")
  category_zh: string;    // Chinese label

  // Question type
  type: 'text' | 'choice' | 'multi_select' | 'date' | 'location';

  // Choices (if applicable)
  choices?: Choice[];
  allow_other?: boolean;  // Always true for choice questions

  // Requirements
  required: boolean;
  can_skip: boolean;

  // Progress context
  progress: {
    current: number;      // 1-based index
    total: number;
    percentage: number;
    estimated_remaining?: string;  // "约 1 分钟"
  };

  // Follow-up support (Zaoya-specific)
  follow_up_questions?: ZaoyaQuestion[];

  // Default value (when skipped)
  default_value?: any;
  default_explanation?: string;  // Why this default?
}

interface Choice {
  label: string;          // Short name
  description: string;    // What this means
  preview_hint?: string;  // E.g., "Pink theme with sparkles"
}
```

### Example: Zaoya Question Card (Claude-Inspired)

```
┌─────────────────────────────────────────────┐
│  📅 时间地点      问题 2 / 6     ████░░░░   │
├─────────────────────────────────────────────┤
│                                             │
│  派对计划在什么时候举办？                    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  🎀 Pink Princess Theme             │   │
│  │  Dreamy and cute, perfect for       │   │
│  │  little girls' parties              │   │
│  ├─────────────────────────────────────┤   │
│  │  🦸 Superhero Adventure            │   │
│  │  Bold and energetic, great for      │   │
│  │  active kids                        │   │
│  ├─────────────────────────────────────┤   │
│  │  🌈 Rainbow Fun                    │   │
│  │  Colorful and cheerful, works       │   │
│  │  for any theme                      │   │
│  ├─────────────────────────────────────┤   │
│  │  Other...                          │   │
│  │  Type your own theme idea          │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [选择] [跳过 → 使用默认: "温馨可爱风"]      │
│                                             │
│  💡 提示: 详细回答能获得更好的效果           │
│                                             │
└─────────────────────────────────────────────┘
```

### Summary of Adaptations

| Pattern from Claude Code | Zaoya Adaptation | Why |
|-------------------------|------------------|-----|
| Clear question text | ✅ Keep | Essential for understanding |
| Option descriptions | ✅ Keep | Helps non-technical users |
| "Other" option | ✅ Keep | Flexibility for custom needs |
| Category headers | ✅ Keep | Visual organization |
| Multi-select | ✅ Keep | For content selection |
| 60s timeout | ❌ Drop | Pre-generation, no urgency |
| Batch questions | ❌ Drop | Sequential is better for UX |
| Mid-execution context | ❌ N/A | Zaoya is pre-generation |

---

## v2 Feature Summary

| Feature | Description | Priority |
|---------|-------------|----------|
| **Interview Flow** | Plan Mode →逐个提问 → Product Document | P0 |
| **Design System Editor** | 可视化编辑颜色、字体、间距、圆角、动画 | P0 |
| **Version History & Diff** | 版本对比、Side-by-Side Diff、Restore | P0 |
| **Undo / Redo** | 操作历史回退 (Cmd+Z)、快捷键 | P0 |
| **Code Download** | HTML/ZIP/Source 多格式下载 | P0 |
| **shadcn/ui** | 编辑器 UI 组件库 | P0 |
| **Device Toggle** | 移动端/桌面端预览切换 | P1 |
| **Image Upload** | 用户上传自己的图片 | P1 |

---

**Document Version**: 2.1
**Last Updated**: 2026-01-23
**Status**: Draft - v2 Complete Specification
