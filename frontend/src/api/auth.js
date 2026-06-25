/**
 * Mock authentication.
 *
 * Replace the body of `mockLogin` with a real API call when ready:
 *
 *   import client from './client'
 *
 *   export async function mockLogin(email, password) {
 *     const { data } = await client.post('/api/auth/login', { email, password })
 *     // data should return: { id, name, email, role, token }
 *     return data
 *   }
 *
 * Role values the rest of the app expects: 'executive' | 'consultant'
 */

const MOCK_USERS = [
  {
    id: 'u1',
    name: 'John Doe',
    email: 'john.doe@cgi.com',
    role: 'executive',         // sees Executive Briefing
    roleLabel: 'Supply Chain Executive Advisor',
    initials: 'JD',
    password: 'demo123',
    token: 'mock-jwt-token-executive',
  },
  {
    id: 'u2',
    name: 'Max Mustermann',
    email: 'max.mustermann@cgi.com',
    role: 'consultant',        // no Executive Briefing
    roleLabel: 'Supply Chain Consultant',
    initials: 'MM',
    password: 'demo123',
    token: 'mock-jwt-token-consultant',
  },
]

export async function mockLogin(email, password) {
  // Simulate network latency
  await new Promise((r) => setTimeout(r, 600))

  const user = MOCK_USERS.find(
    (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
  )

  if (!user) {
    const err = new Error('Invalid email or password.')
    err.code = 'AUTH_FAILED'
    throw err
  }

  const { password: _pw, ...safeUser } = user
  return safeUser
}
