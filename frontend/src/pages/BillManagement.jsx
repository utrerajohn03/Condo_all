import { useState } from 'react'
import Layout from '../components/Layout'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { useAuth } from '../AuthContext'
import { useUnits } from '../hooks/useUnits'
import { useBills, useCreateBill, useUpdateBill } from '../hooks/useBills'
import { usePayments } from '../hooks/usePayments'

const BILL_STATUS_TONE = {
  pending: 'amber',
  partially_paid: 'blue',
  paid: 'emerald',
  overdue: 'rose',
  void: 'muted',
}

const TABS = [
  { key: 'all', label: 'All Bills' },
  { key: 'pending', label: 'Pending' },
  { key: 'partially_paid', label: 'Partially Paid' },
  { key: 'paid', label: 'Paid' },
  { key: 'overdue', label: 'Overdue' },
]

function money(v) {
  return `₱${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const emptyForm = {
  unit_id: '', bill_type: 'association_dues', description: '', amount: '',
  billing_cycle: 'monthly', due_date: '',
}

export default function BillManagement() {
  const { role } = useAuth()
  const canManage = role === 'manager' || role === 'admin'

  const [tab, setTab] = useState('all')
  const { data: bills = [], isLoading } = useBills(tab === 'all' ? {} : { status: tab })
  const { data: payments = [] } = usePayments()
  const { data: units = [] } = useUnits()
  const createBill = useCreateBill()
  const updateBill = useUpdateBill()

  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [voidTarget, setVoidTarget] = useState(null)
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  const totalOutstanding = bills
    .filter((b) => ['pending', 'partially_paid', 'overdue'].includes(b.status))
    .reduce((sum, b) => sum + (Number(b.amount) - Number(b.amount_paid)), 0)
  const totalCollected = payments.reduce((sum, p) => sum + Number(p.amount), 0)
  const overdueCount = bills.filter((b) => b.status === 'overdue').length

  async function handleCreate(e) {
    e.preventDefault()
    try {
      await createBill.mutateAsync({ ...form, amount: parseFloat(form.amount) })
      showToast('Bill created.')
      setShowCreate(false)
      setForm(emptyForm)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create bill.', 'error')
    }
  }

  async function handleVoid() {
    try {
      await updateBill.mutateAsync({ id: voidTarget.id, status: 'void' })
      showToast('Bill voided.')
      setVoidTarget(null)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to void bill.', 'error')
    }
  }

  return (
    <Layout title="Bill Management">
      {toast && (
        <div className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>
          {toast.message}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Outstanding', value: money(totalOutstanding), icon: 'bi-hourglass-split', color: 'bg-amber-50 text-amber-600' },
          { label: 'Total Collected', value: money(totalCollected), icon: 'bi-cash-coin', color: 'bg-emerald-50 text-emerald-600' },
          { label: 'Overdue Bills', value: overdueCount, icon: 'bi-exclamation-triangle', color: 'bg-rose-50 text-rose-600' },
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

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h2 className="font-semibold text-ink">Bills</h2>
            <p className="text-xs text-gray-500">Association dues, utilities, and one-time or recurring charges, org-wide</p>
          </div>
          {canManage && (
            <Button onClick={() => setShowCreate(true)}>
              <i className="bi bi-plus-lg"></i> New Bill
            </Button>
          )}
        </div>

        <div className="flex items-center gap-1 px-4 pt-3">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                tab === t.key ? 'bg-gray-100 text-ink' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <table className="w-full text-sm mt-2">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Description</th>
              <th className="px-4 py-3 font-medium">Cycle</th>
              <th className="px-4 py-3 font-medium">Due Date</th>
              <th className="px-4 py-3 font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canManage && <th className="px-4 py-3 font-medium text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!isLoading && bills.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No bills match this view.</td></tr>
            )}
            {!isLoading && bills.map((b) => (
              <tr key={b.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">{b.unit_number}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{b.bill_type.replace('_', ' ')}</td>
                <td className="px-4 py-3 text-gray-600">{b.description}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{b.billing_cycle.replace('_', ' ')}</td>
                <td className="px-4 py-3 text-gray-600">{b.due_date}</td>
                <td className="px-4 py-3 text-gray-600">{money(b.amount)}</td>
                <td className="px-4 py-3"><Badge tone={BILL_STATUS_TONE[b.status] || 'neutral'}>{b.status.replace('_', ' ')}</Badge></td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    {b.status !== 'void' && b.status !== 'paid' && (
                      <button onClick={() => setVoidTarget(b)} className="text-danger hover:underline text-xs font-medium">
                        Void
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showCreate && canManage && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-ink">New Bill</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400"><i className="bi bi-x-lg"></i></button>
            </div>
            <form onSubmit={handleCreate} className="p-4 space-y-3">
              <select required value={form.unit_id} onChange={(e) => setForm({ ...form, unit_id: e.target.value })} className="input">
                <option value="" disabled>Select unit…</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>{u.building ? `${u.building} — ` : ''}{u.unit_number}</option>
                ))}
              </select>
              <select value={form.bill_type} onChange={(e) => setForm({ ...form, bill_type: e.target.value })} className="input">
                <option value="association_dues">Association Dues</option>
                <option value="utility">Utility</option>
                <option value="other">Other</option>
              </select>
              <input required placeholder="Description" value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })} className="input" />
              <input required type="number" step="0.01" min="0.01" placeholder="Amount" value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })} className="input" />
              <select value={form.billing_cycle} onChange={(e) => setForm({ ...form, billing_cycle: e.target.value })} className="input">
                <option value="one_time">One-Time</option>
                <option value="monthly">Monthly (Recurring)</option>
                <option value="quarterly">Quarterly (Recurring)</option>
                <option value="annual">Annual (Recurring)</option>
              </select>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Due Date</label>
                <input required type="date" value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="input" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={createBill.isPending}>
                  {createBill.isPending ? 'Saving…' : 'Create Bill'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {voidTarget && canManage && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm p-4">
            <h3 className="font-semibold text-ink mb-2">Void this bill?</h3>
            <p className="text-sm text-gray-600 mb-4">
              {voidTarget.description} — {money(voidTarget.amount)} for unit {voidTarget.unit_number}.
              This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setVoidTarget(null)}>Cancel</Button>
              <Button variant="delete" onClick={handleVoid} disabled={updateBill.isPending}>
                {updateBill.isPending ? 'Voiding…' : 'Void Bill'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
