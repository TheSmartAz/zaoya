# Phase 6: Settings Page

**Duration**: Week 5
**Status**: Pending
**Depends On**: None (can be done in parallel with Phase 5)

---

## Phase Overview

This phase implements the Settings page - a centralized place for users to configure language, AI model, design defaults, and notifications. This removes clutter from the editor header and provides a better UX for preferences.

---

## Prerequisites

### Must Be Completed Before Starting
1. **None** - Can be done independently

### External Dependencies
- **shadcn/ui components** - Tabs, Switch, Select, Input
- **API endpoints for settings** (new)

---

## Detailed Tasks

### Task 6.1: Implement Settings API

**Description**: Create backend API for user settings

**File: `backend/app/api/settings.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/settings", tags=["settings"])

class UserSettings(BaseModel):
    # Language
    language: str = "en"
    auto_detect_language: bool = True

    # AI Model
    preferred_model: str = "glm-4.7"
    model_region: str = "auto"

    # Default design system
    default_design_system: Optional[dict] = None

    # Notifications
    email_enabled: bool = True
    email_submission_notifications: bool = True
    email_weekly_analytics: bool = False
    email_project_updates: bool = False
    notification_email: Optional[str] = None

    browser_notifications_enabled: bool = True
    browser_notify_submissions: bool = True
    browser_notify_published: bool = True
    browser_notify_generation: bool = False

@router.get("/")
async def get_settings(user=Depends(get_current_user)) -> UserSettings:
    """Get user settings."""
    # Implementation here

@router.put("/")
async def update_settings(
    settings: UserSettings,
    user=Depends(get_current_user)
) -> UserSettings:
    """Update user settings."""
    # Implementation here
```

**Dependencies**: None
**Parallelizable**: Yes (with Task 6.2)

---

### Task 6.2: Create Settings Store

**Description**: Implement Zustand store for settings

**File: `frontend/src/stores/settingsStore.ts`**

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Settings {
  language: string;
  auto_detect_language: boolean;
  preferred_model: string;
  model_region: string;
  default_design_system: Record<string, unknown> | null;
  email_enabled: boolean;
  email_submission_notifications: boolean;
  email_weekly_analytics: boolean;
  email_project_updates: boolean;
  notification_email: string | null;
  browser_notifications_enabled: boolean;
  browser_notify_submissions: boolean;
  browser_notify_published: boolean;
  browser_notify_generation: boolean;
}

interface SettingsStore extends Settings {
  isLoading: boolean;
  error: string | null;
  loadSettings: () => Promise<void>;
  saveSettings: (settings: Partial<Settings>) => Promise<void>;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      // Default values
      language: 'en',
      auto_detect_language: true,
      preferred_model: 'glm-4.7',
      model_region: 'auto',
      default_design_system: null,
      email_enabled: true,
      email_submission_notifications: true,
      email_weekly_analytics: false,
      email_project_updates: false,
      notification_email: null,
      browser_notifications_enabled: true,
      browser_notify_submissions: true,
      browser_notify_published: true,
      browser_notify_generation: false,
      isLoading: false,
      error: null,

      async loadSettings() {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/settings');
          if (response.ok) {
            const settings = await response.json();
            set({ ...settings, isLoading: false });
          }
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to load settings',
            isLoading: false
          });
        }
      },

      async saveSettings(updates: Partial<Settings>) {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...get(), ...updates })
          });
          if (response.ok) {
            const settings = await response.json();
            set({ ...settings, isLoading: false });
          }
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to save settings',
            isLoading: false
          });
        }
      }
    }),
    { name: 'settings-store' }
  )
);
```

**Dependencies**: Task 6.1
**Parallelizable**: Yes (with Task 6.3)

---

### Task 6.3: Create Settings Components

**Description**: Create Settings page and section components

**File: `frontend/src/components/settings/SettingsPage.tsx`**

```typescript
import React from 'react';
import { useSettingsStore } from '@/stores/settingsStore';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LanguageSection } from './LanguageSection';
import { ModelSection } from './ModelSection';
import { DesignSection } from './DesignSection';
import { NotificationSection } from './NotificationSection';
import { AccountSection } from './AccountSection';

export function SettingsPage() {
  return (
    <PageLayout title="Settings">
      <Tabs defaultValue="language" className="space-y-6">
        <TabsList>
          <TabsTrigger value="language">Language</TabsTrigger>
          <TabsTrigger value="model">AI Model</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>

        <TabsContent value="language">
          <LanguageSection />
        </TabsContent>

        <TabsContent value="model">
          <ModelSection />
        </TabsContent>

        <TabsContent value="design">
          <DesignSection />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationSection />
        </TabsContent>

        <TabsContent value="account">
          <AccountSection />
        </TabsContent>
      </Tabs>
    </PageLayout>
  );
}
```

**Dependencies**: Task 6.2
**Parallelizable**: No

---

### Task 6.4: Remove Header Selectors

**Description**: Remove language/model selectors from ChatPanel header

**File: `frontend/src/components/editor/ChatPanel.tsx`**

```typescript
// Before:
// <ChatPanelHeader>
//   <LanguageSelector />
//   <ModelSelector />
//   <Title />
//   <UserMenu />
// </ChatPanelHeader>

// After:
<ChatPanelHeader>
  <Title />
  <UserMenu />
</ChatPanelHeader>
```

**Dependencies**: Task 6.3
**Parallelizable**: No

---

## Acceptance Criteria

- [ ] Settings page accessible at /settings
- [ ] Language section allows language selection
- [ ] Model section allows model selection
- [ ] Design section allows design defaults
- [ ] Notification section allows notification preferences
- [ ] Settings persist and load correctly
- [ ] Language/model selectors removed from chat header
- [ ] Tests cover settings functionality

---

## Estimated Scope

**Complexity**: Medium

**Key Effort Drivers**:
- Creating multiple UI sections
- Backend API integration
- Removing selectors from existing components

**Estimated Lines of Code**: ~500-700

---

## Testing Strategy

### Unit Tests
- Test settings store actions
- Test component rendering

### Test Files
- `frontend/tests/unit/stores/settingsStore.test.ts`
- `frontend/tests/unit/components/settings/SettingsPage.test.tsx`
