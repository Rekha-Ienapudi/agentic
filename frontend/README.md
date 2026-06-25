# Supply Chain Control Tower — Frontend

React + Vite frontend for the Agentic Supply Chain Demo.

> **Status:** Frontend is fully built and running against mock data. Backend is being built separately (Python/FastAPI + LangGraph + Azure OpenAI + PostgreSQL) by another developer. Integration is pending — see "Backend integration" below for exactly what needs to happen and what's still undecided.

## Contents

- [Quick start](#quick-start)
- [Demo accounts](#demo-accounts)
- [Project structure](#project-structure)
- [System architecture](#system-architecture)
- [Agentic framework decision](#agentic-framework-decision)
- [API contract](#api-contract)
- [Open questions for the backend team](#open-questions-for-the-backend-team)
- [Wiring up the backend](#wiring-up-the-backend)
- [Role-based rendering](#role-based-rendering)
- [React concepts used in this codebase](#react-concepts-used-in-this-codebase)
- [Known issues / housekeeping](#known-issues--housekeeping)

## Quick start

```bash
npm install
npm run dev        # → http://localhost:3000
```

## Demo accounts

| Role                        | Email                       | Password  |
|-----------------------------|-----------------------------|-----------|
| Supply Chain Executive Advisor | john.doe@cgi.com         | demo123   |
| Supply Chain Consultant     | max.mustermann@cgi.com      | demo123   |

The **Executive** role sees the Executive Briefing card on the dashboard.  
The **Consultant** role does not.

## Project structure

```
docs/
└── SupplyChain_Backend_Briefing.docx   # Full team briefing — framework decision, API contract, questions

src/
├── api/
│   ├── auth.js          # Mock login — swap for real POST /api/auth/login
│   ├── agent.js         # Mock agent query — swap for real POST /api/agent/query
│   └── client.js        # Axios instance with JWT interceptor (commented out)
├── context/
│   └── AuthContext.jsx  # Auth state + role — consumed by all components
├── hooks/
│   └── useAgentQuery.js # Agent query state management
├── mock/
│   └── agentResponses.js # Realistic supply chain mock data
├── components/
│   ├── layout/
│   │   ├── NavBar.jsx
│   │   └── ProtectedRoute.jsx
│   ├── dashboard/
│   │   ├── QueryBar.jsx
│   │   ├── KPIRow.jsx
│   │   ├── ChartPanel.jsx       # Recharts — OTIF + delay distribution
│   │   ├── ExecutiveBrief.jsx   # Executive role only
│   │   └── ResponseCards.jsx    # RiskList, ActionList, FollowUpChips
│   └── shared/
│       └── SeverityBadge.jsx
└── pages/
    ├── LoginPage.jsx
    ├── HomePage.jsx
    └── DashboardPage.jsx
```

## System architecture

```
React Frontend  (Vite, localhost:3000)
      │
      │  POST /api/auth/login
      │  POST /api/agent/query
      ▼
FastAPI Backend  (Python, localhost:8000)
      │
      ├── JWT auth middleware
      │
      ├── LangGraph Agent
      │       │
      │       ├── [intent_node]   Classifies query type
      │       ├── [tool_node]     Calls PostgreSQL via SQLAlchemy
      │       │     get_supplier_risks()
      │       │     get_inventory(material_id)
      │       │     get_open_orders(material_id)
      │       │     get_shipments(supplier_id)
      │       │     find_alternative_suppliers(material_id)
      │       │     create_action_plan(alert_id)
      │       │
      │       └── [response_node] Formats JSON matching the contract below
      │
      └── Azure OpenAI Mini  (LLM calls from within LangGraph)
              │
      PostgreSQL DB  (synthetic demo data — ~25 suppliers, 150 materials,
                       5 plants, 300 orders, 120 shipments, 10–15 alerts)
```

**Key principle:** the React frontend never talks to the LLM or the database directly. Everything routes through FastAPI. This keeps secrets off the client and gives full control over what the agent can do.

## Agentic framework decision

**Recommendation: LangGraph.** Decision owner: Mohd Sadiq.

The PoC owner originally suggested "OpenClaw" for the agentic framework. That's **not viable** — as of mid-2026 it has no public repository or installable package, was rebranded three times in six months (Clawdbot → Moltbot → OpenClaw), and is architecturally a messaging-platform daemon (WhatsApp/Telegram bot), not a Python library that embeds in a FastAPI backend.

Comparison of real options:

| Framework | Assessment |
|---|---|
| **LangGraph** | **Recommended.** Graph-based orchestration — each step (intent classification, tool call, response formatting) is an explicit node. Predictable, auditable execution path you can show the customer mid-demo ("here's exactly what the agent did"). Native Azure OpenAI support via `langchain-openai`. Maps directly onto this agent's flow: query → classify intent → call DB tools → format response. |
| **CrewAI** | Valid fallback. Faster initial setup (~40 min to a working multi-agent system), role-based abstraction. Less transparent than LangGraph — harder to explain or debug live in front of a customer. |
| **OpenClaw** | Not viable. No installable package, wrong architecture for this use case. |
| **LangChain (base)** | The lower-level library LangGraph is built on. Don't use directly — LangGraph gives everything LangChain does plus stateful graph orchestration. |

Minimal LangGraph shape for this project:

```python
pip install langgraph langchain-openai

from langgraph.graph import StateGraph
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool

@tool
def get_supplier_risks() -> list:
    """Returns suppliers with risk_score > 70 from the database."""
    # SQL query against PostgreSQL here
    ...

graph = StateGraph(AgentState)
graph.add_node('intent', classify_intent)
graph.add_node('tools', call_tools)
graph.add_node('response', format_response)
graph.add_edge('intent', 'tools')
graph.add_edge('tools', 'response')
```

A full writeup (with rationale, comparison table, and code) was shared with the team as `SupplyChain_Backend_Briefing.docx`.

## API contract

This is the **authoritative spec** the backend (built by Rekha) needs to match. The frontend is already built and tested against this exact shape using mock data in `src/mock/agentResponses.js` — that file is the clearest reference if anything here is ambiguous.

### `POST /api/auth/login`

Request:
```json
{ "email": "john.doe@cgi.com", "password": "..." }
```

Success (200):
```json
{
  "id": "u1",
  "name": "John Doe",
  "email": "john.doe@cgi.com",
  "role": "executive",
  "roleLabel": "Supply Chain Executive Advisor",
  "initials": "JD",
  "token": "eyJhbGci..."
}
```

`role` must be exactly `"executive"` or `"consultant"` (lowercase) — the frontend uses this string directly to decide whether to render the Executive Briefing.

Error (401):
```json
{ "detail": "Invalid email or password." }
```

### `POST /api/agent/query`

Request:
```json
{ "query": "What critical risks do we currently have?", "conversationId": "conv-001" }
```
`conversationId` is `null` for new conversations.

Success (200):
```json
{
  "conversationId": "conv-001",
  "query": "What critical risks do we currently have?",

  "kpis": {
    "otif":            { "value": "87.4%", "delta": "-2.1% vs last month", "trend": "down" },
    "ordersAtRisk":    { "value": "47",    "delta": "+12 this week",       "trend": "down" },
    "revenueExposure": { "value": "4.2M",  "delta": "3 critical suppliers","trend": "down" },
    "inventoryHealth": { "value": "73%",   "delta": "2 stockout risks",    "trend": "neutral" }
  },

  "executiveBrief": {
    "summary": "...",
    "metrics": [
      { "value": "87.4%", "label": "OTIF" },
      { "value": "4.2M",  "label": "Revenue at risk", "highlight": true },
      { "value": "3",     "label": "Plants affected" },
      { "value": "47",    "label": "Orders at risk" }
    ],
    "recommendation": "..."
  },

  "risks": [
    { "id": "r1", "severity": "critical", "title": "Foxconn delay — 12 materials affected", "detail": "14 days · 47 customer orders impacted" }
  ],

  "actions": [
    { "id": "a1", "title": "Activate alternative supplier for Material Y", "detail": "Supplier B · qualified · +8% cost delta · 5-day lead time" }
  ],

  "followUps": [
    "Which customer orders are affected by the Foxconn delay?",
    "What are the alternative suppliers for Material Y?"
  ],

  "chartData": {
    "otif":   { "labels": ["Foxconn", "Supplier B", "Supplier C"], "values": [78, 95, 91] },
    "delays": { "labels": ["0–3 d", "4–7 d", "8–14 d", "15–21 d", ">21 d"], "values": [42, 28, 18, 9, 3] }
  },

  "alertsBanner": "3 active disruptions · Foxconn: 14-day delay · ..."
}
```

Important details:
- `trend` is `"up"` | `"down"` | `"neutral"` — controls KPI card colour and icon. Always include it.
- `severity` is `"critical"` | `"high"` | `"medium"` | `"low"`.
- `executiveBrief` must be `null` for the consultant role — the frontend checks for null and skips that card.

## Open questions for the backend team

These were sent to Rekha and Mohd Sadiq alongside the briefing doc. Tracking them here so Claude Code (or future-you) knows what's still unresolved.

**Group 1 — blocks integration, needs answers first**
1. Exact login response JSON — does it match the contract above?
2. Streaming (SSE) or single JSON response? This changes `useAgentQuery` significantly — see the comment block in that file for the streaming swap-in plan.
3. Confirm exact endpoint paths (`/api/auth/login`, `/api/agent/query` assumed).
4. CORS — FastAPI needs `fastapi.middleware.cors` allowing `localhost:3000`, or every browser request gets blocked.

**Group 2 — needed before the agent is built**
5. Azure OpenAI deployment name + API version (`AzureChatOpenAI(deployment_name=..., api_version=..., azure_endpoint=...)`).
6. Who seeds the synthetic PostgreSQL data (~25 suppliers, 150 materials, 5 plants, etc.)?
7. Final LangGraph tool function signatures — need to match `get_supplier_risks()`, `get_inventory(material_id)`, etc.
8. Is conversation history persistence in scope for the PoC, or does it stay client-side (`sessionStorage`, current behaviour)?

**Group 3 — needed before demo day**
9. Hosting plan for the demo — local laptop, or deployed somewhere for remote/on-site presentation?
10. Secrets management — `.env.local` pattern on frontend; backend needs equivalent for Azure OpenAI keys + DB connection string. Nothing gets committed.

## Wiring up the backend

### 1. Auth
In `src/api/auth.js`, replace `mockLogin` with:
```js
import client from './client'
export async function mockLogin(email, password) {
  const { data } = await client.post('/api/auth/login', { email, password })
  return data  // expects: { id, name, email, role, roleLabel, initials, token }
}
```
Then uncomment the JWT request interceptor in `src/api/client.js`.

### 2. Agent queries
In `src/api/agent.js`, replace `mockAgentQuery` with:
```js
import client from './client'
export async function mockAgentQuery(query) {
  const { data } = await client.post('/api/agent/query', { query })
  return data
}
```

### 3. Streaming (if backend supports SSE)
In `src/hooks/useAgentQuery.js`, replace the `mockAgentQuery` call with an
EventSource that calls `setResult` incrementally as chunks arrive.

### 4. Backend URL
Copy `.env.example` to `.env.local` and set:
```
VITE_API_URL=http://localhost:8000
```

Also uncomment the proxy in `vite.config.js` for local dev (avoids CORS).

## Role-based rendering

Role is stored on the `user` object in `AuthContext`. Components check:
```js
const { user } = useAuth()
const isExecutive = user?.role === 'executive'
```

Role values: `'executive'` | `'consultant'`. Adding new roles only requires updating the conditionals in `DashboardPage.jsx` and `HomePage.jsx`.

## React concepts used in this codebase

Notes for understanding (not just copying) this code — useful context if you're learning React alongside building this.

**Context (`src/context/AuthContext.jsx`)** — solves prop drilling. Without it, `user` would need to be passed as a prop through every component between `App` and anything that needs it (`NavBar`, `DashboardPage`, `ExecutiveBrief`). Instead, `AuthProvider` wraps the whole app once, and any component calls `useAuth()` to read `{ user, login, logout }` directly. When `login()` calls `setUser(...)`, every component consuming `useAuth()` re-renders automatically — no manual wiring.

**Hooks used:**
- `useState` — value that persists across renders, triggers re-render on update. The `AuthContext` initial state uses the *lazy initializer* form (`useState(() => {...})`) to read `sessionStorage` once on mount, not on every render.
- `useEffect` — side effects after render (data fetching, reading the URL). `DashboardPage` uses `useEffect(() => { ... }, [])` to fire the initial query once when the page loads, using the empty dependency array to mean "run once."
- `useContext` — reads from a Context Provider; powers `useAuth()`.
- `useCallback` — memoizes a function so it isn't recreated every render; used in `useAgentQuery` so the `query` function has a stable identity.

**Custom hook (`src/hooks/useAgentQuery.js`)** — extracts the loading/result/error state machine out of `DashboardPage` entirely. The page just does `const { isLoading, result, error, query } = useAgentQuery()` and renders conditionally. This means when the backend is wired up, only the hook's internals change — no component touches new code.

**The golden rule used throughout:** data flows down via props, events flow up via callback functions, and only truly global state (auth) lives in Context. Components are kept "dumb" — they receive state and render it; the logic for *how* state changes lives in hooks.

**Routing (`react-router-dom`)** — `App.jsx` defines all routes. `useNavigate()` changes the URL programmatically (e.g., after login). `useLocation()` reads the current URL and any state attached to it — this is how clicking an example query on `HomePage` pre-fills and auto-fires the query on `DashboardPage` (`navigate('/dashboard', { state: { initialQuery: q } })`, then `location.state?.initialQuery` on the other end).

**`ProtectedRoute.jsx`** — wraps any route needing auth. Redirects to `/login` if no `user`, and remembers the originally requested path (`state: { from: location }`) so `LoginPage` can send the user back there after a successful login.

## Known issues / housekeeping

- `npm audit` reports 2 high-severity vulnerabilities in `esbuild` (bundled inside Vite). **Do not run `npm audit fix --force`** — it jumps to Vite 8, a breaking major version change. The vulnerability is dev-server-only (a malicious website could send requests to the local dev server) and not a meaningful risk for this PoC. Address it deliberately later via a real Vite upgrade, not an auto-fix.
- Conversation history currently lives in `sessionStorage` only — lost on refresh. See Group 2, question 8 above for the decision on whether this moves server-side.
- Zscaler (corporate proxy) did not cause SSL issues with `npm install` on the dev machine this was tested on, but if it does on a different machine: `npm config set cafile /etc/ssl/cert.pem`, or extract the Zscaler root cert via `security find-certificate -a -p /Library/Keychains/System.keychain > ~/zscaler-certs.pem` and point `cafile` at that.

