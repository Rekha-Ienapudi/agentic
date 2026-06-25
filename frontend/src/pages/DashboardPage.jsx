import React, { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useAgentQuery } from '../hooks/useAgentQuery'
import QueryBar from '../components/dashboard/QueryBar'
import KPIRow from '../components/dashboard/KPIRow'
import ChartPanel from '../components/dashboard/ChartPanel'
import ExecutiveBrief from '../components/dashboard/ExecutiveBrief'
import { RiskList, ActionList/*, FollowUpChips*/ } from '../components/dashboard/ResponseCards'
import styles from './DashboardPage.module.css'

function AlertsBanner({ message }) {
  if (!message) return null
  return (
    <div className={styles.alertsBanner} role="alert">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      {message}
    </div>
  )
}

function LoadingState() {
  return (
    <div className={styles.loadingState} aria-live="polite" aria-label="Analysing supply chain data">
      <div className={styles.spinner} aria-hidden="true" />
      <p>Agent is analysing your supply chain data…</p>
    </div>
  )
}

function ErrorState({ message, onRetry }) {
  return (
    <div className={styles.errorState} role="alert">
      <p>{message}</p>
      <button onClick={onRetry} className={styles.retryBtn}>Try again</button>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const location = useLocation()
  const { isLoading, result, error, query } = useAgentQuery()

  const isExecutive = user?.role === 'executive'

  // Fire initial query if navigated here with one
  useEffect(() => {
    const initialQuery = location.state?.initialQuery
    if (initialQuery) query(initialQuery)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // const handleFollowUp = (q) => {
  //   query(q)
  //   window.scrollTo({ top: 0, behavior: 'smooth' })
  // }

  return (
    <div className={styles.wrap}>
      <QueryBar
        initialValue={location.state?.initialQuery ?? ''}
        onSubmit={query}
        isLoading={isLoading}
      />

      {isLoading && <LoadingState />}

      {error && !isLoading && (
        <ErrorState message={error} onRetry={() => query(location.state?.initialQuery ?? '')} />
      )}

      {result && !isLoading && (
        <>
          <AlertsBanner message={result.alertsBanner} />
          <KPIRow kpis={result.kpis} />
          <ChartPanel chartData={result.chartData} />

          {/* Executive Briefing — executive role only */}
          {isExecutive && <ExecutiveBrief brief={result.executiveBrief} />}

          <div className={styles.responseGrid}>
            <RiskList risks={result.risks} />
            <ActionList actions={result.actions} />
          </div>

          {/* <FollowUpChips followUps={result.followUps} onSelect={handleFollowUp} /> */}
        </>
      )}

      {!result && !isLoading && !error && (
        <div className={styles.emptyState}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p>Ask the agent a question to see the analysis here.</p>
        </div>
      )}
    </div>
  )
}
