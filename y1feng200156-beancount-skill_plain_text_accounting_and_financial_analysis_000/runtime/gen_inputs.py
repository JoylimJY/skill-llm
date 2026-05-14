import os
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory structure ---
dirs = [
    "data/raw",
    "data/processed",
    "data/archive",
    "scripts",
    "references",
    "reports/2022",
    "reports/2023",
    "tax/2022",
    "tax/2023",
    "notes",
    "backups",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "notes" / "todo.txt").write_text(
    "- Call accountant\n- Review Q4 expenses\n- Check insurance renewal\n- Submit invoices\n"
)
(workspace / "notes" / "meeting_notes.txt").write_text(
    "Client meeting 2023-03-15: discussed project scope, budget ~$15k\n"
    "2023-07-20: raised rates to $150/hr\n"
)
(workspace / "data" / "archive" / "expenses_2022_final.csv").write_text(
    "date,description,amount,category\n"
    "2022-01-10,AWS hosting,120.00,Software\n"
    "2022-02-15,Office supplies,45.00,Office\n"
    "2022-03-01,Client lunch,80.00,Entertainment\n"
)
(workspace / "reports" / "2022" / "annual_summary.txt").write_text(
    "2022 Annual Summary\nTotal Revenue: $82,000\nTotal Expenses: $18,500\nNet Income: $63,500\n"
)
(workspace / "tax" / "2022" / "tax_return_draft.txt").write_text(
    "Draft Tax Return 2022\nBusiness Income: 82000\nDeductions: 18500\nTaxable Income: 63500\n"
)
(workspace / "tax" / "2023" / "receipts_folder.txt").write_text(
    "Receipts scanned and stored in Google Drive folder: /Tax2023/Receipts/\n"
)
(workspace / "backups" / "old_ledger.txt").write_text(
    "This was an old manual ledger attempt. Abandoned.\nJan: +8500 income, -1200 expenses\nFeb: +9000 income, -980 expenses\n"
)
(workspace / "data" / "processed" / "bank_export_Q1.csv").write_text(
    "Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit\n"
    "01/05/2023,01/06/2023,****1234,TRANSFER FROM CLIENT,,, 8500.00\n"
    "01/12/2023,01/13/2023,****1234,GITHUB SUBSCRIPTION,Software,7.00,\n"
    "01/18/2023,01/19/2023,****1234,WHOLE FOODS,Groceries,95.32,\n"
)
(workspace / "data" / "processed" / "README_DO_NOT_USE.txt").write_text(
    "These exports are raw and uncategorized. Use data/raw/transactions_2023.csv instead.\n"
)
(workspace / "reports" / "2023" / "placeholder.txt").write_text(
    "2023 reports will go here once accounting is set up.\n"
)

# --- Partially broken beancount file as red herring ---
(workspace / "backups" / "attempt1.beancount").write_text(
    '; Incomplete attempt - DO NOT USE\n'
    '2023-01-01 open Assets:Checking USD\n'
    '2023-01-05 * "Client A" "Invoice payment"\n'
    '  Assets:Checking  8500.00\n'
    '  ; missing second posting - broken!\n'
    '2023-02-01 * "GitHub" "Subscription"\n'
    '  Expenses:Software  7.00\n'
    '  ; also broken\n'
)

