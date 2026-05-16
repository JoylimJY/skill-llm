#!/usr/bin/env python3
"""
Evaluation script for the openclaw-auto-dream-lite sandbox.
Usage: python eval.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

def evaluate(workspace_str: str) -> dict:
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ── Fixed dates (matching gen_inputs_script seed) ────────────────────────
    today = date(2024, 3, 15)
    log1_date = today - timedelta(days=3)  # 2024-03-12 — should be consolidated
    log2_date = today - timedelta(days=2)  # 2024-03-13 — should be consolidated
    log3_date = today - timedelta(days=5)  # 2024-03-10 — ALREADY consolidated
    log4_date = today - timedelta(days=1)  # 2024-03-14 — should be consolidated

    # ════════════════════════════════════════════════════════════════
    # CHECK 1: MEMORY.md exists at workspace root
    # ════════════════════════════════════════════════════════════════
    memory_path = workspace / "MEMORY.md"
    try:
        memory_exists = memory_path.exists()
        add_check(
            "MEMORY.md exists at workspace root",
            memory_exists,
            f"MEMORY.md {'found' if memory_exists else 'NOT found'} at {memory_path}",
            weight=1.5
        )
    except Exception as e:
        add_check("MEMORY.md exists at workspace root", False, f"Exception: {e}", weight=1.5)

    # ════════════════════════════════════════════════════════════════
    # CHECK 2: MEMORY.md was created from the template (has PERMANENT section intact)
    # ════════════════════════════════════════════════════════════════
    try:
        memory_content = memory_path.read_text() if memory_path.exists() else ""
        has_permanent_marker = "⚠️ PERMANENT" in memory_content
        has_agent_name = "OpenClaw Dev Assistant" in memory_content
        template_respected = has_permanent_marker and has_agent_name
        add_check(
            "MEMORY.md initialized from memory-template.md",
            template_respected,
            f"⚠️ PERMANENT marker present: {has_permanent_marker}; "
            f"'OpenClaw Dev Assistant' preserved: {has_agent_name}",
            weight=1.5
        )
    except Exception as e:
        add_check("MEMORY.md initialized from memory-template.md", False, f"Exception: {e}", weight=1.5)

    # ════════════════════════════════════════════════════════════════
    # CHECK 3: Backup file MEMORY.md.pre-dream exists (exact name — proprietary trap)
    # ════════════════════════════════════════════════════════════════
    try:
        pre_dream_path = workspace / "MEMORY.md.pre-dream"
        backup_exists = pre_dream_path.exists()
        add_check(
            "MEMORY.md.pre-dream backup created (exact filename)",
            backup_exists,
            f"Backup file 'MEMORY.md.pre-dream' {'found' if backup_exists else 'NOT found'}. "
            f"Note: must be exactly '.pre-dream' suffix, not '.bak' or '.backup'.",
            weight=2.0
        )
    except Exception as e:
        add_check("MEMORY.md.pre-dream backup created (exact filename)", False, f"Exception: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════
    # CHECK 4: The 3 unconsolidated logs now have <!-- consolidated --> marker
    # ════════════════════════════════════════════════════════════════
    newly_consolidated = []
    consolidation_failures = []

    for log_date in [log1_date, log2_date, log4_date]:
        log_path = workspace / f"memory/{log_date}.md"
        try:
            content = log_path.read_text()
            if "<!-- consolidated -->" in content:
                newly_consolidated.append(str(log_date))
            else:
                consolidation_failures.append(str(log_date))
        except Exception as e:
            consolidation_failures.append(f"{log_date} (error: {e})")

    all_marked = len(newly_consolidated) == 3 and len(consolidation_failures) == 0
    add_check(
        "All 3 unconsolidated logs marked <!-- consolidated -->",
        all_marked,
        f"Marked: {newly_consolidated}; Missing: {consolidation_failures}",
        weight=2.0
    )

    # ════════════════════════════════════════════════════════════════
    # CHECK 5: Already-consolidated log was NOT double-processed (idempotency)
    # ════════════════════════════════════════════════════════════════
    try:
        already_done_path = workspace / f"memory/{log3_date}.md"
        content = already_done_path.read_text()
        # Count occurrences — should be exactly 1 (the original one)
        count = content.count("<!-- consolidated -->")
        not_doubled = count == 1
        add_check(
            "Pre-consolidated log not double-processed (idempotency)",
            not_doubled,
            f"Log {log3_date} has {count} '<!-- consolidated -->' marker(s); expected exactly 1.",
            weight=1.5
        )
    except Exception as e:
        add_check("Pre-consolidated log not double-processed (idempotency)", False, f"Exception: {e}", weight=1.5)

    # ════════════════════════════════════════════════════════════════
    # CHECK 6: ⚠️ PERMANENT section in MEMORY.md was NOT modified
    # ════════════════════════════════════════════════════════════════
    try:
        memory_content = memory_path.read_text() if memory_path.exists() else ""
        # Check that all original PERMANENT content is still present verbatim
        permanent_lines = [
            "Agent name: OpenClaw Dev Assistant",
            "Owner: workspace user",
            "Primary language: Python",
            "Coding style: PEP 8 strictly enforced",
            "This section must NEVER be modified or deleted by any automated process.",
        ]
        missing_permanent = [line for line in permanent_lines if line not in memory_content]
        permanent_intact = len(missing_permanent) == 0
        add_check(
            "⚠️ PERMANENT section content untouched in MEMORY.md",
            permanent_intact,
            f"Missing permanent lines: {missing_permanent if missing_permanent else 'None — all intact'}",
            weight=2.0
        )
    except Exception as e:
        add_check("⚠️ PERMANENT section content untouched in MEMORY.md", False, f"Exception: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════
    # CHECK 7: MEMORY.md has been enriched with content from daily logs
    # ════════════════════════════════════════════════════════════════
    try:
        memory_content = memory_path.read_text() if memory_path.exists() else ""
        # Look for substantive content from the logs — at least one clear technical detail
        enrichment_signals = [
            "Redis", "cache", "JWT", "PostgreSQL", "async",
            "nginx", "rate limit", "OpenAPI", "idempotency", "payment",
            "Jordan", "Sam", "Alex",  # People from logs
        ]
        found_signals = [s for s in enrichment_signals if s.lower() in memory_content.lower()]
        enriched = len(found_signals) >= 3  # At least 3 pieces of info from logs
        add_check(
            "MEMORY.md enriched with content from daily logs",
            enriched,
            f"Found {len(found_signals)}/3 required signals from logs: {found_signals[:5]}",
            weight=2.0
        )
    except Exception as e:
        add_check("MEMORY.md enriched with content from daily logs", False, f"Exception: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════
    # CHECK 8: dream-report.md exists in memory/ with exactly 3 lines
    # ════════════════════════════════════════════════════════════════
    try:
        report_path = workspace / "memory/dream-report.md"
        report_exists = report_path.exists()

        if report_exists:
            report_content = report_path.read_text().strip()
            report_lines = [l for l in report_content.splitlines() if l.strip()]
            exactly_three_lines = len(report_lines) == 3
            add_check(
                "memory/dream-report.md exists with exactly 3 lines",
                exactly_three_lines,
                f"Report found. Line count: {len(report_lines)} (expected 3). Lines: {report_lines}",
                weight=1.5
            )
        else:
            add_check(
                "memory/dream-report.md exists with exactly 3 lines",
                False,
                "dream-report.md not found in memory/ directory.",
                weight=1.5
            )
    except Exception as e:
        add_check("memory/dream-report.md exists with exactly 3 lines", False, f"Exception: {e}", weight=1.5)

    # ════════════════════════════════════════════════════════════════
    # CHECK 9: dream-report.md line 1 matches expected format
    # ════════════════════════════════════════════════════════════════
    try:
        report_path = workspace / "memory/dream-report.md"
        if report_path.exists():
            lines = [l for l in report_path.read_text().strip().splitlines() if l.strip()]
            if lines:
                line1 = lines[0]
                # Must start with "Dream cycle completed:" followed by an ISO date
                match = re.match(r"Dream cycle completed:\s+\d{4}-\d{2}-\d{2}", line1)
                format_ok = bool(match)
                add_check(
                    "dream-report.md line 1 format: 'Dream cycle completed: YYYY-MM-DD'",
                    format_ok,
                    f"Line 1: '{line1}'; regex match: {format_ok}",
                    weight=1.0
                )
            else:
                add_check("dream-report.md line 1 format", False, "Report is empty.", weight=1.0)
        else:
            add_check("dream-report.md line 1 format", False, "dream-report.md not found.", weight=1.0)
    except Exception as e:
        add_check("dream-report.md line 1 format", False, f"Exception: {e}", weight=1.0)

    # ════════════════════════════════════════════════════════════════
    # CHECK 10: dream-report.md line 2 shows correct consolidation count (3 logs)
    # ════════════════════════════════════════════════════════════════
    try:
        report_path = workspace / "memory/dream-report.md"
        if report_path.exists():
            lines = [l for l in report_path.read_text().strip().splitlines() if l.strip()]
            if len(lines) >= 2:
                line2 = lines[1]
                # Must say "Logs consolidated: 3"
                match = re.search(r"Logs consolidated:\s*3", line2)
                count_ok = bool(match)
                add_check(
                    "dream-report.md line 2: 'Logs consolidated: 3'",
                    count_ok,
                    f"Line 2: '{line2}'; expected count 3: {count_ok}",
                    weight=1.0
                )
            else:
                add_check("dream-report.md line 2", False, "Report has fewer than 2 lines.", weight=1.0)
        else:
            add_check("dream-report.md line 2", False, "dream-report.md not found.", weight=1.0)
    except Exception as e:
        add_check("dream-report.md line 2", False, f"Exception: {e}", weight=1.0)

    # ════════════════════════════════════════════════════════════════
    # CHECK 11: config/crons.yaml contains the auto-memory-dream cron job
    # ════════════════════════════════════════════════════════════════
    try:
        import yaml
        crons_path = workspace / "config/crons.yaml"
        crons_content = crons_path.read_text()
        # Check for required fields in the cron job
        has_name = "auto-memory-dream" in crons_content
        has_schedule = "0 4 * * *" in crons_content
        has_session_target = "isolated" in crons_content
        has_announce = "announce" in crons_content
        has_timeout = "600" in crons_content
        has_agent_turn = "agentTurn" in crons_content

        cron_complete = all([has_name, has_schedule, has_session_target, has_announce, has_timeout, has_agent_turn])
        missing = []
        if not has_name: missing.append("name:auto-memory-dream")
        if not has_schedule: missing.append("schedule:0 4 * * *")
        if not has_session_target: missing.append("sessionTarget:isolated")
        if not has_announce: missing.append("delivery.mode:announce")
        if not has_timeout: missing.append("timeoutSeconds:600")
        if not has_agent_turn: missing.append("kind:agentTurn")

        add_check(
            "config/crons.yaml has complete auto-memory-dream cron job",
            cron_complete,
            f"Present: {cron_complete}; Missing fields: {missing if missing else 'None'}",
            weight=2.0
        )
    except Exception as e:
        add_check("config/crons.yaml has complete auto-memory-dream cron job", False, f"Exception: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════
    # CHECK 12: Daily logs themselves were NOT deleted (safety rule)
    # ════════════════════════════════════════════════════════════════
    try:
        all_logs_present = all(
            (workspace / f"memory/{d}.md").exists()
            for d in [log1_date, log2_date, log3_date, log4_date]
        )
        add_check(
            "Daily log files preserved (never deleted)",
            all_logs_present,
            f"All 4 original log files still present: {all_logs_present}",
            weight=1.5
        )
    except Exception as e:
        add_check("Daily log files preserved (never deleted)", False, f"Exception: {e}", weight=1.5)

    # ─── Final scoring ────────────────────────────────────────────
    overall_passed = total_score >= (max_score * 0.75)  # 75% threshold to pass
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))