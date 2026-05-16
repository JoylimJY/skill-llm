#!/usr/bin/env python3
"""
Evaluation script for the deep-research skill task.
Checks:
1. research-config.yaml correctly updated (domain != healthcare, >=2 performance metrics)
2. executive-summary.md exists, has correct completeness tags, is <=50 lines
3. validation-checklist.md exists with missing metrics table
4. full-report.md exists with verified/pending sections, short/medium/long-term strategy, card index
5. Sourcing validation passes (all card references resolve to existing source files)
6. All three completeness levels (high/medium/low) appear in outputs
"""

import sys
import json
import re
import subprocess
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    ws = Path(workspace)
    skill_dir = ws / "skills" / "deep-research"
    reports_dir = skill_dir / "reports"
    sources_dir = skill_dir / "sources"
    config_path = skill_dir / "config" / "research-config.yaml"

    checks = []
    total_score = 0.0
    weights = {
        "config_domain_updated": 0.15,
        "config_performance_metrics": 0.10,
        "executive_summary_exists": 0.05,
        "executive_summary_length": 0.10,
        "executive_summary_completeness_tags": 0.10,
        "validation_checklist_exists": 0.05,
        "validation_checklist_has_table": 0.05,
        "full_report_exists": 0.05,
        "full_report_verified_section": 0.05,
        "full_report_pending_section": 0.05,
        "full_report_strategy_sections": 0.10,
        "full_report_card_index": 0.05,
        "sourcing_validation_passes": 0.10,
    }

    # ── 1. Config: domain updated ──────────────────────────────────────────────
    try:
        import yaml
        config = yaml.safe_load(config_path.read_text())
        domain = config.get("research_domain", "")
        domain_ok = (
            bool(domain)
            and domain.lower() not in ("healthcare", "your_domain_here", "")
        )
        checks.append(check(
            "config_domain_updated",
            domain_ok,
            f"research_domain='{domain}' (must not be 'healthcare' or empty)"
        ))
        if domain_ok:
            total_score += weights["config_domain_updated"]
    except Exception as e:
        checks.append(check("config_domain_updated", False, f"Exception: {e}"))

    # ── 2. Config: performance metrics >=2 ────────────────────────────────────
    try:
        import yaml
        config = yaml.safe_load(config_path.read_text())
        km = config.get("key_metrics", {})
        perf = km.get("performance", [])
        perf_ok = isinstance(perf, list) and len(perf) >= 2
        checks.append(check(
            "config_performance_metrics",
            perf_ok,
            f"performance metrics count={len(perf) if isinstance(perf, list) else 0} (need >=2)"
        ))
        if perf_ok:
            total_score += weights["config_performance_metrics"]
    except Exception as e:
        checks.append(check("config_performance_metrics", False, f"Exception: {e}"))

    # ── 3. Executive summary exists ────────────────────────────────────────────
    exec_path = reports_dir / "executive-summary.md"
    exec_exists = exec_path.exists()
    checks.append(check(
        "executive_summary_exists",
        exec_exists,
        f"reports/executive-summary.md {'found' if exec_exists else 'NOT FOUND'}"
    ))
    if exec_exists:
        total_score += weights["executive_summary_exists"]

    # ── 4. Executive summary length ≤50 lines ──────────────────────────────────
    try:
        if exec_exists:
            lines = exec_path.read_text().splitlines()
            line_count = len(lines)
            length_ok = line_count <= 50
            checks.append(check(
                "executive_summary_length",
                length_ok,
                f"executive-summary.md has {line_count} lines (must be <=50)"
            ))
            if length_ok:
                total_score += weights["executive_summary_length"]
        else:
            checks.append(check("executive_summary_length", False, "File missing"))
    except Exception as e:
        checks.append(check("executive_summary_length", False, f"Exception: {e}"))

    # ── 5. Executive summary has completeness tags ─────────────────────────────
    try:
        if exec_exists:
            content = exec_path.read_text().lower()
            has_high = "high" in content
            has_medium = "medium" in content
            has_low = "low" in content
            has_verified = "verified" in content or "pending" in content
            tags_ok = has_high and has_medium and has_low and has_verified
            checks.append(check(
                "executive_summary_completeness_tags",
                tags_ok,
                f"Has high={has_high}, medium={has_medium}, low={has_low}, verified/pending={has_verified}"
            ))
            if tags_ok:
                total_score += weights["executive_summary_completeness_tags"]
        else:
            checks.append(check("executive_summary_completeness_tags", False, "File missing"))
    except Exception as e:
        checks.append(check("executive_summary_completeness_tags", False, f"Exception: {e}"))

    # ── 6. Validation checklist exists ────────────────────────────────────────
    check_path = reports_dir / "validation-checklist.md"
    check_exists = check_path.exists()
    checks.append(check(
        "validation_checklist_exists",
        check_exists,
        f"reports/validation-checklist.md {'found' if check_exists else 'NOT FOUND'}"
    ))
    if check_exists:
        total_score += weights["validation_checklist_exists"]

    # ── 7. Validation checklist has table ─────────────────────────────────────
    try:
        if check_exists:
            content = check_path.read_text()
            # Look for markdown table with pipe characters and card references
            has_table = "|" in content and ("card-" in content.lower() or "Card" in content)
            has_verification = "verif" in content.lower()
            table_ok = has_table and has_verification
            checks.append(check(
                "validation_checklist_has_table",
                table_ok,
                f"Has table={has_table}, has verification steps={has_verification}"
            ))
            if table_ok:
                total_score += weights["validation_checklist_has_table"]
        else:
            checks.append(check("validation_checklist_has_table", False, "File missing"))
    except Exception as e:
        checks.append(check("validation_checklist_has_table", False, f"Exception: {e}"))

    # ── 8. Full report exists ─────────────────────────────────────────────────
    full_path = reports_dir / "full-report.md"
    full_exists = full_path.exists()
    checks.append(check(
        "full_report_exists",
        full_exists,
        f"reports/full-report.md {'found' if full_exists else 'NOT FOUND'}"
    ))
    if full_exists:
        total_score += weights["full_report_exists"]

    # ── 9. Full report verified section ──────────────────────────────────────
    try:
        if full_exists:
            content = full_path.read_text().lower()
            has_verified = "verified conclusion" in content or "## verified" in content
            checks.append(check(
                "full_report_verified_section",
                has_verified,
                f"Has verified conclusions section: {has_verified}"
            ))
            if has_verified:
                total_score += weights["full_report_verified_section"]
        else:
            checks.append(check("full_report_verified_section", False, "File missing"))
    except Exception as e:
        checks.append(check("full_report_verified_section", False, f"Exception: {e}"))

    # ── 10. Full report pending section ──────────────────────────────────────
    try:
        if full_exists:
            content = full_path.read_text().lower()
            has_pending = "pending" in content or "needs verification" in content or "待验证" in content
            checks.append(check(
                "full_report_pending_section",
                has_pending,
                f"Has pending/needs-verification section: {has_pending}"
            ))
            if has_pending:
                total_score += weights["full_report_pending_section"]
        else:
            checks.append(check("full_report_pending_section", False, "File missing"))
    except Exception as e:
        checks.append(check("full_report_pending_section", False, f"Exception: {e}"))

    # ── 11. Full report has short/medium/long-term strategy ──────────────────
    try:
        if full_exists:
            content = full_path.read_text().lower()
            has_short = "short" in content and ("term" in content or "month" in content)
            has_medium = "medium" in content and ("term" in content or "month" in content)
            has_long = "long" in content and ("term" in content or "month" in content)
            strategy_ok = has_short and has_medium and has_long
            checks.append(check(
                "full_report_strategy_sections",
                strategy_ok,
                f"Has short={has_short}, medium={has_medium}, long={has_long} term strategy"
            ))
            if strategy_ok:
                total_score += weights["full_report_strategy_sections"]
        else:
            checks.append(check("full_report_strategy_sections", False, "File missing"))
    except Exception as e:
        checks.append(check("full_report_strategy_sections", False, f"Exception: {e}"))

    # ── 12. Full report card index ────────────────────────────────────────────
    try:
        if full_exists:
            content = full_path.read_text()
            card_refs = re.findall(r'card-\d+', content, re.IGNORECASE)
            has_index = len(card_refs) >= 3  # Should reference at least 3 of 4 cards
            checks.append(check(
                "full_report_card_index",
                has_index,
                f"Found {len(card_refs)} card references (need >=3 for complete index)"
            ))
            if has_index:
                total_score += weights["full_report_card_index"]
        else:
            checks.append(check("full_report_card_index", False, "File missing"))
    except Exception as e:
        checks.append(check("full_report_card_index", False, f"Exception: {e}"))

    # ── 13. Sourcing validation passes ───────────────────────────────────────
    try:
        if full_exists:
            check_script = skill_dir / "scripts" / "check-sourcing.sh"
            result = subprocess.run(
                ["bash", str(check_script), str(full_path), str(sources_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            sourcing_ok = result.returncode == 0 and "PASSED" in result.stdout
            checks.append(check(
                "sourcing_validation_passes",
                sourcing_ok,
                f"check-sourcing.sh exit={result.returncode}, output: {result.stdout.strip()[-200:]}"
            ))
            if sourcing_ok:
                total_score += weights["sourcing_validation_passes"]
        else:
            checks.append(check("sourcing_validation_passes", False, "full-report.md missing"))
    except Exception as e:
        checks.append(check("sourcing_validation_passes", False, f"Exception: {e}"))

    passed = total_score >= 0.70  # Must score at least 70% to pass
    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))