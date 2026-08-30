import { useState } from 'react'
import Layout from '../components/Layout'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { useAuth } from '../AuthContext'
import { useUnitResidents, useCreateAssignment, useEndAssignment } from '../hooks/useUnitResidents'
import { useUnits } from '../hooks/useUnits'
import { useUsers } from '../hooks/useUsers'

const TABS = [
  { key: 'all', label: 'All Assignments' },
  { key: 'permanent', label: 'Permanent' },
  { key: 'temporary', label: 'Temporary' },
  { key: 'history', label: 'History' },
]

const RELATIONSHIP_TONE = { owner: 'emerald', tenant: 'blue', co_resident: 'amber' }

export default function ResidentAssignments() {
  const { role } = useAuth()
  const canManage = role === 'manager' || role === 'admin'

  const { data: assignments = [], isLoading } = useUnitResidents()
  const { data: units = [] } = useUnits()
  // Assignments link a unit to either a Resident (tenant) OR a Unit Owner account —
  // both are valid targets here (relationship_type is what says which), so fetch the
  // full user list and filter client-side rather than a single-role server filter.
  const { data: allUsers = [] } = useUsers()
  const residents = allUsers.filter((u) => u.role === 'resident' || u.role === 'unit_owner')
  const createAssignment = useCreateAssignment()
  const endAssignment = useEndAssignment()

  const [tab, setTab] = useState('all')
  const [search, setSearch] = useState('')
  const [toast, setToast] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ unit_id: '', user_id: '', relationship_type: 'tenant', is_primary_contact: false })

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  const tabbed = assignments.filter((a) => {
    if (tab === 'permanent') return a.relationship_type === 'owner' && !a.moved_out_at
    if (tab === 'temporary') return a.relationship_type !== 'owner' && !a.moved_out_at
    if (tab === 'history') return !!a.moved_out_at
    return true
  })
  const filtered = tabbed.filter((a) =>
    !search ||
    a.resident_name.toLowerCase().includes(search.toLowerCase()) ||
    a.unit_number.includes(search)
  )

  const counts = {
    total: assignments.filter((a) => !a.moved_out_at).length,
    pending: assignments.filter((a) => !a.moved_out_at && new Date(a.moved_in_at) > new Date()).length,
    recentMoveOuts: assignments.filter((a) => a.moved_out_at && (Date.now() - new Date(a.moved_out_at)) < 30 * 86400000).length,
    history: assignments.length,
  }

  async function handleCreate(e) {
    e.preventDefault()
    try {
      await createAssignment.mutateAsync(form)
      showToast('Resident assigned to unit.')
      setShowCreate(false)
      setForm({ unit_id: '', user_id: '', relationship_type: 'tenant', is_primary_contact: false })
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create assignment.', 'error')
    }
  }

  async function handleEnd(a) {
    if (!confirm(`End ${a.resident_name}'s assignment to unit ${a.unit_number}?`)) return
    try {
      await endAssignment.mutateAsync(a.id)
      showToast('Assignment ended.')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to end assignment.', 'error')
    }
  }

  return (
    <Layout title="Resident Assignments">
      {toast && (
        <div className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>
          {toast.message}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Assignments', value: counts.total, icon: 'bi-people-fill', color: 'bg-emerald-50 text-emerald-600' },
          { label: 'Pending Move-Ins', value: counts.pending, icon: 'bi-box-arrow-in-right', color: 'bg-amber-50 text-amber-600' },
          { label: 'Recent Move-Outs', value: counts.recentMoveOuts, icon: 'bi-box-arrow-right', color: 'bg-blue-50 text-blue-600' },
          { label: 'Total History', value: counts.history, icon: 'bi-clock-history', color: 'bg-purple-50', style: { color: '#7c3aed' } },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${kpi.color}`} style={kpi.style}>
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
            <h2 className="font-semibold text-ink">Resident-Unit Assignments</h2>
            <p className="text-xs text-gray-500">
              {canManage ? 'Manage which residents are linked to which unit' : 'View resident-to-unit assignments'}
            </p>
          </div>
          {canManage && (
            <Button onClick={() => setShowCreate(true)}>
              <i className="bi bi-plus-lg"></i> Assign Resident
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

        <div className="flex items-center gap-3 p-4 border-b border-gray-100">
          <div className="relative flex-1 max-w-xs">
            <i className="bi bi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search resident or unit..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Resident</th>
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Relationship</th>
              <th className="px-4 py-3 font-medium">Date / Duration</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canManage && <th className="px-4 py-3 font-medium text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!isLoading && filtered.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No assignments match this view.</td></tr>
            )}
            {!isLoading && filtered.map((a) => (
              <tr key={a.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">
                  {a.resident_name}
                  {a.is_primary_contact && <span className="ml-1.5 text-[10px] text-primary">★ primary</span>}
                </td>
                <td className="px-4 py-3 text-gray-600">Unit {a.unit_number}</td>
                <td className="px-4 py-3"><Badge tone={RELATIONSHIP_TONE[a.relationship_type]}>{a.relationship_type.replace('_', ' ')}</Badge></td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(a.moved_in_at).toLocaleDateString()}
                  {a.moved_out_at ? ` → ${new Date(a.moved_out_at).toLocaleDateString()}` : ' → present'}
                </td>
                <td className="px-4 py-3">
                  <Badge tone={a.moved_out_at ? 'muted' : 'emerald'}>{a.moved_out_at ? 'Ended' : 'Active'}</Badge>
                </td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    {!a.moved_out_at && (
                      <button onClick={() => handleEnd(a)} className="text-danger hover:underline text-xs font-medium">
                        End Assignment
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
          <span>Showing {filtered.length} of {assignments.length}</span>
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-ink">Assign Resident</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400"><i className="bi bi-x-lg"></i></button>
            </div>
            <form onSubmit={handleCreate} className="p-4 space-y-3">
              <select required value={form.unit_id} onChange={(e) => setForm({ ...form, unit_id: e.target.value })} className="input">
                <option value="">Select a unit</option>
                {units.map((u) => <option key={u.id} value={u.id}>{u.building} - {u.unit_number}</option>)}
              </select>
              <select required value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} className="input">
                <option value="">Select a resident or unit owner</option>
                {residents.map((r) => <option key={r.id} value={r.id}>{r.full_name} ({r.email} — {r.role.replace('_', ' ')})</option>)}
              </select>
              <select value={form.relationship_type} onChange={(e) => setForm({ ...form, relationship_type: e.target.value })} className="input">
                <option value="owner">Owner</option>
                <option value="tenant">Tenant</option>
                <option value="co_resident">Co-Resident</option>
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input type="checkbox" checked={form.is_primary_contact}
                  onChange={(e) => setForm({ ...form, is_primary_contact: e.target.checked })} />
                Primary contact for this unit
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={createAssignment.isPending}>
                  {createAssignment.isPending ? 'Saving…' : 'Assign'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
