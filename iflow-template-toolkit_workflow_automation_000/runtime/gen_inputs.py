#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "config",
    "scripts/legacy",
    "scripts/utils",
    "templates",
    "logs",
    "i18n_overrides",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/app_settings.yaml": "environment: production\nlog_level: INFO\nmax_retries: 3\n",
    "config/db_config.yaml": "host: localhost\nport: 5432\ndbname: logistics\n",
    "logs/error.log": "[ERROR] 2024-01-15 Connection timeout\n[WARN]  2024-01-15 Retry attempt 2\n",
    "logs/access.log": "GET /api/shipments 200\nPOST /api/orders 201\n",
    "scripts/legacy/migrate_v1.py": "# deprecated migration script\ndef migrate(): pass\n",
    "scripts/utils/helpers.py": "def slugify(s): return s.lower().replace(' ', '-')\n",
    "reports/archive/Q3_summary.txt": "Total shipments: 1842\nDelivered: 1600\nPending: 242\n",
    "reports/drafts/draft_report.txt": "DRAFT - DO NOT USE\nThis template is outdated.\n",
    "i18n_overrides/overrides.json": json.dumps({"en": {"old_key": "old value"}}),
    "data/processed/cleaned_orders_v0.csv": "id,status\n001,DONE\n002,FAIL\n",
    "data/raw/raw_dump_2024.jsonl": json.dumps({"id": "X001", "note": "legacy"}) + "\n",
    "scripts/utils/date_utils.py": "import datetime\ndef today(): return datetime.date.today()\n",
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# ── core input: shipment data ────────────────────────────────────────────────
shipments = [
    {"tracking_id": "SHP-1001", "destination": "Shanghai", "status": "active",    "carrier": "FastFreight"},
    {"tracking_id": "SHP-1002", "destination": "Berlin",   "status": "pending",   "carrier": "EuroLogix"},
    {"tracking_id": "SHP-1003", "destination": "Chicago",  "status": "cancelled", "carrier": "MidWest Cargo"},
    {"tracking_id": "SHP-1004", "destination": "Mumbai",   "status": "active",    "carrier": "IndiaShip"},
    {"tracking_id": "SHP-1005", "destination": "Toronto",  "status": "pending",   "carrier": "NorthExpress"},
]

with open(os.path.join(WORKSPACE, "data/raw/shipments.json"), "w") as f:
    json.dump({"region": "APAC-EMEA-NA", "operator": "Alex", "shipments": shipments}, f, indent=2)

# ── template file for the agent to use ──────────────────────────────────────
# NOTE: This template is intentionally incomplete/raw so the agent must
# understand the syntax to wire everything together.
template_content = """\
{{report_header}}

Operator: {{operator}}
Region: {{region}}

{% for shipment in shipments %}
{% if first %}--- BEGIN SHIPMENT LIST ---
{% endif %}
[{{index1}}] Tracking: {{tracking_id}} | Destination: {{destination}} | Carrier: {{carrier}}
  Status Note: {% if status == "active" %}IN TRANSIT{% elif status == "pending" %}AWAITING DISPATCH{% else %}ORDER CANCELLED{% endif %}
{% if last %}--- END SHIPMENT LIST ---
{% endif %}
{% endfor %}

{{report_footer}}
"""
with open(os.path.join(WORKSPACE, "templates/shipment_summary.tmpl"), "w") as f:
    f.write(template_content)

# ── translation hints file (raw, unstructured — agent must interpret) ────────
# This is NOT a ready-to-use config; it's raw notes that the agent must
# turn into the correct init_translator call.
translation_notes = """\
# Translation Keys Needed for Report
# Format: key | english_text | chinese_text

report_header  | Shipment Status Report  | 货物状态报告
report_footer  | End of Report. Prepared by: {operator} | 报告结束。由{operator}编制
welcome_note   | Welcome, {operator}! | 欢迎, {operator}!
"""
with open(os.path.join(WORKSPACE, "data/raw/translation_notes.txt"), "w") as f:
    f.write(translation_notes)

# ── task specification ───────────────────────────────────────────────────────
task_spec = """\
TASK:
Generate two localized shipment reports using the toolkit installed in /skills/iflow-template-toolkit.

Files to produce:
  reports/shipment_report_en.md  — English version
  reports/shipment_report_zh.md  — Chinese (zh) version

Data source: data/raw/shipments.json
Template:    templates/shipment_summary.tmpl
Translations: data/raw/translation_notes.txt (parse and use these)

Both reports must:
  - Use the template engine to render the template with shipment data.
  - Replace {{report_header}} and {{report_footer}} with translated strings.
  - The footer must include the operator's name via interpolation.
  - Shipment list items must be correctly numbered starting from 1.
  - The first shipment block must include the '--- BEGIN SHIPMENT LIST ---' marker.
  - The last shipment block must include the '--- END SHIPMENT LIST ---' marker.
  - Each shipment's status must map to the correct label:
      active    -> IN TRANSIT
      pending   -> AWAITING DISPATCH
      cancelled -> ORDER CANCELLED
"""
with open(os.path.join(WORKSPACE, "TASK.md"), "w") as f:
    f.write(task_spec)

print("Workspace initialized.")