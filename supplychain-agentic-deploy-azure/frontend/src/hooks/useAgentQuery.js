import { useState, useCallback } from 'react'
import { queryAgent } from '../api/agent'
import { useAuth } from '../context/AuthContext'

export function useAgentQuery() {
  const { user } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  const [conversationId, setConversationId] = useState(null)

  const query = useCallback(async (queryText) => {
    if (!queryText.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      // Rekha's backend requires role; conversationId chains history across turns
      const role = user?.role ?? 'executive'
      const data = await queryAgent(queryText, role, conversationId)

      setResult(data)
      // Persist the ID returned by the backend so the next query continues the same thread
      setConversationId(data.conversationId)
      setHistory((prev) => [
        { query: queryText, timestamp: new Date().toLocaleTimeString() },
        ...prev,
      ])
    } catch (err) {
      setError(err.message ?? 'Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [user, conversationId])

  return { isLoading, result, error, history, query }
}
