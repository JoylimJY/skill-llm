import sys
import json
import re
from pathlib import Path

def score_checks(checks):
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / len(checks), 3) if checks else 0.0

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def read_file(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None

def check_contains(text, patterns, flags=re.IGNORECASE):
    return all(re.search(p, text, flags) for p in patterns)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Locate the three required output files ────────────────────────────────
    audit_file   = find_file(workspace, "safety_audit_report.md")
    jha_file     = find_file(workspace, "forklift_jha.md")
    incident_file = find_file(workspace, "incident_report.md")

    audit_text   = read_file(audit_file)   if audit_file   else None
    jha_text     = read_file(jha_file)     if jha_file     else None
    incident_text = read_file(incident_file) if incident_file else None

    # ═══════════════════════════════════════════════════════════════════
    # BLOCK 1 — safety_audit_report.md
    # ═══════════════════════════════════════════════════════════════════

    # 1.1 File exists
    checks.append({
        "name": "audit_file_exists",
        "passed": audit_text is not None,
        "detail": f"Found at {audit_file}" if audit_file else "File safety_audit_report.md not found in workspace"
    })

    if audit_text:
        # 1.2 Hazard Assessment Matrix with severity × probability structure
        has_matrix_header = bool(re.search(
            r'hazard.{0,30}(assessment|matrix|risk)', audit_text, re.IGNORECASE
        ))
        has_severity = bool(re.search(r'severity', audit_text, re.IGNORECASE))
        has_probability = bool(re.search(r'(probability|likelihood)', audit_text, re.IGNORECASE))
        has_risk_score = bool(re.search(r'(risk.{0,10}score|score|rating)', audit_text, re.IGNORECASE))
        has_md_table = bool(re.search(r'\|.+\|.+\|', audit_text))
        checks.append({
            "name": "audit_hazard_matrix_severity_probability",
            "passed": has_matrix_header and has_severity and has_probability and has_risk_score and has_md_table,
            "detail": (
                f"matrix_header={has_matrix_header}, severity={has_severity}, "
                f"probability={has_probability}, risk_score={has_risk_score}, md_table={has_md_table}"
            )
        })

        # 1.3 OSHA Compliance Checklist mapped to 29 CFR 1910 (general industry — manufacturing)
        has_checklist = bool(re.search(r'(compliance.{0,20}checklist|checklist)', audit_text, re.IGNORECASE))
        has_cfr_1910 = bool(re.search(r'29\s*CFR\s*1910', audit_text, re.IGNORECASE))
        has_specific_1910 = bool(re.search(
            r'1910\.(147|178|132|1200|23|119|134|303)',  # LOTO, forklift, PPE, HazCom, walking-working, PS, respiratory, electrical
            audit_text, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_osha_checklist_29cfr1910",
            "passed": has_checklist and has_cfr_1910 and has_specific_1910,
            "detail": (
                f"checklist={has_checklist}, 29CFR1910={has_cfr_1910}, "
                f"specific_subpart={has_specific_1910}"
            )
        })

        # 1.4 Gap Analysis section present
        has_gap = bool(re.search(r'gap.{0,20}(analysis|assessment)', audit_text, re.IGNORECASE))
        # Must reference specific gaps from the input: LOTO missing, HazCom missing
        has_loto_gap = bool(re.search(r'loto|lockout.{0,10}tagout', audit_text, re.IGNORECASE))
        has_hazcom_gap = bool(re.search(r'haz.?com|hazard.{0,15}communication|SDS', audit_text, re.IGNORECASE))
        checks.append({
            "name": "audit_gap_analysis_specific_gaps",
            "passed": has_gap and has_loto_gap and has_hazcom_gap,
            "detail": f"gap_section={has_gap}, loto_gap={has_loto_gap}, hazcom_gap={has_hazcom_gap}"
        })

        # 1.5 Priority Action Plan with ranked items, cost estimates, and timeline
        has_action_plan = bool(re.search(
            r'(priority.{0,20}action|action.{0,20}plan|corrective.{0,20}action)',
            audit_text, re.IGNORECASE
        ))
        has_cost = bool(re.search(r'\$[\d,]+|cost.{0,15}estimate|estimated.{0,15}cost', audit_text, re.IGNORECASE))
        has_timeline = bool(re.search(
            r'(timeline|days|weeks|months|immediate|30.day|60.day|90.day)',
            audit_text, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_priority_action_plan_with_cost_timeline",
            "passed": has_action_plan and has_cost and has_timeline,
            "detail": f"action_plan={has_action_plan}, cost={has_cost}, timeline={has_timeline}"
        })

        # 1.6 Penalty context — must reference dollar figures (shows use of SKILL.md penalty data)
        # $16,131 serious violation or $161,323 willful
        has_penalty = bool(re.search(
            r'\$16[,.]?131|\$161[,.]?323|serious.{0,20}violation|penalty|citation',
            audit_text, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_penalty_figures_or_citation_context",
            "passed": has_penalty,
            "detail": f"penalty_reference={has_penalty} (expected $16,131 or $161,323 or citation/penalty context)"
        })

        # 1.7 References actual plant data (78 employees, manufacturing/metal)
        has_employee_count = bool(re.search(r'78\s*(employee|worker|total)', audit_text, re.IGNORECASE))
        has_industry = bool(re.search(r'(metal.{0,20}fabricat|manufactur)', audit_text, re.IGNORECASE))
        checks.append({
            "name": "audit_reflects_actual_plant_data",
            "passed": has_employee_count and has_industry,
            "detail": f"78_employees={has_employee_count}, industry_context={has_industry}"
        })

    else:
        # File missing — add failed stubs for sub-checks
        for name in [
            "audit_hazard_matrix_severity_probability",
            "audit_osha_checklist_29cfr1910",
            "audit_gap_analysis_specific_gaps",
            "audit_priority_action_plan_with_cost_timeline",
            "audit_penalty_figures_or_citation_context",
            "audit_reflects_actual_plant_data",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Audit file missing"})

    # ═══════════════════════════════════════════════════════════════════
    # BLOCK 2 — forklift_jha.md
    # ═══════════════════════════════════════════════════════════════════

    checks.append({
        "name": "jha_file_exists",
        "passed": jha_text is not None,
        "detail": f"Found at {jha_file}" if jha_file else "File forklift_jha.md not found in workspace"
    })

    if jha_text:
        # 2.1 Task broken into steps
        has_steps = bool(re.search(
            r'(step\s*\d|task\s*step|\d+\.\s+.{5,})',
            jha_text, re.IGNORECASE
        ))
        checks.append({
            "name": "jha_broken_into_steps",
            "passed": has_steps,
            "detail": f"task_steps_found={has_steps}"
        })

        # 2.2 Hazards identified per step
        has_hazard_per_step = bool(re.search(r'hazard', jha_text, re.IGNORECASE))
        has_multiple_hazards = len(re.findall(r'hazard', jha_text, re.IGNORECASE)) >= 3
        checks.append({
            "name": "jha_hazards_identified_per_step",
            "passed": has_hazard_per_step and has_multiple_hazards,
            "detail": f"hazard_mentions={len(re.findall(r'hazard', jha_text, re.IGNORECASE))}"
        })

        # 2.3 Risk rating (severity × likelihood) present
        has_risk_rating = bool(re.search(
            r'(severity.{0,30}(likelihood|probability)|risk.{0,10}(rating|score|level))',
            jha_text, re.IGNORECASE
        ))
        checks.append({
            "name": "jha_risk_rating_severity_x_likelihood",
            "passed": has_risk_rating,
            "detail": f"risk_rating_found={has_risk_rating}"
        })

        # 2.4 Hierarchy of controls — must include elimination AND PPE (not just PPE)
        has_elimination = bool(re.search(r'eliminat', jha_text, re.IGNORECASE))
        has_ppe = bool(re.search(r'\bPPE\b|personal.{0,15}protective', jha_text, re.IGNORECASE))
        has_engineering = bool(re.search(r'engineering.{0,15}control|substitut|isolat', jha_text, re.IGNORECASE))
        has_hierarchy = has_elimination and has_ppe
        checks.append({
            "name": "jha_hierarchy_of_controls_elimination_to_ppe",
            "passed": has_hierarchy,
            "detail": (
                f"elimination={has_elimination}, ppe={has_ppe}, "
                f"engineering_controls={has_engineering}"
            )
        })

        # 2.5 OSHA reference for forklifts (29 CFR 1910.178)
        has_forklift_standard = bool(re.search(
            r'1910\.178|powered.{0,20}(industrial.{0,10}truck|truck)|forklift.{0,20}(standard|regulation|CFR)',
            jha_text, re.IGNORECASE
        ))
        checks.append({
            "name": "jha_references_osha_1910_178_or_forklift_standard",
            "passed": has_forklift_standard,
            "detail": f"forklift_osha_ref={has_forklift_standard}"
        })

        # 2.6 Field-ready format — markdown table present
        has_md_table = bool(re.search(r'\|.+\|.+\|', jha_text))
        checks.append({
            "name": "jha_field_ready_markdown_table",
            "passed": has_md_table,
            "detail": f"markdown_table={has_md_table}"
        })

    else:
        for name in [
            "jha_broken_into_steps",
            "jha_hazards_identified_per_step",
            "jha_risk_rating_severity_x_likelihood",
            "jha_hierarchy_of_controls_elimination_to_ppe",
            "jha_references_osha_1910_178_or_forklift_standard",
            "jha_field_ready_markdown_table",
        ]:
            checks.append({"name": name, "passed": False, "detail": "JHA file missing"})

    # ═══════════════════════════════════════════════════════════════════
    # BLOCK 3 — incident_report.md
    # ═══════════════════════════════════════════════════════════════════

    checks.append({
        "name": "incident_report_file_exists",
        "passed": incident_text is not None,
        "detail": f"Found at {incident_file}" if incident_file else "File incident_report.md not found in workspace"
    })

    if incident_text:
        # 3.1 Structured header: date, time, location, personnel
        has_date = bool(re.search(r'(date|june\s*3|2024-06-03|june.{0,5}2024)', incident_text, re.IGNORECASE))
        has_time = bool(re.search(r'(time|10:22|10\.22)', incident_text, re.IGNORECASE))
        has_location = bool(re.search(r'(aisle\s*7|warehouse|location)', incident_text, re.IGNORECASE))
        has_personnel = bool(re.search(r'(mendez|brown|personnel|employee\s*involved)', incident_text, re.IGNORECASE))
        checks.append({
            "name": "incident_report_structured_header_details",
            "passed": has_date and has_time and has_location and has_personnel,
            "detail": f"date={has_date}, time={has_time}, location={has_location}, personnel={has_personnel}"
        })

        # 3.2 Incident classification — must be "near miss" (correct per skill)
        has_near_miss = bool(re.search(r'near.?miss', incident_text, re.IGNORECASE))
        checks.append({
            "name": "incident_report_correct_classification_near_miss",
            "passed": has_near_miss,
            "detail": f"near_miss_classification={has_near_miss}"
        })

        # 3.3 Root cause analysis — 5 Whys (must appear)
        has_5whys = bool(re.search(r'5.?why|five.?why|why\s*#?\s*[1-5]', incident_text, re.IGNORECASE))
        checks.append({
            "name": "incident_report_5_whys_root_cause",
            "passed": has_5whys,
            "detail": f"5_whys_present={has_5whys}"
        })

        # 3.4 Fishbone diagram prompts / categories (cause categories expected)
        has_fishbone = bool(re.search(
            r'(fishbone|cause.{0,20}(diagram|category)|ishikawa|man|machine|method|material|environment)',
            incident_text, re.IGNORECASE
        ))
        checks.append({
            "name": "incident_report_fishbone_diagram_prompts",
            "passed": has_fishbone,
            "detail": f"fishbone_present={has_fishbone}"
        })

        # 3.5 Corrective actions with owner + deadline
        has_corrective = bool(re.search(r'corrective.{0,20}action', incident_text, re.IGNORECASE))
        has_owner = bool(re.search(r'(owner|responsible|assigned.{0,10}to)', incident_text, re.IGNORECASE))
        has_deadline = bool(re.search(
            r'(deadline|due.{0,10}date|by\s+\w+\s+\d{4}|complete.{0,15}by)',
            incident_text, re.IGNORECASE
        ))
        checks.append({
            "name": "incident_report_corrective_actions_with_owner_deadline",
            "passed": has_corrective and has_owner and has_deadline,
            "detail": f"corrective={has_corrective}, owner={has_owner}, deadline={has_deadline}"
        })

        # 3.6 OSHA 300 log guidance — must mention OSHA 300 log
        has_osha300 = bool(re.search(r'osha.{0,10}300|300\s*log|recordkeeping|29\s*CFR\s*1904', incident_text, re.IGNORECASE))
        checks.append({
            "name": "incident_report_osha_300_log_guidance",
            "passed": has_osha300,
            "detail": f"osha_300_ref={has_osha300}"
        })

        # 3.7 Near-miss correctly noted as NOT OSHA 300 recordable
        # Per OSHA, near-miss is not recordable; the agent should note this
        not_recordable_noted = bool(re.search(
            r'(not.{0,20}record|near.?miss.{0,60}(not|no).{0,20}record|record.{0,30}not.{0,20}required)',
            incident_text, re.IGNORECASE
        ))
        checks.append({
            "name": "incident_report_near_miss_not_osha_recordable",
            "passed": not_recordable_noted,
            "detail": (
                f"near_miss_not_recordable_noted={not_recordable_noted}. "
                "Expected statement that near-miss is not OSHA 300 recordable."
            )
        })

    else:
        for name in [
            "incident_report_structured_header_details",
            "incident_report_correct_classification_near_miss",
            "incident_report_5_whys_root_cause",
            "incident_report_fishbone_diagram_prompts",
            "incident_report_corrective_actions_with_owner_deadline",
            "incident_report_osha_300_log_guidance",
            "incident_report_near_miss_not_osha_recordable",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Incident report file missing"})

    # ─── Final scoring ────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= int(total * 0.80)  # 80% threshold to pass

    result = {
        "passed": overall_passed,
        "score": score_checks(checks),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()