import * as React from 'react'
import { cn } from '@/lib/utils'

export interface SwitchProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> {
  checked?: boolean
  defaultChecked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  (
    {
      checked,
      defaultChecked,
      onCheckedChange,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    const [internalChecked, setInternalChecked] = React.useState(
      defaultChecked ?? false
    )

    const isControlled = checked !== undefined
    const isChecked = isControlled ? checked : internalChecked

    const toggle = () => {
      if (disabled) return
      const next = !isChecked
      if (!isControlled) {
        setInternalChecked(next)
      }
      onCheckedChange?.(next)
    }

    return (
      <button
        type="button"
        role="switch"
        aria-checked={isChecked}
        data-state={isChecked ? 'checked' : 'unchecked'}
        onClick={toggle}
        disabled={disabled}
        className={cn(
          'inline-flex h-6 w-11 items-center rounded-full border border-transparent transition-colors',
          isChecked ? 'bg-primary' : 'bg-input',
          disabled && 'cursor-not-allowed opacity-50',
          className
        )}
        ref={ref}
        {...props}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-5 w-5 translate-x-0 rounded-full bg-background shadow transition-transform',
            isChecked && 'translate-x-5'
          )}
        />
      </button>
    )
  }
)
Switch.displayName = 'Switch'

export { Switch }
