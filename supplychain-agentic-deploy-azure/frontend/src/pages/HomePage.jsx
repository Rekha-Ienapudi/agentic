import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { PREVIOUS_CONVERSATIONS } from '../mock/agentResponses'
import styles from './HomePage.module.css'

// const BASE_QUERIES = [
//   'What critical risks do we currently have in our supply chain?',
//   'Which customer orders are at risk due to supplier delays?',
//   'Where is a stockout risk imminent in the next 7 days?',
// ]

// const EXEC_QUERIES = [
//   'Give me an executive briefing on our supply chain health.',
//   'Which three measures will improve delivery reliability within 30 days?',
// ]

export default function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [showHistory, setShowHistory] = useState(false)

  // const exampleQueries = user?.role === 'executive'
  //   ? [...BASE_QUERIES, ...EXEC_QUERIES]
  //   : BASE_QUERIES

  const goToDashboard = (query = '') => {
    navigate('/dashboard', { state: { initialQuery: query } })
  }

  return (
    <div className={styles.wrap}>
      <section className={styles.welcome}>
        <h2 className={styles.heading}>Welcome, {user?.name?.split(' ')[0]}!</h2>
        <p className={styles.description}>
          This AI-powered Supply Chain Control Tower monitors your end-to-end supply chain,
          identifies disruptions in real time, and helps you take action — from spotting a
          delayed shipment to drafting a COO briefing.
        </p>

        {/* Example queries hidden — AI-suggested prompts removed per tech lead feedback */}
        {/* <div className={styles.queries}>
          <p className={styles.queriesLabel}>Example queries</p>
          <ul className={styles.queryList}>
            {exampleQueries.map((q) => (
              <li key={q}>
                <button className={styles.queryChip} onClick={() => goToDashboard(q)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                  </svg>
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div> */}
      </section>

      <div className={styles.cards}>
        <button className={styles.card} onClick={() => goToDashboard()}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <h3 className={styles.cardTitle}>Start a new conversation</h3>
          <p className={styles.cardDesc}>Ask the agent about risks, delays, suppliers, or customer orders</p>
        </button>

        <button className={styles.card} onClick={() => setShowHistory((s) => !s)}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="12 8 12 12 14 14"/><path d="M3.05 11a9 9 0 1 0 .5-3"/>
            <polyline points="3 4 3 11 10 11"/>
          </svg>
          <h3 className={styles.cardTitle}>Previous conversations</h3>
          <p className={styles.cardDesc}>Resume a past session or review earlier analyses</p>
        </button>
      </div>

      {showHistory && (
        <section className={styles.history}>
          <h3 className={styles.historyLabel}>Recent conversations</h3>
          {PREVIOUS_CONVERSATIONS.map((convo) => (
            <button
              key={convo.id}
              className={styles.convoItem}
              onClick={() => goToDashboard(convo.query)}
            >
              <div className={styles.convoMain}>
                <span className={styles.convoTitle}>{convo.title}</span>
                <span className={styles.convoPreview}>{convo.preview}</span>
              </div>
              <span className={styles.convoTime}>{convo.timestamp}</span>
            </button>
          ))}
        </section>
      )}
    </div>
  )
}
