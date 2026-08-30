import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusBadge from './StatusBadge'

describe('StatusBadge', () => {
  it('renders the human-readable label for each lifecycle status', () => {
    const cases = [
      ['submitted', 'Submitted'],
      ['assigned', 'Assigned'],
      ['in_progress', 'In Progress'],
      ['completed', 'Completed'],
      ['cancelled', 'Cancelled'],
      ['rejected', 'Rejected'],
    ]
    for (const [status, label] of cases) {
      const { unmount } = render(<StatusBadge status={status} />)
      expect(screen.getByText(label)).toBeInTheDocument()
      unmount()
    }
  })

  it('falls back to the raw value for an unknown status instead of crashing', () => {
    render(<StatusBadge status="some_future_status" />)
    expect(screen.getByText('some_future_status')).toBeInTheDocument()
  })
})
