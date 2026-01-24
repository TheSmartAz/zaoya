# Frontend Rebuild Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the Zaoya frontend from scratch with a clean, minimal (Linear-inspired) design system using shadcn/ui, Geist typography, and a preview-dominant 3-panel layout.

**Architecture:** Fresh Vite + React + TypeScript scaffold. shadcn/ui primitives with zinc color scheme. Zustand for state. CSS variables for theming (light + dark). Component layers: ui/ (primitives) → composed/ (app-specific) → layout/ (structural).

**Tech Stack:** Vite 5, React 18, TypeScript, Tailwind CSS, shadcn/ui (new-york style), Zustand, Lucide React icons, Geist font

**Design System Reference:** `docs/plans/2026-01-24-design-system.md`

---

## Phase 1: Project Scaffold & Design Tokens

### Task 1.1: Clean Slate - Remove Old Frontend

**Files:**
- Delete: `frontend/src/` (entire directory)
- Keep: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`

**Step 1: Backup and remove old source**

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya/.worktrees/frontend-rebuild
rm -rf frontend/src
```

**Step 2: Verify deletion**

```bash
ls frontend/
```

Expected: `node_modules`, `package.json`, `vite.config.ts`, etc. — no `src/`

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove old frontend source for rebuild"
```

---

### Task 1.2: Initialize Fresh Vite + React + TypeScript

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/index.html`

**Step 1: Create minimal entry point**

Create `frontend/src/main.tsx`:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

**Step 2: Create App shell**

Create `frontend/src/App.tsx`:

```tsx
export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <h1 className="text-2xl font-semibold p-8">Zaoya</h1>
      <p className="px-8 text-muted-foreground">Frontend rebuild in progress...</p>
    </div>
  )
}
```

**Step 3: Create index.html**

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Zaoya</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 4: Commit**

```bash
git add frontend/src/main.tsx frontend/src/App.tsx frontend/index.html
git commit -m "feat: add fresh React entry point"
```

---

### Task 1.3: Configure Tailwind with Design Tokens

**Files:**
- Create: `frontend/src/styles/globals.css`
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/postcss.config.js` (if needed)

**Step 1: Create globals.css with CSS variables**

Create `frontend/src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
    --radius: 0.375rem;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-family: 'Geist', system-ui, -apple-system, sans-serif;
  }
}
```

**Step 2: Update tailwind.config.js**

Create/update `frontend/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['Geist', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Geist Mono', 'SF Mono', 'Monaco', 'Consolas', 'monospace'],
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out',
        'slide-up': 'slide-up 150ms ease-out',
        'scale-in': 'scale-in 200ms ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

**Step 3: Verify build works**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors

**Step 4: Commit**

```bash
git add frontend/src/styles/globals.css frontend/tailwind.config.js
git commit -m "feat: add design system tokens and Tailwind config"
```

---

### Task 1.4: Install and Configure shadcn/ui

**Files:**
- Create: `frontend/components.json`
- Create: `frontend/src/lib/utils.ts`

**Step 1: Install required dependencies**

```bash
cd frontend
npm install tailwindcss-animate class-variance-authority clsx tailwind-merge lucide-react
npm install -D @types/node
```

**Step 2: Create lib/utils.ts**

Create `frontend/src/lib/utils.ts`:

```ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Step 3: Create components.json**

Create `frontend/components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/styles/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

**Step 4: Update tsconfig.json paths**

Ensure `frontend/tsconfig.json` has path aliases:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Step 5: Update vite.config.ts for aliases**

Update `frontend/vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Step 6: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: configure shadcn/ui with path aliases"
```

---

### Task 1.5: Add Core shadcn/ui Components

**Files:**
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/input.tsx`
- Create: `frontend/src/components/ui/card.tsx`
- Create: `frontend/src/components/ui/scroll-area.tsx`

**Step 1: Create Button component**

Create `frontend/src/components/ui/button.tsx`:

```tsx
import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground shadow hover:bg-primary/90',
        destructive:
          'bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90',
        outline:
          'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground',
        secondary:
          'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
```

**Step 2: Install Radix dependencies**

```bash
npm install @radix-ui/react-slot @radix-ui/react-scroll-area
```

**Step 3: Create Input component**

Create `frontend/src/components/ui/input.tsx`:

```tsx
import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'

export { Input }
```

**Step 4: Create Card component**

Create `frontend/src/components/ui/card.tsx`:

```tsx
import * as React from 'react'
import { cn } from '@/lib/utils'

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-lg border bg-card text-card-foreground shadow-sm',
      className
    )}
    {...props}
  />
))
Card.displayName = 'Card'

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('font-semibold leading-none tracking-tight', className)}
    {...props}
  />
))
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
))
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
))
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
))
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
```

**Step 5: Create ScrollArea component**

Create `frontend/src/components/ui/scroll-area.tsx`:

```tsx
import * as React from 'react'
import * as ScrollAreaPrimitive from '@radix-ui/react-scroll-area'
import { cn } from '@/lib/utils'

