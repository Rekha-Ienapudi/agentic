from langchain_core.tools import tool
from db import SessionLocal
from models import Supplier, Material, Shipment, CustomerOrder, Inventory


@tool
def get_supplier_risks() -> list:
    """Returns all suppliers with risk_score above 70, classified as critical (>85) or high."""
    db = SessionLocal()
    try:
        rows = db.query(Supplier).filter(Supplier.risk_score > 70).order_by(Supplier.risk_score.desc()).all()
        return [
            {
                "id": s.id,
                "severity": "critical" if s.risk_score > 85 else "high",
                "title": f"{s.name} — risk score {s.risk_score}",
                "detail": f"OTIF {round(s.otif, 1)}% · {s.category} · {s.region}",
            }
            for s in rows
        ]
    finally:
        db.close()


@tool
def get_delayed_shipments() -> list:
    """Returns all shipments currently delayed, joined with supplier name and delay severity."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Shipment, Supplier)
            .join(Supplier, Shipment.supplier_id == Supplier.id)
            .filter(Shipment.delay_days > 0)
            .order_by(Shipment.delay_days.desc())
            .all()
        )
        return [
            {
                "id": sh.id,
                "supplier": s.name,
                "supplier_id": sh.supplier_id,
                "delay_days": sh.delay_days,
                "status": sh.status or "delayed",
            }
            for sh, s in rows
        ]
    finally:
        db.close()


@tool
def get_at_risk_orders() -> list:
    """Returns customer orders flagged at-risk, with material name, plant, and priority."""
    db = SessionLocal()
    try:
        rows = (
            db.query(CustomerOrder, Material)
            .join(Material, CustomerOrder.material_id == Material.id)
            .filter(CustomerOrder.at_risk == True)
            .order_by(CustomerOrder.priority)
            .all()
        )
        return [
            {
                "id": o.id,
                "material": m.name,
                "material_id": o.material_id,
                "priority": o.priority or "medium",
                "plant": o.plant_id or "Unknown",
            }
            for o, m in rows
        ]
    finally:
        db.close()


@tool
def get_low_inventory() -> list:
    """Returns materials where available stock is below the safety stock threshold."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Inventory, Material)
            .join(Material, Inventory.material_id == Material.id)
            .all()
        )
        low = [
            {
                "id": i.id,
                "material": m.name,
                "material_id": i.material_id,
                "plant": m.plant_id or "Unknown",
                "available_qty": i.available_qty,
                "safety_stock": i.safety_stock or 30,
                "gap": (i.safety_stock or 30) - i.available_qty,
            }
            for i, m in rows
            if i.available_qty < (i.safety_stock or 30)
        ]
        return sorted(low, key=lambda x: x["available_qty"])
    finally:
        db.close()


@tool
def find_alternative_suppliers(material_id: str) -> list:
    """Finds qualified alternative suppliers in the same category as a material's current supplier."""
    db = SessionLocal()
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return []
        current = db.query(Supplier).filter(Supplier.id == material.supplier_id).first()
        if not current:
            return []
        alternatives = (
            db.query(Supplier)
            .filter(
                Supplier.category == current.category,
                Supplier.id != current.id,
                Supplier.risk_score < 60,
            )
            .order_by(Supplier.otif.desc())
            .limit(3)
            .all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "region": s.region,
                "otif": round(s.otif, 1),
                "risk_score": s.risk_score,
                "replaces": current.name,
            }
            for s in alternatives
        ]
    finally:
        db.close()


