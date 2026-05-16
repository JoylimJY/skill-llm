import os
import random
import json
from pathlib import Path

random.seed(42)

base = Path("/workspace")

# Create directory structure
dirs = [
    "workspace/artifacts",
    "workspace/clients/alfreds_plumbing",
    "workspace/clients/alfreds_plumbing/invoices",
    "workspace/clients/alfreds_plumbing/communications",
    "workspace/clients/other_clients/sunrise_hvac",
    "workspace/clients/other_clients/metro_electric",
    "workspace/internal/templates_old",
    "workspace/internal/crm_exports",
    "workspace/internal/finance/q1",
    "workspace/internal/finance/q2",
    "workspace/marketing/campaigns",
    "workspace/marketing/leads",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# Old/deprecated monthly report template (wrong format, missing fields)
with open("workspace/internal/templates_old/monthly_report_v1.txt", "w") as f:
    f.write("""Hi [Client],

Things are going well this month. Your service is running.

Thanks,
Support Team
""")

# A messy CRM export CSV
with open("workspace/internal/crm_exports/clients_export_2025.csv", "w") as f:
    f.write("""client_id,name,status,mrr,start_date,plan
001,Alfred's Plumbing,active,149,2025-01-15,Growth
002,Sunrise HVAC,churned,0,2024-09-01,Basic
003,Metro Electric,active,299,2024-11-20,Scale
004,Corner Bakery,paused,149,2025-02-01,Growth
005,Townview Realty,active,449,2024-07-10,Scale
""")

# A fake old invoice
with open("workspace/clients/alfreds_plumbing/invoices/inv_2025_01.txt", "w") as f:
    f.write("Invoice #001 | Alfred's Plumbing | Jan 2025 | $149.00 | PAID")

with open("workspace/clients/alfreds_plumbing/invoices/inv_2025_02.txt", "w") as f:
    f.write("Invoice #002 | Alfred's Plumbing | Feb 2025 | $149.00 | PAID")

with open("workspace/clients/alfreds_plumbing/invoices/inv_2025_03.txt", "w") as f:
    f.write("Invoice #003 | Alfred's Plumbing | Mar 2025 | $149.00 | PAID")

with open("workspace/clients/alfreds_plumbing/invoices/inv_2025_04.txt", "w") as f:
    f.write("Invoice #004 | Alfred's Plumbing | Apr 2025 | $149.00 | PAID")

# Client communication history
with open("workspace/clients/alfreds_plumbing/communications/email_log.txt", "w") as f:
    f.write("""2025-01-16: Onboarding call completed. Alfred happy with setup.
2025-02-01: Month 1 check-in. 47 messages handled, 12 bookings captured.
2025-03-01: Month 2 check-in. 63 messages handled, 18 bookings captured.
2025-04-01: Month 3 check-in. 71 messages handled, 22 bookings captured.
2025-04-28: Alfred's main contact (Sarah) left the company.
2025-05-01: Month 4 check-in email sent. NO REPLY RECEIVED.
2025-05-10: Usage data shows only 9 messages handled this month (vs. avg 60).
2025-05-12: Alfred asked via email: "Can you remind me what the contract terms are?"
""")

# Alfred's usage stats (raw data dump)
with open("workspace/clients/alfreds_plumbing/usage_stats_raw.json", "w") as f:
    json.dump({
        "client": "Alfred's Plumbing",
        "plan": "Growth",
        "monthly_rate_usd": 149,
        "months_active": 4,
        "usage_history": [
            {"month": "2025-02", "messages_handled": 47, "bookings_captured": 12, "avg_booking_value_usd": 180},
            {"month": "2025-03", "messages_handled": 63, "bookings_captured": 18, "avg_booking_value_usd": 180},
            {"month": "2025-04", "messages_handled": 71, "bookings_captured": 22, "avg_booking_value_usd": 180},
            {"month": "2025-05", "messages_handled": 9, "bookings_captured": 2, "avg_booking_value_usd": 180},
        ],
        "renewal_due": "2025-06-15"
    }, f, indent=2)

# Distractor: a generic "churn" article snippet (wrong framework)
with open("workspace/internal/crm_exports/churn_notes_generic.txt", "w") as f:
    f.write("""Generic churn prevention tips from internet:
1. Send a survey
2. Offer a discount
3. Escalate to manager
4. Close the ticket
These are informal notes, NOT the official process.
""")

# Finance distractors
with open("workspace/internal/finance/q1/revenue_summary.txt", "w") as f:
    f.write("Q1 2025 Revenue: $4,470 from 10 active clients. Churn: 2 clients.")

with open("workspace/internal/finance/q2/forecast.txt", "w") as f:
    f.write("Q2 2025 Forecast: $5,200 if 0 churn. At-risk clients: Alfred's Plumbing, Corner Bakery.")

# Marketing distractors
with open("workspace/marketing/campaigns/spring_promo.txt", "w") as f:
    f.write("Spring 2025 new client promo: 1st month free. Target: 5 new signups.")

with open("workspace/marketing/leads/leads_may2025.csv", "w") as f:
    f.write("lead_id,name,source,status\nL001,Fresh Floors LLC,referral,contacted\nL002,QuickFix Auto,ads,new\n")

# Sunrise HVAC distractor
with open("workspace/clients/other_clients/sunrise_hvac/notes.txt", "w") as f:
    f.write("Sunrise HVAC churned Sept 2024. Reason: found cheaper competitor. No winback attempted.")

# Metro Electric distractor
with open("workspace/clients/other_clients/metro_electric/notes.txt", "w") as f:
    f.write("Metro Electric on Scale plan $299/mo. Happy client. Referred 2 businesses.")

# Old onboarding checklist (incomplete/wrong)
with open("workspace/internal/templates_old/onboarding_old.txt", "w") as f:
    f.write("""Onboarding steps:
- Send welcome email
- Set up account
- Follow up after 1 month
(Outdated — do not use)
""")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(Path("/workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")