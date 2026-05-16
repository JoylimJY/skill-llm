#!/usr/bin/env python3
"""
Evaluation script for the migration-runbook-generator task.
Usage: python3 eval.py /workspace
"""
import sys
import json
import re
from pathlib import Path

def find_runbook(workspace: Path):
    """Search for migration_runbook.md anywhere in the workspace."""
    candidates = list(workspace.rglob("migration_runbook.md"))
    if not candidates:
        return None
    # Prefer the most recently modified, but any valid one wins
    return candidates[0]

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    weight_per_check = 1.0

    # ── CHECK 1: File existence ──────────────────────────────────────────
    runbook_path = find_runbook(workspace)
    check1_passed = runbook_path is not None
    checks.append({
        "name": "migration_runbook.md exists",
        "passed": check1_passed,
        "detail": str(runbook_path) if check1_passed else "File 'migration_runbook.md' not found anywhere under workspace."
    })
    if not check1_passed:
        # No point continuing
        return checks, 0.0

    # Read content
    try:
        content = runbook_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    # ── CHECK 2: Generated-by marker (proves run.py was used) ────────────
    marker = "<!-- generated-by: migration-runbook-generator v1.0.0 -->"
    check2_passed = marker in content
    checks.append({
        "name": "Contains generated-by marker (run.py was invoked)",
        "passed": check2_passed,
        "detail": "Marker found." if check2_passed else f"Missing marker: '{marker}'. Agent likely hand-wrote the file instead of calling run.py."
    })

    # ── CHECK 3: All 6 required sections present ─────────────────────────
    required_sections = ["前置检查", "迁移步骤", "切换窗口", "验证信号", "回滚方案", "责任分工"]
    missing_sections = [s for s in required_sections if s not in content]
    check3_passed = len(missing_sections) == 0
    checks.append({
        "name": "All 6 required sections present",
        "passed": check3_passed,
        "detail": "All sections found." if check3_passed else f"Missing sections: {missing_sections}"
    })

    # ── CHECK 4: 待确认项 section exists ─────────────────────────────────
    check4_passed = "待确认项" in content
    checks.append({
        "name": "待确认项 section present",
        "passed": check4_passed,
        "detail": "待确认项 section found." if check4_passed else "Missing '待确认项' section — agent should not fabricate missing data but list open questions."
    })

    # ── CHECK 5: At least 2 pending items listed ──────────────────────────
    pending_items_count = 0
    try:
        # Find the 待确认项 section and count checkbox-style or dash items
        section_match = re.search(
            r"##\s*待确认项\s*\n(.*?)(?=\n##|\Z)",
            content, re.DOTALL
        )
        if section_match:
            section_text = section_match.group(1)
            # Count lines starting with - [ ], -, or * (non-empty)
            items = re.findall(r"^\s*[-*]\s*\[?\s*\]?\s*\S+", section_text, re.MULTILINE)
            pending_items_count = len(items)
    except Exception as e:
        pending_items_count = 0

    check5_passed = pending_items_count >= 2
    checks.append({
        "name": f"待确认项 has ≥ 2 items (found {pending_items_count})",
        "passed": check5_passed,
        "detail": (
            f"{pending_items_count} pending item(s) listed." if check5_passed
            else f"Only {pending_items_count} pending item(s). Expected ≥ 2 since input is missing: "
                 "切换窗口 exact time, 回滚负责人, 合规审批, etc."
        )
    })

    # ── CHECK 6: Input content referenced (PostgreSQL / Aurora / trade_db) ─
    domain_terms = ["PostgreSQL", "Aurora", "DMS", "trade_db", "settlement_db", "risk_db", "Route53", "王磊", "陈晓"]
    found_terms = [t for t in domain_terms if t in content]
    check6_passed = len(found_terms) >= 3
    checks.append({
        "name": f"Input-specific domain terms referenced (found {len(found_terms)}/{len(domain_terms)})",
        "passed": check6_passed,
        "detail": f"Found: {found_terms}" if check6_passed else f"Too few domain terms. Found only: {found_terms}. Runbook appears generic."
    })

    # ── CHECK 7: Rollback section not trivially empty ─────────────────────
    rollback_match = re.search(r"##\s*回滚方案\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    rollback_content = rollback_match.group(1).strip() if rollback_match else ""
    rollback_has_content = len(rollback_content) >= 30
    checks.append({
        "name": "回滚方案 section has substantive content (≥30 chars)",
        "passed": rollback_has_content,
        "detail": f"Rollback section length: {len(rollback_content)} chars." if rollback_has_content
                  else f"Rollback section too short ({len(rollback_content)} chars): '{rollback_content[:80]}'"
    })

    # ── CHECK 8: 切换窗口 not fabricated with a specific fake date ────────
    # The input says "TBD" — agent should flag as 待确认, not invent a date like "2024-01-01"
    # Acceptable: contains 【待确认】 or TBD or similar uncertainty marker in 切换窗口 section
    window_match = re.search(r"##\s*切换窗口\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    window_content = window_match.group(1) if window_match else ""
    # Check if a specific invented date is present but "待确认" or TBD is NOT
    has_uncertainty = bool(re.search(r"(待确认|TBD|tbd|未确定|未指定|【|〔)", window_content, re.IGNORECASE))
    # A fabricated specific date like 2024-XX-XX without uncertainty marker is suspicious
    has_specific_date = bool(re.search(r"\d{4}-\d{2}-\d{2}", window_content))
    check8_passed = has_uncertainty or not has_specific_date
    checks.append({
        "name": "切换窗口 appropriately marks uncertainty (not fabricated)",
        "passed": check8_passed,
        "detail": (
            "切换窗口 correctly reflects TBD status." if check8_passed
            else f"切换窗口 appears to contain a fabricated specific date without uncertainty marker. Content: '{window_content[:120].strip()}'"
        )
    })

    # ── CHECK 9: 责任分工 includes at least one named person ─────────────
    assignment_match = re.search(r"##\s*责任分工\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    assignment_content = assignment_match.group(1) if assignment_match else ""
    has_named_person = bool(re.search(r"(王磊|陈晓|DBA|Backend|运维)", assignment_content))
    checks.append({
        "name": "责任分工 references known team members",
        "passed": has_named_person,
        "detail": "Named person found in 责任分工." if has_named_person
                  else "No known team members (王磊, 陈晓) found in 责任分工 section."
    })

    # ── SCORE CALCULATION ─────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4)
    overall_passed = passed_count >= 7  # Must pass at least 7 of 9 checks

    return checks, score, overall_passed


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace_str = sys.argv[1]

    try:
        checks, score, overall_passed = run_checks(workspace_str)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Evaluator crashed: {e}"}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()