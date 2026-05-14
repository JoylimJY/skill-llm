import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    ".state",
    "archive/2022/reports",
    "archive/2023/reports",
    "archive/2023/drafts",
    "data/raw/filings",
    "data/processed",
    "docs/internal",
    "docs/committee",
    "portfolio/watchlist",
    "portfolio/holdings",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "archive/2022/reports/annual_summary.txt": "Annual report summary for FY2022. Data archived.",
    "archive/2023/reports/Q4_notes.txt": "Q4 2023 earnings call notes. Draft only.",
    "archive/2023/drafts/screening_v1.json": json.dumps({"note": "old format - deprecated", "companies": []}),
    "data/raw/filings/10k_meta.csv": "ticker,year,filing_date\nXXX,2023,2024-02-15\nYYY,2023,2024-03-01",
    "data/processed/normalized_roe.csv": "ticker,year,roe\nXXX,2021,0.14\nXXX,2022,0.16\nXXX,2023,0.18",
    "docs/internal/framework_notes.txt": "Use the standard evaluation framework. See scripts folder for tooling.",
    "docs/committee/agenda_2024Q2.txt": "Agenda item 3: Investment screening results for new candidates.",
    "portfolio/watchlist/candidates_raw.txt": "BRND-US\nNETW-US\nCOMM-US\n# Add tickers here for screening",
    "portfolio/holdings/current_positions.json": json.dumps({"holdings": ["AAPL", "BRK.B"], "cash_pct": 0.12}),
    "tmp/scratch/old_calc.py": "# scratch calc\nroe_avg = sum([0.16, 0.18, 0.20]) / 3\nprint(roe_avg)",
    "docs/internal/rating_confusion.txt": (
        "REMINDER: Our old system used 1-5 stars. New framework uses A/B/C/D. "
        "Do NOT use old star ratings in committee reports."
    ),
    "data/processed/debt_ratios_old.json": json.dumps({
        "note": "pre-2024 calculations, methodology changed",
        "BRND": 0.48,
        "NETW": 0.55,
        "COMM": 0.31,
    }),
}
for rel_path, content in distractors.items():
    with open(os.path.join(workspace, rel_path), "w") as f:
        f.write(content)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: us-value-investing-framework
description: US stock valuation model skill (English-first + 中文) based on financial report data. Use when you need to apply explicit rules: ROE > 15% for 3+ years, debt ratio < 50%, free cash flow > 80% of net income, moat assessment (brand/network effect/cost advantage), then output investment rating (A/B/C/D) with reasons.
---

# US Stock Valuation Model - Value Investing Framework (EN + 中文)

This skill is an explicit rule-based value model focused on US stocks.

## Input

Company financial report data (structured JSON), including:
- 3+ years of ROE
- Debt ratio
- Free cash flow and net income
- Moat assessment: brand / network effect / cost advantage

Use the bundled template: `references/input-template.json`.

## Decision Rules (strict)

1. **ROE rule**: ROE > 15% for at least 3 consecutive years
2. **Leverage rule**: Debt ratio < 50%
3. **Cash conversion rule**: Free cash flow > 80% of net income
4. **Moat rule**: evaluate brand/network effect/cost advantage

## Output

- Investment rating: **A / B / C / D**
- Reasons (pass/fail explanation per rule)
- Bilingual summary (EN main + 中文摘要)

## Run

```bash
python3 scripts/evaluate_company.py \\
  --input references/input-template.json \\
  --out .state/eval.json \\
  --markdown .state/eval.md
```

## Rating policy

- **A**: all 4 rules pass
- **B**: 3 rules pass
- **C**: 2 rules pass
- **D**: 0-1 rule pass

## Resources

- `scripts/evaluate_company.py`: deterministic evaluator
- `references/input-template.json`: input schema example
"""
with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── references/input-template.json (schema example) ─────────────────────────
template = {
    "company": "ExampleCorp",
    "ticker": "EXMP",
    "roe_history": [0.18, 0.17, 0.20, 0.19],
    "debt_ratio": 0.42,
    "free_cash_flow": 950,
    "net_income": 1000,
    "moat": {
        "brand": True,
        "network_effect": False,
        "cost_advantage": True
    }
}
with open(os.path.join(workspace, "references/input-template.json"), "w") as f:
    json.dump(template, f, indent=2)

# ── scripts/evaluate_company.py (the deterministic evaluator) ────────────────
evaluator_code = r'''#!/usr/bin/env python3
"""
Deterministic value-investing evaluator.
Usage:
  python3 scripts/evaluate_company.py \
      --input <input.json> \
      --out <output.json> \
      --markdown <output.md>
