import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { PageLayout } from '@/components/layout/PageLayout'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LanguageSection } from './LanguageSection'
import { ModelSection } from './ModelSection'
import { DesignSection } from './DesignSection'
import { NotificationSection } from './NotificationSection'
import { AccountSection } from './AccountSection'
import { useSettingsStore } from '@/stores/settingsStore'

export function SettingsPage() {
  const loadSettings = useSettingsStore((state) => state.loadSettings)
  const isLoading = useSettingsStore((state) => state.isLoading)
  const error = useSettingsStore((state) => state.error)

  useEffect(() => {
    void loadSettings()
  }, [loadSettings])

  return (
    <PageLayout
      title="Settings"
      description="Personalize language, models, and notifications across your workspace."
      headerActions={
        isLoading ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Saving changes...
          </div>
        ) : null
      }
    >
      <div className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <Tabs defaultValue="language" className="space-y-4">
          <div className="overflow-x-auto">
            <TabsList className="min-w-max">
              <TabsTrigger value="language">Language</TabsTrigger>
              <TabsTrigger value="model">AI Model</TabsTrigger>
              <TabsTrigger value="design">Design</TabsTrigger>
              <TabsTrigger value="notifications">Notifications</TabsTrigger>
              <TabsTrigger value="account">Account</TabsTrigger>
            </TabsList>
          </div>

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
      </div>
    </PageLayout>
  )
}
