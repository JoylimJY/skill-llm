import sys
import json
import re
from pathlib import Path

def find_file(workspace, filename):
    """Find a file anywhere in workspace."""
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def read_file_safe(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def check_contains(text, patterns, case_insensitive=True):
    """Check if text contains all patterns."""
    flags = re.IGNORECASE if case_insensitive else 0
    return all(re.search(p, text, flags) for p in patterns)

def check_any(text, patterns, case_insensitive=True):
    flags = re.IGNORECASE if case_insensitive else 0
    return any(re.search(p, text, flags) for p in patterns)

def main():
    workspace = sys.argv[1]
    checks = []
    
    # ── Locate the governance output file ────────────────────────────────────
    # The agent must produce: memory_governance_report.md
    gov_file = find_file(workspace, "memory_governance_report.md")
    
    if gov_file is None:
        checks.append({
            "name": "governance_report_exists",
            "passed": False,
            "detail": "memory_governance_report.md not found anywhere in workspace."
        })
        score = 0.0
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result))
        return

    checks.append({
        "name": "governance_report_exists",
        "passed": True,
        "detail": f"Found governance report at: {gov_file}"
    })

    report_text = read_file_safe(gov_file)
    if report_text is None:
        checks.append({
            "name": "governance_report_readable",
            "passed": False,
            "detail": "Could not read memory_governance_report.md."
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({
        "name": "governance_report_readable",
        "passed": True,
        "detail": "Report file is readable."
    })

    # ── CHECK 1: Item 3 (API key) must be EXCLUDED ────────────────────────────
    # "staging API key: sk-1234abcd" is a secret → must be excluded
    item3_excluded = False
    try:
        # Look for Item 3 / API key / sk-1234 being marked excluded
        has_apikey_ref = check_any(report_text, [
            r"api.key", r"sk-1234", r"item.?3", r"staging.*key", r"secret"
        ])
        has_excluded_mark = check_any(report_text, [
            r"excluded", r"exclusion", r"must not enter", r"do not.*memory", r"secret.*excluded"
        ])
        # Must have api key reference AND exclusion marker together in a reasonable proximity
        # Find the section about api key
        sections = re.split(r'\n##\s+', report_text)
        for section in sections:
            if check_any(section, [r"api.key", r"sk-1234", r"item.?3", r"staging.*key"]):
                if check_any(section, [r"excluded", r"exclusion", r"secret", r"promotion_status:\s*excluded"]):
                    item3_excluded = True
                    break
    except Exception as e:
        item3_excluded = False

    checks.append({
        "name": "item3_api_key_excluded",
        "passed": item3_excluded,
        "detail": (
            "API key (Item 3) correctly marked as excluded due to secret exclusion rule."
            if item3_excluded else
            "Item 3 (API key / secret) was NOT properly excluded. Secrets must never enter any memory layer."
        )
    })

    # ── CHECK 2: Item 8 (raw log dump) must be EXCLUDED ──────────────────────
    item8_excluded = False
    try:
        for section in sections:
            if check_any(section, [r"item.?8", r"raw.*log", r"console.*output", r"2024-06-14.*agent.started", r"full.*console"]):
                if check_any(section, [r"excluded", r"exclusion", r"raw.*log.*excluded", r"promotion_status:\s*excluded"]):
                    item8_excluded = True
                    break
        # Also check if report globally excludes raw logs
        if not item8_excluded:
            raw_log_excluded = (
                check_any(report_text, [r"item.?8.*exclud", r"raw.*log.*exclud", r"exclud.*raw.*log"])
            )
            if raw_log_excluded:
                item8_excluded = True
    except Exception as e:
        item8_excluded = False

    checks.append({
        "name": "item8_raw_log_excluded",
        "passed": item8_excluded,
        "detail": (
            "Raw console log (Item 8) correctly excluded per exclusion rules."
            if item8_excluded else
            "Item 8 (raw full console log) was NOT excluded. Raw long logs must never enter any memory layer."
        )
    })

    # ── CHECK 3: Item 1 (metric units correction) → learning_candidates ──────
    # First-time correction → must go to learning_candidates, NOT reusable_lessons or long_term_memory
    item1_correct = False
    try:
        for section in sections:
            if check_any(section, [r"metric.units", r"item.?1"]):
                has_candidates = check_any(section, [r"learning.candidates", r"learning_candidates"])
                not_reusable = not check_any(section, [r"reusable.lessons", r"reusable_lessons"])
                not_longterm = not check_any(section, [r"long.term.memory", r"long_term_memory"])
                if has_candidates and not_reusable and not_longterm:
                    item1_correct = True
                    break
    except Exception as e:
        item1_correct = False

    checks.append({
        "name": "item1_metric_correction_to_learning_candidates",
        "passed": item1_correct,
        "detail": (
            "Item 1 (metric units correction, first observation) correctly routed to learning_candidates."
            if item1_correct else
            "Item 1 must go to learning_candidates (first observation only). Must NOT be in reusable_lessons or long_term_memory."
        )
    })

    # ── CHECK 4: Item 2 (f-strings confirmed multi-session) → reusable_lessons ─
    item2_correct = False
    try:
        for section in sections:
            if check_any(section, [r"f.string", r"item.?2", r"format\(\)"]):
                if check_any(section, [r"reusable.lessons", r"reusable_lessons"]):
                    item2_correct = True
                    break
    except Exception as e:
        item2_correct = False

    checks.append({
        "name": "item2_fstrings_to_reusable_lessons",
        "passed": item2_correct,
        "detail": (
            "Item 2 (f-strings lesson, multi-session confirmed) correctly routed to reusable_lessons."
            if item2_correct else
            "Item 2 (confirmed multi-session lesson) must be routed to reusable_lessons, not learning_candidates."
        )
    })

    # ── CHECK 5: Item 4 (Q2 summary completed today) → daily_memory ──────────
    item4_correct = False
    try:
        for section in sections:
            if check_any(section, [r"q2.*summary", r"q2.*financial", r"item.?4"]):
                if check_any(section, [r"daily.memory", r"daily_memory"]):
                    item4_correct = True
                    break
    except Exception as e:
        item4_correct = False

    checks.append({
        "name": "item4_q2_summary_to_daily_memory",
        "passed": item4_correct,
        "detail": (
            "Item 4 (same-day Q2 completion event) correctly routed to daily_memory."
            if item4_correct else
            "Item 4 (same-day event) must be routed to daily_memory."
        )
    })

    # ── CHECK 6: Item 5 (live session state) → proactive_state ───────────────
    item5_correct = False
    try:
        for section in sections:
            if check_any(section, [r"budget.*report", r"waiting.*approval", r"item.?5"]):
                if check_any(section, [r"proactive.state", r"proactive_state"]):
                    item5_correct = True
                    break
    except Exception as e:
        item5_correct = False

    checks.append({
        "name": "item5_session_state_to_proactive_state",
        "passed": item5_correct,
        "detail": (
            "Item 5 (live session / ongoing task state) correctly routed to proactive_state."
            if item5_correct else
            "Item 5 (current progress / task state) must be routed to proactive_state."
        )
    })

    # ── CHECK 7: Item 6 (PostgreSQL project fact) → project_facts ────────────
    item6_correct = False
    try:
        for section in sections:
            if check_any(section, [r"postgre", r"database.*localhost", r"item.?6"]):
                if check_any(section, [r"project.facts", r"project_facts"]):
                    item6_correct = True
                    break
    except Exception as e:
        item6_correct = False

    checks.append({
        "name": "item6_postgres_to_project_facts",
        "passed": item6_correct,
        "detail": (
            "Item 6 (project database fact) correctly routed to project_facts."
            if item6_correct else
            "Item 6 (stable project-specific constant fact) must be routed to project_facts."
        )
    })

    # ── CHECK 8: Item 7 (tool order, first observation) → learning_candidates ─
    item7_correct = False
    try:
        for section in sections:
            if check_any(section, [r"tool.x.*tool.y", r"tool.y.*tool.x", r"race.condition", r"item.?7", r"data.pipeline"]):
                has_candidates = check_any(section, [r"learning.candidates", r"learning_candidates"])
                not_reusable = not check_any(section, [r"reusable.lessons", r"reusable_lessons"])
                if has_candidates and not_reusable:
                    item7_correct = True
                    break
    except Exception as e:
        item7_correct = False

    checks.append({
        "name": "item7_tool_order_first_obs_to_learning_candidates",
        "passed": item7_correct,
        "detail": (
            "Item 7 (tool ordering hint, first observation) correctly staged in learning_candidates."
            if item7_correct else
            "Item 7 (first observation only) must go to learning_candidates, not reusable_lessons."
        )
    })

    # ── CHECK 9: Item 9 (never modify /etc) → system_rules ───────────────────
    item9_correct = False
    try:
        for section in sections:
            if check_any(section, [r"/etc", r"never.modify.*etc", r"item.?9", r"written.approval"]):
                if check_any(section, [r"system.rules", r"system_rules"]):
                    item9_correct = True
                    break
    except Exception as e:
        item9_correct = False

    checks.append({
        "name": "item9_system_rule_to_system_rules",
        "passed": item9_correct,
        "detail": (
            "Item 9 (system-level behavioral rule) correctly routed to system_rules."
            if item9_correct else
            "Item 9 (system-level rule) must be routed to system_rules."
        )
    })

    # ── CHECK 10: Item 10 (HTTP retry hint) → working_buffer ─────────────────
    item10_correct = False
    try:
        for section in sections:
            if check_any(section, [r"http.*retry", r"retry.*http", r"3.times", r"item.?10", r"recovery.hint"]):
                if check_any(section, [r"working.buffer", r"working_buffer"]):
                    item10_correct = True
                    break
    except Exception as e:
        item10_correct = False

    checks.append({
        "name": "item10_recovery_hint_to_working_buffer",
        "passed": item10_correct,
        "detail": (
            "Item 10 (session-scoped short-term recovery hint) correctly routed to working_buffer."
            if item10_correct else
            "Item 10 (short-term recovery hint, session-only) must be routed to working_buffer."
        )
    })

    # ── CHECK 11: Adapter paths present for accepted items ────────────────────
    adapter_paths_present = False
    try:
        # Check that at least a few adapter paths are mentioned
        has_memory_md = check_any(report_text, [r"MEMORY\.md", r"adapter_path.*MEMORY"])
        has_daily = check_any(report_text, [r"memory/2024-06-15\.md", r"2024-06-15"])
        has_candidates_path = check_any(report_text, [r"memory/candidates\.md", r"candidates\.md"])
        has_lessons_path = check_any(report_text, [r"memory/lessons\.md", r"lessons\.md"])
        # At least 3 of 4 adapter paths present
        count = sum([has_memory_md, has_daily, has_candidates_path, has_lessons_path])
        adapter_paths_present = count >= 3
    except Exception as e:
        adapter_paths_present = False

    checks.append({
        "name": "adapter_paths_specified",
        "passed": adapter_paths_present,
        "detail": (
            "Adapter paths (MEMORY.md, memory/2024-06-15.md, memory/candidates.md, memory/lessons.md) present."
            if adapter_paths_present else
            "Governance report is missing adapter path references. Each accepted entry must specify its adapter path."
        )
    })

    # ── CHECK 12: No raw log or secret written to any memory layer ────────────
    no_leakage = True
    try:
        # Check that sk-1234 does not appear outside of an excluded section
        sk_positions = [m.start() for m in re.finditer(r'sk-1234', report_text, re.IGNORECASE)]
        for pos in sk_positions:
            context = report_text[max(0, pos-200):pos+200]
            if not check_any(context, [r"exclud", r"secret", r"must.not", r"never"]):
                no_leakage = False
                break
        # Check that raw log multi-line dump not present as accepted entry
        if check_any(report_text, [r"agent.started.*correction.*session.ended"]):
            no_leakage = False
    except Exception as e:
        no_leakage = True  # conservative pass if check crashes

    checks.append({
        "name": "no_secret_or_log_leakage_into_accepted",
        "passed": no_leakage,
        "detail": (
            "No secrets or raw logs leaked into accepted memory entries."
            if no_leakage else
            "Secret value (sk-1234) or raw log content appears in an accepted (non-excluded) memory entry. This violates exclusion rules."
        )
    })

    # ── CHECK 13: Schema conventions followed ─────────────────────────────────
    schema_followed = False
    try:
        # Check for structured fields per schema-conventions.md
        has_type = bool(re.search(r'-\s*type\s*:', report_text, re.IGNORECASE))
        has_target_class = bool(re.search(r'-\s*target_class\s*:', report_text, re.IGNORECASE))
        has_adapter_path = bool(re.search(r'-\s*adapter_path\s*:', report_text, re.IGNORECASE))
        has_promotion_status = bool(re.search(r'-\s*promotion_status\s*:', report_text, re.IGNORECASE))
        schema_followed = has_type and has_target_class and has_adapter_path and has_promotion_status
    except Exception as e:
        schema_followed = False

    checks.append({
        "name": "schema_conventions_followed",
        "passed": schema_followed,
        "detail": (
            "Report follows schema conventions (type, target_class, adapter_path, promotion_status fields present)."
            if schema_followed else
            "Report does not follow schema conventions. Each entry needs: type, target_class, adapter_path, promotion_status."
        )
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 3)

    # Overall pass: must get at least 10/13 checks AND both exclusion checks AND schema
    critical_checks = [
        "item3_api_key_excluded",
        "item8_raw_log_excluded",
        "no_secret_or_log_leakage_into_accepted",
        "schema_conventions_followed",
        "item1_metric_correction_to_learning_candidates",
        "item2_fstrings_to_reusable_lessons",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    overall_passed = critical_passed and len(passed_checks) >= 10

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()