# --- Main raw transaction CSV (the actual input to process) ---
transactions_csv = """\
date,type,payee,description,amount,currency,category
2023-01-03,income,Client Alpha,Invoice #1001 - Web Development,9500.00,USD,Consulting
2023-01-15,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-01-20,expense,Amazon,Office chair for home office,-289.99,USD,Office
2023-01-25,expense,Whole Foods,Groceries,-112.45,USD,Groceries
2023-02-01,income,Client Beta,Invoice #1002 - API Integration,6200.00,USD,Consulting
2023-02-10,expense,Adobe Creative Cloud,Annual subscription (prorated),-54.99,USD,Software
2023-02-14,expense,Restaurant Elara,Client dinner,-187.50,USD,Meals
2023-02-20,expense,Whole Foods,Groceries,-98.30,USD,Groceries
2023-02-22,expense,AT&T,Mobile phone bill (business 60%),-89.00,USD,Utilities
2023-03-01,income,Client Alpha,Invoice #1003 - Maintenance retainer,3000.00,USD,Consulting
2023-03-05,expense,Linode,Cloud server hosting,-40.00,USD,Software
2023-03-12,expense,Staples,Printer paper and ink,-65.00,USD,Office
2023-03-25,expense,Whole Foods,Groceries,-125.00,USD,Groceries
2023-03-28,expense,United Airlines,Conference travel,-450.00,USD,Travel
2023-04-01,income,Client Gamma,Invoice #1004 - Data Pipeline build,11000.00,USD,Consulting
2023-04-10,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-04-15,expense,WeWork,Coworking day pass,-35.00,USD,Office
2023-04-20,expense,Whole Foods,Groceries,-108.90,USD,Groceries
2023-04-22,expense,DocuSign,E-signature subscription,-25.00,USD,Software
2023-05-01,income,Client Beta,Invoice #1005 - Consulting hours,4800.00,USD,Consulting
2023-05-08,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-05-14,expense,Restaurant Elara,Client lunch,-95.00,USD,Meals
2023-05-20,expense,Whole Foods,Groceries,-131.20,USD,Groceries
2023-05-25,expense,AT&T,Mobile phone bill (business 60%),-89.00,USD,Utilities
2023-06-01,income,Client Alpha,Invoice #1006 - Feature development,7500.00,USD,Consulting
2023-06-05,expense,Linode,Cloud server hosting,-40.00,USD,Software
2023-06-10,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-06-18,expense,Whole Foods,Groceries,-119.75,USD,Groceries
2023-06-22,expense,Zoom,Annual subscription,-149.90,USD,Software
2023-07-03,income,Client Delta,Invoice #1007 - Security audit,8000.00,USD,Consulting
2023-07-10,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-07-15,expense,Whole Foods,Groceries,-102.40,USD,Groceries
2023-07-20,expense,Office Depot,Standing desk accessories,-178.00,USD,Office
2023-07-25,expense,AT&T,Mobile phone bill (business 60%),-89.00,USD,Utilities
2023-08-01,income,Client Alpha,Invoice #1008 - Ongoing retainer,3000.00,USD,Consulting
2023-08-07,expense,Amazon,External monitor,-329.99,USD,Office
2023-08-10,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-08-18,expense,Whole Foods,Groceries,-115.60,USD,Groceries
2023-08-22,expense,Linode,Cloud server hosting,-40.00,USD,Software
2023-09-01,income,Client Gamma,Invoice #1009 - ML pipeline consulting,12500.00,USD,Consulting
2023-09-08,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-09-12,expense,Restaurant Elara,Client dinner,-210.00,USD,Meals
2023-09-20,expense,Whole Foods,Groceries,-128.90,USD,Groceries
2023-09-25,expense,AT&T,Mobile phone bill (business 60%),-89.00,USD,Utilities
2023-10-01,income,Client Beta,Invoice #1010 - Code review sprint,5200.00,USD,Consulting
2023-10-10,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-10-15,expense,Linode,Cloud server hosting,-40.00,USD,Software
2023-10-20,expense,Whole Foods,Groceries,-98.75,USD,Groceries
2023-10-28,expense,Delta Airlines,Client site visit travel,-380.00,USD,Travel
2023-11-01,income,Client Alpha,Invoice #1011 - Year-end project,9000.00,USD,Consulting
2023-11-08,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-11-12,expense,Staples,Office supplies,-42.00,USD,Office
2023-11-18,expense,Whole Foods,Groceries,-135.25,USD,Groceries
2023-11-22,expense,AT&T,Mobile phone bill (business 60%),-89.00,USD,Utilities
2023-12-01,income,Client Delta,Invoice #1012 - Security hardening,6500.00,USD,Consulting
2023-12-08,expense,GitHub,Monthly Pro subscription,-7.00,USD,Software
2023-12-10,expense,Linode,Cloud server hosting,-40.00,USD,Software
2023-12-15,expense,Restaurant Elara,Year-end client dinner,-320.00,USD,Meals
2023-12-20,expense,Whole Foods,Groceries,-145.80,USD,Groceries
2023-12-28,expense,Amazon,Tax software,-79.99,USD,Software
"""

(workspace / "data" / "raw" / "transactions_2023.csv").write_text(transactions_csv)

