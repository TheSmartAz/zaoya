import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { useSettingsStore } from '@/stores/settingsStore'

const MODEL_OPTIONS = [
  { value: 'glm-4.7', label: 'GLM 4.7' },
  { value: 'glm-4.7-flash', label: 'GLM 4.7 Flash' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'doubao', label: 'Doubao' },
  { value: 'qwen', label: 'Qwen' },
  { value: 'qwen-flash', label: 'Qwen Flash' },
  { value: 'hunyuan', label: 'Hunyuan' },
  { value: 'kimi', label: 'Kimi' },
  { value: 'minimax', label: 'Minimax' },
]

const REGION_OPTIONS = [
  { value: 'auto', label: 'Auto' },
  { value: 'us', label: 'United States' },
  { value: 'eu', label: 'Europe' },
  { value: 'cn', label: 'China' },
]

export function ModelSection() {
  const preferredModel = useSettingsStore((state) => state.preferred_model)
  const modelRegion = useSettingsStore((state) => state.model_region)
  const isLoading = useSettingsStore((state) => state.isLoading)
  const saveSettings = useSettingsStore((state) => state.saveSettings)

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Model</CardTitle>
        <CardDescription>
          Pick a default model and routing preference for new generations.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">Preferred model</label>
            <Select
              value={preferredModel}
              disabled={isLoading}
              onChange={(event) =>
                void saveSettings({ preferred_model: event.target.value })
              }
            >
              {MODEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Region</label>
            <Select
              value={modelRegion}
              disabled={isLoading}
              onChange={(event) =>
                void saveSettings({ model_region: event.target.value })
              }
            >
              {REGION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Used as the default for new generations.
        </p>
      </CardContent>
    </Card>
  )
}
