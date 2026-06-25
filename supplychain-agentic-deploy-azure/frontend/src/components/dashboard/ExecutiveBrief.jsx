import React from 'react'
import styles from './ExecutiveBrief.module.css'

export default function ExecutiveBrief({ brief }) {
  if (!brief) return null

  return (
    <div className={styles.card}>
      <h4 className={styles.title}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
        </svg>
        Executive Briefing
      </h4>

      <p className={styles.summary}>{brief.summary}</p>

      <div className={styles.metrics}>
        {brief.metrics.map((m) => (
          <div key={m.label} className={styles.metric}>
            <span className={`${styles.metricValue} ${m.highlight ? styles.highlight : ''}`}>{m.value}</span>
            <span className={styles.metricLabel}>{m.label}</span>
          </div>
        ))}
      </div>

      {brief.recommendation && (
        <p className={styles.recommendation}>
          <strong>Recommendation:</strong> {brief.recommendation}
        </p>
      )}
    </div>
  )
}