# --- A note from the "owner" describing their situation ---
(workspace / "data" / "raw" / "context_notes.txt").write_text(
    "My financial situation for 2023:\n"
    "- I am a freelance software consultant operating as a sole proprietor\n"
    "- All income goes into my main checking account: Chase Checking\n"
    "- I also have savings: Ally Savings with $25,000 balance as of 2023-01-01\n"
    "- My checking account started 2023 with $8,200.00\n"
    "- All amounts in USD\n"
    "- For the ledger, treat ALL expenses as coming from the checking account\n"
    "- Income: use Income:Freelance:Consulting\n"
    "- Expenses should be categorized under Expenses:Business:* or Expenses:Personal:*\n"
    "  * Software -> Expenses:Business:Software\n"
    "  * Office -> Expenses:Business:Office\n"
    "  * Meals (client) -> Expenses:Business:Meals\n"
    "  * Travel -> Expenses:Business:Travel\n"
    "  * Utilities -> Expenses:Business:Utilities\n"
    "  * Groceries -> Expenses:Personal:Groceries\n"
    "- Equity account for opening balances: Equity:Opening-Balances\n"
    "- I want monthly budget targets tracked: $200/month for Software, $300/month for Office\n"
)

# --- Reference files (required by SKILL.md to exist) ---
# beancount_syntax.md
(workspace / "references" / "beancount_syntax.md").write_text(textwrap.dedent("""\
    # Beancount Syntax Reference

    ## File Structure
    A Beancount file consists of directives. Each directive starts with a date.

    ## Directives

    ### option
    ```
    option "operating_currency" "USD"
    option "title" "My Finances"
    ```

    ### open
    Opens an account. Must appear before any transaction using that account.
    ```
    YYYY-MM-DD open Account:Name COMMODITY
    ```
    Example:
    ```
    2023-01-01 open Assets:Checking USD
    2023-01-01 open Expenses:Food USD
    ```

    ### commodity
    Declares a commodity (optional but recommended).
    ```
    2023-01-01 commodity USD
    ```

    ### Transactions
    Format:
    ```
    YYYY-MM-DD [*|!] ["Payee"] "Narration"
      Account  Amount COMMODITY
      Account  Amount COMMODITY
    ```
    - `*` = cleared transaction
    - `!` = pending transaction
    - Postings must be indented with 2+ spaces (conventionally 2 or 4 spaces)
    - Amounts must balance to zero (one posting may omit amount for auto-calculation)

    Example:
    ```
    2023-01-15 * "GitHub" "Monthly subscription"
      Expenses:Software    7.00 USD
      Assets:Checking     -7.00 USD
    ```

    ### balance
    Asserts account balance at a specific date:
    ```
    YYYY-MM-DD balance Account  Amount COMMODITY
    ```

    ### pad
    Automatically pads an account to meet a balance assertion:
    ```
    YYYY-MM-DD pad Account:From Account:To
    ```

    ### close
    Closes an account:
    ```
    YYYY-MM-DD close Account:Name
    ```

    ### note
    Adds a note to an account:
    ```
    YYYY-MM-DD note Account:Name "Note text"
    ```

    ### Custom directives (Fava budgets)
    ```
    2023-01-01 custom "budget" Expenses:Business:Software "monthly" 200 USD
    ```

    ## Account Types
    - Assets (debit-normal)
    - Liabilities (credit-normal)
    - Income (credit-normal)
    - Expenses (debit-normal)
    - Equity (credit-normal)

    ## Tags and Links
    ```
    2023-01-15 * "GitHub" "Subscription" #Q1 ^invoice-001
      Expenses:Software  7.00 USD
      Assets:Checking   -7.00 USD
    ```

    ## File Organization Tips
    - Keep open directives at top of file
    - Group by year or by account
    - Use comments with semicolons: ; this is a comment
"""))