const ScrollArea = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root>
>(({ className, children, ...props }, ref) => (
  <ScrollAreaPrimitive.Root
    ref={ref}
    className={cn('relative overflow-hidden', className)}
    {...props}
  >
    <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">
      {children}
    </ScrollAreaPrimitive.Viewport>
    <ScrollBar />
    <ScrollAreaPrimitive.Corner />
  </ScrollAreaPrimitive.Root>
))
ScrollArea.displayName = ScrollAreaPrimitive.Root.displayName

const ScrollBar = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>
>(({ className, orientation = 'vertical', ...props }, ref) => (
  <ScrollAreaPrimitive.ScrollAreaScrollbar
    ref={ref}
    orientation={orientation}
    className={cn(
      'flex touch-none select-none transition-colors',
      orientation === 'vertical' &&
        'h-full w-2.5 border-l border-l-transparent p-[1px]',
      orientation === 'horizontal' &&
        'h-2.5 flex-col border-t border-t-transparent p-[1px]',
      className
    )}
    {...props}
  >
    <ScrollAreaPrimitive.ScrollAreaThumb className="relative flex-1 rounded-full bg-border" />
  </ScrollAreaPrimitive.ScrollAreaScrollbar>
))
ScrollBar.displayName = ScrollAreaPrimitive.ScrollAreaScrollbar.displayName

export { ScrollArea, ScrollBar }
```

**Step 6: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add core shadcn/ui components (button, input, card, scroll-area)"
```

---

## Phase 2: Layout Components

### Task 2.1: Create EditorLayout (3-Panel)

**Files:**
- Create: `frontend/src/components/layout/EditorLayout.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/Header.tsx`
- Create: `frontend/src/components/layout/Panel.tsx`

**Step 1: Create Panel component**

Create `frontend/src/components/layout/Panel.tsx`:

```tsx
import { cn } from '@/lib/utils'

interface PanelProps {
  children: React.ReactNode
  className?: string
}

export function Panel({ children, className }: PanelProps) {
  return (
    <div className={cn('flex flex-col h-full', className)}>
      {children}
    </div>
  )
}

export function PanelHeader({ children, className }: PanelProps) {
  return (
    <div className={cn('flex items-center h-12 px-4 border-b shrink-0', className)}>
      {children}
    </div>
  )
}

export function PanelContent({ children, className }: PanelProps) {
  return (
    <div className={cn('flex-1 overflow-hidden', className)}>
      {children}
    </div>
  )
}
```

**Step 2: Create Sidebar component**

Create `frontend/src/components/layout/Sidebar.tsx`:

```tsx
import { cn } from '@/lib/utils'
import { Home, Settings, History, Layers } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  className?: string
}

const sidebarItems = [
  { icon: Home, label: 'Home', href: '/' },
  { icon: Layers, label: 'Pages', href: '#pages' },
  { icon: History, label: 'History', href: '#history' },
  { icon: Settings, label: 'Settings', href: '#settings' },
]

export function Sidebar({ className }: SidebarProps) {
  return (
    <aside
      className={cn(
        'w-12 border-r bg-background flex flex-col items-center py-2 gap-1',
        className
      )}
    >
      {sidebarItems.map((item) => (
        <Button
          key={item.label}
          variant="ghost"
          size="icon"
          className="h-10 w-10"
          title={item.label}
        >
          <item.icon className="h-5 w-5" />
        </Button>
      ))}
    </aside>
  )
}
```

**Step 3: Create Header component**

Create `frontend/src/components/layout/Header.tsx`:

