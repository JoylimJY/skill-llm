import json
import os
import random
import csv
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create distractor directory structure
dirs = [
    "accounting/2024/Q1",
    "accounting/2024/Q2",
    "accounting/2024/Q3",
    "accounting/2024/Q4",
    "accounting/2025/Q1",
    "accounting/2025/archive",
    "clients/invoices/2025",
    "clients/contracts",
    "admin/legal",
    "admin/insurance",
    "tools/scripts",
    "reports/annual",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "accounting/2024/Q1/summary.txt": "Q1 2024 revenue: 45000 EUR. Expenses: 12000 EUR.",
    "accounting/2024/Q2/summary.txt": "Q2 2024 revenue: 52000 EUR. Expenses: 14500 EUR.",
    "accounting/2024/Q4/year_end_notes.txt": "Remember to check AfA for laptop purchased in October.",
    "accounting/2025/archive/old_categories.csv": "id,category\n1,Misc\n2,Office\n3,Travel",
    "clients/invoices/2025/invoice_001.txt": "Invoice #001 - 5000 EUR - Software consulting - 2025-01-15",
    "clients/invoices/2025/invoice_002.txt": "Invoice #002 - 7500 EUR - Architecture review - 2025-02-10",
    "clients/contracts/contract_template.txt": "This agreement is between [CLIENT] and [FREELANCER]...",
    "admin/legal/impressum.txt": "Mustermann IT-Consulting, Musterstrasse 42, 10115 Berlin",
    "admin/insurance/policy_notes.txt": "Berufshaftpflicht policy renewed 2025-01-01. Annual premium: 480 EUR.",
    "tools/scripts/export_helper.py": "# Helper script for data export\nimport csv\nprint('helper')",
    "reports/annual/2024_annual.txt": "Annual report 2024 - Total deductions claimed: 18200 EUR",
    "accounting/2025/Q1/notes.txt": "Q1 2025 transactions need review. Some may be miscategorized.",
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# Company details (simulating get_company_details MCP output)
company_details = {
    "company_id": "de_freelancer_001",
    "name": "Maximilian Bauer IT-Consulting",
    "type": "Freiberufler",
    "tax_id": "123/456/78901",
    "address": {
        "street": "Kantstrasse 17",
        "city": "Berlin",
        "zip": "10623",
        "country": "DE"
    },
    "founded": "2019-03-01",
    "industry": "Software Development & IT Consulting",
    "home_office_percentage": 20,
    "employees": 0
}
(workspace / "accounting/2025/Q1/company_details.json").write_text(
    json.dumps(company_details, indent=2)
)

# Tax settings (simulating list_tax_settings MCP output)
tax_settings = {
    "vat_registered": True,
    "vat_id": "DE298765432",
    "tax_regime": "Einkommensteuer",
    "accounting_method": "Einnahmenüberschussrechnung",
    "vat_rate_standard": 19,
    "fiscal_year": "calendar",
    "skr": "SKR04",
    "estimated_marginal_rate_pct": 37
}
(workspace / "accounting/2025/Q1/tax_settings.json").write_text(
    json.dumps(tax_settings, indent=2)
)

# Messy transactions CSV for Q1 2025 (simulating search_transactions MCP output)
# Fields: id, date, amount_gross_eur, vat_rate_pct, description, vendor, current_category, notes
# Deliberately messy: wrong categories, ambiguous descriptions, tricky amounts
transactions = [
    # Home office: internet - currently categorized as "Personal"
    {
        "id": "TXN-001",
        "date": "2025-01-05",
        "amount_gross_eur": 47.60,
        "vat_rate_pct": 19,
        "description": "Vodafone DSL Rechnung Januar",
        "vendor": "Vodafone GmbH",
        "current_category": "Personal",
        "notes": "Monthly internet + phone bundle"
    },
    # SaaS subscription - currently "Uncategorized"
    {
        "id": "TXN-002",
        "date": "2025-01-08",
        "amount_gross_eur": 23.80,
        "vat_rate_pct": 19,
        "description": "Adobe Creative Cloud Monthly",
        "vendor": "Adobe Systems",
        "current_category": "Uncategorized",
        "notes": ""
    },
    # Laptop - 1190 EUR gross, net = 1190/1.19 = 1000.00 EUR exactly (edge case: NOT under GWG, exactly at threshold, must be depreciated)
    {
        "id": "TXN-003",
        "date": "2025-01-15",
        "amount_gross_eur": 1190.00,
        "vat_rate_pct": 19,
        "description": "MacBook Pro 14 Zubehoer - USB Hub + Adapter Set",
        "vendor": "Apple Premium Reseller Berlin",
        "current_category": "Office Supplies",
        "notes": "Accessories bundle"
    },
    # Second hardware item - 595 EUR gross, net = 595/1.19 = 500.00 EUR (under GWG, fully deductible)
    {
        "id": "TXN-004",
        "date": "2025-01-20",
        "amount_gross_eur": 595.00,
        "vat_rate_pct": 19,
        "description": "Dell 24 inch Monitor P2422H",
        "vendor": "MediaMarkt",
        "current_category": "Personal",
        "notes": "New monitor for home office"
    },
    # Business travel meal - 1 day trip (no overnight), should be 14 EUR Verpflegungspauschale
    {
        "id": "TXN-005",
        "date": "2025-02-03",
        "amount_gross_eur": 38.50,
        "vat_rate_pct": 19,
        "description": "Restaurant Borchard - Mittagessen Kundengespräch München",
        "vendor": "Restaurant Borchard",
        "current_category": "Meals",
        "notes": "Day trip to Munich client, no overnight stay"
    },
    # Train ticket - business travel
    {
        "id": "TXN-006",
        "date": "2025-02-03",
        "amount_gross_eur": 89.00,
        "vat_rate_pct": 19,
        "description": "Deutsche Bahn ICE Berlin-München-Berlin",
        "vendor": "Deutsche Bahn",
        "current_category": "Travel",
        "notes": "Client meeting in Munich"
    },
    # Professional liability insurance - currently "Insurance" but wrong SKR04 subcode
    {
        "id": "TXN-007",
        "date": "2025-01-02",
        "amount_gross_eur": 120.00,
        "vat_rate_pct": 0,
        "description": "HDI Berufshaftpflicht Q1 2025",
        "vendor": "HDI Versicherung",
        "current_category": "Insurance",
        "notes": "Quarterly professional liability premium"
    },
    # Conference registration - currently "Personal"
    {
        "id": "TXN-008",
        "date": "2025-02-14",
        "amount_gross_eur": 595.00,
        "vat_rate_pct": 19,
        "description": "PyCon DE 2025 Ticket",
        "vendor": "Python Software Verband e.V.",
        "current_category": "Personal",
        "notes": "Annual developer conference"
    },
    # Client gift - currently "Uncategorized" - 28 EUR (under 35 EUR cap, fully deductible)
    {
        "id": "TXN-009",
        "date": "2025-02-20",
        "amount_gross_eur": 28.00,
        "vat_rate_pct": 0,
        "description": "Amazon - Buchgeschenk fuer Kunde Herr Schmidt",
        "vendor": "Amazon",
        "current_category": "Uncategorized",
        "notes": "Gift for client Hans Schmidt"
    },
    # Client gift to SAME person - 15 EUR, cumulative = 43 EUR > 35 EUR cap, only 35 EUR deductible total
    {
        "id": "TXN-010",
        "date": "2025-03-05",
        "amount_gross_eur": 15.00,
        "vat_rate_pct": 0,
        "description": "Weinhandlung - Flasche Wein fuer Kunde Herr Schmidt",
        "vendor": "Weinhandlung Popp",
        "current_category": "Uncategorized",
        "notes": "Gift for client Hans Schmidt"
    },
    # Tax advisor fee - currently "Personal"
    {
        "id": "TXN-011",
        "date": "2025-03-10",
        "amount_gross_eur": 416.50,
        "vat_rate_pct": 19,
        "description": "Steuerberater Kanzlei Müller - Jahresabschluss 2024",
        "vendor": "Kanzlei Müller & Partner",
        "current_category": "Personal",
        "notes": "Annual tax return preparation"
    },
    # Domain + hosting - currently "Uncategorized"
    {
        "id": "TXN-012",
        "date": "2025-01-12",
        "amount_gross_eur": 9.99,
        "vat_rate_pct": 19,
        "description": "IONOS Webhosting Paket M + domain bauer-it.de",
        "vendor": "IONOS SE",
        "current_category": "Uncategorized",
        "notes": "Business website hosting"
    },
    # Private purchase - correctly categorized, should NOT be flagged
    {
        "id": "TXN-013",
        "date": "2025-01-25",
        "amount_gross_eur": 65.00,
        "vat_rate_pct": 0,
        "description": "REWE Lebensmittel",
        "vendor": "REWE",
        "current_category": "Personal",
        "notes": "Grocery shopping"
    },
    # Bank account fee - currently "Personal"
    {
        "id": "TXN-014",
        "date": "2025-01-31",
        "amount_gross_eur": 12.90,
        "vat_rate_pct": 0,
        "description": "QONTO Kontoführungsgebühr Januar 2025",
        "vendor": "Qonto",
        "current_category": "Personal",
        "notes": "Business bank account monthly fee"
    },
    # Book for professional development - currently "Personal"
    {
        "id": "TXN-015",
        "date": "2025-02-28",
        "amount_gross_eur": 49.90,
        "vat_rate_pct": 7,
        "description": "O'Reilly - Designing Data-Intensive Applications",
        "vendor": "O'Reilly Media",
        "current_category": "Personal",
        "notes": "Technical book for project work"
    },
    # Overnight business trip hotel - qualifies for 28 EUR Verpflegungspauschale
    {
        "id": "TXN-016",
        "date": "2025-03-18",
        "amount_gross_eur": 149.00,
        "vat_rate_pct": 7,
        "description": "Hotel Ibis Hamburg Altona - 1 Nacht",
        "vendor": "Accor Hotels",
        "current_category": "Travel",
        "notes": "Overnight stay for Hamburg client workshop"
    },
    # Another large hardware item ABOVE GWG - net = 2100/1.19 = 1764.71 EUR, must be depreciated (AfA)
    {
        "id": "TXN-017",
        "date": "2025-03-22",
        "amount_gross_eur": 2100.00,
        "vat_rate_pct": 19,
        "description": "Apple Mac Studio M3 Ultra",
        "vendor": "Apple Store Berlin",
        "current_category": "Office Supplies",
        "notes": "Main workstation replacement"
    },
    # Slack subscription - currently "Uncategorized"
    {
        "id": "TXN-018",
        "date": "2025-02-01",
        "amount_gross_eur": 10.00,
        "vat_rate_pct": 19,
        "description": "Slack Technologies Pro Plan",
        "vendor": "Slack Technologies",
        "current_category": "Uncategorized",
        "notes": "Team communication tool"
    },
    # Private restaurant - should NOT be flagged as deductible
    {
        "id": "TXN-019",
        "date": "2025-02-14",
        "amount_gross_eur": 95.00,
        "vat_rate_pct": 19,
        "description": "Restaurant Valentinstag Abendessen",
        "vendor": "Grill Royal Berlin",
        "current_category": "Personal",
        "notes": "Valentines day dinner"
    },
    # Mobile phone plan - 50% business use
    {
        "id": "TXN-020",
        "date": "2025-01-10",
        "amount_gross_eur": 39.99,
        "vat_rate_pct": 19,
        "description": "O2 Business Mobilfunk Januar",
        "vendor": "Telefónica Germany",
        "current_category": "Personal",
        "notes": "Mobile plan, estimated 50% business use"
    },
]

# Write transactions as CSV
csv_path = workspace / "accounting/2025/Q1/transactions_q1_2025.csv"
fieldnames = ["id", "date", "amount_gross_eur", "vat_rate_pct", "description", "vendor", "current_category", "notes"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(transactions)

# SKR04 reference (partial, for context - real codes from German chart of accounts)
skr04_reference = {
    "4120": "Gehälter",
    "4210": "Miete und Pacht",
    "4240": "Gas, Strom, Wasser",
    "4270": "Reinigung",
    "4350": "Kfz-Kosten (nicht abzugsfähig)",
    "4360": "Reisekosten Arbeitnehmer",
    "4380": "Werbe- und Reisekosten",
    "4520": "Gerichts- und Beratungskosten",
    "4530": "Buchführungskosten",
    "4540": "Sonstige Verwaltungskosten",
    "4570": "Beiträge und Gebühren",
    "4600": "Werbekosten",
    "4610": "Messe, Ausstellung, Kongresse",
    "4630": "Warenabgaben / Geschenke abzugsfähig",
    "4635": "Geschenke nicht abzugsfähig (>35 EUR)",
    "4650": "Bewirtungskosten",
    "4655": "Bewirtungskosten nicht abzugsfähig",
    "4660": "Reisekosten Unternehmer",
    "4670": "Verpflegungsmehraufwand",
    "4740": "Kosten des Geldverkehrs",
    "4810": "Bürokosten",
    "4830": "Zeitschriften, Bücher",
    "4840": "Fortbildungskosten",
    "4850": "Beratungskosten / Steuerberatung",
    "4860": "Fachliteratur",
    "4900": "Sonstige betriebliche Aufwendungen",
    "4920": "Telefon",
    "4930": "Beiträge",
    "4940": "Versicherungen",
    "4945": "Berufshaftpflicht",
    "0410": "Büro- und Geschäftsausstattung (GWG)",
    "0420": "Büromaschinen und EDV-Anlagen",
    "4980": "Sonstige Kosten",
    "4813": "EDV-Kosten / Softwarekosten",
    "4822": "Internetkosten",
}
(workspace / "accounting/2025/Q1/skr04_reference.json").write_text(
    json.dumps(skr04_reference, indent=2)
)

print("Workspace generated successfully.")
print(f"Transactions: {len(transactions)}")
print(f"Files created in: {workspace}")