# beancount_query.md
(workspace / "references" / "beancount_query.md").write_text(textwrap.dedent("""\
    # Beancount Query Language (BQL) Reference

    ## Overview
    BQL is a SQL-like language for querying Beancount data. Run queries with:
    ```
    bean-query file.beancount "SELECT ..."
    ```

    ## Basic Syntax
    ```sql
    SELECT [columns] FROM [table] WHERE [conditions] GROUP BY [columns] ORDER BY [columns]
    ```

    ## Tables
    - `postings` (default): individual postings within transactions
    - `transactions`: full transactions

    ## Columns (postings table)
    - `date`: transaction date
    - `account`: posting account name
    - `position`: the lot
    - `balance`: running balance
    - `number`: numeric amount
    - `currency`: commodity
    - `narration`: transaction narration
    - `payee`: transaction payee
    - `flag`: transaction flag
    - `tags`: transaction tags

    ## Functions
    - `SUM(position)`: sum of positions
    - `SUM(number)`: sum of amounts
    - `COUNT(*)`: count rows
    - `MONTH(date)`: extract month
    - `YEAR(date)`: extract year
    - `UNITS(position)`: get units
    - `COST(position)`: get cost

    ## WHERE Conditions
    - `account ~ 'pattern'`: regex match on account name
    - `date >= DATE(2023, 1, 1)`: date comparison
    - `date < DATE(2024, 1, 1)`: date comparison
    - `currency = 'USD'`: currency filter
    - `flag = '*'`: flag filter

    ## Example Queries

    ### Total expenses by account for a year
    ```sql
    SELECT account, SUM(position) AS total
    WHERE account ~ 'Expenses' AND year = 2023
    GROUP BY account
    ORDER BY total DESC
    ```

    ### Monthly income
    ```sql
    SELECT MONTH(date) AS month, SUM(position) AS income
    WHERE account ~ 'Income' AND year = 2023
    GROUP BY month
    ORDER BY month
    ```

    ### Top expense categories
    ```sql
    SELECT account, SUM(number) AS total
    WHERE account ~ 'Expenses' AND year = 2023
    GROUP BY account
    ORDER BY total DESC
    LIMIT 10
    ```

    ### Saving query to file
    Save queries in a .bql file and run with bean-query.
"""))

# fava_features.md
(workspace / "references" / "fava_features.md").write_text(textwrap.dedent("""\
    # Fava Features Reference

    ## Starting Fava
    ```
    fava myfile.beancount
    ```

    ## Fava Options (in beancount file)
    ```
    2023-01-01 custom "fava-option" "default-file" ""
    2023-01-01 custom "fava-option" "fiscal-year-end" "December"
    2023-01-01 custom "fava-option" "language" "en"
    ```

    ## Budget Directives
    Fava supports budget tracking via custom directives:
    ```
    YYYY-MM-DD custom "budget" Account "period" Amount COMMODITY
    ```

    Periods: "daily", "weekly", "monthly", "yearly"

    Examples:
    ```
    2023-01-01 custom "budget" Expenses:Business:Software "monthly" 200.00 USD
    2023-01-01 custom "budget" Expenses:Personal:Groceries "monthly" 400.00 USD
    2023-01-01 custom "budget" Expenses:Business:Office "monthly" 300.00 USD
    2023-01-01 custom "budget" Expenses:Business:Meals "monthly" 250.00 USD
    ```

    ## Fava Query Interface
    - Access via Reports > Query in Fava UI
    - Save named queries in beancount file:
    ```
    2023-01-01 custom "fava-option" "insert-entry" "..."
    ```

    ## Key Reports
    - Income Statement: revenues vs expenses
    - Balance Sheet: assets, liabilities, equity
    - Trial Balance: all accounts with balances
    - Journal: all transactions
    - Commodities: currency/commodity tracking
    - Statistics: transaction counts and distribution

    ## Account Hierarchy
    Fava displays accounts in tree structure matching their colon-separated names.
"""))

# fava_dashboards.md
(workspace / "references" / "fava_dashboards.md").write_text(textwrap.dedent("""\
    # Fava Dashboards Reference

    ## Installation
    ```
    pip install fava-dashboards
    ```

    ## Configuration
    Add to beancount file:
    ```
    2023-01-01 custom "fava-extension" "fava_dashboards" "{}"
    ```

    ## Dashboard YAML format
    Create `dashboards.yaml` in the same directory as your beancount file.

    ## Widget Types
    - `beancount_query`: runs a BQL query and displays results
    - `echarts`: renders a chart from query data
    - `jinja2`: renders a Jinja2 template

    ## Example Dashboard Config
    ```yaml
    dashboards:
      - title: "Financial Overview 2023"
        panels:
          - title: "Expenses by Category"
            width: "50%"
            type: beancount_query
            query: |
              SELECT account, SUM(position) AS total
              WHERE account ~ 'Expenses' AND year = 2023
              GROUP BY account
              ORDER BY total DESC
    ```
"""))

