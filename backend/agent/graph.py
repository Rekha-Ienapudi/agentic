import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from langgraph.graph import StateGraph, END
from agent.llm import call_llm
from agent.kpi import compute_executive_kpis, compute_scm_kpis, compute_logistics_kpis
from agent.memory import get_history, save_message
from agent.tools import (
    get_supplier_risks,
    get_delayed_shipments,
    get_at_risk_orders,
    get_low_inventory,
    find_alternative_suppliers,
    create_action_plan,
    compute_chart_data,
    get_orders_by_customer,
    get_shipments_by_supplier,
    get_carrier_performance,
    simulate_supplier_failure,
)

State = dict

_VALID_INTENTS = {"risk_analysis", "inventory", "orders", "alternatives",
                  "customer_lookup", "supplier_lookup", "plant_lookup", "category_lookup",
                  "scenario_simulation", "carrier_performance", "general"}
MAX_RETRIES = 2
CRITIQUE_THRESHOLD = 7


# ── Node 1: LLM intent classification ────────────────────────────────────────
def intent_node(state: State) -> State:
    q = state.get("query", "")
    prompt = (
        "Classify the following supply chain query into exactly one of these intents:\n"
        "- risk_analysis: supplier risk scores, OTIF performance, shipment delays, disruptions\n"
        "- inventory: stock levels, stockouts, safety stock, material availability\n"
        "- orders: customer orders overview, fulfilment status, delivery commitments\n"
        "- alternatives: finding replacement or backup suppliers\n"
        "- customer_lookup: orders or status for a specific named customer company\n"
        "- supplier_lookup: shipments, performance, or status for a specific named supplier\n"
        "- plant_lookup: situation at a specific manufacturing plant (Prague, Munich, Berlin, Warsaw, Vienna)\n"
        "- category_lookup: performance of a material or supplier category (Electronics, Semiconductors, Mechanical, etc.)\n"
        "- scenario_simulation: 'what if' or 'what happens if' a supplier fails, stops, or is disrupted\n"
        "- carrier_performance: which carriers are on time, carrier SLA, transport partner performance\n"
        "- general: overview, dashboard summary, or anything that doesn't fit the above\n\n"
        f"Query: {q}\n\n"
        "Reply with ONLY the intent label, nothing else."
    )
    raw    = call_llm(prompt).strip().lower().replace(".", "").replace("\"", "")
    intent = raw if raw in _VALID_INTENTS else "general"
    state["intent"] = intent
    state.setdefault("retry_count", 0)
    state.setdefault("critique_feedback", "")

    # Extract entity name before parallel fan-out so all agents share it without extra LLM calls.
    if intent == "customer_lookup":
        state["entity_name"] = call_llm(
            f"Extract the customer company name from this query. Reply with the name only.\nQuery: {q}"
        ).strip()
    elif intent == "supplier_lookup":
        state["entity_name"] = call_llm(
            f"Extract the supplier company name from this query. Reply with the name only.\nQuery: {q}"
        ).strip()
    elif intent == "plant_lookup":
        state["entity_name"] = call_llm(
            f"Extract the plant name from this query. Must be one of: Prague, Munich, Berlin, Warsaw, Vienna. Reply with the name only.\nQuery: {q}"
        ).strip()
    elif intent == "category_lookup":
        state["entity_name"] = call_llm(
            f"Extract the supply chain category from this query (e.g. Electronics, Semiconductors, Mechanical, Raw Materials). Reply with the category name only.\nQuery: {q}"
        ).strip()
    elif intent == "scenario_simulation":
        state["entity_name"] = call_llm(
            f"Extract the supplier name from this scenario/what-if query. Reply with the supplier name only.\nQuery: {q}"
        ).strip()
        duration_raw = call_llm(
            f"Extract the failure duration in days from this query (e.g. '2 weeks' → 14, '1 month' → 30, '10 days' → 10). If not specified reply with 14. Reply with a number only.\nQuery: {q}"
        ).strip()
        try:
            state["scenario_duration"] = int(duration_raw)
        except ValueError:
            state["scenario_duration"] = 14
    else:
        state["entity_name"] = ""

    print(f"\n[AGENT] ── intent_node (LLM) ── intent={intent}  entity='{state['entity_name']}'")
    return state


# ── Node 2: Parallel multi-agent tool execution ───────────────────────────────
# Each agent is a named function run concurrently via ThreadPoolExecutor.
# Results are collected and written to state once all agents complete.

