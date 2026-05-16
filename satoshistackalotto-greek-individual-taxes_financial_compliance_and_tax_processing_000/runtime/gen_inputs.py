#!/usr/bin/env python3
"""
Generates the messy, realistic workspace for the Greek individual tax task.
All randomness uses fixed seeds for determinism.
"""
import os
import json
import random

random.seed(42)

BASE = "/workspace"
DATA_DIR = "/data"

# Create directory structure
dirs = [
    f"{DATA_DIR}/2025/employment",
    f"{DATA_DIR}/2025/property",
    f"{DATA_DIR}/2025/professional",
    f"{DATA_DIR}/2025/deductions",
    f"{DATA_DIR}/2025/family",
    f"{DATA_DIR}/2024/employment",
    f"{DATA_DIR}/2024/property",
    f"{DATA_DIR}/2024/deductions",
    f"{DATA_DIR}/archive/old_forms",
    f"{DATA_DIR}/templates",
    f"{BASE}/notes",
    f"{BASE}/drafts",
    f"{BASE}/output",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ──────────────────────────────────────────────
# DISTRACTOR FILES (irrelevant / misleading)
# ──────────────────────────────────────────────

# Distractor 1: Old 2024 salary (should be ignored)
with open(f"{DATA_DIR}/2024/employment/salary_2024.csv", "w") as f:
    f.write("month,gross,withheld,social_security\n")
    for m in range(1, 13):
        f.write(f"2024-{m:02d},2800.00,420.00,350.00\n")
    f.write("2024-12,2800.00,420.00,350.00\n")  # duplicate December distractor

# Distractor 2: Template placeholder
with open(f"{DATA_DIR}/templates/e1_template_blank.json", "w") as f:
    json.dump({"taxpayer_afm": "XXXXXXXXX", "year": 0, "income": {}, "tax": {}}, f, indent=2)

# Distractor 3: 2024 rental income (should be ignored)
with open(f"{DATA_DIR}/2024/property/rental_2024.tsv", "w") as f:
    f.write("month\trent_received\texpenses\n")
    for m in range(1, 13):
        f.write(f"2024-{m:02d}\t900.00\t150.00\n")

# Distractor 4: Archive note
with open(f"{DATA_DIR}/archive/old_forms/e1_2023_submitted.txt", "w") as f:
    f.write("E1 form for 2023 was submitted on 2024-06-28. Net tax paid: 1,850 EUR.\n")

# Distractor 5: Draft notes in workspace
with open(f"{BASE}/notes/todo.txt", "w") as f:
    f.write("TODO: Ask client for ENFIA receipt\nTODO: Check if consulting contract signed\n")

# Distractor 6: Wrong-year consulting file
with open(f"{DATA_DIR}/2024/employment/consulting_2024.json", "w") as f:
    json.dump({"year": 2024, "total_fees": 18000, "withholding": 3600, "expenses": 5000}, f)

# Distractor 7: Drafts folder decoy
with open(f"{BASE}/drafts/tax_estimate_rough.txt", "w") as f:
    f.write("Rough estimate: total tax maybe around 8000? Need to recalculate.\n")

# Distractor 8: Template YAML (not the real family config)
with open(f"{DATA_DIR}/templates/family_template.yaml", "w") as f:
    f.write("# Template — do not use\ntaxpayer: UNKNOWN\nspouse: false\nchildren: 0\n")

# Distractor 9: Noise property file
with open(f"{DATA_DIR}/2025/property/enfia_notice_text.txt", "w") as f:
    f.write("ENFIA Notice 2025\nProperty: Flat at Patision 45, Athens\nObjective Value: 165000 EUR\nENFIA Amount Due: 412.50 EUR\nPayment deadline: September 30, 2025\n")

# Distractor 10: Old insurance CSV (2024, should be ignored)
with open(f"{DATA_DIR}/2024/deductions/insurance_2024.csv", "w") as f:
    f.write("type,annual_premium\nlife,900\nhealth,800\n")

# ──────────────────────────────────────────────
# REAL 2025 INPUT FILES (messy / needs cleaning)
# ──────────────────────────────────────────────

# FILE 1: Employment payslips CSV — has duplicate row, header repeated mid-file, inconsistent spacing
# Real: 12 months × €3,200 gross + 13th month payment of €3,200
# Withholding: €6,100 total (from employer)
# Social security: €4,608 total (12 × €384)
with open(f"{DATA_DIR}/2025/employment/payslips_2025.csv", "w") as f:
    f.write("month , gross_salary , withheld_tax , social_security\n")
    months = [
        ("2025-01", 3200.00, 380.00, 384.00),
        ("2025-02", 3200.00, 380.00, 384.00),
        ("2025-03", 3200.00, 380.00, 384.00),
        ("2025-04", 3200.00, 380.00, 384.00),
        ("2025-05", 3200.00, 380.00, 384.00),
        ("2025-06", 3200.00, 380.00, 384.00),
        ("2025-07", 3200.00, 380.00, 384.00),
        ("2025-08", 3200.00, 380.00, 384.00),
        ("2025-09", 3200.00, 380.00, 384.00),
        ("2025-10", 3200.00, 380.00, 384.00),
        ("2025-11", 3200.00, 380.00, 384.00),
        ("2025-12", 3200.00, 380.00, 384.00),
    ]
    for row in months:
        f.write(f"{row[0]} , {row[1]:.2f} , {row[2]:.2f} , {row[3]:.2f}\n")
    # Duplicate row (distractor — same month, must be deduplicated)
    f.write("2025-06 , 3200.00 , 380.00 , 384.00\n")
    # Re-printed header mid-file (noise)
    f.write("month , gross_salary , withheld_tax , social_security\n")
    # 13th month payment row
    f.write("2025-13M , 3200.00 , 340.00 , 0.00\n")

# FILE 2: Rental income ledger (TSV) — monthly rent from a flat
# Gross rental: 12 × €750 = €9,000
# Rental expenses: €1,800 (maintenance + management fee)
# Net rental income for tax: €9,000 (rental expenses are deductible, but rental tax
# is applied to GROSS rental income minus allowable expenses)
# Rental taxable income = 9000 - 1800 = 7200
with open(f"{DATA_DIR}/2025/property/rental_income_2025.tsv", "w") as f:
    f.write("month\trent_received\texpense_type\texpense_amount\n")
    for m in range(1, 13):
        expense = 150.00 if m in [3, 6, 9, 12] else 0.00
        expense_type = "maintenance" if m in [3, 6, 9, 12] else "none"
        f.write(f"2025-{m:02d}\t750.00\t{expense_type}\t{expense:.2f}\n")

# FILE 3: Consulting/professional income JSON — messy unicode currency symbol, needs parsing
# Consulting fees: €14,000 gross
# Withholding tax paid by clients: 20% × 14,000 = €2,800
# Deductible business expenses: €3,500
with open(f"{DATA_DIR}/2025/professional/consulting_invoices_2025.json", "w") as f:
    invoices = [
        {"invoice_id": "INV-2025-001", "client": "Techniki SA", "date": "2025-02-15",
         "amount_eur": 3500.00, "withholding_pct": 20, "expense_notes": "software tools: 800 EUR"},
        {"invoice_id": "INV-2025-002", "client": "Logotech EPE", "date": "2025-05-20",
         "amount_eur": 4000.00, "withholding_pct": 20, "expense_notes": "travel: 700 EUR"},
        {"invoice_id": "INV-2025-003", "client": "Techniki SA", "date": "2025-08-10",
         "amount_eur": 3500.00, "withholding_pct": 20, "expense_notes": "equipment: 1200 EUR"},
        # Distractor: draft invoice, not confirmed, should be excluded
        {"invoice_id": "INV-2025-004-DRAFT", "client": "Pending Client", "date": "2025-12-30",
         "amount_eur": 2000.00, "withholding_pct": 20, "expense_notes": "DRAFT - not issued",
         "status": "draft"},
        {"invoice_id": "INV-2025-005", "client": "Synergasia AE", "date": "2025-10-05",
         "amount_eur": 3000.00, "withholding_pct": 20, "expense_notes": "office rent portion: 800 EUR"},
    ]
    json.dump({"year": 2025, "currency": "EUR", "invoices": invoices}, f, indent=2, ensure_ascii=False)

# FILE 4: Deductions receipts — flat text, multiple types
# Life insurance: €1,100
# Health insurance: €900
# Charitable donation: €1,500
# Medical expenses: €2,200
with open(f"{DATA_DIR}/2025/deductions/receipts_summary_2025.txt", "w") as f:
    f.write("DEDUCTION RECEIPTS SUMMARY - TAX YEAR 2025\n")
    f.write("==========================================\n\n")
    f.write("INSURANCE PREMIUMS:\n")
    f.write("  Life Insurance (Ethniki Asfalistiki): EUR 1,100.00  [Annual policy 2025]\n")
    f.write("  Health Insurance (Generali Hellas): EUR 900.00  [Annual policy 2025]\n")
    f.write("  Total Insurance: EUR 2,000.00\n\n")
    f.write("CHARITABLE DONATIONS:\n")
    f.write("  Donation to MSF Greece: EUR 800.00  [Receipt #MSF-2025-0341]\n")
    f.write("  Donation to Church of Athens: EUR 400.00  [Receipt #ATH-CHR-2025-112]\n")
    f.write("  Donation to University of Athens Foundation: EUR 300.00  [Receipt #UOA-2025-087]\n")
    f.write("  Total Donations: EUR 1,500.00\n\n")
    f.write("MEDICAL EXPENSES:\n")
    f.write("  Cardiologist consultation (patient: Nikolaos Papadopoulos): EUR 250.00\n")
    f.write("  Pharmacy receipts (patient: Nikolaos Papadopoulos): EUR 480.00\n")
    f.write("  Dental treatment (patient: Maria Papadopoulou - spouse): EUR 870.00\n")
    f.write("  Physiotherapy (patient: Nikolaos Papadopoulos): EUR 600.00\n")
    f.write("  Total Medical: EUR 2,200.00\n\n")
    f.write("NOTE: All payments made by bank card (electronic payment bonus applies).\n")

# FILE 5: Family situation config (YAML-like, slightly malformed)
with open(f"{DATA_DIR}/2025/family/family_info_2025.yaml", "w") as f:
    f.write("# Family Tax Info - 2025\n")
    f.write("taxpayer:\n")
    f.write("  name: Nikolaos Papadopoulos\n")
    f.write("  afm: 123456789\n")
    f.write("  dob: 1978-04-12\n")
    f.write("  tax_resident: Greece\n\n")
    f.write("spouse:\n")
    f.write("  name: Maria Papadopoulou\n")
    f.write("  afm: 987654321\n")
    f.write("  income_2025: 0.00\n")
    f.write("  joint_filing: false\n\n")
    f.write("dependents:\n")
    f.write("  - name: Eleni Papadopoulou\n")
    f.write("    dob: 2010-09-03\n")
    f.write("    student: false\n")
    f.write("  - name: Giorgos Papadopoulos\n")
    f.write("    dob: 2013-03-17\n")
    f.write("    student: false\n\n")
    f.write("employer_withholding_certificate:\n")
    f.write("  employer: Hellas Tech AE\n")
    f.write("  total_withheld: 6100.00\n")
    f.write("  # Note: sum from payslips may differ slightly due to rounding — use THIS certificate value\n")

print("Workspace generated successfully.")
print(f"DATA_DIR: {DATA_DIR}")
print("Files created:")
for root, dirs_list, files in os.walk(DATA_DIR):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        fpath = os.path.join(root, fname)
        if DATA_DIR not in fpath:
            print(f"  {fpath}")