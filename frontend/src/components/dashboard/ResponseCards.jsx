import React from 'react'
import SeverityBadge from '../shared/SeverityBadge'
import styles from './ResponseCards.module.css'

export function RiskList({ risks }) {
  if (!risks?.length) return null

  return (
    <div className={styles.card}>
      <h4 className={styles.cardTitle}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--color-warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        Top Risks
      </h4>
      <ul className={styles.list}>
        {risks.map((risk) => (
          <li key={risk.id} className={styles.riskItem}>
            <SeverityBadge severity={risk.severity} />
            <div className={styles.riskText}>
              <span className={styles.itemTitle}>{risk.title}</span>
              <span className={styles.itemDetail}>{risk.detail}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function ActionList({ actions }) {
  if (!actions?.length) return null

  return (
    <div className={styles.card}>
      <h4 className={styles.cardTitle}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
        Recommended Actions
      </h4>
      <ol className={styles.list}>
        {actions.map((action, i) => (
          <li key={action.id} className={styles.actionItem}>
            <span className={styles.actionNum}>{i + 1}</span>
            <div className={styles.actionText}>
              <span className={styles.itemTitle}>{action.title}</span>
              <span className={styles.itemDetail}>{action.detail}</span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}

export function FollowUpChips({ followUps, onSelect }) {
  if (!followUps?.length) return null

  return (
    <div className={styles.card}>
      <h4 className={styles.cardTitle}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        Follow-up questions
      </h4>
      <div className={styles.chips}>
        {followUps.map((q) => (
          <button key={q} className={styles.chip} onClick={() => onSelect(q)}>
            {q} ↗
          </button>
        ))}
      </div>
    </div>
  )
}
