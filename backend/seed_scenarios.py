"""
Expanded supply chain seed
50 suppliers · 500 materials · 500 shipments · ~2350 orders · 60 customers · 500 inventory records

Plant risk profiles (intentional, emerge from supplier concentration):
  Prague  — CRISIS   : Electronics/Semiconductor cluster, Foxconn + ChipTech crisis
  Munich  — HIGH     : Mixed electronics + APAC semiconductor exposure
  Berlin  — MODERATE : Automotive components + connectors, moderate delays
  Warsaw  — LOW      : Raw materials + mechanical, mostly reliable
  Vienna  — HEALTHY  : Chemical/specialty + packaging, best OTIF in the network
"""

import sys, os, random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from db import SessionLocal, engine, Base
from models import Supplier, Material, Shipment, CustomerOrder, Inventory

random.seed(42)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Tables recreated.")
db = SessionLocal()

TODAY = date(2026, 6, 19)
def future(days): return (TODAY + timedelta(days=max(1, days))).isoformat()
def past(days):   return (TODAY - timedelta(days=max(1, days))).isoformat()

PLANTS = ["Prague", "Munich", "Berlin", "Warsaw", "Vienna"]

CARRIERS = [
    "DHL Freight", "DB Schenker", "Kuehne+Nagel", "DSV Logistics",
    "Rhenus Logistics", "Hellmann Worldwide", "Dachser SE", "CEVA Logistics",
    "Panalpina", "Geodis", "XPO Logistics", "Maersk Logistics",
    "MSC Mediterranean", "Hapag-Lloyd", "CMA CGM Logistics",
]

# CO2 factor (kg/ton-km), distance (km), cost range (EUR)
TRANSPORT_CONFIG = {
    "Air":  {"co2": 0.600, "dist": 8000,  "cost": (7000, 14000)},
    "Sea":  {"co2": 0.015, "dist": 18000, "cost": (1800,  5500)},
    "Road": {"co2": 0.090, "dist":  800,  "cost": ( 350,   900)},
    "Rail": {"co2": 0.020, "dist": 1500,  "cost": ( 500,  1200)},
}

# Additive modifier to at-risk probability by plant
PLANT_RISK_MOD = {
    "Prague": +0.18,
    "Munich": +0.08,
    "Berlin":  0.00,
    "Warsaw": -0.08,
    "Vienna": -0.18,
}

