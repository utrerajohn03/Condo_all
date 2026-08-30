import axios from 'axios'

// In local dev, Vite reads VITE_API_BASE from .env.local (defaults to localhost:8000
// if that file is missing). In production:
//  - Split deployment (Vercel): set VITE_API_BASE to the backend project's URL.
//  - Combined single-origin deployment (e.g. Replit, where FastAPI serves this built
//    frontend itself): set VITE_API_BASE="" (empty string) so requests go to the same
//    origin the page was loaded from. Uses `??` rather than `||` on purpose — an
//    explicitly empty string must NOT fall back to the localhost default.
export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('condo_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('condo_token')
      localStorage.removeItem('condo_role')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
