import os
import json
import csv
import random

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "legacy/reports/2022",
    "legacy/reports/2023",
    "ops/configs",
    "ops/logs",
    "procurement/raw",
    "procurement/processed",
    "compliance/audits",
    "compliance/flags",
    "hr/onboarding",
    "finance/invoices",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "legacy/reports/2022/annual_summary.txt": "Annual supplier count: 142\nCompliance rate: 87%\n",
    "legacy/reports/2023/q4_review.txt": "Q4 2023: 3 suppliers flagged for audit.\n",
    "ops/configs/db_config.yaml": "host: localhost\nport: 5432\ndb: supply_chain\n",
    "ops/logs/access.log": "2024-01-01 10:00:00 GET /api/suppliers 200\n2024-01-02 11:23:11 POST /api/flag 201\n",
    "ops/configs/network.json": json.dumps({"proxy": "none", "timeout": 30}),
    "procurement/processed/vendor_list_old.csv": "id,name,country\n1,OldCorp,US\n2,LegacyCo,DE\n",
    "compliance/audits/2023_audit.txt": "All tier-1 suppliers passed ISO 9001 audit.\n",
    "compliance/flags/pending.txt": "SupplierID 77: Manual review pending.\n",
    "hr/onboarding/checklist.md": "# Onboarding\n- Complete security training\n- Submit ID docs\n",
    "finance/invoices/invoice_0042.txt": "Invoice #0042\nAmount: $14,200\nVendor: TexTronics\n",
    "procurement/raw/scratch_notes.txt": "Check on AsiaParts delivery status - delayed 3 weeks\n",
}

for path, content in distractor_files.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# --- THE CORE PROBLEM: messy supplier data in CSV ---
# Suppliers with various risk profiles and certifications
supplier_data = [
    # id, name, country, risk_level, certified
    ("S001", "NovaTex Fabrics", "Bangladesh", "high", "false"),
    ("S002", "EuroMetal GmbH", "Germany", "low", "true"),
    ("S003", "AsiaParts Ltd", "China", "high", "false"),
    ("S004", "GreenLeaf Organics", "Netherlands", "low", "true"),
    ("S005", "FastShip Logistics", "India", "medium", "false"),
    ("S006", "PrecisionCast Co", "Japan", "low", "true"),
    ("S007", "Delta Chemicals", "Nigeria", "high", "false"),
    ("S008", "NordicWood AB", "Sweden", "low", "true"),
]

with open(os.path.join(workspace, "procurement/raw/suppliers_2024.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["supplier_id", "supplier_name", "country", "risk_level", "certified"])
    for row in supplier_data:
        writer.writerow(row)

# --- A separate compliance notes JSON (messy, partial overlap) ---
compliance_notes = {
    "flagged_suppliers": ["S001", "S003", "S007"],
    "review_date": "2024-06-01",
    "notes": "These suppliers failed the last environmental audit.",
    "certifications_pending": ["S005"]
}
with open(os.path.join(workspace, "compliance/flags/compliance_notes.json"), "w") as f:
    json.dump(compliance_notes, f, indent=2)

# --- A partial old JS file that does NOT use the correct library (distractor) ---
old_js_content = """
// DEPRECATED: Old approach using raw SQLite
const sqlite3 = require('sqlite3');
// ... this file is no longer maintained
"""
with open(os.path.join(workspace, "ops/configs/old_db_loader.js"), "w") as f:
    f.write(old_js_content)

print("Workspace generated successfully.")
print("Key input files:")
print("  - procurement/raw/suppliers_2024.csv  (main supplier data)")
print("  - compliance/flags/compliance_notes.json  (compliance flags)")