# ── Supplier definitions (50) ──────────────────────────────────────────────────
# (id, name, region, category, otif, risk_score, transport_mode, origin_city, primary_plants)
SUPPLIER_DEFS = [
    # Electronics — varied risk
    ("s01","Foxconn Technology Group",   "Asia-Pacific","Electronics",          72,88,"Air", "Shenzhen, China",               ["Prague","Munich"]),
    ("s02","Pegatron Corporation",        "Asia-Pacific","Electronics",          79,71,"Air", "Zhongli, Taiwan",                ["Prague","Munich","Berlin"]),
    ("s03","Flextronics International",   "Asia-Pacific","Electronics",          84,65,"Sea", "Singapore",                     ["Munich","Berlin"]),
    ("s04","Jabil Circuit",               "North America","Electronics",         88,55,"Road","St. Petersburg, USA",           ["Munich","Vienna"]),
    ("s05","Celestica Inc",               "North America","Electronics",         91,42,"Road","Toronto, Canada",                ["Vienna","Warsaw"]),
    ("s06","BYD Electronic",              "Asia-Pacific","Electronics",          76,78,"Air", "Shenzhen, China",               ["Prague","Berlin"]),
    ("s07","Wistron Corporation",         "Asia-Pacific","Electronics",          82,67,"Air", "Taoyuan, Taiwan",                ["Prague","Munich"]),
    ("s08","Compal Electronics",          "Asia-Pacific","Electronics",          85,59,"Sea", "Taipei, Taiwan",                 ["Berlin","Warsaw"]),
    ("s09","FastParts Ltd",               "Asia-Pacific","Electronics",          68,85,"Air", "Guangzhou, China",              ["Prague"]),
    ("s10","EuroComp GmbH",               "Europe",      "Electronics",          74,72,"Road","Nuremberg, Germany",            ["Prague","Munich"]),
    # Semiconductors
    ("s11","TSMC",                        "Asia-Pacific","Semiconductors",       94,82,"Air", "Hsinchu, Taiwan",               ["Munich","Berlin"]),
    ("s12","Samsung Semiconductor",       "Asia-Pacific","Semiconductors",       91,74,"Air", "Hwaseong, South Korea",         ["Prague","Munich"]),
    ("s13","Infineon Technologies",       "Europe",      "Semiconductors",       89,45,"Road","Munich, Germany",               ["Munich","Vienna"]),
    ("s14","NXP Semiconductors",          "Europe",      "Semiconductors",       87,50,"Road","Eindhoven, Netherlands",        ["Berlin","Vienna"]),
    ("s15","STMicroelectronics",          "Europe",      "Semiconductors",       86,48,"Rail","Geneva, Switzerland",           ["Berlin","Warsaw"]),
    ("s16","Renesas Electronics",         "Asia-Pacific","Semiconductors",       83,62,"Air", "Tokyo, Japan",                  ["Munich","Prague"]),
    ("s17","Microchip Technology",        "North America","Semiconductors",      92,38,"Road","Chandler, USA",                 ["Vienna","Munich"]),
    ("s18","ChipTech Asia",               "Asia-Pacific","Semiconductors",       61,92,"Air", "Shanghai, China",               ["Prague"]),
    # Mechanical
    ("s19","SKF Group",                   "Europe",      "Mechanical",           94,22,"Road","Gothenburg, Sweden",            ["Warsaw","Munich","Vienna"]),
    ("s20","Schaeffler Group",            "Europe",      "Mechanical",           93,25,"Road","Herzogenaurach, Germany",       ["Munich","Warsaw","Berlin"]),
    ("s21","Parker Hannifin",             "North America","Mechanical",          91,30,"Road","Cleveland, USA",                ["Vienna","Munich"]),
    ("s22","Eaton Corporation",           "North America","Mechanical",          90,32,"Road","Dublin, Ireland",               ["Warsaw","Berlin"]),
    ("s23","Dana Incorporated",           "North America","Mechanical",          89,35,"Road","Maumee, USA",                   ["Warsaw","Vienna"]),
    ("s24","Timken Company",              "North America","Mechanical",          93,20,"Road","North Canton, USA",             ["Vienna","Warsaw"]),
    ("s25","MechParts Eastern",           "Asia-Pacific","Mechanical",           75,70,"Sea", "Qingdao, China",                ["Prague","Berlin"]),
    ("s26","PrecisionParts Europe",       "Europe",      "Mechanical",           88,40,"Rail","Wroclaw, Poland",               ["Berlin","Warsaw"]),
    # Raw Materials
    ("s27","Novelis Inc",                 "North America","Raw Materials",       96,15,"Sea", "Atlanta, USA",                  ["Warsaw","Munich"]),
    ("s28","Aurubis AG",                  "Europe",      "Raw Materials",        95,18,"Rail","Hamburg, Germany",              ["Warsaw","Berlin"]),
    ("s29","ThyssenKrupp Steel",          "Europe",      "Raw Materials",        92,28,"Rail","Duisburg, Germany",             ["Munich","Berlin","Warsaw"]),
    ("s30","SteelWorks Central",          "Europe",      "Raw Materials",        78,63,"Road","Katowice, Poland",              ["Prague","Munich"]),
    ("s31","Alcoa Corporation",           "North America","Raw Materials",       94,20,"Sea", "Pittsburgh, USA",               ["Warsaw","Vienna"]),
    ("s32","Glencore Metals",             "Europe",      "Raw Materials",        91,30,"Rail","Baar, Switzerland",             ["Berlin","Warsaw"]),
    # Chemical & Specialty
    ("s33","BASF SE",                     "Europe",      "Chemical & Specialty", 97,12,"Road","Ludwigshafen, Germany",        ["Vienna","Munich","Warsaw"]),
    ("s34","Covestro AG",                 "Europe",      "Chemical & Specialty", 96,14,"Road","Leverkusen, Germany",          ["Vienna","Berlin"]),
    ("s35","Lanxess AG",                  "Europe",      "Chemical & Specialty", 94,19,"Road","Cologne, Germany",             ["Warsaw","Vienna"]),
    ("s36","PlasticTech Industries",      "Asia-Pacific","Chemical & Specialty", 71,79,"Sea", "Ningbo, China",                ["Prague","Berlin"]),
    # Automotive Components
    ("s37","Valeo SE",                    "Europe",      "Automotive Components",91,32,"Road","Paris, France",                ["Munich","Prague"]),
    ("s38","Aptiv PLC",                   "Europe",      "Automotive Components",90,35,"Road","Dublin, Ireland",              ["Berlin","Munich"]),
    ("s39","Lear Corporation",            "North America","Automotive Components",89,37,"Road","Southfield, USA",             ["Vienna","Warsaw"]),
    ("s40","Denso Corporation",           "Asia-Pacific","Automotive Components",93,42,"Sea", "Kariya, Japan",                ["Munich","Berlin"]),
    ("s41","Aisin Corporation",           "Asia-Pacific","Automotive Components",92,38,"Sea", "Kariya, Japan",                ["Vienna","Warsaw"]),
    ("s42","BorgWarner Inc",              "North America","Automotive Components",91,33,"Road","Auburn Hills, USA",           ["Berlin","Munich"]),
    ("s43","Magna International",         "North America","Automotive Components",93,30,"Road","Aurora, Canada",              ["Warsaw","Vienna"]),
    ("s44","LogisTech Components",        "Asia-Pacific","Automotive Components",69,83,"Air", "Ho Chi Minh, Vietnam",        ["Prague"]),
    # Connectors & Sensors
    ("s45","TE Connectivity",             "Europe",      "Connectors & Sensors", 95,20,"Road","Schaffhausen, Switzerland",    ["Berlin","Munich","Vienna"]),
    ("s46","Amphenol Corporation",        "North America","Connectors & Sensors",94,22,"Road","Wallingford, USA",            ["Munich","Vienna"]),
    ("s47","Molex LLC",                   "North America","Connectors & Sensors",93,24,"Road","Lisle, USA",                  ["Berlin","Warsaw"]),
    ("s48","Sensata Technologies",        "North America","Connectors & Sensors",92,26,"Road","Attleboro, USA",              ["Vienna","Munich"]),
    ("s49","Yazaki Corporation",          "Asia-Pacific","Connectors & Sensors", 88,44,"Air", "Miyazu, Japan",               ["Prague","Munich"]),
    # Packaging
    ("s50","Smurfit Kappa",               "Europe",      "Packaging",            97,10,"Road","Dublin, Ireland",              ["Prague","Munich","Berlin","Warsaw","Vienna"]),
]

