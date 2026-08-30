import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import Button from '../components/ui/Button'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-sidebar">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="flex justify-center mb-4">
          <div className="bg-primary text-white rounded-xl w-12 h-12 flex items-center justify-center text-xl">
            <i className="bi bi-building"></i>
          </div>
        </div>
        <h1 className="text-xl font-semibold text-center text-ink mb-1">Condominium Management</h1>
        <p className="text-sm text-gray-500 text-center mb-6">condo_ module — ARGO platform</p>

        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-lg p-3 mb-5">
          <i className="bi bi-info-circle mr-1"></i>
          Local sandbox stand-in login only. In real ARGO, this module receives the platform
          JWT directly — no separate login page ships in the integrated module.
        </div>

        {error && (
          <div className="bg-danger/10 text-danger text-sm rounded-lg p-3 mb-4">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="admin@condo.test"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Password123!"
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        <div className="mt-6 pt-4 border-t border-gray-100 text-xs text-gray-500">
          <p className="font-medium mb-1">Demo accounts (password: Password123!)</p>
          <ul className="space-y-0.5">
            <li>admin@condo.test — Administrator (Superadmin Portal)</li>
            <li>manager@condo.test — Property Manager</li>
            <li>staff@condo.test — Front Desk Staff</li>
            <li>resident@condo.test — Resident (Tenant)</li>
            <li>owner@condo.test — Unit Owner (Owner Portal)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
