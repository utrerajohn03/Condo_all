import { useState } from 'react'
import Layout from '../components/Layout'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { useAuth } from '../AuthContext'
import {
  useUsers, useCreateUser, useActivateUser, useDeactivateUser, useDeleteUser,
} from '../hooks/useUsers'

const TABS = [
  { key: 'all', label: 'All Users' },
  { key: 'manager', label: 'Manager' },
  { key: 'staff', label: 'Staff' },
  { key: 'resident', label: 'Residents' },
  { key: 'unit_owner', label: 'Unit Owners' },
]

export default function ManageUsers() {
  const { role } = useAuth()
  const isAdmin = role === 'admin'
  const [tab, setTab] = useState('all')
  const [search, setSearch] = useState('')
  const { data: users = [], isLoading } = useUsers(tab === 'all' ? undefined : tab)
  const createUser = useCreateUser()
  const activateUser = useActivateUser()
  const deactivateUser = useDeactivateUser()
  const deleteUser = useDeleteUser()

  const [toast, setToast] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'resident' })

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  const filtered = users.filter((u) =>
    !search ||
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  const counts = {
    total: users.length,
    active: users.filter((u) => u.is_active).length,
    residents: users.filter((u) => u.role === 'resident').length,
    unitOwners: users.filter((u) => u.role === 'unit_owner').length,
    staffPlus: users.filter((u) => ['staff', 'manager', 'admin'].includes(u.role)).length,
  }

  async function handleCreate(e) {
    e.preventDefault()
    try {
      await createUser.mutateAsync(form)
      showToast('User created.')
      setShowCreate(false)
      setForm({ email: '', full_name: '', password: '', role: 'resident' })
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create user.', 'error')
    }
  }

  async function handleToggleActive(u) {
    try {
      if (u.is_active) {
        await deactivateUser.mutateAsync(u.id)
        showToast(`${u.full_name} deactivated.`)
      } else {
        await activateUser.mutateAsync(u.id)
        showToast(`${u.full_name} activated.`)
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Action failed.', 'error')
    }
  }

  async function handleDelete(u) {
    if (!confirm(`Delete ${u.full_name}? This cannot be undone.`)) return
    try {
      await deleteUser.mutateAsync(u.id)
      showToast('User deleted.')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete.', 'error')
    }
  }

  return (
    <Layout title="Manage Users">
      {toast && (
        <div className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>
          {toast.message}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {[
          { label: 'Active Users', value: counts.active, icon: 'bi-people', color: 'bg-blue-50 text-blue-600' },
          { label: 'Total Users', value: counts.total, icon: 'bi-person-lines-fill', color: 'bg-teal-50 text-teal-600' },
          { label: 'Staff / Manager / Admin', value: counts.staffPlus, icon: 'bi-person-badge', color: 'bg-amber-50 text-amber-600' },
          { label: 'Residents', value: counts.residents, icon: 'bi-house', color: 'bg-emerald-50 text-emerald-600' },
          { label: 'Unit Owners', value: counts.unitOwners, icon: 'bi-house-gear', color: 'bg-indigo-50 text-indigo-600' },
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
            <h2 className="font-semibold text-ink">Manage Users</h2>
            <p className="text-xs text-gray-500">
              {isAdmin ? 'Administrator: add, edit, activate, or deactivate accounts' : 'View residents and users in your organization'}
            </p>
          </div>
          {isAdmin && (
            <Button onClick={() => setShowCreate(true)}>
              <i className="bi bi-plus-lg"></i> Add User
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
              placeholder="Search name or email..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {isAdmin && <th className="px-4 py-3 font-medium text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>}
            {!isLoading && filtered.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No users match this view.</td></tr>
            )}
            {!isLoading && filtered.map((u) => (
              <tr key={u.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-ink">{u.full_name}</td>
                <td className="px-4 py-3 text-gray-600">{u.email}</td>
                <td className="px-4 py-3"><Badge tone="blue">{u.role.replace('_', ' ')}</Badge></td>
                <td className="px-4 py-3">
                  <Badge tone={u.is_active ? 'emerald' : 'muted'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                </td>
                {isAdmin && (
                  <td className="px-4 py-3 text-right space-x-3">
                    <button onClick={() => handleToggleActive(u)} className="text-primary hover:underline text-xs font-medium">
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button onClick={() => handleDelete(u)} className="text-danger hover:underline text-xs font-medium">
                      Delete
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
          <span>Showing {filtered.length} of {users.length}</span>
        </div>
      </div>

      {showCreate && isAdmin && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-ink">Add User</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400"><i className="bi bi-x-lg"></i></button>
            </div>
            <form onSubmit={handleCreate} className="p-4 space-y-3">
              <input required type="email" placeholder="Email" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" />
              <input required placeholder="Full name" value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="input" />
              <input required type="password" minLength={8} placeholder="Password (min. 8 characters)" value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })} className="input" />
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="input">
                <option value="resident">Resident</option>
                <option value="unit_owner">Unit Owner</option>
                <option value="staff">Staff</option>
                <option value="manager">Manager</option>
                <option value="admin">Administrator</option>
              </select>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={createUser.isPending}>
                  {createUser.isPending ? 'Saving…' : 'Add User'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
