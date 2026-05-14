import os
import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "business/marketing/campaigns",
    "business/marketing/analytics",
    "business/finance/invoices",
    "business/finance/reports",
    "business/product/roadmap",
    "business/product/specs",
    "ops/infra/configs",
    "ops/infra/logs",
    "ops/support/tickets",
    "data/raw/exports",
    "data/processed",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "business/marketing/campaigns/q1_email_blasts.txt": "Q1 email campaigns sent to 3200 subscribers. Open rate 22%. Click-through 4.5%.",
    "business/marketing/analytics/ad_spend_2024.csv": "month,spend,clicks\nJan,1200,340\nFeb,1500,410\nMar,1100,290",
    "business/finance/invoices/invoice_template.txt": "Invoice #XXXX\nDate: \nDue: Net-30\nAmount: $",
    "business/finance/reports/annual_revenue_2023.txt": "Total Revenue 2023: $142,000\nMRR End of Year: $11,833",
    "business/product/roadmap/features_q2.txt": "Q2 Features:\n- Bulk export\n- Zapier integration\n- Custom branding",
    "business/product/specs/onboarding_flow_v2.txt": "Step 1: Account creation\nStep 2: Profile setup\nStep 3: First project\nStep 4: Invite team",
    "ops/infra/configs/server_config.json": json.dumps({"region": "us-east-1", "instance": "t3.small", "autoscale": False}),
    "ops/infra/logs/deploy_log_2024-03-01.txt": "[2024-03-01 09:12:33] Deploy v2.4.1 SUCCESS\n[2024-03-01 09:12:45] Health check OK",
    "ops/support/tickets/open_tickets_march.txt": "TKT-201: Login issue - HIGH\nTKT-202: Export bug - MED\nTKT-203: Billing question - LOW",
    "data/raw/exports/stripe_payments_feb.csv": "customer_id,amount,status\nc_001,49,succeeded\nc_002,49,failed\nc_003,99,succeeded",
    "data/processed/churn_notes_old.txt": "Old notes from 2022: churn was around 8% back then. No structured tracking.",
    "business/marketing/analytics/social_metrics.txt": "Twitter followers: 1240\nLinkedIn: 890\nInstagram: 340",
}
for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Core Input Data Generation ───────────────────────────────────────────────
# Reference date: analysis run on 2024-04-01
REFERENCE_DATE = datetime(2024, 4, 1)

# ── File 1: customers.csv
# Columns: customer_id, signup_date, status (active/churned), plan (basic/pro),
#          last_login_date, monthly_logins_baseline (avg over first 60 days),
#          monthly_logins_last30 (last 30 days)
# We'll create 130 customers total with varied states

customers = []
cid = 1

# Cohort Jan 2024 (91 days ago from April 1) - 40 customers
# Some churned, some active
jan_signups = []
for i in range(40):
    signup = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 30))
    days_since_signup = (REFERENCE_DATE - signup).days  # ~60-90 days
    if i < 8:  # 8 churned = 20% churn for this cohort
        status = "churned"
        last_login = signup + timedelta(days=random.randint(5, 45))
        baseline = random.randint(3, 8)
        last30 = 0
        churn_reason = random.choice(["not_using_enough", "too_expensive", "missing_feature", "found_alternative", "no_value"])
    else:
        status = "active"
        last_login = REFERENCE_DATE - timedelta(days=random.randint(0, 35))
        baseline = random.randint(8, 25)
        last30 = random.randint(1, baseline)
        churn_reason = ""
    customers.append({
        "customer_id": f"C{cid:04d}",
        "signup_date": signup.strftime("%Y-%m-%d"),
        "status": status,
        "plan": random.choice(["basic", "pro"]),
        "last_login_date": last_login.strftime("%Y-%m-%d"),
        "monthly_logins_baseline": baseline,
        "monthly_logins_last30": last30,
        "churn_reason": churn_reason,
        "monthly_spend": 49 if random.random() < 0.6 else 99,
    })
    cid += 1
    jan_signups.append(customers[-1])

# Cohort Feb 2024 (29-59 days ago) - 35 customers
feb_signups = []
for i in range(35):
    signup = datetime(2024, 2, 1) + timedelta(days=random.randint(0, 27))
    if i < 4:  # ~11% churn
        status = "churned"
        last_login = signup + timedelta(days=random.randint(3, 25))
        baseline = random.randint(2, 6)
        last30 = 0
        churn_reason = random.choice(["not_using_enough", "too_expensive", "missing_feature"])
    else:
        status = "active"
        last_login = REFERENCE_DATE - timedelta(days=random.randint(0, 40))
        baseline = random.randint(6, 20)
        last30 = random.randint(0, baseline)
        churn_reason = ""
    customers.append({
        "customer_id": f"C{cid:04d}",
        "signup_date": signup.strftime("%Y-%m-%d"),
        "status": status,
        "plan": random.choice(["basic", "pro"]),
        "last_login_date": last_login.strftime("%Y-%m-%d"),
        "monthly_logins_baseline": baseline,
        "monthly_logins_last30": last30,
        "churn_reason": churn_reason,
        "monthly_spend": 49 if random.random() < 0.6 else 99,
    })
    cid += 1

