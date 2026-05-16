import os
import csv
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "reports/monthly",
    "reports/quarterly",
    "marketing/campaigns",
    "marketing/templates",
    "ops/billing",
    "ops/support",
    "product/roadmap",
    "analytics/dashboards",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "data/processed/acquisition_metrics_q1.csv": "month,new_signups,cac\n2024-01,45,120\n2024-02,52,115\n2024-03,61,108\n",
    "data/processed/revenue_2024.csv": "month,mrr,arr\n2024-01,8200,98400\n2024-02,8750,105000\n2024-03,9100,109200\n",
    "reports/monthly/nps_jan_2024.txt": "NPS Survey Results January 2024\nPromoters: 42\nPassives: 31\nDetractors: 12\nNPS Score: 35\n",
    "reports/quarterly/q1_summary.txt": "Q1 Business Summary\nTotal Revenue: $25,050\nNew Customers: 158\nSupport Tickets: 94\n",
    "marketing/campaigns/spring_promo.txt": "Spring Fitness Challenge Campaign\nDiscount: 20% off first month\nTarget: New signups\nBudget: $500\n",
    "marketing/templates/welcome_email.txt": "Subject: Welcome to FitStream!\nBody: Thanks for joining. Here is your starter plan.\n",
    "ops/billing/failed_payments_march.csv": "customer_id,amount,date,reason\nC0234,49,2024-03-15,card_declined\nC0571,29,2024-03-18,insufficient_funds\n",
    "ops/support/tickets_open.csv": "ticket_id,customer_id,issue,created_at\nT001,C0100,login_issue,2024-03-10\nT002,C0213,billing_question,2024-03-12\n",
    "product/roadmap/features_q2.txt": "Q2 Feature Roadmap\n- Video workout library expansion\n- AI form checker (beta)\n- Group challenge rooms\n- Nutrition tracker integration\n",
    "analytics/dashboards/kpi_definitions.txt": "KPI Definitions\nMAU: Monthly Active Users (logged in at least once)\nWAU: Weekly Active Users\nDAU: Daily Active Users\nARPU: Average Revenue Per User\n",
}
for path, content in distractors.items():
    (workspace / path).write_text(content)

# ── PRIMARY INPUT 1: Raw customer subscription data (messy) ────────────────
# January 2024 cohort: 120 customers signed up
# We need data for: start of month counts, end of month active counts, and cohort tracking
# Format: customer_id, cohort_month, signup_date, status_jan, status_feb, status_mar,
#         status_apr, status_may, status_jun, status_jul, status_aug, status_sep,
#         status_oct, status_nov, status_dec  (active/churned)
#
# ALSO: February & March subscription snapshots for monthly churn calculation

# Generate January cohort (120 customers)
jan_cohort = []
random.seed(42)
for i in range(1, 121):
    cid = f"C{1000+i}"
    # Survival probabilities per month (realistic decay)
    # Month 1 (Feb): 88% survival, Month 3 (Apr): 76%, Month 6 (Jul): 67%, Month 12 (Jan-25): 57%
    alive = [True]  # Jan: all alive
    for m in range(1, 12):
        thresholds = [0.88, 0.83, 0.79, 0.76, 0.74, 0.72, 0.70, 0.69, 0.68, 0.67, 0.65]
        # Random survival based on cumulative threshold
        alive.append(random.random() < thresholds[m-1] if alive[-1] else False)
    jan_cohort.append([cid, "2024-01"] + alive)

# Counts for cohort retention
jan_active_counts = [sum(1 for r in jan_cohort if r[2+i]) for i in range(12)]
# Month 0 = 120, then month 1..11

# Generate February snapshot data for monthly churn calculation
# Feb: started with 200 customers (includes Jan cohort survivors + pre-existing)
# Lost 18 customers during February
feb_start = 200
feb_churned = 18

# March: started with 210 customers, lost 11
mar_start = 210
mar_churned = 11

# Write the subscription snapshot file
with open(workspace / "data/raw/subscription_snapshots.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["month", "customers_at_start", "customers_lost", "customers_at_end", "new_customers"])
    writer.writerow(["2024-01", 185, 12, 173, 47])   # Jan: older data
    writer.writerow(["2024-02", feb_start, feb_churned, feb_start - feb_churned, 28])
    writer.writerow(["2024-03", mar_start, mar_churned, mar_start - mar_churned, 21])

# Write January cohort tracking
with open(workspace / "data/raw/jan_cohort_tracking.csv", "w", newline="") as f:
    writer = csv.writer(f)
    months = ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06",
              "2024-07","2024-08","2024-09","2024-10","2024-11","2024-12"]
    writer.writerow(["customer_id", "cohort_month"] + months)
    for row in jan_cohort:
        writer.writerow(row)

