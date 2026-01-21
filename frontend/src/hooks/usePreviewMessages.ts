import { useEffect } from 'react'

export function usePreviewMessages() {
  useEffect(() => {
    const containerId = 'zaoya-toast-container'

    const getContainer = () => {
      let container = document.getElementById(containerId)
      if (!container) {
        container = document.createElement('div')
        container.id = containerId
        container.style.position = 'fixed'
        container.style.left = '50%'
        container.style.bottom = '24px'
        container.style.transform = 'translateX(-50%)'
        container.style.display = 'flex'
        container.style.flexDirection = 'column'
        container.style.gap = '8px'
        container.style.zIndex = '9999'
        document.body.appendChild(container)
      }
      return container
    }

    const resolveToastType = (value: unknown): 'info' | 'success' | 'error' => {
      if (value === 'success' || value === 'error') return value
      return 'info'
    }

    const showToast = (message: string, toastType: 'info' | 'success' | 'error' = 'info') => {
      const container = getContainer()
      const toast = document.createElement('div')
      const background = toastType === 'success'
        ? '#10b981'
        : toastType === 'error'
          ? '#ef4444'
          : '#111827'

      toast.textContent = message
      toast.style.background = background
      toast.style.color = '#ffffff'
      toast.style.padding = '10px 16px'
      toast.style.borderRadius = '10px'
      toast.style.fontSize = '14px'
      toast.style.fontFamily = 'system-ui, -apple-system, Segoe UI, sans-serif'
      toast.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.15)'
      toast.style.opacity = '0'
      toast.style.transform = 'translateY(6px)'
      toast.style.transition = 'opacity 0.2s ease, transform 0.2s ease'

      container.appendChild(toast)

      requestAnimationFrame(() => {
        toast.style.opacity = '1'
        toast.style.transform = 'translateY(0)'
      })

      setTimeout(() => {
        toast.style.opacity = '0'
        toast.style.transform = 'translateY(6px)'
        setTimeout(() => toast.remove(), 200)
      }, 2800)
    }

    const handler = (event: MessageEvent) => {
      // Only accept messages from same-origin (our iframe)
      // Note: Since iframe is sandboxed without allow-same-origin,
      // origin will be "null" - we still accept it

      const data = event.data
      if (!data || typeof data !== 'object') return

      switch (data.type) {
        case 'ZAOYA_READY':
          console.log('Zaoya runtime ready')
          break

        case 'ZAOYA_FORM_SUBMIT':
          console.log('Form submitted:', data.data)
          // TODO: Handle form submission
          break

        case 'ZAOYA_TRACK':
          console.log('Track event:', data.event, data.data)
          // TODO: Handle analytics tracking
          break

        case 'ZAOYA_TOAST':
          showToast(data.message, resolveToastType(data.toastType))
          break

        case 'ZAOYA_NAVIGATE':
          console.log('Navigate to:', data.path)
          // TODO: Handle navigation
          break
      }
    }

    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])
}
