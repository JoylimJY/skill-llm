import sys
import json
import os
import re
from pathlib import Path

def load_result_file(workspace):
    """Find the diagnostic output JSON file."""
    candidates = list(Path(workspace).rglob("trading_pipeline_diagnostic.json"))
    if not candidates:
        # Also accept alternate reasonable names with diagnostic in them
        candidates = list(Path(workspace).rglob("*diagnostic*.json"))
    if not candidates:
        candidates = list(Path(workspace).rglob("*bullwhip*.json"))
    return candidates[0] if candidates else None

def run_eval(workspace):
    checks = []
    total_score = 0.0

    # --- Find output file ---
    result_file = load_result_file(workspace)
    file_found = result_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found: {result_file}" if file_found else "No diagnostic JSON file found. Expected 'trading_pipeline_diagnostic.json'."
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # --- Parse JSON ---
    try:
        with open(result_file) as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File parses as valid JSON."})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # --- Check 1: skill and version fields ---
    skill_ok = data.get("skill") == "cognitive-bullwhip"
    version_ok = data.get("version") == "1.0"
    checks.append({
        "name": "skill_version_fields",
        "passed": skill_ok and version_ok,
        "detail": f"skill='{data.get('skill')}', version='{data.get('version')}'. Expected skill='cognitive-bullwhip', version='1.0'."
    })

    # --- Check 2: bullwhip_active must be True ---
    bullwhip_active = data.get("bullwhip_active")
    ba_ok = bullwhip_active is True
    checks.append({
        "name": "bullwhip_active_true",
        "passed": ba_ok,
        "detail": f"bullwhip_active={bullwhip_active}. Must be True (amplification ratio >3.0 confirmed in data)."
    })

    # --- Check 3: severity must be 'high' or 'critical' (score >70), severity_score must be >=71 ---
    severity = data.get("severity", "")
    severity_score = data.get("severity_score", 0)
    sev_ok = severity in ("high", "critical") and isinstance(severity_score, (int, float)) and severity_score >= 71
    checks.append({
        "name": "severity_and_score",
        "passed": sev_ok,
        "detail": f"severity='{severity}', severity_score={severity_score}. Expected severity in ['high','critical'] and score>=71."
    })

    # --- Check 4: origin_layer must be 'reasoning' ---
    try:
        origin_layer = data["amplification_map"]["origin_layer"]
        origin_ok = origin_layer == "reasoning"
    except (KeyError, TypeError):
        origin_layer = None
        origin_ok = False
    checks.append({
        "name": "origin_layer_reasoning",
        "passed": origin_ok,
        "detail": f"origin_layer='{origin_layer}'. Must be 'reasoning' — first amplification >3x occurred at reasoning layer."
    })

    # --- Check 5: amplification_chain present and reasoning layer ratio > 3.0 ---
    try:
        chain = data["amplification_map"]["amplification_chain"]
        chain_ok = isinstance(chain, list) and len(chain) >= 1
        reasoning_ratio_ok = False
        max_ratio = 0.0
        for entry in chain:
            if entry.get("layer") in ("reasoning", "reasoning_engine", "reasoning layer"):
                ratio = entry.get("amplification_ratio", 0.0)
                if isinstance(ratio, (int, float)) and ratio > 3.0:
                    reasoning_ratio_ok = True
                    max_ratio = max(max_ratio, ratio)
        # Also accept if any layer named reasoning has ratio >3.0
        if not reasoning_ratio_ok:
            for entry in chain:
                ratio = entry.get("amplification_ratio", 0.0)
                if isinstance(ratio, (int, float)) and ratio > 3.0:
                    reasoning_ratio_ok = True  # at least one layer >3.0 confirms bullwhip
                    max_ratio = max(max_ratio, ratio)
    except (KeyError, TypeError):
        chain_ok = False
        reasoning_ratio_ok = False
        max_ratio = 0.0
    checks.append({
        "name": "amplification_chain_ratio_exceeds_threshold",
        "passed": chain_ok and reasoning_ratio_ok,
        "detail": f"chain_present={chain_ok}, at least one ratio>3.0={reasoning_ratio_ok}, max_ratio_found={max_ratio:.2f}. The proprietary threshold is ratio>3.0 to confirm bullwhip."
    })

    # --- Check 6: pattern_type must be 'reasoning_drift' (reasoning layer origin) ---
    pattern_type = data.get("pattern_type", "")
    pt_ok = pattern_type == "reasoning_drift"
    checks.append({
        "name": "pattern_type_reasoning_drift",
        "passed": pt_ok,
        "detail": f"pattern_type='{pattern_type}'. Reasoning layer origin → must be 'reasoning_drift'."
    })

    # --- Check 7: primary_skill must be 'logic-stack' ---
    try:
        primary_skill = data["recommended_intervention"]["primary_skill"]
        ps_ok = primary_skill == "logic-stack"
    except (KeyError, TypeError):
        primary_skill = None
        ps_ok = False
    checks.append({
        "name": "primary_skill_logic_stack",
        "passed": ps_ok,
        "detail": f"primary_skill='{primary_skill}'. reasoning_drift → must recommend 'logic-stack'."
    })

    # --- Check 8: urgency must be 'immediate' (severity_score > 70) ---
    try:
        urgency = data["recommended_intervention"]["urgency"]
        urg_ok = urgency == "immediate"
    except (KeyError, TypeError):
        urgency = None
        urg_ok = False
    checks.append({
        "name": "urgency_immediate",
        "passed": urg_ok,
        "detail": f"urgency='{urgency}'. severity_score>70 → urgency must be 'immediate'."
    })

    # --- Check 9: get_skill link present ---
    try:
        get_skill = data["recommended_intervention"]["get_skill"]
        link_ok = "agdp.io" in str(get_skill)
    except (KeyError, TypeError):
        get_skill = None
        link_ok = False
    checks.append({
        "name": "get_skill_link_present",
        "passed": link_ok,
        "detail": f"get_skill='{get_skill}'. Must contain agdp.io link."
    })

    # --- Check 10: available_skills array present with all 4 skills ---
    try:
        avail = data["recommended_intervention"]["available_skills"]
        avail_names = {s.get("name", "") for s in avail}
        required_skills = {"SignalAnchor", "LogicStack", "CausalMesh", "PrincipleGate"}
        avail_ok = required_skills.issubset(avail_names)
    except (KeyError, TypeError):
        avail = None
        avail_ok = False
        avail_names = set()
    checks.append({
        "name": "available_skills_all_four_present",
        "passed": avail_ok,
        "detail": f"Found skills: {avail_names}. Required: {{'SignalAnchor','LogicStack','CausalMesh','PrincipleGate'}}."
    })

    # --- Check 11: trace array has 3 steps ---
    try:
        trace = data.get("trace", [])
        trace_steps = [t.get("step", "") for t in trace]
        trace_ok = (
            len(trace) >= 3 and
            "variance_scan" in trace_steps and
            "origin_trace" in trace_steps and
            "pattern_classification" in trace_steps
        )
    except Exception:
        trace_ok = False
    checks.append({
        "name": "trace_has_three_required_steps",
        "passed": trace_ok,
        "detail": f"Trace steps found: {trace_steps if 'trace_steps' in dir() else 'none'}. Required: variance_scan, origin_trace, pattern_classification."
    })

    # --- Check 12: diagnostic_report field exists in JSON and is a string ---
    diag_report = data.get("diagnostic_report", None)
    dr_exists = isinstance(diag_report, str) and len(diag_report) > 100
    checks.append({
        "name": "diagnostic_report_field_in_json",
        "passed": dr_exists,
        "detail": f"diagnostic_report is a string field in JSON: {dr_exists}. Length: {len(diag_report) if isinstance(diag_report,str) else 'N/A'}."
    })

    # --- Check 13: diagnostic_report contains required sections ---
    if dr_exists:
        report = diag_report
        required_sections = [
            "COGNITIVE BULLWHIP DIAGNOSTIC",
            "Status:",
            "Origin:",
            "Ratio:",
            "Confidence:",
            "Impact Forecast",
            "Recommended Actions",
            "Logic Trace",
            "VARIANCE SCAN",
            "ORIGIN TRACE",
            "PATTERN CLASSIFICATION",
            "FIX IT NOW",
            "SignalAnchor",
            "LogicStack",
            "CausalMesh",
            "PrincipleGate",
            "agdp.io",
            "-----"
        ]
        missing_sections = [s for s in required_sections if s not in report]
        dr_sections_ok = len(missing_sections) == 0
        checks.append({
            "name": "diagnostic_report_all_sections_present",
            "passed": dr_sections_ok,
            "detail": f"Missing sections from diagnostic_report: {missing_sections if missing_sections else 'None — all present'}."
        })

        # --- Check 14: report mentions reasoning or reasoning_drift ---
        reasoning_mention = "reasoning" in report.lower()
        reasoning_drift_mention = "reasoning_drift" in report or "reasoning drift" in report.lower()
        rd_ok = reasoning_mention and reasoning_drift_mention
        checks.append({
            "name": "diagnostic_report_mentions_reasoning_drift",
            "passed": rd_ok,
            "detail": f"Report mentions 'reasoning': {reasoning_mention}, 'reasoning_drift': {reasoning_drift_mention}."
        })

        # --- Check 15: report mentions LogicStack ---
        logicstack_ok = "LogicStack" in report or "logic-stack" in report.lower()
        checks.append({
            "name": "diagnostic_report_recommends_logicstack",
            "passed": logicstack_ok,
            "detail": f"LogicStack mentioned in diagnostic_report: {logicstack_ok}."
        })

        # --- Check 16: report uses dash dividers (proprietary format) ---
        dash_ok = "-----" in report
        checks.append({
            "name": "diagnostic_report_dash_dividers",
            "passed": dash_ok,
            "detail": f"Dash dividers (-----) present in report: {dash_ok}. This is the mandatory proprietary format."
        })
    else:
        checks.append({"name": "diagnostic_report_all_sections_present", "passed": False, "detail": "diagnostic_report field missing or empty — cannot check sections."})
        checks.append({"name": "diagnostic_report_mentions_reasoning_drift", "passed": False, "detail": "diagnostic_report field missing."})
        checks.append({"name": "diagnostic_report_recommends_logicstack", "passed": False, "detail": "diagnostic_report field missing."})
        checks.append({"name": "diagnostic_report_dash_dividers", "passed": False, "detail": "diagnostic_report field missing."})

    # --- Check 17: observation_window reflected (last_24h) ---
    try:
        obs_ok = False
        for t in data.get("trace", []):
            if "last_24h" in str(t.get("result", "")) or "24h" in str(t.get("result", "")):
                obs_ok = True
        if not obs_ok and isinstance(diag_report, str):
            obs_ok = "last_24h" in diag_report or "24h" in diag_report
    except Exception:
        obs_ok = False
    checks.append({
        "name": "observation_window_reflected",
        "passed": obs_ok,
        "detail": f"Observation window 'last_24h' from system_context reflected in output: {obs_ok}."
    })

    # --- Scoring ---
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = len(passed_checks) / total_checks

    # Critical checks that must pass for overall pass
    critical_checks = [
        "bullwhip_active_true",
        "origin_layer_reasoning",
        "pattern_type_reasoning_drift",
        "primary_skill_logic_stack",
        "urgency_immediate",
        "diagnostic_report_field_in_json",
        "diagnostic_report_all_sections_present",
        "amplification_chain_ratio_exceeds_threshold",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)