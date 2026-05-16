import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 10.0

    # ─── Helper ───
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ─── Locate the output file ───
    # Agent is asked to produce board_deck_narrative.md
    output_candidates = list(ws.rglob("board_deck_narrative.md"))
    output_file = output_candidates[0] if output_candidates else None

    if output_file is None:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "No file named 'board_deck_narrative.md' found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read output file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    total_score += add_check("output_file_exists", True, f"Found at {output_file}", weight=0.5)

    # ─── CHECK 1: Script was invoked (validate via run.py, exit 0) ───
    # We check this indirectly: run.py in validate mode returns exit 0 only if all sections present.
    # We'll re-run it ourselves as part of eval.
    import subprocess
    script_path = ws / "skills" / "deck-narrative-planner" / "scripts" / "run.py"
    try:
        result = subprocess.run(
            ["python3", str(script_path), "--input",
             str(ws / "raw_materials" / "clinical" / "novapulse_board_deck_draft.md"),
             "--output", str(output_file)],
            capture_output=True, text=True, timeout=30
        )
        script_passed = result.returncode == 0
        script_detail = f"stdout: {result.stdout.strip()!r} | stderr: {result.stderr.strip()!r}"
        total_score += add_check(
            "run_py_validation_passes",
            script_passed,
            script_detail,
            weight=2.0
        )
    except Exception as e:
        total_score += add_check("run_py_validation_passes", False, f"Exception running script: {e}", weight=2.0)

    # ─── CHECK 2: 任务书 (Task Brief) section exists ───
    has_task_brief = "任务书" in content
    total_score += add_check(
        "task_brief_section_present",
        has_task_brief,
        "Found '任务书' section" if has_task_brief else "Missing '任务书' restructured task brief section",
        weight=1.0
    )

    # ─── CHECK 3: 待确认项 (Pending Items) section exists AND mentions target audience ───
    has_pending = "待确认项" in content
    # Target audience was explicitly marked as unknown: "[待填写——Leo说要先确认...]"
    # Agent MUST NOT invent an audience; must list it as pending
    audience_pending = False
    if has_pending:
        # Find the 待确认项 section content
        pending_match = re.search(r"待确认项(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if pending_match:
            pending_text = pending_match.group(1)
            # Check that audience / 受众 is mentioned as pending
            audience_pending = bool(re.search(r"(受众|audience|目标受众|投资人类型|专业医疗|综合PE|Leo|待填写)", 
                                              pending_text, re.IGNORECASE))
    total_score += add_check(
        "pending_items_has_audience",
        has_pending and audience_pending,
        "待确认项 section correctly flags unknown target audience" if (has_pending and audience_pending)
        else f"待确认项 present: {has_pending}; audience flagged as pending: {audience_pending}",
        weight=1.5
    )

    # ─── CHECK 4: 整体主线 section exists and is non-trivial ───
    has_main_narrative = "整体主线" in content
    main_narrative_ok = False
    if has_main_narrative:
        match = re.search(r"整体主线(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Must have at least 20 Chinese characters (non-trivial)
            cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            main_narrative_ok = cn_chars >= 15
    total_score += add_check(
        "main_narrative_substantive",
        has_main_narrative and main_narrative_ok,
        "整体主线 is substantive" if (has_main_narrative and main_narrative_ok)
        else "整体主线 missing or too short",
        weight=0.5
    )

    # ─── CHECK 5: 页级标题 with at least 6 numbered items ───
    has_slide_titles = "页级标题" in content
    slide_count = 0
    if has_slide_titles:
        match = re.search(r"页级标题(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if match:
            slide_text = match.group(1)
            numbered = re.findall(r"(?m)^\s*\d+[.、．。]\s*.+", slide_text)
            slide_count = len(numbered)
    slides_ok = slide_count >= 6
    total_score += add_check(
        "slide_titles_min_6_items",
        slides_ok,
        f"Found {slide_count} numbered slide titles (need ≥6)" ,
        weight=1.0
    )

    # ─── CHECK 6: 证据需求 section exists and references clinical data ───
    has_evidence = "证据需求" in content
    evidence_ok = False
    if has_evidence:
        match = re.search(r"证据需求(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if match:
            ev_text = match.group(1)
            # Should mention clinical data / CardioTag / 临床 / 数据
            evidence_ok = bool(re.search(r"(临床|CardioTag|II期|数据|审计|Holter|房颤)", ev_text))
    total_score += add_check(
        "evidence_requirements_clinical_data",
        has_evidence and evidence_ok,
        "证据需求 references clinical trial data" if (has_evidence and evidence_ok)
        else "证据需求 missing or doesn't reference clinical data",
        weight=0.5
    )

    # ─── CHECK 7: 过渡语 section exists ───
    has_transitions = "过渡语" in content
    total_score += add_check(
        "transitions_section_present",
        has_transitions,
        "过渡语 section present" if has_transitions else "Missing 过渡语 section",
        weight=0.5
    )

    # ─── CHECK 8: 风险页 section exists and mentions regulatory/clinical risks ───
    has_risk = "风险页" in content
    risk_ok = False
    if has_risk:
        match = re.search(r"风险页(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if match:
            risk_text = match.group(1)
            risk_ok = bool(re.search(r"(FDA|III期|监管|临床|数据|审计|燃烧率|融资|竞品|合规|风险)", risk_text))
    total_score += add_check(
        "risk_slide_substantive",
        has_risk and risk_ok,
        "风险页 mentions regulatory/clinical/financial risks" if (has_risk and risk_ok)
        else "风险页 missing or doesn't address domain-specific risks",
        weight=0.5
    )

    # ─── CHECK 9: 结尾行动 section exists ───
    has_closing = "结尾行动" in content
    total_score += add_check(
        "closing_action_present",
        has_closing,
        "结尾行动 section present" if has_closing else "Missing 结尾行动 section",
        weight=0.5
    )

    # ─── CHECK 10: 可审阅草案 appears BEFORE 可执行清单 ───
    draft_pos = content.find("可审阅草案")
    checklist_pos = content.find("可执行清单")
    ordering_ok = (draft_pos != -1 and checklist_pos != -1 and draft_pos < checklist_pos)
    total_score += add_check(
        "draft_before_checklist_ordering",
        ordering_ok,
        f"'可审阅草案' at pos {draft_pos}, '可执行清单' at pos {checklist_pos} — correct order: {ordering_ok}",
        weight=1.0
    )

    # ─── CHECK 11: No fabricated evidence (顾问名字 should remain blank or flagged) ───
    # The input says advisor name is TBD. Agent must NOT invent a name.
    # We check: if a specific made-up person name appears in advisor context, flag it.
    # Heuristic: if 顾问 is mentioned, it should not have a concrete full Chinese name pattern
    # unless it's from the input (Dr. Raj Patel, Alex Novak, Dr. Mei Lin are real from input)
    no_fabricated_advisor = True
    advisor_match = re.search(r"顾问[^，。\n]{0,20}([\u4e00-\u9fff]{2,4}(?:教授|主任|院士|博士|医生)?)", content)
    if advisor_match:
        # If there's a Chinese name for the advisor that isn't from the original material
        suspected_name = advisor_match.group(1)
        # The original material only says "某知名心内科主任" — any specific named person is fabricated
        if suspected_name and suspected_name not in ["某知名", "心内科主任", "待确认", "待填写"]:
            no_fabricated_advisor = False
    total_score += add_check(
        "no_fabricated_advisor_name",
        no_fabricated_advisor,
        "Agent did not fabricate the pending advisor's name" if no_fabricated_advisor
        else f"Agent may have fabricated advisor name: {advisor_match.group(1) if advisor_match else '?'}",
        weight=0.5
    )

    # ─── Final scoring ───
    final_score = min(total_score / max_score, 1.0)
    all_critical = (
        checks[0]["passed"] and  # file exists
        any(c["name"] == "run_py_validation_passes" and c["passed"] for c in checks) and
        any(c["name"] == "pending_items_has_audience" and c["passed"] for c in checks) and
        any(c["name"] == "slide_titles_min_6_items" and c["passed"] for c in checks) and
        any(c["name"] == "draft_before_checklist_ordering" and c["passed"] for c in checks)
    )

    return {
        "passed": all_critical and final_score >= 0.65,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))