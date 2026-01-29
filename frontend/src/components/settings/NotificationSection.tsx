import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { useSettingsStore } from '@/stores/settingsStore'

interface PreferenceRowProps {
  title: string
  description: string
  checked: boolean
  disabled?: boolean
  onChange: (checked: boolean) => void
}

function PreferenceRow({
  title,
  description,
  checked,
  disabled,
  onChange,
}: PreferenceRowProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border p-4',
        disabled && 'opacity-60'
      )}
    >
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Switch checked={checked} disabled={disabled} onCheckedChange={onChange} />
    </div>
  )
}

export function NotificationSection() {
  const {
    email_enabled,
    email_submission_notifications,
    email_weekly_analytics,
    email_project_updates,
    notification_email,
    browser_notifications_enabled,
    browser_notify_submissions,
    browser_notify_published,
    browser_notify_generation,
    isLoading,
    saveSettings,
  } = useSettingsStore((state) => state)

  const [emailDraft, setEmailDraft] = useState(notification_email ?? '')

  useEffect(() => {
    setEmailDraft(notification_email ?? '')
  }, [notification_email])

  const emailDisabled = !email_enabled || isLoading
  const browserDisabled = !browser_notifications_enabled || isLoading

  const handleEmailSave = () => {
    const normalized = emailDraft.trim()
    void saveSettings({ notification_email: normalized || null })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>
          Control when Zaoya reaches out with updates and alerts.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Email notifications</p>
              <p className="text-xs text-muted-foreground">
                Receive project updates in your inbox.
              </p>
            </div>
            <Switch
              checked={email_enabled}
              disabled={isLoading}
              onCheckedChange={(checked) =>
                void saveSettings({ email_enabled: checked })
              }
            />
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_auto]">
            <Input
              type="email"
              placeholder="you@company.com"
              value={emailDraft}
              disabled={emailDisabled}
              onChange={(event) => setEmailDraft(event.target.value)}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={emailDisabled || emailDraft === (notification_email ?? '')}
              onClick={handleEmailSave}
            >
              Save email
            </Button>
          </div>

          <div className="space-y-3">
            <PreferenceRow
              title="Submission alerts"
              description="Get notified when new submissions arrive."
              checked={email_submission_notifications}
              disabled={emailDisabled}
              onChange={(checked) =>
                void saveSettings({ email_submission_notifications: checked })
              }
            />
            <PreferenceRow
              title="Weekly analytics"
              description="A weekly summary of traffic and conversions."
              checked={email_weekly_analytics}
              disabled={emailDisabled}
              onChange={(checked) =>
                void saveSettings({ email_weekly_analytics: checked })
              }
            />
            <PreferenceRow
              title="Project updates"
              description="Release notes, feature drops, and tips."
              checked={email_project_updates}
              disabled={emailDisabled}
              onChange={(checked) =>
                void saveSettings({ email_project_updates: checked })
              }
            />
          </div>
        </div>

        <div className="border-t pt-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Browser notifications</p>
              <p className="text-xs text-muted-foreground">
                Show updates while you work in the editor.
              </p>
            </div>
            <Switch
              checked={browser_notifications_enabled}
              disabled={isLoading}
              onCheckedChange={(checked) =>
                void saveSettings({ browser_notifications_enabled: checked })
              }
            />
          </div>

          <div className="space-y-3">
            <PreferenceRow
              title="New submissions"
              description="Instant alerts when leads arrive."
              checked={browser_notify_submissions}
              disabled={browserDisabled}
              onChange={(checked) =>
                void saveSettings({ browser_notify_submissions: checked })
              }
            />
            <PreferenceRow
              title="Publish status"
              description="Know when a page goes live."
              checked={browser_notify_published}
              disabled={browserDisabled}
              onChange={(checked) =>
                void saveSettings({ browser_notify_published: checked })
              }
            />
            <PreferenceRow
              title="Generation complete"
              description="Alert me when a build finishes."
              checked={browser_notify_generation}
              disabled={browserDisabled}
              onChange={(checked) =>
                void saveSettings({ browser_notify_generation: checked })
              }
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
