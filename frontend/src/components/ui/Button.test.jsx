import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Button from './Button'

describe('Button (cva)', () => {
  it('defaults to the primary variant and default size', () => {
    render(<Button>Save</Button>)
    const btn = screen.getByRole('button', { name: 'Save' })
    expect(btn.className).toContain('bg-primary')
    expect(btn.className).toContain('h-9')
  })

  it('applies the delete variant classes', () => {
    render(<Button variant="delete">Delete</Button>)
    const btn = screen.getByRole('button', { name: 'Delete' })
    expect(btn.className).toContain('bg-danger')
  })

  it('applies the small size classes', () => {
    render(<Button size="sm">Small</Button>)
    const btn = screen.getByRole('button', { name: 'Small' })
    expect(btn.className).toContain('h-8')
  })

  it('merges a caller-supplied className without dropping variant classes', () => {
    render(<Button className="w-full">Full width</Button>)
    const btn = screen.getByRole('button', { name: 'Full width' })
    expect(btn.className).toContain('w-full')
    expect(btn.className).toContain('bg-primary')
  })
})
