import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import Badge from '../components/ui/Badge'
import { useMyUnits } from '../hooks/useUnits'
import { useMyBills } from '../hooks/useBills'
import { useMyPayments } from '../hooks/usePayments'
import { useUnitResidents } from '../hooks/useUnitResidents'
import { useMaintenanceRequests } from '../hooks/useMaintenanceRequests'

const BILL_STATUS_TONE = {
  pending: 'amber',
  partially_paid: 'blue',
  paid: 'emerald',
  overdue: 'rose',
  void: 'muted',
}

function money(v) {
  return `₱${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function OwnerPortal() {
  const { data: units = [], isLoading: unitsLoading } = useMyUnits()
  const { data: bills = [] } = useMyBills()
  const { data: payments = [] } = useMyPayments()
  const { data: assignments = [] } = useUnitResidents()
  const { data: requests = [] } = useMaintenanceRequests()

  const outstanding = bills.filter((b) => ['pending', 'partially_paid', 'overdue'].includes(b.status))
  const totalDue = outstanding.reduce((sum, b) => sum + (Number(b.amount) - Number(b.amount_paid)), 0)
  const lastPayment = [...payments].sort((a, b) => new Date(b.paid_at) - new Date(a.paid_at))[0]
  const openRequests = requests.filter((r) => !['completed', 'cancelled', 'rejected'].includes(r.status)).length

  const unitIds = new Set(units.map((u) => u.id))
  const tenantsByUnit = assignments.filter((a) => unitIds.has(a.unit_id) && !a.moved_out_at)

  return (
    <Layout title="Owner Portal">
      <p className="text-xs text-gray-500 -mt-3 mb-5">
        Your dedicated view as a Unit Owner — the unit(s) you hold title to, who is currently
        linked to them, and your billing/payment standing at a glance.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Units Owned', value: units.length, icon: 'bi-door-closed', color: 'bg-blue-50 text-blue-600' },
          { label: 'Total Due', value: money(totalDue), icon: 'bi-wallet2', color: 'bg-amber-50 text-amber-600' },
          { label: 'Open Maintenance Requests', value: openRequests, icon: 'bi-tools', color: 'bg-teal-50 text-teal-600' },
          { label: 'Last Payment', value: lastPayment ? money(lastPayment.amount) : '—', icon: 'bi-check-circle', color: 'bg-emerald-50 text-emerald-600' },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${kpi.color}`}>
              <i className={`bi ${kpi.icon}`}></i>
            </div>
            <div className="text-2xl font-semibold text-ink">{kpi.value}</div>
            <div className="text-xs text-gray-500">{kpi.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-ink">My Units</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[560px]">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Building</th>
              <th className="px-4 py-3 font-medium">Floor</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Currently Linked</th>
            </tr>
          </thead>
          <tbody>
            {unitsLoading && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!unitsLoading && units.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No units are linked to your account yet.</td></tr>
            )}
            {!unitsLoading && units.map((u) => {
              const linked = tenantsByUnit.filter((a) => a.unit_id === u.id)
              return (
                <tr key={u.id} className="border-b border-gray-50 align-top">
                  <td className="px-4 py-3 font-medium text-ink">{u.unit_number}</td>
                  <td className="px-4 py-3 text-gray-600">{u.building || '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{u.floor ?? '—'}</td>
                  <td className="px-4 py-3"><Badge tone="blue">{u.status.replace('_', ' ')}</Badge></td>
                  <td className="px-4 py-3 text-gray-600">
                    {linked.length === 0 ? '—' : (
                      <ul className="space-y-1">
                        {linked.map((a) => (
                          <li key={a.id}>
                            {a.resident_name} <span className="text-xs text-gray-400 capitalize">({a.relationship_type.replace('_', ' ')}{a.is_primary_contact ? ', primary' : ''})</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h2 className="font-semibold text-ink">Outstanding Bills</h2>
            <p className="text-xs text-gray-500">Full billing and payment history is on the Payments page</p>
          </div>
          <Link to="/payments" className="text-primary text-xs font-medium hover:underline">Go to Payments →</Link>
        </div>
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[520px]">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Description</th>
              <th className="px-4 py-3 font-medium">Due Date</th>
              <th className="px-4 py-3 font-medium">Amount Due</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {outstanding.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Nothing outstanding — you're all caught up.</td></tr>
            )}
            {outstanding.map((b) => (
              <tr key={b.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">{b.unit_number}</td>
                <td className="px-4 py-3 text-gray-600">{b.description}</td>
                <td className="px-4 py-3 text-gray-600">{b.due_date}</td>
                <td className="px-4 py-3 text-gray-600">{money(Number(b.amount) - Number(b.amount_paid))}</td>
                <td className="px-4 py-3"><Badge tone={BILL_STATUS_TONE[b.status] || 'neutral'}>{b.status.replace('_', ' ')}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </Layout>
  )
}
