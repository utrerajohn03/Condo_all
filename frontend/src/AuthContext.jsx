import { createContext, useContext, useState } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [role, setRole] = useState(localStorage.getItem('condo_role'))
  const [email, setEmail] = useState(localStorage.getItem('condo_email'))

  async function login(loginEmail, password) {
    const res = await api.post('/api/auth/login', { email: loginEmail, password })
    localStorage.setItem('condo_token', res.data.token)
    localStorage.setItem('condo_role', res.data.role)
    localStorage.setItem('condo_email', loginEmail)
    setRole(res.data.role)
    setEmail(loginEmail)
  }

  function logout() {
    localStorage.removeItem('condo_token')
    localStorage.removeItem('condo_role')
    localStorage.removeItem('condo_email')
    setRole(null)
    setEmail(null)
  }

  const isAuthenticated = !!localStorage.getItem('condo_token')

  return (
    <AuthContext.Provider value={{ role, email, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
