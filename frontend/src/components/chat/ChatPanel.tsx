import { useMemo, useRef, useState } from 'react'
import { Panel, PanelContent } from '@/components/layout'
import { ResizablePanel } from '@/components/ui/resizable'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'
import { useChatStore, useProjectStore } from '@/stores'
import { InterviewCard } from '@/components/composed/InterviewCard'
import { BuildPlanCard } from '@/components/composed/BuildPlanCard'

type InterviewAction = 'start' | 'answer' | 'skip' | 'generate_now' | 'skip_all'

interface InterviewOption {
  value: string
  label: string
  description?: string
}

interface InterviewQuestion {
  id: string
  text: string
  type: 'single_select' | 'multi_select' | 'text' | 'date'
  options?: InterviewOption[]
  allow_other?: boolean
}

interface InterviewGroup {
  id: string
  topic: string
  topic_label: string
  questions: InterviewQuestion[]
  is_completed: boolean
}

interface InterviewAnswerPayload {
  question_id: string
  raw_text: string
  selected_options?: string[] | null
}

interface InterviewTurnResponse {
  state: any
  orchestrator: {
    mode: 'interview' | 'off_topic' | 'finish'
    next_action:
      | { type: 'ask_group'; group: InterviewGroup }
      | { type: 'ask_followup'; questions: InterviewQuestion[]; reason: string }
      | { type: 'finish'; plan: any; product_document?: any }
      | { type: 'handle_offtopic'; response: string; return_to: string }
      | { type: 'suggest_early_finish'; message: string }
    agent_callouts?: Array<{ agent: string; content: string }>
    brief_patch?: Record<string, any>
  }
}

