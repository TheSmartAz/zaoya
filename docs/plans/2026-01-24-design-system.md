# Zaoya Design System

**Created**: 2026-01-24
**Status**: Approved
**Visual Direction**: Clean & Minimal (Linear-inspired)

---

## 1. Foundation & Tokens

### Visual Identity
- Preview-dominant layout with subtle editor chrome
- Border-based components (hairline borders, flat surfaces)
- Geist typography for modern, distinctive feel
- Black/charcoal primary with muted grays
- Light + Dark mode via CSS custom properties

### Color Tokens

```css
:root {
  /* Backgrounds */
  --background: 0 0% 100%;           /* white */
  --foreground: 240 10% 4%;          /* zinc-950 */

  /* Muted */
  --muted: 240 5% 96%;               /* zinc-100 */
  --muted-foreground: 240 4% 46%;    /* zinc-500 */

  /* Borders & Inputs */
  --border: 240 6% 90%;              /* zinc-200 */
  --input: 240 6% 90%;               /* zinc-200 */
  --ring: 240 5% 65%;                /* zinc-400 */

  /* Primary (charcoal) */
  --primary: 240 6% 10%;             /* zinc-900 */
  --primary-foreground: 0 0% 100%;   /* white */

  /* Accent */
  --accent: 240 5% 96%;              /* zinc-100 */
  --accent-foreground: 240 6% 10%;   /* zinc-900 */

  /* Destructive */
  --destructive: 0 84% 60%;          /* red-500 */
  --destructive-foreground: 0 0% 100%;

  /* Semantic */
  --success: 142 76% 36%;            /* green-600 */
  --warning: 38 92% 50%;             /* amber-500 */
}

.dark {
  --background: 240 10% 4%;          /* zinc-950 */
  --foreground: 240 5% 96%;          /* zinc-100 */

  --muted: 240 4% 16%;               /* zinc-800 */
  --muted-foreground: 240 5% 65%;    /* zinc-400 */

  --border: 240 4% 16%;              /* zinc-800 */
  --input: 240 4% 16%;               /* zinc-800 */
  --ring: 240 5% 65%;                /* zinc-300 */

  --primary: 240 5% 96%;             /* zinc-100 */
  --primary-foreground: 240 6% 10%;  /* zinc-900 */

  --accent: 240 4% 16%;              /* zinc-800 */
  --accent-foreground: 240 5% 96%;   /* zinc-100 */

  --destructive: 0 63% 31%;          /* red-900 */
}
```

### Spacing Scale

```css
:root {
  --space-0: 0;
  --space-0.5: 0.125rem;   /* 2px */
  --space-1: 0.25rem;      /* 4px */
  --space-1.5: 0.375rem;   /* 6px */
  --space-2: 0.5rem;       /* 8px */
  --space-3: 0.75rem;      /* 12px */
  --space-4: 1rem;         /* 16px */
  --space-5: 1.25rem;      /* 20px */
  --space-6: 1.5rem;       /* 24px */
  --space-8: 2rem;         /* 32px */
  --space-10: 2.5rem;      /* 40px */
  --space-12: 3rem;        /* 48px */
  --space-16: 4rem;        /* 64px */
}
```

### Border Radius

```css
:root {
  --radius-none: 0;
  --radius-sm: 4px;        /* inputs */
  --radius-md: 6px;        /* cards */
  --radius-lg: 8px;        /* modals */
  --radius-xl: 12px;       /* large panels */
  --radius-full: 9999px;   /* pills, avatars */
}
```

---

## 2. Typography

### Font Stack

```css
:root {
  --font-sans: 'Geist', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Geist Mono', 'SF Mono', Monaco, Consolas, 'Liberation Mono', monospace;
}
```

### Type Scale

| Token | Size | Use Case |
|-------|------|----------|
| `text-xs` | 0.75rem (12px) | Captions, timestamps, badges |
| `text-sm` | 0.875rem (14px) | Secondary text, labels, chat messages |
| `text-base` | 1rem (16px) | Body text, inputs, interview questions |
| `text-lg` | 1.125rem (18px) | Card titles, section headers |
| `text-xl` | 1.25rem (20px) | Page section headers |
| `text-2xl` | 1.5rem (24px) | Page titles |
| `text-3xl` | 1.875rem (30px) | Landing page hero only |

