/** Interview question type */
export type QuestionType = 'single' | 'multi' | 'text' | 'skip';

/** Interview question */
export interface InterviewQuestion {
  id: string;
  question: string;
  type: QuestionType;
  options?: string[];
  skipLabel?: string;
}

/** Interview state */
export interface InterviewState {
  knownFacts: Record<string, string>;
  questionsAsked: string[];
  questionsRemaining: number;
  isReady: boolean;
}

/** Interview API request */
export interface InterviewRequest {
  template: {
    id: string;
    name: string;
    systemPromptAddition: string;
  };
  knownFacts: Record<string, string>;
  questionsAsked: string[];
}

/** Interview API response */
export interface InterviewResponse {
  readyToGenerate: boolean;
  questions: InterviewQuestion[];
}

/** Interview answer */
export interface InterviewAnswer {
  questionId: string;
  answer: string;
}
