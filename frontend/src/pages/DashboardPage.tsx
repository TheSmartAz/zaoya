import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '@/stores/projectStore'
import type { Project } from '@/types/project'
import { ProjectActions } from '@/components/project/ProjectActions'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function DashboardPage() {
  const navigate = useNavigate()
  const { projects, loadProjects, createProject, loadProject } = useProjectStore()
  const [newProjectName, setNewProjectName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    void loadProjects().catch((error) => {
      console.error('Failed to load projects:', error)
    })
  }, [loadProjects])

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || isCreating) return

    setIsCreating(true)
    try {
      const project = await createProject(newProjectName.trim())
      await loadProject(project.id)
      await fetch(`${API_BASE_URL}/api/projects/${project.id}/pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Home', path: '/', is_home: true }),
      })
      await loadProjects()
      navigate(`/editor/${project.id}`)
    } catch (error) {
      console.error('Failed to create project:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleEnterProject = (project: Project) => {
    navigate(`/editor/${project.id}`)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Zaoya</h1>
          <button className="text-sm text-gray-600 hover:text-gray-900">
            Settings
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <section className="mb-12">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Create a New Project
          </h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
              placeholder="Describe what you want to build..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isCreating}
            />
            <button
              onClick={handleCreateProject}
              disabled={!newProjectName.trim() || isCreating}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCreating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Your Projects ({projects.length})
          </h2>

          {projects.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No projects yet. Create your first one above!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <div
                  key={project.id}
                  className="bg-white p-6 rounded-lg border hover:shadow-md hover:border-blue-300 transition-all relative group"
                >
                  <div onClick={() => handleEnterProject(project)} className="cursor-pointer">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {project.name}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          project.status === 'published'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {project.status}
                      </span>
                      <span>•</span>
                      <span>
                        {project.updated_at
                          ? new Date(project.updated_at).toLocaleDateString()
                          : '—'}
                      </span>
                    </div>
                  </div>
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ProjectActions project={project} onImportComplete={loadProjects} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
