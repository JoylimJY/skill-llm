import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "finance/budgets/2023",
    "finance/budgets/2024",
    "finance/tax/receipts",
    "finance/credit/history",
    "personal/travel/flights",
    "personal/travel/hotels",
    "personal/subscriptions",
    "tools/scripts",
    "tools/config",
    "reports/monthly",
    "reports/quarterly",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "finance/budgets/2023/budget_jan.csv": "category,amount\nfood,450\ntravel,200\nentertainment,80\n",
    "finance/budgets/2024/budget_q1.csv": "category,amount\nfood,500\ntravel,350\nentertainment,100\n",
    "finance/tax/receipts/receipt_001.txt": "Date: 2024-03-15\nMerchant: Amazon\nAmount: $89.99\nCategory: Shopping\n",
    "finance/tax/receipts/receipt_002.txt": "Date: 2024-04-01\nMerchant: United Airlines\nAmount: $340.00\nCategory: Travel\n",
    "finance/credit/history/equifax_pull.txt": "Hard inquiries: 3\nAccounts: 8\nOldest account: 2018-05\n",
    "personal/travel/flights/trip_nyc.json": json.dumps({"destination": "NYC", "date": "2024-06-10", "cost": 320}),
    "personal/travel/hotels/marriott_reservation.txt": "Confirmation: MR-449821\nHotel: Marriott Times Square\nNights: 3\n",
    "personal/subscriptions/active.csv": "service,monthly_cost\nNetflix,15.99\nSpotify,9.99\nAmazon Prime,14.99\n",
    "tools/config/env_vars.sh": "export EDITOR=vim\nexport LANG=en_US.UTF-8\n",
    "tools/scripts/backup.sh": "#!/bin/bash\necho 'backup started'\ntar czf /tmp/backup.tar.gz /workspace\n",
    "reports/monthly/march_summary.txt": "Total spend: $2,340\nTop category: Travel\nPoints earned: 4,200\n",
    "reports/quarterly/q1_2024.txt": "Total spend: $6,800\nAnnual fees paid: $550\nNet rewards value: $890\n",
    "data/raw/transactions_raw.csv": "date,merchant,amount,category\n2024-01-10,Delta,$450,Travel\n2024-01-15,Whole Foods,$120,Groceries\n2024-02-03,Cheesecake Factory,$85,Dining\n",
    "data/processed/transactions_clean.json": json.dumps([
        {"date": "2024-01-10", "merchant": "Delta", "amount": 450, "category": "Travel"},
        {"date": "2024-01-15", "merchant": "Whole Foods", "amount": 120, "category": "Groceries"},
    ]),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── THE ACTUAL TASK INPUT ─────────────────────────────────────────────────
# A messy "card history" document that the agent must parse and act upon
card_history = {
    "user_profile": {
        "name": "Alex Chen",
        "goal": "Maximize travel rewards, considering Chase application strategy"
    },
    "cards_to_add": [
        {
            "card_name": "Chase Sapphire Preferred",
            "bank": "Chase",
            "opened_date": "2022-03-15",
            "credit_limit": 15000,
            "bonus_earned": True,
            "notes": "Primary travel card"
        },
        {
            "card_name": "Chase Freedom Unlimited",
            "bank": "Chase",
            "opened_date": "2021-08-20",
            "credit_limit": 8000,
            "bonus_earned": True,
            "notes": "Everyday spend"
        },
        {
            "card_name": "Amex Gold",
            "bank": "Amex",
            "opened_date": "2023-01-10",
            "credit_limit": None,
            "bonus_earned": True,
            "notes": "Dining and groceries"
        },
        {
            "card_name": "Capital One Venture X",
            "bank": "Capital One",
            "opened_date": "2023-07-05",
            "credit_limit": 20000,
            "bonus_earned": True,
            "notes": "Travel portal card"
        }
    ],
    "analysis_request": {
        "check_524_after_adding": True,
        "find_best_personal_offers": {
            "min_bonus_usd": 500,
            "is_business": False,
            "limit": 5
        },
        "compare_top_offers": True,
        "output_file": "card_strategy_report.json"
    }
}

(workspace / "card_history.json").write_text(json.dumps(card_history, indent=2))

# A note about the expected output structure (intentionally vague, not a hint)
task_brief = """TASK BRIEF — Credit Card Strategy Audit
========================================
User: Alex Chen
Request date: 2024-07-01

Alex has recently opened several credit cards and needs a full strategy audit.
The audit should:
1. Register all cards in the tracking system
2. Determine current application slot availability under bank rules
3. Identify the top personal sign-up bonuses available (min $500 value)
4. Compare those top offers side-by-side
5. Save the full analysis to a file named: card_strategy_report.json
"""

(workspace / "TASK_BRIEF.txt").write_text(task_brief)

# Additional distractor: an old partial report that is WRONG and outdated
old_report = {
    "date": "2024-01-01",
    "note": "OUTDATED — do not use",
    "chase_524_slots": "unknown",
    "top_cards": []
}
(workspace / "reports/monthly/old_card_report.json").write_text(json.dumps(old_report, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")