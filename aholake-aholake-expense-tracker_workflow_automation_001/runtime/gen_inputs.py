import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/home/user/workspace")

# Create directory structure
dirs = [
    "scripts",
    "references",
    "expenses",
    "notes",
    "notes/meetings",
    "notes/goals",
    "reports",
    "reports/q1",
    "reports/archive",
    "config",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ---- Create the actual log_expense.py script ----
log_expense_script = r'''#!/usr/bin/env python3
"""Expense Tracker - Log and summarize daily expenses."""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def get_workspace(args_workspace=None):
    if args_workspace:
        return Path(args_workspace)
    return Path.home() / ".openclaw" / "workspace"


def get_expenses_dir(workspace):
    expenses_dir = workspace / "expenses"
    expenses_dir.mkdir(parents=True, exist_ok=True)
    return expenses_dir


def format_amount(amount):
    return f"{amount:,}"


def parse_amount(s):
    return int(s.replace(",", ""))


def get_month_file(expenses_dir, year_month):
    return expenses_dir / f"{year_month}.md"


def ensure_month_file(expenses_dir, year_month):
    filepath = get_month_file(expenses_dir, year_month)
    if not filepath.exists():
        with open(filepath, "w") as f:
            f.write(f"# Expenses - {year_month}\n\n")
            f.write("| Date | Category | Amount (VND) | Description | Tags |\n")
            f.write("|------|----------|-------------|-------------|------|\n")
    return filepath


def log_expense(args):
    workspace = get_workspace(args.workspace)
    expenses_dir = get_expenses_dir(workspace)

    if args.date:
        try:
            date_obj = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        date_obj = datetime.now()

    date_str = date_obj.strftime("%Y-%m-%d")
    year_month = date_obj.strftime("%Y-%m")

    filepath = ensure_month_file(expenses_dir, year_month)

    description = args.description or ""
    tags = args.tags or ""

    row = f"| {date_str} | {args.category} | {format_amount(args.amount)} | {description} | {tags} |\n"

    with open(filepath, "a") as f:
        f.write(row)

    print(f"✓ Logged: {args.category} {format_amount(args.amount)} VND on {date_str}")
    print(f"  File: {filepath}")


def parse_markdown_table(filepath):
    expenses = []
    with open(filepath, "r") as f:
        lines = f.readlines()

    in_table = False
    header_passed = False
    for line in lines:
        line = line.strip()
        if line.startswith("| Date |"):
            in_table = True
            header_passed = False
            continue
        if in_table and line.startswith("|---"):
            header_passed = True
            continue
        if in_table and header_passed and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                try:
                    amount = parse_amount(parts[2])
                    expenses.append({
                        "date": parts[0],
                        "category": parts[1],
                        "amount": amount,
                        "description": parts[3] if len(parts) > 3 else "",
                        "tags": parts[4] if len(parts) > 4 else "",
                    })
                except (ValueError, IndexError):
                    continue

    return expenses


def summarize(args):
    workspace = get_workspace(args.workspace)
    expenses_dir = get_expenses_dir(workspace)

    if args.year_month:
        year_month = args.year_month
    else:
        year_month = datetime.now().strftime("%Y-%m")

    filepath = get_month_file(expenses_dir, year_month)

    if not filepath.exists():
        if args.json:
            print(json.dumps({"year_month": year_month, "total": 0, "count": 0, "categories": {}}))
        else:
            print(f"No expenses found for {year_month}")
        return

    expenses = parse_markdown_table(filepath)

    total = sum(e["amount"] for e in expenses)
    count = len(expenses)
    categories = {}
    for e in expenses:
        cat = e["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "count": 0}
        categories[cat]["total"] += e["amount"]
        categories[cat]["count"] += 1

    if args.json:
        result = {
            "year_month": year_month,
            "total": total,
            "count": count,
            "categories": categories,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== Expense Summary: {year_month} ===")
        print(f"Total: {format_amount(total)} VND ({count} expenses)\n")
        print("By Category:")
        for cat, data in sorted(categories.items(), key=lambda x: -x[1]["total"]):
            print(f"  {cat}: {format_amount(data['total'])} VND ({data['count']} expenses)")


def main():
    parser = argparse.ArgumentParser(description="Expense Tracker")
    subparsers = parser.add_subparsers(dest="command")

    # log subcommand
    log_parser = subparsers.add_parser("log", help="Log an expense")
    log_parser.add_argument("amount", type=int, help="Amount in VND")
    log_parser.add_argument("category", help="Expense category")
    log_parser.add_argument("--description", "-d", default="", help="Description")
    log_parser.add_argument("--tags", "-t", default="", help="Comma-separated tags")
    log_parser.add_argument("--date", help="Date (YYYY-MM-DD)")
    log_parser.add_argument("--workspace", help="Workspace path")

    # summary subcommand
    summary_parser = subparsers.add_parser("summary", help="View monthly summary")
    summary_parser.add_argument("year_month", nargs="?", help="YYYY-MM")
    summary_parser.add_argument("--json", action="store_true", help="Output as JSON")
    summary_parser.add_argument("--workspace", help="Workspace path")

    args = parser.parse_args()

    if args.command == "log":
        log_expense(args)
    elif args.command == "summary":
        summarize(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "log_expense.py").write_text(log_expense_script)

# ---- Create references/categories.md ----
categories_md = """# Expense Categories

Common categories for organizing expenses. Use these as guidelines; create custom categories as needed.

## Essential Living

- **Housing** - Rent, mortgage, property tax, home insurance
- **Utilities** - Electricity, water, gas, internet, phone
- **Groceries** - Food shopping, household supplies
- **Healthcare** - Doctor visits, medication, health insurance

## Transportation

- **Vehicle** - Car payment, motorcycle, gas, maintenance
- **Public Transport** - Bus, taxi, Grab, bike rental
- **Parking** - Parking fees, toll roads

## Food & Drink

- **Dining** - Restaurants, cafes, food delivery
- **Coffee** - Coffee shops, café work sessions
- **Snacks** - Convenience stores, street food

## Personal

- **Clothing** - Clothes, shoes, accessories
- **Personal Care** - Haircuts, toiletries, cosmetics
- **Entertainment** - Movies, games, hobbies
- **Subscriptions** - Netflix, Spotify, gym, apps

## Work & Education

- **Work Expenses** - Equipment, software, coworking
- **Education** - Courses, books, training
- **Professional** - Certifications, conferences

## Financial

- **Debt Payment** - Credit card, loans, installments
- **Savings** - Emergency fund, investments
- **Insurance** - Life, health, vehicle insurance
- **Fees** - Bank fees, transaction fees

## Shopping

- **Electronics** - Gadgets, computers, accessories
- **Home** - Furniture, appliances, decor
- **Gifts** - Presents, celebrations
- **Shopping** - General shopping, online purchases

## Lifestyle

- **Travel** - Vacation, trips, hotels
- **Fitness** - Gym, sports, equipment
- **Social** - Outings with friends, dates
- **Pet** - Pet food, vet, supplies

## Other

- **Miscellaneous** - Uncategorized expenses
- **Emergency** - Unexpected urgent expenses
- **Transfer** - Money sent to family/friends
"""

(WORKSPACE / "references" / "categories.md").write_text(categories_md)

# ---- Distractor files ----
(WORKSPACE / "notes" / "meetings" / "2025-12-standup.md").write_text(
    "# Standup Notes\n- Reviewed Q4 budget\n- Action items pending\n"
)
(WORKSPACE / "notes" / "meetings" / "2026-01-kickoff.md").write_text(
    "# Kickoff Meeting\n- Set annual goals\n- Budget 50M VND for operations\n"
)
(WORKSPACE / "notes" / "goals" / "financial_goals_2026.md").write_text(
    "# Financial Goals 2026\n- Save 20% of income\n- Pay off motorcycle loan\n- Emergency fund: 30M VND\n"
)
(WORKSPACE / "reports" / "q1" / "placeholder.txt").write_text(
    "Q1 2026 report placeholder. Pending data collection.\n"
)
(WORKSPACE / "reports" / "archive" / "2025_annual.md").write_text(
    "# 2025 Annual Summary\nTotal spending: 480,000,000 VND\n"
)
(WORKSPACE / "config" / "settings.json").write_text(
    json.dumps({"currency": "VND", "locale": "vi-VN", "theme": "default"}, indent=2)
)
(WORKSPACE / "config" / "budget_targets.json").write_text(
    json.dumps({
        "2026-03": {"total": 15000000, "Dining": 3000000, "Coffee": 500000, "Shopping": 2000000},
        "2026-04": {"total": 15000000, "Dining": 3000000, "Coffee": 500000, "Shopping": 2000000}
    }, indent=2)
)
(WORKSPACE / "tmp" / "scratch.txt").write_text("temp notes: check gas bill\n")
(WORKSPACE / "notes" / "grocery_list.txt").write_text(
    "- Eggs\n- Milk\n- Bread\n- Coffee beans\n"
)
(WORKSPACE / "reports" / "spending_notes.txt").write_text(
    "March seems high on dining. Check coffee and transport.\n"
)
(WORKSPACE / "tmp" / "old_receipts_raw.txt").write_text(
    "March 3: coffee 45k\nMarch 3: lunch 85k\nMarch 5: grab 32k\nMarch 7: gym 300k\n"
)

# ---- The actual task input: a messy receipt dump for March and April 2026 ----
# This is the "raw input" the agent must process
receipts_data = """# Expense Receipts - To Be Logged

## March 2026

2026-03-01 | Grabbed morning coffee at Highlands | 55,000 VND | coffee
2026-03-01 | Team lunch at Bun Bo Hue restaurant | 180,000 VND | dining, work
2026-03-03 | Filled petrol for motorbike | 95,000 VND | vehicle
2026-03-05 | Bought new headphones from Thien Hoa | 1,200,000 VND | electronics, work
2026-03-10 | Netflix monthly subscription | 260,000 VND | subscriptions
2026-03-12 | Dentist appointment | 450,000 VND | healthcare
2026-03-15 | Coffee at The Coffee House (client meeting) | 75,000 VND | coffee, work
2026-03-20 | Grocery run at Vinmart | 620,000 VND | groceries
2026-03-25 | Paid electric + water bill | 850,000 VND | utilities
2026-03-28 | Night out with friends at bar | 350,000 VND | social, entertainment

## April 2026

2026-04-02 | Morning coffee + pastry | 65,000 VND | coffee
2026-04-05 | Dinner with family at Nha Hang Ngon | 720,000 VND | dining, family
2026-04-08 | Spotify + Apple One bundle | 215,000 VND | subscriptions
2026-04-10 | Grab bike rides throughout week | 145,000 VND | public transport
2026-04-14 | Bought birthday gift for colleague | 500,000 VND | gifts
2026-04-18 | Online course on Udemy | 399,000 VND | education
2026-04-22 | Weekend trip hotel stay | 2,500,000 VND | travel
2026-04-25 | Motorbike oil change + check | 320,000 VND | vehicle
2026-04-28 | Coffee + snacks while working remotely | 95,000 VND | coffee, work
2026-04-30 | Monthly gym membership | 500,000 VND | fitness
"""

(WORKSPACE / "tmp" / "receipts_to_log.txt").write_text(receipts_data)

print("Workspace generated successfully.")
print(f"Structure created at: {WORKSPACE}")