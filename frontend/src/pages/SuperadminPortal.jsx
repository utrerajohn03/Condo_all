import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { useUsers } from '../hooks/useUsers'
import {
  useSuperadminOverview, useOrganization, useUpdateOrganization,
  usePortalConfig, useSetPortalConfig,
} from '../hooks/useSuperadmin'

const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'organization', label: 'Organization Settings' },
  { key: 'users', label: 'Users' },
  { key: 'billing', label: 'Billing Configuration' },
  { key: 'portal', label: 'Portal Configuration' },
]

const SETTING_LABEL = {
  currency: 'Display Currency',
  late_fee_percent: 'Late Fee (%)',
  dues_due_day_of_month: 'Dues Due Day of Month',
  enable_owner_portal: 'Enable Owner Portal',
  enable_online_payments: 'Enable Online Payments',
  enable_maintenance_requests: 'Enable Maintenance Requests',
}

const BILLING_KEYS = ['currency', 'late_fee_percent', 'dues_due_day_of_month']
const PORTAL_KEYS = ['enable_owner_portal', 'enable_online_payments', 'enable_maintenance_requests']

function money(v) {
  return `₱${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function SuperadminPortal() {
  const [tab, setTab] = useState('overview')
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  const { data: overview } = useSuperadminOverview()
  const { data: org } = useOrganization()
  const updateOrg = useUpdateOrganization()
  const { data: users = [] } = useUsers()
  const { data: settings = [] } = usePortalConfig()
  const setSetting = useSetPortalConfig()

  const [orgName, setOrgName] = useState('')
  useEffect(() => { if (org) setOrgName(org.name) }, [org])

  const [draftValues, setDraftValues] = useState({})
  useEffect(() => {
    const map = {}
    settings.forEach((s) => { map[s.setting_key] = s.setting_value })
    setDraftValues(map)
  }, [settings])

  async function handleSaveOrg(e) {
    e.preventDefault()
    try {
      await updateOrg.mutateAsync({ name: orgName })
      showToast('Organization updated.')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update organization.', 'error')
    }
  }

  async function handleSaveSetting(key) {
    try {
      await setSetting.mutateAsync({ key, setting_value: draftValues[key] })
      showToast('Setting saved.')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to save setting.', 'error')
    }
  }

  function renderSettingRow(key) {
    const isToggle = key.startsWith('enable_')
    return (
      <div key={key} className="flex items-center justify-between p-4 border-b border-gray-50 last:border-0">
        <div>
          <div className="text-sm font-medium text-ink">{SETTING_LABEL[key] || key}</div>
        </div>
        <div className="flex items-center gap-2">
          {isToggle ? (
            <select
              value={draftValues[key] ?? 'true'}
              onChange={(e) => setDraftValues({ ...draftValues, [key]: e.target.value })}
              className="input !w-auto"
            >
              <option value="true">Enabled</option>
              <option value="false">Disabled</option>
            </select>
          ) : (
            <input
              value={draftValues[key] ?? ''}
              onChange={(e) => setDraftValues({ ...draftValues, [key]: e.target.value })}
              className="input !w-32"
            />
          )}
          <Button size="sm" variant="secondary" onClick={() => handleSaveSetting(key)} disabled={setSetting.isPending}>
            Save
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Layout title="Superadmin Portal">
      {toast && (
        <div className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>
          {toast.message}
        </div>
      )}

      <p className="text-xs text-gray-500 -mt-3 mb-5">
        Administrator-only: condo-wide settings, users, billing configuration, and portal
        configuration for {org?.name || 'your organization'}.
      </p>

      <div className="flex items-center gap-1 mb-5 bg-white border border-gray-200 rounded-xl p-1 shadow-sm w-fit">
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

      {tab === 'overview' && overview && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { label: 'Total Units', value: overview.total_units, icon: 'bi-door-closed', color: 'bg-blue-50 text-blue-600' },
            { label: 'Total Users', value: overview.total_users, icon: 'bi-people', color: 'bg-teal-50 text-teal-600' },
            { label: 'Active Users', value: overview.active_users, icon: 'bi-person-check', color: 'bg-emerald-50 text-emerald-600' },
            { label: 'Outstanding Dues', value: money(overview.total_bills_outstanding), icon: 'bi-hourglass-split', color: 'bg-amber-50 text-amber-600' },
            { label: 'Total Collected', value: money(overview.total_collected), icon: 'bi-cash-coin', color: 'bg-emerald-50 text-emerald-600' },
            { label: 'Open Maintenance Requests', value: overview.pending_maintenance_requests, icon: 'bi-tools', color: 'bg-rose-50 text-rose-600' },
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
      )}

      {tab === 'organization' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm max-w-md">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-ink">Organization Settings</h2>
            <p className="text-xs text-gray-500">Condominium-wide identity settings</p>
          </div>
          <form onSubmit={handleSaveOrg} className="p-4 space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Condominium Corporation Name</label>
              <input value={orgName} onChange={(e) => setOrgName(e.target.value)} className="input" required />
            </div>
            <Button type="submit" disabled={updateOrg.isPending}>
              {updateOrg.isPending ? 'Saving…' : 'Save Changes'}
            </Button>
          </form>
        </div>
      )}

      {tab === 'users' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <div>
              <h2 className="font-semibold text-ink">Users</h2>
              <p className="text-xs text-gray-500">{users.length} accounts across all five roles in this organization</p>
            </div>
            <Link to="/manage-users" className="text-primary text-xs font-medium hover:underline">
              Add / edit users →
            </Link>
          </div>
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[480px]">
            <thead>
              <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-100">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-50">
                  <td className="px-4 py-3 font-medium text-ink">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3"><Badge tone="blue">{u.role.replace('_', ' ')}</Badge></td>
                  <td className="px-4 py-3">
                    <Badge tone={u.is_active ? 'emerald' : 'muted'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {tab === 'billing' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm max-w-lg">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-ink">Billing Configuration</h2>
            <p className="text-xs text-gray-500">Condo-wide defaults used by Bill Management</p>
          </div>
          {BILLING_KEYS.map(renderSettingRow)}
        </div>
      )}

      {tab === 'portal' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm max-w-lg">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-ink">Portal Configuration</h2>
            <p className="text-xs text-gray-500">Feature toggles for the portals residents, owners, and staff see</p>
          </div>
          {PORTAL_KEYS.map(renderSettingRow)}
        </div>
      )}
    </Layout>
  )
}
