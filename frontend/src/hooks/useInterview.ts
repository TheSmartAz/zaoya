import { useState, useCallback } from 'react';
import {
  InterviewQuestion,
  InterviewState,
  InterviewRequest,
  InterviewResponse,
} from '@/types/interview';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function useInterview(template: { id: string; name: string; systemPromptAddition: string }) {
  const [state, setState] = useState<InterviewState>({
    knownFacts: {},
    questionsAsked: [],
    questionsRemaining: 6,
    isReady: false,
  });

  const [currentQuestions, setCurrentQuestions] = useState<InterviewQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = useCallback(async () => {
    if (state.questionsRemaining <= 0) {
      if (!state.isReady) {
        setState((prev) => ({ ...prev, isReady: true }));
      }
      return;
    }

    if (state.isReady) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: InterviewRequest = {
        template,
        knownFacts: state.knownFacts,
        questionsAsked: state.questionsAsked,
      };

      const response = await fetch(`${API_BASE}/api/interview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data: InterviewResponse = await response.json();

      const readyToGenerate = data.readyToGenerate ?? (data as { ready_to_generate?: boolean }).ready_to_generate;

      if (readyToGenerate) {
        setState((prev) => ({ ...prev, isReady: true }));
        setCurrentQuestions([]);
      } else {
        setCurrentQuestions(data.questions);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch questions';
      setError(message);
      // On error, mark as ready to proceed anyway
      setState((prev) => ({ ...prev, isReady: true }));
    } finally {
      setIsLoading(false);
    }
  }, [state.questionsRemaining, state.isReady, state.knownFacts, state.questionsAsked, template]);

  const answerQuestion = useCallback((question: InterviewQuestion, answer: string) => {
    setState((prev) => {
      const remaining = prev.questionsRemaining - 1;
      return {
        ...prev,
        knownFacts: { ...prev.knownFacts, [question.question]: answer },
        questionsAsked: [...prev.questionsAsked, question.id],
        questionsRemaining: remaining,
        isReady: remaining <= 0 ? true : prev.isReady,
      };
    });

    // Clear current questions - next fetch will get new ones
    setCurrentQuestions([]);
  }, []);

  const skipQuestion = useCallback((question: InterviewQuestion) => {
    setState((prev) => {
      const remaining = prev.questionsRemaining - 1;
      return {
        ...prev,
        questionsAsked: [...prev.questionsAsked, question.id],
        questionsRemaining: remaining,
        isReady: remaining <= 0 ? true : prev.isReady,
      };
    });

    // Clear current questions
    setCurrentQuestions([]);
  }, []);

  const setKnownFacts = useCallback((facts: Record<string, string>) => {
    setState((prev) => ({
      ...prev,
      knownFacts: { ...prev.knownFacts, ...facts },
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      knownFacts: {},
      questionsAsked: [],
      questionsRemaining: 6,
      isReady: false,
    });
    setCurrentQuestions([]);
    setError(null);
  }, []);

  return {
    state,
    currentQuestions,
    isLoading,
    error,
    isReady: state.isReady,
    knownFacts: state.knownFacts,
    answerQuestion,
    skipQuestion,
    fetchQuestions,
    setKnownFacts,
    reset,
  };
}
