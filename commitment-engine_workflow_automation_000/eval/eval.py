import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Load commitments.md ──────────────────────────────────────────────────
    ledger_path = workspace / "commitments.md"
    try:
        ledger_content = ledger_path.read_text(encoding="utf-8")
    except Exception as e:
        check("commitments_md_exists", False, f"Cannot read commitments.md: {e}")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    check("commitments_md_exists", True, "commitments.md found and readable")

    # ── Parse table rows ─────────────────────────────────────────────────────
    # Extract all non-header, non-separator rows
    table_rows = []
    for line in ledger_content.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Skip header row (contains 'ID' or '承诺内容') and separator rows
            if any(c.startswith("---") or c.startswith(":---") for c in cells):
                continue
            if cells and cells[0] in ("ID", "**ID**"):
                continue
            if len(cells) >= 8:
                table_rows.append(cells)

    # ── Check: Header row has required 9 columns ──────────────────────────────
    header_found = False
    required_headers = ["ID", "承诺内容", "类型", "触发时间", "状态", "创建时间"]
    for line in ledger_content.splitlines():
        if "承诺内容" in line and "类型" in line and "状态" in line:
            header_found = True
            # Check for all required columns
            missing = [h for h in required_headers if h not in line]
            check("header_9_columns", len(missing) == 0,
                  f"Header found. Missing columns: {missing}" if missing else "All required columns present in header")
            break
    if not header_found:
        check("header_9_columns", False, "No valid table header found with required columns")

    # ── Check: Exactly 5 commitment entries ──────────────────────────────────
    n_rows = len(table_rows)
    check("five_commitments_recorded", n_rows == 5,
          f"Found {n_rows} data rows; expected 5")

    # ── Check: All entries have status=active ─────────────────────────────────
    if table_rows:
        status_col_index = 4  # 0-based: ID, 承诺内容, 类型, 触发时间, 状态
        all_active = all(
            len(row) > status_col_index and "active" in row[status_col_index].lower()
            for row in table_rows
        )
        non_active = [row[status_col_index] for row in table_rows
                      if len(row) > status_col_index and "active" not in row[status_col_index].lower()]
        check("all_status_active", all_active,
              f"All statuses are 'active'" if all_active else f"Non-active statuses found: {non_active}")
    else:
        check("all_status_active", False, "No rows to check status")

    # ── Check: Request 1 is typed as 'recurring' ──────────────────────────────
    recurring_rows = [r for r in table_rows
                      if len(r) > 2 and "recurring" in r[2].lower()]
    check("request1_is_recurring", len(recurring_rows) >= 1,
          f"Found {len(recurring_rows)} recurring row(s); expected at least 1 (the daily report)")

    # ── Check: Request 1 has correct cron time 17:50 (17:50, weekdays Mon-Fri) ─
    if recurring_rows:
        r1 = recurring_rows[0]
        trigger_field = r1[3] if len(r1) > 3 else ""
        has_1750 = "17:50" in trigger_field or "17:50" in ledger_content
        check("request1_trigger_time_1750", has_1750,
              f"Trigger time field contains '17:50': {trigger_field}")
    else:
        check("request1_trigger_time_1750", False, "No recurring row found to check trigger time")

    # ── Check: One-time commitments (requests 2-5) ───────────────────────────
    onetime_rows = [r for r in table_rows
                    if len(r) > 2 and "one-time" in r[2].lower().replace("_", "-").replace(" ", "-")]
    check("onetime_commitments_count", len(onetime_rows) >= 4,
          f"Found {len(onetime_rows)} one-time rows; expected 4 (requests 2-5)")

    # ── Check: Request 2 - "记得做X" → deadline=当天21:00 ────────────────────
    # Request 2 is "帮我记得今天做一下对手方敞口复核" → no explicit time → 21:00
    # Look for a row mentioning 敞口 or 复核 with 21:00
    req2_rows = [r for r in table_rows
                 if len(r) > 3 and ("敞口" in " ".join(r) or "复核" in " ".join(r) or "counterpart" in " ".join(r).lower())]
    if req2_rows:
        r2 = req2_rows[0]
        trigger = r2[3] if len(r2) > 3 else ""
        has_21 = "21:00" in trigger or "21:00" in " ".join(r2)
        check("request2_deadline_2100", has_21,
              f"Request2 trigger field: '{trigger}' - contains 21:00: {has_21}")
    else:
        # Try broader search in full content
        has_21_in_context = bool(re.search(r"敞口.*21:00|21:00.*敞口|复核.*21:00|21:00.*复核", ledger_content))
        check("request2_deadline_2100", has_21_in_context,
              f"Could not isolate request2 row. Broad search for '敞口/复核 + 21:00': {has_21_in_context}")

    # ── Check: Request 4 - "记得联系路透社" → also 21:00 (no explicit time) ──
    req4_rows = [r for r in table_rows
                 if len(r) > 3 and ("路透" in " ".join(r) or "reuters" in " ".join(r).lower() or "feed" in " ".join(r).lower())]
    if req4_rows:
        r4 = req4_rows[0]
        trigger = r4[3] if len(r4) > 3 else ""
        has_21 = "21:00" in trigger or "21:00" in " ".join(r4)
        check("request4_deadline_2100", has_21,
              f"Request4 (路透社) trigger field: '{trigger}' - contains 21:00: {has_21}")
    else:
        has_21_in_context = bool(re.search(r"路透.*21:00|21:00.*路透|reuters.*21:00|21:00.*reuters", ledger_content, re.IGNORECASE))
        check("request4_deadline_2100", has_21_in_context,
              f"Could not isolate request4. Broad search: {has_21_in_context}")

    # ── Check: Request 3 - explicit "14:00" deadline ─────────────────────────
    req3_rows = [r for r in table_rows
                 if len(r) > 3 and ("PnL" in " ".join(r) or "pnl" in " ".join(r).lower() 
                                    or "结算" in " ".join(r) or "合规" in " ".join(r))]
    if req3_rows:
        r3 = req3_rows[0]
        trigger = r3[3] if len(r3) > 3 else ""
        has_14 = "14:00" in trigger or "14:00" in " ".join(r3)
        check("request3_deadline_1400", has_14,
              f"Request3 (PnL/合规) trigger field: '{trigger}' - contains 14:00: {has_14}")
    else:
        has_14_in_context = bool(re.search(r"(PnL|结算|合规).*14:00|14:00.*(PnL|结算|合规)", ledger_content))
        check("request3_deadline_1400", has_14_in_context,
              f"Broad search for PnL/合规 + 14:00: {has_14_in_context}")

    # ── Check: Request 5 - "稍后给你" → deadline = now + 1 hour ─────────────
    # Reference time: 2025-07-16 09:30:00. So deadline should be ~10:30
    req5_rows = [r for r in table_rows
                 if len(r) > 3 and ("未结算" in " ".join(r) or "汇总" in " ".join(r) 
                                    or "会议" in " ".join(r) or "开会" in " ".join(r))]
    if req5_rows:
        r5 = req5_rows[0]
        trigger = r5[3] if len(r5) > 3 else ""
        # Should be approximately 10:30 (09:30 + 1 hour)
        has_1030 = bool(re.search(r"10:[23][0-9]", trigger) or re.search(r"10:[23][0-9]", " ".join(r5)))
        check("request5_deadline_plus1hr", has_1030,
              f"Request5 (未结算/汇总) trigger field: '{trigger}' - ~10:30 (09:30+1hr): {has_1030}")
    else:
        # Broad search for 10:3x anywhere in file
        has_1030_in_content = bool(re.search(r"10:[23][0-9]", ledger_content))
        check("request5_deadline_plus1hr", has_1030_in_content,
              f"Could not isolate request5. Broad search for ~10:30: {has_1030_in_content}")

    # ── Check: openclaw cron add was invoked for recurring commitment ─────────
    openclaw_log = workspace / "logs" / "openclaw_invocations.log"
    try:
        claw_content = openclaw_log.read_text(encoding="utf-8")
        has_cron_add = "cron" in claw_content and "add" in claw_content
        has_1750_cron = "50 17" in claw_content or "17:50" in claw_content
        has_name_flag = "--name" in claw_content
        has_cron_flag = "--cron" in claw_content
        has_message_flag = "--message" in claw_content

        check("openclaw_cron_invoked", has_cron_add,
              f"openclaw cron add invoked: {has_cron_add}. Log excerpt: {claw_content[:300]}")
        check("openclaw_cron_time_1750", has_1750_cron,
              f"Cron expression contains 17:50 (50 17): {has_1750_cron}")
        check("openclaw_cron_flags_correct", has_name_flag and has_cron_flag and has_message_flag,
              f"--name: {has_name_flag}, --cron: {has_cron_flag}, --message: {has_message_flag}")
        # Check weekday constraint (1-5)
        has_weekday = "1-5" in claw_content
        check("openclaw_cron_weekday_constraint", has_weekday,
              f"Cron expression includes weekday '1-5': {has_weekday}")
    except Exception as e:
        check("openclaw_cron_invoked", False, f"Cannot read openclaw log: {e}")
        check("openclaw_cron_time_1750", False, "openclaw log not available")
        check("openclaw_cron_flags_correct", False, "openclaw log not available")
        check("openclaw_cron_weekday_constraint", False, "openclaw log not available")

    # ── Check: IDs follow a pattern (C001, C002 etc.) ────────────────────────
    id_col = [r[0] for r in table_rows if r]
    id_pattern = re.compile(r"C\d{3}|c\d{3}|\d{3}")
    has_id_pattern = all(id_pattern.search(i) for i in id_col if i.strip())
    check("commitment_ids_formatted", has_id_pattern and len(id_col) >= 5,
          f"IDs found: {id_col}. Pattern match: {has_id_pattern}")

    # ── Compute final score ───────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))