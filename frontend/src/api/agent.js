import client from './client'

export async function queryAgent(queryText, role, conversationId = null) {
  const { data } = await client.post('/api/agent/query', {
    query: queryText,
    role,
    conversationId,
  })
  return data
}