# Write summary counts file for cohort (so eval can verify agent's math)
cohort_summary = {"cohort": "2024-01", "initial_size": 120, "active_per_month": jan_active_counts}
with open(workspace / "data/raw/jan_cohort_counts.json", "w") as f:
    json.dump(cohort_summary, f, indent=2)

# ── PRIMARY INPUT 2: Cancellation survey export (messy, free-text + coded) ──
random.seed(7)

# Canonical reasons from SKILL.md cancellation survey
canonical_reasons = [
    "Not using it enough",
    "Too expensive",
    "Missing a feature I need",
    "Found a better alternative",
    "Product didn't deliver expected value",
    "Other",
]

# Messy free-text variants that map to canonical reasons
reason_variants = {
    "Not using it enough": [
        "I just don't have time to use it",
        "haven't logged in in weeks",
        "Not using it enough",
        "no time to work out",
        "barely used it",
        "I forgot I even had this",
        "not using it",
        "too busy to use the app",
    ],
    "Too expensive": [
        "Too expensive",
        "costs too much",
        "price is too high",
        "can't afford it anymore",
        "too pricey for what it offers",
        "the monthly fee is steep",
    ],
    "Missing a feature I need": [
        "Missing a feature I need",
        "no nutrition tracking",
        "needs live classes",
        "I need a running plan which isn't there",
        "missing features I want",
        "no Apple Watch integration",
    ],
    "Found a better alternative": [
        "Found a better alternative",
        "switched to Peloton",
        "using a different app now",
        "competitor had what I needed",
        "found something cheaper and better",
    ],
    "Product didn't deliver expected value": [
        "Product didn't deliver expected value",
        "didn't see results",
        "not what I expected",
        "didn't help me reach my goals",
        "underwhelmed with the content quality",
    ],
    "Other": [
        "moving abroad",
        "gym membership covers everything",
        "personal reasons",
        "Other",
        "doctor's advice to rest",
    ],
}

# Distribution: 35 not-using, 22 too-expensive, 15 missing-feature, 12 better-alt, 10 no-value, 6 other = 100
distribution = {
    "Not using it enough": 35,
    "Too expensive": 22,
    "Missing a feature I need": 15,
    "Found a better alternative": 12,
    "Product didn't deliver expected value": 10,
    "Other": 6,
}

survey_rows = []
cid_counter = 2000
for reason, count in distribution.items():
    variants = reason_variants[reason]
    for _ in range(count):
        cid_counter += 1
        text = random.choice(variants)
        survey_rows.append({
            "customer_id": f"C{cid_counter}",
            "cancel_date": f"2024-0{random.randint(1,3)}-{random.randint(1,28):02d}",
            "plan": random.choice(["basic_29", "pro_49", "elite_79"]),
            "months_subscribed": random.randint(1, 14),
            "cancellation_reason_text": text,
            "nps_before_cancel": random.randint(1, 7),
        })

random.shuffle(survey_rows)

with open(workspace / "data/raw/cancellation_survey_export.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["customer_id","cancel_date","plan","months_subscribed","cancellation_reason_text","nps_before_cancel"])
    writer.writeheader()
    writer.writerows(survey_rows)

# ── PRIMARY INPUT 3: At-risk users list ──────────────────────────────────
random.seed(99)
at_risk = []
for i in range(1, 26):
    last_login_days_ago = random.randint(31, 75)
    at_risk.append({
        "customer_id": f"CR{3000+i}",
        "name": f"User_{i}",
        "email": f"user{i}@fitstream-example.com",
        "plan": random.choice(["basic_29", "pro_49", "elite_79"]),
        "days_since_last_login": last_login_days_ago,
        "usage_drop_pct": random.randint(50, 95),
    })

with open(workspace / "data/raw/at_risk_users.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["customer_id","name","email","plan","days_since_last_login","usage_drop_pct"])
    writer.writeheader()
    writer.writerows(at_risk)

print("Workspace generated successfully.")
print(f"Jan cohort active counts: {jan_active_counts}")
print(f"Feb: start={feb_start}, lost={feb_churned}, churn_rate={feb_churned/feb_start*100:.2f}%")
print(f"Mar: start={mar_start}, lost={mar_churned}, churn_rate={mar_churned/mar_start*100:.2f}%")