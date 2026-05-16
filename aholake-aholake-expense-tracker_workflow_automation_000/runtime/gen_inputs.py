import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# Create the expense tracker script directory structure (simulating the existing skill)
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

references_dir = WORKSPACE / "references"
references_dir.mkdir(parents=True, exist_ok=True)

expenses_dir = WORKSPACE / "expenses"
expenses_dir.mkdir(parents=True, exist_ok=True)

# Write the actual log_expense.py script (this is the skill's script)
log_expense_script = '''#!/usr/bin/env python3
"""Expense tracker script for logging and summarizing expenses."""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path


def get_expenses_dir(workspace=None):
    if workspace:
        base = Path(workspace)
    else:
        base = Path.home() / ".openclaw" / "workspace"
    expenses = base / "expenses"
    expenses.mkdir(parents=True, exist_ok=True)
    return expenses


def format_amount(amount):
    return f"{int(amount):,}"


def get_month_file(year_month, workspace=None):
    expenses_dir = get_expenses_dir(workspace)
    return expenses_dir / f"{year_month}.md"


def parse_amount(s):
    return int(s.replace(",", ""))


def read_expenses(year_month, workspace=None):
    filepath = get_month_file(year_month, workspace)
    if not filepath.exists():
        return []
    
    expenses = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    in_table = False
    header_passed = False
    for line in lines:
        line = line.strip()
        if line.startswith("| Date"):
            in_table = True
            header_passed = False
            continue
        if in_table and line.startswith("|---"):
            header_passed = True
            continue
        if in_table and header_passed and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5:
                try:
                    expense = {
                        "date": parts[0],
                        "category": parts[1],
                        "amount": parse_amount(parts[2]),
                        "description": parts[3],
                        "tags": parts[4],
                    }
                    expenses.append(expense)
                except (ValueError, IndexError):
                    pass
    return expenses


def log_expense(amount, category, description="", tags="", date=None, workspace=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    year_month = date[:7]
    filepath = get_month_file(year_month, workspace)
    
    if not filepath.exists():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Expenses - {year_month}\\n\\n")
            f.write("| Date | Category | Amount (VND) | Description | Tags |\\n")
            f.write("|------|----------|-------------|-------------|------|\\n")
    
    formatted_amount = format_amount(amount)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"| {date} | {category} | {formatted_amount} | {description} | {tags} |\\n")
    
    print(f"Logged: {category} {formatted_amount} VND on {date} -> {filepath}")
    return filepath


def summarize(year_month, as_json=False, workspace=None):
    expenses = read_expenses(year_month, workspace)
    
    total = sum(e["amount"] for e in expenses)
    count = len(expenses)
    
    by_category = {}
    for e in expenses:
        cat = e["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "count": 0}
        by_category[cat]["total"] += e["amount"]
        by_category[cat]["count"] += 1
    
    result = {
        "month": year_month,
        "total": total,
        "count": count,
        "by_category": by_category,
    }
    
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\\n=== Expense Summary: {year_month} ===")
        print(f"Total: {format_amount(total)} VND")
        print(f"Transactions: {count}")
        print("\\nBy Category:")
        for cat, data in sorted(by_category.items(), key=lambda x: -x[1]["total"]):
            print(f"  {cat}: {format_amount(data['total'])} VND ({data['count']} transactions)")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Expense Tracker")
    subparsers = parser.add_subparsers(dest="command")
    
    # Log command
    log_parser = subparsers.add_parser("log", help="Log an expense")
    log_parser.add_argument("amount", type=int)
    log_parser.add_argument("category")
    log_parser.add_argument("--description", "-d", default="")
    log_parser.add_argument("--tags", "-t", default="")
    log_parser.add_argument("--date", default=None)
    log_parser.add_argument("--workspace", default=None)
    
    # Summary command
    sum_parser = subparsers.add_parser("summary", help="View monthly summary")
    sum_parser.add_argument("year_month", nargs="?", default=None)
    sum_parser.add_argument("--json", action="store_true", dest="as_json")
    sum_parser.add_argument("--workspace", default=None)
    
    args = parser.parse_args()
    
    if args.command == "log":
        log_expense(
            args.amount,
            args.category,
            description=args.description,
            tags=args.tags,
            date=args.date,
            workspace=args.workspace,
        )
    elif args.command == "summary":
        year_month = args.year_month
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")
        summarize(year_month, as_json=args.as_json, workspace=args.workspace)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''

(scripts_dir / "log_expense.py").write_text(log_expense_script, encoding="utf-8")

# Write the categories reference file
categories_content = """# Expense Categories

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

## Custom Categories

Feel free to create categories specific to your lifestyle:
- **Investing** - Stock purchases, crypto
- **Side Hustle** - Business expenses
- **Content Creation** - Camera gear, software
- **Gaming** - Games, in-app purchases, equipment
"""

(references_dir / "categories.md").write_text(categories_content, encoding="utf-8")

# Create distractor files to simulate a real workspace
distractor_structure = {
    "notes/meeting-2025-11-03.md": "# Meeting Notes\nDiscussed Q4 targets.\n- Revenue goal: 500M VND\n- Cut costs by 15%\n",
    "notes/ideas.md": "# Random Ideas\n- Build a budgeting app\n- Freelance more\n",
    "notes/retrospective-2025-12.md": "# Dec Retrospective\nGood month overall. Need to track expenses better.\n",
    "projects/freelance/client_a/invoice_001.txt": "Invoice #001\nClient: Acme Corp\nAmount: 5,000,000 VND\nDue: 2026-01-15\n",
    "projects/freelance/client_a/contract.txt": "Service Agreement\nDuration: 3 months\nRate: 2,500,000 VND/month\n",
    "projects/freelance/client_b/brief.txt": "Project Brief\nWebsite redesign\nBudget: 8,000,000 VND\n",
    "projects/personal/blog/drafts/post1.md": "# Draft: Why I started tracking expenses\nContent here...\n",
    "config/settings.json": json.dumps({"theme": "dark", "language": "vi", "currency": "VND"}, indent=2),
    "config/aliases.sh": "alias ll='ls -la'\nalias gs='git status'\n",
    "archive/2025/summary.txt": "2025 was a great year. Total income: 120,000,000 VND\n",
    "archive/2025/goals.md": "# 2025 Goals\n- [x] Save 20M VND\n- [ ] Pay off loan\n",
    "tools/convert_currency.py": "# Placeholder: currency converter\ndef convert(amount, rate):\n    return amount * rate\n",
}

for rel_path, content in distractor_structure.items():
    full_path = WORKSPACE / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# Create the raw transaction log the agent needs to process
# This is the "messy input" — a plain text file with expenses listed conversationally
raw_transactions = """EXPENSE LOG - Freelance Consultant
Period: March and April 2026
(Please enter these into the tracking system)

=== MARCH 2026 ===

March 3:
  - Morning coffee at Highlands: 55,000 VND [tags: work,morning]
  - Grabbed pho for lunch: 85,000 VND, place was "Pho Thin" [tags: lunch]
  - Bought a new USB-C hub for work: 450,000 VND [tags: work,equipment]

March 10:
  - Monthly Netflix subscription auto-renewed: 260,000 VND
  - Spotify premium: 59,000 VND
  - Topped up Grab wallet: 200,000 VND (for rides this week) [category: Public Transport, tags: commute]

March 17:
  - Team dinner at a restaurant: 780,000 VND [description: "Team dinner at Nha Hang Ngon", tags: work,social]
  - Coffee for myself during dinner: 65,000 VND

March 24:
  - Paid rent for April: 4,500,000 VND [category: Housing]
  - Electricity bill: 320,000 VND [category: Utilities]
  - Haircut: 120,000 VND [category: Personal Care]

=== APRIL 2026 ===

April 2:
  - Coffee at The Coffee House: 75,000 VND [tags: morning]
  - Bought programming book online: 350,000 VND [category: Education, tags: learning]

April 9:
  - Lunch with client: 340,000 VND [description: "Client lunch at Bun Bo Nam Bo", tags: work,client]
  - Parking fee: 15,000 VND [category: Parking]

April 15:
  - Gym membership renewed: 600,000 VND [category: Fitness, tags: health,monthly]
  - Medicine from pharmacy: 180,000 VND [category: Healthcare, tags: health]

April 22:
  - New running shoes: 1,200,000 VND [category: Clothing, tags: fitness,weekend]
  - Dinner out with friends: 450,000 VND [category: Dining, description: "Weekend dinner at Bun Cha 145", tags: social,weekend]

=== END OF LOG ===

After entering all transactions, please produce a JSON comparison report saved as spending_comparison.json 
showing both months side by side with their totals and category breakdowns.
"""

(WORKSPACE / "raw_transactions.txt").write_text(raw_transactions, encoding="utf-8")

print("Workspace setup complete.")
print(f"Files created in: {WORKSPACE}")