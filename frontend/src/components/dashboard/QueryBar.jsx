import React, { useState, useEffect } from 'react'
import styles from './QueryBar.module.css'

export default function QueryBar({ initialValue = '', onSubmit, isLoading }) {
  const [value, setValue] = useState(initialValue)

  useEffect(() => {
    if (initialValue) setValue(initialValue)
  }, [initialValue])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (value.trim() && !isLoading) onSubmit(value.trim())
  }

  return (
    <form className={styles.bar} onSubmit={handleSubmit} role="search">
      <svg className={styles.icon} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        className={styles.input}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask the agent about your supply chain…"
        aria-label="Supply chain query"
        disabled={isLoading}
      />
      <button
        type="submit"
        className={styles.submitBtn}
        disabled={!value.trim() || isLoading}
      >
        {isLoading ? 'Analysing…' : 'Submit'}
      </button>
    </form>
  )
}
