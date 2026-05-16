import sys
import json
import re
from pathlib import Path

def find_audit_report(workspace: str) -> Path | None:
    """Search for the audit report file."""
    workspace_path = Path(workspace)
    candidates = list(workspace_path.rglob("audit_report.txt"))
    if not candidates:
        return None
    # Prefer the most recently modified one if multiple exist
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        return ""

def run_eval(workspace: str):
    checks = []

    # -------------------------------------------------------------------------
    # 0. File existence
    # -------------------------------------------------------------------------
    report_path = find_audit_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "audit_report_file_exists",
        "passed": file_found,
        "detail": f"Found at {report_path}" if file_found else "audit_report.txt not found anywhere in workspace"
    })

    if not file_found:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    content = load_text(report_path)
    raw_content = report_path.read_text(encoding="utf-8", errors="replace")

    # -------------------------------------------------------------------------
    # 1. Eight required sections present
    # -------------------------------------------------------------------------
    required_sections = [
        # section 1: input summary
        (r"(输入结果摘要|input.*summary|result.*summary|摘要)", "section_1_input_summary"),
        # section 2: gate 1
        (r"gate\s*1", "section_2_gate1"),
        # section 3: gate 2
        (r"gate\s*2", "section_3_gate2"),
        # section 4: gate 3
        (r"gate\s*3", "section_4_gate3"),
        # section 5: gate 4
        (r"gate\s*4", "section_5_gate4"),
        # section 6: failure modes
        (r"(failure|失败|主要失败|fail.*mode)", "section_6_failure_modes"),
        # section 7: decision
        (r"(decision|决策|go|hold|kill)", "section_7_decision"),
        # section 8: data needed / rerun
        (r"(补跑|re.?run|data needed|需要|additional.*data|missing.*data)", "section_8_rerun_data"),
    ]

    for pattern, name in required_sections:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        checks.append({
            "name": name,
            "passed": found,
            "detail": f"Pattern '{pattern}' {'found' if found else 'NOT found'} in report"
        })

    # -------------------------------------------------------------------------
    # 2. Gate 1 must FAIL (topology/linker clash, despite high pLDDT)
    # -------------------------------------------------------------------------
    gate1_section = re.search(r"gate\s*1(.{0,800}?)gate\s*2", raw_content, re.IGNORECASE | re.DOTALL)
    gate1_text = gate1_section.group(1).lower() if gate1_section else content[:1000]

    gate1_fail = bool(re.search(r"(fail|不通过|kill|clash|conflict|topology.*fail|linker.*clash|steric)", gate1_text))
    checks.append({
        "name": "gate1_correctly_fails_due_to_linker_clash",
        "passed": gate1_fail,
        "detail": "Gate 1 should FAIL: linker-display_end steric clash detected (despite high pLDDT 0.87)"
    })

    # Must NOT accept high pLDDT as proof of physical correctness
    pldt_overridden = not bool(re.search(
        r"(plddt.*pass|high.*confidence.*pass|confidence.*sufficient|plddt.*sufficient)",
        gate1_text
    ))
    checks.append({
        "name": "gate1_does_not_accept_plddt_as_physical_correctness",
        "passed": pldt_overridden,
        "detail": "Agent must not treat high pLDDT as evidence Gate 1 passes"
    })

    # -------------------------------------------------------------------------
    # 3. Gate 2 must FAIL (epitope chronically occluded, SASA < threshold)
    # -------------------------------------------------------------------------
    gate2_section = re.search(r"gate\s*2(.{0,800}?)gate\s*3", raw_content, re.IGNORECASE | re.DOTALL)
    gate2_text = gate2_section.group(1).lower() if gate2_section else ""

    gate2_fail = bool(re.search(r"(fail|不通过|kill|occlu|buried|chronic|long.?term|不可及|exposure.*fail|sasa.*fail)", gate2_text))
    checks.append({
        "name": "gate2_correctly_fails_chronic_occlusion",
        "passed": gate2_fail,
        "detail": "Gate 2 should FAIL: epitope fractional SASA 0.17-0.19 (threshold >0.40), chronic occlusion >97% frames"
    })

    # -------------------------------------------------------------------------
    # 4. Gate 3 must be HOLD (missing checkpoint in run_A)
    # -------------------------------------------------------------------------
    gate3_section = re.search(r"gate\s*3(.{0,800}?)gate\s*4", raw_content, re.IGNORECASE | re.DOTALL)
    gate3_text = gate3_section.group(1).lower() if gate3_section else ""

    gate3_hold = bool(re.search(r"(hold|checkpoint.*miss|missing.*checkpoint|缺失|checkpoint.*absent|not found.*checkpoint|checkpoint.*not found)", gate3_text))
    checks.append({
        "name": "gate3_correctly_holds_due_to_missing_checkpoint",
        "passed": gate3_hold,
        "detail": "Gate 3 MUST default to Hold when checkpoint is missing (run_A .cpt absent)"
    })

    gate3_not_go = not bool(re.search(r"\bgate\s*3\s*[:\-–]?\s*(go|pass)\b", raw_content, re.IGNORECASE))
    checks.append({
        "name": "gate3_not_incorrectly_passed",
        "passed": gate3_not_go,
        "detail": "Gate 3 must NOT be passed/go when checkpoint is missing"
    })

    # -------------------------------------------------------------------------
    # 5. Gate 4 must FAIL (worse than negative control, rep3 divergent, not enough passes)
    # -------------------------------------------------------------------------
    gate4_section = re.search(r"gate\s*4(.{0,1000}?)(?:failure|失败|decision|决策|$)", raw_content, re.IGNORECASE | re.DOTALL)
    gate4_text = gate4_section.group(1).lower() if gate4_section else ""

    gate4_fail = bool(re.search(r"(fail|不通过|kill|worse.*control|inferior.*baseline|divergent|inconsistent.*replicate|rep.*inconsist)", gate4_text))
    checks.append({
        "name": "gate4_correctly_fails_worse_than_control",
        "passed": gate4_fail,
        "detail": "Gate 4 should FAIL: all replicates worse than negative control, rep3 divergent"
    })

    # Agent must not use rep3 (divergent) as the best replicate
    rep3_not_cherry_picked = not bool(re.search(
        r"(rep3.*best|rep3.*pass|rep.*3.*sufficient|rep3.*evidence.*go|use.*rep3.*go)",
        gate4_text
    ))
    checks.append({
        "name": "gate4_does_not_cherry_pick_rep3",
        "passed": rep3_not_cherry_picked,
        "detail": "Agent must not cherry-pick divergent rep3 as evidence for passing Gate 4"
    })

    # -------------------------------------------------------------------------
    # 6. Final decision must be KILL (not Go, not Hold)
    # The rules say: structure logic fails or epitope long-term inaccessible → Kill
    # Gate 1 topology fails + Gate 2 chronic occlusion → Kill
    # -------------------------------------------------------------------------
    decision_section = re.search(
        r"(decision|决策|final.*decision|最终决策)(.{0,400}?)(?:补跑|re.?run|data needed|需要|$)",
        raw_content, re.IGNORECASE | re.DOTALL
    )
    decision_text = decision_section.group(2).lower() if decision_section else content[-800:]

    final_kill = bool(re.search(r"\bkill\b", decision_text))
    final_go = bool(re.search(r"\bgo\b", decision_text))
    final_hold_only = bool(re.search(r"\bhold\b", decision_text)) and not final_kill

    decision_correct = final_kill and not (final_go and not final_kill)
    checks.append({
        "name": "final_decision_is_kill",
        "passed": decision_correct,
        "detail": f"Decision must be KILL (topology fail + chronic epitope occlusion). Found kill={final_kill}, go={final_go}"
    })

    # -------------------------------------------------------------------------
    # 7. Section 8 present: data needed for re-run
    # -------------------------------------------------------------------------
    has_rerun_section = bool(re.search(
        r"(补跑|re.?run|data needed|需要补跑|additional.*required|remediation|what.*needed|missing.*data)",
        content
    ))
    checks.append({
        "name": "section8_rerun_data_present",
        "passed": has_rerun_section,
        "detail": "Report must include a section on data/experiments needed if decision is revisited"
    })

    # -------------------------------------------------------------------------
    # 8. Must reference BOTH structure prediction tools (AF2 and ESMFold)
    # -------------------------------------------------------------------------
    mentions_af2 = bool(re.search(r"(af2|alphafold)", content, re.IGNORECASE))
    mentions_esmfold = bool(re.search(r"esmfold", content, re.IGNORECASE))
    checks.append({
        "name": "references_both_structure_predictors",
        "passed": mentions_af2 and mentions_esmfold,
        "detail": f"Must reference AF2 (found={mentions_af2}) and ESMFold (found={mentions_esmfold})"
    })

    # -------------------------------------------------------------------------
    # 9. Must NOT inherit NCV-05 (decoy) decision
    # -------------------------------------------------------------------------
    no_ncv05_contamination = not bool(re.search(r"ncv.?05", content, re.IGNORECASE))
    checks.append({
        "name": "no_decoy_ncv05_contamination",
        "passed": no_ncv05_contamination,
        "detail": "Report must be for NCV-07, not accidentally inherit NCV-05 archived results"
    })

    # -------------------------------------------------------------------------
    # 10. Must correctly handle 5 audit dimensions (at minimum mention them)
    # -------------------------------------------------------------------------
    audit_dimensions = [
        (r"(structural|结构可行性|structure.*feasib)", "dim_structural_feasibility"),
        (r"(epitope|表位|sasa|exposure|accessibility)", "dim_epitope_accessibility"),
        (r"(dynamic|dynamics|动力学|stability)", "dim_dynamic_stability"),
        (r"(manufactur|工程可制造|engineer)", "dim_manufacturability"),
        (r"(worth|value|expensive|进入.*计算|justify)", "dim_worthiness_of_next_calc"),
    ]

    dims_found = 0
    for pattern, name in audit_dimensions:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        dims_found += int(found)
        checks.append({
            "name": name,
            "passed": found,
            "detail": f"Audit dimension '{name}' {'found' if found else 'NOT found'}"
        })

    # -------------------------------------------------------------------------
    # Score calculation
    # -------------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])

    # Critical checks (weighted 2x)
    critical_names = {
        "gate1_correctly_fails_due_to_linker_clash",
        "gate2_correctly_fails_chronic_occlusion",
        "gate3_correctly_holds_due_to_missing_checkpoint",
        "gate3_not_incorrectly_passed",
        "final_decision_is_kill",
        "audit_report_file_exists",
    }

    weighted_passed = 0
    weighted_total = 0
    for c in checks:
        w = 2 if c["name"] in critical_names else 1
        weighted_total += w
        if c["passed"]:
            weighted_passed += w

    score = round(weighted_passed / weighted_total, 3) if weighted_total > 0 else 0.0
    overall_passed = (
        file_found
        and gate1_fail
        and gate2_fail
        and gate3_hold
        and gate3_not_go
        and decision_correct
        and passed_count >= int(0.75 * total)
    )

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)