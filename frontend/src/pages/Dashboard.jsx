import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import Layout from '../components/Layout'
import Badge from '../components/ui/Badge'
import { useAuth } from '../AuthContext'
import { useMaintenanceRequests } from '../hooks/useMaintenanceRequests'
import { useUnits, useMyUnits } from '../hooks/useUnits'
import { STATUS_LABELS } from '../components/StatusBadge'

// Chart segment colors pulled from the Argo UI reference semantic palette —
// same tokens used by StatusBadge, kept in sync manually since recharts needs
// literal hex values rather than Tailwind classes.
const STATUS_CHART_COLOR = {
  submitted: '#6B7280',
  assigned: '#2563EB',
  in_progress: '#D97706',
  completed: '#059669',
  cancelled: '#9CA3AF',
  rejected: '#E11D48',
}

export default function Dashboard() {
  const { role } = useAuth()
  const isSelfScoped = role === 'resident' || role === 'unit_owner'
  const { data: requests = [], isLoading: loadingRequests } = useMaintenanceRequests()
  const { data: units = [], isLoading: loadingUnits } = useUnits()
  const { data: myUnits = [] } = useMyUnits()

  const counts = {
    total: requests.length,
    submitted: requests.filter((r) => r.status === 'submitted').length,
    active: requests.filter((r) => ['assigned', 'in_progress'].includes(r.status)).length,
    completed: requests.filter((r) => r.status === 'completed').length,
  }

  const cards = [
    { label: 'Total Requests', value: counts.total, icon: 'bi-tools', color: 'bg-blue-50 text-blue-600' },
    { label: 'New / Submitted', value: counts.submitted, icon: 'bi-inbox', color: 'bg-amber-50 text-amber-600' },
    { label: 'Active (Assigned/In Progress)', value: counts.active, icon: 'bi-activity', color: 'bg-teal-50 text-teal-600' },
    { label: 'Completed', value: counts.completed, icon: 'bi-check2-circle', color: 'bg-emerald-50 text-emerald-600' },
  ]

  // Maintenance Status Breakdown chart data — one segment per lifecycle status,
  // computed from whatever the caller is currently allowed to see (org-wide for
  // staff/manager/admin, own-unit only for residents — the API already scopes this).
  const chartData = Object.keys(STATUS_LABELS)
    .map((status) => ({
      status,
      name: STATUS_LABELS[status],
      value: requests.filter((r) => r.status === status).length,
    }))
    .filter((d) => d.value > 0)

  return (
    <Layout title={`Welcome back${role ? `, ${role.replace('_', ' ')}` : ''}`}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {cards.map((c) => (
          <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${c.color}`}>
              <i className={`bi ${c.icon}`}></i>
            </div>
            <div className="text-2xl font-semibold text-ink">{c.value}</div>
            <div className="text-xs text-gray-500">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <h3 className="font-semibold text-ink mb-3 text-sm">Maintenance Status Breakdown</h3>
          {chartData.length === 0 ? (
            <p className="text-sm text-gray-400 py-10 text-center">No maintenance requests yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                >
                  {chartData.map((entry) => (
                    <Cell key={entry.status} fill={STATUS_CHART_COLOR[entry.status]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={24} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          {isSelfScoped ? (
            <>
              <h3 className="font-semibold text-ink mb-3 text-sm">My Unit{myUnits.length !== 1 ? 's' : ''}</h3>
              {myUnits.length === 0 ? (
                <p className="text-sm text-gray-400 py-10 text-center">No unit is linked to your account yet.</p>
              ) : (
                <div className="space-y-3">
                  {myUnits.map((u) => (
                    <div key={u.id} className="flex items-center justify-between border border-gray-100 rounded-lg p-3">
                      <div>
                        <div className="text-sm font-medium text-ink">Unit {u.unit_number}</div>
                        <div className="text-xs text-gray-500">{u.building}{u.floor != null ? ` · Floor ${u.floor}` : ''}</div>
                      </div>
                      <Badge tone={u.status === 'occupied' ? 'emerald' : u.status === 'vacant' ? 'blue' : 'amber'}>
                        {u.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <>
              <h3 className="font-semibold text-ink mb-3 text-sm">Unit Overview</h3>
              <div className="text-3xl font-semibold text-ink mb-1">{units.length}</div>
              <p className="text-xs text-gray-500 mb-3">Total units on record</p>
              <div className="flex gap-2 flex-wrap">
                {['occupied', 'vacant', 'under_maintenance'].map((s) => (
                  <span key={s} className="text-xs bg-gray-50 border border-gray-200 rounded-full px-2.5 py-1 capitalize">
                    {s.replace('_', ' ')}: {units.filter((u) => u.status === s).length}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {(loadingRequests || loadingUnits) && (
        <p className="text-xs text-gray-400 mt-4">Loading latest data…</p>
      )}
    </Layout>
  )
}
