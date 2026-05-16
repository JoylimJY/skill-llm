import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "internal_docs/compliance/2023",
    "internal_docs/compliance/2024",
    "internal_docs/product_drafts/loans",
    "internal_docs/product_drafts/cards",
    "internal_docs/product_drafts/forex",
    "internal_docs/legacy_data",
    "tools/scripts",
    "tools/templates",
    "reports/q1",
    "reports/q3",
    "archive/old_rates",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files with WRONG/OUTDATED data to confuse the agent ---

# Outdated rates doc (WRONG values)
with open(os.path.join(workspace, "internal_docs/legacy_data/old_product_rates.txt"), "w") as f:
    f.write("""LEGACY RATE SHEET (DEPRECATED - DO NOT USE)
Huimin Loan: 4.2% annually
Car Loan: 5.1% annually
First-home mortgage: LPR+10BP
Large CD minimum: 10万
Cross-border transfer fee: 0.5%, min 30 yuan, max 500 yuan
Mobile transfer daily limit: 500,000 yuan
Credit card gold annual fee: 200 yuan (waived if 12 swipes)
""")

# Partial/incomplete JSON draft (missing fields, wrong values)
partial_data = {
    "loans": {
        "huimin_loan": {
            "max_amount_wan": 30,
            "annual_rate_pct": 4.2,  # WRONG
            "max_term_years": 5       # WRONG
        }
    },
    "credit_cards": {
        "gold_card": {
            "annual_fee_yuan": 200,  # WRONG
            "waiver_condition": "swipe 12 times"  # WRONG
        }
    }
}
with open(os.path.join(workspace, "internal_docs/product_drafts/partial_product_data.json"), "w") as f:
    json.dump(partial_data, f, ensure_ascii=False, indent=2)

# Distractor: a note with some correct but mostly irrelevant info
with open(os.path.join(workspace, "internal_docs/compliance/2024/audit_notes.txt"), "w") as f:
    f.write("""Audit cycle: Q2 2024
Reviewer: Zhang Wei
Note: Cross-check all rates against official documentation before submission.
Do not use figures from the legacy rate sheet.
Pending items: forex fee structure, CD minimum deposit, mobile banking limits.
""")

# Distractor: a script that does nothing useful
with open(os.path.join(workspace, "tools/scripts/fetch_rates.sh"), "w") as f:
    f.write("""#!/bin/bash
# Placeholder - rates fetcher not yet implemented
echo "Rate fetching not configured"
exit 1
""")

# Distractor: a template JSON with placeholder values
template = {
    "report_version": "TBD",
    "products": {
        "loans": {},
        "deposits": {},
        "credit_cards": {},
        "forex": {}
    }
}
with open(os.path.join(workspace, "tools/templates/report_template.json"), "w") as f:
    json.dump(template, f, ensure_ascii=False, indent=2)

# Distractor: old Q1 report with fabricated/wrong numbers
with open(os.path.join(workspace, "reports/q1/q1_summary.json"), "w") as f:
    json.dump({
        "period": "Q1 2024",
        "mortgage_first_home_rate": "LPR+30BP",  # WRONG
        "savings_bond_3yr_rate_pct": 2.75,        # WRONG
        "remittance_fee_permille": 2,             # WRONG
        "remittance_fee_min_yuan": 30,            # WRONG
        "remittance_fee_max_yuan": 500,           # WRONG
    }, f, ensure_ascii=False, indent=2)

# Distractor: forex draft with partial info
with open(os.path.join(workspace, "internal_docs/product_drafts/forex/forex_notes.txt"), "w") as f:
    f.write("""USD forex wealth product: Dehao - Huitianli
Terms: 30-180 days
Rate range: approximately 4-5%
Note: verify exact range from official docs
EUR rate: unknown, needs verification
HKD: needs verification
""")

# Distractor: card notes
with open(os.path.join(workspace, "internal_docs/product_drafts/cards/card_benefits.txt"), "w") as f:
    f.write("""Gold card note: annual fee around 100 yuan
Platinum card: ~1000 yuan/year, maybe waived with points
Y-Power: free
Walmart card: free
Need to confirm: exact waiver conditions for gold card
""")

# Distractor: loan notes with some correct but unstructured info
with open(os.path.join(workspace, "internal_docs/product_drafts/loans/loan_overview.txt"), "w") as f:
    f.write("""Personal Loans Overview:
- Huimin Loan (惠民贷): Consumer use, up to 300,000 yuan
  Rate: check official docs - our records may be outdated
  Term: check official docs
- Study Abroad Loan: up to 2,000,000 yuan
- Car loan: up to 80% of vehicle price (confirm)
- Business loan (Puhui e-loan): up to 5,000,000 yuan
""")

# Distractor: large CD note with wrong minimum
with open(os.path.join(workspace, "archive/old_rates/cd_rates_2022.txt"), "w") as f:
    f.write("""2022 Large Certificate of Deposit:
1-year: 2.00%, min 100,000 yuan
2-year: 2.40%, min 100,000 yuan  
3-year: 3.00%, min 100,000 yuan
NOTE: These are 2022 figures, current minimums may differ.
""")

# Distractor: a misleading README-like file (but NOT actually helpful)
with open(os.path.join(workspace, "internal_docs/compliance/2023/checklist.txt"), "w") as f:
    f.write("""2023 Compliance Checklist:
[x] Verify mortgage rates
[ ] Confirm CD minimum deposit thresholds  
[ ] Update remittance fee table
[ ] Check mobile banking transfer limits
[ ] Validate credit card annual fee waiver rules
Status: INCOMPLETE - requires update from official source
""")

# Distractor: empty archive file
with open(os.path.join(workspace, "reports/q3/q3_placeholder.txt"), "w") as f:
    f.write("Q3 report pending.\n")

# Distractor: a tools script
with open(os.path.join(workspace, "tools/scripts/validate_json.py"), "w") as f:
    f.write("""#!/usr/bin/env python3
import json, sys
try:
    with open(sys.argv[1]) as f:
        json.load(f)
    print("Valid JSON")
except Exception as e:
    print(f"Invalid: {e}")
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")