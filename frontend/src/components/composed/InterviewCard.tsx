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
    if (question.type === 'multi_select') {
      setSelected((prev) =>
        prev.includes(option.value)
          ? prev.filter((v) => v !== option.value)
          : [...prev, option.value]
      )
      return
    }

    setSelected([option.value])
    onAnswer(question.id, option.value)
  }

  const handleOtherSubmit = () => {
    if (otherValue.trim()) {
      onAnswer(question.id, otherValue.trim())
      setOtherValue('')
    }
  }

  const handleContinue = () => {
    if (question.type === 'multi_select' && selected.length > 0) {
      onAnswer(question.id, selected)
      return
    }
    if (otherValue.trim()) {
      onAnswer(question.id, otherValue.trim())
      setOtherValue('')
    }
  }

  const canContinue =
    (question.type === 'multi_select' && selected.length > 0) ||
    (question.type !== 'multi_select' && otherValue.trim().length > 0)

  return (
    <Card className={cn('border-l-[3px] border-l-primary animate-scale-in', className)}>
      <CardHeader className="pb-3 px-3 sm:px-4 md:px-6">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2 truncate">
            {groupIcon && <span className="shrink-0">{groupIcon}</span>}
            <span className="truncate">{groupTitle}</span>
          </CardTitle>
          <span className="text-xs text-muted-foreground shrink-0">
            Q{questionNumber}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 px-3 sm:px-4 md:px-6">
        <p className="font-medium break-words">{question.text}</p>

        {question.options && (
          <div className="space-y-2">
            {question.options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleOptionClick(option)}
                className={cn(
                  'w-full flex items-start gap-2 sm:gap-3 p-2 sm:p-3 rounded-md text-left transition-all',
                  selected.includes(option.value)
                    ? 'bg-muted border border-primary'
                    : 'hover:bg-muted border border-transparent'
                )}
              >
                <div
                  className={cn(
                    'w-4 h-4 sm:w-5 sm:h-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5',
                    selected.includes(option.value)
                      ? 'border-primary bg-primary'
                      : 'border-muted-foreground'
                  )}
                >
                  {selected.includes(option.value) && (
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-primary-foreground" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium break-words">{option.label}</p>
                  {option.description && (
                    <p className="text-xs text-muted-foreground break-words">
                      {option.description}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

        {question.allowOther !== false && (
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Or type your answer..."
              value={otherValue}
              onChange={(e) => setOtherValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleOtherSubmit()}
              className="flex-1 min-w-0"
            />
            {(otherValue.trim() || question.type === 'single_select') && (
              <Button size="sm" onClick={handleOtherSubmit} className="shrink-0">
                Send
              </Button>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-2">
          <Button variant="ghost" size="sm" onClick={onSkip} className="w-full sm:w-auto">
            Skip
          </Button>
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            {question.type !== 'single_select' && (
              <Button size="sm" onClick={handleContinue} disabled={!canContinue}>
                Continue →
              </Button>
            )}
            <Button variant="secondary" size="sm" onClick={onGenerateNow}>
              Generate now
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
