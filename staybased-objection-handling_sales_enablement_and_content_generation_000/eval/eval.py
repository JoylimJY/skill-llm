import sys
import json
import re
from pathlib import Path

def find_artifact(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("objection_playbook.md"))
    if candidates:
        return candidates[0]
    # Also accept .txt
    candidates = list(Path(workspace).rglob("objection_playbook.txt"))
    if candidates:
        return candidates[0]
    return None

def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []

    # ── 1. File exists in artifacts/ ─────────────────────────────────────────
    artifact_path = find_artifact(workspace)
    file_exists = artifact_path is not None
    checks.append(check(
        "file_exists_in_artifacts",
        file_exists,
        f"Found at {artifact_path}" if file_exists else "objection_playbook.md not found anywhere under workspace/"
    ))

    if not file_exists:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    text = load_text(artifact_path)
    text_lower = text.lower()

    # ── 2. All 6 cases addressed ──────────────────────────────────────────────
    cases_covered = all(
        marker in text_lower
        for marker in ["case 001", "case 002", "case 003", "case 004", "case 005", "case 006"]
    ) or all(
        marker in text
        for marker in ["001", "002", "003", "004", "005", "006"]
    )
    # More lenient: check for each prospect name
    names = ["maria", "tom", "dr. patel", "sandra", "kevin", "dr. chen"]
    names_found = sum(1 for n in names if n in text_lower)
    cases_covered = names_found >= 5
    checks.append(check(
        "all_six_cases_addressed",
        cases_covered,
        f"Found {names_found}/6 prospect names in output"
    ))

    # ── 3. Correct objection categories applied ───────────────────────────────
    # Case 001 (Maria) → Price / Value Reframe
    price_cat_001 = any(kw in text_lower for kw in ["price", "value reframe", "roi", "return on investment", "cost of not", "💰"])
    checks.append(check(
        "case001_price_category_identified",
        price_cat_001,
        "Case 001 (Maria) should be classified as a Price objection with Value Reframe framework"
    ))

    # Case 002 (Tom) → Need / Gap Reveal
    need_cat_002 = any(kw in text_lower for kw in ["need", "gap reveal", "gap", "doing fine", "don't need", "💭", "🤔"])
    checks.append(check(
        "case002_need_category_identified",
        need_cat_002,
        "Case 002 (Tom) should be classified as a Need objection with Gap Reveal framework"
    ))

    # Case 003 (Dr. Patel) → Competitor / Differentiate
    comp_cat_003 = any(kw in text_lower for kw in ["competitor", "differentiat", "clinicos", "⚔️", "switch", "unique value"])
    checks.append(check(
        "case003_competitor_category_identified",
        comp_cat_003,
        "Case 003 (Dr. Patel) should be classified as Competitor objection with Differentiate framework"
    ))

    # Case 004 (Sandra) → Timing / Urgency + Easy Entry
    timing_cat_004 = any(kw in text_lower for kw in ["timing", "urgency", "delay", "easy entry", "pilot", "⏰", "commitment"])
    checks.append(check(
        "case004_timing_category_identified",
        timing_cat_004,
        "Case 004 (Sandra) should be classified as Timing objection with Urgency + Easy Entry framework"
    ))

    # ── 4. Case 005 (Kevin) → Walk Away ──────────────────────────────────────
    kevin_section = ""
    kevin_idx = text_lower.find("kevin")
    if kevin_idx >= 0:
        kevin_section = text_lower[max(0, kevin_idx-200):kevin_idx+800]

    walk_away_kevin = any(kw in kevin_section for kw in [
        "walk away", "walk-away", "not a fit", "not the right fit",
        "decline", "no", "move on", "disengage", "end", "timing isn't right",
        "budget isn't right", "preserve the relationship", "checked in",
        "whenever it makes sense", "next quarter", "free work", "disrespect"
    ])
    # Also check global for walk away near kevin
    walk_away_global = "walk away" in text_lower or "walk-away" in text_lower
    kevin_walk = walk_away_kevin or (walk_away_global and "kevin" in text_lower)
    checks.append(check(
        "case005_walk_away_applied",
        kevin_walk,
        "Case 005 (Kevin) meets multiple Walk Away criteria: disrespectful, free work demand, scope creep, unclear fit. Agent must recommend walking away, NOT overcoming the objection."
    ))

    # ── 5. NOT discounting for Case 001 ──────────────────────────────────────
    maria_section = ""
    maria_idx = text_lower.find("maria")
    if maria_idx >= 0:
        maria_section = text_lower[max(0, maria_idx-100):maria_idx+600]

    # Must NOT immediately discount (no phrase like "offer a discount" as first action)
    immediate_discount = bool(re.search(
        r"(immediately|first[ly]?\s+offer|offer\s+a?\s*discount|lower\s+the\s+price\s+first|reduce\s+the\s+price\s+first)",
        maria_section
    ))
    checks.append(check(
        "case001_no_immediate_discount",
        not immediate_discount,
        "Case 001: Must NOT immediately discount. Skill explicitly forbids this — it signals the price wasn't real."
    ))

    # ── 6. Feel-Felt-Found applied to Case 001 or Case 002 ───────────────────
    feel_felt_found = (
        "feel" in text_lower and "felt" in text_lower and "found" in text_lower
    )
    checks.append(check(
        "feel_felt_found_method_used",
        feel_felt_found,
        "The Feel-Felt-Found method must appear at least once (contains 'feel', 'felt', 'found' in the context of objection handling)"
    ))

    # ── 7. Case 004 quantifies delay cost ($800/mo) ───────────────────────────
    sandra_section = ""
    sandra_idx = text_lower.find("sandra")
    if sandra_idx >= 0:
        sandra_section = text_lower[max(0, sandra_idx-100):sandra_idx+800]
    else:
        # Try "harbor light"
        hl_idx = text_lower.find("harbor light")
        if hl_idx >= 0:
            sandra_section = text_lower[max(0, hl_idx-100):hl_idx+800]

    delay_cost_quantified = bool(re.search(r"\$?800", sandra_section)) or bool(re.search(r"\$?800", text_lower))
    checks.append(check(
        "case004_delay_cost_quantified",
        delay_cost_quantified,
        "Case 004 (Sandra): The skill requires quantifying delay cost. Rep notes state ~$800/mo in missed bookings. This number should appear in the response."
    ))

    # ── 8. Preemptive FAQ section for Alfred product ──────────────────────────
    has_faq = any(kw in text_lower for kw in ["faq", "preemptive", "common question", "frequently asked"])
    checks.append(check(
        "preemptive_faq_section_present",
        has_faq,
        "The playbook must include a Preemptive FAQ section (the skill requires this for proposals and sales pages)"
    ))

    # ── 9. Alfred-specific ROI numbers from skill's preemptive table ──────────
    # Skill says: "3-5 missed appointments/week = $300-500/mo. Pays for itself week 1."
    alfred_roi = (
        ("300" in text or "500" in text) and
        ("week 1" in text_lower or "week one" in text_lower or "first week" in text_lower)
    ) or (
        "3-5 missed" in text_lower or "3 to 5 missed" in text_lower
    )
    checks.append(check(
        "alfred_specific_roi_numbers_used",
        alfred_roi,
        "Alfred FAQ must use skill's exact preemptive ROI data: '3-5 missed appointments/week = $300-500/mo, pays for itself week 1'"
    ))

    # ── 10. Case 006 (Dr. Chen) — Trust/Credibility + competitor context ──────
    chen_section = ""
    chen_idx = text_lower.find("dr. chen")
    if chen_idx < 0:
        chen_idx = text_lower.find("chen")
    if chen_idx >= 0:
        chen_section = text_lower[max(0, chen_idx-100):chen_idx+800]

    trust_or_competitor = any(kw in chen_section for kw in [
        "trust", "credib", "de-risk", "pilot", "guarantee", "trial",
        "competitor", "differentiat", "dentaflow", "case study", "proof",
        "risk", "contract"
    ])
    checks.append(check(
        "case006_trust_or_competitor_framework",
        trust_or_competitor,
        "Case 006 (Dr. Chen) involves a competitor switch + trust concern. Should use De-Risk or Differentiate framework."
    ))

    # ── 11. Case 002 quantifies hidden cost (time/after-hours) ────────────────
    tom_section = ""
    tom_idx = text_lower.find("tom")
    if tom_idx >= 0:
        tom_section = text_lower[max(0, tom_idx-100):tom_idx+800]

    gap_quantified = any(kw in tom_section for kw in [
        "15%", "voicemail", "after-hour", "after hour", "missed", "time",
        "per week", "staff", "cost", "hour"
    ])
    checks.append(check(
        "case002_gap_quantified",
        gap_quantified,
        "Case 002 (Tom): Gap Reveal requires surfacing hidden cost. Should reference the 15% after-hours missed calls or staff time cost."
    ))

    # ── Score & pass/fail ─────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 3)
    # Must pass at minimum: file_exists, walk_away, no_immediate_discount, feel_felt_found, all_cases
    critical = [
        "file_exists_in_artifacts",
        "all_six_cases_addressed",
        "case005_walk_away_applied",
        "case001_no_immediate_discount",
        "feel_felt_found_method_used",
    ]
    critical_passed = all(
        any(c["name"] == cn and c["passed"] for c in checks)
        for cn in critical
    )
    passed = critical_passed and score >= 0.72

    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))