"""
import argparse
import json
import sys
from pathlib import Path


def evaluate(data: dict) -> dict:
    company = data.get("company", "Unknown")
    ticker = data.get("ticker", "???")
    roe_history = data.get("roe_history", [])
    debt_ratio = data.get("debt_ratio", 1.0)
    free_cash_flow = data.get("free_cash_flow", 0)
    net_income = data.get("net_income", 1)
    moat = data.get("moat", {})

    results = {}

    # Rule 1: ROE > 15% for at least 3 consecutive years
    # Must find a run of >= 3 consecutive years all > 0.15
    roe_pass = False
    if len(roe_history) >= 3:
        max_run = 0
        current_run = 0
        for roe in roe_history:
            if roe > 0.15:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        roe_pass = max_run >= 3
    results["roe"] = {
        "pass": roe_pass,
        "detail": f"ROE history: {roe_history}. Max consecutive years > 15%: needed 3.",
    }

    # Rule 2: Debt ratio < 50%
    debt_pass = debt_ratio < 0.50
    results["leverage"] = {
        "pass": debt_pass,
        "detail": f"Debt ratio: {debt_ratio:.2%}. Threshold: < 50%.",
    }

    # Rule 3: Free cash flow > 80% of net income (strict >)
    if net_income > 0:
        fcf_ratio = free_cash_flow / net_income
        cash_pass = fcf_ratio > 0.80
    else:
        fcf_ratio = 0.0
        cash_pass = False
    results["cash_conversion"] = {
        "pass": cash_pass,
        "detail": f"FCF/NI ratio: {fcf_ratio:.2%}. Threshold: > 80%.",
    }

    # Rule 4: Moat — at least one moat factor must be True
    brand = bool(moat.get("brand", False))
    network = bool(moat.get("network_effect", False))
    cost = bool(moat.get("cost_advantage", False))
    moat_pass = brand or network or cost
    results["moat"] = {
        "pass": moat_pass,
        "detail": f"Brand={brand}, NetworkEffect={network}, CostAdvantage={cost}.",
    }

    # Rating
    passes = sum(1 for v in results.values() if v["pass"])
    if passes == 4:
        rating = "A"
    elif passes == 3:
        rating = "B"
    elif passes == 2:
        rating = "C"
    else:
        rating = "D"

    return {
        "company": company,
        "ticker": ticker,
        "rating": rating,
        "rules": results,
        "passes": passes,
    }


def to_markdown(eval_result: dict) -> str:
    c = eval_result["company"]
    t = eval_result["ticker"]
    r = eval_result["rating"]
    lines = [
        f"# Investment Evaluation: {c} ({t})",
        f"",
        f"## Rating: **{r}**",
        f"",
        f"## Rule Results",
        f"",
    ]
    rule_labels = {
        "roe": "ROE Rule (>15% for 3+ consecutive years)",
        "leverage": "Leverage Rule (debt ratio < 50%)",
        "cash_conversion": "Cash Conversion Rule (FCF > 80% of net income)",
        "moat": "Moat Rule (brand / network effect / cost advantage)",
    }
    for key, label in rule_labels.items():
        rule = eval_result["rules"][key]
        status = "✅ PASS" if rule["pass"] else "❌ FAIL"
        lines.append(f"### {label}")
        lines.append(f"- Status: {status}")
        lines.append(f"- Detail: {rule['detail']}")
        lines.append("")

    # Bilingual summary
    lines.append("## Summary (EN)")
    lines.append(
        f"{c} ({t}) receives an investment rating of **{r}** "
        f"based on {eval_result['passes']} out of 4 rules passing."
    )
    lines.append("")
    lines.append("## 中文摘要")
    rating_cn = {"A": "优质", "B": "良好", "C": "一般", "D": "不达标"}
    lines.append(
        f"{c}（{t}）的投资评级为 **{r}**（{rating_cn.get(r, r)}），"
        f"共通过 {eval_result['passes']}/4 项规则。"
    )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        data = json.load(f)

    result = evaluate(data)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    md_path = Path(args.markdown)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w") as f:
        f.write(to_markdown(result))

    print(f"Rating: {result['rating']} | Passes: {result['passes']}/4")
    print(f"JSON -> {out_path}")
    print(f"MD   -> {md_path}")


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts/evaluate_company.py"), "w") as f:
    f.write(evaluator_code)

# ── Three company input files for the agent to process ───────────────────────
# Company 1: "BrandMoat Inc." — designed to be Rating A (all 4 pass)
# ROE: 4 consecutive years all > 15% ✓
# Debt: 0.38 < 0.50 ✓
# FCF/NI: 920/1000 = 92% > 80% ✓
# Moat: brand=True ✓
company1 = {
    "company": "BrandMoat Inc.",
    "ticker": "BRND",
    "roe_history": [0.16, 0.17, 0.19, 0.21],
    "debt_ratio": 0.38,
    "free_cash_flow": 920,
    "net_income": 1000,
    "moat": {
        "brand": True,
        "network_effect": False,
        "cost_advantage": False
    }
}

# Company 2: "NetworkEdge Corp." — designed to be Rating B (3 pass)
# ROE: [0.14, 0.18, 0.19, 0.22] — year 1 is 0.14, so max consecutive run = 3 (years 2-4) ✓
# Debt: 0.53 >= 0.50 ✗  (FAILS)
# FCF/NI: 850/1000 = 85% > 80% ✓
# Moat: network_effect=True ✓
# Passes: ROE✓, Leverage✗, Cash✓, Moat✓ → 3 passes → B
company2 = {
    "company": "NetworkEdge Corp.",
    "ticker": "NETW",
    "roe_history": [0.14, 0.18, 0.19, 0.22],
    "debt_ratio": 0.53,
    "free_cash_flow": 850,
    "net_income": 1000,
    "moat": {
        "brand": False,
        "network_effect": True,
        "cost_advantage": False
    }
}

# Company 3: "CostCut LLC" — designed to be Rating C (2 pass)
# ROE: [0.20, 0.12, 0.18, 0.19] — year 2 is 0.12, breaks the run.
#   Run before break: 1 (year1=0.20), run after break: 2 (year3=0.18, year4=0.19)
#   Max consecutive = 2 < 3 → FAILS ROE
# Debt: 0.44 < 0.50 ✓
# FCF/NI: 800/1000 = exactly 80% — NOT > 80% (strict greater than), so FAILS
# Moat: cost_advantage=True ✓
# Passes: ROE✗, Leverage✓, Cash✗, Moat✓ → 2 passes → C
company3 = {
    "company": "CostCut LLC",
    "ticker": "COMM",
    "roe_history": [0.20, 0.12, 0.18, 0.19],
    "debt_ratio": 0.44,
    "free_cash_flow": 800,
    "net_income": 1000,
    "moat": {
        "brand": False,
        "network_effect": False,
        "cost_advantage": True
    }
}

for company_data, filename in [
    (company1, "data/raw/filings/BRND_financials.json"),
    (company2, "data/raw/filings/NETW_financials.json"),
    (company3, "data/raw/filings/COMM_financials.json"),
]:
    with open(os.path.join(workspace, filename), "w") as f:
        json.dump(company_data, f, indent=2)

# ── Committee brief (the "business ask" context) ─────────────────────────────
brief = """\
Investment Committee — Pre-Meeting Screening Brief
===================================================
Date: 2024-Q2 Review

Three candidate companies have been identified for potential portfolio inclusion.
Raw financial data files are available in the data/raw/filings/ directory:
  - BRND_financials.json
  - NETW_financials.json
  - COMM_financials.json

The investment team needs standardized evaluation reports for each candidate
before the committee meeting. Please use the firm's established evaluation
framework to produce structured output files for each company.

Expected deliverables for each company (named by ticker):
  - A structured evaluation result file
  - A formatted markdown report

Place all output under the .state/ directory, organized by ticker.
"""
with open(os.path.join(workspace, "docs/committee/screening_brief.txt"), "w") as f:
    f.write(brief)

print("Workspace generated successfully.")
print("Companies configured:")
print("  BRND → expected rating: A")
print("  NETW → expected rating: B (debt ratio fails, ROE consecutive-run edge case passes)")
print("  COMM → expected rating: C (ROE broken run fails, FCF exactly 80% fails strict >)")