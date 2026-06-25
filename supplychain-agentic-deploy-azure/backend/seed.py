import random
from db import SessionLocal, engine, Base
from models import Supplier, Material, Shipment, CustomerOrder, Inventory

Base.metadata.create_all(bind=engine)
db = SessionLocal()

suppliers = []
for i in range(25):
    s = Supplier(id=f"s{i}", name=f"Supplier {i}", region="EU",
                 otif=random.uniform(70, 95), risk_score=random.randint(30, 95))
    db.add(s)
    suppliers.append(s)

materials = []
for i in range(150):
    m = Material(id=f"m{i}", name=f"Material {i}", supplier_id=random.choice(suppliers).id)
    db.add(m)
    materials.append(m)

for i in range(120):
    db.add(Shipment(id=f"sh{i}", supplier_id=random.choice(suppliers).id,
                    delay_days=random.choice([0, 5, 14])))

for i in range(80):
    db.add(CustomerOrder(id=f"o{i}", material_id=random.choice(materials).id,
                         at_risk=random.choice([True, False])))

for i in range(200):
    db.add(Inventory(id=f"inv{i}", material_id=random.choice(materials).id,
                     available_qty=random.randint(10, 100)))

db.commit()
db.close()