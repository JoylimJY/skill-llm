import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create the skill directory structure ---
skill_dir = workspace / "skills" / "expense-tracker"
dirs = [
    skill_dir / "references",
    skill_dir / "scripts",
    skill_dir / "templates",
    skill_dir / "expenses",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- categories.json ---
categories = [
    {"name": "Groceries", "keywords": ["grocery", "groceries", "costco", "trader joe", "whole foods", "safeway", "kroger", "aldi", "publix", "market", "supermarket"]},
    {"name": "Dining", "keywords": ["restaurant", "cafe", "coffee", "chipotle", "mcdonald", "starbucks", "sushi", "pizza", "dinner", "lunch", "breakfast", "diner", "grill", "bistro", "thai", "chinese", "italian", "panera", "olive garden", "burger", "taco", "bar", "pub"]},
    {"name": "Gas/Transport", "keywords": ["gas", "shell", "exxon", "chevron", "bp", "fuel", "uber", "lyft", "taxi", "transit", "metro", "parking", "toll", "amtrak", "bus"]},
    {"name": "Subscriptions", "keywords": ["netflix", "spotify", "hulu", "disney", "amazon prime", "apple", "youtube", "subscription", "monthly", "annual plan"]},
    {"name": "Health/Fitness", "keywords": ["pharmacy", "cvs", "walgreens", "gym", "fitness", "yoga", "doctor", "dentist", "hospital", "clinic", "medicine", "vitamin", "health"]},
    {"name": "Entertainment", "keywords": ["movie", "cinema", "theater", "concert", "ticket", "event", "museum", "game", "bowling", "amusement", "netflix", "fun"]},
    {"name": "Shopping", "keywords": ["amazon", "target", "walmart", "ebay", "etsy", "clothing", "clothes", "shoes", "mall", "store", "shop", "department"]},
    {"name": "Utilities", "keywords": ["electric", "electricity", "water", "gas bill", "internet", "phone", "utility", "verizon", "at&t", "comcast", "xfinity", "t-mobile"]},
    {"name": "Housing", "keywords": ["rent", "mortgage", "landlord", "lease", "housing", "apartment", "hoa", "property"]},
    {"name": "Personal Care", "keywords": ["haircut", "salon", "barber", "spa", "nail", "beauty", "grooming", "cosmetic"]},
    {"name": "Education", "keywords": ["tuition", "course", "book", "textbook", "school", "udemy", "coursera", "class", "workshop", "training"]},
    {"name": "Gifts", "keywords": ["gift", "present", "birthday", "anniversary", "wedding", "flowers", "card", "donate", "donation"]},
    {"name": "Travel", "keywords": ["hotel", "airbnb", "flight", "airline", "airport", "travel", "trip", "vacation", "motel", "hostel", "resort", "paris", "booking", "expedia"]},
    {"name": "Insurance", "keywords": ["insurance", "premium", "policy", "coverage", "geico", "allstate", "progressive", "state farm"]},
    {"name": "Pets", "keywords": ["vet", "veterinary", "pet", "dog", "cat", "animal", "petco", "petsmart", "grooming", "food pet"]},
    {"name": "Miscellaneous", "keywords": ["misc", "other", "general", "miscellaneous"]},
]
(skill_dir / "references" / "categories.json").write_text(json.dumps(categories, indent=2))

# --- budgets.json --- (initial budgets, some will need updating by agent)
budgets = {
    "month": "2026-06",
    "income": 5000,
    "limits": {
        "Groceries": 500,
        "Dining": 250,
        "Gas/Transport": 200,
        "Subscriptions": 100,
        "Health/Fitness": 150,
        "Entertainment": 120,
        "Shopping": 300,
        "Utilities": 200,
        "Housing": 1800,
        "Personal Care": 80,
        "Education": 100,
        "Gifts": 100,
        "Travel": 400,
        "Insurance": 200,
        "Pets": 150,
        "Miscellaneous": 100
    }
}
(skill_dir / "references" / "budgets.json").write_text(json.dumps(budgets, indent=2))

# --- add-expense.sh ---
add_expense_sh = r"""#!/usr/bin/env bash
# Usage: add-expense.sh <amount> <category> <vendor> [date] [notes]
set -euo pipefail

AMOUNT="${1}"
CATEGORY="${2}"
VENDOR="${3}"
DATE="${4:-$(date +%Y-%m-%d)}"
NOTES="${5:-}"

LEDGER="skills/expense-tracker/expenses/ledger.json"
CATEGORIES_FILE="skills/expense-tracker/references/categories.json"

# Validate category exists
VALID=$(jq --arg cat "$CATEGORY" '[.[].name] | map(select(. == $cat)) | length' "$CATEGORIES_FILE")
if [ "$VALID" -eq 0 ]; then
    echo "ERROR: Unknown category '$CATEGORY'. Valid categories: $(jq -r '[.[].name] | join(", ")' "$CATEGORIES_FILE")" >&2
    exit 1
fi

# Initialize ledger if missing
if [ ! -f "$LEDGER" ]; then
    echo "[]" > "$LEDGER"
fi

# Get next ID
NEXT_ID=$(jq 'if length == 0 then 1 else (map(.id) | max + 1) end' "$LEDGER")

# Get current UTC timestamp
CREATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Append entry
UPDATED=$(jq \
    --argjson id "$NEXT_ID" \
    --argjson amount "$AMOUNT" \
    --arg category "$CATEGORY" \
    --arg vendor "$VENDOR" \
    --arg date "$DATE" \
    --arg notes "$NOTES" \
    --arg created_at "$CREATED_AT" \
    '. + [{
        "id": $id,
        "amount": $amount,
        "category": $category,
        "vendor": $vendor,
        "date": $date,
        "notes": $notes,
        "created_at": $created_at
    }]' "$LEDGER")

echo "$UPDATED" > "$LEDGER"
echo "Expense #${NEXT_ID}: ${AMOUNT} at ${VENDOR} (${CATEGORY}) on ${DATE}"
"""
(skill_dir / "scripts" / "add-expense.sh").write_text(add_expense_sh)

# --- query.sh ---
query_sh = r"""#!/usr/bin/env bash
# Usage: query.sh [--from DATE] [--to DATE] [--category CAT] [--vendor TEXT] [--format FMT]
set -euo pipefail

LEDGER="skills/expense-tracker/expenses/ledger.json"
FROM_DATE=""
TO_DATE=""
CATEGORY=""
VENDOR_FILTER=""
FORMAT="summary"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --from) FROM_DATE="$2"; shift 2 ;;
        --to)   TO_DATE="$2";   shift 2 ;;
        --category) CATEGORY="$2"; shift 2 ;;
        --vendor)   VENDOR_FILTER="$2"; shift 2 ;;
        --format)   FORMAT="$2"; shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

if [ ! -f "$LEDGER" ]; then
    echo "[]"
    exit 0
fi

RESULT=$(jq \
    --arg from "$FROM_DATE" \
    --arg to "$TO_DATE" \
    --arg cat "$CATEGORY" \
    --arg vendor "$VENDOR_FILTER" \
    '[.[] |
        select(if $from != "" then .date >= $from else true end) |
        select(if $to != "" then .date <= $to else true end) |
        select(if $cat != "" then .category == $cat else true end) |
        select(if $vendor != "" then (.vendor | ascii_downcase | contains(($vendor | ascii_downcase))) else true end)
    ]' "$LEDGER")

case "$FORMAT" in
    json)
        echo "$RESULT"
        ;;
    detail)
        echo "$RESULT" | jq -r '.[] | "#\(.id) | \(.date) | \(.vendor) | \(.category) | $\(.amount) | \(.notes)"'
        ;;
    summary)
        echo "$RESULT" | jq -r '
            group_by(.category)[] |
            {category: .[0].category, total: (map(.amount) | add)} |
            "\(.category): $\(.total)"
        '
        ;;
esac
"""
(skill_dir / "scripts" / "query.sh").write_text(query_sh)

# --- budget-check.sh ---
budget_check_sh = r"""#!/usr/bin/env bash
# Usage: budget-check.sh [YYYY-MM]
set -euo pipefail

MONTH="${1:-$(date +%Y-%m)}"
LEDGER="skills/expense-tracker/expenses/ledger.json"
BUDGETS_FILE="skills/expense-tracker/references/budgets.json"

FROM_DATE="${MONTH}-01"
# Last day of month
TO_DATE=$(date -d "${FROM_DATE} +1 month -1 day" +%Y-%m-%d 2>/dev/null || \
          python3 -c "import calendar, datetime; y,m = map(int,'${MONTH}'.split('-')); print('%s-%02d-%02d' % (y,m,calendar.monthrange(y,m)[1]))")

echo "=== Budget Check: ${MONTH} ==="

if [ ! -f "$LEDGER" ]; then
    echo "No expenses recorded."
    exit 0
fi

EXIT_CODE=0

jq -r '.limits | to_entries[] | "\(.key)|\(.value)"' "$BUDGETS_FILE" | while IFS='|' read -r cat limit; do
    if [ ! -f "$LEDGER" ]; then
        spent=0
    else
        spent=$(jq --arg cat "$cat" --arg from "$FROM_DATE" --arg to "$TO_DATE" \
            '[.[] | select(.category == $cat) | select(.date >= $from) | select(.date <= $to) | .amount] | if length == 0 then 0 else add end' \
            "$LEDGER")
    fi
    pct=$(echo "scale=0; ($spent * 100) / $limit" | bc 2>/dev/null || echo "0")
    if (( $(echo "$spent >= $limit" | bc -l) )); then
        icon="🔴 OVER "
    elif (( $(echo "$spent >= $limit * 0.80" | bc -l) )); then
        icon="🟡 WARN "
    elif (( $(echo "$spent >= $limit * 0.50" | bc -l) )); then
        icon="🟢 OK   "
    else
        icon="⚪ LOW  "
    fi
    printf "  %s %-18s \$%-8.2f / \$%-8.2f (%s%%)\n" "$icon" "$cat" "$spent" "$limit" "$pct"
done

echo ""
TOTAL=$(jq --arg from "$FROM_DATE" --arg to "$TO_DATE" \
    '[.[] | select(.date >= $from) | select(.date <= $to) | .amount] | if length == 0 then 0 else add end' \
    "$LEDGER" 2>/dev/null || echo "0")
echo "  TOTAL: \$${TOTAL}"

exit $EXIT_CODE
"""
(skill_dir / "scripts" / "budget-check.sh").write_text(budget_check_sh)

# --- weekly-report.md template ---
weekly_report_md = """# Weekly Expense Report
**Period:** {{WEEK_START}} to {{WEEK_END}}

## Summary by Category
{{CATEGORY_BREAKDOWN}}

## Top Expenses
{{TOP_EXPENSES}}

## Budget Status
{{BUDGET_STATUS}}

## Week-over-Week
{{WOW_COMPARISON}}
"""
(skill_dir / "templates" / "weekly-report.md").write_text(weekly_report_md)

# --- monthly-report.md template ---
monthly_report_md = """# Monthly Expense Report
**Month:** {{MONTH}}

## Summary by Category
{{CATEGORY_BREAKDOWN}}

## Top Expenses
{{TOP_EXPENSES}}

## Weekly Breakdown
{{WEEKLY_BREAKDOWN}}

## Month-over-Month Comparison
{{MOM_COMPARISON}}

## Savings Rate
{{SAVINGS_RATE}}
"""
(skill_dir / "templates" / "monthly-report.md").write_text(monthly_report_md)

# --- DISTRACTOR FILES (realistic noise) ---

# Personal finance notes (distractor)
(workspace / "notes").mkdir(exist_ok=True)
(workspace / "notes" / "shopping_list.txt").write_text(
    "Milk, eggs, bread, cheese, coffee beans, protein bars, shampoo\n"
    "Check if avocados are on sale at Costco\n"
)
(workspace / "notes" / "todo.txt").write_text(
    "1. Call landlord about AC repair\n"
    "2. Schedule dentist appointment\n"
    "3. Renew car registration\n"
    "4. Review subscription services\n"
    "5. Meal prep Sunday\n"
)

# Old receipts as text files (distractor)
(workspace / "receipts").mkdir(exist_ok=True)
(workspace / "receipts" / "2026-05-receipt-costco.txt").write_text(
    "COSTCO WHOLESALE\nDate: 2026-05-10\nTotal: $234.56\nThank you!\n"
)
(workspace / "receipts" / "2026-05-receipt-netflix.txt").write_text(
    "NETFLIX.COM\nBilling Date: 2026-05-01\nAmount: $15.49\nPlan: Standard\n"
)
(workspace / "receipts" / "2026-04-dentist.txt").write_text(
    "City Dental Clinic\nAppt: 2026-04-22\nTotal Due: $180.00\nInsurance covered: $0\n"
)

# Config files (distractor)
(workspace / "config").mkdir(exist_ok=True)
(workspace / "config" / "app.json").write_text(json.dumps({"theme": "dark", "language": "en-US", "notifications": True}, indent=2))
(workspace / "config" / "aliases.sh").write_text(
    "alias ll='ls -la'\nalias gs='git status'\nalias gc='git commit'\n"
)

# Fake financial data CSV (distractor - wrong format)
(workspace / "receipts" / "old_expenses_export.csv").write_text(
    "date,description,amount,account\n"
    "2026-04-01,Grocery Store,-45.23,Checking\n"
    "2026-04-03,Gas Station,-38.10,Checking\n"
    "2026-04-05,Restaurant,-67.00,Checking\n"
    "2026-04-10,Salary,3500.00,Checking\n"
)

# Random project files (distractor)
(workspace / "projects").mkdir(exist_ok=True)
(workspace / "projects" / "photo-gig-june.txt").write_text(
    "Client: Harmon Weddings\nShoot Date: 2026-06-14\nLocation: Marin Headlands\nRate: $1200\nDeposit received: $400\n"
)
(workspace / "projects" / "equipment-list.md").write_text(
    "# Camera Gear\n- Sony A7IV\n- 50mm f/1.4\n- 85mm f/1.8\n- Drone: DJI Mini 4 Pro\n- ND Filter set\n- 3x batteries\n"
)
(workspace / "projects" / "travel-plans-2026.txt").write_text(
    "July: Portland, OR - workshop\nAugust: Paris, France - 2 weeks (photography)\nSeptember: TBD\n"
)

# Logs (distractor)
(workspace / "logs").mkdir(exist_ok=True)
(workspace / "logs" / "system.log").write_text(
    "[2026-06-01 09:00:01] INFO: System started\n"
    "[2026-06-01 09:01:44] INFO: Config loaded\n"
    "[2026-06-01 10:23:17] WARN: Disk usage at 72%\n"
)

# Empty expenses ledger (no pre-existing data — agent must create entries fresh)
(skill_dir / "expenses" / "ledger.json").write_text("[]")

print("Workspace initialized successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Distractor files created in: notes/, receipts/, config/, projects/, logs/")