import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

/**
 * cva-driven Button — variants/sizes match the Argo UI reference "Core components"
 * panel exactly (Primary/Secondary/Outline/Ghost/Delete; Small/Default/Large;
 * rounded-md, h-9, text-sm/500 base).
 */
export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-1.5 rounded-md text-sm font-medium transition disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-white hover:bg-blue-700',
        secondary: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50',
        outline: 'bg-white border border-gray-300 text-ink hover:bg-gray-50',
        ghost: 'text-gray-600 hover:bg-gray-100',
        delete: 'bg-danger text-white hover:bg-rose-700',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        default: 'h-9 px-4',
        lg: 'h-11 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'default',
    },
  }
)

export default function Button({ className, variant, size, ...props }) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
}