# ── Customers (60) ────────────────────────────────────────────────────────────
CUSTOMERS = [
    # German Automotive OEM (big → 50 orders each)
    ("c01","BMW Group"),               ("c02","Volkswagen AG"),
    ("c03","Mercedes-Benz Group"),     ("c04","Audi AG"),
    ("c05","Porsche AG"),
    # German Tier 1
    ("c06","Robert Bosch GmbH"),       ("c07","Continental AG"),
    ("c08","ZF Friedrichshafen"),      ("c09","Schaeffler Technologies"),
    ("c10","MAHLE Group"),
    # European OEM
    ("c11","Stellantis NV"),           ("c12","Renault Group"),
    ("c13","Volvo Cars"),              ("c14","Volvo Group"),
    ("c15","Daimler Truck AG"),
    # Asian OEM (mid-tier → 40 orders)
    ("c16","Toyota Motor Corporation"),("c17","Honda Motor Company"),
    ("c18","Hyundai Motor Company"),   ("c19","Kia Corporation"),
    ("c20","Nissan Motor Company"),
    # North American OEM
    ("c21","Ford Motor Company"),      ("c22","General Motors"),
    ("c23","Tesla Inc"),               ("c24","Rivian Automotive"),
    ("c25","Lucid Motors"),
    # Industrial & Technology
    ("c26","Siemens AG"),              ("c27","ABB Ltd"),
    ("c28","Schneider Electric"),      ("c29","Honeywell International"),
    ("c30","Emerson Electric"),
    # Aerospace & Defense
    ("c31","Airbus SE"),               ("c32","Leonardo SpA"),
    ("c33","Thales Group"),            ("c34","MTU Aero Engines"),
    ("c35","Diehl Aviation"),
    # Energy
    ("c36","Siemens Energy"),          ("c37","Vestas Wind Systems"),
    ("c38","GE Vernova"),              ("c39","Enel Group"),
    ("c40","RWE AG"),
    # Consumer Electronics (niche → 30 orders)
    ("c41","Philips Electronics"),     ("c42","BSH Home Appliances"),
    ("c43","Miele & Cie"),             ("c44","Electrolux AB"),
    ("c45","Whirlpool Corporation"),
    # Medical Devices
    ("c46","Fresenius Medical Care"),  ("c47","B. Braun Melsungen"),
    ("c48","Ottobock SE"),             ("c49","Carl Zeiss AG"),
    ("c50","Sartorius AG"),
    # Rail & Transport
    ("c51","Alstom SA"),               ("c52","Siemens Mobility"),
    ("c53","Knorr-Bremse AG"),         ("c54","Wabtec Corporation"),
    ("c55","CRRC Corporation"),
    # Machinery & Equipment
    ("c56","Kion Group"),              ("c57","TRUMPF GmbH"),
    ("c58","Liebherr Group"),          ("c59","Krones AG"),
    ("c60","Körber AG"),
]

