import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { ArrowUp } from 'lucide-react'

interface InputBarProps {
  onSend: (message: string) => void
  onAbort: () => void
  isBuilding: boolean
  disabled?: boolean
  className?: string
}

export function InputBar({ onSend, onAbort, isBuilding, disabled, className }: InputBarProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const inputDisabled = disabled || isBuilding

  const handleSubmit = () => {
    if (value.trim() && !inputDisabled) {
      onSend(value.trim())
      setValue('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isBuilding) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [value])

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ message?: string; autoSend?: boolean }>).detail
      if (!detail?.message) return
      if (detail.autoSend && !inputDisabled) {
        onSend(detail.message)
        setValue('')
        return
      }
      setValue(detail.message)
    }
    window.addEventListener('chat-input', handler as EventListener)
    return () => window.removeEventListener('chat-input', handler as EventListener)
  }, [inputDisabled, onSend])

  return (
    <div className={cn('border-t p-4', className)}>
      <div className="relative flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to create..."
          disabled={inputDisabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        />
        {isBuilding ? (
          <Button
            onClick={onAbort}
            disabled={disabled}
            className="h-10 shrink-0 bg-red-500 px-4 text-white hover:bg-red-600"
          >
            ■ Abort
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={handleSubmit}
            disabled={!value.trim() || disabled}
            className="h-10 w-10 shrink-0"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
