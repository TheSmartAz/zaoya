import { useState, useEffect } from 'react';
import { useChatStream } from '@/hooks/useChatStream';
import { useInterview } from '@/hooks/useInterview';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { QuickActions } from './QuickActions';
import { InterviewQuestionComponent } from './InterviewQuestion';
import { QuickAction } from '@/types/quickAction';
import { Template } from '@/types/template';
import { useChatStore } from '@/stores/chatStore';

interface ChatPanelProps {
  template: Template | null;
  templateInputs: Record<string, string>;
  hasGenerated: boolean;
}

export function ChatPanel({ template, templateInputs, hasGenerated }: ChatPanelProps) {
  const { messages, isStreaming, sendMessage } = useChatStream();
  const addMessage = useChatStore((s) => s.addMessage);
  const setInterviewAnswers = useChatStore((s) => s.setInterviewAnswers);

  // Interview hook
  const interview = useInterview(
    template || {
      id: 'custom',
      name: 'Custom Page',
      systemPromptAddition: '',
    }
  );

  const [interviewStarted, setInterviewStarted] = useState(false);

  useEffect(() => {
    setInterviewAnswers(interview.knownFacts);
  }, [interview.knownFacts, setInterviewAnswers]);

  // Start interview when template is set
  useEffect(() => {
    if (template && !hasGenerated && !interviewStarted) {
      // Set known facts from template inputs
      interview.setKnownFacts(templateInputs);
      interview.fetchQuestions();
      setInterviewStarted(true);
    }
  }, [template, hasGenerated, interviewStarted, templateInputs, interview]);

  // Handle interview question answer
  const handleQuestionAnswer = (question: (typeof interview.currentQuestions)[number], answer: string) => {
    interview.answerQuestion(question, answer);

    // Add user message to chat
    addMessage({
      id: `msg-${Date.now()}`,
      role: 'user',
      content: answer,
      timestamp: Date.now(),
    });

    // Fetch next questions or start generation
    setTimeout(() => {
      interview.fetchQuestions();
    }, 300);
  };

  const handleQuestionSkip = (question: (typeof interview.currentQuestions)[number]) => {
    interview.skipQuestion(question);

    // Add skip message
    addMessage({
      id: `msg-${Date.now()}`,
      role: 'user',
      content: "Skip - choose for me",
      timestamp: Date.now(),
    });

    // Fetch next questions
    setTimeout(() => {
      interview.fetchQuestions();
    }, 300);
  };

  const buildContext = (isQuickAction = false) => ({
    template: template ? {
      id: template.id,
      name: template.name,
      systemPromptAddition: template.systemPromptAddition,
    } : null,
    templateInputs,
    interviewAnswers: interview.knownFacts,
    isQuickAction,
  });

  const handleSend = (message: string) => {
    sendMessage(message, buildContext());
  };

  const handleQuickAction = (action: QuickAction) => {
    sendMessage(action.prompt, buildContext(true));
  };

  const currentQuestions = interview.currentQuestions;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <div>
          <h1 className="text-lg font-semibold text-gray-800">
            {template?.name || 'Create Page'}
          </h1>
          {template && (
            <p className="text-xs text-gray-500">{template.description}</p>
          )}
        </div>
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />

        {/* Interview questions */}
        {currentQuestions.length > 0 && !interview.isReady && (
          <div className="p-4 space-y-3">
            {currentQuestions.map((question) => (
              <InterviewQuestionComponent
                key={question.id}
                question={question}
                onAnswer={(answer) => handleQuestionAnswer(question, answer)}
                onSkip={() => handleQuestionSkip(question)}
                disabled={isStreaming}
              />
            ))}
          </div>
        )}

        {/* Ready to generate indicator */}
        {interview.isReady && interviewStarted && !hasGenerated && (
          <div className="p-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
              <p className="text-green-800 text-sm">
                ✅ Ready! Type a message or use quick actions to generate your page.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Quick actions - show after first generation */}
      {hasGenerated && template && (
        <QuickActions
          template={template.id}
          onAction={handleQuickAction}
          disabled={isStreaming}
        />
      )}

      {/* Input bar */}
      <InputBar
        onSend={handleSend}
        disabled={isStreaming || (!!template && !hasGenerated && !interview.isReady)}
      />
    </div>
  );
}
