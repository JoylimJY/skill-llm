import sys
import json
import re
import os
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    weights = {}

    # ================================================================
    # CHECK 1: Daily log for 2026-07-15 exists with correct format
    # ================================================================
    daily_log_path = workspace / "memory" / "2026-07-15.md"
    try:
        daily_content = daily_log_path.read_text()
        # Must start with # 2026-07-15
        has_header = daily_content.strip().startswith("# 2026-07-15")
        checks.append(check(
            "daily_log_exists_with_header",
            has_header,
            f"Daily log {'has' if has_header else 'MISSING'} correct '# 2026-07-15' header. Content preview: {daily_content[:200]}"
        ))
    except Exception as e:
        checks.append(check("daily_log_exists_with_header", False, f"File missing or unreadable: {e}"))
        daily_content = ""

    # CHECK 2: Daily log uses correct HH:MM -- Event Title format (not bullet points or other formats)
    try:
        # The proprietary format: ## HH:MM -- Title (24-hour, no AM/PM)
        entries = re.findall(r'^## \d{2}:\d{2} -- .+', daily_content, re.MULTILINE)
        has_correct_format = len(entries) >= 3  # At least 3 of the 4 inbox events should appear
        checks.append(check(
            "daily_log_correct_format",
            has_correct_format,
            f"Found {len(entries)} correctly formatted entries (## HH:MM -- Title). Need >= 3. Entries found: {entries}"
        ))
    except Exception as e:
        checks.append(check("daily_log_correct_format", False, f"Error checking format: {e}"))

    # CHECK 3: Daily log contains reference to TSLA breakout (momentum signal)
    try:
        has_tsla = "TSLA" in daily_content or "tsla" in daily_content.lower()
        checks.append(check(
            "daily_log_contains_tsla_signal",
            has_tsla,
            f"Daily log {'contains' if has_tsla else 'MISSING'} TSLA breakout signal entry."
        ))
    except Exception as e:
        checks.append(check("daily_log_contains_tsla_signal", False, f"Error: {e}"))

    # CHECK 4: Daily log contains AAPL mean reversion failure / loss entry
    try:
        has_aapl = "AAPL" in daily_content or "mean reversion" in daily_content.lower() or "mean-reversion" in daily_content.lower()
        checks.append(check(
            "daily_log_contains_aapl_failure",
            has_aapl,
            f"Daily log {'contains' if has_aapl else 'MISSING'} AAPL mean-reversion failure entry."
        ))
    except Exception as e:
        checks.append(check("daily_log_contains_aapl_failure", False, f"Error: {e}"))

    # CHECK 5: Daily log mentions platform poster / anti-duplicate or scan cycle
    try:
        has_platform_or_scan = (
            "duplicate" in daily_content.lower() or
            "platform" in daily_content.lower() or
            "scan cycle" in daily_content.lower() or
            "scanner" in daily_content.lower()
        )
        checks.append(check(
            "daily_log_contains_platform_or_scan",
            has_platform_or_scan,
            f"Daily log {'contains' if has_platform_or_scan else 'MISSING'} platform/scanner entries."
        ))
    except Exception as e:
        checks.append(check("daily_log_contains_platform_or_scan", False, f"Error: {e}"))

    # ================================================================
    # CHECK 6: MEMORY.md has been updated with significant item
    # The AAPL mean-reversion-fails-near-earnings is the critical lesson
    # (Third time it caused a loss -- classic "promote to long-term" trigger)
    # ================================================================
    memory_path = workspace / "MEMORY.md"
    try:
        memory_content = memory_path.read_text()
        # Must still have original identity/structure
        has_identity = "Identity" in memory_content or "autonomous" in memory_content
        # Must have the AAPL/earnings/mean-reversion lesson added
        has_new_lesson = (
            ("mean reversion" in memory_content.lower() or "mean-reversion" in memory_content.lower()) and
            ("earnings" in memory_content.lower())
        )
        checks.append(check(
            "memory_md_still_has_identity",
            has_identity,
            f"MEMORY.md {'preserved' if has_identity else 'LOST'} identity section."
        ))
        checks.append(check(
            "memory_md_has_new_lesson",
            has_new_lesson,
            f"MEMORY.md {'contains' if has_new_lesson else 'MISSING'} the mean-reversion-near-earnings lesson. Preview: {memory_content[-500:]}"
        ))
    except Exception as e:
        checks.append(check("memory_md_still_has_identity", False, f"MEMORY.md unreadable: {e}"))
        checks.append(check("memory_md_has_new_lesson", False, f"MEMORY.md unreadable: {e}"))
        memory_content = ""

    # CHECK 7: MEMORY.md lesson is distilled wisdom, not a raw copy-paste dump
    try:
        # The memory should NOT just be a verbatim copy of the inbox entry header line
        raw_inbox_header = "## [2026-07-15 03:47] Market Scanner -- Mean Reversion Failure on AAPL"
        is_raw_dump = raw_inbox_header in memory_content
        checks.append(check(
            "memory_md_is_distilled_not_raw_dump",
            not is_raw_dump,
            f"MEMORY.md {'is properly distilled' if not is_raw_dump else 'appears to be a raw inbox dump (verbatim cron-inbox header found in MEMORY.md)'}."
        ))
    except Exception as e:
        checks.append(check("memory_md_is_distilled_not_raw_dump", False, f"Error: {e}"))

    # ================================================================
    # CHECK 8: strategy-notes.md updated with mean-reversion-near-earnings lesson
    # Must include the date (2026-07-15) and the lesson
    # ================================================================
    strategy_path = workspace / "memory" / "strategy-notes.md"
    try:
        strategy_content = strategy_path.read_text()
        # Must still have original content
        has_original = "20-day MA" in strategy_content or "momentum" in strategy_content.lower()
        # Must have new lesson about mean reversion near earnings
        has_earnings_lesson = (
            ("mean reversion" in strategy_content.lower() or "mean-reversion" in strategy_content.lower()) and
            ("earnings" in strategy_content.lower())
        )
        # Must include a date stamp (2026-07-15 or learned YYYY-MM-DD pattern)
        has_date = "2026-07-15" in strategy_content
        checks.append(check(
            "strategy_notes_preserves_original",
            has_original,
            f"strategy-notes.md {'preserved' if has_original else 'LOST'} original content."
        ))
        checks.append(check(
            "strategy_notes_has_earnings_lesson",
            has_earnings_lesson,
            f"strategy-notes.md {'contains' if has_earnings_lesson else 'MISSING'} mean-reversion-near-earnings lesson. Preview: {strategy_content[-400:]}"
        ))
        checks.append(check(
            "strategy_notes_has_date",
            has_date,
            f"strategy-notes.md {'contains' if has_date else 'MISSING'} the date 2026-07-15 for the new lesson."
        ))
    except Exception as e:
        checks.append(check("strategy_notes_preserves_original", False, f"strategy-notes.md unreadable: {e}"))
        checks.append(check("strategy_notes_has_earnings_lesson", False, f"strategy-notes.md unreadable: {e}"))
        checks.append(check("strategy_notes_has_date", False, f"strategy-notes.md unreadable: {e}"))

    # ================================================================
    # CHECK 9: heartbeat-state.json updated (market_scanner timestamp is newer)
    # Original: market_scanner = 1752501600 (2026-07-14 14:00 UTC)
    # Must now be > 1752501600 (any timestamp from 2026-07-15 works)
    # 2026-07-15 00:00 UTC = 1752537600
    # ================================================================
    hb_path = workspace / "memory" / "heartbeat-state.json"
    try:
        hb_data = json.loads(hb_path.read_text())
        last_checks = hb_data.get("lastChecks", {})
        market_scanner_ts = last_checks.get("market_scanner")
        # Must be a number (unix timestamp, not a string date)
        is_numeric = isinstance(market_scanner_ts, (int, float))
        # Must be newer than the stale value 1752501600 (2026-07-14 14:00 UTC)
        is_updated = is_numeric and market_scanner_ts > 1752501600
        # Sanity: should not be an absurdly future date (> year 2030)
        is_sane = is_numeric and market_scanner_ts < 1893456000  # 2030-01-01
        checks.append(check(
            "heartbeat_market_scanner_is_numeric_timestamp",
            is_numeric,
            f"market_scanner value is {'a numeric Unix timestamp' if is_numeric else f'NOT numeric: {market_scanner_ts}'}."
        ))
        checks.append(check(
            "heartbeat_market_scanner_updated",
            is_updated and is_sane,
            f"market_scanner timestamp: {market_scanner_ts}. Expected > 1752501600 (2026-07-14 14:00 UTC). Updated: {is_updated}, Sane: {is_sane}."
        ))
        # Also check structure is intact
        has_structure = "lastChecks" in hb_data and isinstance(last_checks, dict)
        checks.append(check(
            "heartbeat_structure_preserved",
            has_structure,
            f"heartbeat-state.json {'has' if has_structure else 'MISSING'} correct {{lastChecks: {{...}}}} structure."
        ))
    except Exception as e:
        checks.append(check("heartbeat_market_scanner_is_numeric_timestamp", False, f"heartbeat-state.json error: {e}"))
        checks.append(check("heartbeat_market_scanner_updated", False, f"heartbeat-state.json error: {e}"))
        checks.append(check("heartbeat_structure_preserved", False, f"heartbeat-state.json error: {e}"))

    # ================================================================
    # CHECK 10: cron-inbox.md CLEARED (only header remains, no entries)
    # The proprietary rule: keep the header "# Cron Inbox", remove all entries
    # ================================================================
    inbox_path = workspace / "memory" / "cron-inbox.md"
    try:
        inbox_content = inbox_path.read_text()
        # Must still have the header
        has_header = inbox_content.strip().startswith("# Cron Inbox")
        # Must NOT have the original entries (check for a distinctive token)
        entries_cleared = "[2026-07-15" not in inbox_content
        # Must NOT be completely empty (header should remain)
        not_deleted = len(inbox_content.strip()) > 0
        checks.append(check(
            "inbox_header_preserved",
            has_header,
            f"cron-inbox.md {'has' if has_header else 'MISSING'} '# Cron Inbox' header. Content: {inbox_content[:200]}"
        ))
        checks.append(check(
            "inbox_entries_cleared",
            entries_cleared,
            f"cron-inbox.md entries {'cleared' if entries_cleared else 'NOT CLEARED -- original [2026-07-15 ...] entries still present'}."
        ))
        checks.append(check(
            "inbox_file_not_deleted",
            not_deleted,
            f"cron-inbox.md {'exists and non-empty' if not_deleted else 'was completely deleted or emptied'}."
        ))
    except Exception as e:
        checks.append(check("inbox_header_preserved", False, f"cron-inbox.md error: {e}"))
        checks.append(check("inbox_entries_cleared", False, f"cron-inbox.md error: {e}"))
        checks.append(check("inbox_file_not_deleted", False, f"cron-inbox.md error: {e}"))

    # ================================================================
    # CHECK 11: yesterday's daily log NOT modified (read-only in sub-agent pattern)
    # ================================================================
    yesterday_path = workspace / "memory" / "2026-07-14.md"
    try:
        yesterday_content = yesterday_path.read_text()
        # Original had exactly 3 entries, ending with "## 16:45 -- Strategy Tweak"
        original_last = "## 16:45 -- Strategy Tweak" in yesterday_content
        original_header = "# 2026-07-14" in yesterday_content
        checks.append(check(
            "yesterday_log_not_modified",
            original_last and original_header,
            f"Yesterday's log {'intact' if (original_last and original_header) else 'WAS MODIFIED unexpectedly'}."
        ))
    except Exception as e:
        checks.append(check("yesterday_log_not_modified", False, f"Error reading yesterday log: {e}"))

    # ================================================================
    # SCORE CALCULATION
    # ================================================================
    # Define weights for each check
    check_weights = {
        "daily_log_exists_with_header": 1.0,
        "daily_log_correct_format": 1.5,       # Proprietary format trap
        "daily_log_contains_tsla_signal": 0.75,
        "daily_log_contains_aapl_failure": 0.75,
        "daily_log_contains_platform_or_scan": 0.5,
        "memory_md_still_has_identity": 0.75,
        "memory_md_has_new_lesson": 1.5,        # Core distillation requirement
        "memory_md_is_distilled_not_raw_dump": 1.0,  # Proprietary trap
        "strategy_notes_preserves_original": 0.5,
        "strategy_notes_has_earnings_lesson": 1.5,   # Strategy update requirement
        "strategy_notes_has_date": 1.0,              # Proprietary trap (must date learnings)
        "heartbeat_market_scanner_is_numeric_timestamp": 1.0,  # Unix timestamp trap
        "heartbeat_market_scanner_updated": 1.0,
        "heartbeat_structure_preserved": 0.5,
        "inbox_header_preserved": 1.5,          # Proprietary trap (keep header!)
        "inbox_entries_cleared": 1.5,           # Core inbox clearing rule
        "inbox_file_not_deleted": 0.5,
        "yesterday_log_not_modified": 0.5,
    }

    total_weight = sum(check_weights.values())
    earned_weight = sum(
        check_weights.get(c["name"], 0)
        for c in checks
        if c["passed"]
    )
    score = round(earned_weight / total_weight, 4)

    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))