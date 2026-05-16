import os
import json
import random
import csv
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ─── Deep distractor directory structure ───────────────────────────────────────
dirs = [
    "data/raw/inbound",
    "data/raw/outbound",
    "data/processed",
    "data/archive/2023/Q3",
    "data/archive/2023/Q4",
    "data/archive/2024/Q1",
    "reports/finance",
    "reports/ops",
    "config/carriers",
    "config/warehouses",
    "scripts",
    "logs",
    "tmp/staging",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files (irrelevant but realistic) ─────────────────────────────
(workspace / "config/carriers/fedex_rates_2024.csv").write_text(
    "carrier,zone,rate_per_kg\nFedEx,1,3.20\nFedEx,2,4.10\nFedEx,3,5.80\n"
)
(workspace / "config/carriers/dhl_rates_2024.csv").write_text(
    "carrier,zone,rate_per_kg\nDHL,1,2.90\nDHL,2,3.75\nDHL,3,5.20\n"
)
(workspace / "config/warehouses/eu_hubs.json").write_text(json.dumps({
    "hubs": [
        {"id": "AMS01", "city": "Amsterdam", "capacity_cbm": 5000},
        {"id": "RTM02", "city": "Rotterdam", "capacity_cbm": 8000},
        {"id": "HAM03", "city": "Hamburg", "capacity_cbm": 6500},
    ]
}, indent=2))
(workspace / "config/warehouses/apac_cfs.json").write_text(json.dumps({
    "cfs_stations": [
        {"id": "SHA-CFS1", "city": "Shanghai", "weekly_cutoff": "Friday 18:00"},
        {"id": "SZX-CFS1", "city": "Shenzhen", "weekly_cutoff": "Thursday 15:00"},
        {"id": "HKG-CFS1", "city": "Hong Kong", "weekly_cutoff": "Wednesday 12:00"},
    ]
}, indent=2))
(workspace / "logs/freight_errors_2024.log").write_text(
    "2024-03-12 ERROR shipment SH-2041 missing CBM declaration\n"
    "2024-03-15 WARN  shipment SH-2055 weight exceeds manifest\n"
    "2024-04-01 ERROR customs hold on SH-2071 Rotterdam\n"
)
(workspace / "data/archive/2023/Q4/q4_summary.txt").write_text(
    "Q4 2023 Total Shipments: 412\nDirect: 189\nConsolidated: 223\nTotal Spend: USD 1,842,000\n"
)
(workspace / "data/archive/2024/Q1/q1_kpis.txt").write_text(
    "On-time delivery: 91.4%\nDamage claims: 2.1%\nConsolidation ratio: 54.3%\n"
)
(workspace / "reports/finance/budget_2024.txt").write_text(
    "Annual freight budget: USD 2,100,000\nConsolidation savings target: 18%\n"
)
(workspace / "reports/ops/carrier_performance.txt").write_text(
    "Carrier\tOn-Time%\tDamage%\nMaersk\t93.1\t1.2\nEvergreen\t89.4\t2.0\nCOSCO\t91.7\t1.8\n"
)
(workspace / "tmp/staging/manifest_draft.txt").write_text(
    "DRAFT - DO NOT USE\nShipment staging manifest incomplete\n"
)
(workspace / "logs/system.log").write_text(
    "2024-06-01 INFO  Consolidation engine started\n"
    "2024-06-01 INFO  Loaded 14 pending shipments\n"
    "2024-06-01 WARN  3 shipments missing supplier confirmation\n"
)

# ─── THE CORE PROBLEM: messy pending shipments dataset ───────────────────────
# Intentionally messy: mixed units, missing fields, inconsistent naming
shipments = [
    # id, origin_city, origin_country, dest_hub, weight_kg, volume_cbm, declared_value_usd, supplier, notes
    {"id": "PO-4421", "origin": "Shanghai", "country": "CN", "dest_hub": "AMS01",
     "weight_kg": 320,  "volume_cbm": 1.8,  "value_usd": 18500, "supplier": "SinoTech Ltd",
     "notes": "Electronics components - capacitors"},
    {"id": "PO-4422", "origin": "Shenzhen", "country": "CN", "dest_hub": "AMS01",
     "weight_kg": 510,  "volume_cbm": 2.9,  "value_usd": 42000, "supplier": "SinoTech Ltd",
     "notes": "PCB assemblies"},
    {"id": "PO-4423", "origin": "Shanghai",  "country": "CN", "dest_hub": "AMS01",
     "weight_kg": 185,  "volume_cbm": 0.9,  "value_usd": 9200,  "supplier": "EastComp Co",
     "notes": "Cables and connectors"},
    {"id": "PO-4424", "origin": "Hong Kong", "country": "HK", "dest_hub": "RTM02",
     "weight_kg": 740,  "volume_cbm": 4.1,  "value_usd": 65000, "supplier": "HK Electronics",
     "notes": "Display panels"},
    {"id": "PO-4425", "origin": "Shenzhen", "country": "CN", "dest_hub": "RTM02",
     "weight_kg": 290,  "volume_cbm": 1.6,  "value_usd": 22000, "supplier": "EastComp Co",
     "notes": "Power supplies"},
    {"id": "PO-4426", "origin": "Shanghai",  "country": "CN", "dest_hub": "AMS01",
     "weight_kg": 95,   "volume_cbm": 0.5,  "value_usd": 4100,  "supplier": "MicroParts SZ",
     "notes": "Microcontrollers - small parcel"},
    {"id": "PO-4427", "origin": "Osaka",    "country": "JP", "dest_hub": "HAM03",
     "weight_kg": 420,  "volume_cbm": 2.3,  "value_usd": 38000, "supplier": "Nippon Components",
     "notes": "Sensors and actuators"},
    {"id": "PO-4428", "origin": "Osaka",    "country": "JP", "dest_hub": "HAM03",
     "weight_kg": 310,  "volume_cbm": 1.7,  "value_usd": 27500, "supplier": "Nippon Components",
     "notes": "Motor drivers"},
    {"id": "PO-4429", "origin": "Shenzhen", "country": "CN", "dest_hub": "RTM02",
     "weight_kg": 880,  "volume_cbm": 5.2,  "value_usd": 71000, "supplier": "HK Electronics",
     "notes": "LED modules - high volume"},
    {"id": "PO-4430", "origin": "Shanghai",  "country": "CN", "dest_hub": "AMS01",
     "weight_kg": 150,  "volume_cbm": 0.8,  "value_usd": 6800,  "supplier": "SinoTech Ltd",
     "notes": "Heat sinks"},
    {"id": "PO-4431", "origin": "Guangzhou", "country": "CN", "dest_hub": "AMS01",
     "weight_kg": 230,  "volume_cbm": 1.3,  "value_usd": 14200, "supplier": "GZ Precision",
     "notes": "CNC machined parts"},
    {"id": "PO-4432", "origin": "Shenzhen", "country": "CN", "dest_hub": "HAM03",
     "weight_kg": 560,  "volume_cbm": 3.1,  "value_usd": 49000, "supplier": "MicroParts SZ",
     "notes": "Embedded modules"},
    {"id": "PO-4433", "origin": "Osaka",    "country": "JP", "dest_hub": "HAM03",
     "weight_kg": 75,   "volume_cbm": 0.4,  "value_usd": 3900,  "supplier": "Nippon Components",
     "notes": "Prototype parts - urgent"},
    {"id": "PO-4434", "origin": "Guangzhou", "country": "CN", "dest_hub": "RTM02",
     "weight_kg": 410,  "volume_cbm": 2.2,  "value_usd": 31000, "supplier": "GZ Precision",
     "notes": "Injection molded housings"},
]

with open(workspace / "data/raw/inbound/pending_shipments.json", "w") as f:
    json.dump({"generated": "2024-06-01", "status": "pending_review", "shipments": shipments}, f, indent=2)

# Also write a CSV version (redundant / distractor)
with open(workspace / "data/raw/inbound/pending_shipments_legacy.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id","origin","country","dest_hub","weight_kg","volume_cbm","value_usd","supplier","notes"])
    writer.writeheader()
    writer.writerows(shipments)

# Carrier cost reference (distractor - uses wrong units for consolidation)
(workspace / "data/raw/outbound/direct_rates.json").write_text(json.dumps({
    "note": "Direct FCL rates per container",
    "routes": [
        {"from": "CNSHA", "to": "NLAMS", "rate_20ft": 2400, "rate_40ft": 3800},
        {"from": "CNSZX", "to": "NLRTM", "rate_20ft": 2600, "rate_40ft": 4100},
        {"from": "JPOSA", "to": "DEHAM", "rate_20ft": 3100, "rate_40ft": 5200},
    ]
}, indent=2))

print("Workspace initialized successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")