# Agentic Supply Chain — PoC

A working AI-powered supply chain control tower built for CGI's event demo. Three distinct employee copilots sit on top of a real PostgreSQL database — each with its own persona, KPI set, and response framing. Ask any supply chain question in natural language and the agent classifies intent, fans out to parallel data agents, generates a structured response, then runs it through a critique loop before returning it.

**Stack:** React + Vite · FastAPI · LangGraph · AzureChatOpenAI (gpt-4.1-mini) · PostgreSQL · SQLAlchemy · JWT auth

---

## Quick Start

You need two terminals — one for the backend, one for the frontend.

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (running locally)
- Access to an Azure OpenAI resource with `gpt-4.1-mini` deployed

### Terminal 1 — Backend

```bash
cd backend

python -m venv venv                          # first time only
venv/bin/pip install -r requirements.txt     # first time only

# Create backend/.env — see Environment Variables section below

createdb supplychain                          # first time only (PostgreSQL)
venv/bin/python seed_scenarios.py            # first time only — builds all tables and data

venv/bin/uvicorn app:app --reload --port 8000
```

### Terminal 2 — Frontend

```bash
cd frontend
npm install        # first time only
npm run dev        # → http://localhost:3000
```

Open **http://localhost:3000** in your browser.

---

## Environment Variables

Create `backend/.env` — **this file is gitignored, never commit it.**

```env
DATABASE_URL=postgresql://<your-pg-username>@localhost/supplychain
SECRET_KEY=supplychain-dev-secret-2026

AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2025-04-01-preview
```

Get the Azure key from: **Azure AI Studio → your project → Settings → API Keys**.

> If the server starts but queries fail, check the backend terminal for `LLM error: 401` — the key is wrong or missing.

---

## Demo Accounts — Three Copilots

Each account is a distinct AI persona with its own KPI set and response framing.

| # | Role | Email | Password | KPIs shown |
|---|------|-------|----------|------------|
| 1 | **Supply Chain Executive Advisor** | john.doe@cgi.com | demo123 | OTIF · Revenue at risk · Suppliers flagged · Inventory health |
| 2 | **Operations Manager (Control Tower)** | max.mustermann@cgi.com | demo123 | Same supply chain KPIs, operational tone, no brief card |
| 3 | **Logistics & Transportation Manager** | lisa.transport@cgi.com | demo123 | On-time delivery · Delayed shipments · Freight cost · CO₂ |

**Persona differences in action:** Ask the same question — e.g. *"What is the situation at Prague?"* — as Operations Manager and then as Logistics Manager. The Operations Manager gets root causes, supplier names, and mitigation actions. The Logistics Manager gets shipment IDs, carrier performance, freight costs, and CO₂ impact.

---

## Demo Queries by Account

### Executive Advisor — Board-level briefing

```
"Give me the current health of our supply chain."
"What is the situation at our Prague plant?"
"How does Prague compare to Vienna?"
"What three actions would improve our OTIF the most within 30 days?"
"What is our total revenue exposure from Electronics suppliers?"
```

### Operations Manager — Control Tower daily briefing

```
"Which critical risks do we have in the supply chain right now?"
"What is causing the Prague plant crisis?"
"What is ChipTech Asia's current performance?"
"Which customer orders are affected by Foxconn's delays?"
"Which materials are at risk of stockout?"
"Find alternative suppliers for the Foxconn materials."
```

### Logistics Manager — Transport operations review

```
"Which shipments are currently delayed?"
"Which transport routes are generating the highest freight costs?"
"Show me all shipments from Foxconn Technology Group."
"What is our CO₂ footprint from air freight versus road?"
"What is the logistics situation at the Prague plant?"
"Which carriers have the worst on-time performance?"
```

### Role-switching demo (high impact)
Log out and ask the same question — e.g. *"What is the situation at our Prague plant?"* — as each of the three accounts in turn. The KPI cards change, the tone changes, and the recommended actions change.

---

## Database — What's in It

The database is seeded with real-world-scale data and intentional plant risk profiles.

| Entity | Count | Notes |
|--------|-------|-------|
| Suppliers | 50 | Real company names: Foxconn, TSMC, Infineon, SKF, BASF, Valeo, etc. |
| Materials | 500 | 10 per supplier, realistic part numbering by category |
| Shipments | 500 | 10 per supplier, delay rate tied to risk score |
| Customer orders | 2,350 | 33% at-risk globally |
| Inventory records | 500 | Stock levels tied to supplier risk + plant |
| Customers | 60 | BMW, VW, Airbus, Siemens, Tesla, Foxconn customers, etc. |
| Plants | 5 | Prague · Munich · Berlin · Warsaw · Vienna |

**Plant risk profiles** (intentional, for demo contrast):

| Plant | At-risk orders | OTIF | Stockouts | Profile |
|-------|---------------|------|-----------|---------|
| Prague | 70% | 55% | 29 | CRISIS — Electronics/Semiconductor cluster |
| Munich | 44% | ~72% | 1 | HIGH — Mixed APAC exposure |
| Berlin | 28% | ~78% | 0 | MODERATE — Automotive components |
| Warsaw | 16% | ~86% | 0 | LOW — Raw materials, reliable suppliers |
| Vienna | 6% | 82% | 0 | HEALTHY — Chemical/specialty, best OTIF |