# financial_analysis.md
(workspace / "references" / "financial_analysis.md").write_text(textwrap.dedent("""\
    # Financial Analysis Reference

    ## Key Metrics

    ### Net Worth
    Net Worth = Total Assets - Total Liabilities

    ### Savings Rate
    Savings Rate = (Income - Expenses) / Income * 100
    Healthy benchmark: 20%+ is good, 30%+ is excellent

    ### Expense Ratios
    - Housing: ideally < 30% of gross income
    - Food: 10-15% of income
    - Business expenses: track separately for tax purposes

    ## Benchmarks
    - Emergency fund: 3-6 months of expenses
    - Retirement savings: 15% of gross income
    - Discretionary spending: < 30% of after-tax income

    ## Analysis Framework
    1. Calculate total income and expenses
    2. Identify largest expense categories
    3. Compare to benchmarks
    4. Identify optimization opportunities
    5. Project future net worth based on current savings rate
"""))

# analyze_beancount.py script
analyze_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """
    Beancount Financial Analysis Script
    Usage: python scripts/analyze_beancount.py <file> [options]
    """
    import sys
    import argparse
    from decimal import Decimal
    from collections import defaultdict

    def load_beancount(filepath):
        """Load and parse a beancount file using the beancount library."""
        try:
            from beancount import loader
            entries, errors, options = loader.load_file(filepath)
            if errors:
                print(f"WARNING: {len(errors)} parsing error(s) found:", file=sys.stderr)
                for e in errors[:5]:
                    print(f"  {e}", file=sys.stderr)
            return entries, errors, options
        except ImportError:
            print("ERROR: beancount library not installed. Run: pip install beancount", file=sys.stderr)
            sys.exit(1)
        except Exception as ex:
            print(f"ERROR loading file: {ex}", file=sys.stderr)
            sys.exit(1)

    def get_account_balances(entries):
        """Calculate final balances for all accounts."""
        from beancount.core import data, amount as amt
        from beancount.core.number import ZERO
        balances = defaultdict(lambda: defaultdict(Decimal))
        for entry in entries:
            if isinstance(entry, data.Transaction):
                for posting in entry.postings:
                    currency = posting.units.currency
                    balances[posting.account][currency] += posting.units.number
        return balances

    def get_transactions_by_year(entries, year):
        """Get transactions filtered by year."""
        from beancount.core import data
        return [e for e in entries
                if isinstance(e, data.Transaction) and e.date.year == year]

    def calculate_net_worth(entries):
        """Calculate net worth from asset and liability accounts."""
        balances = get_account_balances(entries)
        net_worth = defaultdict(Decimal)
        assets = defaultdict(Decimal)
        liabilities = defaultdict(Decimal)
        for account, currencies in balances.items():
            for currency, amount in currencies.items():
                if account.startswith("Assets:"):
                    assets[currency] += amount
                    net_worth[currency] += amount
                elif account.startswith("Liabilities:"):
                    liabilities[currency] += amount
                    net_worth[currency] += amount
        return net_worth, assets, liabilities

    def calculate_savings_rate(entries, year=None):
        """Calculate savings rate for given year or all time."""
        from beancount.core import data
        income = defaultdict(Decimal)
        expenses = defaultdict(Decimal)
        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            if year and entry.date.year != year:
                continue
            for posting in entry.postings:
                currency = posting.units.currency
                if posting.account.startswith("Income:"):
                    income[currency] -= posting.units.number  # Income is negative in double-entry
                elif posting.account.startswith("Expenses:"):
                    expenses[currency] += posting.units.number
        return income, expenses

    def get_top_expenses(entries, n=5, year=None):
        """Get top N expense categories."""
        from beancount.core import data
        expense_totals = defaultdict(lambda: defaultdict(Decimal))
        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            if year and entry.date.year != year:
                continue
            for posting in entry.postings:
                if posting.account.startswith("Expenses:"):
                    currency = posting.units.currency
                    expense_totals[posting.account][currency] += posting.units.number
        return expense_totals

    def get_monthly_expenses(entries, year=None):
        """Get monthly expense breakdown."""
        from beancount.core import data
        from collections import OrderedDict
        monthly = defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal)))
        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            if year and entry.date.year != year:
                continue
            month = entry.date.month
            for posting in entry.postings:
                if posting.account.startswith("Expenses:"):
                    currency = posting.units.currency
                    monthly[month][posting.account][currency] += posting.units.number
        return monthly

    def print_net_worth(entries):
        print("=" * 50)
        print("NET WORTH REPORT")
        print("=" * 50)
        net_worth, assets, liabilities = calculate_net_worth(entries)
        print("\\nAssets:")
        for currency, amount in sorted(assets.items()):
            print(f"  {currency}: {amount:>12,.2f}")
        print("\\nLiabilities:")
        for currency, amount in sorted(liabilities.items()):
            print(f"  {currency}: {amount:>12,.2f}")
        print("\\nNet Worth:")
        for currency, amount in sorted(net_worth.items()):
            print(f"  {currency}: {amount:>12,.2f}")
        print()

    def print_savings_rate(entries, year=None):
        print("=" * 50)
        print(f"SAVINGS RATE REPORT{f\' ({year})\' if year else \'\'}")
        print("=" * 50)
        income, expenses = calculate_savings_rate(entries, year)
        for currency in set(list(income.keys()) + list(expenses.keys())):
            inc = income.get(currency, Decimal("0"))
            exp = expenses.get(currency, Decimal("0"))
            savings = inc - exp
            rate = (savings / inc * 100) if inc else Decimal("0")
            print(f"\\nCurrency: {currency}")
            print(f"  Total Income:   {inc:>12,.2f}")
            print(f"  Total Expenses: {exp:>12,.2f}")
            print(f"  Net Savings:    {savings:>12,.2f}")
            print(f"  Savings Rate:   {rate:>11.1f}%")
            if rate >= 30:
                print(f"  Status: EXCELLENT (>=30%)")
            elif rate >= 20:
                print(f"  Status: GOOD (>=20%)")
            elif rate >= 10:
                print(f"  Status: FAIR (>=10%)")
            else:
                print(f"  Status: NEEDS IMPROVEMENT (<10%)")
        print()

    def print_top_expenses(entries, n=5, year=None):
        print("=" * 50)
        print(f"TOP {n} EXPENSE CATEGORIES{f\' ({year})\' if year else \'\'}")
        print("=" * 50)
        expense_totals = get_top_expenses(entries, n, year)
        all_expenses = []
        for account, currencies in expense_totals.items():
            for currency, amount in currencies.items():
                all_expenses.append((account, currency, amount))
        all_expenses.sort(key=lambda x: x[2], reverse=True)
        for i, (account, currency, amount) in enumerate(all_expenses[:n], 1):
            print(f"  {i}. {account:<45} {currency} {amount:>10,.2f}")
        print()

    def print_monthly_expenses(entries, year=None):
        print("=" * 50)
        print(f"MONTHLY EXPENSE BREAKDOWN{f\' ({year})\' if year else \'\'}")
        print("=" * 50)
        monthly = get_monthly_expenses(entries, year)
        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        for month in sorted(monthly.keys()):
            print(f"\\n{month_names.get(month, month)}:")
            month_data = monthly[month]
            month_total = defaultdict(Decimal)
            for account, currencies in month_data.items():
                for currency, amount in currencies.items():
                    print(f"  {account:<45} {currency} {amount:>10,.2f}")
                    month_total[currency] += amount
            for currency, total in sorted(month_total.items()):
                print(f"  {\'MONTH TOTAL\':<45} {currency} {total:>10,.2f}")
        print()

    def main():
        parser = argparse.ArgumentParser(description="Beancount Financial Analyzer")
        parser.add_argument("file", help="Path to beancount file")
        parser.add_argument("--net-worth", action="store_true", help="Calculate net worth")
        parser.add_argument("--savings-rate", action="store_true", help="Calculate savings rate")
        parser.add_argument("--top-expenses", type=int, metavar="N", help="Show top N expense categories")
        parser.add_argument("--monthly-expenses", action="store_true", help="Monthly expense breakdown")
        parser.add_argument("--year", type=int, help="Filter by year")
        parser.add_argument("--all", action="store_true", help="Run all reports")
        args = parser.parse_args()

        entries, errors, options = load_beancount(args.file)

        if args.all or args.net_worth:
            print_net_worth(entries)
        if args.all or args.savings_rate:
            print_savings_rate(entries, args.year)
        if args.all or args.top_expenses:
            n = args.top_expenses if args.top_expenses else 5
            print_top_expenses(entries, n, args.year)
        if args.all or args.monthly_expenses:
            print_monthly_expenses(entries, args.year)

        if not any([args.all, args.net_worth, args.savings_rate,
                    args.top_expenses, args.monthly_expenses]):
            print("No report selected. Use --help for options.")

    if __name__ == "__main__":
        main()
''')

(workspace / "scripts" / "analyze_beancount.py").write_text(analyze_script)
(workspace / "scripts" / "analyze_beancount.py").chmod(0o755)

print("Workspace generated successfully.")
print(f"Key file: {workspace}/data/raw/transactions_2023.csv")
print(f"Context: {workspace}/data/raw/context_notes.txt")