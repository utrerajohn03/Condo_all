import { useState } from 'react'
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
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function closeSidebar() {
    setOpen(false)
  }

  const initials = (email || '?').slice(0, 2).toUpperCase()
  const visibleItems = navItems.filter((item) => !item.roles || item.roles.includes(role))

  return (
    <div className="min-h-screen bg-canvas">
      {/* Mobile overlay — dims content and closes on tap */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar — flat, one level, w-240px, #0F172A. Off-canvas on mobile, pinned on lg+ */}
      <aside
        className={`fixed top-0 left-0 h-screen w-60 bg-sidebar flex flex-col z-30 transform transition-transform duration-300 ${
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="h-16 flex items-center gap-2 px-4 border-b border-white/10">
          <div className="bg-primary text-white rounded-lg w-8 h-8 flex items-center justify-center">
            <i className="bi bi-building"></i>
          </div>
          <span className="text-white font-semibold text-sm">Condo Management</span>
          <button
            onClick={closeSidebar}
            className="ml-auto text-gray-400 hover:text-white lg:hidden"
            title="Close menu"
          >
            <i className="bi bi-x-lg"></i>
          </button>
        </div>
        <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={closeSidebar}
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

      {/* Header — h-64px sticky, #0F172A. Slides right with the sidebar on mobile */}
      <header className={`fixed top-0 right-0 h-16 bg-sidebar flex items-center justify-between px-4 lg:px-6 z-10 transition-[left] duration-300 ${open ? 'left-60' : 'left-0 lg:left-60'}`}>
        <div className="flex items-center gap-2 min-w-0">
          <button
            onClick={() => setOpen(!open)}
            className="lg:hidden text-white hover:text-gray-300 p-1"
            title="Open menu"
          >
            <i className="bi bi-list text-2xl"></i>
          </button>
          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5 text-xs text-white truncate">
            <i className="bi bi-diagram-3"></i>
            <span className="truncate">Utrera Condos Corporation</span>
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <i className="bi bi-bell text-gray-300"></i>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-semibold">
              {initials}
            </div>
            <div className="text-white text-xs hidden sm:block">
              <div className="font-medium">{email}</div>
              <div className="text-gray-400 capitalize">{(role || '').replace('_', ' ')}</div>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-white ml-1"
              title="Log out"
            >
              <i className="bi bi-box-arrow-right"></i>
            </button>
          </div>
        </div>
      </header>

      {/* Content canvas — padded for the pinned sidebar on lg+, full width on mobile */}
      <main className={`pt-16 p-4 lg:p-6 lg:ml-60 transition-[margin-left] duration-300`}>
        <h1 className="text-xl font-semibold text-ink mb-5">{title}</h1>
        {children}
      </main>
    </div>
  )
}