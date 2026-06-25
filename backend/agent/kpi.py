"""
KPI computation for three roles.

Each function returns a dict with 4 keys (otif, ordersAtRisk, revenueExposure, inventoryHealth).
Every value carries: label, value, delta, trend.
The frontend reads `label` from the response — no hardcoded card titles in the UI.

Roles:
  executive   → OTIF · Revenue at Risk · Days of Supply · Supplier Risk Score
  operations  → Stockout Risk % · Inventory Turns · Order Cycle Time · Working Capital
  logistics   → On-Time Delivery · Delayed Shipments · Cost per Shipment · CO₂ per Shipment
"""

from datetime import date
from db import SessionLocal
from models import Supplier, Material, Shipment, CustomerOrder, Inventory


def _kpi_entry(label, value, delta, trend):
    return {"label": label, "value": value, "delta": delta, "trend": trend}


# ── Executive KPIs ─────────────────────────────────────────────────────────────
def compute_executive_kpis(customer_name=None, supplier_name=None,
                            plant_id=None, category=None):
    """OTIF · Revenue at Risk · Days of Supply · Supplier Risk Score"""
    db = SessionLocal()
    try:
        label = ""

        # ── OTIF ──────────────────────────────────────────────────────────────
        if supplier_name:
            sup = db.query(Supplier).filter(Supplier.name.ilike(f"%{supplier_name}%")).first()
            if sup:
                ships   = db.query(Shipment).filter(Shipment.supplier_id == sup.id).all()
                on_time = sum(1 for s in ships if s.delay_days == 0)
                otif    = round((on_time / len(ships) * 100) if ships else 0, 1)
                label   = f" · {supplier_name}"
            else:
                ships   = db.query(Shipment).all()
                on_time = sum(1 for s in ships if s.delay_days == 0)
                otif    = round((on_time / len(ships) * 100) if ships else 0, 1)
        elif plant_id:
            ships   = db.query(Shipment).filter(Shipment.destination == plant_id).all()
            on_time = sum(1 for s in ships if s.delay_days == 0)
            otif    = round((on_time / len(ships) * 100) if ships else 0, 1)
            label   = f" · {plant_id} plant"
        elif customer_name:
            ships   = db.query(Shipment).all()
            on_time = sum(1 for s in ships if s.delay_days == 0)
            otif    = round((on_time / len(ships) * 100) if ships else 0, 1)
            label   = f" · {customer_name}"
        elif category:
            sup_ids = [s.id for s in db.query(Supplier).filter(
                Supplier.category.ilike(f"%{category}%")
            ).all()]
            ships   = db.query(Shipment).filter(Shipment.supplier_id.in_(sup_ids)).all()
            on_time = sum(1 for s in ships if s.delay_days == 0)
            otif    = round((on_time / len(ships) * 100) if ships else 0, 1)
            label   = f" · {category}"
        else:
            ships   = db.query(Shipment).all()
            on_time = sum(1 for s in ships if s.delay_days == 0)
            otif    = round((on_time / len(ships) * 100) if ships else 0, 1)

        # ── Revenue at Risk ───────────────────────────────────────────────────
        if customer_name:
            orders = db.query(CustomerOrder).filter(
                CustomerOrder.customer_name.ilike(f"%{customer_name}%"),
                CustomerOrder.at_risk == True
            ).all()
        elif plant_id:
            orders = db.query(CustomerOrder).filter(
                CustomerOrder.plant_id == plant_id,
                CustomerOrder.at_risk == True
            ).all()
        elif supplier_name and sup:
            mat_ids = [m.id for m in db.query(Material).filter(
                Material.supplier_id == sup.id
            ).all()]
            orders  = db.query(CustomerOrder).filter(
                CustomerOrder.material_id.in_(mat_ids),
                CustomerOrder.at_risk == True
            ).all()
        elif category:
            mat_ids = [m.id for m in db.query(Material).filter(
                Material.supplier_id.in_(sup_ids)
            ).all()]
            orders  = db.query(CustomerOrder).filter(
                CustomerOrder.material_id.in_(mat_ids),
                CustomerOrder.at_risk == True
            ).all()
        else:
            orders = db.query(CustomerOrder).filter(CustomerOrder.at_risk == True).all()

        at_risk_count = len(orders)
        revenue_m     = round(at_risk_count * 90_000 / 1_000_000, 1)

        # ── Days of Supply (DOS) — median per-material coverage ──────────────
        if plant_id:
            mat_ids  = [m.id for m in db.query(Material).filter(Material.plant_id == plant_id).all()]
            inv_rows = db.query(Inventory).filter(Inventory.material_id.in_(mat_ids)).all()
        else:
            inv_rows = db.query(Inventory).all()

        # Per-material daily demand = safety_stock / 30 (proxy for monthly burn rate)
        dos_list = []
        for i in inv_rows:
            daily = (i.safety_stock or 30) / 30
            dos_list.append(i.available_qty / daily if daily else 0)
        dos_list.sort()
        dos = round(dos_list[len(dos_list) // 2], 1) if dos_list else 0  # median

        # ── Supplier Risk Score (weighted avg) ────────────────────────────────
        if category:
            sups = db.query(Supplier).filter(Supplier.category.ilike(f"%{category}%")).all()
        elif supplier_name:
            sups = [sup] if sup else db.query(Supplier).all()
        else:
            sups = db.query(Supplier).all()
        avg_risk = round(sum(s.risk_score for s in sups) / len(sups), 1) if sups else 0

    finally:
        db.close()

    otif_delta = round(otif - 90.0, 1)
    dos_trend  = "up" if dos > 30 else "down"

    return {
        "otif": _kpi_entry(
            "OTIF", f"{otif}%",
            f"{otif_delta:+.1f}% vs 90% target{label}",
            "up" if otif_delta >= 0 else "down"
        ),
        "ordersAtRisk": _kpi_entry(
            "Revenue at Risk", f"€{revenue_m}M",
            f"{at_risk_count} at-risk orders{label}",
            "down"
        ),
        "revenueExposure": _kpi_entry(
            "Days of Supply", f"{dos}d",
            f"avg inventory coverage{label}",
            dos_trend
        ),
        "inventoryHealth": _kpi_entry(
            "Supplier Risk Score", f"{avg_risk}/100",
            f"avg across {len(sups)} suppliers{label}",
            "down" if avg_risk > 60 else ("neutral" if avg_risk > 35 else "up")
        ),
    }


# ── Supply Chain Manager KPIs ──────────────────────────────────────────────────
def compute_scm_kpis(customer_name=None, supplier_name=None,
                     plant_id=None, category=None):
    """Stockout Risk % · Inventory Turns · Order Cycle Time · Working Capital"""
    db = SessionLocal()
    try:
        label = ""

        # ── Stockout Risk % ───────────────────────────────────────────────────
        if plant_id:
            mat_ids  = [m.id for m in db.query(Material).filter(Material.plant_id == plant_id).all()]
            inv_rows = db.query(Inventory).filter(Inventory.material_id.in_(mat_ids)).all()
            label    = f" · {plant_id}"
        elif category:
            sup_ids  = [s.id for s in db.query(Supplier).filter(
                Supplier.category.ilike(f"%{category}%")
            ).all()]
            mat_ids  = [m.id for m in db.query(Material).filter(
                Material.supplier_id.in_(sup_ids)
            ).all()]
            inv_rows = db.query(Inventory).filter(Inventory.material_id.in_(mat_ids)).all()
            label    = f" · {category}"
        elif supplier_name:
            sup      = db.query(Supplier).filter(Supplier.name.ilike(f"%{supplier_name}%")).first()
            mat_ids  = [m.id for m in db.query(Material).filter(
                Material.supplier_id == sup.id
            ).all()] if sup else []
            inv_rows = db.query(Inventory).filter(Inventory.material_id.in_(mat_ids)).all() if mat_ids else db.query(Inventory).all()
            label    = f" · {supplier_name}"
        else:
            inv_rows = db.query(Inventory).all()

        total_mats   = len(inv_rows)
        stockout_mats = sum(1 for i in inv_rows if i.available_qty < (i.safety_stock or 0))
        stockout_pct  = round((stockout_mats / total_mats * 100) if total_mats else 0, 1)

        # ── Inventory Turns (annualised) ──────────────────────────────────────
        total_orders = db.query(CustomerOrder).count()
        avg_inv_qty  = sum(i.available_qty for i in inv_rows) / len(inv_rows) if inv_rows else 1
        inv_turns    = round((total_orders / 365 * 52) / avg_inv_qty, 1) if avg_inv_qty else 0

        # ── Order Cycle Time (avg days from order_date to expected_delivery) ──
        if customer_name:
            sample = db.query(CustomerOrder).filter(
                CustomerOrder.customer_name.ilike(f"%{customer_name}%")
            ).limit(200).all()
            label = f" · {customer_name}"
        elif plant_id:
            sample = db.query(CustomerOrder).filter(
                CustomerOrder.plant_id == plant_id
            ).limit(200).all()
        else:
            sample = db.query(CustomerOrder).limit(200).all()

        cycle_times = []
        for o in sample:
            try:
                od = date.fromisoformat(o.order_date)
                ed = date.fromisoformat(o.expected_delivery)
                cycle_times.append((ed - od).days)
            except Exception:
                pass
        avg_cycle = round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else 0

        # ── Working Capital (inventory value estimate, EUR) ───────────────────
        # Rough: avg qty × €150 unit value × number of materials
        wc_m = round(avg_inv_qty * 150 * total_mats / 1_000_000, 1)

    finally:
        db.close()

    return {
        "otif": _kpi_entry(
            "Stockout Risk", f"{stockout_pct}%",
            f"{stockout_mats} of {total_mats} materials below safety stock{label}",
            "down" if stockout_pct > 10 else ("neutral" if stockout_pct > 3 else "up")
        ),
        "ordersAtRisk": _kpi_entry(
            "Inventory Turns", f"{inv_turns}x",
            f"annualised{label}",
            "up" if inv_turns > 4 else "down"
        ),
        "revenueExposure": _kpi_entry(
            "Order Cycle Time", f"{avg_cycle}d",
            f"avg order-to-delivery{label}",
            "up" if avg_cycle < 20 else "down"
        ),
        "inventoryHealth": _kpi_entry(
            "Working Capital", f"€{wc_m}M",
            f"est. inventory value{label}",
            "neutral"
        ),
    }


# ── Logistics Manager KPIs ─────────────────────────────────────────────────────
def compute_logistics_kpis(supplier_name=None, plant_id=None):
    """On-Time Delivery · Delayed Shipments · Cost per Shipment · CO₂ per Shipment"""
    db = SessionLocal()
    try:
        q = db.query(Shipment)
        if supplier_name:
            sup = db.query(Supplier).filter(Supplier.name.ilike(f"%{supplier_name}%")).first()
            if sup:
                q = q.filter(Shipment.supplier_id == sup.id)
        if plant_id:
            q = q.filter(Shipment.destination == plant_id)
        ships = q.all()

        total      = len(ships)
        delayed    = sum(1 for s in ships if s.delay_days > 0)
        on_time_pct = round(((total - delayed) / total * 100) if total else 0, 1)
        avg_cost   = round(sum(s.freight_cost_eur or 0 for s in ships) / total, 0) if total else 0
        avg_co2    = round(sum(s.co2_kg or 0 for s in ships) / total, 1) if total else 0
        avg_delay  = round(sum(s.delay_days for s in ships) / total, 1) if total else 0

        modes = {}
        for s in ships:
            m = s.transport_mode or "Road"
            modes[m] = modes.get(m, 0) + 1
        top_mode = max(modes, key=modes.get) if modes else "Road"

    finally:
        db.close()

    otif_delta = round(on_time_pct - 95.0, 1)

    return {
        "otif": _kpi_entry(
            "On-Time Delivery", f"{on_time_pct}%",
            f"{otif_delta:+.1f}% vs 95% SLA target",
            "up" if otif_delta >= 0 else "down"
        ),
        "ordersAtRisk": _kpi_entry(
            "Delayed Shipments", str(delayed),
            f"{delayed} of {total} shipments delayed · avg {avg_delay}d",
            "down" if delayed > 0 else "neutral"
        ),
        "revenueExposure": _kpi_entry(
            "Cost per Shipment", f"€{int(avg_cost):,}",
            f"avg freight cost · {top_mode} dominant",
            "neutral"
        ),
        "inventoryHealth": _kpi_entry(
            "CO₂ per Shipment", f"{avg_co2}kg",
            f"avg emissions per consignment",
            "neutral"
        ),
    }


# Backwards-compatible alias (used by graph.py for executive role default)
def compute_kpis(customer_name=None, supplier_name=None, plant_id=None, category=None):
    return compute_executive_kpis(customer_name, supplier_name, plant_id, category)
