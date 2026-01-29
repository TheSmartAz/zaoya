interface InterviewCardProps {
  interview: {
    questions: { id: string; question: string; hint?: string }[]
    answers: Record<string, string>
    stats?: {
      asked: number
      answered: number
      skipped: number
    }
  }
}

export function InterviewCard({ interview }: InterviewCardProps) {
  return (
    <div className="max-w-md rounded-lg border bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-lg">🧩</span>
        <span className="font-medium">Interview summary</span>
        {interview.stats && (
          <span className="text-xs text-muted-foreground">
            {interview.stats.answered}/{interview.stats.asked} answered
          </span>
        )}
      </div>
      <div className="space-y-2 text-sm">
        {interview.questions.map((question) => (
          <div key={question.id} className="rounded border border-dashed p-2">
            <div className="text-xs font-medium text-muted-foreground">
              {question.question}
            </div>
            {question.hint && (
              <div className="text-[11px] text-muted-foreground">
                {question.hint}
              </div>
            )}
            <div className="mt-1">{interview.answers[question.id] || '—'}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
