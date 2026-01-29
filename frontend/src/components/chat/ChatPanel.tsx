import { useMemo, useRef, useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { Panel, PanelContent } from '@/components/layout'
import { ResizablePanel } from '@/components/ui/resizable'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'
import { useBuildStore, useChatStore, useProjectStore, useSettingsStore } from '@/stores'
import { InterviewCard } from '@/components/composed/InterviewCard'
import { BuildPlanCard } from '@/components/composed/BuildPlanCard'
import { useBuildStream } from '@/hooks'
import type { BuildPlanSummary as UiBuildPlan } from '@/types/buildPlanSummary'

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

interface InterviewBuildPlanPage {
  id?: string
  name?: string
  path?: string
}

interface InterviewBuildPlanDesignSystem {
  style?: string
  theme?: string
  name?: string
  colors?: {
    primary?: string
  }
  color_palette?: string[]
}

interface InterviewBuildPlan {
  pages?: InterviewBuildPlanPage[]
  design_system?: InterviewBuildPlanDesignSystem
  features?: string[]
}

type ProductDocument = Record<string, unknown>

interface InterviewState {
  brief?: Record<string, unknown>
  build_plan?: InterviewBuildPlan | null
  product_document?: ProductDocument | null
}

interface InterviewTurnResponse {
  state: InterviewState
  orchestrator: {
    mode: 'interview' | 'off_topic' | 'finish'
    next_action:
      | { type: 'ask_group'; group: InterviewGroup }
      | { type: 'ask_followup'; questions: InterviewQuestion[]; reason: string }
      | {
          type: 'finish'
          plan: InterviewBuildPlan | null
          product_document?: ProductDocument
          brief?: Record<string, unknown>
        }
      | { type: 'handle_offtopic'; response: string; return_to: string }
      | { type: 'suggest_early_finish'; message: string }
    agent_callouts?: Array<{ agent: string; content: string }>
    brief_patch?: Record<string, unknown>
  }
}

type ChatRequestMessage = { role: 'user' | 'assistant' | 'system'; content: string }

type ChatStreamChunk = { choices?: Array<{ delta?: { content?: string } }> }

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const normalizeSseChunk = (chunk: string) => chunk.replace(/\r\n/g, '\n')
const extractSseDataLines = (raw: string) =>
  normalizeSseChunk(raw)
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trim())
    .filter((line) => line && line !== '[DONE]')
