import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('cn()', () => {
  it('joins plain class strings', () => {
    expect(cn('px-2', 'py-1')).toBe('px-2 py-1')
  })

  it('drops falsy conditional classes', () => {
    expect(cn('px-2', false && 'hidden', null, undefined, 'py-1')).toBe('px-2 py-1')
  })

  it('resolves conflicting Tailwind utilities, keeping the last one', () => {
    // tailwind-merge should collapse these to a single bg-* class
    expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500')
  })

  it('does not collapse non-conflicting utilities', () => {
    expect(cn('rounded-md', 'text-sm', 'font-medium')).toBe('rounded-md text-sm font-medium')
  })
})
