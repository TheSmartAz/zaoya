import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'
import { ResizableHandle } from '@/components/ui/resizable'

// Mock data types
interface MockMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

interface MockProject {
  id: string
  name: string
  status: 'draft' | 'published'
  created_at: string
  updated_at: string
}

interface MockPage {
  id: string
  name: string
  path: string
  is_home: boolean
  content?: {
    html?: string
    js?: string
  }
}

// Mock API service
const mockApi = {
  // Mock project data
  getProject: async (projectId: string): Promise<MockProject> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          id: projectId,
          name: 'Mock Project: Portfolio Website',
          status: 'draft',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      }, 100)
    })
  },

  // Mock pages data
  getPages: async (projectId: string): Promise<MockPage[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: 'page-1',
            name: 'Home',
            path: '/',
            is_home: true,
            content: {
              html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portfolio</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">John Doe</h1>
      <p class="text-xl text-gray-600 mb-8">Software Engineer</p>
      <div class="flex gap-4 justify-center">
        <a href="#" class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Contact</a>
        <a href="#" class="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-100">Projects</a>
      </div>
    </div>
  </div>
</body>
</html>`,
            },
          },
          {
            id: 'page-2',
            name: 'About',
            path: '/about',
            is_home: false,
            content: {
              html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About - Portfolio</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
  <div class="max-w-4xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-6">About Me</h1>
    <p class="text-gray-700 leading-relaxed">
      I'm a software engineer with 5+ years of experience in web development.
      I love building beautiful, functional applications that solve real problems.
    </p>
  </div>
</body>
</html>`,
            },
          },
        ])
      }, 150)
    })
  },

  // Mock interview stream
  streamInterview: async function* (
    projectId: string,
    payload: { action: string; content?: string; answers?: any[] }
  ) {
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

    // Simulate AI thinking
    await delay(500)

    if (payload.action === 'start' || payload.action === 'generate_now') {
      // Mock interview questions
      const mockQuestions = [
        {
          type: 'ask_group',
          group: {
            id: 'group-1',
            topic: 'project_type',
            topic_label: 'Project Type',
            questions: [
              {
                id: 'q-1',
                text: 'What type of page do you want to create?',
                type: 'single_select',
                options: [
                  { value: 'portfolio', label: 'Portfolio' },
                  { value: 'landing', label: 'Landing Page' },
                  { value: 'blog', label: 'Blog' },
                  { value: 'other', label: 'Other' },
                ],
              },
            ],
            is_completed: false,
          },
        },
      ]

      for (const question of mockQuestions) {
        yield question
        await delay(800)
      }
    } else if (payload.action === 'answer') {
      // Mock finish after answer
      await delay(1000)

      yield {
        type: 'finish',
        plan: {
          pages: [
            { id: 'page-1', name: 'Home', path: '/', is_home: true },
            { id: 'page-2', name: 'About', path: '/about', is_home: false },
          ],
          design_system: {
            style: 'Modern',
            theme: 'Light',
            colors: {
              primary: '#3B82F6',
            },
            color_palette: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
          },
          features: ['Responsive Design', 'Contact Form', 'Portfolio Gallery'],
        },
        product_document: {
          project_name: 'My Portfolio',
          overview: 'A personal portfolio website showcasing projects and skills',
        },
      }
    }
  },

  // Mock chat stream
  streamChat: async function* (messages: MockMessage[]) {
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

    const lastUserMessage = messages.filter(m => m.role === 'user').pop()
    if (!lastUserMessage) {
      yield "I'm ready to help! What would you like to create?"
      return
    }

    // Simulate AI response
    const response = `Great! I'll help you create a ${lastUserMessage.content}.

I've designed a modern, responsive layout with:
- Clean typography
- Mobile-first design
- Smooth animations

The preview is now available on the right side. What would you like to change?`

    for (const char of response) {
      yield char
      await delay(20)
    }
  },
}

