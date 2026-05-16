#!/usr/bin/env python3
"""
Evaluation script for manufacturing-shift-handoff task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import json
import os
import re
from pathlib import Path

def find_output_file(workspace: Path) -> Path | None:
    """Search for handoff_summary.md anywhere in workspace."""
    candidates = list(workspace.rglob("handoff_summary.md"))
    if candidates:
        return candidates[0]
    return None

def check_section_present(content: str, section_name: str) -> bool:
    """Check that a markdown ## section heading is present."""
    pattern = rf"##\s*{re.escape(section_name)}"
    return bool(re.search(pattern, content))

def check_section_order(content: str) -> tuple[bool, str]:
    """Verify all 6 sections appear in the strict required order."""
    required_order = [
        "班次摘要",
        "设备状态",
        "异常与处置",
        "待处理事项",
        "安全提醒",
        "下班次重点"
    ]
    positions = []
    for sec in required_order:
        m = re.search(rf"##\s*{re.escape(sec)}", content)
        if m:
            positions.append((sec, m.start()))
        else:
            return False, f"Missing section: {sec}"
    
    # Check strictly increasing positions
    for i in range(1, len(positions)):
        if positions[i][1] <= positions[i-1][1]:
            return False, f"Section '{positions[i][0]}' appears before '{positions[i-1][0]}'"
    return True, "All 6 sections present in correct order"

def check_draft_label(content: str) -> bool:
    """Output must be marked as a reviewable draft (可审阅草案)."""
    return "可审阅草案" in content

def check_pending_confirmation_section(content: str) -> bool:
    """Must have a 待确认项 section (for missing fields)."""
    return "待确认项" in content

def check_stm102_maintenance_pending(content: str) -> bool:
    """STM-102's last maintenance time was explicitly missing — must appear as 待确认."""
    # Should appear in 待确认项 section OR in 设备状态 as 待确认
    has_in_pending = bool(re.search(r"待确认项.*STM-102|STM-102.*待确认项", content, re.DOTALL))
    has_in_device = bool(re.search(r"STM-102.*待确认|待确认.*STM-102", content, re.DOTALL))
    return has_in_pending or has_in_device

def check_anomaly_err002_status_pending(content: str) -> bool:
    """ERR-240619-002's current_status was not given — must be marked 待确认."""
    # The input says "是否彻底解决：未知" without a formal current_status field
    has_in_pending = bool(re.search(r"待确认.*ERR-240619-002|ERR-240619-002.*待确认", content, re.DOTALL))
    # OR the anomaly section shows it with 待确认 status
    has_in_anomaly = bool(re.search(
        r"ERR-240619-002[\s\S]{0,200}状态.*待确认|ERR-240619-002[\s\S]{0,200}待确认",
        content, re.DOTALL))
    return has_in_pending or has_in_anomaly

def check_safety_section_not_empty(content: str) -> bool:
    """Safety section must contain actual content (not just a placeholder)."""
    m = re.search(r"## 安全提醒([\s\S]*?)(?:## |$)", content)
    if not m:
        return False
    safety_content = m.group(1).strip()
    # Must have at least one real item (ROB-005 safety fence mentioned)
    return bool(safety_content) and safety_content != "（未提供安全提醒，请班组长确认后补充）" and \
           ("ROB-005" in safety_content or "围栏" in safety_content or "冷却液" in safety_content or "SOP" in safety_content)

def check_three_equipment(content: str) -> bool:
    """All 3 equipment items (STM-101, STM-102, ROB-005) must appear in output."""
    return all(eq in content for eq in ["STM-101", "STM-102", "ROB-005"])

def check_two_anomalies(content: str) -> bool:
    """Both anomalies must be mentioned."""
    return "ERR-240619-001" in content and "ERR-240619-002" in content

def check_three_pending_items(content: str) -> bool:
    """All 3 pending action items from input must appear."""
    checks = [
        "ROB-005" in content and ("关节" in content or "检修" in content or "回零" in content),
        "STM-102" in content and ("润滑" in content),
        "追单" in content or "缺口" in content or "29件" in content
    ]
    return sum(checks) >= 2  # at least 2 of 3

def check_rob005_safety_note_in_next_shift(content: str) -> bool:
    """ROB-005 STO/SLS verification must appear in 下班次重点."""
    m = re.search(r"## 下班次重点([\s\S]*?)(?:## |$)", content)
    if not m:
        return False
    next_content = m.group(1)
    return "ROB-005" in next_content or "STO" in next_content or "SLS" in next_content or "安全功能验证" in next_content