# ── Material name templates (10 per category) ──────────────────────────────────
MAT_TEMPLATES = {
    "Electronics": [
        ("PCB","Main Controller Board"),    ("PSU","Power Supply Unit"),
        ("DSP","Signal Processor Module"),  ("LCD","Display Driver Board"),
        ("ADC","Analog-Digital Converter"), ("DAC","Digital-Analog Converter"),
        ("EMI","EMI Filter Assembly"),      ("RFM","RF Communication Module"),
        ("OPT","Optical Interface Card"),   ("PWM","Power Management IC"),
    ],
    "Semiconductors": [
        ("MCU","Microcontroller Unit"),     ("FPG","Field Programmable Gate Array"),
        ("DRM","Dynamic RAM Module"),       ("NND","NAND Flash Memory"),
        ("GPU","Graphics Processing Unit"), ("TPU","Tensor Processing Unit"),
        ("SoC","System-on-Chip"),           ("DSP","Digital Signal Processor"),
        ("AHD","High-Speed ADC"),           ("DPC","Precision DAC"),
    ],
    "Mechanical": [
        ("BRG","Deep Groove Ball Bearing"), ("GBX","Helical Gear Box"),
        ("HSG","Aluminum Housing"),         ("SFT","Drive Shaft Assembly"),
        ("CPL","Flexible Coupling"),        ("SPR","Compression Spring Set"),
        ("VLV","Control Valve"),            ("ACT","Linear Actuator"),
        ("SLR","Precision Slide Rail"),     ("CLT","Collet Chuck Module"),
    ],
    "Raw Materials": [
        ("ALU","Aluminum Alloy Sheet 6061-T6"), ("COP","Copper Rod C11000"),
        ("STL","High-Strength Steel DP980"),    ("TIT","Titanium Plate Grade 5"),
        ("NIK","Nickel Strip N200"),             ("ZNC","Zinc Die-Cast Blank"),
        ("SIL","Silicon Wafer 300mm"),           ("MAG","Magnesium Alloy Ingot"),
        ("BRS","Brass Bar C26000"),              ("INC","Inconel 718 Billet"),
    ],
    "Chemical & Specialty": [
        ("ADH","Structural Adhesive"),      ("LUB","High-Temperature Lubricant"),
        ("COA","Protective Coating"),       ("SOL","Cleaning Solvent"),
        ("PLY","Polymer Compound"),         ("SLT","Electrolyte Solution"),
        ("SLN","Solder Paste"),             ("FLX","Flux Remover"),
        ("THM","Thermal Interface Material"),("ENC","Encapsulation Resin"),
    ],
    "Automotive Components": [
        ("THR","Throttle Body Assembly"),   ("TRQ","Torque Converter"),
        ("ABS","ABS Brake Module"),         ("STR","Steering Column"),
        ("CLS","Clutch Assembly"),          ("DRV","Drive Axle"),
        ("SUS","Suspension Control Arm"),   ("FUL","Fuel Injection Rail"),
        ("EXH","Exhaust Manifold"),         ("TCU","Transmission Control Unit"),
    ],
    "Connectors & Sensors": [
        ("CON","Industrial Connector D-Sub"),("CAB","High-Flex Cable Assembly"),
        ("SEN","Pressure Sensor"),           ("HAR","Wire Harness"),
        ("PLG","Quick-Connect Plug"),        ("SKT","Socket Assembly"),
        ("SCM","Signal Conditioning Module"),("ANT","Embedded Antenna"),
        ("TMP","Temperature Sensor"),        ("POS","Position Encoder"),
    ],
    "Packaging": [
        ("BOX","Corrugated Shipping Box"),  ("PLT","Euro Pallet"),
        ("BAG","Protective Poly Bag"),      ("FLM","Stretch Wrap Film"),
        ("TRP","Transport Dunnage"),        ("LAB","Shipping Label Set"),
        ("INS","Anti-Static Insert"),       ("PAD","Foam Padding"),
        ("BOT","Bottle Packaging"),         ("TUB","Industrial Tube Container"),
    ],
}

