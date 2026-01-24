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
