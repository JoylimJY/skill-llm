import os
import json
import csv
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# Create realistic distractor directory structure
dirs = [
    "workspace/data/raw_exports",
    "workspace/data/processed",
    "workspace/reports/archive",
    "workspace/reports/drafts",
    "workspace/config",
    "workspace/scripts/legacy",
    "workspace/scripts/utils",
    "workspace/marketing/campaigns",
    "workspace/marketing/analytics",
    "workspace/ops/billing",
    "workspace/ops/support",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

Path("workspace/config/stripe_webhook_config.json").write_text(json.dumps({
    "endpoint": "https://hooks.example.com/stripe",
    "events": ["payment_intent.succeeded", "customer.subscription.deleted"],
    "secret": "whsec_REDACTED"
}, indent=2))

Path("workspace/config/app_settings.yaml").write_text(
    "env: production\ndatabase_url: postgres://localhost/saas_db\nfeature_flags:\n  new_dashboard: false\n  annual_plans: true\n"
)

Path("workspace/scripts/legacy/old_mrr_calc.py").write_text(
    "# DEPRECATED - do not use\ndef calc_mrr(subscriptions):\n    return sum(s['amount'] for s in subscriptions)\n"
)

Path("workspace/scripts/utils/export_helper.sh").write_text(
    "#!/bin/bash\n# Exports customer data from CRM\necho 'Export complete'\n"
)

Path("workspace/marketing/campaigns/q2_campaign.csv").write_text(
    "campaign,spend,clicks,signups\nGoogle Ads,4200,1850,34\nLinkedIn,3100,620,18\nContent,800,5500,12\n"
)

Path("workspace/marketing/analytics/utm_report.json").write_text(json.dumps({
    "period": "2024-Q1",
    "sessions": 48200,
    "signups": 312,
    "conversion_rate": 0.0065
}, indent=2))

Path("workspace/ops/billing/failed_payments_log.txt").write_text(
    "2024-03-01 | cust_089 | $49 | card_declined\n"
    "2024-03-04 | cust_112 | $99 | insufficient_funds\n"
    "2024-03-18 | cust_203 | $49 | card_expired\n"
)

Path("workspace/ops/support/ticket_summary.json").write_text(json.dumps({
    "open_tickets": 23,
    "avg_resolution_hours": 14.2,
    "top_issues": ["billing confusion", "feature request", "integration bug"]
}, indent=2))

Path("workspace/reports/drafts/q1_narrative.txt").write_text(
    "Q1 Revenue Review - DRAFT\n"
    "Overall the quarter showed positive momentum but churn remains a concern.\n"
    "Details to be filled in from the official data export.\n"
)

Path("workspace/reports/archive/2023_annual_summary.txt").write_text(
    "2023 Annual Summary\nTotal Revenue: $68,400\nCustomers at EOY: 87\nAvg MRR: $5,700\n"
)

Path("workspace/data/processed/cohort_notes.txt").write_text(
    "March 2023 cohort showed 18% 90-day churn - investigate onboarding flow\n"
    "Agency customers 3x more likely to upgrade than solo freelancers\n"
)


# ── Core problem inputs ───────────────────────────────────────────────────────
# Simulate a SaaS (B2B project management tool) launched 8 months ago.
# We'll generate:
#   1. monthly_subscription_events.csv  (sign-ups, cancellations, upgrades)
#   2. customer_profiles.json           (customer details including LTV, acquisition source)
#   3. monthly_expenses.csv             (burn rate data)
#
# Business scenario:
#   Month 1 MRR: $820  (BELOW $1000 target - bad start)
#   Month 2 MRR: $1,340
#   Month 3 MRR: $2,650 (BELOW $3000 target)
#   Month 4 MRR: $3,400
#   Month 5 MRR: $4,200
#   Month 6 MRR: $5,100 (BELOW $7500 target)
#   Month 7 MRR: $5,050  <- slight dip
#   Month 8 MRR: $4,890  <- declining (2nd month of decline)
#
# This gives: mixed status - "The Ugly" emerging (2 months decline)
# Monthly growth Month7→8: (4890-5050)/5050 = -3.17%
# Churn in recent months: ~11-12% (HIGH - "The Bad" threshold crossed)

months = [
    {"month": 1, "mrr": 820,  "new_customers": 14, "churned": 0,  "active_customers": 14},
    {"month": 2, "mrr": 1340, "new_customers": 9,  "churned": 2,  "active_customers": 21},
    {"month": 3, "mrr": 2650, "new_customers": 18, "churned": 3,  "active_customers": 36},
    {"month": 4, "mrr": 3400, "new_customers": 11, "churned": 5,  "active_customers": 42},
    {"month": 5, "mrr": 4200, "new_customers": 12, "churned": 4,  "active_customers": 50},
    {"month": 6, "mrr": 5100, "new_customers": 14, "churned": 6,  "active_customers": 58},
    {"month": 7, "mrr": 5050, "new_customers": 8,  "churned": 7,  "active_customers": 59},
    {"month": 8, "mrr": 4890, "new_customers": 6,  "churned": 8,  "active_customers": 57},
]

with open("workspace/data/raw_exports/monthly_subscription_events.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["month", "mrr", "new_customers", "churned_customers", "active_customers"])
    writer.writeheader()
    for row in months:
        writer.writerow({
            "month": row["month"],
            "mrr": row["mrr"],
            "new_customers": row["new_customers"],
            "churned_customers": row["churned"],
            "active_customers": row["active_customers"]
        })

# Customer profiles - 57 currently active customers
# Top ~11-12 customers (20% of 57) should account for ~80% of revenue
# MRR = $4890, so whales should account for ~$3912
# We'll create 57 customer records

customers = []
customer_id = 1

# Whale tier: 11 customers (≈20% of 57), contributing ~80% of MRR ($3912)
# Each whale pays $299-$499/mo (agency plan)
whale_amounts = [499, 499, 449, 399, 399, 349, 349, 299, 299, 299, 299]  # sum = 3939 ≈ 80%
for i, amt in enumerate(whale_amounts):
    customers.append({
        "customer_id": f"cust_{customer_id:03d}",
        "name": f"Agency Partner {i+1}",
        "plan": "agency",
        "monthly_mrr": amt,
        "acquisition_source": random.choice(["referral", "organic", "partner"]),
        "months_active": random.randint(4, 8),
        "ltv_estimate": amt * random.randint(18, 36),
        "cac": random.randint(180, 350),
        "status": "active",
        "segment_hint": "high_value"
    })
    customer_id += 1

# Core tier: 34 customers (steady, mid-range), contributing ~18% of MRR (~$880)
# Each pays $19-$49/mo (starter/pro plan)
core_amounts = ([49]*10) + ([29]*14) + ([19]*10)  # 34 customers, sum = 490+406+190 = 1086
random.shuffle(core_amounts)
for i, amt in enumerate(core_amounts):
    customers.append({
        "customer_id": f"cust_{customer_id:03d}",
        "name": f"Freelancer {i+1}",
        "plan": random.choice(["starter", "pro"]),
        "monthly_mrr": amt,
        "acquisition_source": random.choice(["paid_ads", "organic", "content"]),
        "months_active": random.randint(2, 7),
        "ltv_estimate": amt * random.randint(6, 18),
        "cac": random.randint(80, 200),
        "status": "active",
        "segment_hint": "steady"
    })
    customer_id += 1

# Remaining 12 customers - mixed (some trial-like, recent signups)
trial_amounts = ([19]*6) + ([29]*4) + ([49]*2)
for i, amt in enumerate(trial_amounts):
    customers.append({
        "customer_id": f"cust_{customer_id:03d}",
        "name": f"New User {i+1}",
        "plan": "starter",
        "monthly_mrr": amt,
        "acquisition_source": random.choice(["paid_ads", "cold_outreach"]),
        "months_active": random.randint(1, 2),
        "ltv_estimate": amt * random.randint(2, 6),
        "cac": random.randint(120, 280),
        "status": "active",
        "segment_hint": "new"
    })
    customer_id += 1

# Write customer profiles
with open("workspace/data/raw_exports/customer_profiles.json", "w") as f:
    json.dump(customers, f, indent=2)

# Monthly expenses
expenses = [
    {"month": 1, "hosting": 120, "tools": 280, "marketing": 1200, "salaries": 3000, "other": 150},
    {"month": 2, "hosting": 130, "tools": 280, "marketing": 1400, "salaries": 3000, "other": 200},
    {"month": 3, "hosting": 145, "tools": 310, "marketing": 1800, "salaries": 4500, "other": 180},
    {"month": 4, "hosting": 160, "tools": 310, "marketing": 2000, "salaries": 4500, "other": 220},
    {"month": 5, "hosting": 175, "tools": 330, "marketing": 2200, "salaries": 6000, "other": 250},
    {"month": 6, "hosting": 190, "tools": 330, "marketing": 2500, "salaries": 6000, "other": 300},
    {"month": 7, "hosting": 200, "tools": 350, "marketing": 2300, "salaries": 6000, "other": 280},
    {"month": 8, "hosting": 210, "tools": 350, "marketing": 2100, "salaries": 6000, "other": 260},
]

with open("workspace/data/raw_exports/monthly_expenses.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["month", "hosting", "tools", "marketing", "salaries", "other"])
    writer.writeheader()
    writer.writerows(expenses)

# Write a metadata manifest so the agent knows what files exist
Path("workspace/data/raw_exports/DATA_MANIFEST.txt").write_text(
    "Raw exports available for analysis:\n"
    "1. monthly_subscription_events.csv - MRR, new signups, churn per month\n"
    "2. customer_profiles.json - Individual customer records with LTV and CAC data\n"
    "3. monthly_expenses.csv - Monthly operating costs breakdown\n"
    "\nNote: Data covers months 1-8 of product launch. No pre-processing has been done.\n"
    "Figures may need cross-validation across files.\n"
)

print("Workspace generated successfully.")
print(f"Total customers in profiles: {len(customers)}")
print(f"Total MRR check: ${sum(c['monthly_mrr'] for c in customers)}")
print(f"Whale revenue check: ${sum(whale_amounts)}")