# ── Build suppliers ────────────────────────────────────────────────────────────
suppliers = [
    Supplier(id=row[0], name=row[1], region=row[2], category=row[3],
             otif=float(row[4]), risk_score=row[5])
    for row in SUPPLIER_DEFS
]
db.add_all(suppliers)

sup_row_by_id = {row[0]: row for row in SUPPLIER_DEFS}

# ── Build materials (10 per supplier = 500) ────────────────────────────────────
materials = []
mid_ctr   = 1

for row in SUPPLIER_DEFS:
    s_id, _, _, category, _, _, _, _, primary_plants = row
    templates = MAT_TEMPLATES.get(category, [("GEN", "General Component")] * 10)

    for j, (prefix, desc) in enumerate(templates[:10]):
        n = len(primary_plants)
        if n >= 5:
            plant = PLANTS[j % 5]
        elif n == 3:
            plant = primary_plants[0] if j < 4 else (primary_plants[1] if j < 7 else primary_plants[2])
        elif n == 2:
            plant = primary_plants[0] if j < 6 else primary_plants[1]
        else:
            plant = primary_plants[0]

        materials.append(Material(
            id=f"m{mid_ctr:04d}",
            name=f"{prefix}-{mid_ctr:04d} {desc}",
            supplier_id=s_id,
            category=category,
            plant_id=plant,
        ))
        mid_ctr += 1

db.add_all(materials)

# ── Build shipments (10 per supplier = 500) ────────────────────────────────────
shipments = []
sh_ctr    = 1

for row in SUPPLIER_DEFS:
    s_id, _, _, _, _, risk_score, mode, origin, primary_plants = row
    tc = TRANSPORT_CONFIG[mode]

    n = len(primary_plants)
    if n >= 5:
        dests = (PLANTS * 2)[:10]
    elif n == 3:
        dests = [primary_plants[0]] * 4 + [primary_plants[1]] * 3 + [primary_plants[2]] * 3
    elif n == 2:
        dests = [primary_plants[0]] * 6 + [primary_plants[1]] * 4
    else:
        dests = [primary_plants[0]] * 10

    random.shuffle(dests)

    for dest in dests:
        p_delay    = risk_score / 100 * 0.60
        is_delayed = random.random() < p_delay

        if is_delayed:
            if risk_score > 80:
                delay, status = random.randint(7, 16), "critical_delay"
            elif risk_score > 60:
                delay, status = random.randint(4, 9),  "delayed"
            else:
                delay, status = random.randint(2, 5),  "delayed"
        else:
            delay, status = 0, "on_time"

        weight = round(random.uniform(100, 2500), 1)
        co2    = round(tc["co2"] * weight / 1000 * tc["dist"], 1)
        cost   = round(random.uniform(*tc["cost"]) * random.uniform(0.85, 1.25), 2)
        if delay > 0:
            cost = round(cost * random.uniform(1.10, 1.25), 2)

        shipments.append(Shipment(
            id=f"sh{sh_ctr:04d}",
            supplier_id=s_id,
            delay_days=delay,
            status=status,
            origin=origin,
            destination=dest,
            estimated_arrival=future(delay + random.randint(1, 6)),
            carrier=random.choice(CARRIERS),
            transport_mode=mode,
            freight_cost_eur=cost,
            weight_kg=weight,
            co2_kg=co2,
        ))
        sh_ctr += 1

