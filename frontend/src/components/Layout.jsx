import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

// Sidebar order per the panel's spec: Dashboard, Owner Portal, Manage Users, Manage
// Units, Resident Assignments, Maintenance, Payments, Bill Management, Superadmin
// Portal. `roles: null` = visible to everyone. A role sees the item if it holds at
// least VIEW-level access to that page — what a role can actually DO once there
// (add/edit/delete vs. read-only) is still enforced by the page itself and by the
// backend permission checks.
const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'bi-speedometer2', roles: null },
  { to: '/owner-portal', label: 'Owner Portal', icon: 'bi-house-gear', roles: ['unit_owner'] },
  { to: '/manage-users', label: 'Manage Users', icon: 'bi-people', roles: ['staff', 'manager', 'admin'] },
  { to: '/units', label: 'Manage Units', icon: 'bi-door-closed', roles: ['staff', 'manager', 'admin'] },
  { to: '/resident-assignments', label: 'Resident Assignments', icon: 'bi-link-45deg', roles: ['staff', 'manager', 'admin'] },
  { to: '/maintenance-requests', label: 'Maintenance', icon: 'bi-tools', roles: null },
  { to: '/payments', label: 'Payments', icon: 'bi-credit-card', roles: ['resident', 'unit_owner'] },
  { to: '/bill-management', label: 'Bill Management', icon: 'bi-receipt', roles: ['staff', 'manager', 'admin'] },
  { to: '/superadmin', label: 'Superadmin Portal', icon: 'bi-shield-lock', roles: ['admin'] },
]

export default function Layout({ children, title }) {
  const { role, email, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = (email || '?').slice(0, 2).toUpperCase()
  const visibleItems = navItems.filter((item) => !item.roles || item.roles.includes(role))

  return (
    <div className="min-h-screen bg-canvas">
      {/* Sidebar — flat, one level, w-240px, #0F172A */}
      <aside className="fixed top-0 left-0 h-screen w-60 bg-sidebar flex flex-col z-20">
        <div className="h-16 flex items-center gap-2 px-4 border-b border-white/10">
          <div className="bg-primary text-white rounded-lg w-8 h-8 flex items-center justify-center">
            <i className="bi bi-building"></i>
          </div>
          <span className="text-white font-semibold text-sm">Condo Management</span>
        </div>
        <nav className="flex-1 py-3 px-2 space-y-1">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-active text-white'
                    : 'text-gray-400 hover:bg-active/50 hover:text-white'
                }`
              }
            >
              <i className={`bi ${item.icon}`}></i>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 text-[10px] text-gray-500 border-t border-white/10">
          condo_ module · v0.2
        </div>
      </aside>

      {/* Header — h-64px sticky, #0F172A */}
      <header className="fixed top-0 left-60 right-0 h-16 bg-sidebar flex items-center justify-between px-6 z-10">
        <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5 text-xs text-white">
          <i className="bi bi-diagram-3"></i>
          Utrera Condos Corporation
        </div>
        <div className="flex items-center gap-4">
          <i className="bi bi-bell text-gray-300"></i>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-semibold">
              {initials}
            </div>
            <div className="text-white text-xs">
              <div className="font-medium">{email}</div>
              <div className="text-gray-400 capitalize">{(role || '').replace('_', ' ')}</div>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-white ml-2"
              title="Log out"
            >
              <i className="bi bi-box-arrow-right"></i>
            </button>
          </div>
        </div>
      </header>

      {/* Content canvas */}
      <main className="ml-60 pt-16 p-6">
        <h1 className="text-xl font-semibold text-ink mb-5">{title}</h1>
        {children}
      </main>
    </div>
  )
}