**Supplier categories:** Electronics · Semiconductors · Mechanical · Raw Materials · Chemical & Specialty · Automotive Components · Connectors & Sensors · Packaging

**Transport modes on shipments:** Air (APAC high-risk, avg €11k/shipment, high CO₂) · Sea (APAC bulk, avg €3k) · Road (EU domestic, avg €500) · Rail (EU long-haul, avg €800)

To reseed from scratch (drops all tables):
```bash
cd backend && venv/bin/python seed_scenarios.py
```

---

## Agent Architecture

```
Browser (localhost:3000)
    │
    │  POST /api/auth/login     → JWT token
    │  POST /api/agent/query    → { query, role, conversationId }
    ▼
FastAPI (localhost:8000)
    │
    ├── JWT auth (routes/auth.py)
    │
    └── LangGraph 4-node pipeline (agent/graph.py)
            │
            ├── [intent_node]
            │     LLM classifies query into one of 9 intents:
            │     risk_analysis | inventory | orders | alternatives |
            │     customer_lookup | supplier_lookup | plant_lookup |
            │     category_lookup | general
            │     Then extracts entity name (customer/supplier/plant/category)
            │     before parallel fan-out — avoids duplicate LLM calls
            │
            ├── [tool_node]   ThreadPoolExecutor — parallel agents
            │     _kpi_agent()         context-aware KPIs (role + entity filtered)
            │     _risk_agent()        supplier risks + delayed shipments
            │     _inventory_agent()   low-stock materials
            │     _orders_agent()      at-risk customer orders
            │     _customer_agent()    orders for a named customer
            │     _supplier_lookup_agent()  shipments from a named supplier
            │     _alternatives_agent()    backup supplier search
            │
            ├── [response_node]
            │     Role-specific persona prompt (executive / operations / logistics)
            │     Injects critique feedback on retry
            │     Calls gpt-4.1-mini → parses JSON → builds response
            │
            └── [critique_node]
                  Scores response 1–10 on: relevance, action quality, recommendation
                  If score < 7 and retry_count < 2 → loops back to response_node
                  Otherwise → END
                        │
                        ▼
                  PostgreSQL (SQLAlchemy ORM)
                  50 suppliers · 500 materials · 500 shipments
                  2,350 orders · 500 inventory records · 60 customers
```

**Short-term conversation memory** (`agent/memory.py`) — in-memory, keyed by `conversationId` UUID. The last 6 turns are injected into every response prompt so the agent can answer follow-up questions.

**Context-aware KPIs** (`agent/kpi.py`) — the KPI agent reads intent and entity_name from state to filter its query:
- `plant_lookup + "Prague"` → KPIs filtered to Prague shipments/orders/inventory
- `customer_lookup + "BMW Group"` → at-risk count filtered to BMW's orders
- `logistics` role → transport KPIs (on-time rate, freight cost, CO₂) instead of supply chain KPIs

---

## Project Structure

```
supplychain-agentic/
├── README.md
│
├── backend/
│   ├── app.py                  FastAPI app — routes, CORS, startup check
│   ├── models.py               SQLAlchemy ORM: Supplier, Material, Shipment,
│   │                           CustomerOrder, Inventory
│   ├── db.py                   PostgreSQL session factory (SQLAlchemy)
│   ├── seed_scenarios.py       Drops + rebuilds all tables with demo data
│   │                           Edit this file to change suppliers/customers/data
│   ├── init_db.py              Called on startup — creates tables if missing
│   ├── requirements.txt
│   ├── .env                    ← NOT committed — create manually (see above)
│   │
│   ├── agent/
│   │   ├── graph.py            LangGraph 4-node pipeline — main orchestrator
│   │   │                       Edit here to change agent behaviour/personas
│   │   ├── tools.py            @tool decorated DB query functions
│   │   │                       Add new data tools here
│   │   ├── kpi.py              KPI computation — supply chain + logistics variants
│   │   │                       Edit here to change what KPI cards show
│   │   ├── llm.py              AzureChatOpenAI wrapper (call_llm helper)
│   │   └── memory.py           In-memory conversation history per conversationId
│   │
│   ├── routes/
│   │   ├── agent.py            POST /api/agent/query
│   │   └── auth.py             POST /api/auth/login — demo user registry
│   │                           Add new demo accounts here
│   └── auth/
│       ├── utils.py            JWT creation
│       └── deps.py             JWT verification FastAPI dependency
│
└── frontend/
    ├── vite.config.js          Dev proxy: /api/* → localhost:8000
    └── src/
        ├── api/
        │   ├── client.js       Axios instance — JWT interceptor, 401 redirect
        │   └── agent.js        queryAgent() — wraps POST /api/agent/query
        ├── context/
        │   └── AuthContext.jsx Auth state, real backend login, session persistence
        ├── hooks/
        │   └── useAgentQuery.js Loading/result/error state + conversationId
        ├── pages/
        │   ├── LoginPage.jsx   3-account demo buttons
        │   ├── HomePage.jsx    Landing page
        │   └── DashboardPage.jsx  Main UI — KPI row, chat, response cards
        └── components/
            └── dashboard/
                ├── QueryBar.jsx
                ├── KPIRow.jsx           KPI cards (labels adapt per role)
                ├── ChartPanel.jsx       OTIF bar chart + delay distribution
                ├── ExecutiveBrief.jsx   Executive + Logistics brief card
                └── ResponseCards.jsx    Risk list + action list
```

