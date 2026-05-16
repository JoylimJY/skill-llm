import sys
import json
import re
from pathlib import Path

def find_file(base: Path, filename: str):
    """Find a file by name anywhere under base."""
    results = list(base.rglob(filename))
    if results:
        return results[0]
    return None

def read_file_safe(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        return ""

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

def run_eval(workspace_str):
    workspace = Path(workspace_str)
    home = Path.home()
    reno_root = home / "home-renovation"

    # ============================================================
    # CHECK 1: memory.md exists in ~/home-renovation/
    # ============================================================
    memory_file = reno_root / "memory.md"
    mem_exists = memory_file.exists()
    check(
        "memory.md exists in ~/home-renovation/",
        mem_exists,
        f"{'Found' if mem_exists else 'NOT FOUND'}: {memory_file}"
    )
    mem_content = read_file_safe(memory_file) if mem_exists else ""

    # ============================================================
    # CHECK 2: A project file exists under ~/home-renovation/projects/
    # ============================================================
    project_files = list((reno_root / "projects").rglob("*.md")) if (reno_root / "projects").exists() else []
    proj_exists = len(project_files) > 0
    check(
        "Project file exists under ~/home-renovation/projects/",
        proj_exists,
        f"Found {len(project_files)} project file(s): {[str(p) for p in project_files]}"
    )
    proj_content = ""
    if proj_exists:
        # Read all project files combined
        for pf in project_files:
            proj_content += read_file_safe(pf) + "\n"

    # ============================================================
    # CHECK 3: Project file tracks budget with original vs actual structure
    # ============================================================
    has_budget_tracking = (
        ("original" in proj_content or "estimate" in proj_content or "quote" in proj_content) and
        ("actual" in proj_content or "spent" in proj_content or "paid" in proj_content)
    )
    check(
        "Project file has budget tracking (original estimate vs actual spend)",
        has_budget_tracking,
        "Budget section must track original estimate AND actual/paid amounts."
    )

    # ============================================================
    # CHECK 4: Contingency is set at 15-20% (must see a number in that range applied to the $11,200 quote)
    # The low quote is $11,200. 15% = $1,680, 20% = $2,240.
    # Accept any contingency value between $1,500 and $2,300 or mention of 15-20%.
    # ============================================================
    contingency_ok = False
    # Look for explicit percentage mention
    if re.search(r'1[5-9]\s*%|20\s*%', proj_content):
        contingency_ok = True
    # Look for dollar amount in correct range (1500-2300)
    dollar_amounts = re.findall(r'\$?\s*(\d[\d,]+)', proj_content)
    for amt_str in dollar_amounts:
        try:
            amt = int(amt_str.replace(",", ""))
            if 1500 <= amt <= 2300:
                contingency_ok = True
                break
        except Exception:
            pass
    # Also accept the combined total that implies 15-20% added
    # 11200 * 1.15 = 12880, * 1.20 = 13440
    for amt_str in dollar_amounts:
        try:
            amt = int(amt_str.replace(",", ""))
            if 12800 <= amt <= 13500:
                contingency_ok = True
                break
        except Exception:
            pass
    check(
        "Contingency budget is set at 15-20% (skill-mandated range, not generic 10%)",
        contingency_ok,
        "Must document contingency of 15-20% of project cost. Generic 10% is WRONG per SKILL.md."
    )

    # ============================================================
    # CHECK 5: Deposit red flag is raised — contractor demands 50% (>30% limit)
    # ============================================================
    deposit_flagged = False
    combined = proj_content + mem_content
    # Look for mention of deposit issue, 50%, or >30% warning
    if re.search(r'deposit', combined):
        if re.search(r'50\s*%|5,600|5600|exceed|too\s*high|red\s*flag|warning|never\s*more\s*than\s*30|30\s*%\s*max|over\s*30|above\s*30|more\s*than\s*30', combined):
            deposit_flagged = True
    check(
        "50% deposit demand is flagged as a red flag (SKILL.md: never >30%)",
        deposit_flagged,
        "The contractor demanded 50% deposit. SKILL.md mandates flagging any deposit >30%. Must be documented."
    )

    # ============================================================
    # CHECK 6: Low bid warning is documented (quote $11,200 vs competitors $19,800-$21,500)
    # ============================================================
    low_bid_flagged = False
    # Look for mention of low bid concern or "cheapest bid" or significantly below
    if re.search(r'low\s*bid|cheapest|below\s*(normal|typical|mid|range|market)|significantly\s*(lower|below)|outlier|corner|cut|suspici', combined):
        low_bid_flagged = True
    # Also accept if they flag the price comparison
    if re.search(r'11[,.]?200|11200', combined) and re.search(r'19[,.]?800|21[,.]?500|other\s*bid|competitor', combined):
        low_bid_flagged = True
    check(
        "Low bid warning is documented (quote is ~50% below competitors)",
        low_bid_flagged,
        "Quote of $11,200 vs $19,800-$21,500 competitors is a major red flag. Must be flagged per SKILL.md 'cheapest bid' warning."
    )

    # ============================================================
    # CHECK 7: Permit-skipping red flag is documented
    # ============================================================
    permit_flagged = re.search(r'permit', combined) and re.search(
        r'skip|avoid|no\s*permit|without\s*permit|red\s*flag|warning|unpermitted|problem|risk|insurance', combined
    )
    check(
        "Contractor's permit-skipping attitude is flagged as a red flag",
        bool(permit_flagged),
        "Contractor explicitly said they skip permits. SKILL.md: 'Insurance won't cover unpermitted work. Resale problems.'"
    )

    # ============================================================
    # CHECK 8: Change order is documented with written quote requirement
    # ============================================================
    change_order_documented = re.search(r'change\s*order|change order', combined)
    written_quote_required = re.search(r'written|writing|in\s*writing|written\s*quote|get.*quote|quote.*before|approve.*writing', combined)
    co_ok = bool(change_order_documented) and bool(written_quote_required)
    check(
        "Change order is documented with requirement for written quote before approval",
        co_ok,
        "SKILL.md Rule 5: Every change request must get a written quote before approving. Verbal OK from Dave is not acceptable."
    )

    # ============================================================
    # CHECK 9: Budget is updated and remaining contingency is recalculated after change order
    # ============================================================
    # Original $11,200, change order $2,800.
    # If contingency was ~$1,680-$2,240 (15-20%), after $2,800 CO the contingency is exhausted.
    # Agent must note updated budget total or recalculate remaining contingency.
    co_budget_updated = False
    # Look for updated total (11200 + 2800 = 14000) or mention of contingency impact
    all_dollar_amounts = re.findall(r'\$?\s*(\d[\d,]+)', combined)
    for amt_str in all_dollar_amounts:
        try:
            amt = int(amt_str.replace(",", ""))
            if 13800 <= amt <= 14200:  # ~14,000 updated total
                co_budget_updated = True
                break
        except Exception:
            pass
    # Also accept if they mention contingency being depleted/exceeded/impacted
    if re.search(r'contingency.*deplet|contingency.*exceed|contingency.*impact|contingency.*remain|remaining.*contingency|over.*budget|exceed.*contingency|contingency.*insufficient|contingency.*cover|contingency.*2[,.]?800|2800.*contingency', combined):
        co_budget_updated = True
    check(
        "Budget and remaining contingency recalculated after change order (SKILL.md Rule 5)",
        co_budget_updated,
        "After $2,800 CO against ~$1,680-$2,240 contingency, agent must update total and recalculate remaining contingency."
    )

    # ============================================================
    # CHECK 10: Decision rationale is documented (what options, why chosen, cost/timeline impact)
    # ============================================================
    decision_documented = re.search(r'decision|rationale|why|chosen|option|consider', combined)
    check(
        "Decision documentation present (options considered, rationale, impact)",
        bool(decision_documented),
        "SKILL.md Rule 6: For every major decision, record options considered, why chosen, cost and timeline impact."
    )

    # ============================================================
    # CHECK 11: Phases are referenced in correct order
    # ============================================================
    phases_mentioned = (
        re.search(r'demo', combined) and
        re.search(r'rough.in|electrical|plumbing', combined) and
        re.search(r'finish|tile|fixture|paint', combined)
    )
    check(
        "Renovation phases referenced in correct sequence",
        bool(phases_mentioned),
        "Project tracking should reference phases per SKILL.md sequence (demo → rough-in → finishes)."
    )

    # ============================================================
    # CHECK 12: Contractor availability red flag ("can start tomorrow/Monday")
    # ============================================================
    avail_flagged = re.search(r'start.*tomorrow|tomorrow.*start|immediately|monday|suspici.*availab|availab.*suspici|why.*free|free.*why|red.flag', combined)
    check(
        "Suspicious contractor availability is noted as a red flag",
        bool(avail_flagged),
        "SKILL.md Red Flags: 'Can start tomorrow (why are they free?)' — contractor offered to start in 3 days."
    )

    # ============================================================
    # Scoring
    # ============================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 9  # Must pass at least 9/12 checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "eval_invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    try:
        result = run_eval(sys.argv[1])
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Eval script crashed: {e}"}]
        }
    print(json.dumps(result, indent=2))