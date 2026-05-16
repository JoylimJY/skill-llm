import os
import random
import csv
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "data/raw",
    "data/interim",
    "data/processed",
    "data/archive",
    "reports/q1",
    "reports/q2",
    "reports/drafts",
    "scripts/legacy",
    "scripts/utils",
    "config",
    "notebooks",
    "models/baseline",
    "models/candidates",
    "docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────
(workspace / "config" / "db_config.json").write_text(json.dumps({"host": "localhost", "port": 5432, "db": "retail"}))
(workspace / "config" / "feature_flags.yaml").write_text("loyalty_v2: true\nchurn_model: false\n")
(workspace / "docs" / "data_dictionary.md").write_text("# Data Dictionary\n\n- customer_id: unique customer identifier\n- tenure_days: days since first purchase\n")
(workspace / "reports" / "q1" / "q1_summary.txt").write_text("Q1 Revenue: $4.2M\nChurn Rate: 18%\n")
(workspace / "reports" / "q2" / "q2_summary.txt").write_text("Q2 Revenue: $4.8M\nChurn Rate: 15%\n")
(workspace / "reports" / "drafts" / "draft_notes.txt").write_text("Needs proper statistical analysis. TODO: A/B test evaluation.\n")
(workspace / "scripts" / "legacy" / "old_etl.py").write_text("# Legacy ETL - deprecated\nimport pandas as pd\nprint('old pipeline')\n")
(workspace / "scripts" / "utils" / "helpers.py").write_text("def fmt_currency(v):\n    return f'${v:,.2f}'\n")
(workspace / "notebooks" / "exploration_v1.ipynb").write_text('{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}')
(workspace / "notebooks" / "exploration_v2.ipynb").write_text('{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}')
(workspace / "data" / "archive" / "customers_2023.csv").write_text("customer_id,revenue\n1,200\n2,450\n")
(workspace / "data" / "interim" / "partial_clean.csv").write_text("customer_id,region\n1,North\n2,South\n")
(workspace / "models" / "baseline" / "baseline_metrics.json").write_text(json.dumps({"accuracy": 0.72, "auc": 0.68}))
(workspace / "models" / "candidates" / "README.txt").write_text("Candidate models pending evaluation.\n")

# ── Main dataset: customer churn + A/B test combined (messy) ───────────────
# This is the primary file the agent must use
rows = []
regions = ["North", "South", "East", "West", None, "NORTH", "south", "E", "W", "Northeast"]
products = ["Basic", "Premium", "Enterprise", None, "basic", "PREMIUM", "Ent.", "enterprise"]
date_formats = [
    lambda d: d.strftime("%m/%d/%Y"),
    lambda d: d.strftime("%Y-%m-%d"),
    lambda d: d.strftime("%d-%m-%Y"),
    lambda d: d.strftime("%b %d %Y"),
]

base_date = datetime(2023, 1, 1)
for i in range(1, 801):
    tenure = random.randint(10, 1200)
    monthly_spend = round(random.uniform(20, 500), 2)
    logins = random.randint(0, 90)
    support_tickets = random.randint(0, 15)
    variant = random.choice(["A", "B"])
    # Churn logic: higher support tickets + low logins + short tenure → more likely to churn
    churn_prob = (support_tickets / 15) * 0.4 + (1 - logins / 90) * 0.35 + (1 - min(tenure, 500) / 500) * 0.25
    if variant == "B":
        churn_prob *= 0.82  # B variant reduces churn
    churned = 1 if random.random() < churn_prob else 0
    converted = 1 if random.random() < (0.12 if variant == "A" else 0.17) else 0
    revenue = round(monthly_spend * random.uniform(0.8, 1.3) if converted else 0, 2)
    signup_date = base_date + timedelta(days=random.randint(0, 365))
    fmt = random.choice(date_formats)
    date_str = fmt(signup_date)
    region = random.choice(regions)
    product = random.choice(products)
    # Introduce messy revenue formatting occasionally
    rev_str = f"${revenue:,.2f}" if (i % 7 == 0) else str(revenue)
    # Introduce duplicate rows
    rows.append({
        "customer_id": i,
        "signup_date": date_str,
        "region": region,
        "product_tier": product,
        "tenure_days": tenure,
        "monthly_spend": monthly_spend,
        "logins_last_90d": logins,
        "support_tickets": support_tickets,
        "ab_variant": variant,
        "converted": converted,
        "revenue": rev_str,
        "churned": churned,
    })

# Add ~30 duplicate rows
for _ in range(30):
    rows.append(random.choice(rows[:700]))

# Add some rows with missing churned value
for i in range(5):
    r = dict(random.choice(rows[:100]))
    r["churned"] = ""
    rows.append(r)

random.shuffle(rows)

fieldnames = ["customer_id", "signup_date", "region", "product_tier", "tenure_days",
              "monthly_spend", "logins_last_90d", "support_tickets", "ab_variant",
              "converted", "revenue", "churned"]

out_path = workspace / "data" / "raw" / "customer_loyalty_study.csv"
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows → {out_path}")

# ── Mock cellcog SDK package layout ───────────────────────────────────────
sdk_dir = workspace / "cellcog_sdk"
sdk_dir.mkdir(exist_ok=True)
(sdk_dir / "__init__.py").write_text("")
# The agent must write its own script that uses the SDK
print("Workspace ready.")