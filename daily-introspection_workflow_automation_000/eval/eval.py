#!/usr/bin/env python3
"""
Evaluation script for daily-introspection skill task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import re
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def read_file_safe(path):
    try:
        return Path(path).read_text(encoding="utf-8"), None
    except Exception as e:
        return None, str(e)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ── CHECK 1: Daily introspection file created at correct path ────────────
    intro_file = workspace / ".daily-introspection" / "introspection-2025-01-13.md"
    intro_content, intro_err = read_file_safe(intro_file)
    
    if intro_err:
        checks.append({
            "name": "daily_introspection_file_exists",
            "passed": False,
            "detail": f"File not found at {intro_file}: {intro_err}"
        })
        intro_has_content = False
    else:
        checks.append({
            "name": "daily_introspection_file_exists",
            "passed": True,
            "detail": f"Found introspection file at {intro_file}"
        })
        intro_has_content = True

    # ── CHECK 2: Introspection file has meaningful analysis (not just skeleton) ──
    if intro_has_content:
        # Must contain references to the actual errors from the conversation
        has_error_analysis = any(keyword in intro_content.lower() for keyword in [
            "linting", "memory retrieval", "promotion", "recurrence", "repeat",
            "e001", "e002", "e003", "incorrect", "rule violation"
        ])
        has_classification = any(kw in intro_content.lower() for kw in [
            "repeat pattern", "one-time", "new rule", "✅", "recorded", "corrected"
        ])
        # The skill mandates distinction between "Recorded, Rule Added" and "Corrected"
        has_status_distinction = (
            ("recorded" in intro_content.lower() or "rule added" in intro_content.lower())
            and len(intro_content) > 400
        )
        content_quality = has_error_analysis and (has_classification or has_status_distinction)
        checks.append({
            "name": "introspection_file_has_analysis",
            "passed": content_quality,
            "detail": (
                f"Content analysis: error_analysis={has_error_analysis}, "
                f"classification={has_classification}, status_distinction={has_status_distinction}, "
                f"length={len(intro_content)}"
            )
        })
    else:
        checks.append({
            "name": "introspection_file_has_analysis",
            "passed": False,
            "detail": "Cannot check content — file missing"
        })

    # ── CHECK 3: OpenClaw cron registry has the daily cron entry ────────────
    cron_registry_path = workspace / ".openclaw/crons/cron_registry.json"
    registry, reg_err = load_json_safe(cron_registry_path)

    if reg_err:
        checks.append({
            "name": "openclaw_cron_registry_exists",
            "passed": False,
            "detail": f"Cron registry not found: {reg_err}"
        })
        daily_cron_ok = False
        weekly_cron_ok = False
    else:
        checks.append({
            "name": "openclaw_cron_registry_exists",
            "passed": True,
            "detail": f"Registry found with {len(registry.get('crons', []))} entries"
        })

        crons = registry.get("crons", [])

        # CHECK 4: Daily cron entry with correct parameters
        daily_matches = [
            c for c in crons
            if c.get("name") == "Daily Self-Introspection"
            and c.get("cron") == "0 22 * * *"
            and c.get("tz") == "Asia/Shanghai"
            and c.get("session") == "main"
            and "exact" in c
        ]
        daily_cron_ok = len(daily_matches) > 0
        # Also check system-event content for key phrases
        if daily_cron_ok:
            se = daily_matches[0].get("system-event", "")
            se_ok = (
                "daily-introspect" in se
                and "daily-introspection" in se.lower()
            )
        else:
            se_ok = False

        checks.append({
            "name": "daily_cron_registered_correctly",
            "passed": daily_cron_ok and se_ok,
            "detail": (
                f"Daily cron found={daily_cron_ok}, system-event valid={se_ok}. "
                f"Cron entries: {[c.get('name') for c in crons]}"
            )
        })

        # CHECK 5: Weekly cron entry with correct parameters
        weekly_matches = [
            c for c in crons
            if c.get("name") == "Weekly Introspection Promotion"
            and c.get("cron") == "0 20 * * 0"
            and c.get("tz") == "Asia/Shanghai"
            and c.get("session") == "main"
            and "exact" in c
        ]
        weekly_cron_ok = len(weekly_matches) > 0
        if weekly_cron_ok:
            se_w = weekly_matches[0].get("system-event", "")
            se_w_ok = (
                "weekly-promote" in se_w or "weekly promotion" in se_w.lower()
            ) and "daily-introspection" in se_w.lower()
        else:
            se_w_ok = False

        checks.append({
            "name": "weekly_cron_registered_correctly",
            "passed": weekly_cron_ok and se_w_ok,
            "detail": (
                f"Weekly cron found={weekly_cron_ok}, system-event valid={se_w_ok}. "
                f"Expected: name='Weekly Introspection Promotion', cron='0 20 * * 0', "
                f"tz='Asia/Shanghai', session='main', --exact flag present"
            )
        })

    # ── CHECK 6: Evolution report created at correct path with correct format ─
    # Jan 13, 2025: ISO week 3 of 2025 → YYWW = "2503"
    # (Jan 13, 2025 = Monday of week 3)
    # Verify: date(2025,1,13).isocalendar() = (2025, 3, 1)
    import datetime
    d = datetime.date(2025, 1, 13)
    iso = d.isocalendar()
    expected_yyww = f"{str(iso[0])[2:]}{iso[1]:02d}"  # "2503"
    
    evolution_file = workspace / ".daily-introspection" / f"evolution-{expected_yyww}.md"
    evo_content, evo_err = read_file_safe(evolution_file)

    if evo_err:
        # Also check if agent used wrong format like evolution-2025-03.md or evolution-03-25.md
        wrong_formats = list((workspace / ".daily-introspection").glob("evolution-*.md")) if (workspace / ".daily-introspection").exists() else []
        checks.append({
            "name": "evolution_report_correct_filename",
            "passed": False,
            "detail": (
                f"Expected evolution-{expected_yyww}.md not found. "
                f"Error: {evo_err}. "
                f"Files found: {[f.name for f in wrong_formats]}"
            )
        })
        evo_ok = False
    else:
        checks.append({
            "name": "evolution_report_correct_filename",
            "passed": True,
            "detail": f"Found evolution-{expected_yyww}.md (YYWW format verified)"
        })
        evo_ok = True

    # ── CHECK 7: Evolution report has meaningful content ──────────────────────
    if evo_ok:
        has_week_ref = expected_yyww in evo_content or "week" in evo_content.lower()
        has_promotion_section = any(kw in evo_content.lower() for kw in [
            "promot", "agents.md", "memory.md", "tools.md", "rule"
        ])
        has_patterns = any(kw in evo_content.lower() for kw in [
            "pattern", "recurrence", "repeat", "improvement", "evolution", "mature"
        ])
        evo_content_ok = has_week_ref and has_promotion_section and len(evo_content) > 200
        checks.append({
            "name": "evolution_report_has_content",
            "passed": evo_content_ok,
            "detail": (
                f"week_ref={has_week_ref}, promotion_section={has_promotion_section}, "
                f"patterns={has_patterns}, length={len(evo_content)}"
            )
        })
    else:
        checks.append({
            "name": "evolution_report_has_content",
            "passed": False,
            "detail": "Cannot check — evolution file missing"
        })

    # ── CHECK 8: Mature rules promoted to target files BEFORE evolution report ─
    # The skill mandates: promotions happen BEFORE the evolution report is written.
    # Check: at least one target file (AGENTS.md, MEMORY.md, TOOLS.md) was modified
    # to include a promoted rule, AND the file mtime <= evolution report mtime.
    promotion_targets = {
        "AGENTS.md": workspace / "AGENTS.md",
        "MEMORY.md": workspace / "MEMORY.md",
        "TOOLS.md": workspace / "TOOLS.md",
    }
    
    promoted_rules_found = False
    promotion_before_report = False
    promotion_detail = []

    for fname, fpath in promotion_targets.items():
        content, err = read_file_safe(fpath)
        if err:
            promotion_detail.append(f"{fname}: read error ({err})")
            continue
        # Check if content was augmented beyond the original (original had ~4-6 rules)
        # Original AGENTS.md had exactly "Always confirm destructive operations", "Respond in user's language" etc.
        # A promotion would add something about linting, memory retrieval, or promotion thresholds
        original_markers = {
            "AGENTS.md": ["confirm destructive", "respond in the user"],
            "MEMORY.md": ["always search memory", "prefer the most recent"],
            "TOOLS.md": ["validate all tool inputs", "handle tool errors"],
        }
        new_rule_keywords = [
            "linting", "memory retrieval", "promotion threshold", ">1 week", "one week",
            "check memory", "optional", "recurrence", "introspection", "corrective"
        ]
        has_new_rule = any(kw in content.lower() for kw in new_rule_keywords)
        if has_new_rule:
            promoted_rules_found = True
            promotion_detail.append(f"{fname}: new rule detected")
        else:
            promotion_detail.append(f"{fname}: no new rule found")

    # Check ordering: if both evolution report and a promoted target exist,
    # the target file must have been modified at or before the evolution report.
    if evo_ok and promoted_rules_found:
        try:
            evo_mtime = evolution_file.stat().st_mtime
            for fname, fpath in promotion_targets.items():
                if fpath.exists():
                    target_mtime = fpath.stat().st_mtime
                    if target_mtime <= evo_mtime + 1:  # 1 second tolerance
                        promotion_before_report = True
                        break
        except Exception as e:
            promotion_detail.append(f"mtime check error: {e}")
    elif promoted_rules_found:
        # Evolution not present but promotions done — partial credit
        promotion_before_report = True

    checks.append({
        "name": "rules_promoted_before_report",
        "passed": promoted_rules_found and promotion_before_report,
        "detail": (
            f"promoted_rules_found={promoted_rules_found}, "
            f"promotion_before_report={promotion_before_report}. "
            + "; ".join(promotion_detail)
        )
    })

    # ── SCORING ──────────────────────────────────────────────────────────────
    # Weight the checks:
    weights = {
        "daily_introspection_file_exists":      0.15,
        "introspection_file_has_analysis":      0.15,
        "openclaw_cron_registry_exists":        0.05,
        "daily_cron_registered_correctly":      0.15,
        "weekly_cron_registered_correctly":     0.15,
        "evolution_report_correct_filename":    0.15,
        "evolution_report_has_content":         0.10,
        "rules_promoted_before_report":         0.10,
    }

    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w

    passed = score >= 0.70

    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()