### Font Weights

| Weight | Value | Use Case |
|--------|-------|----------|
| Regular | 400 | Body text, descriptions |
| Medium | 500 | Labels, buttons, nav items |
| Semibold | 600 | Headings, emphasis |

### Line Heights

| Name | Value | Use Case |
|------|-------|----------|
| Tight | 1.4 | Headings |
| Normal | 1.6 | Body text |
| Relaxed | 1.8 | Long-form content |

### Letter Spacing

| Name | Value | Use Case |
|------|-------|----------|
| Tight | -0.02em | Headings |
| Normal | 0 | Body text |
| Wide | 0.02em | All-caps labels, badges |

---

## 3. Core Components

### Buttons

| Variant | Style | Use Case |
|---------|-------|----------|
| Primary | `bg-zinc-900 text-white` | Main CTAs (Publish, Generate) |
| Secondary | `bg-transparent border-zinc-200 text-zinc-900` | Secondary actions (Cancel, Back) |
| Ghost | `bg-transparent text-zinc-600` | Tertiary, icon buttons |
| Destructive | `bg-red-500 text-white` | Dangerous actions (Delete) |

**Sizes**:
- `sm`: 32px height
- `default`: 36px height
- `lg`: 40px height

**States**:
- Hover: Slightly darker/lighter background
- Focus: `ring-2 ring-zinc-400 ring-offset-2`
- Disabled: `opacity-50 cursor-not-allowed`

### Inputs

```css
.input {
  height: 36px;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-sm);
  padding: 0 12px;
  font-size: 0.875rem;
  background: hsl(var(--background));
}

.input:focus {
  outline: none;
  ring: 2px;
  ring-color: hsl(var(--ring));
  ring-offset: 2px;
}

.input::placeholder {
  color: hsl(var(--muted-foreground));
}
```

### Cards

```css
.card {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-md);
  background: hsl(var(--background));
  padding: 16px;
}

/* Compact variant */
.card-compact {
  padding: 12px;
}

/* Dark mode: subtle shadow for depth */
.dark .card {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
```

### Interview Question Cards

```css
.interview-card {
  border: 1px solid hsl(var(--border));
  border-left: 3px solid hsl(var(--primary));
  border-radius: var(--radius-md);
  padding: 20px;
}
```

### Quick Action Chips

```css
.chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 100ms ease-out;
}

.chip:hover {
  background: hsl(var(--muted));
  border-color: hsl(var(--muted-foreground) / 0.3);
}

.chip-active {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  border-color: transparent;
}
```

---

## 4. Layout System

### Editor Layout (3-Panel)

```
┌─────────────────────────────────────────────────────────┐
│  Header (48px fixed)                                    │
├────────┬─────────────────────┬──────────────────────────┤
│Sidebar │   Chat Panel        │    Preview Panel         │
│ 48px   │   320px fixed       │    flex-1 (remaining)    │
│        │                     │                          │
│ icons  │   messages          │    ┌──────────────┐      │
│ only   │   interview cards   │    │ iPhone frame │      │
│        │   input bar         │    │   375x667    │      │
│        │                     │    └──────────────┘      │
└────────┴─────────────────────┴──────────────────────────┘
```

### Panel Dimensions

| Panel | Width | Notes |
|-------|-------|-------|
| Sidebar | 48px collapsed, 240px expanded | Icons only when collapsed |
| Chat | 320px fixed | Comfortable reading width |
| Preview | flex-1 | Takes remaining space |
| Preview content | 375px max | Centered iPhone SE frame |

### Header (48px)

- Left: Logo + project name (editable inline)
- Center: Empty (focus on content)
- Right: Version history, Settings, Publish button

### Z-Index Scale