type ChatRequestMessage = { role: 'user' | 'assistant' | 'system'; content: string }

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const { messages, isLoading, addMessage, setLoading, setError, appendToMessage } =
    useChatStore()
  const setPreviewHtml = useProjectStore((state) => state.setPreviewHtml)
  const [interviewState, setInterviewState] = useState<any | null>(null)
  const [currentGroup, setCurrentGroup] = useState<InterviewGroup | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [pendingAnswers, setPendingAnswers] = useState<
    Record<string, InterviewAnswerPayload>
  >({})
  const [buildPlan, setBuildPlan] = useState<any | null>(null)
  const [productDocument, setProductDocument] = useState<any | null>(null)
  const [mode, setMode] = useState<'idle' | 'interview' | 'chat'>('idle')
  const [autoGenerate, setAutoGenerate] = useState(false)
  const chatHistoryRef = useRef<ChatRequestMessage[]>([])

  const currentQuestion = useMemo(() => {
    if (!currentGroup) {
      return null
    }
    return currentGroup.questions[currentQuestionIndex] || null
  }, [currentGroup, currentQuestionIndex])

  const uiBuildPlan = useMemo(() => {
    if (!buildPlan) {
      return null
    }
    const pages =
      buildPlan.pages?.map((page: any) => page.name || page.path || page.id) || []
    const designStyle =
      buildPlan.design_system?.style ||
      buildPlan.design_system?.theme ||
      buildPlan.design_system?.name ||
      'Modern'
    const colorScheme =
      buildPlan.design_system?.colors?.primary ||
      buildPlan.design_system?.color_palette?.[0] ||
      undefined
    return {
      pages,
      features: buildPlan.features || [],
      designStyle,
      colorScheme,
    }
  }, [buildPlan])

  const disabledInput = isLoading || (mode === 'interview' && !!currentGroup)

  const handleSend = async (content: string) => {
    addMessage({ role: 'user', content })

    if (mode === 'idle') {
      setLoading(true)
      await submitInterview('start', [], content)
      setLoading(false)
      return
    }

    if (mode === 'chat') {
      await streamChat([{ role: 'user', content }], true)
      return
    }
  }

  const submitInterview = async (
    action: InterviewAction,
    answers: InterviewAnswerPayload[] = [],
    userMessage?: string
  ) => {
    setError(null)
    try {
      const payload: any = {
        action,
        answers,
        userMessage,
      }
      if (action === 'start') {
        payload.templateInputs = {}
      } else {
        payload.state = interviewState
      }

      const response = await fetch(`${API_BASE_URL}/api/interview/v2`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data: InterviewTurnResponse = await response.json()
      setInterviewState(data.state)
      handleOrchestratorResponse(data, action)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Interview failed')
    }
  }

  const handleOrchestratorResponse = (
    data: InterviewTurnResponse,
    action: InterviewAction
  ) => {
    const next = data.orchestrator.next_action
    if (next.type === 'ask_group') {
      setMode('interview')
      setCurrentGroup(next.group)
      setCurrentQuestionIndex(0)
      setPendingAnswers({})
      return
    }

    if (next.type === 'ask_followup') {
      setMode('interview')
      setCurrentGroup({
        id: `followup_${Date.now()}`,
        topic: 'follow_up',
        topic_label: 'Follow-up',
        questions: next.questions,
        is_completed: false,
      })
      setCurrentQuestionIndex(0)
      setPendingAnswers({})
      return
    }

    if (next.type === 'finish') {
      setMode('chat')
      setCurrentGroup(null)
      setPendingAnswers({})
      setBuildPlan(next.plan)
      setProductDocument(next.product_document || null)
      if (next.plan && (action === 'generate_now' || action === 'answer' || autoGenerate)) {
        setAutoGenerate(false)
        void generateFromPlan(next.plan, next.product_document || null)
      } else if (!next.plan) {
        setAutoGenerate(false)
        void submitInterview('generate_now')
      }
      return
    }

    if (next.type === 'suggest_early_finish') {
      setAutoGenerate(true)
      void submitInterview('generate_now')
      return
    }
  }

  const buildAnswerPayload = (
    question: InterviewQuestion,
    value: string | string[]
  ): InterviewAnswerPayload => {
    if (Array.isArray(value)) {
      return { question_id: question.id, raw_text: '', selected_options: value }
    }

    const optionValues = question.options?.map((opt) => opt.value) || []
    if (question.type !== 'text' && question.type !== 'date') {
      return {
        question_id: question.id,
        raw_text: '',
        selected_options: optionValues.includes(value) ? [value] : undefined,
      }
    }

    if (optionValues.includes(value)) {
      return { question_id: question.id, raw_text: '', selected_options: [value] }
    }

    return { question_id: question.id, raw_text: value }
  }

  const handleAnswer = async (question: InterviewQuestion, value: string | string[]) => {
    const answerPayload = buildAnswerPayload(question, value)
    const nextAnswers = { ...pendingAnswers, [question.id]: answerPayload }
    setPendingAnswers(nextAnswers)

    if (!currentGroup) {
      return
    }

    if (currentQuestionIndex < currentGroup.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
      return
    }

    setLoading(true)
    await submitInterview('answer', Object.values(nextAnswers))
    setLoading(false)
  }

  const handleSkipQuestion = async (question: InterviewQuestion) => {
    const answerPayload: InterviewAnswerPayload = {
      question_id: question.id,
      raw_text: '',
      selected_options: ['skip'],
    }
    await handleAnswer(question, answerPayload.selected_options || 'skip')
  }

  const handleGenerateNow = async () => {
    setLoading(true)
    setAutoGenerate(true)
    await submitInterview('generate_now')
    setLoading(false)
  }

  const streamChat = async (
    newMessages: ChatRequestMessage[],
    addUserMessageToHistory: boolean
  ) => {
    setError(null)
    setLoading(true)

    if (addUserMessageToHistory) {
      chatHistoryRef.current = [...chatHistoryRef.current, ...newMessages]
    }

    const assistantMessageId = addMessage({ role: 'assistant', content: '' })
    let fullContent = ''
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: chatHistoryRef.current,
          stream: true,
        }),
      })

      if (!response.body) {
        throw new Error('No response stream')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const data = line.slice(5).trim()
          if (data === '[DONE]') {
            break
          }
          try {
            const payload = JSON.parse(data)
            const delta = payload?.choices?.[0]?.delta?.content
            if (delta) {
              fullContent += delta
              appendToMessage(assistantMessageId, delta)
            }
          } catch {
            // ignore malformed chunks
          }
        }
      }

      chatHistoryRef.current = [
        ...chatHistoryRef.current,
        { role: 'assistant', content: fullContent },
      ]
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Chat failed')
    } finally {
      setLoading(false)
    }

    const extractedHtml = extractHtml(fullContent)
    if (extractedHtml) {
      setPreviewHtml(extractedHtml)
    }
  }

  const extractHtml = (content: string) => {
    const match = content.match(/```html\s*([\s\S]*?)```/i)
    if (match?.[1]) {
      return match[1].trim()
    }
    return null
  }

  const generateFromPlan = async (plan: any, productDoc: any | null) => {
    const promptPayload = {
      plan,
      product_document: productDoc,
    }
    const prompt = `Generate a mobile-first HTML page using Tailwind CSS based on the following plan JSON:\n${JSON.stringify(
      promptPayload,
      null,
      2
    )}`
    await streamChat([{ role: 'user', content: prompt }], true)
  }

  const handleEditPlan = () => {
    addMessage({
      role: 'assistant',
      content: 'Plan edits are not wired up yet. Tell me what you want to change.',
    })
  }

  return (
    <ResizablePanel
      id="chat-panel"
      defaultSize={25}
      minSize={10}
      maxSize={60}
    >
      <Panel>
        <PanelContent className="flex flex-col">
          <MessageList messages={messages} className="flex-1" />
          {currentQuestion && currentGroup && (
            <div className="border-t p-4">
              <InterviewCard
                key={currentQuestion.id}
                question={currentQuestion}
                groupTitle={currentGroup.topic_label}
                questionNumber={currentQuestionIndex + 1}
                onAnswer={(_questionId, value) => handleAnswer(currentQuestion, value)}
                onSkip={() => handleSkipQuestion(currentQuestion)}
                onGenerateNow={handleGenerateNow}
                className="w-full"
              />
            </div>
          )}
          {mode === 'chat' && uiBuildPlan && (
            <div className="border-t p-4">
              <BuildPlanCard
                plan={uiBuildPlan}
                onGenerate={() => generateFromPlan(buildPlan, productDocument)}
                onEdit={handleEditPlan}
              />
            </div>
          )}
          <InputBar onSend={handleSend} disabled={disabledInput} />
        </PanelContent>
      </Panel>
    </ResizablePanel>
  )
}
