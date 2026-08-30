import Badge from './ui/Badge'

const STATUS_TONE = {
  submitted: 'neutral',
  assigned: 'blue',
  in_progress: 'amber',
  completed: 'emerald',
  cancelled: 'muted',
  rejected: 'rose',
}

const STATUS_LABELS = {
  submitted: 'Submitted',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rejected: 'Rejected',
}

export default function StatusBadge({ status }) {
  return (
    <Badge tone={STATUS_TONE[status] || 'neutral'}>
      {STATUS_LABELS[status] || status}
    </Badge>
  )
}

// Exported for reuse by pages that need the raw label/tone lookup (e.g. chart legends).
export { STATUS_TONE, STATUS_LABELS }
