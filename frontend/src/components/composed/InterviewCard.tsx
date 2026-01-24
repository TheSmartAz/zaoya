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
    if (question.type === 'single_select') {
      setSelected([option.value])
      onAnswer(question.id, option.value)
    } else if (question.type === 'multi_select') {
      setSelected((prev) =>
        prev.includes(option.value)
          ? prev.filter((v) => v !== option.value)
          : [...prev, option.value]
      )
    }
  }

  const handleOtherSubmit = () => {
    if (otherValue.trim()) {
      onAnswer(question.id, otherValue.trim())
      setOtherValue('')
    }
  }

  return (
    <Card className={cn('border-l-[3px] border-l-primary animate-scale-in', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            {groupIcon && <span>{groupIcon}</span>}
            {groupTitle}
          </CardTitle>
          <span className="text-xs text-muted-foreground">
            Question {questionNumber}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="font-medium">{question.text}</p>

        {question.options && (
          <div className="space-y-2">
            {question.options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleOptionClick(option)}
                className={cn(
                  'w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors',
                  selected.includes(option.value)
                    ? 'bg-muted border border-primary'
                    : 'hover:bg-muted border border-transparent'
                )}
              >
                <div
                  className={cn(
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selected.includes(option.value)
                      ? 'border-primary bg-primary'
                      : 'border-muted-foreground'
                  )}
                >
                  {selected.includes(option.value) && (
                    <div className="w-2 h-2 rounded-full bg-primary-foreground" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium">{option.label}</p>
                  {option.description && (
                    <p className="text-xs text-muted-foreground">
                      {option.description}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

        {question.allowOther !== false && (
          <div className="flex gap-2">
            <Input
              placeholder="Or type your answer..."
              value={otherValue}
              onChange={(e) => setOtherValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleOtherSubmit()}
            />
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <Button variant="ghost" size="sm" onClick={onSkip}>
            Skip this question
          </Button>
          <Button size="sm" onClick={onGenerateNow}>
            Generate now →
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
