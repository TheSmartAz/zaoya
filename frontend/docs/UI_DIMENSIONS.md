# UI Component Dimensions Reference

## Layout Hierarchy

```
EditorLayout (h-screen, flex-col)
├── Header (h-12 = 48px)
├── Main (flex-1, flex, overflow-hidden)
    ├── Sidebar (w-12 = 48px)
    └── ResizablePanelGroup (orientation: horizontal, id: editor-layout)
        ├── ChatPanel (id: chat-panel)
        │   ├── MessageList (flex-1, px-4)
        │   ├── InterviewCard (conditional, border-t p-4)
        │   ├── BuildPlanCard (conditional, border-t p-4)
        │   └── InputBar (border-t p-4)
        ├── ResizableHandle (withHandle)
        └── PreviewPanel (id: preview-panel)
            └── DeviceFrame
                └── iframe (360px × 780px, 19.5:9)
```

## Component Sizes

| Component | Width | Height | Notes |
|-----------|-------|--------|-------|
| **Header** | 100% | 48px (h-12) | px-4 padding |
| **Sidebar** | 48px (w-12) | 100% | py-2, gap-1 |
| **Chat Panel** | 40% (default) | 100% | min: 25%, max: 65% |
| **Preview Panel** | 60% (default) | 100% | min: 35% |
| **Resize Handle** | 1px (w-px) | 100% | Handle: 16px × 12px |
| **Device Frame** | 365px | 785px | 360×780 + p-2.5 |
| **Screen/iframe** | 360px | 780px | 19.5:9 ratio |
| **Notch** | 100px | 28px | Dynamic Island |

## Internal Component Spacing

| Element | Padding | Gap |
|---------|---------|-----|
| Header | px-4 (16px) | gap-3 (12px), gap-2 (8px) |
| Sidebar icons | py-2 (8px) | gap-1 (4px) |
| MessageList | px-4 (16px) | py-4 (16px), space-y-4 (16px) |
| InterviewCard | p-4 (16px) | space-y-4 (16px), space-y-2 (8px) |
| BuildPlanCard | p-4 (16px) | space-y-3 (12px) |
| InputBar | p-4 (16px) | gap-2 (8px) |
| Preview content | p-8 (32px) | - |

## Button Sizes

| Button | Size | Width | Height |
|--------|------|-------|--------|
| Header actions | sm | auto | auto |
| Send button | icon | 40px (w-10) | 40px (h-10) |
| Sidebar nav | icon | 40px (w-10) | 40px (h-10) |
| Interview actions | sm | auto | auto |
| Option radio | - | 20px (w-5) | 20px (h-5) |
| Radio inner dot | - | 8px (w-2) | 8px (h-2) |

## Text Sizes

| Element | Size | Weight |
|---------|------|--------|
| Header logo | text-lg | font-semibold |
| Header project | text-sm | normal |
| Empty state heading | text-lg | font-medium |
| Empty state sub | text-sm | normal |
| Message text | text-sm | normal |
| Interview question | text-sm | font-medium (in CardTitle) |
| Option label | text-sm | font-medium |
| Option description | text-xs | normal |
| Question number | text-xs | normal |
| Build plan labels | text-xs | font-medium, uppercase |
| Input placeholder | text-sm | normal |

## Border Radius

| Element | Radius |
|---------|--------|
| Device frame outer | rounded-[44px] |
| Device screen | rounded-[36px] |
| Notch | rounded-b-3xl |
| User message bubble | rounded-2xl rounded-br-md |
| Input textarea | rounded-lg |
| Option button | rounded-md |
| Radio button | rounded-full |
| Handle grip | rounded-sm |

## Colors (Themed)

| Element | Color |
|---------|-------|
| Interview card accent | border-l-primary |
| User message bg | bg-primary text-primary-foreground |
| Selected option border/bg | border-primary bg-primary |
| Radio selected | border-primary bg-primary |
| Preview panel | bg-muted/50 |
| Empty state | text-muted-foreground |
| Separator | bg-border |

## Shadow Effects

| Element | Shadow |
|---------|--------|
| Device frame | shadow-2xl |
| Message bubble | none (flat) |
| Cards | none (uses border) |
