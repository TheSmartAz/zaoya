import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/stores'

interface HeaderProps {
  projectName?: string
  className?: string
  showActions?: boolean
  actions?: ReactNode
}

export function Header({
  projectName = 'Untitled',
  className,
  showActions = true,
  actions,
}: HeaderProps) {
  const navigate = useNavigate()
  const params = useParams()
  const { projects, loadProjects } = useProjectStore()
  const [showProjectDropdown, setShowProjectDropdown] = useState(false)

  useEffect(() => {
    void loadProjects().catch((error) => {
      console.error('Failed to load projects:', error)
    })
  }, [loadProjects])

  const actionContent =
    actions ??
    (showActions ? (
      <>
        <Button variant="outline" size="sm">
          Preview
        </Button>
        <Button size="sm">Publish</Button>
      </>
    ) : null)

  const handleSwitchProject = (projectId: string) => {
    setShowProjectDropdown(false)
    navigate(`/editor/${projectId}`)
  }

  const handleCreateNewProject = () => {
    setShowProjectDropdown(false)
    navigate('/')
  }

  return (
    <header
      className={cn(
        'h-12 border-b bg-background flex items-center justify-between px-4',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="font-semibold text-lg hover:opacity-70 transition-opacity"
        >
          Zaoya
        </button>
        <span className="text-muted-foreground">/</span>
        <div className="relative">
          <button
            onClick={() => setShowProjectDropdown(!showProjectDropdown)}
            className="flex items-center gap-1 px-2 py-1 text-sm bg-muted hover:bg-muted/80 rounded transition-colors"
          >
            <span className="max-w-[200px] truncate">{projectName}</span>
            <svg
              className={`w-4 h-4 transition-transform ${showProjectDropdown ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showProjectDropdown && (
            <div className="absolute top-full left-0 mt-1 w-56 bg-white border rounded-lg shadow-lg z-50">
              <div className="p-2 border-b">
                <button
                  onClick={handleCreateNewProject}
                  className="w-full text-left px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
                >
                  + Create New Project
                </button>
              </div>
              <div className="max-h-60 overflow-y-auto">
                {projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => handleSwitchProject(project.id)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 truncate ${
                      project.id === params.projectId ? 'bg-blue-50 text-blue-700' : ''
                    }`}
                  >
                    {project.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      {actionContent && <div className="flex items-center gap-2">{actionContent}</div>}
    </header>
  )
}
