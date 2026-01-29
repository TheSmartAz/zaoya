import { useEffect, useState } from 'react'
import type { BuildPlan } from '@/types/buildPlan'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useBuildPlan(buildId: string | null) {
  const [plan, setPlan] = useState<BuildPlan | null>(null)

  useEffect(() => {
    if (!buildId) {
      setPlan(null)
      return
    }

    fetch(`${API_BASE_URL}/api/build/${buildId}/plan`)
      .then((res) => res.json())
      .then((data) => setPlan(data as BuildPlan))
      .catch(console.error)

    const handleUpdate = (event: CustomEvent<Partial<BuildPlan>>) => {
      if ((event.detail as BuildPlan).id === buildId) {
        setPlan((prev) => (prev ? { ...prev, ...event.detail } : prev))
      }
    }

    window.addEventListener('build-plan-update', handleUpdate as EventListener)

    return () => {
      window.removeEventListener('build-plan-update', handleUpdate as EventListener)
    }
  }, [buildId])

  return plan
}
