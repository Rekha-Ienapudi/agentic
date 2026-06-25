import React, { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './LoginPage.module.css'

const DEMO_ACCOUNTS = [
  { label: 'Executive Advisor',      email: 'john.doe@cgi.com',        password: 'demo123' },
  { label: 'Operations Manager',     email: 'max.mustermann@cgi.com',   password: 'demo123' },
  { label: 'Logistics Manager',      email: 'lisa.transport@cgi.com',   password: 'demo123' },
]

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Already logged in — skip to intended destination
  const from = location.state?.from?.pathname ?? '/home'
  if (user) return <Navigate to={from} replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message ?? 'Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const fillDemo = (account) => {
    setEmail(account.email)
    setPassword(account.password)
    setError('')
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.header}>
          <svg className={styles.logoIcon} width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0070F2" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/>
            <line x1="12" y1="7" x2="5" y2="17"/><line x1="12" y1="7" x2="19" y2="17"/><line x1="5" y1="19" x2="19" y2="19"/>
          </svg>
          <h1 className={styles.title}>Agentic Supply Chain Demo</h1>
          <p className={styles.subtitle}>Sign in to access the Control Tower</p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className={styles.field}>
            <label htmlFor="email" className={styles.label}>User Name / Email</label>
            <input
              id="email"
              type="email"
              className={styles.input}
              placeholder="john.doe@cgi.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              disabled={isLoading}
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password" className={styles.label}>Password</label>
            <input
              id="password"
              type="password"
              className={styles.input}
              placeholder="••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <p className={styles.error} role="alert">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </p>
          )}

          <button type="submit" className={styles.submitBtn} disabled={isLoading || !email || !password}>
            {isLoading ? 'Signing in…' : 'Log In'}
          </button>
        </form>

        <div className={styles.demoSection}>
          <p className={styles.demoLabel}>Demo accounts</p>
          <div className={styles.demoAccounts}>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                className={styles.demoBtn}
                onClick={() => fillDemo(acc)}
                disabled={isLoading}
              >
                <span className={styles.demoBtnRole}>{acc.label}</span>
                <span className={styles.demoBtnEmail}>{acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
