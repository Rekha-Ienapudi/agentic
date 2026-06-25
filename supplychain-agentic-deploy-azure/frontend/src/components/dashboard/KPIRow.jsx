import React from 'react'
import styles from './KPIRow.module.css'

function TrendIcon({ trend }) {
  if (trend === 'up') return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
    </svg>
  )
  if (trend === 'down') return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>
    </svg>
  )
  return null
}

const KPI_KEYS = [
  { key: 'otif',            valueColor: 'var(--color-success)' },
  { key: 'ordersAtRisk',    valueColor: 'var(--color-danger)'  },
  { key: 'revenueExposure', valueColor: 'var(--color-warning)' },
  { key: 'inventoryHealth', valueColor: 'var(--color-accent)'  },
]

export default function KPIRow({ kpis }) {
  if (!kpis) return null

  return (
    <div className={styles.row}>
      {KPI_KEYS.map(({ key, valueColor }) => {
        const kpi = kpis[key]
        if (!kpi) return null
        return (
          <div key={key} className={styles.card}>
            <p className={styles.label}>{kpi.label ?? key}</p>
            <p className={styles.value} style={{ color: valueColor }}>{kpi.value}</p>
            <p className={`${styles.delta} ${styles[kpi.trend]}`}>
              <TrendIcon trend={kpi.trend} />
              {kpi.delta}
            </p>
          </div>
        )
      })}
    </div>
  )
}
