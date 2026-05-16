import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime, timezone

def load_json(path):
    with open(path) as f:
        return json.load(f)

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def run_eval(workspace_dir):
    base = Path("/home/ubuntu/.openclaw/workspace/goal-mode")
    memory = Path("/home/ubuntu/.openclaw/workspace/memory/goal-mode")
    checks = []

    # ── 1. Find the NAS goal slug ─────────────────────────────────────────
    expected_slug_prefix = "select-the-best-nas-device-for-a-4k-home-media-server-with"
    goal_dir = None
    goal_slug = None
    try:
        for d in base.iterdir():
            if d.is_dir() and d.name.startswith("select-the-best-nas"):
                goal_dir = d
                goal_slug = d.name
                break
        checks.append(check(
            "goal_directory_exists",
            goal_dir is not None,
            f"Found goal dir: {goal_slug}" if goal_dir else "No NAS goal directory found under goal-mode/"
        ))
    except Exception as e:
        checks.append(check("goal_directory_exists", False, f"Exception scanning goal-mode/: {e}"))

    if goal_dir is None:
        # Can't proceed with remaining checks
        remaining = [
            "slug_format_correct", "session_json_exists", "criteria_count",
            "criteria_specificity", "criteria_json_exists", "active_goal_json_exists",
            "active_session_md_exists", "evaluate_page_event_file_exists",
            "event_timestamp_format", "per_page_coverage_cap", "depth_over_breadth_score",
            "criteria_relevance_completeness", "criteria_exact_strings",
            "confidence_is_float", "session_pages_updated", "wrap_up_json_exists",
            "wrap_up_recommendation_null_or_justified", "history_md_appended",
            "latest_session_md_written", "active_session_md_finished",
            "findings_not_shopping_types"
        ]
        for r in remaining:
            checks.append(check(r, False, "Skipped: no NAS goal directory found"))
        score = sum(c["passed"] for c in checks) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── 2. Slug format ────────────────────────────────────────────────────
    try:
        # Must be lowercase, hyphens only (no spaces, no special chars), max 60 chars, no trailing hyphens
        slug_ok = (
            goal_slug == goal_slug.lower() and
            re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', goal_slug) is not None and
            len(goal_slug) <= 60 and
            not goal_slug.endswith('-')
        )
        checks.append(check("slug_format_correct", slug_ok,
            f"Slug '{goal_slug}': len={len(goal_slug)}, lowercase={goal_slug==goal_slug.lower()}, no-trailing-hyphen={not goal_slug.endswith('-')}"))
    except Exception as e:
        checks.append(check("slug_format_correct", False, str(e)))

    # ── 3. session.json exists and is valid ───────────────────────────────
    session = None
    session_path = goal_dir / "session.json"
    try:
        session = load_json(session_path)
        checks.append(check("session_json_exists", True, f"session.json found at {session_path}"))
    except Exception as e:
        checks.append(check("session_json_exists", False, f"session.json missing or invalid JSON: {e}"))

    # ── 4. Criteria count (4-12) ──────────────────────────────────────────
    try:
        criteria = session.get("criteria", [])
        criteria_count_ok = 4 <= len(criteria) <= 12
        checks.append(check("criteria_count", criteria_count_ok,
            f"Criteria count: {len(criteria)} (must be 4–12)"))
    except Exception as e:
        checks.append(check("criteria_count", False, str(e)))

    # ── 5. Criteria specificity (under 120 chars, no broad terms) ─────────
    try:
        criteria = session.get("criteria", []) if session else []
        too_broad = []
        too_long = []
        for c in criteria:
            text = c.get("text", "")
            if len(text) > 120:
                too_long.append(text[:60])
            # Check for overly broad single-word criteria like "Performance", "Storage", "Software"
            broad_patterns = [r'^performance$', r'^storage$', r'^software( features)?$',
                              r'^build quality$', r'^price$', r'^noise$', r'^power$']
            if any(re.fullmatch(p, text.strip().lower()) for p in broad_patterns):
                too_broad.append(text)
        specificity_ok = len(too_broad) == 0 and len(too_long) == 0
        checks.append(check("criteria_specificity", specificity_ok,
            f"Too broad: {too_broad}, Too long: {too_long}" if not specificity_ok else "All criteria are specific and within 120 chars"))
    except Exception as e:
        checks.append(check("criteria_specificity", False, str(e)))

    # ── 6. criteria.json exists ───────────────────────────────────────────
    try:
        cj = load_json(goal_dir / "criteria.json")
        checks.append(check("criteria_json_exists", isinstance(cj, list),
            f"criteria.json is a list with {len(cj)} items"))
    except Exception as e:
        checks.append(check("criteria_json_exists", False, str(e)))

    # ── 7. active-goal.json ───────────────────────────────────────────────
    try:
        agj = load_json(base / "active-goal.json")
        slug_matches = agj.get("goal_slug") == goal_slug
        has_session_path = "session_path" in agj
        checks.append(check("active_goal_json_exists", slug_matches and has_session_path,
            f"goal_slug matches: {slug_matches}, has session_path: {has_session_path}"))
    except Exception as e:
        checks.append(check("active_goal_json_exists", False, str(e)))

    # ── 8. active-session.md exists and references the NAS goal ──────────
    try:
        asm = (memory / "active-session.md").read_text()
        nas_mentioned = "nas" in asm.lower() or "4k" in asm.lower() or goal_slug in asm.lower()
        checks.append(check("active_session_md_exists", nas_mentioned,
            f"active-session.md mentions NAS goal: {nas_mentioned}"))
    except Exception as e:
        checks.append(check("active_session_md_exists", False, str(e)))

    # ── 9. evaluate_page event file exists ────────────────────────────────
    events_dir = goal_dir / "events"
    event_file = None
    try:
        event_files = list(events_dir.glob("*-evaluate-page.json"))
        checks.append(check("evaluate_page_event_file_exists", len(event_files) >= 1,
            f"Found {len(event_files)} evaluate-page event file(s)"))
        if event_files:
            event_file = event_files[0]
    except Exception as e:
        checks.append(check("evaluate_page_event_file_exists", False, str(e)))

    # ── 10. Event file timestamp format: YYYYMMDDTHHmmssZ ─────────────────
    try:
        if event_file:
            ts_part = event_file.name.replace("-evaluate-page.json", "")
            ts_pattern = re.fullmatch(r'\d{8}T\d{6}Z', ts_part)
            checks.append(check("event_timestamp_format", ts_pattern is not None,
                f"Timestamp '{ts_part}' matches YYYYMMDDTHHmmssZ: {ts_pattern is not None}"))
        else:
            checks.append(check("event_timestamp_format", False, "No event file found"))
    except Exception as e:
        checks.append(check("event_timestamp_format", False, str(e)))

    # ── 11. Per-page coverage cap: ≤3 criteria covered after single page ──
    try:
        criteria_after = session.get("criteria", [])
        covered_count = sum(1 for c in criteria_after if c.get("covered", False))
        cap_ok = covered_count <= 3
        checks.append(check("per_page_coverage_cap", cap_ok,
            f"Covered criteria after one evaluate_page: {covered_count} (must be ≤ 3)"))
    except Exception as e:
        checks.append(check("per_page_coverage_cap", False, str(e)))

    # ── 12. Depth-over-breadth: overview page should NOT have overall relevance > 0.65 ──
    try:
        if event_file:
            ev = load_json(event_file)
        else:
            ev = None
        # The page is a roundup/overview — should score 0.3–0.65 overall, not 0.8+
        if ev:
            rel = ev.get("relevance_score", 0)
            depth_ok = rel <= 0.65
            checks.append(check("depth_over_breadth_score", depth_ok,
                f"Overview page relevance_score={rel:.3f} (must be ≤ 0.65 for a roundup/overview)"))
        else:
            checks.append(check("depth_over_breadth_score", False, "No event data to evaluate"))
    except Exception as e:
        checks.append(check("depth_over_breadth_score", False, str(e)))

    # ── 13. criteria_relevance completeness: entry for every criterion ────
    try:
        if ev and session:
            criteria_texts = {c["text"] for c in session.get("criteria", [])}
            cr_entries = ev.get("criteria_relevance", [])
            cr_texts = {entry["criterion"] for entry in cr_entries}
            missing = criteria_texts - cr_texts
            all_present = len(missing) == 0
            checks.append(check("criteria_relevance_completeness", all_present,
                f"Missing criteria in criteria_relevance: {missing}" if missing else f"All {len(criteria_texts)} criteria present"))
        else:
            checks.append(check("criteria_relevance_completeness", False, "Missing event or session data"))
    except Exception as e:
        checks.append(check("criteria_relevance_completeness", False, str(e)))

    # ── 14. Exact criterion strings (no rephrasing) ───────────────────────
    try:
        if ev and session:
            criteria_texts = {c["text"] for c in session.get("criteria", [])}
            cr_entries = ev.get("criteria_relevance", [])
            rephrased = [e["criterion"] for e in cr_entries if e["criterion"] not in criteria_texts]
            checks.append(check("criteria_exact_strings", len(rephrased) == 0,
                f"Rephrased criteria found: {rephrased[:3]}" if rephrased else "All criterion strings are exact matches"))
        else:
            checks.append(check("criteria_exact_strings", False, "Missing event or session data"))
    except Exception as e:
        checks.append(check("criteria_exact_strings", False, str(e)))

    # ── 15. Confidence values are floats, not strings ─────────────────────
    try:
        string_confidences = []
        if ev:
            for finding in ev.get("findings", []):
                conf = finding.get("confidence")
                if isinstance(conf, str):
                    string_confidences.append(conf)
        checks.append(check("confidence_is_float", len(string_confidences) == 0,
            f"String confidence values found: {string_confidences}" if string_confidences else "All confidence values are numeric"))
    except Exception as e:
        checks.append(check("confidence_is_float", False, str(e)))

    # ── 16. session.json pages array updated after evaluate_page ─────────
    try:
        pages = session.get("pages", [])
        page_added = any("servethehome" in p.get("url", "") for p in pages)
        checks.append(check("session_pages_updated", page_added,
            f"servethehome.com page found in session.pages: {page_added}"))
    except Exception as e:
        checks.append(check("session_pages_updated", False, str(e)))

    # ── 17. wrap-up.json exists ───────────────────────────────────────────
    wrapup = None
    try:
        wrapup = load_json(goal_dir / "wrap-up.json")
        checks.append(check("wrap_up_json_exists", wrapup.get("operation") == "create_wrap_up",
            f"wrap-up.json operation field: {wrapup.get('operation')}"))
    except Exception as e:
        checks.append(check("wrap_up_json_exists", False, str(e)))

    # ── 18. wrap-up recommendation must be null (only 1 page evaluated) ───
    try:
        if wrapup:
            # 1 page evaluated, likely <3 covered → recommendation must be null
            pages_evaluated = wrapup.get("pages_evaluated", 0)
            covered_in_wrapup = wrapup.get("criteria_coverage", {}).get("covered", 99)
            rec = wrapup.get("recommendation")
            # Null is required if covered < 3 OR pages < 2
            needs_null = covered_in_wrapup < 3 or pages_evaluated < 2
            rec_ok = (rec is None) if needs_null else True
            checks.append(check("wrap_up_recommendation_null_or_justified", rec_ok,
                f"pages={pages_evaluated}, covered={covered_in_wrapup}, recommendation={rec!r} (null required when covered<3 or pages<2)"))
        else:
            checks.append(check("wrap_up_recommendation_null_or_justified", False, "wrap-up.json missing"))
    except Exception as e:
        checks.append(check("wrap_up_recommendation_null_or_justified", False, str(e)))

    # ── 19. history.md appended with new entry ────────────────────────────
    try:
        hist = (memory / "history.md").read_text()
        # Must have the old entry AND a new entry for the NAS goal
        has_old = "old-laptop-research-2023" in hist
        has_new = goal_slug in hist or "nas" in hist.lower()
        history_ok = has_old and has_new
        checks.append(check("history_md_appended", history_ok,
            f"Old entry present: {has_old}, New NAS entry present: {has_new}"))
    except Exception as e:
        checks.append(check("history_md_appended", False, str(e)))

    # ── 20. latest-session.md written for NAS goal ────────────────────────
    try:
        lsm = (memory / "latest-session.md").read_text()
        latest_ok = "nas" in lsm.lower() or goal_slug in lsm.lower() or "4k" in lsm.lower()
        checks.append(check("latest_session_md_written", latest_ok,
            f"latest-session.md references NAS goal: {latest_ok}"))
    except Exception as e:
        checks.append(check("latest_session_md_written", False, str(e)))

    # ── 21. active-session.md shows finished status ───────────────────────
    try:
        asm2 = (memory / "active-session.md").read_text()
        finished_ok = "finish" in asm2.lower() or "finished" in asm2.lower()
        checks.append(check("active_session_md_finished", finished_ok,
            f"active-session.md indicates finished: {finished_ok}"))
    except Exception as e:
        checks.append(check("active_session_md_finished", False, str(e)))

    # ── 22. Findings are NOT shopping types ───────────────────────────────
    try:
        shopping_types = {"price_drop", "deal_alert", "discount", "sale", "price_comparison", "coupon"}
        bad_types = []
        if ev:
            for finding in ev.get("findings", []):
                ftype = finding.get("type", "").lower()
                if ftype in shopping_types:
                    bad_types.append(ftype)
        checks.append(check("findings_not_shopping_types", len(bad_types) == 0,
            f"Shopping-type findings found: {bad_types}" if bad_types else "All finding types are domain-appropriate (not shopping defaults)"))
    except Exception as e:
        checks.append(check("findings_not_shopping_types", False, str(e)))

    total = len(checks)
    passed_count = sum(c["passed"] for c in checks)
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= int(total * 0.8)  # 80% threshold

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/.openclaw/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))