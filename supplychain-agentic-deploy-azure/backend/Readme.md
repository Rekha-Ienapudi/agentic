Client (Swagger / curl / frontend)
↓
FastAPI (app.py)
↓
Route (routes/agent.py)
↓
LangGraph (agent/graph.py)
↓
LLM Call (agent/llm.py)
↓
Azure OpenAI (gpt-4.1-mini)

---


---

# 🔑 Setup (IMPORTANT)

After cloning the repo, you MUST create a `.env` file.

---

## ✅ 1. Create `.env`


touch .env

---

## ✅ 2. Add API Key

```env
AZURE_OPENAI_API_KEY=your_foundry_project_key_here

👉 Get this from:
Azure AI Studio → Project → API Key


⚠️ Important Notes
❗ .env is NOT included in repo
❗ You must add your own API key
❗ Do NOT commit secrets

▶️ How to Run

✅ 1. Install dependencies
pip install -r requirements.txt

✅ 2. Start server
Shelluvicorn app:app --reload

✅ 3. Open API Docs
http://localhost:8000/docs


✅ 4. Test API
Endpoint:
POST /api/agent/query

Example request:
JSON{  "query": "What supply chain risks do we have?"}Weitere Zeilen anzeigen

✅ Sample Response
JSON{  "conversationId": "conv-001",  "query": "What supply chain risks do we have?",  "executiveBrief": {    "summary": "The supply chain is currently experiencing delays...",    "recommendation": "Review supplier risks"  },  "risks": [    {      "title": "Supplier Delay"    }  ]}Weitere Zeilen anzeigen

⚙️ Tech Stack

FastAPI
LangGraph
Azure OpenAI (Foundry)
Python


💰 Cost Consideration

Uses gpt-4.1-mini (low-cost model ✅)
Limited tokens → minimal usage cost
Suitable for development and demos


❌ What is Not Included
For security reasons, the following are NOT committed:

.env (API keys)
Local database files
Any secrets


📄 .env.example
AZURE_OPENAI_API_KEY=your_key_here