def _kpi_agent(state):
    intent = state.get("intent", "general")
    entity = state.get("entity_name", "")
    role   = state.get("role", "executive")
    print("[KPI AGENT]       running...")

    filters = dict(
        customer_name = entity if intent == "customer_lookup" else None,
        supplier_name = entity if intent == "supplier_lookup" else None,
        plant_id      = entity if intent == "plant_lookup"    else None,
        category      = entity if intent == "category_lookup" else None,
    )

    if role == "logistics":
        kpis = compute_logistics_kpis(
            supplier_name=filters["supplier_name"],
            plant_id=filters["plant_id"],
        )
    elif role == "operations":
        kpis = compute_scm_kpis(**filters)
    else:
        kpis = compute_executive_kpis(**filters)

    result = {"kpis": kpis, "chart_data": compute_chart_data.invoke({})}
    print(f"[KPI AGENT]       done — ordersAtRisk={kpis['ordersAtRisk']['value']}  otif={kpis['otif']['value']}")
    return result

def _risk_agent(_):
    print("[RISK AGENT]      running...")
    result = {
        "risks":             get_supplier_risks.invoke({}),
        "delayed_shipments": get_delayed_shipments.invoke({}),
    }
    print(f"[RISK AGENT]      done — {len(result['risks'])} risks, {len(result['delayed_shipments'])} delays")
    return result

def _inventory_agent(_):
    print("[INVENTORY AGENT] running...")
    result = {"low_inventory": get_low_inventory.invoke({})}
    print(f"[INVENTORY AGENT] done — {len(result['low_inventory'])} low-stock items")
    return result

def _orders_agent(_):
    print("[ORDERS AGENT]    running...")
    result = {"at_risk_orders": get_at_risk_orders.invoke({})}
    print(f"[ORDERS AGENT]    done — {len(result['at_risk_orders'])} at-risk orders")
    return result

def _customer_agent(state):
    # Entity already extracted in intent_node — no second LLM call needed
    name = state.get("entity_name", "")
    print("[CUSTOMER AGENT]  running...")
    orders = get_orders_by_customer.invoke({"customer_name": name})
    print(f"[CUSTOMER AGENT]  done — {len(orders)} orders for '{name}'")
    return {"customer_orders": orders}

def _supplier_lookup_agent(state):
    name = state.get("entity_name", "")
    print("[SUPPLIER AGENT]  running...")
    shipments = get_shipments_by_supplier.invoke({"supplier_name": name})
    print(f"[SUPPLIER AGENT]  done — {len(shipments)} shipments for '{name}'")
    return {"supplier_shipments": shipments}

def _carrier_agent(_):
    print("[CARRIER AGENT]   running...")
    result = {"carrier_performance": get_carrier_performance.invoke({})}
    print(f"[CARRIER AGENT]   done — {len(result['carrier_performance'])} carriers")
    return result

def _scenario_agent(state):
    supplier = state.get("entity_name", "")
    duration = state.get("scenario_duration", 14)
    print(f"[SCENARIO AGENT]  running — supplier='{supplier}' duration={duration}d...")
    result = {"scenario_result": simulate_supplier_failure.invoke({"supplier_name": supplier, "duration_days": duration})}
    print(f"[SCENARIO AGENT]  done — {result['scenario_result'].get('affected_orders', 0)} orders affected")
    return result

def _alternatives_agent(state):
    print("[ALT AGENT]       running...")
    risks    = get_supplier_risks.invoke({})
    at_risk  = get_at_risk_orders.invoke({})
    plan     = create_action_plan.invoke({"supplier_id": risks[0]["id"]}) if risks else {}
    alts     = find_alternative_suppliers.invoke({"material_id": at_risk[0]["material_id"]}) if at_risk else []
    result   = {
        "risks":         risks,
        "action_plan":   plan,
        "alternatives":  alts,
        "at_risk_orders": at_risk,
    }
    print(f"[ALT AGENT]       done — plan={bool(plan)}, alts={len(alts)}")
    return result