```tsx
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface HeaderProps {
  projectName?: string
  className?: string
}

export function Header({ projectName = 'Untitled', className }: HeaderProps) {
  return (
    <header
      className={cn(
        'h-12 border-b bg-background flex items-center justify-between px-4',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <span className="font-semibold text-lg">Zaoya</span>
        <span className="text-muted-foreground">/</span>
        <span className="text-sm">{projectName}</span>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm">
          Preview
        </Button>
        <Button size="sm">Publish</Button>
      </div>
    </header>
  )
}
```

**Step 4: Create EditorLayout component**

Create `frontend/src/components/layout/EditorLayout.tsx`:

```tsx
import { cn } from '@/lib/utils'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

interface EditorLayoutProps {
  children: React.ReactNode
  projectName?: string
  className?: string
}

export function EditorLayout({
  children,
  projectName,
  className,
}: EditorLayoutProps) {
  return (
    <div className={cn('h-screen flex flex-col', className)}>
      <Header projectName={projectName} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex overflow-hidden">{children}</main>
      </div>
    </div>
  )
}
```

**Step 5: Create layout index**

Create `frontend/src/components/layout/index.ts`:

```ts
export { EditorLayout } from './EditorLayout'
export { Sidebar } from './Sidebar'
export { Header } from './Header'
export { Panel, PanelHeader, PanelContent } from './Panel'
```

**Step 6: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add layout components (EditorLayout, Sidebar, Header, Panel)"
```

---

### Task 2.2: Create Chat Panel Structure

**Files:**
- Create: `frontend/src/components/chat/ChatPanel.tsx`
- Create: `frontend/src/components/chat/MessageList.tsx`
- Create: `frontend/src/components/chat/InputBar.tsx`
- Create: `frontend/src/components/chat/index.ts`

**Step 1: Create MessageList component**

Create `frontend/src/components/chat/MessageList.tsx`:

```tsx
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface MessageListProps {
  messages: Message[]
  className?: string
}

export function MessageList({ messages, className }: MessageListProps) {
  return (
    <ScrollArea className={cn('flex-1 px-4', className)}>
      <div className="py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <p className="text-lg font-medium">What do you want to create?</p>
            <p className="text-sm mt-1">Describe your page and I'll build it for you.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'animate-slide-up',
                message.role === 'user' ? 'flex justify-end' : ''
              )}
            >
              <div
                className={cn(
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[85%]'
                    : 'text-foreground'
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </ScrollArea>
  )
}
```

**Step 2: Create InputBar component**

Create `frontend/src/components/chat/InputBar.tsx`:

```tsx
import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { ArrowUp } from 'lucide-react'

interface InputBarProps {
  onSend: (message: string) => void
  disabled?: boolean
  className?: string
}

export function InputBar({ onSend, disabled, className }: InputBarProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    if (value.trim() && !disabled) {
      onSend(value.trim())
      setValue('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [value])

  return (
    <div className={cn('border-t p-4', className)}>
      <div className="relative flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to create..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        />
        <Button
          size="icon"
          onClick={handleSubmit}
          disabled={!value.trim() || disabled}
          className="h-10 w-10 shrink-0"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
```

**Step 3: Create ChatPanel component**

Create `frontend/src/components/chat/ChatPanel.tsx`:

```tsx
import { useState } from 'react'
import { Panel, PanelContent } from '@/components/layout'
import { MessageList, type Message } from './MessageList'
import { InputBar } from './InputBar'
import { cn } from '@/lib/utils'

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])

  const handleSend = (content: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
    }
    setMessages((prev) => [...prev, userMessage])

    // Simulate AI response (replace with real API later)
    setTimeout(() => {
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: `I'll help you create that. Let me ask a few questions to understand what you need...`,
      }
      setMessages((prev) => [...prev, aiMessage])
    }, 500)
  }

  return (
    <Panel className={cn('w-80 border-r', className)}>
      <PanelContent className="flex flex-col">
        <MessageList messages={messages} className="flex-1" />
        <InputBar onSend={handleSend} />
      </PanelContent>
    </Panel>
  )
}
```

**Step 4: Create chat index**

Create `frontend/src/components/chat/index.ts`:

```ts
export { ChatPanel } from './ChatPanel'
export { MessageList, type Message } from './MessageList'
export { InputBar } from './InputBar'
```

**Step 5: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add chat panel components (MessageList, InputBar, ChatPanel)"
```

---

### Task 2.3: Create Preview Panel with Device Frame

**Files:**
- Create: `frontend/src/components/preview/PreviewPanel.tsx`
- Create: `frontend/src/components/preview/DeviceFrame.tsx`
- Create: `frontend/src/components/preview/index.ts`