@tool
def create_action_plan(supplier_id: str) -> dict:
    """Creates a structured mitigation action plan for a disrupted supplier."""
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return {}
        delayed_count = (
            db.query(Shipment)
            .filter(Shipment.supplier_id == supplier_id, Shipment.delay_days > 0)
            .count()
        )
        affected_materials = (
            db.query(Material).filter(Material.supplier_id == supplier_id).limit(5).all()
        )
        at_risk_count = (
            db.query(CustomerOrder)
            .join(Material, CustomerOrder.material_id == Material.id)
            .filter(Material.supplier_id == supplier_id, CustomerOrder.at_risk == True)
            .count()
        )
    finally:
        db.close()

    return {
        "supplier": supplier.name,
        "severity": "critical" if supplier.risk_score > 85 else "high",
        "delayed_shipments": delayed_count,
        "affected_materials": [m.name for m in affected_materials],
        "at_risk_orders": at_risk_count,
        "actions": [
            f"Escalate account review with {supplier.name} within 24 hours",
            f"Activate safety stock protocol for {len(affected_materials)} affected materials",
            f"Identify and qualify alternative {supplier.category} suppliers",
            f"Notify plants of potential {delayed_count}-shipment delay",
        ],
    }


@tool
def compute_chart_data() -> dict:
    """Returns OTIF performance chart for 5 worst suppliers and delay distribution across all shipments."""
    db = SessionLocal()
    try:
        suppliers = db.query(Supplier).order_by(Supplier.otif).limit(5).all()
        shipments = db.query(Shipment).all()
    finally:
        db.close()

    otif_labels = [s.name.split()[0] for s in suppliers]
    otif_values = [round(s.otif, 1) for s in suppliers]

    buckets = {"0–3 d": 0, "4–7 d": 0, "8–14 d": 0, "15–21 d": 0, ">21 d": 0}
    for sh in shipments:
        d = sh.delay_days
        if d <= 3:      buckets["0–3 d"] += 1
        elif d <= 7:    buckets["4–7 d"] += 1
        elif d <= 14:   buckets["8–14 d"] += 1
        elif d <= 21:   buckets["15–21 d"] += 1
        else:           buckets[">21 d"] += 1

    return {
        "otif":   {"labels": otif_labels, "values": otif_values},
        "delays": {"labels": list(buckets.keys()), "values": list(buckets.values())},
    }


@tool
def get_carrier_performance() -> list:
    """Returns on-time delivery performance for every carrier: total shipments, delayed count, on-time rate, average delay days, and average freight cost."""
    db = SessionLocal()
    try:
        shipments = db.query(Shipment).all()
    finally:
        db.close()

    carriers = {}
    for sh in shipments:
        c = sh.carrier or "Unknown"
        if c not in carriers:
            carriers[c] = {"total": 0, "delayed": 0, "delay_sum": 0, "cost_sum": 0.0}
        carriers[c]["total"]     += 1
        carriers[c]["delay_sum"] += sh.delay_days or 0
        carriers[c]["cost_sum"]  += sh.freight_cost_eur or 0.0
        if (sh.delay_days or 0) > 0:
            carriers[c]["delayed"] += 1

    result = []
    for name, d in carriers.items():
        t = d["total"]
        result.append({
            "carrier":       name,
            "total":         t,
            "delayed":       d["delayed"],
            "on_time_pct":   round((t - d["delayed"]) / t * 100, 1) if t else 0,
            "avg_delay_days": round(d["delay_sum"] / t, 1) if t else 0,
            "avg_cost_eur":  round(d["cost_sum"] / t, 0) if t else 0,
            "sla_breach":    d["delayed"] > 0,
        })

    return sorted(result, key=lambda x: x["on_time_pct"])


