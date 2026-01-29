import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { TaskItem } from '../TaskItem'

describe('TaskItem', () => {
  it('renders running state with spinner and ellipsis', () => {
    const { container } = render(<TaskItem title="Building" status="running" />)

    expect(screen.getByText('Building...')).toBeInTheDocument()
    expect(container.querySelector('.animate-spin')).toBeTruthy()
  })

  it('renders done state with title only', () => {
    render(<TaskItem title="Planning" status="done" />)

    expect(screen.getByText('Planning')).toBeInTheDocument()
  })

  it('renders failed state with retry button', () => {
    const onRetry = vi.fn()
    render(<TaskItem title="Compile" status="failed" onRetry={onRetry} />)

    const retryButton = screen.getByRole('button', { name: /retry/i })
    fireEvent.click(retryButton)

    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