**Step 1: Create DeviceFrame component**

Create `frontend/src/components/preview/DeviceFrame.tsx`:

```tsx
import { cn } from '@/lib/utils'

interface DeviceFrameProps {
  children: React.ReactNode
  className?: string
}

export function DeviceFrame({ children, className }: DeviceFrameProps) {
  return (
    <div
      className={cn(
        'relative bg-primary rounded-[40px] p-2 shadow-2xl',
        className
      )}
    >
      {/* Notch */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[120px] h-[24px] bg-primary rounded-b-2xl z-10" />

      {/* Screen */}
      <div className="relative w-[375px] h-[667px] bg-background rounded-[32px] overflow-hidden">
        {children}
      </div>
    </div>
  )
}
```

**Step 2: Create PreviewPanel component**

Create `frontend/src/components/preview/PreviewPanel.tsx`:

```tsx
import { Panel, PanelContent } from '@/components/layout'
import { DeviceFrame } from './DeviceFrame'
import { cn } from '@/lib/utils'

interface PreviewPanelProps {
  html?: string
  className?: string
}

export function PreviewPanel({ html, className }: PreviewPanelProps) {
  return (
    <Panel className={cn('flex-1 bg-muted/50', className)}>
      <PanelContent className="flex items-center justify-center p-8">
        <DeviceFrame>
          {html ? (
            <iframe
              srcDoc={html}
              className="w-full h-full border-0"
              sandbox="allow-scripts"
              title="Preview"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <p className="text-lg font-medium">Your page will appear here</p>
                <p className="text-sm mt-1">Start by describing what you want to create</p>
              </div>
            </div>
          )}
        </DeviceFrame>
      </PanelContent>
    </Panel>
  )
}
```

**Step 3: Create preview index**

Create `frontend/src/components/preview/index.ts`:

```ts
export { PreviewPanel } from './PreviewPanel'
export { DeviceFrame } from './DeviceFrame'
```

**Step 4: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add preview panel with device frame"
```

---

### Task 2.4: Assemble Editor Page

**Files:**
- Create: `frontend/src/pages/EditorPage.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create EditorPage**

Create `frontend/src/pages/EditorPage.tsx`:

```tsx
import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'

export function EditorPage() {
  return (
    <EditorLayout projectName="My Landing Page">
      <ChatPanel />
      <PreviewPanel />
    </EditorLayout>
  )
}
```

**Step 2: Update App.tsx**

Update `frontend/src/App.tsx`:

```tsx
import { EditorPage } from '@/pages/EditorPage'

export default function App() {
  return <EditorPage />
}
```

**Step 3: Run dev server and verify**

```bash
npm run dev
```

Open browser at http://localhost:5173 — should see:
- Header with "Zaoya / My Landing Page"
- Sidebar with icons
- Chat panel on left (320px)
- Preview panel with device frame on right

**Step 4: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: assemble EditorPage with 3-panel layout"
```

---

## Phase 3: Interview Components

### Task 3.1: Create QuickActionChip Component

**Files:**
- Create: `frontend/src/components/composed/QuickActionChip.tsx`

**Step 1: Create component**

Create `frontend/src/components/composed/QuickActionChip.tsx`:

```tsx
import { cn } from '@/lib/utils'

interface QuickActionChipProps {
  label: string
  onClick: () => void
  active?: boolean
  className?: string
}

export function QuickActionChip({
  label,
  onClick,
  active,
  className,
}: QuickActionChipProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium border transition-colors',
        active
          ? 'bg-primary text-primary-foreground border-transparent'
          : 'bg-background text-foreground border-border hover:bg-muted hover:border-muted-foreground/30',
        className
      )}
    >
      {label}
    </button>
  )
}
```

**Step 2: Commit**

```bash
git add -A
git commit -m "feat: add QuickActionChip component"
```

---

### Task 3.2: Create InterviewCard Component

**Files:**
- Create: `frontend/src/components/composed/InterviewCard.tsx`
- Create: `frontend/src/types/interview.ts`

**Step 1: Create interview types**

Create `frontend/src/types/interview.ts`:

```ts
export interface InterviewOption {
  value: string
  label: string
  description?: string
}

export interface InterviewQuestion {
  id: string
  text: string
  type: 'single_select' | 'multi_select' | 'text' | 'date'
  options?: InterviewOption[]
  allowOther?: boolean
}

