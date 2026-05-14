import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def main():
    workspace = sys.argv[1]
    checks = []

    # ── Locate the three required output files ──────────────────────────────
    task_start_path  = find_file(workspace, "task_start.txt")
    status_path      = find_file(workspace, "status_update.txt")
    task_close_path  = find_file(workspace, "task_close.txt")

    # ── File existence ───────────────────────────────────────────────────────
    checks.append(check(
        "task_start.txt exists",
        task_start_path is not None,
        str(task_start_path) if task_start_path else "File not found"
    ))
    checks.append(check(
        "status_update.txt exists",
        status_path is not None,
        str(status_path) if status_path else "File not found"
    ))
    checks.append(check(
        "task_close.txt exists",
        task_close_path is not None,
        str(task_close_path) if task_close_path else "File not found"
    ))

    # ── Read contents ────────────────────────────────────────────────────────
    ts  = read_file(task_start_path)  if task_start_path  else ""
    su  = read_file(status_path)      if status_path      else ""
    tc  = read_file(task_close_path)  if task_close_path  else ""

    ts  = ts  or ""
    su  = su  or ""
    tc  = tc  or ""

    # ════════════════════════════════════════════════════════════════════════
    # CHECKS FOR ALL THREE FILES: proprietary header/footer
    # ════════════════════════════════════════════════════════════════════════

    HEADER = "🤖 MISSION CONTROL"
    # The separator uses em-dashes: ——————————————
    SEPARATOR = "——————————————"
    FOOTER = "🌸 powered by miyabi"

    for label, content in [("task_start.txt", ts), ("status_update.txt", su), ("task_close.txt", tc)]:
        checks.append(check(
            f"{label} has correct header '🤖 MISSION CONTROL'",
            HEADER in content,
            f"Header found: {HEADER in content}"
        ))
        checks.append(check(
            f"{label} has correct em-dash separator",
            SEPARATOR in content,
            f"Separator (——————————————) found: {SEPARATOR in content}. "
            f"(Hyphens would be wrong; must be em-dashes U+2014)"
        ))
        checks.append(check(
            f"{label} has correct footer '🌸 powered by miyabi'",
            FOOTER in content,
            f"Footer found: {FOOTER in content}"
        ))
        # No code blocks allowed
        has_code_block = "```" in content
        checks.append(check(
            f"{label} has no code blocks (plain text only)",
            not has_code_block,
            "No ``` found" if not has_code_block else "FAIL: code block detected"
        ))

    # ════════════════════════════════════════════════════════════════════════
    # CHECKS FOR task_start.txt  (/task-start command)
    # ════════════════════════════════════════════════════════════════════════

    checks.append(check(
        "task_start.txt contains /task-start command",
        "/task-start" in ts,
        f"/task-start present: {'/task-start' in ts}"
    ))
    checks.append(check(
        "task_start.txt has 'Owner: SHUNSUKE AI' (fixed owner field)",
        "Owner: SHUNSUKE AI" in ts,
        f"'Owner: SHUNSUKE AI' found: {'Owner: SHUNSUKE AI' in ts}"
    ))
    checks.append(check(
        "task_start.txt references Issue #99",
        "#99" in ts,
        f"#99 found: {'#99' in ts}"
    ))
    checks.append(check(
        "task_start.txt contains Scope field",
        "Scope:" in ts,
        f"Scope: field found: {'Scope:' in ts}"
    ))
    checks.append(check(
        "task_start.txt contains Risk field",
        "Risk:" in ts,
        f"Risk: field found: {'Risk:' in ts}"
    ))
    checks.append(check(
        "task_start.txt contains Completion Criteria field",
        "Completion Criteria:" in ts,
        f"Completion Criteria: found: {'Completion Criteria:' in ts}"
    ))
    checks.append(check(
        "task_start.txt contains Goal field",
        "Goal:" in ts,
        f"Goal: field found: {'Goal:' in ts}"
    ))

    # ════════════════════════════════════════════════════════════════════════
    # CHECKS FOR status_update.txt (MISO mission board message)
    # ════════════════════════════════════════════════════════════════════════

    # Must have mission field
    checks.append(check(
        "status_update.txt contains 📋 mission line",
        "📋" in su,
        f"📋 found: {'📋' in su}"
    ))

    # Must have elapsed/agents/state line with ∣ (U+2223 divider) and 🧩
    has_timing_line = "🧩" in su and "∣" in su
    checks.append(check(
        "status_update.txt has timing line with 🧩 and ∣ (U+2223) dividers",
        has_timing_line,
        f"🧩 found: {'🧩' in su}, ∣ (U+2223) found: {'∣' in su}"
    ))

    # State emoji: must use 🔥 for RUNNING/PARTIAL or 👀 for AWAITING APPROVAL
    # The brief says status_update is at PARTIAL state → should have 🔥
    has_state_emoji = any(e in su for e in ["🔥", "👀", "🎉", "❌"])
    checks.append(check(
        "status_update.txt uses a valid state emoji (🔥/👀/🎉/❌)",
        has_state_emoji,
        f"State emoji found: {[e for e in ['🔥','👀','🎉','❌'] if e in su]}"
    ))

    # For PARTIAL state (mid-mission), must use 🔥
    checks.append(check(
        "status_update.txt uses 🔥 for PARTIAL state (not 👀 or 🎉)",
        "🔥" in su,
        f"🔥 found: {'🔥' in su} (PARTIAL state requires 🔥)"
    ))

    # Must have agent status lines with ↳ prefix
    has_agent_arrows = su.count("↳") >= 3
    checks.append(check(
        "status_update.txt has at least 3 agent lines with ↳ prefix",
        has_agent_arrows,
        f"↳ count: {su.count('↳')} (need ≥3)"
    ))

    # Must reference all three agents
    for agent in ["analyze", "execute", "review"]:
        checks.append(check(
            f"status_update.txt references agent '{agent}'",
            agent in su.lower(),
            f"'{agent}' found: {agent in su.lower()}"
        ))

    # Must have Issue, Owner, Goal, Next fields
    checks.append(check(
        "status_update.txt has 'Issue:' field",
        "Issue:" in su,
        f"Issue: found: {'Issue:' in su}"
    ))
    checks.append(check(
        "status_update.txt has 'Owner: SHUNSUKE AI' (fixed owner)",
        "Owner: SHUNSUKE AI" in su,
        f"Owner: SHUNSUKE AI found: {'Owner: SHUNSUKE AI' in su}"
    ))
    checks.append(check(
        "status_update.txt has 'Goal:' field",
        "Goal:" in su,
        f"Goal: found: {'Goal:' in su}"
    ))
    checks.append(check(
        "status_update.txt has 'Next:' field",
        "Next:" in su,
        f"Next: found: {'Next:' in su}"
    ))
    checks.append(check(
        "status_update.txt references Issue #99",
        "#99" in su,
        f"#99 found: {'#99' in su}"
    ))

    # ════════════════════════════════════════════════════════════════════════
    # CHECKS FOR task_close.txt (/task-close command)
    # ════════════════════════════════════════════════════════════════════════

    checks.append(check(
        "task_close.txt contains /task-close command",
        "/task-close" in tc,
        f"/task-close present: {'/task-close' in tc}"
    ))
    checks.append(check(
        "task_close.txt has 'Implemented:' field",
        "Implemented:" in tc,
        f"Implemented: found: {'Implemented:' in tc}"
    ))
    checks.append(check(
        "task_close.txt has 'Validation:' field",
        "Validation:" in tc,
        f"Validation: found: {'Validation:' in tc}"
    ))
    checks.append(check(
        "task_close.txt has 'Changes:' field",
        "Changes:" in tc,
        f"Changes: found: {'Changes:' in tc}"
    ))
    checks.append(check(
        "task_close.txt has 'Risks / next steps:' field",
        "Risks" in tc and "next steps" in tc,
        f"Risks/next steps found: {'Risks' in tc and 'next steps' in tc}"
    ))
    checks.append(check(
        "task_close.txt has 'Notify:' field",
        "Notify:" in tc,
        f"Notify: found: {'Notify:' in tc}"
    ))
    checks.append(check(
        "task_close.txt uses 🎉 emoji for COMPLETE state",
        "🎉" in tc,
        f"🎉 found: {'🎉' in tc}"
    ))
    checks.append(check(
        "task_close.txt references Issue #99",
        "#99" in tc,
        f"#99 found: {'#99' in tc}"
    ))

    # ════════════════════════════════════════════════════════════════════════
    # CROSS-FILE CONSISTENCY
    # ════════════════════════════════════════════════════════════════════════

    # All three files must reference #99
    all_ref_issue = "#99" in ts and "#99" in su and "#99" in tc
    checks.append(check(
        "All three files consistently reference Issue #99",
        all_ref_issue,
        f"ts:#99={'#99' in ts}, su:#99={'#99' in su}, tc:#99={'#99' in tc}"
    ))

    # All three files must have the same proprietary footer
    all_have_footer = (FOOTER in ts) and (FOOTER in su) and (FOOTER in tc)
    checks.append(check(
        "All three files share the same '🌸 powered by miyabi' footer",
        all_have_footer,
        f"ts:{FOOTER in ts}, su:{FOOTER in su}, tc:{FOOTER in tc}"
    ))

    # ════════════════════════════════════════════════════════════════════════
    # SCORING
    # ════════════════════════════════════════════════════════════════════════

    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = score >= 0.85

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()