import { useState } from 'react'
import Layout from '../components/Layout'
import StatusBadge from '../components/StatusBadge'
import Button from '../components/ui/Button'
import { useAuth } from '../AuthContext'
import { useMaintenanceFilterStore } from '../store/useFilterStore'
import { useUnits } from '../hooks/useUnits'
import {
  useMaintenanceRequests,
  useCreateMaintenanceRequest,
  useAssignMaintenanceRequest,
  useUpdateMaintenanceStatus,
  useDeleteMaintenanceRequest,
} from '../hooks/useMaintenanceRequests'

export default function MaintenanceRequests() {
  const { role } = useAuth()

  // zustand — search/filter/tab client state (never server data itself).
  const { search, statusFilter, activeTab, setSearch, setStatusFilter, setActiveTab } =
    useMaintenanceFilterStore()

  // react-query — server state: requests list (re-fetches when statusFilter changes,
  // auto-invalidated by every mutation below) and the units list for the create form.
  const { data: requests = [], isLoading } = useMaintenanceRequests(statusFilter)
  const { data: units = [] } = useUnits()

  const createRequest = useCreateMaintenanceRequest()
  const assignRequest = useAssignMaintenanceRequest()
  const updateStatus = useUpdateMaintenanceStatus()
  const deleteRequest = useDeleteMaintenanceRequest()

  const [toast, setToast] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ unit_id: '', category: '', description: '', priority: 'medium' })
  const [assignTarget, setAssignTarget] = useState(null)
  const [assignStaffId, setAssignStaffId] = useState('')
  const [statusTarget, setStatusTarget] = useState(null)
  const [statusValue, setStatusValue] = useState('')
  const [statusReason, setStatusReason] = useState('')

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  const tabbed = activeTab === 'completed' ? requests.filter((r) => r.status === 'completed') : requests
  const filtered = tabbed.filter((r) =>
    !search || (r.category || '').toLowerCase().includes(search.toLowerCase()) || r.unit_number.includes(search)
  )

  const counts = {
    submitted: requests.filter((r) => r.status === 'submitted').length,
    assigned: requests.filter((r) => r.status === 'assigned').length,
    in_progress: requests.filter((r) => r.status === 'in_progress').length,
    completed: requests.filter((r) => r.status === 'completed').length,
  }

  async function handleCreate(e) {
    e.preventDefault()
    try {
      const res = await createRequest.mutateAsync(createForm)
      showToast(`Request created (status: ${res.data.data.status}).`)
      setShowCreate(false)
      setCreateForm({ unit_id: '', category: '', description: '', priority: 'medium' })
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create request.', 'error')
    }
  }

  async function handleAssign(e) {
    e.preventDefault()
    try {
      await assignRequest.mutateAsync({ id: assignTarget.id, assigned_to: assignStaffId })
      showToast('Request assigned.')
      setAssignTarget(null)
      setAssignStaffId('')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to assign.', 'error')
    }
  }

  async function handleStatusChange(e) {
    e.preventDefault()
    try {
      await updateStatus.mutateAsync({
        id: statusTarget.id,
        status: statusValue,
        reason: statusValue === 'rejected' ? statusReason : undefined,
      })
      showToast('Status updated.')
      setStatusTarget(null)
      setStatusValue('')
      setStatusReason('')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update status.', 'error')
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this maintenance request?')) return
    try {
      await deleteRequest.mutateAsync(id)
      showToast('Request deleted.')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete.', 'error')
    }
  }

  const canDelete = role === 'manager' || role === 'admin'
  const canAssign = role === 'staff' || role === 'manager' || role === 'admin'
  const canCreate = true // all roles hold maintenance.create

  return (
    <Layout title="Maintenance Requests">
      {toast && (
        <div className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>
          {toast.message}
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Submitted', value: counts.submitted, icon: 'bi-inbox', color: 'bg-blue-50 text-blue-600' },
          { label: 'Assigned', value: counts.assigned, icon: 'bi-person-check', color: 'bg-teal-50 text-teal-600' },
          { label: 'In Progress', value: counts.in_progress, icon: 'bi-hourglass-split', color: 'bg-amber-50 text-amber-600' },
          { label: 'Completed', value: counts.completed, icon: 'bi-check2-circle', color: 'bg-emerald-50 text-emerald-600' },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition">
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
            <h2 className="font-semibold text-ink">All Requests</h2>
            <p className="text-xs text-gray-500">Manage unit maintenance tickets</p>
          </div>
          {canCreate && (
            <Button onClick={() => setShowCreate(true)}>
              <i className="bi bi-plus-lg"></i> New Request
            </Button>
          )}
        </div>

        {/* In-page tabs — Argo UI: sub-navigation is tabs, not a nested sidebar */}
        <div className="flex items-center gap-1 px-4 pt-3">
          {[{ key: 'all', label: 'All Requests' }, { key: 'completed', label: 'Completed' }].map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                activeTab === t.key ? 'bg-gray-100 text-ink' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 p-4 border-b border-gray-100">
          <div className="relative flex-1 max-w-xs">
            <i className="bi bi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by category or unit..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        {/* Data table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
                <th className="px-4 py-3 font-medium">Unit</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              )}
              {!isLoading && filtered.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No maintenance requests yet.</td></tr>
              )}
              {filtered.map((r) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="px-4 py-3 font-medium text-ink">{r.unit_number}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{r.category || '—'}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{r.priority}</td>
                  <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                  <td className="px-4 py-3 text-gray-500">{new Date(r.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {canAssign && r.status === 'submitted' && (
                      <button
                        onClick={() => setAssignTarget(r)}
                        className="text-primary hover:underline text-xs font-medium"
                      >
                        Assign
                      </button>
                    )}
                    {(role !== 'resident' || r.status === 'submitted') && !['completed', 'cancelled', 'rejected'].includes(r.status) && (
                      <button
                        onClick={() => { setStatusTarget(r); setStatusValue('') }}
                        className="text-gray-600 hover:underline text-xs font-medium"
                      >
                        Update Status
                      </button>
                    )}
                    {canDelete && (
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="text-danger hover:underline text-xs font-medium"
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
          <span>Showing {filtered.length} of {requests.length}</span>
        </div>
      </div>

      {/* Create modal */}
      {showCreate && (
        <Modal title="New Maintenance Request" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="space-y-3">
            <Field label="Unit">
              <select
                required
                value={createForm.unit_id}
                onChange={(e) => setCreateForm({ ...createForm, unit_id: e.target.value })}
                className="input"
              >
                <option value="">Select a unit</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>{u.building} - {u.unit_number}</option>
                ))}
              </select>
            </Field>
            <Field label="Category">
              <input
                value={createForm.category}
                onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                placeholder="plumbing, electrical, hvac..."
                className="input"
              />
            </Field>
            <Field label="Priority">
              <select
                value={createForm.priority}
                onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                className="input"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </Field>
            <Field label="Description (10-2000 characters)">
              <textarea
                required
                minLength={10}
                rows={3}
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                className="input"
              />
            </Field>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button type="submit" disabled={createRequest.isPending}>
                {createRequest.isPending ? 'Submitting…' : 'Submit Request'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Assign modal */}
      {assignTarget && (
        <Modal title={`Assign Request — Unit ${assignTarget.unit_number}`} onClose={() => setAssignTarget(null)}>
          <form onSubmit={handleAssign} className="space-y-3">
            <Field label="Staff User ID">
              <input
                required
                value={assignStaffId}
                onChange={(e) => setAssignStaffId(e.target.value)}
                placeholder="Paste a staff/manager/admin user UUID"
                className="input"
              />
            </Field>
            <p className="text-xs text-gray-500">Tip: use the seeded staff user id from the README / seed script output.</p>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" onClick={() => setAssignTarget(null)}>Cancel</Button>
              <Button type="submit" disabled={assignRequest.isPending}>
                {assignRequest.isPending ? 'Assigning…' : 'Assign'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Status modal */}
      {statusTarget && (
        <Modal title={`Update Status — Unit ${statusTarget.unit_number}`} onClose={() => setStatusTarget(null)}>
          <form onSubmit={handleStatusChange} className="space-y-3">
            <Field label="New Status">
              <select required value={statusValue} onChange={(e) => setStatusValue(e.target.value)} className="input">
                <option value="">Select status</option>
                {role === 'resident' ? (
                  <option value="cancelled">Cancelled</option>
                ) : (
                  <>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                    <option value="rejected">Rejected</option>
                  </>
                )}
              </select>
            </Field>
            {statusValue === 'rejected' && (
              <Field label="Reason (required)">
                <input required value={statusReason} onChange={(e) => setStatusReason(e.target.value)} className="input" />
              </Field>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" onClick={() => setStatusTarget(null)}>Cancel</Button>
              <Button type="submit" disabled={updateStatus.isPending}>
                {updateStatus.isPending ? 'Updating…' : 'Update'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </Layout>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="font-semibold text-ink">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <i className="bi bi-x-lg"></i>
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  )
}