export interface InterviewGroup {
  id: string
  title: string
  icon?: string
  questions: InterviewQuestion[]
  currentIndex: number
  totalInGroup: number
}
```

**Step 2: Create InterviewCard component**

Create `frontend/src/components/composed/InterviewCard.tsx`:

```tsx
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { InterviewQuestion, InterviewOption } from '@/types/interview'

interface InterviewCardProps {
  question: InterviewQuestion
  groupTitle: string
  groupIcon?: string
  questionNumber: number
  onAnswer: (questionId: string, value: string | string[]) => void
  onSkip: () => void
  onGenerateNow: () => void
  className?: string
}

export function InterviewCard({
  question,
  groupTitle,
  groupIcon,
  questionNumber,
  onAnswer,
  onSkip,
  onGenerateNow,
  className,
}: InterviewCardProps) {
  const [selected, setSelected] = useState<string[]>([])
  const [otherValue, setOtherValue] = useState('')

  const handleOptionClick = (option: InterviewOption) => {
    if (question.type === 'single_select') {
      setSelected([option.value])
      onAnswer(question.id, option.value)
    } else if (question.type === 'multi_select') {
      setSelected((prev) =>
        prev.includes(option.value)
          ? prev.filter((v) => v !== option.value)
          : [...prev, option.value]
      )
    }
  }

  const handleOtherSubmit = () => {
    if (otherValue.trim()) {
      onAnswer(question.id, otherValue.trim())
      setOtherValue('')
    }
  }

  return (
    <Card className={cn('border-l-[3px] border-l-primary animate-scale-in', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            {groupIcon && <span>{groupIcon}</span>}
            {groupTitle}
          </CardTitle>
          <span className="text-xs text-muted-foreground">
            Question {questionNumber}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="font-medium">{question.text}</p>

        {question.options && (
          <div className="space-y-2">
            {question.options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleOptionClick(option)}
                className={cn(
                  'w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors',
                  selected.includes(option.value)
                    ? 'bg-muted border border-primary'
                    : 'hover:bg-muted border border-transparent'
                )}
              >
                <div
                  className={cn(
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selected.includes(option.value)
                      ? 'border-primary bg-primary'
                      : 'border-muted-foreground'
                  )}
                >
                  {selected.includes(option.value) && (
                    <div className="w-2 h-2 rounded-full bg-primary-foreground" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium">{option.label}</p>
                  {option.description && (
                    <p className="text-xs text-muted-foreground">
                      {option.description}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

        {question.allowOther !== false && (
          <div className="flex gap-2">
            <Input
              placeholder="Or type your answer..."
              value={otherValue}
              onChange={(e) => setOtherValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleOtherSubmit()}
            />
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <Button variant="ghost" size="sm" onClick={onSkip}>
            Skip this question
          </Button>
          <Button size="sm" onClick={onGenerateNow}>
            Generate now →
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: add InterviewCard component with question types"
```

---

### Task 3.3: Create AgentCallout Component

**Files:**
- Create: `frontend/src/components/composed/AgentCallout.tsx`

**Step 1: Create component**

Create `frontend/src/components/composed/AgentCallout.tsx`:

```tsx
import { cn } from '@/lib/utils'
import { ClipboardList, Palette, Settings } from 'lucide-react'

type AgentType = 'requirements' | 'ux' | 'tech'

interface AgentCalloutProps {
  type: AgentType
  message: string
  className?: string
}

const agentConfig: Record<AgentType, { icon: typeof ClipboardList; label: string }> = {
  requirements: { icon: ClipboardList, label: 'RequirementsAgent' },
  ux: { icon: Palette, label: 'UXAgent' },
  tech: { icon: Settings, label: 'TechAgent' },
}

export function AgentCallout({ type, message, className }: AgentCalloutProps) {
  const config = agentConfig[type]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-muted text-muted-foreground text-xs animate-fade-in',
        className
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="font-medium">{config.label}:</span>
      <span>{message}</span>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add -A
git commit -m "feat: add AgentCallout component"
```

---

### Task 3.4: Create BuildPlanCard Component

**Files:**
- Create: `frontend/src/components/composed/BuildPlanCard.tsx`
- Create: `frontend/src/types/buildPlan.ts`

**Step 1: Create build plan types**

Create `frontend/src/types/buildPlan.ts`:

```ts
export interface BuildPlan {
  pages: string[]
  features: string[]
  designStyle: string
  colorScheme?: string
}
```

**Step 2: Create BuildPlanCard component**

Create `frontend/src/components/composed/BuildPlanCard.tsx`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { BuildPlan } from '@/types/buildPlan'

interface BuildPlanCardProps {
  plan: BuildPlan
  onGenerate: () => void
  onEdit: () => void
  className?: string
}

export function BuildPlanCard({
  plan,
  onGenerate,
  onEdit,
  className,
}: BuildPlanCardProps) {
  return (
    <Card className={cn('animate-scale-in', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            📋 Build Plan
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onEdit}>
            Edit
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Pages
          </p>
          <p className="text-sm">{plan.pages.join(', ')}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Features
          </p>
          <p className="text-sm">{plan.features.join(', ')}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Design Style
          </p>
          <p className="text-sm">
            {plan.designStyle}
            {plan.colorScheme && ` (${plan.colorScheme})`}
          </p>
        </div>

        <Button className="w-full mt-4" onClick={onGenerate}>
          Generate Page →
        </Button>
      </CardContent>
    </Card>
  )
}
```

**Step 3: Create composed index**

Create `frontend/src/components/composed/index.ts`:

```ts
export { QuickActionChip } from './QuickActionChip'
export { InterviewCard } from './InterviewCard'
export { AgentCallout } from './AgentCallout'
export { BuildPlanCard } from './BuildPlanCard'
```

**Step 4: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add BuildPlanCard component and composed index"
```

---

## Phase 4: State Management

### Task 4.1: Set Up Zustand Store for Chat

**Files:**
- Create: `frontend/src/stores/chatStore.ts`
- Create: `frontend/src/types/chat.ts`

**Step 1: Install zustand**

```bash
npm install zustand
```

**Step 2: Create chat types**

Create `frontend/src/types/chat.ts`:

```ts
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  type?: 'text' | 'interview' | 'plan'
}

export interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
}
```

**Step 3: Create chat store**

Create `frontend/src/stores/chatStore.ts`:

```ts
import { create } from 'zustand'
import type { ChatMessage } from '@/types/chat'

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null

  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  error: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: Date.now(),
        },
      ],
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearMessages: () => set({ messages: [] }),
}))
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: add Zustand chat store"
```

---

### Task 4.2: Set Up Project Store

**Files:**
- Create: `frontend/src/stores/projectStore.ts`
- Create: `frontend/src/types/project.ts`

**Step 1: Create project types**

Create `frontend/src/types/project.ts`:

```ts
export interface DesignSystem {
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    text: string
  }
  typography: {
    headingFont: string
    bodyFont: string
  }
  spacing: 'compact' | 'comfortable' | 'spacious'
  borderRadius: 'none' | 'small' | 'medium' | 'large'
  animationLevel: 'none' | 'subtle' | 'moderate' | 'energetic'
}

export interface ProjectPage {
  id: string
  name: string
  path: string
  isHome: boolean
  html: string
  css?: string
  js?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  pages: ProjectPage[]
  designSystem: DesignSystem
  currentPageId: string
  createdAt: number
  updatedAt: number
}
```

**Step 2: Create project store**

Create `frontend/src/stores/projectStore.ts`:

```ts
import { create } from 'zustand'
import type { Project, DesignSystem, ProjectPage } from '@/types/project'

const defaultDesignSystem: DesignSystem = {
  colors: {
    primary: '#18181b',
    secondary: '#71717a',
    accent: '#2563eb',
    background: '#ffffff',
    text: '#18181b',
  },
  typography: {
    headingFont: 'Geist',
    bodyFont: 'Geist',
  },
  spacing: 'comfortable',
  borderRadius: 'medium',
  animationLevel: 'subtle',
}

interface ProjectStore {
  project: Project | null
  previewHtml: string | null

  // Actions
  createProject: (name: string) => void
  updateProjectName: (name: string) => void
  updateDesignSystem: (updates: Partial<DesignSystem>) => void
  setPreviewHtml: (html: string) => void
  addPage: (page: Omit<ProjectPage, 'id'>) => void
  updatePage: (pageId: string, updates: Partial<ProjectPage>) => void
  setCurrentPage: (pageId: string) => void
}

export const useProjectStore = create<ProjectStore>((set) => ({
  project: null,
  previewHtml: null,

  createProject: (name) =>
    set({
      project: {
        id: `proj-${Date.now()}`,
        name,
        pages: [
          {
            id: 'home',
            name: 'Home',
            path: '/',
            isHome: true,
            html: '',
          },
        ],
        designSystem: defaultDesignSystem,
        currentPageId: 'home',
        createdAt: Date.now(),
        updatedAt: Date.now(),
      },
    }),

  updateProjectName: (name) =>
    set((state) => ({
      project: state.project
        ? { ...state.project, name, updatedAt: Date.now() }
        : null,
    })),

  updateDesignSystem: (updates) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            designSystem: { ...state.project.designSystem, ...updates },
            updatedAt: Date.now(),
          }
        : null,
    })),

  setPreviewHtml: (html) => set({ previewHtml: html }),

  addPage: (page) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            pages: [
              ...state.project.pages,
              { ...page, id: `page-${Date.now()}` },
            ],
            updatedAt: Date.now(),
          }
        : null,
    })),

  updatePage: (pageId, updates) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            pages: state.project.pages.map((p) =>
              p.id === pageId ? { ...p, ...updates } : p
            ),
            updatedAt: Date.now(),
          }
        : null,
    })),

  setCurrentPage: (pageId) =>
    set((state) => ({
      project: state.project
        ? { ...state.project, currentPageId: pageId }
        : null,
    })),
}))
```

**Step 3: Create stores index**

Create `frontend/src/stores/index.ts`:

```ts
export { useChatStore } from './chatStore'
export { useProjectStore } from './projectStore'
```

**Step 4: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Zustand project store with design system"
```

