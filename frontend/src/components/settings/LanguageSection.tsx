import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useSettingsStore } from '@/stores/settingsStore'

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
]

export function LanguageSection() {
  const language = useSettingsStore((state) => state.language)
  const autoDetect = useSettingsStore((state) => state.auto_detect_language)
  const isLoading = useSettingsStore((state) => state.isLoading)
  const saveSettings = useSettingsStore((state) => state.saveSettings)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Language</CardTitle>
        <CardDescription>
          Choose how Zaoya interprets your prompts and interface text.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Preferred language</label>
          <Select
            value={language}
            disabled={isLoading}
            onChange={(event) =>
              void saveSettings({ language: event.target.value })
            }
          >
            {LANGUAGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <p className="text-xs text-muted-foreground">
            Used when auto-detect is turned off.
          </p>
        </div>

        <div className="flex items-center justify-between rounded-lg border p-4">
          <div>
            <p className="text-sm font-medium">Auto-detect language</p>
            <p className="text-xs text-muted-foreground">
              Detect language based on your prompt.
            </p>
          </div>
          <Switch
            checked={autoDetect}
            disabled={isLoading}
            onCheckedChange={(checked) =>
              void saveSettings({ auto_detect_language: checked })
            }
          />
        </div>
      </CardContent>
    </Card>
  )
}
