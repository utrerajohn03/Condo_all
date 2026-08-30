import { useState } from 'react'
import Layout from '../components/Layout'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { useAuth } from '../AuthContext'
import { useMyBills } from '../hooks/useBills'
import { useMyPayments, useCreatePayment } from '../hooks/usePayments'

const BILL_STATUS_TONE = {
  pending: 'amber',
  partially_paid: 'blue',
  paid: 'emerald',
  overdue: 'rose',
  void: 'muted',
}

const BILL_TYPE_LABEL = {
  association_dues: 'Association Dues',
  utility: 'Utility',
  other: 'Other',
}

function money(v) {
  return `₱${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function Payments() {
  const { role } = useAuth()
  const sectionLabel = role === 'unit_owner' ? 'Unit Owner' : 'Tenant'
  const { data: bills = [], isLoading: billsLoading } = useMyBills()
  const { data: payments = [], isLoading: paymentsLoading } = useMyPayments()
  const createPayment = useCreatePayment()

  const [payTarget, setPayTarget] = useState(null)
  const [form, setForm] = useState({ amount: '', method: 'online', reference_number: '' })
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  const outstandingBills = bills.filter((b) => ['pending', 'partially_paid', 'overdue'].includes(b.status))
  const totalDue = outstandingBills.reduce((sum, b) => sum + (Number(b.amount) - Number(b.amount_paid)), 0)
  const overdueCount = bills.filter((b) => b.status === 'overdue').length
  const totalPaid = payments.reduce((sum, p) => sum + Number(p.amount), 0)

  function openPay(bill) {
    setPayTarget(bill)
    setForm({ amount: (Number(bill.amount) - Number(bill.amount_paid)).toFixed(2), method: 'online', reference_number: '' })
  }

  async function handlePay(e) {
    e.preventDefault()
    try {
      await createPayment.mutateAsync({
        bill_id: payTarget.id,
        amount: parseFloat(form.amount),
        method: form.method,
        reference_number: form.reference_number || undefined,
      })
      showToast('Payment recorded.')
      setPayTarget(null)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Payment failed.', 'error')
    }
  }

  return (
    <Layout title="Payments">
      {toast && (
        <div className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>
          {toast.message}
        </div>
      )}

      <p className="text-xs text-gray-500 -mt-3 mb-5">
        {sectionLabel} Payments — bills and payment history for the unit(s) linked to your account.
        No live payment gateway is connected in this build; "Pay Now" records the payment directly.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Total Due', value: money(totalDue), icon: 'bi-wallet2', color: 'bg-blue-50 text-blue-600' },
          { label: 'Overdue Bills', value: overdueCount, icon: 'bi-exclamation-triangle', color: 'bg-rose-50 text-rose-600' },
          { label: 'Total Paid to Date', value: money(totalPaid), icon: 'bi-check-circle', color: 'bg-emerald-50 text-emerald-600' },
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
          <h2 className="font-semibold text-ink">Bills</h2>
          <p className="text-xs text-gray-500">Association dues, utilities, and other charges on your unit(s)</p>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Description</th>
              <th className="px-4 py-3 font-medium">Due Date</th>
              <th className="px-4 py-3 font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {billsLoading && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!billsLoading && bills.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No bills on record.</td></tr>
            )}
            {!billsLoading && bills.map((b) => (
              <tr key={b.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">{b.unit_number}</td>
                <td className="px-4 py-3 text-gray-600">{BILL_TYPE_LABEL[b.bill_type] || b.bill_type}</td>
                <td className="px-4 py-3 text-gray-600">{b.description}</td>
                <td className="px-4 py-3 text-gray-600">{b.due_date}</td>
                <td className="px-4 py-3 text-gray-600">
                  {money(b.amount)}
                  {b.amount_paid > 0 && b.status !== 'paid' && (
                    <span className="text-xs text-gray-400"> ({money(b.amount_paid)} paid)</span>
                  )}
                </td>
                <td className="px-4 py-3"><Badge tone={BILL_STATUS_TONE[b.status] || 'neutral'}>{b.status.replace('_', ' ')}</Badge></td>
                <td className="px-4 py-3 text-right">
                  {['pending', 'partially_paid', 'overdue'].includes(b.status) ? (
                    <Button size="sm" onClick={() => openPay(b)}>Pay Now</Button>
                  ) : (
                    <span className="text-xs text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-ink">Payment History</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Method</th>
              <th className="px-4 py-3 font-medium">Reference</th>
              <th className="px-4 py-3 font-medium">Paid At</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {paymentsLoading && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!paymentsLoading && payments.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No payments yet.</td></tr>
            )}
            {!paymentsLoading && payments.map((p) => (
              <tr key={p.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">{p.unit_number}</td>
                <td className="px-4 py-3 text-gray-600">{money(p.amount)}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{p.method.replace('_', ' ')}</td>
                <td className="px-4 py-3 text-gray-600">{p.reference_number || '—'}</td>
                <td className="px-4 py-3 text-gray-600">{new Date(p.paid_at).toLocaleString()}</td>
                <td className="px-4 py-3"><Badge tone="emerald">{p.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {payTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-ink">Pay Bill — {payTarget.unit_number}</h3>
              <button onClick={() => setPayTarget(null)} className="text-gray-400"><i className="bi bi-x-lg"></i></button>
            </div>
            <form onSubmit={handlePay} className="p-4 space-y-3">
              <p className="text-xs text-gray-500">{payTarget.description}</p>
              <input required type="number" step="0.01" min="0.01" placeholder="Amount" value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })} className="input" />
              <select value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })} className="input">
                <option value="online">Online</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="cash">Cash</option>
                <option value="check">Check</option>
              </select>
              <input placeholder="Reference number (optional)" value={form.reference_number}
                onChange={(e) => setForm({ ...form, reference_number: e.target.value })} className="input" />
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setPayTarget(null)}>Cancel</Button>
                <Button type="submit" disabled={createPayment.isPending}>
                  {createPayment.isPending ? 'Processing…' : 'Confirm Payment'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
