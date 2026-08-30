import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merges conditional class names (clsx) and resolves conflicting Tailwind
 * utility classes (tailwind-merge) — the standard shadcn-style helper that
 * backs every cva-based component in this module.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}
