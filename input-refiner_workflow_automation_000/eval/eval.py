import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(workspace.rglob("refined_output.txt"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                         "detail": "refined_output.txt not found anywhere in workspace."}]
        }

    output_file = candidates[0]
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False,
                         "detail": f"Could not read refined_output.txt: {e}"}]
        }

    # ── Check 1: Exact section headers present ────────────────────────────────
    required_headers = ["Intent:", "Refined Input:", "Alternative Versions:", "Why:"]
    missing_headers = []
    for h in required_headers:
        if h not in content:
            missing_headers.append(h)
    headers_ok = len(missing_headers) == 0
    checks.append({
        "name": "required_section_headers_present",
        "passed": headers_ok,
        "detail": (
            "All four required section headers found: Intent:, Refined Input:, Alternative Versions:, Why:"
            if headers_ok
            else f"Missing section headers: {missing_headers}"
        )
    })

    # ── Check 2: Intent section is a single-sentence summary ─────────────────
    intent_match = re.search(r"Intent:\s*\n(.+?)(?:\n\n|\nRefined Input:)", content, re.DOTALL)
    if intent_match:
        intent_text = intent_match.group(1).strip()
        # Should be a single sentence or very short
        sentences = [s.strip() for s in re.split(r'[.!?]', intent_text) if s.strip()]
        intent_non_empty = len(intent_text) > 10
        intent_not_too_long = len(intent_text) < 400
        intent_ok = intent_non_empty and intent_not_too_long
    else:
        intent_text = ""
        intent_ok = False
    checks.append({
        "name": "intent_section_valid",
        "passed": intent_ok,
        "detail": (
            f"Intent section found and reasonably concise: '{intent_text[:120]}...'"
            if intent_ok
            else f"Intent section missing or too long/empty. Found: '{intent_text[:80]}'"
        )
    })

    # ── Check 3: Refined Input is a NUMBERED LIST (not a single paragraph) ───
    # The input is long and multi-point, so the skill mandates numbered items.
    refined_match = re.search(
        r"Refined Input:\s*\n(.*?)(?:\nAlternative Versions:|\Z)",
        content, re.DOTALL
    )
    if refined_match:
        refined_text = refined_match.group(1).strip()
    else:
        refined_text = ""

    # Detect numbered list: at least 3 lines starting with "1.", "2.", "3." etc.
    numbered_items = re.findall(r"^\s*\d+\.\s+.+", refined_text, re.MULTILINE)
    has_numbered_list = len(numbered_items) >= 3
    checks.append({
        "name": "refined_input_is_numbered_list",
        "passed": has_numbered_list,
        "detail": (
            f"Refined Input contains {len(numbered_items)} numbered items (≥3 required). "
            "Correct: long multi-point input must be broken into ordered numbered list."
            if has_numbered_list
            else f"Refined Input has only {len(numbered_items)} numbered item(s). "
                 "Expected a numbered priority-ordered list for this long multi-point input, "
                 f"not a paragraph. Refined text starts: '{refined_text[:120]}'"
        )
    })

    # ── Check 4: CSV export as highest-priority item ──────────────────────────
    # The main goal (CSV export from dashboard) must appear first or near-first.
    first_item = numbered_items[0] if numbered_items else ""
    csv_or_export_first = bool(
        re.search(r"(export|csv|data export|dashboard export)", first_item, re.IGNORECASE)
    )
    checks.append({
        "name": "main_goal_is_first_priority",
        "passed": csv_or_export_first,
        "detail": (
            f"First numbered item correctly addresses the primary export goal: '{first_item[:120]}'"
            if csv_or_export_first
            else f"First numbered item does not address the main export/CSV goal. "
                 f"Found: '{first_item[:120]}'"
        )
    })

    # ── Check 5: Alternative Versions section has 1–3 alternatives ───────────
    alt_match = re.search(
        r"Alternative Versions:\s*\n(.*?)(?:\nWhy:|\Z)",
        content, re.DOTALL
    )
    if alt_match:
        alt_text = alt_match.group(1).strip()
        alt_bullets = re.findall(r"^\s*[-•*]\s+.+", alt_text, re.MULTILINE)
        # Also accept numbered alternatives
        alt_numbered = re.findall(r"^\s*\d+\.\s+.+", alt_text, re.MULTILINE)
        total_alts = len(alt_bullets) + len(alt_numbered)
    else:
        total_alts = 0
    alts_ok = 1 <= total_alts <= 3
    checks.append({
        "name": "alternative_versions_count_1_to_3",
        "passed": alts_ok,
        "detail": (
            f"Alternative Versions contains {total_alts} item(s) — within required range of 1–3."
            if alts_ok
            else f"Alternative Versions contains {total_alts} item(s). Must be between 1 and 3."
        )
    })

    # ── Check 6: Why section is non-empty and mentions priority/structure ─────
    why_match = re.search(r"Why:\s*\n(.+)", content, re.DOTALL)
    if why_match:
        why_text = why_match.group(1).strip()
        why_non_empty = len(why_text) > 20
        mentions_priority_or_structure = bool(
            re.search(
                r"(priorit|order|structur|organiz|separ|list|point|multi|broke|break|numbered)",
                why_text, re.IGNORECASE
            )
        )
        why_ok = why_non_empty and mentions_priority_or_structure
    else:
        why_text = ""
        why_ok = False
    checks.append({
        "name": "why_section_explains_restructuring",
        "passed": why_ok,
        "detail": (
            f"Why section explains restructuring/prioritization: '{why_text[:120]}'"
            if why_ok
            else f"Why section is missing, too short, or does not explain why content was "
                 f"reorganized by priority. Found: '{why_text[:120]}'"
        )
    })

    # ── Check 7: No scope expansion — XLSX not as core requirement ────────────
    # David said XLSX is "not urgent at all" — it must not appear in items 1–3
    top_3_items = "\n".join(numbered_items[:3]) if len(numbered_items) >= 3 else ""
    xlsx_in_top3 = bool(re.search(r"xlsx", top_3_items, re.IGNORECASE))
    no_scope_expansion = not xlsx_in_top3
    checks.append({
        "name": "no_scope_expansion_xlsx_not_top_priority",
        "passed": no_scope_expansion,
        "detail": (
            "XLSX format correctly kept out of top-3 priority items (it was marked optional/not urgent)."
            if no_scope_expansion
            else "XLSX format incorrectly placed in top-3 priority items. "
                 "It was stated as 'not urgent at all' and must not be elevated in priority."
        )
    })

    # ── Check 8: Permission/compliance constraint is present ──────────────────
    # Admin vs. regular user permission constraint must appear somewhere in refined output
    permissions_present = bool(
        re.search(r"(admin|permission|role|regular user|own.{0,20}data|compliance)",
                  refined_text, re.IGNORECASE)
    )
    checks.append({
        "name": "permission_constraint_preserved",
        "passed": permissions_present,
        "detail": (
            "Permission/role constraint (admin vs. regular user) correctly preserved in refined output."
            if permissions_present
            else "Permission/role constraint (admin exports all data, regular users export only their own) "
                 "is missing from the Refined Input section."
        )
    })

    # ── Check 9: Async email notification for large exports is present ────────
    async_present = bool(
        re.search(r"(email.{0,30}(notif|complet|done|finish)|async|background|large.{0,20}(export|file)|notif.{0,30}email)",
                  refined_text, re.IGNORECASE)
    )
    checks.append({
        "name": "async_email_notification_preserved",
        "passed": async_present,
        "detail": (
            "Async email notification for large exports correctly preserved."
            if async_present
            else "The async/email-notification requirement for large exports is missing from Refined Input."
        )
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4)

    # Must pass checks 1 (headers), 3 (numbered list), and 4 (main goal first)
    # for overall pass — these are the core discriminative checks
    critical_checks = ["required_section_headers_present",
                       "refined_input_is_numbered_list",
                       "main_goal_is_first_priority"]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))