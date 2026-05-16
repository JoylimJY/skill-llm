import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    # ── FIND THE EXECUTION LOG FILE ──────────────────────────────────────────
    # Agent should produce an execution log — accept any .md or .txt in workspace
    # that contains the execution signals. We search broadly.
    exec_log_content = ""
    exec_log_path = None

    # Priority: look for a dedicated execution log file (not memory file)
    candidate_names = [
        "execution_log.md", "execution_report.md", "run_log.md",
        "distribution_log.md", "ops_log.md", "execution_log.txt",
        "run_report.md", "incident_log.md", "distribution_report.md",
        "execution_report.txt",
    ]
    for name in candidate_names:
        found = list(workspace.rglob(name))
        if found:
            exec_log_path = found[0]
            exec_log_content = exec_log_path.read_text(encoding="utf-8")
            break

    # If not found by name, search all .md/.txt files for the start signal
    if not exec_log_path:
        for f in list(workspace.rglob("*.md")) + list(workspace.rglob("*.txt")):
            # Skip memory files and distractor files
            if "memory" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8")
                if "実行開始" in text or "🔄" in text:
                    exec_log_path = f
                    exec_log_content = text
                    break
            except Exception:
                pass

    # ── CHECK 1: Start signal present with correct Japanese format ───────────
    start_pattern = r"🔄\s*実行開始\s*:"
    start_found = bool(re.search(start_pattern, exec_log_content))
    checks.append({
        "name": "start_signal_format",
        "passed": start_found,
        "detail": (
            f"Found '🔄 実行開始:' start signal in {exec_log_path}"
            if start_found else
            f"Missing '🔄 実行開始:' start signal. File searched: {exec_log_path}. "
            "Must use exact Japanese format per execution discipline."
        )
    })

    # ── CHECK 2: Progress signal with fraction and pipe format ───────────────
    # Format: 🟡 進行中: <done>/<total> | <blocker or none>
    progress_pattern = r"🟡\s*進行中\s*:.*\d+\s*/\s*\d+.*\|"
    progress_found = bool(re.search(progress_pattern, exec_log_content))
    checks.append({
        "name": "progress_signal_format",
        "passed": progress_found,
        "detail": (
            f"Found '🟡 進行中: X/Y | ...' progress signal in {exec_log_path}"
            if progress_found else
            "Missing '🟡 進行中: <done>/<total> | <blocker>' progress signal. "
            "Must include fraction notation with pipe separator."
        )
    })

    # ── CHECK 3: Completion signal (partial success ⚠️ since only 5/8 shipped) ─
    # Should be ⚠️部分成功 or ⚠️ 部分成功 (partial success) NOT ✅完了
    # Accept either ⚠️ partial or ❌ failure since 5/8 is partial
    completion_pattern = r"(⚠️\s*部分成功|✅\s*完了|❌\s*失敗)"
    completion_match = re.search(completion_pattern, exec_log_content)
    completion_found = completion_match is not None
    # Extra credit: check it's the right one (partial success)
    correct_completion = completion_match and "部分成功" in completion_match.group(0) if completion_match else False
    checks.append({
        "name": "completion_signal_present",
        "passed": completion_found,
        "detail": (
            f"Found completion signal: '{completion_match.group(0) if completion_match else ''}'"
            if completion_found else
            "No completion signal found (⚠️部分成功 / ✅完了 / ❌失敗). "
            "Execution discipline requires one of these exact signals."
        )
    })
    checks.append({
        "name": "completion_signal_correct_type",
        "passed": correct_completion,
        "detail": (
            "Correctly used ⚠️部分成功 for a 5/8 partial publish outcome."
            if correct_completion else
            f"Expected ⚠️部分成功 for partial outcome (5/8 articles published), "
            f"but got: '{completion_match.group(0) if completion_match else 'nothing'}'. "
            "Kickoff-only failure with partial output demands partial-success signal."
        )
    })

    # ── CHECK 4: Evidence URLs in completion block ───────────────────────────
    url_pattern = r"https://clawhub\.io/posts/10[0-9]+"
    urls_found = re.findall(url_pattern, exec_log_content)
    unique_urls = set(urls_found)
    urls_ok = len(unique_urls) >= 3  # at least some evidence URLs attached
    checks.append({
        "name": "evidence_urls_attached",
        "passed": urls_ok,
        "detail": (
            f"Found {len(unique_urls)} evidence URL(s): {sorted(unique_urls)}"
            if urls_ok else
            f"Only {len(unique_urls)} evidence URL(s) found. "
            "Execution discipline: finish signal must include evidence pointers (URL/path)."
        )
    })

    # ── CHECK 5: KPI memory file exists for YESTERDAY ────────────────────────
    memory_file = workspace / "memory" / f"{yesterday_str}.md"
    memory_exists = memory_file.exists()
    memory_content = ""
    if memory_exists:
        try:
            memory_content = memory_file.read_text(encoding="utf-8")
        except Exception as e:
            memory_content = ""
    checks.append({
        "name": "kpi_memory_file_exists",
        "passed": memory_exists,
        "detail": (
            f"KPI memory file found: {memory_file}"
            if memory_exists else
            f"Missing KPI memory file at memory/{yesterday_str}.md. "
            "KPI logging add-on requires recording in memory/YYYY-MM-DD.md "
            "where YYYY-MM-DD is the date of the execution run."
        )
    })

    # ── CHECK 6: KPI memory file has required fields ─────────────────────────
    has_executed = bool(re.search(r"\bexecuted\b\s*:", memory_content, re.IGNORECASE))
    has_result   = bool(re.search(r"\bresult\b\s*:", memory_content, re.IGNORECASE))
    has_next     = bool(re.search(r"\bnext\b\s*:", memory_content, re.IGNORECASE))
    kpi_fields_ok = has_executed and has_result and has_next
    checks.append({
        "name": "kpi_fields_complete",
        "passed": kpi_fields_ok,
        "detail": (
            f"All KPI fields present (executed: {has_executed}, result: {has_result}, next: {has_next})"
            if kpi_fields_ok else
            f"Missing KPI fields in memory file. "
            f"executed={has_executed}, result={has_result}, next={has_next}. "
            "Required: 'executed', 'result', 'next' per KPI logging add-on."
        )
    })

    # ── CHECK 7: Postmortem — delay acknowledged ─────────────────────────────
    # Must appear in either the exec log OR the memory file
    combined_text = exec_log_content + "\n" + memory_content
    # Look for postmortem keywords: delay/miss acknowledged + rule update
    delay_ack = bool(re.search(
        r"(delay|miss|遅延|postmortem|post.mortem|kickoff.only|acknowledge)",
        combined_text, re.IGNORECASE
    ))
    checks.append({
        "name": "postmortem_delay_acknowledged",
        "passed": delay_ack,
        "detail": (
            "Postmortem delay/miss acknowledgment found in documentation."
            if delay_ack else
            "No acknowledgment of the delay or kickoff-only failure found. "
            "Postmortem rule: if a delay occurs, immediately acknowledge the miss."
        )
    })

    # ── CHECK 8: Postmortem — permanent rule update logged ───────────────────
    rule_update = bool(re.search(
        r"(permanent.rule|rule.update|BATCH_TIMEOUT|timeout.*30|fix.*timeout|config.*update|cron.*update|永続|ルール更新)",
        combined_text, re.IGNORECASE
    ))
    checks.append({
        "name": "postmortem_rule_update_logged",
        "passed": rule_update,
        "detail": (
            "Permanent rule/config update found (e.g., BATCH_TIMEOUT fix)."
            if rule_update else
            "No permanent rule update found. "
            "Postmortem rule: apply a permanent rule update and log in memory/YYYY-MM-DD.md."
        )
    })

    # ── CHECK 9: Memory file contains postmortem/change log ──────────────────
    postmortem_in_memory = bool(re.search(
        r"(postmortem|rule.update|permanent|fix|BATCH_TIMEOUT|delay|miss|kickoff)",
        memory_content, re.IGNORECASE
    ))
    checks.append({
        "name": "postmortem_logged_in_memory_file",
        "passed": postmortem_in_memory,
        "detail": (
            f"Postmortem/change logged in memory/{yesterday_str}.md."
            if postmortem_in_memory else
            f"Postmortem change not logged in memory/{yesterday_str}.md. "
            "Postmortem rule explicitly states: log the change in memory/YYYY-MM-DD.md."
        )
    })

    # ── CHECK 10: remaining items / next action in completion ────────────────
    remaining_pattern = r"(remaining|残り|article.*[678]|未完|next.action|次\s*:|再実行|relaunch|retry)"
    remaining_found = bool(re.search(remaining_pattern, exec_log_content, re.IGNORECASE))
    checks.append({
        "name": "remaining_items_documented",
        "passed": remaining_found,
        "detail": (
            "Remaining items / next action documented in execution log."
            if remaining_found else
            "Missing 'remaining items' and 'next action' in completion signal. "
            "Execution discipline: completion must include remaining items and next action."
        )
    })

    # ── SCORING ──────────────────────────────────────────────────────────────
    # Weights: core format checks are mandatory; KPI and postmortem are key discriminators
    weights = {
        "start_signal_format":            1.5,
        "progress_signal_format":         1.5,
        "completion_signal_present":      1.0,
        "completion_signal_correct_type": 1.0,
        "evidence_urls_attached":         1.0,
        "kpi_memory_file_exists":         1.5,
        "kpi_fields_complete":            1.5,
        "postmortem_delay_acknowledged":  1.0,
        "postmortem_rule_update_logged":  1.0,
        "postmortem_logged_in_memory_file": 1.5,
        "remaining_items_documented":     0.5,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)
    passed = score >= 0.70

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()