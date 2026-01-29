import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { DashboardPage } from '@/pages/DashboardPage'
import { EditorPage } from '@/pages/EditorPage'
import { MockProjectPage } from '@/pages/MockProjectPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { useSettingsStore } from '@/stores'

export default function App() {
  const loadSettings = useSettingsStore((state) => state.loadSettings)

  useEffect(() => {
    void loadSettings()
  }, [loadSettings])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/editor/:projectId" element={<EditorPage />} />
        <Route path="/editor/:projectId/mock-project-page" element={<MockProjectPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