---

### Task 4.3: Create Theme Hook for Dark Mode

**Files:**
- Create: `frontend/src/hooks/useTheme.ts`

**Step 1: Create useTheme hook**

Create `frontend/src/hooks/useTheme.ts`:

```ts
import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'system'
    return (localStorage.getItem('theme') as Theme) || 'system'
  })

  useEffect(() => {
    const root = window.document.documentElement
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'

    const resolvedTheme = theme === 'system' ? systemTheme : theme

    root.classList.remove('light', 'dark')
    root.classList.add(resolvedTheme)
    localStorage.setItem('theme', theme)
  }, [theme])

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (theme === 'system') {
        const root = window.document.documentElement
        root.classList.remove('light', 'dark')
        root.classList.add(mediaQuery.matches ? 'dark' : 'light')
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme])

  return {
    theme,
    setTheme: setThemeState,
    resolvedTheme:
      theme === 'system'
        ? typeof window !== 'undefined' &&
          window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        : theme,
  }
}
```

**Step 2: Create hooks index**

Create `frontend/src/hooks/index.ts`:

```ts
export { useTheme } from './useTheme'
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: add useTheme hook for dark mode support"
```

---

## Phase 5: Integration & Polish

### Task 5.1: Wire Up ChatPanel with Store

**Files:**
- Modify: `frontend/src/components/chat/ChatPanel.tsx`
- Modify: `frontend/src/components/chat/MessageList.tsx`

