import json
import sys
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/.openclaw/workspace")
    checks = []
    total_score = 0.0

    # ── CHECK 1: soul_rules.json exists and is valid ──────────────────────────
    soul_rules_files = list(workspace.rglob("soul_rules.json"))
    if soul_rules_files:
        soul_rules_path = soul_rules_files[0]
        try:
            soul_rules = json.loads(soul_rules_path.read_text(encoding="utf-8"))
            checks.append({"name": "soul_rules.json_exists_and_valid_json", "passed": True,
                           "detail": f"Found at {soul_rules_path}"})
            total_score += 10.0
        except Exception as e:
            soul_rules = None
            checks.append({"name": "soul_rules.json_exists_and_valid_json", "passed": False,
                           "detail": f"File found but invalid JSON: {e}"})
    else:
        soul_rules = None
        checks.append({"name": "soul_rules.json_exists_and_valid_json", "passed": False,
                       "detail": "soul_rules.json not found anywhere in workspace"})

    # ── CHECK 2: soul_rules.json has correct schema structure ─────────────────
    if soul_rules is not None:
        has_schema = soul_rules.get("schema_version") == "1.0"
        has_stats = "stats" in soul_rules and "total_rules" in soul_rules.get("stats", {})
        has_rules = isinstance(soul_rules.get("rules"), list) and len(soul_rules.get("rules", [])) > 0
        has_workspace = "workspace" in soul_rules
        schema_ok = has_schema and has_stats and has_rules and has_workspace
        checks.append({"name": "soul_rules_schema_correct", "passed": schema_ok,
                       "detail": f"schema_version={soul_rules.get('schema_version')}, "
                                 f"total_rules={soul_rules.get('stats',{}).get('total_rules','missing')}, "
                                 f"rules_count={len(soul_rules.get('rules',[]))}, "
                                 f"has_workspace={has_workspace}"})
        if schema_ok:
            total_score += 10.0
    else:
        checks.append({"name": "soul_rules_schema_correct", "passed": False,
                       "detail": "soul_rules.json not available"})

    # ── CHECK 3: soul_rules.json extracted rules from SOUL.md/TOOLS.md/AGENTS.md
    if soul_rules is not None:
        rules = soul_rules.get("rules", [])
        # Must have extracted rules from at least 2 of the 3 source files
        source_files = {r.get("source_file", "") for r in rules}
        soul_sources = sum(1 for sf in ["SOUL.md", "TOOLS.md", "AGENTS.md"] if sf in source_files)
        has_multi_source = soul_sources >= 2
        # Must have some critical rules
        critical_rules = [r for r in rules if r.get("severity") == "critical"]
        has_critical = len(critical_rules) >= 1
        checks.append({"name": "rules_extracted_from_soul_files", "passed": has_multi_source and has_critical,
                       "detail": f"Source files present: {source_files}, "
                                 f"soul_sources={soul_sources}, critical_rules={len(critical_rules)}"})
        if has_multi_source and has_critical:
            total_score += 15.0
    else:
        checks.append({"name": "rules_extracted_from_soul_files", "passed": False,
                       "detail": "soul_rules.json not available"})

    # ── CHECK 4: drift_report.txt exists ─────────────────────────────────────
    drift_report_files = list(workspace.rglob("drift_report.txt"))
    if drift_report_files:
        drift_report_path = drift_report_files[0]
        try:
            drift_content = drift_report_path.read_text(encoding="utf-8")
            checks.append({"name": "drift_report_exists", "passed": True,
                           "detail": f"Found at {drift_report_path}, length={len(drift_content)}"})
            total_score += 10.0
        except Exception as e:
            drift_content = ""
            checks.append({"name": "drift_report_exists", "passed": False,
                           "detail": f"File found but unreadable: {e}"})
    else:
        drift_content = ""
        checks.append({"name": "drift_report_exists", "passed": False,
                       "detail": "drift_report.txt not found anywhere in workspace"})

    # ── CHECK 5: drift_report.txt contains proper SoulKeeper report structure ─
    if drift_content:
        has_header = "SoulKeeper Drift Report" in drift_content or "drift_score=" in drift_content
        # Must show a score
        score_match = re.search(r"(?:Score:\s*|drift_score=)(\d+)", drift_content)
        has_score = score_match is not None
        # Must mention at least one violation category (sycophantic, permission, padding, etc.)
        violation_keywords = ["sycophantic", "Sycophantic", "permission", "Permission",
                              "padding", "Padding", "waiting", "Waiting", "BUILTIN", "CRITICAL",
                              "HIGH", "MEDIUM", "violation"]
        has_violation_detail = any(kw in drift_content for kw in violation_keywords)
        report_ok = has_header and has_score and has_violation_detail
        score_val = int(score_match.group(1)) if score_match else -1
        checks.append({"name": "drift_report_has_proper_structure", "passed": report_ok,
                       "detail": f"has_header={has_header}, has_score={has_score} (score={score_val}), "
                                 f"has_violation_detail={has_violation_detail}"})
        if report_ok:
            total_score += 15.0
    else:
        checks.append({"name": "drift_report_has_proper_structure", "passed": False,
                       "detail": "drift_content empty or missing"})

    # ── CHECK 6: drift score is in the expected range (50-85 for this transcript)
    # The transcript has: BUILTIN-002 (+25), BUILTIN-005 (+15), BUILTIN-008 (+15),
    # BUILTIN-009 (+8), BUILTIN-010 (+8) = raw 71, capped at 71
    # With extra soul_rules, score may be higher. We accept 50-100.
    if drift_content:
        score_match = re.search(r"(?:Score:\s*|drift_score=)(\d+)", drift_content)
        if score_match:
            score_val = int(score_match.group(1))
            # Minimum expected: the 5 builtin violations alone give 71
            # With soul rules added, could be higher (up to 100 cap)
            score_in_range = score_val >= 50
            checks.append({"name": "drift_score_reflects_violations", "passed": score_in_range,
                           "detail": f"Detected score={score_val}; expected >= 50 based on transcript violations"})
            if score_in_range:
                total_score += 15.0
        else:
            checks.append({"name": "drift_score_reflects_violations", "passed": False,
                           "detail": "No numeric score found in drift report"})
    else:
        checks.append({"name": "drift_score_reflects_violations", "passed": False,
                       "detail": "drift_content empty or missing"})

    # ── CHECK 7: task_briefing.txt exists ────────────────────────────────────
    briefing_files = list(workspace.rglob("task_briefing.txt"))
    if briefing_files:
        briefing_path = briefing_files[0]
        try:
            briefing_content = briefing_path.read_text(encoding="utf-8")
            checks.append({"name": "task_briefing_exists", "passed": True,
                           "detail": f"Found at {briefing_path}, length={len(briefing_content)}"})
            total_score += 10.0
        except Exception as e:
            briefing_content = ""
            checks.append({"name": "task_briefing_exists", "passed": False,
                           "detail": f"File found but unreadable: {e}"})
    else:
        briefing_content = ""
        checks.append({"name": "task_briefing_exists", "passed": False,
                       "detail": "task_briefing.txt not found anywhere in workspace"})

    # ── CHECK 8: task_briefing.txt is from remind.py with database context ───
    if briefing_content:
        # Should be generated by remind.py --context with database/deployment related context
        # Must contain SoulKeeper remind output markers
        has_remind_header = ("Pre-Task Reminders" in briefing_content or
                             "reminder" in briefing_content.lower() or
                             "SOUL:" in briefing_content or
                             "Heartbeat" in briefing_content)
        # Must reference soul-based rules (SOUL: prefix or RULE prefix)
        has_soul_content = "SOUL:" in briefing_content or "RULE [" in briefing_content or "CRITICAL" in briefing_content
        briefing_ok = has_remind_header and has_soul_content
        checks.append({"name": "task_briefing_from_remind_tool", "passed": briefing_ok,
                       "detail": f"has_remind_header={has_remind_header}, has_soul_content={has_soul_content}"})
        if briefing_ok:
            total_score += 15.0
    else:
        checks.append({"name": "task_briefing_from_remind_tool", "passed": False,
                       "detail": "briefing_content empty or missing"})

    # ── FINAL SCORE ───────────────────────────────────────────────────────────
    max_score = 100.0
    normalized = total_score / max_score
    passed = normalized >= 0.6

    print(json.dumps({
        "passed": passed,
        "score": round(normalized, 3),
        "checks": checks,
    }, indent=2))


if __name__ == "__main__":
    main()