# Cohort Mar 2024 (1-30 days ago) - 30 customers, all active (recent signup)
for i in range(30):
    signup = datetime(2024, 3, 1) + timedelta(days=random.randint(0, 30))
    if signup > REFERENCE_DATE:
        signup = REFERENCE_DATE - timedelta(days=1)
    status = "active"
    last_login = REFERENCE_DATE - timedelta(days=random.randint(0, 15))
    baseline = random.randint(4, 15)
    last30 = random.randint(1, baseline)
    churn_reason = ""
    customers.append({
        "customer_id": f"C{cid:04d}",
        "signup_date": signup.strftime("%Y-%m-%d"),
        "status": status,
        "plan": random.choice(["basic", "pro"]),
        "last_login_date": last_login.strftime("%Y-%m-%d"),
        "monthly_logins_baseline": baseline,
        "monthly_logins_last30": last30,
        "churn_reason": churn_reason,
        "monthly_spend": 49 if random.random() < 0.6 else 99,
    })
    cid += 1

# Older cohort: Oct-Dec 2023 (91-183 days ago) - 25 customers
for i in range(25):
    signup = datetime(2023, 10, 1) + timedelta(days=random.randint(0, 91))
    if i < 7:  # 28% churned over time
        status = "churned"
        last_login = signup + timedelta(days=random.randint(10, 60))
        baseline = random.randint(3, 12)
        last30 = 0
        churn_reason = random.choice(["not_using_enough", "too_expensive", "missing_feature", "found_alternative", "no_value"])
    else:
        status = "active"
        last_login = REFERENCE_DATE - timedelta(days=random.randint(0, 50))
        baseline = random.randint(10, 30)
        last30 = random.randint(0, baseline)
        churn_reason = ""
    customers.append({
        "customer_id": f"C{cid:04d}",
        "signup_date": signup.strftime("%Y-%m-%d"),
        "status": status,
        "plan": random.choice(["basic", "pro"]),
        "last_login_date": last_login.strftime("%Y-%m-%d"),
        "monthly_logins_baseline": baseline,
        "monthly_logins_last30": last30,
        "churn_reason": churn_reason,
        "monthly_spend": 49 if random.random() < 0.6 else 99,
    })
    cid += 1

# Write customers.csv
customers_path = os.path.join(workspace, "data/raw/exports/customers.csv")
fieldnames = ["customer_id", "signup_date", "status", "plan", "last_login_date",
              "monthly_logins_baseline", "monthly_logins_last30", "churn_reason", "monthly_spend"]
with open(customers_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(customers)

# ── File 2: monthly_snapshot.csv
# Snapshot of each month: customers at start, customers lost
# Used for churn rate calculation
monthly_data = [
    {"month": "2023-10", "customers_start": 60, "customers_lost": 7},
    {"month": "2023-11", "customers_start": 68, "customers_lost": 4},
    {"month": "2023-12", "customers_start": 78, "customers_lost": 9},  # > 10% churn
    {"month": "2024-01", "customers_start": 85, "customers_lost": 6},
    {"month": "2024-02", "customers_start": 115, "customers_lost": 5},
    {"month": "2024-03", "customers_start": 125, "customers_lost": 4},  # < 5%
]
monthly_path = os.path.join(workspace, "data/raw/exports/monthly_snapshot.csv")
with open(monthly_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["month", "customers_start", "customers_lost"])
    writer.writeheader()
    writer.writerows(monthly_data)

# ── File 3: cohort_retention.csv
# For Jan 2024 cohort: retention at 1m, 3m, 6m, 12m (some are NaN as not yet reached)
cohort_data = [
    {"cohort": "2023-01", "cohort_size": 55, "month_1_active": 50, "month_3_active": 42, "month_6_active": 38, "month_12_active": 30},
    {"cohort": "2023-04", "cohort_size": 48, "month_1_active": 44, "month_3_active": 35, "month_6_active": 28, "month_12_active": ""},
    {"cohort": "2023-07", "cohort_size": 62, "month_1_active": 55, "month_3_active": 46, "month_6_active": "", "month_12_active": ""},
    {"cohort": "2023-10", "cohort_size": 70, "month_1_active": 63, "month_3_active": "", "month_6_active": "", "month_12_active": ""},
    {"cohort": "2024-01", "cohort_size": 85, "month_1_active": "", "month_3_active": "", "month_6_active": "", "month_12_active": ""},
]
cohort_path = os.path.join(workspace, "data/raw/exports/cohort_retention.csv")
with open(cohort_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["cohort", "cohort_size", "month_1_active", "month_3_active", "month_6_active", "month_12_active"])
    writer.writeheader()
    writer.writerows(cohort_data)

# ── Write a brief context file (not a hint, just business context) ──────────
context = """Business Context
================
Business: DesignFlow - Project management SaaS for freelance designers
Analysis Date: 2024-04-01
Current active customer count: 130
Subscription plans: Basic ($49/mo), Pro ($99/mo)

This data export was pulled from our payment processor and internal analytics.
Files are in: data/raw/exports/
"""
with open(os.path.join(workspace, "business_context.txt"), "w") as f:
    f.write(context)

print("Workspace generated successfully.")
print(f"Total customers in dataset: {len(customers)}")