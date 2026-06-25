from sqlalchemy import Column, String, Integer, Boolean, Float
from db import Base


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True)
    name = Column(String)
    region = Column(String)
    category = Column(String)
    otif = Column(Float)
    risk_score = Column(Integer)


class Material(Base):
    __tablename__ = "materials"
    id = Column(String, primary_key=True)
    name = Column(String)
    supplier_id = Column(String)
    category = Column(String)
    plant_id = Column(String)


class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(String, primary_key=True)
    supplier_id = Column(String)
    delay_days = Column(Integer)
    status = Column(String)             # on_time | delayed | critical_delay
    origin = Column(String)             # city / country of dispatch
    destination = Column(String)        # plant receiving the shipment
    estimated_arrival = Column(String)  # ISO date string
    carrier = Column(String)            # logistics company
    transport_mode = Column(String)     # Air | Sea | Road | Rail
    freight_cost_eur = Column(Float)    # total freight cost in EUR
    weight_kg = Column(Float)           # cargo weight
    co2_kg = Column(Float)              # estimated CO2 emissions in kg


class CustomerOrder(Base):
    __tablename__ = "customer_orders"
    id = Column(String, primary_key=True)
    material_id = Column(String)
    customer_id = Column(String)     # e.g. "c1"
    customer_name = Column(String)   # e.g. "BMW Group"
    quantity = Column(Integer)       # units ordered
    order_date = Column(String)      # ISO date string
    expected_delivery = Column(String)  # ISO date string
    at_risk = Column(Boolean)
    priority = Column(String)        # high | medium | low
    plant_id = Column(String)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True)
    material_id = Column(String)
    available_qty = Column(Integer)
    safety_stock = Column(Integer)