export function MockProjectPage() {
  const params = useParams()
  const projectId = params.projectId || 'mock-project'

  const [project, setProject] = useState<MockProject | null>(null)
  const [pages, setPages] = useState<MockPage[]>([])
  const [currentPageId, setCurrentPageId] = useState<string>('')
  const [messages, setMessages] = useState<MockMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [interviewMode, setInterviewMode] = useState<'idle' | 'interview' | 'chat'>('idle')
  const [currentQuestion, setCurrentQuestion] = useState<any>(null)
  const [collapsedAnswers, setCollapsedAnswers] = useState<Array<{ questionText: string; answer: string }>>([])

  // Load mock data
  useEffect(() => {
    const loadData = async () => {
      const [projectData, pagesData] = await Promise.all([
        mockApi.getProject(projectId),
        mockApi.getPages(projectId),
      ])
      setProject(projectData)
      setPages(pagesData)
      if (pagesData.length > 0) {
        setCurrentPageId(pagesData[0].id)
      }
    }
    loadData()
  }, [projectId])

  const handleSend = async (content: string) => {
    const userMessage: MockMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    }

    setMessages(prev => [...prev, userMessage])

    if (interviewMode === 'idle') {
      // Start interview
      setInterviewMode('interview')
      setIsStreaming(true)

      try {
        for await (const response of mockApi.streamInterview(projectId, { action: 'start', content })) {
          if (response.type === 'ask_group') {
            setCurrentQuestion(response.group.questions[0])
          }
        }
      } finally {
        setIsStreaming(false)
      }
    } else if (interviewMode === 'interview') {
      // Handle interview answer
      setIsStreaming(true)

      try {
        for await (const response of mockApi.streamInterview(projectId, { action: 'answer', answers: [{ question_id: currentQuestion.id, raw_text: content }] })) {
          if (response.type === 'finish') {
            setInterviewMode('chat')
            setCurrentQuestion(null)

            // Add collapsed answer
            setCollapsedAnswers(prev => [...prev, {
              questionText: currentQuestion.text,
              answer: content,
            }])
          } else if (response.type === 'ask_group') {
            setCurrentQuestion(response.group.questions[0])
          }
        }
      } finally {
        setIsStreaming(false)
      }
    } else if (interviewMode === 'chat') {
      // Chat mode
      setIsStreaming(true)

      const assistantMessage: MockMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }

      setMessages(prev => [...prev, assistantMessage])

      try {
        let fullContent = ''
        for await (const chunk of mockApi.streamChat([...messages, userMessage])) {
          fullContent += chunk
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessage.id ? { ...msg, content: fullContent } : msg
          ))
        }
      } finally {
        setIsStreaming(false)
      }
    }
  }

  const handleAnswer = async (value: any) => {
    handleSend(value)
  }

  const handleSkip = async () => {
    handleSend('Skipped')
  }

  const currentPage = pages.find(p => p.id === currentPageId) || pages[0]

  return (
    <EditorLayout projectName={project?.name}>
      <ChatPanel />
      <ResizableHandle withHandle panelIds={['chat-panel', 'preview-panel']} />
      <PreviewPanel page={currentPage} projectId={projectId} />

      {/* Mock Controls Panel */}
      <div className="fixed bottom-4 right-4 z-50 bg-white p-4 rounded-lg shadow-lg border max-w-sm">
        <h3 className="font-semibold mb-2">Mock Controls</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="font-medium">Mode:</span>
            <span className="px-2 py-1 bg-gray-100 rounded">{interviewMode}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium">Pages:</span>
            <span className="px-2 py-1 bg-blue-100 rounded text-blue-800">{pages.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium">Messages:</span>
            <span className="px-2 py-1 bg-green-100 rounded text-green-800">{messages.length}</span>
          </div>
          {currentQuestion && (
            <div className="mt-2 p-2 bg-yellow-50 rounded border border-yellow-200">
              <div className="font-medium text-yellow-900">Current Question:</div>
              <div className="text-yellow-800">{currentQuestion.text}</div>
            </div>
          )}
          <button
            onClick={() => {
              setInterviewMode('idle')
              setMessages([])
              setCurrentQuestion(null)
              setCollapsedAnswers([])
            }}
            className="w-full px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded"
          >
            Reset Interview
          </button>
        </div>
      </div>
    </EditorLayout>
  )
}
