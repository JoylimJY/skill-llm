import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory structure with distractor files ---
dirs = [
    "workspace/accounting/2024",
    "workspace/accounting/2023",
    "workspace/contracts/clients",
    "workspace/contracts/vendors",
    "workspace/invoices/outgoing/2024",
    "workspace/invoices/incoming/2024",
    "workspace/tax/filings",
    "workspace/tax/documents",
    "workspace/personal/expenses",
    "workspace/tools/scripts",
    "workspace/tools/config",
    "workspace/notes",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/accounting/2023/summary.csv": "date,description,amount,category\n2023-01-15,Old Invoice,1200.00,Revenue\n",
    "workspace/accounting/2023/notes.txt": "Year-end notes for 2023. No action needed.",
    "workspace/contracts/clients/client_a.txt": "Client A contract signed 2024-01-10. Rate: 120 EUR/hr.",
    "workspace/contracts/vendors/adobe_license.txt": "Adobe Creative Cloud annual license. Renewal: Feb 2025.",
    "workspace/invoices/outgoing/2024/inv_001.txt": "Invoice #001 to Client A: 3600 EUR. Date: 2024-02-01.",
    "workspace/invoices/outgoing/2024/inv_002.txt": "Invoice #002 to Client B: 4800 EUR. Date: 2024-05-15.",
    "workspace/invoices/incoming/2024/vendor_hosting.txt": "Hetzner Cloud invoice: 29.99 EUR/month.",
    "workspace/tax/filings/2022_filing.pdf.txt": "[placeholder] 2022 tax filing submitted.",
    "workspace/tax/documents/vat_registration.txt": "VAT Registration Number: DE123456789. Registered 2021.",
    "workspace/personal/expenses/groceries.csv": "date,item,cost\n2024-03-01,Groceries,45.00\n2024-03-08,Groceries,38.50\n",
    "workspace/tools/scripts/backup.sh": "#!/bin/bash\necho 'Backup script placeholder'",
    "workspace/tools/config/app.cfg": "[settings]\nenv=production\ndebug=false\n",
    "workspace/notes/todo.txt": "- Follow up with client B\n- Renew domain names\n- Check tax deadlines\n",
    "workspace/notes/meeting_notes.txt": "Meeting with Steuerberater on 2024-11-05. Topics: VAT, depreciation.",
}

for path, content in distractors.items():
    Path(path).write_text(content)

# --- Mock server data (transactions, company, tax settings) ---
# These will be served by the mock MCP server

