import { Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { BuildPlanSummary } from '@/types/buildPlanSummary'

interface BuildPlanCardProps {
  plan: BuildPlanSummary
  onGenerate: () => void
  onEdit: () => void
  isGenerating?: boolean
  className?: string
}

export function BuildPlanCard({
  plan,
  onGenerate,
  onEdit,
  isGenerating = false,
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

        <Button
          className="w-full mt-4"
          onClick={onGenerate}
          disabled={isGenerating}
        >
          {isGenerating ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </span>
          ) : (
            'Generate Page →'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