| Token | Value | Use Case |
|-------|-------|----------|
| `z-base` | 0 | Default content |
| `z-sticky` | 10 | Sticky headers |
| `z-dropdown` | 20 | Dropdowns, tooltips |
| `z-modal` | 30 | Modals, dialogs |
| `z-toast` | 40 | Notifications |
| `z-max` | 50 | Critical overlays |

### Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| < 1024px | Hide sidebar, stack chat above preview |
| < 768px | Full-screen chat, preview in sheet/modal |

---

## 5. Motion & Transitions

### Duration Scale

```css
:root {
  --duration-fast: 100ms;    /* hover states, focus rings */
  --duration-normal: 150ms;  /* dropdowns, tooltips */
  --duration-slow: 200ms;    /* modals, panels */
  --duration-slower: 300ms;  /* page transitions */
}
```

### Easing Functions

```css
:root {
  --ease-out: cubic-bezier(0, 0, 0.2, 1);      /* entering */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);       /* exiting */
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1); /* state changes */
}
```

### Animation Keyframes

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

### Component Animations

| Component | Animation |
|-----------|-----------|
| Chat messages | Fade in + slide up 8px (150ms) |
| Interview cards | Fade in + scale from 0.98 (200ms) |
| Quick action chips | Instant (no animation) |
| Modal open | Fade + scale from 0.95 (200ms) |
| Toast notifications | Slide in from right (200ms) |
| Skeleton loaders | Shimmer pulse (1.5s loop) |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 6. Icons & Visual Elements

### Icon Library

- **Library**: Lucide React
- **Default size**: 20px
- **Stroke width**: 1.5px
- **Color**: `currentColor`

### Icon Sizes

| Token | Size | Use Case |
|-------|------|----------|
| `icon-xs` | 14px | Inline with small text |
| `icon-sm` | 16px | Buttons, inputs |
| `icon-md` | 20px | Default, navigation |
| `icon-lg` | 24px | Empty states, features |

### Agent Callout Pills

```css
.agent-callout {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
  font-size: 0.75rem;
  border-radius: var(--radius-full);
}
```

### Loading States

| Type | Style |
|------|-------|
| Skeleton | `bg-zinc-100 rounded animate-pulse` |
| Spinner | Lucide Loader2 with spin animation |
| Streaming | Blinking cursor (▋) |

### Badges

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: hsl(var(--muted));
  color: hsl(var(--foreground));
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-sm);
}

.badge-success { background: hsl(var(--success) / 0.1); color: hsl(var(--success)); }
.badge-warning { background: hsl(var(--warning) / 0.1); color: hsl(var(--warning)); }
.badge-error { background: hsl(var(--destructive) / 0.1); color: hsl(var(--destructive)); }
```

---

## 7. Chat & Interview Components

### Message Bubbles

```css
/* User message */
.message-user {
  max-width: 85%;
  margin-left: auto;
  padding: 12px 16px;
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  border-radius: 16px 16px 4px 16px;
}

/* AI message - no bubble */
.message-ai {
  max-width: 100%;
  color: hsl(var(--foreground));
}
```

### Message Spacing

- Between different senders: 16px
- Between consecutive same-sender: 4px

### Interview Question Card Structure

```
┌─────────────────────────────────────────┐
│ ▎ 📅 Event Details              1 of 3  │  header
├─────────────────────────────────────────┤
│ When is the event?                      │  question
│                                         │
│ ○ This weekend                          │  options
│ ○ Next month                            │
│ ○ Custom date...                        │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Or type your answer...              │ │  text input
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Option Styles

```css
.option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.option:hover {
  background: hsl(var(--muted));
}

.option-selected {
  background: hsl(var(--muted));
  border: 1px solid hsl(var(--primary));
}
```

### Build Plan Card

```css
.build-plan {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-md);
  overflow: hidden;
}

.build-plan-header {
  padding: 12px 16px;
  background: hsl(var(--muted));
  font-weight: 500;
}

.build-plan-content {
  padding: 16px;
}

.build-plan-section {
  margin-bottom: 12px;
}

.build-plan-section:last-child {
  margin-bottom: 0;
}
```

### Input Bar

- Sticky to bottom of chat panel
- Textarea with auto-grow (max 4 lines)
- Send button inside, right-aligned
- Quick action chips row above (horizontally scrollable)