@tool
def simulate_supplier_failure(supplier_name: str, duration_days: int = 14) -> dict:
    """Simulates the business impact if a named supplier stops delivering for a given number of days.
    Returns affected materials, at-risk orders, revenue exposure, recovery options, and alternative suppliers."""
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(
            Supplier.name.ilike(f"%{supplier_name}%")
        ).first()
        if not supplier:
            return {"error": f"Supplier '{supplier_name}' not found."}

        materials = db.query(Material).filter(Material.supplier_id == supplier.id).all()
        mat_ids   = [m.id for m in materials]

        # Orders that would be impacted (at-risk or healthy, all are affected by a full stoppage)
        affected_orders = db.query(CustomerOrder).filter(
            CustomerOrder.material_id.in_(mat_ids)
        ).all()
        at_risk_count = len(affected_orders)
        revenue_m     = round(at_risk_count * 90_000 / 1_000_000, 1)

        # Current inventory — how many days of supply do we have?
        inv_rows  = db.query(Inventory).filter(Inventory.material_id.in_(mat_ids)).all()
        total_qty = sum(i.available_qty for i in inv_rows)
        daily_demand = at_risk_count / 90 if at_risk_count else 1
        days_of_stock = round(total_qty / daily_demand, 1) if daily_demand else 0

        # Plants affected
        plants_hit = list({o.plant_id for o in affected_orders if o.plant_id})

        # Alternative suppliers in same category
        alternatives = (
            db.query(Supplier)
            .filter(
                Supplier.category == supplier.category,
                Supplier.id != supplier.id,
                Supplier.risk_score < 65,
            )
            .order_by(Supplier.otif.desc())
            .limit(3)
            .all()
        )

        alts_data = [
            {
                "name":       a.name,
                "region":     a.region,
                "otif":       round(a.otif, 1),
                "risk_score": a.risk_score,
                "onboarding_weeks": 4 if a.region == supplier.region else 8,
            }
            for a in alternatives
        ]

        # Shipments currently in transit from this supplier
        in_transit = db.query(Shipment).filter(
            Shipment.supplier_id == supplier.id,
            Shipment.delay_days == 0,
        ).count()

    finally:
        db.close()

    can_cover  = days_of_stock >= duration_days
    gap_days   = max(0, duration_days - days_of_stock)

    return {
        "supplier":          supplier.name,
        "category":          supplier.category,
        "duration_days":     duration_days,
        "affected_materials": len(materials),
        "affected_orders":   at_risk_count,
        "revenue_exposure_m": revenue_m,
        "plants_at_risk":    plants_hit,
        "days_of_stock":     days_of_stock,
        "can_cover_with_stock": can_cover,
        "stock_gap_days":    gap_days,
        "shipments_in_transit": in_transit,
        "alternative_suppliers": alts_data,
        "recovery_estimate_weeks": 2 if alts_data and alts_data[0]["region"] == supplier.region else 6,
        "recommendation": (
            f"Current stock covers {days_of_stock} days. {'No gap — buffer sufficient.' if can_cover else f'Gap of {gap_days} days — activate alternatives immediately.'}"
        ),
    }


@tool
def get_orders_by_customer(customer_name: str) -> list:
    """Returns all orders for a named customer, with material, plant, status, quantity, and delivery date."""
    db = SessionLocal()
    try:
        rows = (
            db.query(CustomerOrder, Material)
            .join(Material, CustomerOrder.material_id == Material.id)
            .filter(CustomerOrder.customer_name.ilike(f"%{customer_name}%"))
            .order_by(CustomerOrder.at_risk.desc(), CustomerOrder.priority)
            .all()
        )
        return [
            {
                "id": o.id,
                "customer": o.customer_name,
                "material": m.name,
                "quantity": o.quantity,
                "plant": o.plant_id,
                "priority": o.priority,
                "at_risk": o.at_risk,
                "expected_delivery": o.expected_delivery,
                "order_date": o.order_date,
            }
            for o, m in rows
        ]
    finally:
        db.close()


@tool
def get_shipments_by_supplier(supplier_name: str) -> list:
    """Returns all shipments from a named supplier, including origin, destination, carrier, and delay status."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Shipment, Supplier)
            .join(Supplier, Shipment.supplier_id == Supplier.id)
            .filter(Supplier.name.ilike(f"%{supplier_name}%"))
            .order_by(Shipment.delay_days.desc())
            .all()
        )
        return [
            {
                "id": sh.id,
                "supplier": s.name,
                "status": sh.status,
                "delay_days": sh.delay_days,
                "origin": sh.origin,
                "destination": sh.destination,
                "carrier": sh.carrier,
                "estimated_arrival": sh.estimated_arrival,
            }
            for sh, s in rows
        ]
    finally:
        db.close()
