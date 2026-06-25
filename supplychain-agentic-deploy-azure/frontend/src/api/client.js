import axios from 'axios'

/**
 * Central axios instance.
 *
 * When the backend URL is known:
 *   1. Set VITE_API_URL in your .env file:
 *        VITE_API_URL=http://localhost:8000
 *   2. The baseURL below picks it up automatically.
 *   3. If the backend uses JWT, uncomment the request interceptor.
 */

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

// Attach JWT from session to every outgoing request
client.interceptors.request.use((config) => {
  const stored = sessionStorage.getItem('sc_user')
  if (stored) {
    const { token } = JSON.parse(stored)
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Global error handler ────────────────────────────────────────────────
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      sessionStorage.removeItem('sc_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