---

## 8. Preview & Design Controls

### Device Frame

```css
.device-frame {
  width: 375px;
  height: 667px;
  border: 8px solid hsl(var(--primary));
  border-radius: 40px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.device-frame-notch {
  width: 120px;
  height: 24px;
  background: hsl(var(--primary));
  border-radius: 0 0 12px 12px;
  margin: 0 auto;
}
```

### Preview Panel Background

```css
.preview-panel {
  background: hsl(var(--muted));
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### Design System Panel

- Width: 320px (matches chat panel)
- Slide-out drawer from right
- Collapsible sections for each category

### Theme Preset Swatches

```css
.theme-swatch {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  cursor: pointer;
}

.theme-swatch-selected {
  border-color: hsl(var(--primary));
}
```

---

## 9. Version History & Modals

### Version List Item

```css
.version-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.version-item:hover {
  background: hsl(var(--muted));
}

.version-item-active {
  color: hsl(var(--foreground));
  font-weight: 500;
}

.version-item-published {
  color: hsl(var(--warning));
}
```

### Modal Structure

```css
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: var(--z-modal);
}

.modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: hsl(var(--background));
  border-radius: var(--radius-lg);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  z-index: var(--z-modal);
}

.modal-sm { max-width: 400px; }
.modal-md { max-width: 480px; }
.modal-lg { max-width: 640px; }
```

---

## 10. Dashboard & Settings

### Project Card

```css
.project-card {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: transform 150ms ease-out;
}

.project-card:hover {
  transform: translateY(-2px);
}

.project-card-thumbnail {
  aspect-ratio: 16 / 9;
  background: hsl(var(--muted));
}

.project-card-content {
  padding: 12px;
}
```

### Settings Sections

```css
.settings-section {
  max-width: 640px;
  margin: 0 auto 24px;
}

.settings-section-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--muted-foreground));
  margin-bottom: 8px;
}

.settings-card {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-md);
  padding: 16px;
}
```

### Toggle Switch

```css
.toggle {
  width: 40px;
  height: 24px;
  background: hsl(var(--muted));
  border-radius: var(--radius-full);
  position: relative;
  cursor: pointer;
  transition: background 150ms ease-out;
}

.toggle-active {
  background: hsl(var(--primary));
}

.toggle-handle {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 150ms ease-out;
}

.toggle-active .toggle-handle {
  transform: translateX(16px);
}
```

---

## 11. File Structure

```
frontend/src/
├── styles/
│   ├── globals.css           # CSS variables, base resets
│   ├── tokens.css            # Color, spacing, typography tokens
│   └── animations.css        # Keyframes, transition utilities
│
├── components/
│   ├── ui/                   # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   └── ...
│   │
│   ├── composed/             # App-specific components
│   │   ├── InterviewCard.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── QuickActionChip.tsx
│   │   ├── BuildPlanCard.tsx
│   │   ├── AgentCallout.tsx
│   │   ├── DeviceFrame.tsx
│   │   ├── ProjectCard.tsx
│   │   └── VersionItem.tsx
│   │
│   └── layout/               # Structural components
│       ├── EditorLayout.tsx
│       ├── DashboardLayout.tsx
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Panel.tsx
│
├── lib/
│   └── utils.ts              # cn() helper, formatters
│
└── hooks/
    └── useTheme.ts           # Dark mode toggle
```

---

## Implementation Notes

### shadcn/ui Configuration

```bash
npx shadcn@latest init
# Select: TypeScript, Tailwind CSS, zinc base color, CSS variables, new-york style
```

### Tailwind Config

```js
// tailwind.config.js
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', ...defaultTheme.fontFamily.sans],
        mono: ['Geist Mono', ...defaultTheme.fontFamily.mono],
      },
      animation: {
        'fade-in': 'fadeIn 150ms ease-out',
        'slide-up': 'slideUp 150ms ease-out',
        'scale-in': 'scaleIn 200ms ease-out',
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
}
```

### Font Loading

```html
<!-- In index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono&display=swap" rel="stylesheet">
```
