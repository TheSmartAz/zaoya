import { useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useSettingsStore } from '@/stores/settingsStore'

const PRESET_OPTIONS = [
  { value: 'modern-minimal', label: 'Modern Minimal' },
  { value: 'bold-contrast', label: 'Bold Contrast' },
  { value: 'warm-editorial', label: 'Warm Editorial' },
  { value: 'playful-gradient', label: 'Playful Gradient' },
]

const SPACING_OPTIONS = [
  { value: 'compact', label: 'Compact' },
  { value: 'comfortable', label: 'Comfortable' },
  { value: 'spacious', label: 'Spacious' },
]

const RADIUS_OPTIONS = [
  { value: 'none', label: 'Sharp' },
  { value: 'small', label: 'Subtle' },
  { value: 'medium', label: 'Rounded' },
  { value: 'large', label: 'Pill' },
]

const FALLBACK_DEFAULTS = {
  preset: 'modern-minimal',
  primary_color: '#18181b',
  spacing: 'comfortable',
  radius: 'medium',
}

export function DesignSection() {
  const defaultDesignSystem = useSettingsStore((state) => state.default_design_system)
  const isLoading = useSettingsStore((state) => state.isLoading)
  const saveSettings = useSettingsStore((state) => state.saveSettings)

  const defaultsEnabled = Boolean(defaultDesignSystem)
  const designDefaults = useMemo(
    () => ({ ...FALLBACK_DEFAULTS, ...(defaultDesignSystem || {}) }),
    [defaultDesignSystem]
  )

  const updateDefaults = (updates: Record<string, unknown>) => {
    void saveSettings({
      default_design_system: {
        ...designDefaults,
        ...updates,
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Design Defaults</CardTitle>
        <CardDescription>
          Apply your favorite visual system to every new build.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div>
            <p className="text-sm font-medium">Enable design defaults</p>
            <p className="text-xs text-muted-foreground">
              Use these presets when starting a new project.
            </p>
          </div>
          <Switch
            checked={defaultsEnabled}
            disabled={isLoading}
            onCheckedChange={(checked) =>
              void saveSettings({
                default_design_system: checked ? designDefaults : null,
              })
            }
          />
        </div>

        <div
          className={
            defaultsEnabled
              ? 'space-y-4'
              : 'space-y-4 opacity-50 pointer-events-none'
          }
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Preset</label>
              <Select
                value={String(designDefaults.preset)}
                disabled={!defaultsEnabled || isLoading}
                onChange={(event) =>
                  updateDefaults({ preset: event.target.value })
                }
              >
                {PRESET_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Primary color</label>
              <div className="flex items-center gap-2">
                <Input
                  type="color"
                  className="h-9 w-12 p-1"
                  value={String(designDefaults.primary_color)}
                  disabled={!defaultsEnabled || isLoading}
                  onChange={(event) =>
                    updateDefaults({ primary_color: event.target.value })
                  }
                />
                <Input
                  value={String(designDefaults.primary_color)}
                  disabled={!defaultsEnabled || isLoading}
                  onChange={(event) =>
                    updateDefaults({ primary_color: event.target.value })
                  }
                />
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Spacing</label>
              <Select
                value={String(designDefaults.spacing)}
                disabled={!defaultsEnabled || isLoading}
                onChange={(event) =>
                  updateDefaults({ spacing: event.target.value })
                }
              >
                {SPACING_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Corner radius</label>
              <Select
                value={String(designDefaults.radius)}
                disabled={!defaultsEnabled || isLoading}
                onChange={(event) =>
                  updateDefaults({ radius: event.target.value })
                }
              >
                {RADIUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isLoading}
            onClick={() => void saveSettings({ default_design_system: null })}
          >
            Reset to app defaults
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