**Step 1: Update MessageList to use store types**

Update `frontend/src/components/chat/MessageList.tsx`:

```tsx
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import type { ChatMessage } from '@/types/chat'

interface MessageListProps {
  messages: ChatMessage[]
  className?: string
}

export function MessageList({ messages, className }: MessageListProps) {
  return (
    <ScrollArea className={cn('flex-1 px-4', className)}>
      <div className="py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <p className="text-lg font-medium">What do you want to create?</p>
            <p className="text-sm mt-1">
              Describe your page and I'll build it for you.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'animate-slide-up',
                message.role === 'user' ? 'flex justify-end' : ''
              )}
            >
              <div
                className={cn(
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[85%]'
                    : 'text-foreground'
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </ScrollArea>
  )
}

export type { ChatMessage }
```

**Step 2: Update ChatPanel to use store**

Update `frontend/src/components/chat/ChatPanel.tsx`:

```tsx
import { Panel, PanelContent } from '@/components/layout'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'
import { useChatStore } from '@/stores'
import { cn } from '@/lib/utils'

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const { messages, isLoading, addMessage } = useChatStore()

  const handleSend = (content: string) => {
    addMessage({ role: 'user', content })

    // Simulate AI response (replace with real API later)
    useChatStore.getState().setLoading(true)
    setTimeout(() => {
      addMessage({
        role: 'assistant',
        content: `I'll help you create that. Let me ask a few questions to understand what you need...`,
      })
      useChatStore.getState().setLoading(false)
    }, 500)
  }

  return (
    <Panel className={cn('w-80 border-r', className)}>
      <PanelContent className="flex flex-col">
        <MessageList messages={messages} className="flex-1" />
        <InputBar onSend={handleSend} disabled={isLoading} />
      </PanelContent>
    </Panel>
  )
}
```

**Step 3: Verify build**

```bash
npm run build
```

Expected: Build succeeds

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: wire ChatPanel to Zustand store"
```