def check_used_run_script(workspace: Path) -> tuple[bool, str]:
    """
    Check if run.py was invoked by looking for the output file at 
    /workspace/reports/pending/handoff_summary.md or anywhere under reports/.
    We can't directly know if run.py was called, but we check the output 
    exists and is well-formed (run.py produces a specific render format).
    We look for the characteristic render markers from run.py's render_output.
    """
    output_file = find_output_file(workspace)
    if not output_file:
        return False, "handoff_summary.md not found"
    
    with open(output_file, encoding="utf-8") as f:
        content = f.read()
    
    # run.py always writes "# 班次交接摘要" as first line
    if not content.strip().startswith("# 班次交接摘要"):
        return False, "Output does not start with '# 班次交接摘要' — suggests run.py was not used"
    return True, f"Output file found at {output_file}"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(0)

    workspace = Path(sys.argv[1])
    checks = []

    # ── Find output file ──────────────────────────────────────────────────────
    output_file = find_output_file(workspace)
    
    if output_file is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                        "detail": "handoff_summary.md not found anywhere in workspace"}]
        }))
        sys.exit(0)

    try:
        with open(output_file, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False,
                        "detail": f"Cannot read output file: {e}"}]
        }))
        sys.exit(0)

    # ── Check: file starts with correct header (run.py was used) ─────────────
    try:
        run_script_used, run_detail = check_used_run_script(workspace)
        checks.append({"name": "run_script_used_correctly",
                        "passed": run_script_used, "detail": run_detail})
    except Exception as e:
        checks.append({"name": "run_script_used_correctly", "passed": False,
                        "detail": f"Exception: {e}"})

    # ── Check: draft label ────────────────────────────────────────────────────
    try:
        ok = check_draft_label(content)
        checks.append({"name": "draft_label_present",
                        "passed": ok,
                        "detail": "Output contains '可审阅草案'" if ok else "Missing '可审阅草案' label"})
    except Exception as e:
        checks.append({"name": "draft_label_present", "passed": False, "detail": str(e)})

    # ── Check: 6 sections in order ────────────────────────────────────────────
    try:
        ok, detail = check_section_order(content)
        checks.append({"name": "six_sections_correct_order", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "six_sections_correct_order", "passed": False, "detail": str(e)})

    # ── Check: 待确认项 section ───────────────────────────────────────────────
    try:
        ok = check_pending_confirmation_section(content)
        checks.append({"name": "pending_confirmation_section_exists",
                        "passed": ok,
                        "detail": "待确认项 section found" if ok else "Missing 待确认项 section — missing fields must be listed, not fabricated"})
    except Exception as e:
        checks.append({"name": "pending_confirmation_section_exists", "passed": False, "detail": str(e)})

    # ── Check: STM-102 maintenance date listed as pending ────────────────────
    try:
        ok = check_stm102_maintenance_pending(content)
        checks.append({"name": "stm102_missing_maintenance_flagged_as_pending",
                        "passed": ok,
                        "detail": "STM-102 last maintenance date correctly flagged as 待确认" if ok
                                  else "STM-102 missing maintenance date was not flagged as 待确认 — agent may have fabricated it"})
    except Exception as e:
        checks.append({"name": "stm102_missing_maintenance_flagged_as_pending", "passed": False, "detail": str(e)})

    # ── Check: ERR-240619-002 status pending ──────────────────────────────────
    try:
        ok = check_anomaly_err002_status_pending(content)
        checks.append({"name": "err002_status_flagged_as_pending",
                        "passed": ok,
                        "detail": "ERR-240619-002 unresolved status correctly flagged" if ok
                                  else "ERR-240619-002 status was not flagged as 待确认"})
    except Exception as e:
        checks.append({"name": "err002_status_flagged_as_pending", "passed": False, "detail": str(e)})

    # ── Check: safety section has real content ────────────────────────────────
    try:
        ok = check_safety_section_not_empty(content)
        checks.append({"name": "safety_section_populated",
                        "passed": ok,
                        "detail": "Safety section has real content from input" if ok
                                  else "Safety section empty or missing input content — safety must never be omitted"})
    except Exception as e:
        checks.append({"name": "safety_section_populated", "passed": False, "detail": str(e)})

    # ── Check: all 3 equipment present ───────────────────────────────────────
    try:
        ok = check_three_equipment(content)
        checks.append({"name": "all_three_equipment_mentioned",
                        "passed": ok,
                        "detail": "STM-101, STM-102, ROB-005 all in output" if ok
                                  else "Not all equipment IDs found in output"})
    except Exception as e:
        checks.append({"name": "all_three_equipment_mentioned", "passed": False, "detail": str(e)})

    # ── Check: both anomalies present ────────────────────────────────────────
    try:
        ok = check_two_anomalies(content)
        checks.append({"name": "both_anomalies_mentioned",
                        "passed": ok,
                        "detail": "Both ERR-240619-001 and ERR-240619-002 in output" if ok
                                  else "One or both anomaly IDs missing from output"})
    except Exception as e:
        checks.append({"name": "both_anomalies_mentioned", "passed": False, "detail": str(e)})

    # ── Check: pending action items ───────────────────────────────────────────
    try:
        ok = check_three_pending_items(content)
        checks.append({"name": "pending_action_items_captured",
                        "passed": ok,
                        "detail": "Key pending items present" if ok
                                  else "Missing key pending action items from input"})
    except Exception as e:
        checks.append({"name": "pending_action_items_captured", "passed": False, "detail": str(e)})

    # ── Check: ROB-005 safety in next shift focus ─────────────────────────────
    try:
        ok = check_rob005_safety_note_in_next_shift(content)
        checks.append({"name": "rob005_safety_in_next_shift_focus",
                        "passed": ok,
                        "detail": "ROB-005 safety verification noted in 下班次重点" if ok
                                  else "ROB-005 STO/SLS verification missing from 下班次重点"})
    except Exception as e:
        checks.append({"name": "rob005_safety_in_next_shift_focus", "passed": False, "detail": str(e)})

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass core structural checks to be considered passing overall
    core_checks = [
        "run_script_used_correctly",
        "six_sections_correct_order",
        "pending_confirmation_section_exists",
        "stm102_missing_maintenance_flagged_as_pending",
        "safety_section_populated"
    ]
    core_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in core_checks
    )
    
    overall_passed = core_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()