---

## Where to Make Changes

| What you want to change | Where to edit |
|------------------------|---------------|
| Add a new demo user / role | `backend/routes/auth.py` → `_USERS` dict |
| Change agent personas / tone | `backend/agent/graph.py` → `response_node` persona strings |
| Add a new supply chain intent | `backend/agent/graph.py` → `_VALID_INTENTS`, `intent_node` prompt, `tool_node` routing |
| Add a new DB tool | `backend/agent/tools.py` → new `@tool` function, then wire into `tool_node` |
| Change KPI definitions | `backend/agent/kpi.py` → `compute_kpis()` or `compute_logistics_kpis()` |
| Change critique threshold | `backend/agent/graph.py` → `CRITIQUE_THRESHOLD = 7` and `MAX_RETRIES = 2` |
| Add/modify suppliers or customers | `backend/seed_scenarios.py` → `SUPPLIER_DEFS` or `CUSTOMERS` lists |
| Change plant risk profiles | `backend/seed_scenarios.py` → `PLANT_RISK_MOD` dict |
| Change number of orders | `backend/seed_scenarios.py` → `n_orders_for()` function |
| Reseed the database | `cd backend && venv/bin/python seed_scenarios.py` |
| Add a new KPI card to the UI | `frontend/src/components/dashboard/KPIRow.jsx` |
| Change KPI card labels per role | `frontend/src/pages/DashboardPage.jsx` (passes role to KPIRow) |

---

## API Reference

### `POST /api/auth/login`
```json
Request:  { "email": "john.doe@cgi.com", "password": "demo123" }
Response: { "id": "u1", "name": "John Doe", "role": "executive",
            "roleLabel": "Supply Chain Executive Advisor",
            "token": "<jwt>" }
```

### `POST /api/agent/query`
```json
Request:
{
  "query": "What is the situation at Prague?",
  "role": "executive",
  "conversationId": "<uuid>"   // optional — omit for new conversation
}

Response:
{
  "conversationId": "<uuid>",
  "query": "...",
  "kpis": {
    "otif":            { "value": "55.1%", "delta": "-34.9% vs 90% target · Prague plant", "trend": "down" },
    "ordersAtRisk":    { "value": "307",   "delta": "307 open · Prague plant",              "trend": "down" },
    "revenueExposure": { "value": "€27.6M","delta": "307 at-risk orders · Prague plant",   "trend": "down" },
    "inventoryHealth": { "value": "70.4%", "delta": "vs 80% target · Prague plant",        "trend": "down" }
  },
  "executiveBrief": {              // null for operations role
    "summary": "...",
    "metrics": [...],
    "recommendation": "..."
  },
  "risks": [...],
  "actions": [
    { "id": "a1", "title": "...", "detail": "owner · timeline · impact" }
  ],
  "followUps": [],
  "chartData": { ... },
  "alertsBanner": "1 critical supplier alerts · 307 orders at risk · 29 inventory issues"
}
```

---

## What's In / Out of Scope

| Feature | Status |
|---------|--------|
| LangGraph 4-node pipeline (intent → tools → response → critique) | ✅ Done |
| LLM-based intent classification (9 intents) | ✅ Done |
| Multi-agent parallel execution (ThreadPoolExecutor) | ✅ Done |
| Critique agent — scores 1-10, retries below threshold | ✅ Done |
| Three role-specific personas (executive / operations / logistics) | ✅ Done |
| Context-aware KPIs (filtered by plant / supplier / customer / category) | ✅ Done |
| Logistics KPIs — on-time %, freight cost, CO₂ | ✅ Done |
| Transport data on shipments (mode, cost, CO₂, carrier) | ✅ Done |
| In-memory conversation history (follow-up questions) | ✅ Done |
| Real PostgreSQL — 2,350 orders, 60 customers, 50 suppliers | ✅ Done |
| JWT auth (real backend login) | ✅ Done |
| KPI cards, risk list, action list, charts | ✅ Done |
| Streaming responses (SSE) | ❌ Not implemented |
| Conversation history persisted to PostgreSQL | ❌ Not in scope |
| Deployed hosting | ❌ Local only — run on demo laptop |
| FollowUp chip suggestions | ❌ API field present, UI commented out |

---

## Secrets Checklist

- `backend/.env` is gitignored — **never commit it**
- The Azure OpenAI API key is only in `.env` — it is not in any committed file
- If cloning fresh: create `backend/.env` manually before running the server
