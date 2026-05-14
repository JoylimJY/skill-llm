#!/usr/bin/env python3
"""
Evaluation script for the Greek Individual Tax E1 Summary task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import math
from pathlib import Path

def find_output_file(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("e1_summary_2025.json"))
    if candidates:
        return candidates[0]
    return None

def round2(x):
    return round(x, 2)

def isclose(a, b, tol=0.51):
    """Allow up to 0.51 EUR tolerance for rounding differences."""
    return abs(a - b) <= tol

def calculate_expected():
    """
    Ground truth calculation following SKILL.md rules precisely.
    """
    # ── INCOME ──────────────────────────────────────────────────────────────

    # Employment income:
    # 12 months × 3200 = 38400 + 13th month 3200 = 41600 gross
    # Payslip has a duplicate June row → deduplicate → still 12 months + 13M
    employment_gross = 12 * 3200.00 + 3200.00  # = 41600.00
    # Social security (deductible from employment income per SKILL.md)
    social_security = 12 * 384.00  # = 4608.00
    # Net employment income for tax = 41600 - 4608 = 36992
    employment_net = employment_gross - social_security  # 36992.00

    # Rental income:
    # Gross: 12 × 750 = 9000
    rental_gross = 12 * 750.00  # = 9000.00
    # Expenses: 4 quarters × 150 = 600 maintenance
    rental_expenses = 4 * 150.00  # = 600.00
    # Per SKILL.md, rental deductions include maintenance → net = 9000 - 600 = 8400
    rental_net = rental_gross - rental_expenses  # = 8400.00
    # Rental tax rate (separate schedule per SKILL.md):
    # up to 12000: 15% → 8400 × 15% = 1260
    rental_tax = 8400.00 * 0.15  # = 1260.00

    # Professional/consulting income:
    # CONFIRMED invoices only (exclude DRAFT):
    # INV-001: 3500, INV-002: 4000, INV-003: 3500, INV-005: 3000 → total 14000
    consulting_gross = 3500.00 + 4000.00 + 3500.00 + 3000.00  # = 14000.00
    # Withholding 20% × 14000 = 2800
    consulting_withholding = consulting_gross * 0.20  # = 2800.00
    # Business expenses from expense_notes: 800 + 700 + 1200 + 800 = 3500
    consulting_expenses = 800.00 + 700.00 + 1200.00 + 800.00  # = 3500.00
    consulting_net = consulting_gross - consulting_expenses  # = 10500.00

    # Total income (for tax base and deduction cap calculations):
    # Employment net + consulting net + rental net (rental income enters as net rental income)
    # Note: rental is taxed separately; for the E1 form total income we use gross sources
    # SKILL.md: "total_income = employment + professional + property + investment"
    # For deduction caps: total_income = all sources
    total_income = employment_net + consulting_net + rental_net
    # = 36992 + 10500 + 8400 = 55892.00

    # ── DEDUCTIONS ──────────────────────────────────────────────────────────

    # Insurance premiums:
    # Life: 1100, Health: 900 → declared = 2000
    # Cap = 1200 × family_members; family = taxpayer(1) + spouse(1) + children(2) = 4
    insurance_declared = 2000.00
    family_members = 4  # taxpayer + spouse + 2 children
    insurance_cap = 1200.00 * family_members  # = 4800.00
    insurance_deduction = min(insurance_declared, insurance_cap)  # = 2000.00

    # Charitable donations:
    # Total: 800 + 400 + 300 = 1500
    charity_declared = 1500.00
    # Cap = max(5% of total_income, 2000)
    charity_cap = max(total_income * 0.05, 2000.00)
    # 55892 × 0.05 = 2794.60 → cap = 2794.60
    charity_deduction = min(charity_declared, charity_cap)  # = 1500.00 (under cap)

    # Medical expenses:
    # 250 + 480 + 870 + 600 = 2200
    # SKILL.md: no maximum limit for medical expenses
    medical_deduction = 2200.00

    # Total deductions (from taxable income base):
    total_deductions = insurance_deduction + charity_deduction + medical_deduction
    # = 2000 + 1500 + 2200 = 5700.00

    # ── TAXABLE INCOME ───────────────────────────────────────────────────────

    # Taxable income for progressive tax (employment + professional, net of deductions)
    # Rental is taxed separately at rental rates
    employment_professional_net = employment_net + consulting_net  # 36992 + 10500 = 47492
    taxable_income_main = max(0, employment_professional_net - total_deductions)
    # = 47492 - 5700 = 41792.00

    # ── PROGRESSIVE INCOME TAX ───────────────────────────────────────────────

    def calc_progressive_tax(income):
        tax = 0.0
        brackets = [
            (10000, 0.09),
            (10000, 0.22),  # 10001-20000
            (10000, 0.28),  # 20001-30000
            (10000, 0.36),  # 30001-40000
            (float('inf'), 0.44),  # 40001+
        ]
        remaining = income
        for width, rate in brackets:
            chunk = min(remaining, width)
            tax += chunk * rate
            remaining -= chunk
            if remaining <= 0:
                break
        return round2(tax)

    income_tax = calc_progressive_tax(taxable_income_main)
    # 10000×9% = 900
    # 10000×22% = 2200
    # 10000×28% = 2800
    # 10000×36% = 3600
    # 1792×44%  = 788.48
    # Total = 900+2200+2800+3600+788.48 = 10288.48

    # ── SOLIDARITY TAX ───────────────────────────────────────────────────────

    def calc_solidarity_tax(income):
        # Only on amounts over 30000
        if income <= 30000:
            return 0.0
        tax = 0.0
        # Bracket: 30001-40000 at 2.2%
        if income > 30000:
            chunk = min(income, 40000) - 30000
            tax += chunk * 0.022
        # Bracket: 40001-65000 at 5%
        if income > 40000:
            chunk = min(income, 65000) - 40000
            tax += chunk * 0.05
        # Bracket: 65001-220000 at 6.5%
        if income > 65000:
            chunk = min(income, 220000) - 65000
            tax += chunk * 0.065
        # Over 220000 at 9%
        if income > 220000:
            tax += (income - 220000) * 0.09
        return round2(tax)

    solidarity_tax = calc_solidarity_tax(taxable_income_main)
    # 30000-40000: 10000×2.2% = 220
    # 40000-41792: 1792×5%   = 89.60
    # Total solidarity = 309.60

    # ── TAX CREDITS ──────────────────────────────────────────────────────────

    # Basic credit: 2100
    # Spouse credit: 2100 (spouse has zero income)
    # Dependent children: 2 × 777 = 1554
    tax_credits = 2100.00 + 2100.00 + (2 * 777.00)  # = 6054.00

    # ── NET TAX ──────────────────────────────────────────────────────────────

    # Rental tax is paid separately at rental rates
    # Main income gross tax = income_tax + solidarity_tax
    gross_tax_main = round2(income_tax + solidarity_tax)
    # = 10288.48 + 309.60 = 10598.08

    # Apply credits to main tax
    net_tax_main = max(0, gross_tax_main - tax_credits)
    # = 10598.08 - 6054 = 4544.08

    # Withholding credits:
    # Employer: 6100 (from certificate — the authoritative value)
    # Consulting: 2800
    total_withholding = 6100.00 + consulting_withholding  # = 8900.00

    # Net tax due (main) after withholding
    net_tax_due_main = net_tax_main - total_withholding
    # = 4544.08 - 8900 = -4355.92 → this means refund; clamp at 0 for "due", record as refund

    # Total tax position:
    # Main net tax: 4544.08
    # Rental tax: 1260.00
    # Total tax before withholding: 5804.08
    # Total withholding: 8900.00
    # Net position: 5804.08 - 8900.00 = -3095.92 → refund of 3095.92

    total_gross_tax = round2(net_tax_main + rental_tax)  # 4544.08 + 1260 = 5804.08
    net_final = round2(total_gross_tax - total_withholding)  # 5804.08 - 8900 = -3095.92
    net_tax_due = round2(max(0, net_final))  # 0 if refund
    refund = round2(abs(min(0, net_final)))  # 3095.92

    effective_rate = round2((total_gross_tax / total_income) * 100)
    # = 5804.08 / 55892 × 100 = 10.38%

    return {
        "employment_gross": employment_gross,
        "employment_net": employment_net,
        "social_security": social_security,
        "consulting_gross": consulting_gross,
        "consulting_expenses": consulting_expenses,
        "consulting_net": consulting_net,
        "rental_gross": rental_gross,
        "rental_expenses": rental_expenses,
        "rental_net": rental_net,
        "rental_tax": rental_tax,
        "total_income": total_income,
        "total_deductions": total_deductions,
        "insurance_deduction": insurance_deduction,
        "charity_deduction": charity_deduction,
        "medical_deduction": medical_deduction,
        "taxable_income_main": taxable_income_main,
        "income_tax": income_tax,
        "solidarity_tax": solidarity_tax,
        "tax_credits": tax_credits,
        "gross_tax_main": gross_tax_main,
        "net_tax_main": net_tax_main,
        "total_withholding": total_withholding,
        "total_gross_tax": total_gross_tax,
        "net_tax_due": net_tax_due,
        "refund_amount": refund,
        "effective_rate": effective_rate,
    }

def run_checks(agent_data: dict, expected: dict) -> list:
    checks = []

    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    # Check 1: Employment income correctly parsed (deduplication + 13th month)
    agent_emp_gross = agent_data.get("employment_gross", agent_data.get("employment", {}).get("gross", None))
    try:
        agent_emp_gross = float(agent_emp_gross)
    except (TypeError, ValueError):
        agent_emp_gross = None
    check(
        "employment_gross_income",
        agent_emp_gross is not None and isclose(agent_emp_gross, expected["employment_gross"]),
        f"Expected employment gross {expected['employment_gross']}, got {agent_emp_gross}. Must include 13th month and deduplicate June row."
    )

    # Check 2: Social security deducted from employment
    agent_emp_net = agent_data.get("employment_net", agent_data.get("employment", {}).get("net", None))
    try:
        agent_emp_net = float(agent_emp_net)
    except (TypeError, ValueError):
        agent_emp_net = None
    check(
        "employment_net_income_after_social_security",
        agent_emp_net is not None and isclose(agent_emp_net, expected["employment_net"]),
        f"Expected employment net {expected['employment_net']} (after social security {expected['social_security']}), got {agent_emp_net}."
    )

    # Check 3: Consulting — exclude DRAFT invoice
    agent_consulting_gross = agent_data.get("consulting_gross", agent_data.get("professional", {}).get("gross", None))
    try:
        agent_consulting_gross = float(agent_consulting_gross)
    except (TypeError, ValueError):
        agent_consulting_gross = None
    check(
        "consulting_gross_excludes_draft",
        agent_consulting_gross is not None and isclose(agent_consulting_gross, expected["consulting_gross"]),
        f"Expected consulting gross {expected['consulting_gross']} (DRAFT invoice excluded), got {agent_consulting_gross}."
    )

    # Check 4: Consulting expenses deducted
    agent_consulting_net = agent_data.get("consulting_net", agent_data.get("professional", {}).get("net", None))
    try:
        agent_consulting_net = float(agent_consulting_net)
    except (TypeError, ValueError):
        agent_consulting_net = None
    check(
        "consulting_net_after_expenses",
        agent_consulting_net is not None and isclose(agent_consulting_net, expected["consulting_net"]),
        f"Expected consulting net {expected['consulting_net']} (after {expected['consulting_expenses']} expenses), got {agent_consulting_net}."
    )

    # Check 5: Rental net income
    agent_rental_net = agent_data.get("rental_net", agent_data.get("property", {}).get("rental_net", None))
    try:
        agent_rental_net = float(agent_rental_net)
    except (TypeError, ValueError):
        agent_rental_net = None
    check(
        "rental_net_income",
        agent_rental_net is not None and isclose(agent_rental_net, expected["rental_net"]),
        f"Expected rental net {expected['rental_net']} (gross 9000 - expenses 600), got {agent_rental_net}."
    )

    # Check 6: Rental tax at 15% (SEPARATE rental tax schedule, not progressive)
    agent_rental_tax = agent_data.get("rental_tax", agent_data.get("property", {}).get("rental_tax", None))
    try:
        agent_rental_tax = float(agent_rental_tax)
    except (TypeError, ValueError):
        agent_rental_tax = None
    check(
        "rental_tax_separate_schedule_15pct",
        agent_rental_tax is not None and isclose(agent_rental_tax, expected["rental_tax"]),
        f"Expected rental tax {expected['rental_tax']} (8400 × 15% rental rate schedule), got {agent_rental_tax}. Must use rental-specific rates NOT progressive income rates."
    )

    # Check 7: Total income
    agent_total_income = agent_data.get("total_income", None)
    try:
        agent_total_income = float(agent_total_income)
    except (TypeError, ValueError):
        agent_total_income = None
    check(
        "total_income",
        agent_total_income is not None and isclose(agent_total_income, expected["total_income"]),
        f"Expected total income {expected['total_income']}, got {agent_total_income}."
    )

    # Check 8: Insurance deduction (cap = 1200 × 4 family members = 4800, so 2000 full allowed)
    agent_insurance_ded = agent_data.get("insurance_deduction", agent_data.get("deductions", {}).get("insurance", None))
    try:
        agent_insurance_ded = float(agent_insurance_ded)
    except (TypeError, ValueError):
        agent_insurance_ded = None
    check(
        "insurance_deduction_capped",
        agent_insurance_ded is not None and isclose(agent_insurance_ded, expected["insurance_deduction"]),
        f"Expected insurance deduction {expected['insurance_deduction']} (min(2000, 1200×4)=2000), got {agent_insurance_ded}."
    )

    # Check 9: Charity deduction (1500 < max(55892×5%, 2000)=2794.60 → full 1500)
    agent_charity_ded = agent_data.get("charity_deduction", agent_data.get("deductions", {}).get("charity", None))
    try:
        agent_charity_ded = float(agent_charity_ded)
    except (TypeError, ValueError):
        agent_charity_ded = None
    check(
        "charity_deduction_correct_cap_formula",
        agent_charity_ded is not None and isclose(agent_charity_ded, expected["charity_deduction"]),
        f"Expected charity deduction {expected['charity_deduction']} (min(1500, max(5%×income,2000))=1500), got {agent_charity_ded}."
    )

    # Check 10: Progressive income tax on main taxable income
    agent_income_tax = agent_data.get("income_tax", None)
    try:
        agent_income_tax = float(agent_income_tax)
    except (TypeError, ValueError):
        agent_income_tax = None
    check(
        "progressive_income_tax",
        agent_income_tax is not None and isclose(agent_income_tax, expected["income_tax"], tol=1.0),
        f"Expected progressive income tax {expected['income_tax']} on taxable income {expected['taxable_income_main']}, got {agent_income_tax}."
    )

    # Check 11: Solidarity tax
    agent_solidarity = agent_data.get("solidarity_tax", None)
    try:
        agent_solidarity = float(agent_solidarity)
    except (TypeError, ValueError):
        agent_solidarity = None
    check(
        "solidarity_tax",
        agent_solidarity is not None and isclose(agent_solidarity, expected["solidarity_tax"], tol=1.0),
        f"Expected solidarity tax {expected['solidarity_tax']}, got {agent_solidarity}."
    )

    # Check 12: Tax credits (basic 2100 + spouse 2100 + 2×777=1554 = 6054)
    agent_credits = agent_data.get("tax_credits", None)
    try:
        agent_credits = float(agent_credits)
    except (TypeError, ValueError):
        agent_credits = None
    check(
        "family_tax_credits",
        agent_credits is not None and isclose(agent_credits, expected["tax_credits"]),
        f"Expected tax credits {expected['tax_credits']} (basic 2100 + spouse 2100 + 2 children×777=1554), got {agent_credits}."
    )

    # Check 13: Total withholding (employer 6100 + consulting 2800 = 8900)
    agent_withholding = agent_data.get("total_withholding", agent_data.get("withholding_credits", None))
    try:
        agent_withholding = float(agent_withholding)
    except (TypeError, ValueError):
        agent_withholding = None
    check(
        "total_withholding_credits",
        agent_withholding is not None and isclose(agent_withholding, expected["total_withholding"]),
        f"Expected total withholding {expected['total_withholding']} (employer 6100 from certificate + consulting 2800), got {agent_withholding}."
    )

    # Check 14: Net tax due or refund
    agent_net_due = agent_data.get("net_tax_due", None)
    agent_refund = agent_data.get("refund_amount", agent_data.get("refund", None))
    try:
        agent_net_due = float(agent_net_due) if agent_net_due is not None else None
        agent_refund = float(agent_refund) if agent_refund is not None else None
    except (TypeError, ValueError):
        pass

    # The result should show a refund (net_tax_due=0, refund=3095.92)
    # OR net_tax_due negative indicating refund
    net_due_ok = False
    refund_ok = False
    if agent_net_due is not None:
        net_due_ok = isclose(agent_net_due, expected["net_tax_due"], tol=2.0)  # should be 0
    if agent_refund is not None:
        refund_ok = isclose(agent_refund, expected["refund_amount"], tol=2.0)

    check(
        "net_tax_due_and_refund",
        (net_due_ok and refund_ok) or refund_ok,
        f"Expected net_tax_due={expected['net_tax_due']}, refund_amount={expected['refund_amount']}. "
        f"Got net_tax_due={agent_net_due}, refund={agent_refund}."
    )

    # Check 15: Effective rate reasonable (within 2%)
    agent_eff_rate = agent_data.get("effective_rate", None)
    try:
        agent_eff_rate = float(agent_eff_rate)
    except (TypeError, ValueError):
        agent_eff_rate = None
    check(
        "effective_tax_rate",
        agent_eff_rate is not None and isclose(agent_eff_rate, expected["effective_rate"], tol=2.0),
        f"Expected effective rate ~{expected['effective_rate']}%, got {agent_eff_rate}%."
    )

    # Check 16: Taxpayer AFM present
    agent_afm = str(agent_data.get("taxpayer_afm", agent_data.get("afm", "")))
    check(
        "taxpayer_afm_present",
        "123456789" in agent_afm,
        f"Expected AFM 123456789 in output, got '{agent_afm}'."
    )

    # Check 17: Year is 2025
    agent_year = agent_data.get("year", agent_data.get("tax_year", None))
    try:
        agent_year = int(agent_year)
    except (TypeError, ValueError):
        agent_year = None
    check(
        "tax_year_2025",
        agent_year == 2025,
        f"Expected year=2025, got {agent_year}."
    )

    return checks

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    output_file = find_output_file(workspace)

    if output_file is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_found", "passed": False,
                         "detail": "Could not find e1_summary_2025.json anywhere in workspace."}]
        }
        print(json.dumps(result))
        return

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            agent_data = json.load(f)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False,
                         "detail": f"Found file at {output_file} but could not parse JSON: {e}"}]
        }
        print(json.dumps(result))
        return

    expected = calculate_expected()

    checks = [{"name": "file_found", "passed": True, "detail": f"Found at {output_file}"}]
    checks += run_checks(agent_data, expected)

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall = score >= 0.80  # Need 80% of checks to pass

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()