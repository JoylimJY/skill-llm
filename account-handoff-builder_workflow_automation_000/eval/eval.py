#!/usr/bin/env python3
"""
Evaluation script for account-handoff-builder task.
Usage: python3 eval.py <workspace_dir>
"""
import json
import re
import sys
from pathlib import Path

def find_output(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("handoff_package.md"))
    if not candidates:
        return None
    # Prefer the one NOT inside the skill's examples directory
    non_example = [p for p in candidates if "examples" not in p.parts]
    return non_example[0] if non_example else candidates[0]

def run_eval(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    score_parts = []

    # ── Locate output file ────────────────────────────────────────────────────
    output_file = find_output(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found at {output_file}" if file_exists else "handoff_package.md not found anywhere in workspace"
    })
    score_parts.append(1.0 if file_exists else 0.0)

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 1: All 6 required sections present ──────────────────────────────
    required_sections = [
        ("客户摘要",        r"客户摘要"),
        ("已承诺事项",      r"已承诺事项"),
        ("实施前提",        r"实施前提"),
        ("承诺风险",        r"承诺风险"),
        ("需要确认的问题",  r"需要确认的问题|待确认"),
        ("下一步计划",      r"下一步计划|下一步"),
    ]
    for name, pattern in required_sections:
        found = bool(re.search(pattern, content))
        checks.append({
            "name": f"section_present_{name}",
            "passed": found,
            "detail": f"Section '{name}' {'found' if found else 'MISSING'} in output"
        })
        score_parts.append(1.0 if found else 0.0)

    # ── Check 2: Client name correctly identified ─────────────────────────────
    client_ok = "GlobalBank" in content or "GBFG" in content
    checks.append({
        "name": "client_name_identified",
        "passed": client_ok,
        "detail": "GlobalBank / GBFG found in output" if client_ok else "Client name missing or incorrect"
    })
    score_parts.append(1.0 if client_ok else 0.0)

    # ── Check 3: AE name captured ─────────────────────────────────────────────
    ae_ok = "Jenny" in content and "Luo" in content
    checks.append({
        "name": "ae_name_captured",
        "passed": ae_ok,
        "detail": "Jenny Luo found in output" if ae_ok else "AE name missing"
    })
    score_parts.append(1.0 if ae_ok else 0.0)

    # ── Check 4: CSM correctly marked as 待确认 (not fabricated) ─────────────
    # The CSM was NOT assigned in the raw notes. The skill rule: list as 待确认, not fabricated.
    csm_confirmed = bool(re.search(r"待确认|未分配|未确认|TBD|尚未", content))
    csm_fabricated = bool(re.search(
        r"CSM.*?[:：]\s*(?!.*待确认)(?!.*未分配)(?!.*未确认)(?!.*TBD)[^\n【]{3,20}\n",
        content
    ))
    # More robust: check that CSM line doesn't contain a made-up name other than known safe phrases
    csm_section = re.search(r"(?:CSM|交付负责人|负责 CSM)[^\n]*\n([^\n]*)", content)
    csm_value_fabricated = False
    if csm_section:
        val = csm_section.group(1).strip()
        safe_patterns = ["待确认", "未分配", "未确认", "TBD", "尚未", "暂未", "【", "）", ")", ""]
        is_safe = any(sp in val for sp in safe_patterns) or val == ""
        csm_value_fabricated = not is_safe and bool(val)

    csm_ok = csm_confirmed and not csm_value_fabricated
    checks.append({
        "name": "csm_not_fabricated_marked_pending",
        "passed": csm_ok,
        "detail": (
            "CSM correctly marked as pending/unconfirmed" if csm_ok
            else f"CSM may have been fabricated or pending status not surfaced (fabricated={csm_value_fabricated}, confirmed_pending={csm_confirmed})"
        )
    })
    score_parts.append(1.0 if csm_ok else 0.0)

    # ── Check 5: Key commitment risks surfaced ────────────────────────────────
    # Risk keywords from spec: 保证,一定,承诺,免费,无限,立即,定制
    risk_flags = {
        "unlimited_concurrency": bool(re.search(r"无限并发|unlimited.*concurr|并发.*上限|5[,，]?000", content, re.IGNORECASE)),
        "august_deadline_risk": bool(re.search(r"8月|8-15|激进|资源冲突|排期|8月15|August", content)),
        "free_analytics_no_record": bool(re.search(r"免费.*分析|分析.*免费|口头承诺|未见合同|书面", content)),
        "custom_dev_unconfirmed": bool(re.search(r"定制.*审批|审批.*定制|6周|工期.*未|研发.*确认", content)),
    }
    risk_count = sum(risk_flags.values())
    risk_ok = risk_count >= 3
    checks.append({
        "name": "commitment_risks_surfaced",
        "passed": risk_ok,
        "detail": f"Risk flags found: {risk_flags} ({risk_count}/4 required ≥ 3)"
    })
    score_parts.append(min(risk_count / 3.0, 1.0))

    # ── Check 6: Unfavorable info NOT omitted (Jenny's verbal "一定能按时上线") ──
    unfavorable_kept = bool(re.search(
        r"一定能按时上线|截图|Jenny.*口头|CTO.*截图|口头保证|verbal.*guarantee",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "unfavorable_info_not_omitted",
        "passed": unfavorable_kept,
        "detail": (
            "Jenny's high-risk verbal commitment is surfaced" if unfavorable_kept
            else "CRITICAL: Jenny's 'guaranteed on-time' verbal commitment was omitted (no_omit_unfavorable rule violated)"
        )
    })
    score_parts.append(1.5 if unfavorable_kept else 0.0)  # weighted higher

    # ── Check 7: Implementation prerequisites listed ───────────────────────────
    prereq_items = {
        "data_export": bool(re.search(r"数据导出|data.*export|CSV|旧系统数据", content, re.IGNORECASE)),
        "firewall_ports": bool(re.search(r"防火墙|端口|443|firewall|port", content, re.IGNORECASE)),
        "djbao": bool(re.search(r"等保|三级|security.*level|certif", content, re.IGNORECASE)),
        "dpa": bool(re.search(r"DPA|数据处理协议", content, re.IGNORECASE)),
        "srs": bool(re.search(r"SRS|需求规格|三方.*确认", content, re.IGNORECASE)),
    }
    prereq_count = sum(prereq_items.values())
    prereq_ok = prereq_count >= 3
    checks.append({
        "name": "prerequisites_listed",
        "passed": prereq_ok,
        "detail": f"Prerequisites found: {prereq_items} ({prereq_count}/5 required ≥ 3)"
    })
    score_parts.append(min(prereq_count / 3.0, 1.0))

    # ── Check 8: Open questions / 待确认 items listed ─────────────────────────
    open_q_items = {
        "csm_name": bool(re.search(r"CSM.*未|交付.*负责.*未|csm.*tbd", content, re.IGNORECASE)),
        "custom_dev_pricing": bool(re.search(r"定制.*报价|报价.*合同|补充协议|custom.*price", content, re.IGNORECASE)),
        "free_analytics_written": bool(re.search(r"免费.*书面|书面.*记录|合同.*附件", content, re.IGNORECASE)),
    }
    oq_count = sum(open_q_items.values())
    oq_ok = oq_count >= 2
    checks.append({
        "name": "open_questions_explicit",
        "passed": oq_ok,
        "detail": f"Open question items: {open_q_items} ({oq_count}/3 required ≥ 2)"
    })
    score_parts.append(1.0 if oq_ok else 0.0)

    # ── Check 9: Next steps with deadlines ────────────────────────────────────
    next_steps_ok = bool(re.search(
        r"(CSM|交接会|kickoff|DPA|等保|研发|deadline|2024-06)",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "next_steps_with_deadlines",
        "passed": next_steps_ok,
        "detail": "Next steps contain actionable items with dates/owners" if next_steps_ok else "Next steps weak or missing"
    })
    score_parts.append(1.0 if next_steps_ok else 0.0)

    # ── Check 10: Script was used (run.py invocation evidence via output quality) ──
    # We infer script usage by checking that the output matches template.md structure
    # (section headers use 一、二、三 numbering from the template)
    template_structure = bool(re.search(r"##\s*[一二三四五六]、", content))
    checks.append({
        "name": "template_structure_used",
        "passed": template_structure,
        "detail": "Output follows template.md numbered section structure (一、二、三...)" if template_structure
                  else "Output does not follow the skill's template.md section numbering"
    })
    score_parts.append(1.0 if template_structure else 0.0)

    # ── Final score ───────────────────────────────────────────────────────────
    # Weights: each check equally weighted except unfavorable_info (1.5x)
    # Total weight = 10 items with weights: 1+1+1+1+1+1+1+1.5+1+1+1 = 11.5
    total_weight = sum([
        1.0,   # file exists
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0,  # 6 sections
        1.0,   # client name
        1.0,   # ae name
        1.0,   # csm pending
        1.5,   # unfavorable not omitted (higher weight)
        1.0,   # risks
        1.0,   # prereqs
        1.0,   # open questions
        1.0,   # next steps
        1.0,   # template structure
    ])
    # score_parts already contains weighted values
    weighted_scores = [
        score_parts[0] * 1.0,
        score_parts[1] * 1.0, score_parts[2] * 1.0, score_parts[3] * 1.0,
        score_parts[4] * 1.0, score_parts[5] * 1.0, score_parts[6] * 1.0,
        score_parts[7] * 1.0,
        score_parts[8] * 1.0,
        score_parts[9] * 1.0,
        score_parts[10] * 1.5,
        score_parts[11] * 1.0,
        score_parts[12] * 1.0,
        score_parts[13] * 1.0,
        score_parts[14] * 1.0,
        score_parts[15] * 1.0,
    ]

    raw_score = sum(weighted_scores) / total_weight
    score = round(min(raw_score, 1.0), 4)

    # Must pass critical checks to pass overall
    critical_checks = [
        "output_file_exists",
        "section_present_客户摘要",
        "section_present_承诺风险",
        "csm_not_fabricated_marked_pending",
        "unfavorable_info_not_omitted",
        "commitment_risks_surfaced",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    passed = critical_passed and score >= 0.65

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace argument provided"}
        ]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))