db.add_all(shipments)

# ── Build orders (~2350) ───────────────────────────────────────────────────────
# Big OEM (c01-c15): 50 orders each
# Mid-tier (c16-c40): 40 orders each
# Niche (c41-c60): 30 orders each
# Total: 15×50 + 25×40 + 20×30 = 750 + 1000 + 600 = 2350

orders      = []
oid_ctr     = 1
at_risk_ctr = 0

def n_orders_for(c_idx):
    if c_idx < 15: return 50
    if c_idx < 40: return 40
    return 30

for c_idx, (cust_id, cust_name) in enumerate(CUSTOMERS):
    n        = n_orders_for(c_idx)
    mat_pool = materials[:]
    random.shuffle(mat_pool)

    for m_obj in mat_pool[:n]:
        row        = sup_row_by_id[m_obj.supplier_id]
        risk_score = row[5]
        plant      = m_obj.plant_id

        p_risk  = min(0.95, max(0.02, risk_score / 100 * 0.75 + PLANT_RISK_MOD.get(plant, 0)))
        is_ar   = random.random() < p_risk

        if is_ar:
            at_risk_ctr += 1
            priority = "high" if risk_score > 75 else "medium"
            delivery = future(random.randint(1, 8))
        else:
            priority = random.choices(["low", "medium"], weights=[3, 1])[0]
            delivery = future(random.randint(10, 45))

        orders.append(CustomerOrder(
            id=f"o{oid_ctr:05d}",
            material_id=m_obj.id,
            customer_id=cust_id,
            customer_name=cust_name,
            quantity=random.randint(5, 1000),
            order_date=past(random.randint(3, 90)),
            expected_delivery=delivery,
            at_risk=is_ar,
            priority=priority,
            plant_id=plant,
        ))
        oid_ctr += 1

db.add_all(orders)

# ── Build inventory (one record per material = 500) ────────────────────────────
inventory = []
iid_ctr   = 1

for m_obj in materials:
    row        = sup_row_by_id[m_obj.supplier_id]
    risk_score = row[5]
    plant      = m_obj.plant_id
    plant_adj  = PLANT_RISK_MOD.get(plant, 0)

    # Riskier supplier at riskier plant → lower available stock
    base_qty = int(200 - risk_score * 1.4)       # risk=92→71  risk=10→186
    plant_mod = int(plant_adj * -150)             # Prague→-27  Vienna→+27
    qty       = max(0, base_qty + plant_mod + random.randint(-25, 25))
    ss        = max(20, int(25 + risk_score * 0.35))  # safety stock

    inventory.append(Inventory(
        id=f"inv{iid_ctr:04d}",
        material_id=m_obj.id,
        available_qty=qty,
        safety_stock=ss,
    ))
    iid_ctr += 1

db.add_all(inventory)
db.commit()
db.close()

print(f"\nSeeded:")
print(f"  Suppliers : {len(suppliers)}")
print(f"  Materials : {len(materials)}")
print(f"  Shipments : {len(shipments)}")
print(f"  Orders    : {len(orders)}  ({at_risk_ctr} at-risk, {round(at_risk_ctr/len(orders)*100,1)}%)")
print(f"  Inventory : {len(inventory)}")
print(f"  Customers : {len(CUSTOMERS)}")
print("Done ✅")
