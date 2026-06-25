import React from 'react'
import styles from './SeverityBadge.module.css'

const SEV_MAP = {
  critical: { label: 'Critical', cls: styles.critical },
  high:     { label: 'High',     cls: styles.high },
  medium:   { label: 'Medium',   cls: styles.medium },
  low:      { label: 'Low',      cls: styles.low },
}

export default function SeverityBadge({ severity }) {
  const { label, cls } = SEV_MAP[severity] ?? SEV_MAP.low
  return <span className={`${styles.badge} ${cls}`}>{label}</span>
}
