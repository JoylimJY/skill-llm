import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# ── Main skill root files (already exist, simulate a real project) ──────────
root_skill_md = """\
---
name: customer-analytics-platform
description: A platform for generating customer insights and recommendations.
---

# Customer Analytics Platform

This skill provides tools for customer segmentation, churn prediction, and product recommendations.

## Structure

See subskills/ for feature implementations.
"""

root_config = """{
  "platform": "customer-analytics",
  "version": "2.1.0",
  "features": ["segmentation", "churn-prediction"],
  "output_dir": "data/"
}
"""

# ── Existing subskill: segmentation (distractor) ────────────────────────────
seg_skill_md = """\
---
name: subskill-segmentation
description: Customer segmentation by RFM scoring.
---

# Segmentation Subskill

Uses RFM (Recency, Frequency, Monetary) scoring to segment customers into tiers.

## Usage

Run `python segment.py --input customers.csv` to generate segments.
"""

seg_script = """\
import csv
import json
import sys

def compute_rfm(customers):
    results = []
    for c in customers:
        score = int(c.get('purchases', 0)) * 2
        results.append({'id': c['id'], 'rfm_score': score, 'tier': 'gold' if score > 10 else 'silver'})
    return results

if __name__ == '__main__':
    print("Segmentation stub - not yet implemented for production.")
"""

seg_output_json = json.dumps([
    {"id": "C001", "rfm_score": 18, "tier": "gold"},
    {"id": "C002", "rfm_score": 6, "tier": "silver"},
    {"id": "C003", "rfm_score": 14, "tier": "gold"},
], indent=2)

# ── Existing data/ artifacts (distractors) ──────────────────────────────────
existing_data_report = json.dumps({
    "report": "segmentation_run_2024_01",
    "records": 1200,
    "tiers": {"gold": 340, "silver": 860}
}, indent=2)

existing_data_csv = "customer_id,segment,score\nC001,gold,18\nC002,silver,6\n"

# ── Distractor: a misplaced one-off script in root (bad practice example) ───
bad_root_script = """\
# TODO: move this somewhere proper
# One-off churn test - DO NOT leave here
import pandas as pd
df = pd.read_csv('data/customers.csv')
print(df.head())
"""

# ── Distractor: partial/broken config ───────────────────────────────────────
broken_config = """{
  "feature": "churn-prediction",
  "status": "draft",
  "model": null
}
"""

# ── Distractor: nested legacy folder ────────────────────────────────────────
legacy_notes = """\
Legacy segmentation notes from Q3 2023.
Do not use - superseded by RFM approach.
"""

legacy_sql = """\
SELECT customer_id, COUNT(*) as orders
FROM orders
WHERE created_at > '2023-01-01'
GROUP BY customer_id;
"""

# ─────────────────────────────────────────────────────────────────────────────
# Build directory structure
# ─────────────────────────────────────────────────────────────────────────────

dirs = [
    f"{WORKSPACE}",
    f"{WORKSPACE}/data",
    f"{WORKSPACE}/subskills",
    f"{WORKSPACE}/subskills/segmentation",
    f"{WORKSPACE}/subskills/segmentation/tests",
    f"{WORKSPACE}/legacy",
    f"{WORKSPACE}/legacy/sql",
    f"{WORKSPACE}/legacy/notes",
    f"{WORKSPACE}/docs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Write files
def write(path, content):
    with open(path, "w") as f:
        f.write(content)

# Root
write(f"{WORKSPACE}/SKILL.md", root_skill_md)
write(f"{WORKSPACE}/config.json", root_config)
write(f"{WORKSPACE}/churn_scratch.py", bad_root_script)      # distractor bad file
write(f"{WORKSPACE}/draft_config_churn.json", broken_config) # distractor

# Existing subskill: segmentation
write(f"{WORKSPACE}/subskills/segmentation/SKILL.md", seg_skill_md)
write(f"{WORKSPACE}/subskills/segmentation/segment.py", seg_script)
write(f"{WORKSPACE}/subskills/segmentation/tests/test_segment.py",
      "def test_compute_rfm():\n    assert True  # placeholder\n")

# Existing data artifacts
write(f"{WORKSPACE}/data/segmentation_report_2024_01.json", existing_data_report)
write(f"{WORKSPACE}/data/customer_segments.csv", existing_data_csv)

# Legacy distractors
write(f"{WORKSPACE}/legacy/notes/q3_2023_notes.txt", legacy_notes)
write(f"{WORKSPACE}/legacy/sql/customer_query.sql", legacy_sql)

# Docs distractor
write(f"{WORKSPACE}/docs/architecture.md", "# Architecture\n\nTBD - placeholder.\n")

print("Workspace initialized successfully.")
print(f"Files created under: {WORKSPACE}")