---

### Task 5.2: Wire Up PreviewPanel with Store

**Files:**
- Modify: `frontend/src/components/preview/PreviewPanel.tsx`
- Modify: `frontend/src/pages/EditorPage.tsx`

**Step 1: Update PreviewPanel to use store**

Update `frontend/src/components/preview/PreviewPanel.tsx`:

```tsx
import { Panel, PanelContent } from '@/components/layout'
import { DeviceFrame } from './DeviceFrame'
import { useProjectStore } from '@/stores'
import { cn } from '@/lib/utils'

interface PreviewPanelProps {
  className?: string
}

export function PreviewPanel({ className }: PreviewPanelProps) {
  const previewHtml = useProjectStore((state) => state.previewHtml)

  return (
    <Panel className={cn('flex-1 bg-muted/50', className)}>
      <PanelContent className="flex items-center justify-center p-8">
        <DeviceFrame>
          {previewHtml ? (
            <iframe
              srcDoc={previewHtml}
              className="w-full h-full border-0"
              sandbox="allow-scripts"
              title="Preview"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <p className="text-lg font-medium">Your page will appear here</p>
                <p className="text-sm mt-1">
                  Start by describing what you want to create
                </p>
              </div>
            </div>
          )}
        </DeviceFrame>
      </PanelContent>
    </Panel>
  )
}
```

**Step 2: Update EditorPage to initialize project**

Update `frontend/src/pages/EditorPage.tsx`:

```tsx
import { useEffect } from 'react'
import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'
import { useProjectStore } from '@/stores'

export function EditorPage() {
  const { project, createProject } = useProjectStore()

  useEffect(() => {
    if (!project) {
      createProject('My Landing Page')
    }
  }, [project, createProject])

  return (
    <EditorLayout projectName={project?.name}>
      <ChatPanel />
      <PreviewPanel />
    </EditorLayout>
  )
}
```

**Step 3: Verify build and test**

```bash
npm run build
npm run dev
```

Open browser — should see working editor with chat that persists messages.

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: wire PreviewPanel and EditorPage to stores"
```

---

### Task 5.3: Add Types Index and Final Cleanup

**Files:**
- Create: `frontend/src/types/index.ts`
- Verify all imports work

**Step 1: Create types index**

Create `frontend/src/types/index.ts`:

```ts
export type { ChatMessage, ChatState } from './chat'
export type { InterviewOption, InterviewQuestion, InterviewGroup } from './interview'
export type { BuildPlan } from './buildPlan'
export type { Project, ProjectPage, DesignSystem } from './project'
```

**Step 2: Final build verification**

```bash
npm run build
```

Expected: Build succeeds with no errors or warnings

**Step 3: Run dev server final check**

```bash
npm run dev
```

Verify:
- Editor loads with 3-panel layout
- Chat messages persist
- Dark mode toggle would work (can test by adding .dark class to html)
- All components render correctly

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: add types index and finalize Phase 5"
```

---

## Summary

This plan rebuilds the frontend in 5 phases:

1. **Phase 1**: Clean slate, Vite scaffold, design tokens, shadcn/ui setup
2. **Phase 2**: Layout components (EditorLayout, Sidebar, Header, Panel)
3. **Phase 3**: Interview components (QuickActionChip, InterviewCard, AgentCallout, BuildPlanCard)
4. **Phase 4**: State management (Zustand stores for chat and project)
5. **Phase 5**: Integration and wiring everything together

Each task is self-contained with exact file paths, complete code, and verification steps.

---

## Next Steps After This Plan

After completing this plan:

1. **Add routing** — React Router for `/`, `/editor/:id`, `/dashboard`
2. **API integration** — Connect to backend chat endpoint with SSE streaming
3. **More shadcn/ui components** — Dialog, Dropdown, Tooltip, Toast
4. **Design System Panel** — Visual editor for colors, typography
5. **Version History Panel** — Timeline with restore functionality