const parseJsonCandidates = <T,>(raw: string): T[] => {
  const trimmed = raw.trim()
  if (!trimmed) return []
  const dataLines = extractSseDataLines(trimmed)
  const candidates = dataLines.length > 0 ? dataLines : [trimmed]
  const parsed: T[] = []
  for (const candidate of candidates) {
    try {
      parsed.push(JSON.parse(candidate) as T)
    } catch {
      // ignore malformed chunks
    }
  }
  return parsed
}

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const {
    messages,
    isLoading: isChatStreaming,
    addMessage,
    setLoading: setChatStreaming,
    setError,
    appendToMessage,
  } = useChatStore()
  const setPreviewHtml = useProjectStore((state) => state.setPreviewHtml)
  const loadProductDoc = useProjectStore((state) => state.loadProductDoc)
  const project = useProjectStore((state) => state.project)
  const isBuilding = useBuildStore((state) => state.isBuilding)
  const abortBuild = useBuildStore((state) => state.abortBuild)
  const setStreamStatus = useBuildStore((state) => state.setStreamStatus)
  const setStreamError = useBuildStore((state) => state.setStreamError)
  const preferredModel = useSettingsStore((state) => state.preferred_model)
  const defaultDesignSystem = useSettingsStore((state) => state.default_design_system)
  const settingsLanguage = useSettingsStore((state) => state.language)
  const autoDetectLanguage = useSettingsStore((state) => state.auto_detect_language)
  const [currentGroup, setCurrentGroup] = useState<InterviewGroup | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [pendingAnswers, setPendingAnswers] = useState<
    Record<string, InterviewAnswerPayload>
  >({})
  const [buildPlan, setBuildPlan] = useState<InterviewBuildPlan | null>(null)
  const [productDocument, setProductDocument] = useState<ProductDocument | null>(null)
  const [mode, setMode] = useState<'idle' | 'interview' | 'chat'>('idle')
  const [autoGenerate, setAutoGenerate] = useState(false)
  const [isInterviewLoading, setIsInterviewLoading] = useState(false)
  const chatHistoryRef = useRef<ChatRequestMessage[]>([])
  const isChatStreamingRef = useRef(false)

  useEffect(() => {
    if (!import.meta.env.DEV) return undefined
    ;(window as any).__chatPanelTest = {
      setMode,
      setBuildPlan,
      setProductDocument,
    }
    return () => {
      delete (window as any).__chatPanelTest
    }
  }, [setMode, setBuildPlan, setProductDocument])

  useBuildStream(project?.id || '')

  const currentQuestion = useMemo(() => {
    if (!currentGroup) {
      return null
    }
    return currentGroup.questions[currentQuestionIndex] || null
  }, [currentGroup, currentQuestionIndex])

  const uiBuildPlan = useMemo<UiBuildPlan | null>(() => {
    if (!buildPlan) {
      return null
    }
    const pages = (buildPlan.pages ?? [])
      .map((page) => page.name || page.path || page.id)
      .filter((value): value is string => Boolean(value))
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

  const disabledInput =
    isChatStreaming || isInterviewLoading || (mode === 'interview' && !!currentGroup)

  const handleSend = async (content: string) => {
    if (isChatStreamingRef.current || isInterviewLoading) return
    addMessage({ role: 'user', content })

    if (mode === 'idle') {
      await submitInterview('start', [], content)
      return
    }

    if (mode === 'chat') {
      const handled = await tryProductDocEdit(content)
      if (handled) return
      await streamChat([{ role: 'user', content }], true)
      return
    }
  }

  const tryProductDocEdit = async (content: string) => {
    if (!project?.id) return false
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${project.id}/product-doc/edit`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: content }),
        }
      )

      if (!response.ok) return false
      const result = (await response.json()) as { handled?: boolean }
      if (result?.handled) {
        await loadProductDoc(project.id)
        addMessage({
          role: 'assistant',
          content: '已更新 ProductDoc，可以在预览面板查看。',
        })
        window.dispatchEvent(new CustomEvent('open-product-doc'))
        return true
      }
    } catch {
      return false
    }
    return false
  }

  const streamProjectInterview = async (
    payload: Record<string, unknown>,
    action: InterviewAction
  ) => {
    if (!project?.id) {
      throw new Error('Project not available')
    }
    const response = await fetch(`${API_BASE_URL}/api/projects/${project.id}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || 'Interview failed')
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let rawText = ''
    let receivedPayload = false
    const responseClone = response.clone()

    const emitBuildEvent = (eventType: string, data: unknown) => {
      window.dispatchEvent(
        new CustomEvent('build-sse-event', {
          detail: { event: eventType, data },
        })
      )
    }

    const parseSseChunk = (chunk: string) => {
      const lines = chunk.split('\n')
      let eventType: string | undefined
      const dataLines: string[] = []
      for (const line of lines) {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim()
        }
        if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trim())
        }
      }
      if (dataLines.length === 0) return null
      return { eventType, data: dataLines.join('\n') }
    }

    const processChunk = (chunk: string) => {
      buffer += normalizeSseChunk(chunk)
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const parsed = parseSseChunk(part.trim())
        if (!parsed) continue
        const { eventType, data } = parsed
        if (data === '[DONE]') {
          break
        }
        if (eventType) {
          if (eventType === 'error') {
            try {
              const errorPayload = JSON.parse(data) as { message?: string }
              setError(errorPayload?.message || 'Stream error')
            } catch {
              setError(data || 'Stream error')
            }
            if (isBuilding) {
              setStreamStatus('reconnecting')
              setStreamError('Connection lost, trying to resume build...')
            }
            continue
          }
          if (eventType !== 'message') {
            try {
              const eventPayload = JSON.parse(data)
              emitBuildEvent(eventType, eventPayload)
            } catch {
              // ignore malformed chunks
            }
            continue
          }
        }

        try {
          const payload = JSON.parse(data) as InterviewTurnResponse
          if (payload?.state && payload?.orchestrator) {
            receivedPayload = true
            handleOrchestratorResponse(payload, action)
          }
        } catch {
          // ignore malformed chunks
        }
      }
    }

    const flushBuffer = () => {
      if (!buffer.trim()) return
      const chunk = normalizeSseChunk(buffer)
      buffer = ''
      const parsed = parseSseChunk(chunk.trim())
      if (!parsed) return
      const { eventType, data } = parsed
      if (data === '[DONE]') return
      if (eventType) {
        if (eventType === 'error') {
          try {
            const errorPayload = JSON.parse(data) as { message?: string }
            setError(errorPayload?.message || 'Stream error')
          } catch {
            setError(data || 'Stream error')
          }
          if (isBuilding) {
            setStreamStatus('reconnecting')
            setStreamError('Connection lost, trying to resume build...')
          }
          return
        }
        if (eventType !== 'message') {
          try {
            const eventPayload = JSON.parse(data)
            emitBuildEvent(eventType, eventPayload)
          } catch {
            // ignore malformed chunks
          }
          return
        }
      }

      try {
        const payload = JSON.parse(data) as InterviewTurnResponse
        if (payload?.state && payload?.orchestrator) {
          receivedPayload = true
          handleOrchestratorResponse(payload, action)
        }
      } catch {
        // ignore malformed chunks
      }
    }

    if (!response.body) {
      const text = await response.text()
      if (!text) {
        throw new Error('No response stream')
      }
      rawText = text
      processChunk(text)
      if (!receivedPayload) {
        throw new Error('Interview response missing')
      }
      return
    }

    let usedFallback = false
    let fallbackText: string | null = null
    try {
      const reader = response.body.getReader()

      let done = false
      while (!done) {
        const readResult = await reader.read()
        done = readResult.done
        if (done) break
        const decoded = decoder.decode(readResult.value, { stream: true })
        rawText += decoded
        processChunk(decoded)
      }
      flushBuffer()
    } catch {
      usedFallback = true
      buffer = ''
      fallbackText = await responseClone.text()
      if (fallbackText) {
        rawText = rawText || fallbackText
        processChunk(fallbackText)
        flushBuffer()
      }
    }

    if (!receivedPayload) {
      if (!usedFallback) {
        buffer = ''
        fallbackText = await responseClone.text()
        if (fallbackText) {
          rawText = rawText || fallbackText
          processChunk(fallbackText)
          flushBuffer()
        }
      }
    }

    if (!receivedPayload) {
      const candidateSource = fallbackText || rawText
      if (!candidateSource) {
        // continue to error below
      }
      const candidates = candidateSource
        ? parseJsonCandidates<InterviewTurnResponse>(candidateSource)
        : []
      for (const candidate of candidates) {
        if (candidate?.state && candidate?.orchestrator) {
          receivedPayload = true
          handleOrchestratorResponse(candidate, action)
          break
        }
      }
    }

    if (!receivedPayload) {
      throw new Error('Interview response missing')
    }
  }

  const submitInterview = async (
    action: InterviewAction,
    answers: InterviewAnswerPayload[] = [],
    userMessage?: string
  ) => {
    setError(null)
    if (!project?.id || !UUID_PATTERN.test(project.id)) {
      setError('Project not available')
      return
    }

    const payload: Record<string, unknown> = {
      action,
      answers,
      model: preferredModel,
      language: settingsLanguage,
      auto_detect_language: autoDetectLanguage,
    }
    if (userMessage) {
      payload.content = userMessage
    }

    setIsInterviewLoading(true)
    try {
      await streamProjectInterview(payload, action)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Interview failed')
      if (isBuilding) {
        setStreamStatus('reconnecting')
        setStreamError('Connection lost, trying to resume build...')
      }
    } finally {
      setIsInterviewLoading(false)
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
      const mergedPlan = mergePlanWithDefaults(next.plan)
      setBuildPlan(mergedPlan)
      setProductDocument(next.product_document || null)

      if (mergedPlan && (action === 'generate_now' || action === 'answer' || autoGenerate)) {
        setAutoGenerate(false)
        void generateFromPlan(mergedPlan, next.product_document || null)
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

    await submitInterview('answer', Object.values(nextAnswers))
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
    if (isChatStreamingRef.current) return
    setAutoGenerate(true)
    await submitInterview('generate_now')
  }

  const streamChat = async (
    newMessages: ChatRequestMessage[],
    addUserMessageToHistory: boolean
  ) => {
    if (isChatStreamingRef.current) return
    isChatStreamingRef.current = true
    setError(null)
    setChatStreaming(true)

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
          model: preferredModel,
        }),
      })

      const responseClone = response.clone()
      const decoder = new TextDecoder()
      let buffer = ''
      let rawText = ''
      let gotDelta = false

      const processChunk = (chunk: string) => {
        buffer += normalizeSseChunk(chunk)
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
            const payload = JSON.parse(data) as ChatStreamChunk
            const delta = payload?.choices?.[0]?.delta?.content
            if (delta) {
              fullContent += delta
              gotDelta = true
              appendToMessage(assistantMessageId, delta)
            }
          } catch {
            // ignore malformed chunks
          }
        }
      }

      const flushBuffer = () => {
        if (!buffer.trim()) return
        const chunk = normalizeSseChunk(buffer)
        buffer = ''
        const line = chunk.trim()
        if (!line.startsWith('data:')) return
        const data = line.slice(5).trim()
        if (data === '[DONE]') return
        try {
          const payload = JSON.parse(data) as ChatStreamChunk
          const delta = payload?.choices?.[0]?.delta?.content
          if (delta) {
            fullContent += delta
            gotDelta = true
            appendToMessage(assistantMessageId, delta)
          }
        } catch {
          // ignore malformed chunks
        }
      }

      if (!response.body) {
        const text = await response.text()
        if (!text) {
          throw new Error('No response stream')
        }
        rawText = text
        processChunk(text)
        flushBuffer()
      } else {
        const reader = response.body.getReader()

        let done = false
        while (!done) {
          const readResult = await reader.read()
          done = readResult.done
          if (done) break
          const value = readResult.value
          const decoded = decoder.decode(value, { stream: true })
          rawText += decoded
          processChunk(decoded)
        }
        flushBuffer()
      }

      let fallbackText: string | null = null
      if (!gotDelta) {
        buffer = ''
        fallbackText = await responseClone.text()
        if (fallbackText) {
          processChunk(fallbackText)
          flushBuffer()
        }
      }

      if (!gotDelta && fallbackText) {
        const candidates = parseJsonCandidates<
          ChatStreamChunk & { choices?: Array<{ message?: { content?: string } }> }
        >(fallbackText)
        for (const candidate of candidates) {
          const delta = candidate?.choices?.[0]?.delta?.content
          const message = candidate?.choices?.[0]?.message?.content
          const nextContent = delta || message
          if (nextContent) {
            fullContent += nextContent
            gotDelta = true
            appendToMessage(assistantMessageId, nextContent)
          }
        }
      }

      if (!gotDelta && rawText) {
        const candidates = parseJsonCandidates<
          ChatStreamChunk & { choices?: Array<{ message?: { content?: string } }> }
        >(rawText)
        for (const candidate of candidates) {
          const delta = candidate?.choices?.[0]?.delta?.content
          const message = candidate?.choices?.[0]?.message?.content
          const nextContent = delta || message
          if (nextContent) {
            fullContent += nextContent
            gotDelta = true
            appendToMessage(assistantMessageId, nextContent)
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
      isChatStreamingRef.current = false
      setChatStreaming(false)
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

  const generateFromPlan = async (
    plan: InterviewBuildPlan,
    productDoc: ProductDocument | null
  ) => {
    const mergedPlan = mergePlanWithDefaults(plan)
    const promptPayload = {
      plan: mergedPlan,
      product_document: productDoc,
    }
    const prompt = `Generate a mobile-first HTML page using Tailwind CSS based on the following plan JSON:\n${JSON.stringify(
      promptPayload,
      null,
      2
    )}`
    await streamChat([{ role: 'user', content: prompt }], true)
  }

  const mergePlanWithDefaults = (
    plan: InterviewBuildPlan | null | undefined
  ): InterviewBuildPlan | null => {
    if (!plan) return null
    if (!defaultDesignSystem) return plan
    const mergedDesignSystem = {
      ...(plan.design_system ?? {}),
      ...defaultDesignSystem,
    } as InterviewBuildPlanDesignSystem
    return { ...plan, design_system: mergedDesignSystem }
  }

  const handleEditPlan = () => {
    addMessage({
      role: 'assistant',
      content: 'Plan edits are not wired up yet. Tell me what you want to change.',
    })
  }

  const handleGeneratePlan = () => {
    if (isChatStreamingRef.current) return
    if (!buildPlan) {
      return
    }
    void generateFromPlan(buildPlan, productDocument)
  }

  return (
    <ResizablePanel
      id="chat-panel"
      defaultSize={25}
      minSize={10}
      maxSize={60}
      className={className}
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
          {mode === 'interview' && isInterviewLoading && (
            <div className="border-t px-4 py-3 text-xs text-muted-foreground flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Generating the next questions…</span>
            </div>
          )}
          {mode === 'chat' && isChatStreaming && (
            <div className="border-t px-4 py-3 text-xs text-muted-foreground flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Generating code...</span>
            </div>
          )}
          {mode === 'chat' && uiBuildPlan && (
            <div className="border-t p-4">
              <BuildPlanCard
                plan={uiBuildPlan}
                onGenerate={handleGeneratePlan}
                onEdit={handleEditPlan}
                isGenerating={isChatStreaming}
              />
            </div>
          )}
          <InputBar
            onSend={handleSend}
            onAbort={abortBuild}
            isBuilding={isBuilding}
            disabled={disabledInput}
          />
        </PanelContent>
      </Panel>
    </ResizablePanel>
  )
}
