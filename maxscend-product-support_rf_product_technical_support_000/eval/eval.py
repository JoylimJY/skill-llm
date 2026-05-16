import sys
import json
import math
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Locate the output file ────────────────────────────────────────
    report_files = list(workspace.rglob("feasibility_report.json"))
    
    if not report_files:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "feasibility_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = report_files[0]
    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found at {report_path}"})
    total_score += 0.1

    # ── Parse JSON ───────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False,
                        "detail": f"Failed to parse JSON: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}
    
    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})
    total_score += 0.05

    # ── CHECK 1: Antenna Switch Selection ─────────────────────────────
    # Must select MXD8641 (SP4T, 0.1-6GHz, IL<0.5dB)
    # NOT MXD8651 (SP6T), NOT MXD8621 (DPDT), NOT MXD8661 (SP8T)
    # Requirement: SP4T type, IL<=0.5dB
    try:
        report_str = json.dumps(report).upper()
        switch_correct = "MXD8641" in report_str
        # Penalize if wrong switch models are selected as primary
        wrong_switches = any(m in report_str for m in ["MXD8651", "MXD8661", "MXD8681"])
        switch_passed = switch_correct and not wrong_switches
        checks.append({
            "name": "switch_selection_MXD8641",
            "passed": switch_passed,
            "detail": f"MXD8641 present: {switch_correct}; Wrong switch models present: {wrong_switches}. "
                      f"Requirement: SP4T with IL<0.5dB for n77/n78 band. MXD8641 is the only SP4T meeting IL<0.5dB."
        })
        if switch_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "switch_selection_MXD8641", "passed": False, "detail": str(e)})

    # ── CHECK 2: LNA Selection ────────────────────────────────────────
    # Must select MXD1805 (3.3-4.2GHz, NF=1.2dB, Gain=15dB) for n77/n78
    # NOT MXD1803 (2.3-2.7GHz - wrong band), NOT MXD1802, NOT MXD1810 (wideband but NF=1.5dB)
    try:
        lna_correct = "MXD1805" in report_str
        wrong_lnas = any(m in report_str for m in ["MXD1801", "MXD1802", "MXD1803"])
        lna_passed = lna_correct  # MXD1810 is acceptable as wideband alternative but 1805 is optimal
        checks.append({
            "name": "lna_selection_MXD1805",
            "passed": lna_passed,
            "detail": f"MXD1805 present: {lna_correct}; Wrong-band LNA models (1801/1802/1803) present: {wrong_lnas}. "
                      f"MXD1805 covers 3.3-4.2GHz which exactly matches n77/n78 requirement."
        })
        if lna_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "lna_selection_MXD1805", "passed": False, "detail": str(e)})

    # ── CHECK 3: BAW Filter Selection ─────────────────────────────────
    # Must select MXF2201 (BAW, 3.5GHz, n78) 
    # NOT SAW filters (MXF2101/2102/2103 - wrong frequencies for 5G n78)
    try:
        filter_correct = "MXF2201" in report_str
        wrong_filters = any(m in report_str for m in ["MXF2101", "MXF2102", "MXF2103"])
        filter_passed = filter_correct and not wrong_filters
        checks.append({
            "name": "filter_selection_MXF2201",
            "passed": filter_passed,
            "detail": f"MXF2201 present: {filter_correct}; Wrong filters (SAW 2101/2102/2103) present: {wrong_filters}. "
                      f"MXF2201 is BAW at 3.5GHz for 5G n78 - correct choice."
        })
        if filter_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "filter_selection_MXF2201", "passed": False, "detail": str(e)})

    # ── CHECK 4: Cascade NF Calculation ───────────────────────────────
    # Chain: Antenna → MXD8641 (IL=0.5dB, attenuator, NF=0.5dB, gain=-0.5dB)
    #        → MXF2201 (IL=1.5dB, NF=1.5dB, gain=-1.5dB)
    #        → MXD1805 LNA (NF=1.2dB, Gain=15dB)
    #
    # Friis formula (linear):
    # Stage 1: Switch, NF1=0.5dB → F1=10^(0.5/10)=1.1220, G1=10^(-0.5/10)=0.8913
    # Stage 2: Filter, NF2=1.5dB → F2=10^(1.5/10)=1.4125, G2=10^(-1.5/10)=0.7079
    # Stage 3: LNA,    NF3=1.2dB → F3=10^(1.2/10)=1.3183, G3=10^(15/10)=31.623
    #
    # F_total = F1 + (F2-1)/G1 + (F3-1)/(G1*G2)
    # F1 = 1.1220
    # (F2-1)/G1 = 0.4125/0.8913 = 0.4628
    # (F3-1)/(G1*G2) = 0.3183/(0.8913*0.7079) = 0.3183/0.6310 = 0.5044
    # F_total = 1.1220 + 0.4628 + 0.5044 = 2.0892
    # NF_total = 10*log10(2.0892) = 3.20 dB
    #
    # This is BELOW 3.5dB requirement → PASSES
    
    try:
        # Compute expected value
        nf_switch_db = 0.5
        g_switch_db = -0.5
        nf_filter_db = 1.5
        g_filter_db = -1.5
        nf_lna_db = 1.2
        g_lna_db = 15.0

        F1 = 10 ** (nf_switch_db / 10)
        G1 = 10 ** (g_switch_db / 10)
        F2 = 10 ** (nf_filter_db / 10)
        G2 = 10 ** (g_filter_db / 10)
        F3 = 10 ** (nf_lna_db / 10)

        F_total = F1 + (F2 - 1) / G1 + (F3 - 1) / (G1 * G2)
        expected_nf_db = 10 * math.log10(F_total)
        # expected ~3.20 dB

        # Find cascade_nf in report
        nf_value = None
        def find_nf(obj, depth=0):
            if depth > 10:
                return None
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(kw in k.lower() for kw in ["cascade_nf", "nf_db", "noise_figure", "cascade_noise", "total_nf", "system_nf"]):
                        try:
                            return float(v)
                        except:
                            pass
                    result = find_nf(v, depth+1)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_nf(item, depth+1)
                    if result is not None:
                        return result
            return None

        nf_value = find_nf(report)

        tolerance = 0.5  # Allow ±0.5dB tolerance for different rounding approaches
        if nf_value is not None:
            nf_close = abs(nf_value - expected_nf_db) <= tolerance
            checks.append({
                "name": "cascade_nf_calculation",
                "passed": nf_close,
                "detail": f"Reported NF: {nf_value:.3f} dB, Expected (Friis): {expected_nf_db:.3f} dB "
                          f"(Switch IL=0.5dB + Filter IL=1.5dB + LNA NF=1.2dB/Gain=15dB). "
                          f"Tolerance ±{tolerance}dB. {'PASS' if nf_close else 'FAIL'}"
            })
            if nf_close:
                total_score += 0.15
        else:
            checks.append({
                "name": "cascade_nf_calculation",
                "passed": False,
                "detail": f"Could not find cascade NF value in report. Expected ~{expected_nf_db:.3f} dB. "
                          f"Look for keys like 'cascade_nf_db', 'total_nf', etc."
            })
    except Exception as e:
        checks.append({"name": "cascade_nf_calculation", "passed": False, "detail": str(e)})

    # ── CHECK 5: passes_requirement field ────────────────────────────
    # Cascade NF ~3.20dB < 3.5dB budget → should PASS
    try:
        def find_passes(obj, depth=0):
            if depth > 10:
                return None
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(kw in k.lower() for kw in ["passes", "pass", "meets", "compliant", "feasible"]):
                        if isinstance(v, bool):
                            return v
                        if isinstance(v, str):
                            return v.lower() in ["true", "yes", "pass", "passes"]
                    result = find_passes(v, depth+1)
                    if result is not None:
                        return result
            return None

        passes_val = find_passes(report)
        requirement_met = passes_val is True
        checks.append({
            "name": "passes_nf_requirement",
            "passed": requirement_met,
            "detail": f"Report indicates passes_requirement={passes_val}. "
                      f"Expected: True (cascade NF ~3.20dB < 3.5dB budget). "
                      f"{'PASS' if requirement_met else 'FAIL - should be True/passes'}"
        })
        if requirement_met:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "passes_nf_requirement", "passed": False, "detail": str(e)})

    # ── CHECK 6: Fault Diagnosis - Input Matching ──────────────────────
    # From SKILL.md FAQ Q2 (LNA NF超标): 
    # Step 1: 测量输入匹配（应接近最佳噪声匹配点）
    # Step 4: 评估输入走线长度  (test log: 18mm input trace - too long)
    # Step 2: 检查供电纹波 (test log: supply voltage droop 2.85V vs 3.0V)
    # Step 3: 确认接地过孔数量 (test log: only 3 vias - insufficient)
    try:
        report_lower = json.dumps(report).lower()
        
        # Must mention input matching issue
        input_matching_mentioned = any(kw in report_lower for kw in [
            "input match", "input_match", "noise match", "输入匹配", "noise matching",
            "匹配", "match"
        ])
        # Must mention supply voltage / ripple
        supply_mentioned = any(kw in report_lower for kw in [
            "supply", "voltage", "power", "ripple", "纹波", "供电", "droop", "vcc"
        ])
        # Must mention ground vias
        via_mentioned = any(kw in report_lower for kw in [
            "via", "ground", "gnd", "接地", "过孔"
        ])
        # Must mention input trace length
        trace_mentioned = any(kw in report_lower for kw in [
            "trace", "走线", "input trace", "trace length", "routing"
        ])
        
        fault_checks_passed = sum([input_matching_mentioned, supply_mentioned, via_mentioned, trace_mentioned])
        fault_passed = fault_checks_passed >= 3  # At least 3 of 4 fault factors mentioned
        
        checks.append({
            "name": "fault_diagnosis_completeness",
            "passed": fault_passed,
            "detail": f"Fault factors identified (need ≥3 of 4): "
                      f"input_matching={input_matching_mentioned}, "
                      f"supply_voltage={supply_mentioned}, "
                      f"ground_vias={via_mentioned}, "
                      f"trace_length={trace_mentioned}. "
                      f"Score: {fault_checks_passed}/4. "
                      f"Based on SKILL.md FAQ Q2 NF troubleshooting checklist."
        })
        if fault_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "fault_diagnosis_completeness", "passed": False, "detail": str(e)})

    # ── CHECK 7: Output return loss issue noted ────────────────────────
    # Test log shows LNA output return loss -8.1dB (worse than -10dB target)
    # SKILL.md design point: output matching target <-10dB
    try:
        report_lower = json.dumps(report).lower()
        output_match_mentioned = any(kw in report_lower for kw in [
            "output match", "output return", "return loss", "s22", "output rl",
            "输出匹配", "输出回波"
        ])
        checks.append({
            "name": "output_matching_issue_identified",
            "passed": output_match_mentioned,
            "detail": f"Output return loss issue mentioned: {output_match_mentioned}. "
                      f"Test log shows LNA output RL = -8.1dB, worse than -10dB SKILL.md target. "
                      f"SKILL.md 2.2 design point: output return loss < -10dB."
        })
        if output_match_mentioned:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "output_matching_issue_identified", "passed": False, "detail": str(e)})

    # ── Final determination ───────────────────────────────────────────
    critical_checks = [
        "switch_selection_MXD8641",
        "lna_selection_MXD1805",
        "filter_selection_MXF2201",
        "cascade_nf_calculation",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    critical_passed = all(critical_results.get(c, False) for c in critical_checks)

    final_passed = critical_passed and total_score >= 0.6

    return {
        "passed": final_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                       "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))