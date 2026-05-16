#!/usr/bin/env python3
"""
Evaluation script for the meeting-risk-radar task.
Usage: python3 eval_script.py <workspace_dir>
"""

import json
import os
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "会前风险",
    "缺失材料",
    "责任模糊点",
    "建议改议程",
    "必须提前确认的问题",
    "失控预案",
]

# Expected content signals based on the task input's known risk profile
EXPECTED_SIGNALS = {
    "高风险/合规关键词": [
        r"合规|compliance|监管|隐私|privacy|数据隐私",
    ],
    "参会人数超限警告": [
        r"10\s*人|超过\s*8\s*人|参会人数",
    ],
    "缺失材料-预算或数据隐私": [
        r"数据隐私整改专项|2025预算审批|监管检查结果",
    ],
    "责任模糊-无负责人": [
        r"未指定负责人|2025预算审批|owner.*未|无.*负责人",
    ],
    "无决策者警告或决策项确认": [
        r"决策项|批准.*预算|授权|监管合规路线图|数据隐私整改",
    ],
    "失控预案内容": [
        r"主持人|离线|超时|顺延|分歧|汇总",
    ],
}


def find_report(workspace: str) -> Path | None:
    """Search for the output risk report markdown file."""
    ws = Path(workspace)
    candidates = list(ws.rglob("*.md"))
    # Filter out skill's own template/readme
    skill_base = ws / "skills" / "meeting-risk-radar"
    candidates = [
        c for c in candidates
        if not str(c).startswith(str(skill_base))
        and c.name.lower() not in ("smoke-test.md",)
    ]
    if not candidates:
        return None
    # Prefer most recently modified
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(0)

    workspace = sys.argv[1]
    checks = []

    # ── CHECK 1: Output file exists ──────────────────────────────────────────
    report_path = find_report(workspace)
    check_exists = {
        "name": "output_file_exists",
        "passed": report_path is not None,
        "detail": f"Found: {report_path}" if report_path else "No .md output file found outside skill directory",
    }
    checks.append(check_exists)

    if not check_exists["passed"]:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    # ── Read the report ──────────────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))
        return

    checks.append({"name": "file_readable", "passed": True, "detail": f"Read {len(content)} chars"})

    # ── CHECK 2: All six required sections present ────────────────────────────
    section_results = []
    for section in REQUIRED_SECTIONS:
        pattern = rf"##\s*{re.escape(section)}"
        found = bool(re.search(pattern, content))
        section_results.append({
            "name": f"section__{section}",
            "passed": found,
            "detail": f"Section '## {section}' {'found' if found else 'MISSING'} in report",
        })
    checks.extend(section_results)
    all_sections_present = all(c["passed"] for c in section_results)

    # ── CHECK 3: Content signals (at least 4 of 6 must match) ────────────────
    signal_checks = []
    for signal_name, patterns in EXPECTED_SIGNALS.items():
        matched = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        signal_checks.append({
            "name": f"signal__{signal_name}",
            "passed": matched,
            "detail": f"Signal '{signal_name}' {'detected' if matched else 'NOT detected'}",
        })
    checks.extend(signal_checks)
    signals_passed = sum(1 for c in signal_checks if c["passed"])

    # ── CHECK 4: Script was actually invoked (not just template copy) ─────────
    # The rendered output must contain the actual meeting title from the task input
    task_title_present = "FinTech 监管合规专项董事会会议" in content or "FinTech" in content or "监管合规" in content
    checks.append({
        "name": "task_specific_content",
        "passed": task_title_present,
        "detail": (
            "Report contains task-specific meeting title/content"
            if task_title_present
            else "Report appears to be a blank template — does not reference the actual meeting"
        ),
    })

    # ── CHECK 5: Input JSON was the correct task file ─────────────────────────
    # Verify at least one specific agenda item name appears in the output
    agenda_signal = bool(
        re.search(r"数据隐私整改专项|监管检查结果通报|2025预算审批|监管备忘录授权", content)
    )
    checks.append({
        "name": "correct_input_processed",
        "passed": agenda_signal,
        "detail": (
            "Output references agenda items from board_compliance_meeting.json"
            if agenda_signal
            else "Could not detect agenda items from the task input file — wrong input may have been used"
        ),
    })

    # ── CHECK 6: Report is non-trivial (at least 300 chars) ──────────────────
    non_trivial = len(content.strip()) >= 300
    checks.append({
        "name": "report_non_trivial",
        "passed": non_trivial,
        "detail": f"Report length: {len(content.strip())} chars (min 300 required)",
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    # Weights:
    #   all 6 sections: 40%
    #   ≥4/6 signals:   25%
    #   task-specific:  15%
    #   correct input:  10%
    #   non-trivial:    10%
    score = 0.0
    if all_sections_present:
        score += 0.40
    elif sum(1 for c in section_results if c["passed"]) >= 4:
        score += 0.20  # partial credit

    if signals_passed >= 4:
        score += 0.25
    elif signals_passed >= 2:
        score += 0.12

    if task_title_present:
        score += 0.15
    if agenda_signal:
        score += 0.10
    if non_trivial:
        score += 0.10

    passed = (
        all_sections_present
        and signals_passed >= 4
        and task_title_present
        and agenda_signal
        and non_trivial
    )

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()