def tool_node(state: State) -> State:
    intent = state.get("intent", "general")
    print(f"[AGENT] ── tool_node ── intent={intent}  launching parallel agents...")

    # Decide which specialized agents to run based on intent
    agent_fns = [_kpi_agent]  # KPI agent always runs

    if intent == "risk_analysis":
        agent_fns += [_risk_agent, _orders_agent]
    elif intent == "inventory":
        agent_fns += [_inventory_agent, _orders_agent]
    elif intent == "orders":
        agent_fns += [_orders_agent, _risk_agent]
    elif intent == "alternatives":
        agent_fns += [_alternatives_agent]
    elif intent == "customer_lookup":
        agent_fns += [_customer_agent, _orders_agent]
    elif intent == "supplier_lookup":
        agent_fns += [_supplier_lookup_agent, _risk_agent]
    elif intent == "plant_lookup":
        agent_fns += [_risk_agent, _inventory_agent, _orders_agent]
    elif intent == "category_lookup":
        agent_fns += [_risk_agent, _orders_agent]
    elif intent == "scenario_simulation":
        agent_fns += [_scenario_agent, _alternatives_agent]
    elif intent == "carrier_performance":
        agent_fns += [_carrier_agent, _risk_agent]
    else:  # general — full picture
        agent_fns += [_risk_agent, _inventory_agent, _orders_agent]

    # Run all selected agents in parallel
    with ThreadPoolExecutor(max_workers=len(agent_fns)) as pool:
        futures = {pool.submit(fn, state): fn.__name__ for fn in agent_fns}
        for future in as_completed(futures):
            agent_name = futures[future]
            try:
                updates = future.result()
                state.update(updates)
            except Exception as exc:
                print(f"[AGENT] WARNING: {agent_name} failed — {exc}")

    # Defaults for fields that may not have been set
    state.setdefault("risks", [])
    state.setdefault("delayed_shipments", [])
    state.setdefault("at_risk_orders", [])
    state.setdefault("low_inventory", [])
    state.setdefault("alternatives", [])
    state.setdefault("action_plan", {})
    state.setdefault("customer_orders", [])
    state.setdefault("supplier_shipments", [])
    state.setdefault("carrier_performance", [])
    state.setdefault("scenario_result", {})
    state.setdefault("entity_name", "")
    state.setdefault("scenario_duration", 14)

    print(f"[AGENT] ── tool_node complete ── "
          f"risks={len(state['risks'])}  delayed={len(state['delayed_shipments'])}  "
          f"orders={len(state['at_risk_orders'])}  low_inv={len(state['low_inventory'])}")
    return state