transactions_2024 = [
    # MISSED DEDUCTION: Home office internet (currently "Personal")
    {
        "id": "txn_001",
        "date": "2024-01-05",
        "amount": 49.99,
        "description": "Telekom Internet January",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Adobe Creative Cloud SaaS (currently "Uncategorized")
    {
        "id": "txn_002",
        "date": "2024-01-12",
        "amount": 59.49,
        "description": "Adobe Creative Cloud subscription",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # CORRECTLY categorized: already a deduction
    {
        "id": "txn_003",
        "date": "2024-01-20",
        "amount": 320.00,
        "description": "Steuerberater Q4 consultation",
        "category": "4930",  # SKR04: Steuerberatungskosten
        "currency": "EUR",
        "verified": True
    },
    # MISSED DEDUCTION: Business travel meal - partial day (should use Verpflegungspauschale 14 EUR)
    {
        "id": "txn_004",
        "date": "2024-02-08",
        "amount": 23.50,
        "description": "Restaurant - client meeting Munich",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Under GWG threshold (net 840 EUR < 1000 EUR net), keyboard+monitor set
    {
        "id": "txn_005",
        "date": "2024-02-15",
        "amount": 999.60,  # gross, net = 999.60/1.19 = 840.00 EUR net => under GWG
        "description": "Dell Monitor 27inch + mechanical keyboard",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # TRICKY: Over GWG threshold net (1190 EUR gross / 1.19 = 1000 EUR net exactly = must depreciate)
    {
        "id": "txn_006",
        "date": "2024-03-01",
        "amount": 1190.00,  # gross, net = 1000 EUR => exactly at threshold, must depreciate (>1000 means depreciate, ==1000 still GWG in German law: <=800 EUR is GWG, 800-1000 pool, >1000 depreciate) 
        # Actually GWG in Germany: net <= 800 EUR immediate write-off, 800-1000 EUR optional pool, >1000 EUR AfA
        # Let's make this 952 EUR gross (net=800 EUR exactly at boundary)
        "description": "Laptop stand + webcam + USB hub bundle",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Professional liability insurance
    {
        "id": "txn_007",
        "date": "2024-03-10",
        "amount": 185.00,
        "description": "Hiscox Berufshaftpflicht annual premium",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Domain renewal (marketing/advertising)
    {
        "id": "txn_008",
        "date": "2024-04-01",
        "amount": 12.99,
        "description": "IONOS domain renewal myfreelance.de",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # NOT a deduction: personal grocery run (distractor)
    {
        "id": "txn_009",
        "date": "2024-04-15",
        "amount": 67.30,
        "description": "REWE Supermarket groceries",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Professional development course
    {
        "id": "txn_010",
        "date": "2024-05-03",
        "amount": 299.00,
        "description": "Udemy course: Advanced Kubernetes & DevOps",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Client gift - WITHIN 35 EUR limit (29.90 EUR)
    {
        "id": "txn_011",
        "date": "2024-05-20",
        "amount": 29.90,
        "description": "Amazon - gift for client Klaus Müller",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # TRICKY: Client gift - OVER 35 EUR limit per person (42.00 EUR) - NOT fully deductible
    {
        "id": "txn_012",
        "date": "2024-05-21",
        "amount": 42.00,
        "description": "Amazon - gift for client Anna Schmidt",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Hetzner Cloud hosting (SaaS/infrastructure)
    {
        "id": "txn_013",
        "date": "2024-06-01",
        "amount": 29.99,
        "description": "Hetzner Cloud server June",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Business bank account fees
    {
        "id": "txn_014",
        "date": "2024-06-30",
        "amount": 9.90,
        "description": "Kontofee Geschäftskonto Juni",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Public transport for client visit
    {
        "id": "txn_015",
        "date": "2024-07-12",
        "amount": 34.00,
        "description": "DB Bahn ticket Frankfurt-Hamburg client visit",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # Already correct - Revenue, not a deduction
    {
        "id": "txn_016",
        "date": "2024-07-31",
        "amount": 6000.00,
        "description": "Client B - July invoice payment",
        "category": "Revenue",
        "currency": "EUR",
        "verified": True
    },
    # MISSED DEDUCTION: Slack subscription (SaaS)
    {
        "id": "txn_017",
        "date": "2024-08-01",
        "amount": 7.50,
        "description": "Slack Pro monthly",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Conference ticket (professional development)
    {
        "id": "txn_018",
        "date": "2024-09-14",
        "amount": 450.00,
        "description": "KubeCon EU 2024 conference ticket",
        "category": "Uncategorized",
        "currency": "EUR",
        "verified": False
    },
    # MISSED DEDUCTION: Hotel for conference
    {
        "id": "txn_019",
        "date": "2024-09-15",
        "amount": 189.00,
        "description": "Hotel Ibis Paris - KubeCon conference stay",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
    # NOT a deduction: personal Amazon purchase (clothing)
    {
        "id": "txn_020",
        "date": "2024-10-01",
        "amount": 89.99,
        "description": "Amazon - winter jacket",
        "category": "Personal",
        "currency": "EUR",
        "verified": False
    },
]

# Correct GWG amounts
transactions_2024[5]["amount"] = 952.00  # net = 800 EUR exactly (952/1.19 ≈ 800)

company_details = {
    "name": "Max Mustermann Softwareentwicklung",
    "legal_form": "Freiberufler",
    "business_type": "Software Development & IT Consulting",
    "founding_date": "2021-03-15",
    "address": {
        "street": "Musterstraße 42",
        "city": "Berlin",
        "postal_code": "10115",
        "country": "DE"
    },
    "tax_id": "12/345/67890",
    "vat_number": "DE123456789",
    "home_office_ratio": 0.25  # 25% of apartment used as office
}

tax_settings = {
    "vat_status": "Regelbesteuerung",
    "vat_rate": 0.19,
    "tax_regime": "Einnahmenüberschussrechnung",
    "marginal_tax_rate_estimate": 0.37,
    "soli_applicable": True,
    "trade_tax_applicable": False,  # Freiberufler exempt from Gewerbesteuer
    "skr": "SKR04"
}

# Write mock server data
mock_data_dir = Path("workspace/tools/config")
mock_data_dir.mkdir(parents=True, exist_ok=True)

(mock_data_dir / "mock_transactions.json").write_text(
    json.dumps(transactions_2024, indent=2)
)
(mock_data_dir / "mock_company.json").write_text(
    json.dumps(company_details, indent=2)
)
(mock_data_dir / "mock_tax_settings.json").write_text(
    json.dumps(tax_settings, indent=2)
)

# Write the mock server script
mock_server_script = '''#!/usr/bin/env python3
"""Mock MCP/REST server for norman-finance tax tool."""
import json
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE = Path("/workspace/tools/config")
transactions = json.loads((BASE / "mock_transactions.json").read_text())
company = json.loads((BASE / "mock_company.json").read_text())
tax_settings_data = json.loads((BASE / "mock_tax_settings.json").read_text())

# Track categorization calls
categorized = []

@app.route("/search_transactions", methods=["GET", "POST"])
def search_transactions():
    period = None
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        period = body.get("period", "2024")
    else:
        period = request.args.get("period", "2024")
    
    # Filter by year
    year = str(period)[:4]
    filtered = [t for t in transactions if t["date"].startswith(year)]
    return jsonify({"transactions": filtered, "total": len(filtered)})

@app.route("/get_company_details", methods=["GET", "POST"])
def get_company_details():
    return jsonify(company)

@app.route("/list_tax_settings", methods=["GET", "POST"])
def list_tax_settings():
    return jsonify(tax_settings_data)

@app.route("/categorize_transaction", methods=["POST"])
def categorize_transaction():
    body = request.get_json(silent=True) or {}
    txn_id = body.get("transaction_id")
    new_category = body.get("category")
    
    if not txn_id or not new_category:
        return jsonify({"error": "transaction_id and category required"}), 400
    
    # Update in-memory transaction
    for t in transactions:
        if t["id"] == txn_id:
            old_cat = t["category"]
            t["category"] = new_category
            t["verified"] = True
            categorized.append({
                "transaction_id": txn_id,
                "old_category": old_cat,
                "new_category": new_category
            })
            # Persist categorization log
            log_path = Path("/workspace/tools/config/categorized_log.json")
            log_path.write_text(json.dumps(categorized, indent=2))
            return jsonify({"success": True, "transaction_id": txn_id, "new_category": new_category})
    
    return jsonify({"error": f"Transaction {txn_id} not found"}), 404

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7821, debug=False)
'''

Path("workspace/tools/scripts/mock_server.py").write_text(mock_server_script)
print("Workspace generated successfully.")
print(f"Transactions: {len(transactions_2024)}")
print("Mock server script written to workspace/tools/scripts/mock_server.py")