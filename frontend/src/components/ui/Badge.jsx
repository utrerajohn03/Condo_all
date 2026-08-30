import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

/**
 * cva-driven status badge — one variant per semantic color from the Argo UI
 * reference token set (rounded-full · border-{c}-200 · bg-{c}-50 · text-{c}-700).
 */
export const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize',
  {
    variants: {
      tone: {
        neutral: 'bg-gray-50 text-gray-700 border-gray-200',
        blue: 'bg-blue-50 text-blue-700 border-blue-200',
        amber: 'bg-amber-50 text-amber-700 border-amber-200',
        emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        rose: 'bg-rose-50 text-rose-700 border-rose-200',
        muted: 'bg-gray-50 text-gray-500 border-gray-200',
      },
    },
    defaultVariants: {
      tone: 'neutral',
    },
  }
)

export default function Badge({ className, tone, dot = true, children, ...props }) {
  return (
    <span className={cn(badgeVariants({ tone }), className)} {...props}>
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}
