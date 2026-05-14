import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deeply nested distractor directory structure ---
dirs = [
    "sap_project/legacy_config/fi_gl",
    "sap_project/legacy_config/fi_ap",
    "sap_project/legacy_config/co_cca",
    "sap_project/migration/s4hana/simplification",
    "sap_project/migration/s4hana/universal_journal",
    "sap_project/docs/eu_parent/germany_config",
    "sap_project/docs/eu_parent/france_config",
    "sap_project/aus_subsidiary/draft_notes",
    "sap_project/aus_subsidiary/bank_details",
    "sap_project/aus_subsidiary/tax_office_correspondence",
    "sap_project/testing/unit_tests",
    "sap_project/testing/integration_tests",
    "sap_project/archive/old_versions",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files with misleading/wrong/partial data ---

# Wrong GST rate from EU config (distractor)
eu_tax_config = {
    "country": "DE",
    "tax_codes": [
        {"code": "V1", "rate": 19.0, "description": "Standard VAT Germany"},
        {"code": "V2", "rate": 7.0, "description": "Reduced VAT Germany"},
    ],
    "comment": "This is the German parent company VAT config. DO NOT use for AU subsidiary."
}
with open(os.path.join(workspace, "sap_project/docs/eu_parent/germany_config/tax_codes.json"), "w") as f:
    json.dump(eu_tax_config, f, indent=2)

# Outdated/wrong AU tax config (distractor - wrong rates to trap copy-paste)
au_tax_wrong = {
    "country": "AU",
    "gst_rate": 12.5,  # WRONG - should be 10%
    "payg_no_abn": 46.5,  # WRONG - should be 47%
    "superannuation": 9.5,  # WRONG - should be 11%
    "note": "Draft from 2019 - NOT CURRENT. Rates need verification with ATO."
}
with open(os.path.join(workspace, "sap_project/aus_subsidiary/draft_notes/old_tax_rates_draft.json"), "w") as f:
    json.dump(au_tax_wrong, f, indent=2)

# Wrong BSB patterns (distractor)
bank_bsb_wrong = {
    "CBA": "05xxxx",  # WRONG - should be 06xxxx
    "NAB": "07xxxx",  # WRONG - should be 08xxxx
    "ANZ": "02xxxx",  # WRONG - should be 01xxxx
    "Westpac": "04xxxx",  # WRONG - should be 03xxxx
    "note": "UNVERIFIED draft - needs confirmation"
}
with open(os.path.join(workspace, "sap_project/aus_subsidiary/bank_details/bsb_draft.json"), "w") as f:
    json.dump(bank_bsb_wrong, f, indent=2)

# Partial legacy FI-AP config (distractor)
legacy_ap = """
LEGACY FI-AP CONFIGURATION (Pre-S/4HANA)
Company Code: AU01
Payment Methods: C (Check), T (Bank Transfer)
House Bank: AUSBA
Payment Run: F110
NOTE: This config is from the old ECC 6.0 system. Migration to S/4HANA pending.
BSB: 06-2345 (CBA - OUTDATED account, account closed 2021)
"""
with open(os.path.join(workspace, "sap_project/legacy_config/fi_ap/payment_config_legacy.txt"), "w") as f:
    f.write(legacy_ap)

# GL chart of accounts distractor (irrelevant partial)
gl_coa = """
CHART OF ACCOUNTS - AU SUBSIDIARY (PARTIAL DRAFT)
Account: 100000 - Cash at Bank
Account: 200000 - Trade Creditors  
Account: 300000 - GST Payable (TBD)
Account: 301000 - GST Receivable (TBD)
INCOMPLETE - Pending FICO consultant review
"""
with open(os.path.join(workspace, "sap_project/legacy_config/fi_gl/coa_draft.txt"), "w") as f:
    f.write(gl_coa)

# S/4HANA simplification list distractor
s4_notes = {
    "migration_wave": 2,
    "target": "S/4HANA 2023",
    "acdoca_readiness": "pending",
    "new_asset_accounting": "not_activated",
    "notes": "Universal Journal migration not yet planned. Consultant assessment required."
}
with open(os.path.join(workspace, "sap_project/migration/s4hana/simplification/status.json"), "w") as f:
    json.dump(s4_notes, f, indent=2)

# Contractor payment partial info (distractor)
contractor_memo = """
FROM: CFO Office
TO: SAP Project Team
RE: Contractor Payments Setup

We have 15 contractors who do not have ABN numbers. 
Some are foreign residents (NZ, UK).
We need withholding tax configured URGENTLY before payroll cutover.
Current workaround: manual journal entries (unsustainable).

Also note: superannuation contributions need to start from day 1 for eligible workers.
"""
with open(os.path.join(workspace, "sap_project/aus_subsidiary/tax_office_correspondence/contractor_memo.txt"), "w") as f:
    f.write(contractor_memo)

# Archive noise files
for i in range(5):
    with open(os.path.join(workspace, f"sap_project/archive/old_versions/config_v{i}.bak"), "w") as f:
        f.write(f"Archive backup version {i} - obsolete\n")

# Unit test placeholders (distractor)
for t in ["test_gl.py", "test_ap.py", "test_tax.py"]:
    with open(os.path.join(workspace, f"sap_project/testing/unit_tests/{t}"), "w") as f:
        f.write(f"# Placeholder test - {t}\n# TODO: implement after config is finalised\n")

# The actual task brief (business context only, no technical hints)
task_brief = """
AUSTRALIAN SUBSIDIARY SAP IMPLEMENTATION — CONSULTANT BRIEF
============================================================
Company: Pacific Ridge Manufacturing Pty Ltd
ABN: 51 824 753 009
Industry: Metal fabrication and distribution
SAP Target: S/4HANA 2023
European Parent: Rheinwerk GmbH (Germany)

REQUIREMENTS FROM FINANCE DIRECTOR:

1. TAX SETUP
   We need our SAP system to handle Australian GST correctly across all scenarios.
   We sell both taxable and GST-free goods (some raw materials are GST-free).
   We also have input-taxed financial services income.
   Some of our sales require Reverse Charge Tax Invoices.

2. VENDOR PAYMENTS
   Our main bank is CommBank. We also use NAB for payroll.
   We need electronic payments set up — including BPAY for utility bills.
   All supplier payments must go through the automated payment program.

3. CONTRACTOR & WITHHOLDING
   We use sub-contractors heavily. Some have no ABN.
   Two contractors are foreign residents (one in NZ, one in UK).
   Need full withholding tax setup.
   Superannuation obligations must be tracked in the system.

Please produce a complete SAP implementation guide for our team.
Save your response as: aus_sap_implementation_guide.md
"""
with open(os.path.join(workspace, "sap_project/aus_subsidiary/TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")