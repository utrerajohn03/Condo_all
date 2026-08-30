import { useState } from 'react'
import Layout from '../components/Layout'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { useAuth } from '../AuthContext'
import { useUnits, useCreateUnit, useUpdateUnit } from '../hooks/useUnits'
import { useUnitFilterStore } from '../store/useFilterStore'

const STATUS_TONE = {
  occupied: 'emerald',
  vacant: 'blue',
  under_maintenance: 'amber',
}

const TABS = [
  { key: 'all', label: 'All Units' },
  { key: 'occupied', label: 'Occupied' },
  { key: 'vacant', label: 'Vacant' },
  { key: 'under_maintenance', label: 'Maintenance' },
]

export default function Units() {
  const { role } = useAuth()
  const { data: units = [], isLoading } = useUnits()
  const createUnit = useCreateUnit()
  const updateUnit = useUpdateUnit()

  // zustand — filter/tab client state, kept separate from the react-query server cache.
  const { search, statusTab, setSearch, setStatusTab } = useUnitFilterStore()

  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ unit_number: '', building: '', floor: '', status: 'vacant' })
  const [editTarget, setEditTarget] = useState(null)
  const [editForm, setEditForm] = useState({ unit_number: '', building: '', floor: '', status: 'vacant' })
  const [toast, setToast] = useState(null)

  const canManage = role === 'manager' || role === 'admin'

  const filtered = units.filter((u) => {
    const matchesTab = statusTab === 'all' || u.status === statusTab
    const matchesSearch =
      !search ||
      u.unit_number.toLowerCase().includes(search.toLowerCase()) ||
      (u.building || '').toLowerCase().includes(search.toLowerCase())
    return matchesTab && matchesSearch
  })

  const showToast = (message) => {
    setToast(message)
    setTimeout(() => setToast(null), 3000)
  }

  async function handleCreate(e) {
    e.preventDefault()
    try {
      await createUnit.mutateAsync({ ...form, floor: form.floor ? parseInt(form.floor) : null })
      showToast('Unit created.')
      setShowCreate(false)
      setForm({ unit_number: '', building: '', floor: '', status: 'vacant' })
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create unit.')
    }
  }

  function openEdit(u) {
    setEditTarget(u)
    setEditForm({ unit_number: u.unit_number, building: u.building || '', floor: u.floor ?? '', status: u.status })
  }

  async function handleEdit(e) {
    e.preventDefault()
    try {
      await updateUnit.mutateAsync({
        id: editTarget.id, ...editForm, floor: editForm.floor ? parseInt(editForm.floor) : null,
      })
      showToast('Unit updated.')
      setEditTarget(null)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update unit.')
    }
  }

  return (
    <Layout title="Manage Units">
      {toast && (
        <div className="fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white bg-ink shadow-lg">
          {toast}
        </div>
      )}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h2 className="font-semibold text-ink">All Units</h2>
            <p className="text-xs text-gray-500">{units.length} units on record</p>
          </div>
          {canManage && (
            <Button onClick={() => setShowCreate(true)}>
              <i className="bi bi-plus-lg"></i> New Unit
            </Button>
          )}
        </div>

        {/* In-page tabs, per Argo UI reference — sub-navigation is tabs, never a nested sidebar */}
        <div className="flex items-center gap-1 px-4 pt-3">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setStatusTab(t.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                statusTab === t.key ? 'bg-gray-100 text-ink' : 'text-gray-600 hover:bg-gray-50'
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
              placeholder="Search unit number or building..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Building</th>
              <th className="px-4 py-3 font-medium">Floor</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canManage && <th className="px-4 py-3 font-medium text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!isLoading && filtered.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No units match this view.</td></tr>
            )}
            {!isLoading && filtered.map((u) => (
              <tr key={u.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">{u.unit_number}</td>
                <td className="px-4 py-3 text-gray-600">{u.building || '—'}</td>
                <td className="px-4 py-3 text-gray-600">{u.floor ?? '—'}</td>
                <td className="px-4 py-3">
                  <Badge tone={STATUS_TONE[u.status] || 'neutral'}>{u.status.replace('_', ' ')}</Badge>
                </td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => openEdit(u)} className="text-primary hover:underline text-xs font-medium">
                      Edit
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
          <span>Showing {filtered.length} of {units.length}</span>
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-ink">New Unit</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400"><i className="bi bi-x-lg"></i></button>
            </div>
            <form onSubmit={handleCreate} className="p-4 space-y-3">
              <input required placeholder="Unit number" value={form.unit_number}
                onChange={(e) => setForm({ ...form, unit_number: e.target.value })} className="input" />
              <input placeholder="Building" value={form.building}
                onChange={(e) => setForm({ ...form, building: e.target.value })} className="input" />
              <input placeholder="Floor" type="number" value={form.floor}
                onChange={(e) => setForm({ ...form, floor: e.target.value })} className="input" />
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="input">
                <option value="vacant">Vacant</option>
                <option value="occupied">Occupied</option>
                <option value="under_maintenance">Under Maintenance</option>
              </select>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={createUnit.isPending}>
                  {createUnit.isPending ? 'Saving…' : 'Save Unit'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-ink">Edit Unit {editTarget.unit_number}</h3>
              <button onClick={() => setEditTarget(null)} className="text-gray-400"><i className="bi bi-x-lg"></i></button>
            </div>
            <form onSubmit={handleEdit} className="p-4 space-y-3">
              <input required placeholder="Unit number" value={editForm.unit_number}
                onChange={(e) => setEditForm({ ...editForm, unit_number: e.target.value })} className="input" />
              <input placeholder="Building" value={editForm.building}
                onChange={(e) => setEditForm({ ...editForm, building: e.target.value })} className="input" />
              <input placeholder="Floor" type="number" value={editForm.floor}
                onChange={(e) => setEditForm({ ...editForm, floor: e.target.value })} className="input" />
              <select value={editForm.status} onChange={(e) => setEditForm({ ...editForm, status: e.target.value })} className="input">
                <option value="vacant">Vacant</option>
                <option value="occupied">Occupied</option>
                <option value="under_maintenance">Under Maintenance</option>
              </select>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setEditTarget(null)}>Cancel</Button>
                <Button type="submit" disabled={updateUnit.isPending}>
                  {updateUnit.isPending ? 'Saving…' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
