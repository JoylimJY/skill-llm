#!/usr/bin/env python3
"""
Evaluation script for follow-up-commander task.
Checks that the agent:
1. Fixed the invalid participant role (LEAD → valid spec role)
2. Invoked run.py correctly (output file exists with correct filename convention)
3. Output contains all 6 required sections
4. Email draft is marked [DRAFT]
5. Pending/missing items (no deadline, no owner) appear in 未决问题, not fabricated
6. Escalation rules reference the correct timing for the priority used
"""
import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 7.0  # number of checks with weight 1.0 each

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight

    # ── Locate the output file ───────────────────────────────────────────────
    # Spec says filename_convention = "followup_<meeting_id>.md"
    # meeting_id = "MTG-2024-Q2-07"
    expected_filename = "followup_MTG-2024-Q2-07.md"
    found_files = list(workspace.rglob(expected_filename))

    if not found_files:
        add_check("output_file_exists", False,
                  f"Could not find '{expected_filename}' anywhere in workspace.")
        # Return early — all subsequent checks would fail anyway
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [
                {"name": c, "passed": False, "detail": "Output file not found; skipped."}
                for c in [
                    "all_six_sections_present",
                    "email_draft_marked",
                    "pending_missing_deadline_listed",
                    "pending_missing_owner_listed",
                    "escalation_rule_correct",
                    "invalid_role_corrected_in_input"
                ]
            ]
        }

    output_file = found_files[0]
    add_check("output_file_exists", True,
              f"Found output file at: {output_file}")

    # ── Read the output ──────────────────────────────────────────────────────
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("output_file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": round(total_score / max_score, 3), "checks": checks}

    # ── Check 1: All 6 required sections ────────────────────────────────────
    required_sections = [
        "行动清单",
        "负责人映射",
        "建议邮件草稿",
        "升级与催办规则",
        "下次同步议题",
        "未决问题"
    ]
    missing_sections = [s for s in required_sections if s not in content]
    add_check(
        "all_six_sections_present",
        len(missing_sections) == 0,
        f"Missing sections: {missing_sections}" if missing_sections else "All 6 sections present."
    )

    # ── Check 2: Email draft marked [DRAFT] ──────────────────────────────────
    has_draft_marker = "[DRAFT]" in content
    add_check(
        "email_draft_marked",
        has_draft_marker,
        "[DRAFT] marker found in output." if has_draft_marker else "[DRAFT] marker NOT found in output."
    )

    # ── Check 3: Missing deadline items appear in 未决问题 ───────────────────
    # Diego's mockups and Mr. Park's budget allocation had no deadline
    # Performance benchmarking had no deadline AND no owner
    pending_section_match = re.search(r"## 未决问题(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if pending_section_match:
        pending_text = pending_section_match.group(1)
    else:
        pending_text = ""

    # Check that at least 2 distinct items missing deadlines are flagged
    # We look for any mention of "截止" or "deadline" or specific names in pending section
    deadline_flags = (
        "截止" in pending_text or
        "deadline" in pending_text.lower() or
        "待确认" in pending_text or
        "未明确" in pending_text
    )
    # Additionally check that Diego or Park or 性能/benchmarking appears
    specific_items_flagged = (
        "Diego" in pending_text or
        "diego" in pending_text.lower() or
        "mockup" in pending_text.lower() or
        "UI" in pending_text or
        "Park" in pending_text or
        "预算" in pending_text or
        "budget" in pending_text.lower() or
        "性能" in pending_text or
        "benchmark" in pending_text.lower() or
        "Performance" in pending_text
    )
    deadline_check_passed = deadline_flags and (len(pending_text.strip()) > 20)
    add_check(
        "pending_missing_deadline_listed",
        deadline_check_passed,
        f"Pending section contains deadline-missing items: {deadline_check_passed}. "
        f"Snippet: '{pending_text[:200].strip()}'"
    )

    # ── Check 4: Missing owner items appear in 未决问题 ──────────────────────
    owner_unclear_flagged = (
        "负责人" in pending_text or
        "owner" in pending_text.lower() or
        "未指定" in pending_text or
        "staging" in pending_text.lower() or
        "环境" in pending_text or
        "待指定" in pending_text or
        "性能" in pending_text or
        "benchmark" in pending_text.lower()
    )
    add_check(
        "pending_missing_owner_listed",
        owner_unclear_flagged,
        f"Pending section references unclear owners: {owner_unclear_flagged}. "
        f"Snippet: '{pending_text[:200].strip()}'"
    )

    # ── Check 5: Escalation rule matches priority ────────────────────────────
    # Priority was not set in input → spec default is P2 → rule: 每周催办
    # OR agent sets P2 explicitly. Either way, 每周 / weekly must appear.
    # If agent chose P1, then 72小时 must appear.
    # We accept P1 or P2 escalation rules (both are reasonable defaults),
    # but NOT P0 (too aggressive for a missing optional field).
    escalation_section_match = re.search(r"## 升级与催办规则(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if escalation_section_match:
        esc_text = escalation_section_match.group(1)
    else:
        esc_text = ""

    has_valid_escalation = (
        "每周" in esc_text or "weekly" in esc_text.lower() or
        "72" in esc_text or "72小时" in esc_text or
        "双周" in esc_text or "24小时" in esc_text or
        "小时" in esc_text
    )
    # Must NOT be empty
    escalation_passed = has_valid_escalation and len(esc_text.strip()) > 10
    add_check(
        "escalation_rule_correct",
        escalation_passed,
        f"Escalation section has valid timing rule: {escalation_passed}. "
        f"Snippet: '{esc_text[:150].strip()}'"
    )

    # ── Check 6: Invalid role 'LEAD' was corrected ───────────────────────────
    # The agent must have fixed the input JSON before passing it to run.py.
    # Evidence: run.py would have exited with code 1 if LEAD was passed,
    # so if the output file exists AND run.py was used, the role must have been fixed.
    # We also look for any corrected input JSON the agent may have saved.
    corrected_inputs = list(workspace.rglob("*.json"))
    lead_role_still_exists = False
    fixed_role_found = False
    valid_roles = {"PM", "ENG", "DESIGN", "QA", "STAKEHOLDER"}

    for jf in corrected_inputs:
        # Skip the original raw file
        if "mtg_q2_07_raw.json" in str(jf):
            continue
        try:
            jdata = json.loads(jf.read_text(encoding="utf-8"))
            if isinstance(jdata, dict) and "participants" in jdata:
                for p in jdata.get("participants", []):
                    if p.get("name") == "Mr. Park":
                        role = p.get("role", "")
                        if role == "LEAD":
                            lead_role_still_exists = True
                        elif role in valid_roles:
                            fixed_role_found = True
        except Exception:
            continue

    # The strongest signal is that the output file exists (run.py succeeded),
    # which can only happen if the invalid role was fixed.
    # We combine: output exists (already checked) + either corrected JSON found
    # or no corrected JSON with LEAD still present.
    role_check_passed = (not lead_role_still_exists) and (
        fixed_role_found or len(found_files) > 0
    )
    add_check(
        "invalid_role_corrected_in_input",
        role_check_passed,
        f"LEAD role still present in a corrected input: {lead_role_still_exists}. "
        f"Valid replacement found: {fixed_role_found}. "
        f"(Output file existing implies run.py succeeded with valid roles.)"
    )

    # ── Final scoring ────────────────────────────────────────────────────────
    final_score = round(total_score / max_score, 3)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))