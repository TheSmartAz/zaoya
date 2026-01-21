import { InterviewQuestion } from '@/types/interview';

interface InterviewQuestionProps {
  question: InterviewQuestion;
  onAnswer: (answer: string) => void;
  onSkip: () => void;
  disabled?: boolean;
}

export function InterviewQuestionComponent({
  question,
  onAnswer,
  onSkip,
  disabled = false,
}: InterviewQuestionProps) {
  const handleTextSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const answer = formData.get('answer') as string;
    if (answer?.trim()) {
      onAnswer(answer);
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
      <p className="text-gray-800 font-medium">{question.question}</p>

      {question.options && question.options.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {question.options.map((option) => (
            <button
              key={option}
              onClick={() => onAnswer(option)}
              disabled={disabled}
              className="px-4 py-2 bg-white border-2 border-blue-200 rounded-full hover:border-blue-400 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {option}
            </button>
          ))}
        </div>
      )}

      {question.type === 'text' && (
        <form onSubmit={handleTextSubmit} className="flex gap-2">
          <input
            type="text"
            name="answer"
            disabled={disabled}
            autoComplete="off"
            placeholder="Type your answer..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={disabled}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </form>
      )}

      <button
        onClick={onSkip}
        disabled={disabled}
        className="text-gray-500 text-sm underline hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {question.skipLabel || "Not sure—choose for me"}
      </button>
    </div>
  );
}