# ── Node 3: LLM response generation ──────────────────────────────────────────
def response_node(state: State) -> State:
    query           = state.get("query", "")
    role            = state.get("role", "executive")
    conv_id         = state.get("conversationId", "default")
    intent          = state.get("intent", "general")
    critique_feedback = state.get("critique_feedback", "")
    retry_count     = state.get("retry_count", 0)

    kpis            = state.get("kpis", {})
    risks           = state.get("risks", [])
    delayed         = state.get("delayed_shipments", [])
    at_risk_orders  = state.get("at_risk_orders", [])
    low_inv         = state.get("low_inventory", [])
    action_plan        = state.get("action_plan", {})
    customer_orders    = state.get("customer_orders", [])
    supplier_ships     = state.get("supplier_shipments", [])
    carrier_perf       = state.get("carrier_performance", [])
    scenario_result    = state.get("scenario_result", {})
    entity_name     = state.get("entity_name", "")

    history = get_history(conv_id)
    history_text = (
        "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history[-6:])
        if history else "None"
    )

    kpi_otif   = kpis.get("otif", {}).get("value", "N/A")
    kpi_orders = kpis.get("ordersAtRisk", {}).get("value", "N/A")
    kpi_inv    = kpis.get("inventoryHealth", {}).get("value", "N/A")

    if role == "executive":
        persona = (
            "Supply Chain Executive Advisor. "
            "Your audience is C-level. Focus on strategic impact: Service Level, OTIF trends, "
            "Working Capital, Inventory Turns, revenue exposure, and top 3–5 prioritised actions "
            "that will move the needle within 30 days. Be concise, decisive, and business-outcome driven. "
            "Never go into operational detail — delegate that to the operations team."
        )
    elif role == "logistics":
        persona = (
            "Logistics & Transportation Operations Manager AI. "
            "Your audience is the logistics team. Focus on: shipment status and ETAs, "
            "delayed consignments, freight cost exposure, CO₂ impact, carrier performance, "
            "and alternative routing options. Be specific about shipment IDs, routes, "
            "carriers, and transit times. Recommend cost and carbon optimisation actions."
        )
    else:  # operations / supply chain manager (default)
        persona = (
            "Supply Chain Manager AI — tactical control tower. "
            "Your audience is the supply chain management team. Focus on: balancing demand and supply, "
            "stockout risk, inventory levels, supplier OTD (on-time delivery), customer service levels, "
            "order cycle times, and concrete mitigation actions with named owners and timelines. "
            "Be specific — name suppliers, materials, plants, and quantities."
        )

    # Build extra context depending on intent
    extra_context = ""
    if intent == "scenario_simulation" and scenario_result:
        extra_context = f"\nScenario simulation result for '{entity_name}': {json.dumps(scenario_result)}"
    elif intent == "carrier_performance" and carrier_perf:
        extra_context = f"\nCarrier performance data: {json.dumps(carrier_perf[:15])}"
    elif intent == "customer_lookup" and customer_orders:
        extra_context = f"\nCustomer orders for '{entity_name}': {json.dumps(customer_orders[:10])}"
    elif intent == "supplier_lookup" and supplier_ships:
        extra_context = f"\nShipments from '{entity_name}': {json.dumps(supplier_ships[:10])}"
    elif action_plan:
        extra_context = f"\nAction plan: {json.dumps(action_plan)}"

    improvement_note = (
        f"\n\nIMPORTANT: Your previous answer scored below the quality threshold. "
        f"Improve it based on this feedback: {critique_feedback}"
        if critique_feedback and retry_count > 0 else ""
    )

    if role == "executive":
        summary_hint = "2-3 sentence strategic summary for C-level, focused on business impact and financial risk"
        rec_hint     = "1-2 sentence board-level recommendation prioritising the top action within 30 days"
        action_hint  = "owner (function) · 30-day timeline · measurable business outcome"
    elif role == "logistics":
        summary_hint = "2-3 sentence logistics summary covering shipment status, delays, cost, and CO₂"
        rec_hint     = "1-2 sentence operational recommendation on routing, carrier, or cost optimisation"
        action_hint  = "logistics owner · lead time · cost or CO₂ impact"
    else:
        summary_hint = "2-3 sentence operational summary naming specific suppliers, plants, and materials"
        rec_hint     = "1-2 sentence action recommendation with a named owner and concrete next step"
        action_hint  = "named owner · timeline · risk mitigated"

    prompt = f"""You are a {persona}

Recent conversation:
{history_text}

Live supply chain data:
- OTIF / On-time rate: {kpi_otif}
- Orders / shipments at risk: {kpi_orders}
- Inventory health / CO₂: {kpi_inv}
- High-risk suppliers: {len(risks)} ({sum(1 for r in risks if r.get('severity') == 'critical')} critical)
- Delayed shipments: {len(delayed)}
- Customer orders at risk: {len(at_risk_orders)}
- Low-stock materials: {len(low_inv)}
- Risk details: {json.dumps(risks[:5])}{extra_context}{improvement_note}

User query: {query}

Respond ONLY with this JSON (no markdown fences, no text outside the JSON):
{{
  "summary": "<{summary_hint}>",
  "recommendation": "<{rec_hint}>",
  "actions": [
    {{"title": "<concrete action>", "detail": "<{action_hint}>"}},
    {{"title": "<concrete action>", "detail": "<{action_hint}>"}}
  ]
}}"""

    print(f"[AGENT] ── response_node ── role={role}  retry={retry_count}  conv_id={conv_id[:8]}...")
    print("[AGENT]    calling AzureChatOpenAI (gpt-4.1-mini)...")
    llm_raw = call_llm(prompt)
    print(f"[AGENT]    responded ({len(llm_raw)} chars)")

    try:
        start  = llm_raw.find("{")
        end    = llm_raw.rfind("}") + 1
        parsed = json.loads(llm_raw[start:end])
    except Exception:
        parsed = {
            "summary": llm_raw,
            "recommendation": "Review the supply chain data for actionable insights.",
            "actions": [],
        }

    save_message(conv_id, "user", query)
    save_message(conv_id, "assistant", parsed.get("summary", ""))

    critical_count = sum(1 for r in risks if r.get("severity") == "critical")

    if role == "executive":
        executive_brief = {
            "summary": parsed.get("summary", ""),
            "metrics": [
                {"value": kpi_otif,          "label": "OTIF"},
                {"value": kpi_orders,         "label": "Revenue at risk", "highlight": True},
                {"value": str(len(risks)),    "label": "Suppliers flagged"},
                {"value": kpi_inv,            "label": "Inventory health"},
            ],
            "recommendation": parsed.get("recommendation", ""),
        }
    elif role == "logistics":
        executive_brief = {
            "summary": parsed.get("summary", ""),
            "metrics": [
                {"value": kpi_otif,            "label": "On-time delivery"},
                {"value": str(len(delayed)),   "label": "Delayed shipments", "highlight": True},
                {"value": kpi_orders,          "label": "Freight exposure"},
                {"value": kpi_inv,             "label": "CO₂ impact"},
            ],
            "recommendation": parsed.get("recommendation", ""),
        }
    else:
        executive_brief = None

    state["response"] = {
        "conversationId": conv_id,
        "query":          query,
        "kpis":           kpis,
        "executiveBrief": executive_brief,
        "risks":          risks,
        "actions": [
            {"id": f"a{i}", **a}
            for i, a in enumerate(parsed.get("actions", []), 1)
        ],
        "followUps":   [],
        "chartData":   state.get("chart_data", {}),
        "alertsBanner": (
            f"{critical_count} critical supplier alerts · "
            f"{len(at_risk_orders)} orders at risk · "
            f"{len(low_inv)} inventory issues"
        ),
    }

    # Store parsed response for critique
    state["_parsed_response"] = parsed
    return state


