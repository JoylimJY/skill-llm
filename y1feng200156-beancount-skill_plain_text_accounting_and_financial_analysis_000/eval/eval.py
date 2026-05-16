import sys
import json
import re
import subprocess
from pathlib import Path
from decimal import Decimal, InvalidOperation

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: Find the ledger_2023.beancount file
    # -----------------------------------------------------------------------
    beancount_files = list(workspace.rglob("ledger_2023.beancount"))
    if not beancount_files:
        checks.append({
            "name": "ledger_2023.beancount file exists",
            "passed": False,
            "detail": "Could not find any file named 'ledger_2023.beancount' anywhere in the workspace."
        })
        return checks, 0.0

    beancount_path = beancount_files[0]
    checks.append({
        "name": "ledger_2023.beancount file exists",
        "passed": True,
        "detail": f"Found at {beancount_path}"
    })
    total_score += 0.05

    try:
        beancount_content = beancount_path.read_text()
    except Exception as e:
        checks.append({"name": "Read beancount file", "passed": False, "detail": str(e)})
        return checks, total_score

    # -----------------------------------------------------------------------
    # CHECK 2: Valid Beancount syntax - parse with beancount library
    # -----------------------------------------------------------------------
    try:
        result = subprocess.run(
            ["python3", "-c",
             f"from beancount import loader; entries, errors, options = loader.load_file('{beancount_path}'); print(f'entries={{len(entries)}} errors={{len(errors)}}')"],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()
        # Check for entries found and minimal errors
        entry_match = re.search(r'entries=(\d+)', output)
        error_match = re.search(r'errors=(\d+)', output)
        num_entries = int(entry_match.group(1)) if entry_match else 0
        num_errors = int(error_match.group(1)) if error_match else 999

        if num_entries >= 60 and num_errors <= 5:
            checks.append({
                "name": "Beancount file parses successfully with sufficient entries",
                "passed": True,
                "detail": f"Parsed {num_entries} entries with {num_errors} errors. stderr: {stderr[:200]}"
            })
            total_score += 0.15
        else:
            checks.append({
                "name": "Beancount file parses successfully with sufficient entries",
                "passed": False,
                "detail": f"Found {num_entries} entries (need >=60) and {num_errors} errors (need <=5). Output: {output}. Stderr: {stderr[:300]}"
            })
    except Exception as e:
        checks.append({"name": "Beancount file parses successfully with sufficient entries", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 3: Required open directives present
    # -----------------------------------------------------------------------
    required_accounts = [
        "Assets:Checking",
        "Assets:Savings",
        "Income:Freelance:Consulting",
        "Expenses:Business:Software",
        "Expenses:Business:Office",
        "Expenses:Business:Meals",
        "Expenses:Business:Travel",
        "Expenses:Business:Utilities",
        "Expenses:Personal:Groceries",
        "Equity:Opening-Balances",
    ]
    open_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\s+open\s+(\S+)', re.MULTILINE)
    opened_accounts = set(open_pattern.findall(beancount_content))

    missing = []
    for acct in required_accounts:
        if acct not in opened_accounts:
            missing.append(acct)

    if not missing:
        checks.append({
            "name": "All required account open directives present",
            "passed": True,
            "detail": f"Found open directives for all {len(required_accounts)} required accounts."
        })
        total_score += 0.10
    else:
        checks.append({
            "name": "All required account open directives present",
            "passed": False,
            "detail": f"Missing open directives for: {missing}. Found accounts: {sorted(opened_accounts)}"
        })

    # -----------------------------------------------------------------------
    # CHECK 4: Opening balance transactions exist for Checking and Savings
    # -----------------------------------------------------------------------
    # Checking should show 8200.00 and Savings 25000.00 opening balances
    checking_open = re.search(r'8[,.]?200', beancount_content)
    savings_open = re.search(r'25[,.]?000', beancount_content)
    if checking_open and savings_open:
        checks.append({
            "name": "Opening balances for Checking (8200) and Savings (25000) present",
            "passed": True,
            "detail": "Both opening balance amounts found in file."
        })
        total_score += 0.08
    else:
        missing_balances = []
        if not checking_open:
            missing_balances.append("8200 (Checking)")
        if not savings_open:
            missing_balances.append("25000 (Savings)")
        checks.append({
            "name": "Opening balances for Checking (8200) and Savings (25000) present",
            "passed": False,
            "detail": f"Missing opening balance amounts: {missing_balances}"
        })

    # -----------------------------------------------------------------------
    # CHECK 5: Income transactions present (12 invoices)
    # -----------------------------------------------------------------------
    # Count income transactions - look for Income:Freelance:Consulting postings
    income_postings = re.findall(r'Income:Freelance:Consulting', beancount_content)
    if len(income_postings) >= 12:
        checks.append({
            "name": "At least 12 income (consulting invoice) transactions recorded",
            "passed": True,
            "detail": f"Found {len(income_postings)} Income:Freelance:Consulting postings."
        })
        total_score += 0.10
    else:
        checks.append({
            "name": "At least 12 income (consulting invoice) transactions recorded",
            "passed": False,
            "detail": f"Found only {len(income_postings)} Income:Freelance:Consulting postings (need >= 12)."
        })

    # -----------------------------------------------------------------------
    # CHECK 6: Double-entry format - transactions have exactly balanced postings
    # -----------------------------------------------------------------------
    # Check that most transactions use Assets:Checking as the offsetting account
    checking_postings = re.findall(r'Assets:Checking', beancount_content)
    if len(checking_postings) >= 50:
        checks.append({
            "name": "Double-entry transactions use Assets:Checking as offset (>=50 postings)",
            "passed": True,
            "detail": f"Found {len(checking_postings)} Assets:Checking postings, indicating proper double-entry."
        })
        total_score += 0.08
    else:
        checks.append({
            "name": "Double-entry transactions use Assets:Checking as offset (>=50 postings)",
            "passed": False,
            "detail": f"Found only {len(checking_postings)} Assets:Checking postings (need >= 50). Double-entry may be incomplete."
        })

    # -----------------------------------------------------------------------
    # CHECK 7: Fava budget directives present
    # -----------------------------------------------------------------------
    budget_pattern = re.compile(
        r'^\d{4}-\d{2}-\d{2}\s+custom\s+"budget"\s+\S+\s+"(?:monthly|daily|weekly|yearly)"\s+[\d.]+\s+USD',
        re.MULTILINE
    )
    budget_matches = budget_pattern.findall(beancount_content)
    if len(budget_matches) >= 2:
        checks.append({
            "name": "At least 2 Fava budget directives present with correct syntax",
            "passed": True,
            "detail": f"Found {len(budget_matches)} budget directives: {budget_matches[:3]}"
        })
        total_score += 0.10
    else:
        checks.append({
            "name": "At least 2 Fava budget directives present with correct syntax",
            "passed": False,
            "detail": f"Found {len(budget_matches)} valid budget directives (need >= 2). Directive format: YYYY-MM-DD custom \"budget\" Account \"monthly\" Amount USD"
        })

    # -----------------------------------------------------------------------
    # CHECK 8: Software budget is 200 USD monthly, Office budget is 300 USD monthly
    # -----------------------------------------------------------------------
    software_budget = re.search(
        r'custom\s+"budget"\s+Expenses:Business:Software\s+"monthly"\s+([\d.]+)\s+USD',
        beancount_content
    )
    office_budget = re.search(
        r'custom\s+"budget"\s+Expenses:Business:Office\s+"monthly"\s+([\d.]+)\s+USD',
        beancount_content
    )
    budget_correct = True
    budget_detail = []
    if software_budget:
        val = float(software_budget.group(1))
        if abs(val - 200.0) < 0.01:
            budget_detail.append(f"Software budget: {val} USD/month ✓")
        else:
            budget_correct = False
            budget_detail.append(f"Software budget: {val} USD/month (expected 200.00)")
    else:
        budget_correct = False
        budget_detail.append("Software budget directive not found")
    if office_budget:
        val = float(office_budget.group(1))
        if abs(val - 300.0) < 0.01:
            budget_detail.append(f"Office budget: {val} USD/month ✓")
        else:
            budget_correct = False
            budget_detail.append(f"Office budget: {val} USD/month (expected 300.00)")
    else:
        budget_correct = False
        budget_detail.append("Office budget directive not found")

    checks.append({
        "name": "Software budget=200 USD/month and Office budget=300 USD/month correctly specified",
        "passed": budget_correct,
        "detail": "; ".join(budget_detail)
    })
    if budget_correct:
        total_score += 0.07

    # -----------------------------------------------------------------------
    # CHECK 9: analysis_report.txt exists and contains expected sections
    # -----------------------------------------------------------------------
    report_files = list(workspace.rglob("analysis_report.txt"))
    if not report_files:
        checks.append({
            "name": "analysis_report.txt exists",
            "passed": False,
            "detail": "Could not find analysis_report.txt anywhere in workspace."
        })
    else:
        report_path = report_files[0]
        try:
            report_content = report_path.read_text()
            required_sections = ["NET WORTH", "SAVINGS RATE", "TOP"]
            missing_sections = [s for s in required_sections if s not in report_content.upper()]
            if not missing_sections:
                checks.append({
                    "name": "analysis_report.txt exists and contains NET WORTH, SAVINGS RATE, TOP sections",
                    "passed": True,
                    "detail": f"Found at {report_path}. All required sections present."
                })
                total_score += 0.10
            else:
                checks.append({
                    "name": "analysis_report.txt exists and contains NET WORTH, SAVINGS RATE, TOP sections",
                    "passed": False,
                    "detail": f"Missing sections: {missing_sections}. Content preview: {report_content[:300]}"
                })
        except Exception as e:
            checks.append({
                "name": "analysis_report.txt exists and contains NET WORTH, SAVINGS RATE, TOP sections",
                "passed": False,
                "detail": str(e)
            })

    # -----------------------------------------------------------------------
    # CHECK 10: analysis_report.txt shows reasonable net worth (>= checking + savings opening)
    # -----------------------------------------------------------------------
    if report_files:
        try:
            report_content = report_files[0].read_text()
            # Net worth should be at least initial deposits: 8200 + 25000 = 33200
            # After a full year of consulting, it should be much higher
            # Looking for any USD amount > 33000 in the net worth section
            nw_section = re.search(r'NET WORTH.*?(?=SAVINGS RATE|TOP|MONTHLY|$)', report_content, re.DOTALL | re.IGNORECASE)
            if nw_section:
                nw_text = nw_section.group(0)
                amounts = re.findall(r'[\d,]+\.?\d*', nw_text.replace(',', ''))
                large_amounts = [float(a) for a in amounts if float(a) > 33000]
                if large_amounts:
                    checks.append({
                        "name": "Net worth in analysis report is plausible (> initial deposits of 33200)",
                        "passed": True,
                        "detail": f"Found net worth amount(s) > 33000: {large_amounts[:3]}"
                    })
                    total_score += 0.07
                else:
                    checks.append({
                        "name": "Net worth in analysis report is plausible (> initial deposits of 33200)",
                        "passed": False,
                        "detail": f"No amounts > 33000 found in NET WORTH section. Amounts found: {amounts[:10]}"
                    })
            else:
                checks.append({
                    "name": "Net worth in analysis report is plausible (> initial deposits of 33200)",
                    "passed": False,
                    "detail": "Could not locate NET WORTH section in report."
                })
        except Exception as e:
            checks.append({
                "name": "Net worth in analysis report is plausible (> initial deposits of 33200)",
                "passed": False, "detail": str(e)
            })

    # -----------------------------------------------------------------------
    # CHECK 11: spending_query.bql file exists with valid BQL structure
    # -----------------------------------------------------------------------
    bql_files = list(workspace.rglob("spending_query.bql"))
    if not bql_files:
        checks.append({
            "name": "spending_query.bql file exists",
            "passed": False,
            "detail": "Could not find spending_query.bql anywhere in workspace."
        })
    else:
        bql_path = bql_files[0]
        try:
            bql_content = bql_path.read_text().upper()
            has_select = "SELECT" in bql_content
            has_expenses_filter = "EXPENSES" in bql_content or "ACCOUNT" in bql_content
            has_group_by = "GROUP BY" in bql_content
            has_2023 = "2023" in bql_content or "YEAR" in bql_content

            all_good = has_select and has_expenses_filter and has_group_by and has_2023
            checks.append({
                "name": "spending_query.bql has valid BQL structure (SELECT, expense filter, GROUP BY, 2023 filter)",
                "passed": all_good,
                "detail": (
                    f"SELECT: {has_select}, "
                    f"Expenses filter: {has_expenses_filter}, "
                    f"GROUP BY: {has_group_by}, "
                    f"2023 filter: {has_2023}. "
                    f"Content: {bql_path.read_text()[:300]}"
                )
            })
            if all_good:
                total_score += 0.10
        except Exception as e:
            checks.append({
                "name": "spending_query.bql has valid BQL structure",
                "passed": False,
                "detail": str(e)
            })

    # -----------------------------------------------------------------------
    # CHECK 12: BQL query actually runs against the beancount file
    # -----------------------------------------------------------------------
    if bql_files and beancount_files:
        try:
            bql_content_raw = bql_files[0].read_text().strip()
            result = subprocess.run(
                ["bean-query", str(beancount_path), bql_content_raw],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and len(result.stdout.strip()) > 10:
                checks.append({
                    "name": "BQL query in spending_query.bql executes successfully against ledger",
                    "passed": True,
                    "detail": f"Query output (first 300 chars): {result.stdout[:300]}"
                })
                total_score += 0.10
            else:
                checks.append({
                    "name": "BQL query in spending_query.bql executes successfully against ledger",
                    "passed": False,
                    "detail": f"Return code: {result.returncode}. Stdout: {result.stdout[:200]}. Stderr: {result.stderr[:200]}"
                })
        except Exception as e:
            checks.append({
                "name": "BQL query in spending_query.bql executes successfully against ledger",
                "passed": False,
                "detail": str(e)
            })

    return checks, min(total_score, 1.0)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    checks, score = run_checks(workspace_dir)

    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 8  # Must pass at least 8 of 12 checks

    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()