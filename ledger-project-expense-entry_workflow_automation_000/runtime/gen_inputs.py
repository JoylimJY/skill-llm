import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory skeleton ---
dirs = [
    "projects/scripts",
    "projects/data",
    "projects/docs",
    "projects/reports/2024",
    "projects/reports/2025",
    "projects/config",
    "projects/archive/2023",
    "projects/archive/2024",
    "internal/hr",
    "internal/finance/q1",
    "internal/finance/q2",
    "internal/ops",
    "tools/utils",
    "tools/deprecated",
    "docs/api",
    "docs/internal",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_content = {
    "projects/config/db_config.yaml": "host: localhost\nport: 5432\ndbname: ledger_dev\n",
    "projects/config/currencies.json": json.dumps({"supported": ["CNY", "USD", "JPY", "EUR", "TWD"], "default": "CNY"}, indent=2),
    "projects/reports/2024/annual_summary.csv": "project,total_expense,total_income\nOpenClaw,12450.00,0\nNovaMind,8900.00,5000.00\nPixelFarm,3200.00,0\n",
    "projects/reports/2025/q1_summary.csv": "project,total_expense\nOpenClaw,3100.00\nNovaMind,1200.00\n",
    "projects/archive/2023/ledger_2023_01.jsonl": json.dumps({"date":"2023-01-15","direction":"支出","amount":500,"currency":"CNY","description":"OpenClaw - 服务器","tags":["开发成本","服务器"]}) + "\n",
    "projects/archive/2024/ledger_2024_06.jsonl": json.dumps({"date":"2024-06-10","direction":"支出","amount":89,"currency":"CNY","description":"NovaMind - 域名续费","tags":["开发成本","域名"]}) + "\n",
    "internal/hr/headcount.txt": "Engineering: 4\nDesign: 2\nOps: 1\n",
    "internal/finance/q1/budget_q1.json": json.dumps({"total_budget": 50000, "spent": 23400, "currency": "CNY"}, indent=2),
    "internal/finance/q2/budget_q2.json": json.dumps({"total_budget": 50000, "spent": 0, "currency": "CNY"}, indent=2),
    "internal/ops/infra_notes.md": "# Infra Notes\n\n- All servers provisioned via Hetzner\n- Domain registrar: Namesilo\n- CDN: Cloudflare (free tier)\n",
    "tools/utils/parse_csv.py": "import csv, sys\nfor row in csv.DictReader(open(sys.argv[1])):\n    print(row)\n",
    "tools/deprecated/old_ledger_importer.py": "# DEPRECATED - do not use\n# This script was replaced by add_ledger_entry.py\nraise RuntimeError('Deprecated')\n",
    "docs/api/ledger_api.md": "# Ledger API (internal)\n\nBase: http://localhost:8080\n\nEndpoints:\n  POST /entry  - Add a ledger entry (use CLI instead)\n  GET  /report - Fetch monthly report\n",
    "docs/internal/glossary.md": "# Glossary\n\n- 支出: Expense (outgoing money)\n- 收入: Income (incoming money)\n- JSONL: JSON Lines format, one JSON object per line\n",
}

for path, content in distractor_content.items():
    (WORKSPACE / path).write_text(content, encoding="utf-8")

# --- CATEGORY_CATALOG.md (the key reference document) ---
category_catalog = """\
# Category Catalog

This document defines the valid tags, major categories, and types for ledger entries.

## Major Categories

| major_category | description |
|---|---|
| 开发成本 | All costs directly related to software development infrastructure |
| 生活消费 | Personal/team lifestyle, meals, transport |
| 运营成本 | Business operations including marketing, legal, and admin |

## Tags (use these exact values)

### 开发成本
- `服务器` — cloud/VPS server costs
- `域名` — domain registration and renewal
- `通讯网络` — network, CDN, or communication services
- `软件授权` — software licenses and SaaS subscriptions
- `开发工具` — IDEs, CI/CD tools

### 生活消费
- `外卖` — food delivery
- `下馆子` — dine-in restaurant
- `饮料零食` — drinks and snacks
- `打车` — taxi/rideshare
- `交通卡` — public transit card top-up
- `火车` — train tickets
- `飞机` — flight tickets

### 运营成本
- `广告投放` — paid advertising
- `法律咨询` — legal services
- `会计服务` — accounting/bookkeeping services
- `办公耗材` — office supplies

## Types

| type | values |
|---|---|
| direction | 支出, 收入 |
| currency | CNY, USD, JPY, EUR, TWD |
| source | manual, import, api |
| batch | manual, scheduled, bulk |

## Notes

- Tags must match exactly (case-sensitive Chinese characters).
- Multiple tags allowed, comma-separated.
- If a message mentions "subscription" or "SaaS", prefer `软件授权` over `服务器`.
- If a message mentions "CDN" or "bandwidth", prefer `通讯网络`.
"""
(WORKSPACE / "projects/docs/CATEGORY_CATALOG.md").write_text(category_catalog, encoding="utf-8")

# --- The main script: add_ledger_entry.py ---
# This script is realistic and actually works — it writes JSONL to the correct month file.
add_ledger_script = '''\
#!/usr/bin/env python3
"""
Ledger entry appender. Writes one JSONL record to the correct monthly file.
Month file path: <data-root>/ledger_<YYYY>_<MM>.jsonl
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Append a ledger entry.")
    parser.add_argument("--data-root", required=True, help="Root directory for ledger data files.")
    parser.add_argument("--date", required=True, help="Entry date in YYYY-MM-DD format.")
    parser.add_argument("--direction", required=True, choices=["支出", "收入"], help="支出 or 收入")
    parser.add_argument("--amount", required=True, type=float, help="Numeric amount.")
    parser.add_argument("--currency", required=True, help="Currency code e.g. CNY, USD, JPY")
    parser.add_argument("--description", required=True, help="Human-readable description.")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    parser.add_argument("--source", required=True, help="Entry source e.g. manual, import, api")
    parser.add_argument("--batch", required=True, help="Batch identifier e.g. manual, scheduled")
    args = parser.parse_args()

    try:
        entry_date = datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Invalid date format: {args.date}. Expected YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    data_root = Path(args.data_root)
    data_root.mkdir(parents=True, exist_ok=True)

    month_file = data_root / f"ledger_{entry_date.year}_{entry_date.month:02d}.jsonl"

    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    record = {
        "date": args.date,
        "direction": args.direction,
        "amount": args.amount,
        "currency": args.currency,
        "description": args.description,
        "tags": tags_list,
        "source": args.source,
        "batch": args.batch,
    }

    with month_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\\n")

    print(f"OK: Appended to {month_file}")

if __name__ == "__main__":
    main()
'''
(WORKSPACE / "projects/scripts/add_ledger_entry.py").write_text(add_ledger_script, encoding="utf-8")

# --- SKILL.md ---
skill_md = """\
---
name: ledger-project-expense-entry
description: Record natural-language project expense messages into ledger JSONL. Use when user sends "项目+支出" directly (e.g., "OpenClaw 服务器 89"), wants quick记账, or asks to append project spending. Default to expense and CNY unless user explicitly says otherwise.
---

# Ledger Project Expense Entry

Use this skill for fast bookkeeping from short natural-language messages.

## Defaults

- `direction`: default `支出`
- `currency`: default `CNY`
- `date`: default today (Asia/Taipei)

Only change defaults if user explicitly provides different values.

## Parse target

Extract from message:

- `project` (项目名)
- `description` (消费内容)
- `amount` (number)
- optional `date`
- optional `currency`
- optional `direction` (`收入`/`支出`)
- optional `tags`

If project and description are both present, build description as:

- `<project> - <description>`

If only one exists, use that field directly.

If amount is missing, ask one short clarification question.

## Write command

**IMPORTANT: Get today's date (YYYY-MM-DD) first, for determining which month file to write to.**

```bash
# Get today's date in Asia/Taipei timezone
CURRENT_DATE=$(TZ='Asia/Taipei' date +%Y-%m-%d)
```

Then append via existing script:

```bash
python3 projects/scripts/add_ledger_entry.py \\
  --data-root projects/data \\
  --date "$CURRENT_DATE" \\
  --direction <支出|收入> \\
  --amount <number> \\
  --currency <CNY|USD|JPY|...> \\
  --description <project-description> \\
  --tags <tag1,tag2,...> \\
  --source manual \\
  --batch manual
```

## Category catalog (must check before writing)

Before each write, check:

- `projects/docs/CATEGORY_CATALOG.md`

Selection policy:

- Prefer existing values from catalog (`tags`/`major_category`/`type`/`currency`).
- If user gives a new tag not in catalog and meaning is clear, write it; otherwise ask one short confirmation.
- If uncertain, keep optional fields empty rather than inventing noisy labels.

## Tag suggestion rules

- If user gives tags, use them directly.
- If user does not give tags:
  - project/infra/subscription/domain/server -> `开发成本` / `服务器` / `域名` / `通讯网络` (pick the closest one)
  - meal/drink -> `外卖` / `下馆子` / `饮料零食`
  - ride/transport -> `打车` / `交通卡` / `火车` / `飞机`
- If still uncertain, keep tags empty.

## Response format

After appending, reply with:

- month file path
- one-line summary: `日期 | 流向 | 金额币种 | 描述`
"""
(WORKSPACE / "SKILL.md").write_text(skill_md, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))}")