# ── Node 4: Critique agent ────────────────────────────────────────────────────
def critique_node(state: State) -> State:
    parsed = state.get("_parsed_response", {})
    query  = state.get("query", "")

    summary        = parsed.get("summary", "")
    recommendation = parsed.get("recommendation", "")
    actions        = parsed.get("actions", [])

    prompt = (
        f"You are a quality reviewer for an AI supply chain assistant.\n\n"
        f"User query: {query}\n\n"
        f"AI response:\n"
        f"- Summary: {summary}\n"
        f"- Recommendation: {recommendation}\n"
        f"- Actions: {json.dumps(actions)}\n\n"
        f"Score this response from 1 to 10 using these criteria:\n"
        f"  - Directly and specifically answers the query (0-4 pts)\n"
        f"  - Actions are concrete with owner, timeline, and impact (0-3 pts)\n"
        f"  - Recommendation is actionable and relevant (0-3 pts)\n\n"
        f"Return ONLY this JSON: "
        f'{{\"score\": <integer 1-10>, \"feedback\": \"<one sentence on what to improve, or empty string if score >= {CRITIQUE_THRESHOLD}>\"}}'
    )

    raw = call_llm(prompt).strip()
    try:
        start  = raw.find("{")
        end    = raw.rfind("}") + 1
        result = json.loads(raw[start:end])
        score    = int(result.get("score", 10))
        feedback = result.get("feedback", "")
    except Exception:
        score    = 10
        feedback = ""

    state["critique_score"]    = score
    state["critique_feedback"] = feedback
    print(f"[CRITIQUE AGENT]  score={score}/10  retry_count={state.get('retry_count', 0)}  "
          f"feedback='{feedback[:60]}{'...' if len(feedback) > 60 else ''}'")
    return state


def _should_retry(state: State) -> str:
    score       = state.get("critique_score", 10)
    retry_count = state.get("retry_count", 0)
    if score < CRITIQUE_THRESHOLD and retry_count < MAX_RETRIES:
        state["retry_count"] = retry_count + 1
        print(f"[CRITIQUE AGENT]  → score below {CRITIQUE_THRESHOLD}, retry {state['retry_count']}/{MAX_RETRIES}")
        return "retry"
    print(f"[CRITIQUE AGENT]  → accepted (score={score}, retries={retry_count})")
    return "done"


# ── Graph wiring ──────────────────────────────────────────────────────────────
builder = StateGraph(State)
builder.add_node("intent",   intent_node)
builder.add_node("tools",    tool_node)
builder.add_node("response", response_node)
builder.add_node("critique", critique_node)

builder.set_entry_point("intent")
builder.add_edge("intent",   "tools")
builder.add_edge("tools",    "response")
builder.add_edge("response", "critique")
builder.add_conditional_edges(
    "critique",
    _should_retry,
    {"retry": "response", "done": END},
)

workflow = builder.compile()
