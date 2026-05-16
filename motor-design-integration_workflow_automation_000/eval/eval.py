import sys
import json
import re
import math
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ── Locate the report file ────────────────────────────────────────────
    report_files = list(workspace.rglob("motor_design_report.md"))
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_exists", "passed": False,
                        "detail": "motor_design_report.md not found anywhere in workspace"}]
        }

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_readable", "passed": False,
                        "detail": f"Cannot read report: {e}"}]
        }

    content_lower = content.lower()

    # ─────────────────────────────────────────────────────────────────────
    # DERIVED REFERENCE VALUES (from SKILL.md formulas applied to the spec)
    # Spec: P=350W, n=2500rpm, Vdc=36V, I=11.2A
    # ─────────────────────────────────────────────────────────────────────

    # === CHECK 1: Valid pole-slot selection ==============================
    # Spec: n=2500 rpm → falls in 1000~3000 rpm band → 6-pole recommended,
    # but 8-pole is also acceptable per the table.
    # Valid combos per rules: Q>=2p, q>=1, Q/2p != integer preferred
    # From CSV candidates, valid & fitting speed band:
    #   B: 2p=6, Q=18, q=18/(6*3)=1.0 ✅, Q/2p=3 integer (ok, just not optimal)
    #   C: 2p=8, Q=36, q=36/(8*3)=1.5 ✅, Q/2p=4.5 non-integer ✅ (best)
    #   D: 2p=8, Q=24, q=24/(8*3)=1.0 ✅, Q/2p=3 integer
    #   G: 2p=6, Q=36, q=36/(6*3)=2.0 ✅, Q/2p=6 integer
    #   H: 2p=8, Q=48, q=48/(8*3)=2.0 ✅, Q/2p=6 integer
    # The BEST choice per SKILL.md rules is C (8p36s): non-integer Q/2p, good speed match
    # We accept C as the target but also accept B, D, G, H if validly justified.
    # We check for the SPECIFIC SKILL.MD Kw value for 8p36s: Kw=0.933

    def check_pole_slot(text):
        # Must mention poles and slots
        has_8pole = bool(re.search(r'8\s*[极pole]|2p\s*=\s*8|poles?\s*[=:]\s*8|极数.*8', text, re.IGNORECASE))
        has_36slot = bool(re.search(r'36\s*[槽slot]|Q\s*=\s*36|slots?\s*[=:]\s*36|槽数.*36', text, re.IGNORECASE))
        has_q15 = bool(re.search(r'q\s*=\s*1\.5|每极每相.*1\.5|1\.5.*槽', text, re.IGNORECASE))
        # Kw=0.933 is the canonical value from SKILL.md for 8p36s
        has_kw = bool(re.search(r'k[wd]\s*=?\s*0\.93[0-9]|0\.933|绕组系数.*0\.93', text, re.IGNORECASE))
        return has_8pole, has_36slot, has_q15, has_kw

    has_8p, has_36s, has_q15, has_kw = check_pole_slot(content)

    checks.append({
        "name": "pole_slot_8p36s_selected",
        "passed": has_8p and has_36s,
        "detail": f"8-pole: {has_8p}, 36-slot: {has_36s}. Must select 8p36s configuration."
    })
    checks.append({
        "name": "q_value_1p5_correct",
        "passed": has_q15,
        "detail": f"q=1.5 present: {has_q15}. q=Q/(2p*m)=36/(8*3)=1.5 required."
    })
    checks.append({
        "name": "winding_factor_kw_0p933",
        "passed": has_kw,
        "detail": f"Kw=0.933 present: {has_kw}. This is the SKILL.md canonical value for 8p36s."
    })

    # === CHECK 2: Magnetic circuit results ================================
    # Spec: Br=1.22T, hm=3.5mm, delta=0.6mm
    # Simple MEC: Bg ≈ Br * hm / (hm + Kc*delta) with Kc~1.15
    # Bg ≈ 1.22 * 3.5 / (3.5 + 1.15*0.6) = 1.22 * 3.5 / (3.5 + 0.69) = 4.27/4.19 ≈ 1.02
    # More refined with leakage sigma=0.12: Bg = Br * (1-sigma) * hm / (hm + Kc*delta)
    # = 1.22 * 0.88 * 3.5 / 4.19 = 1.073 * 3.5 / 4.19 ≈ 0.896 T
    # Accept Bg in range 0.70~1.00T as per SKILL.MD checklist
    # Working point Bm/Br must be reported > 55%

    def extract_float_after_pattern(text, pattern, group=1):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(group))
            except:
                return None
        return None

    # Look for Bg value
    bg_val = extract_float_after_pattern(content, r'Bg\s*[=:≈]\s*([0-9]+\.[0-9]+)\s*T')
    bg_ok = bg_val is not None and 0.65 <= bg_val <= 1.05

    checks.append({
        "name": "air_gap_flux_density_Bg_in_range",
        "passed": bg_ok,
        "detail": f"Bg extracted: {bg_val} T. Must be 0.7~1.0T per SKILL.MD checklist (tolerance ±0.05)."
    })

    # Bm/Br working point > 55%
    bmbr_val = None
    bmbr_match = re.search(r'Bm/Br\s*[=:≈]\s*([0-9]+(?:\.[0-9]+)?)\s*%', content, re.IGNORECASE)
    if not bmbr_match:
        # Also accept decimal form like 0.62
        bmbr_match2 = re.search(r'Bm/Br\s*[=:≈]\s*(0\.[5-9][0-9]*)', content, re.IGNORECASE)
        if bmbr_match2:
            bmbr_val = float(bmbr_match2.group(1)) * 100
    else:
        bmbr_val = float(bmbr_match.group(1))

    bmbr_ok = bmbr_val is not None and bmbr_val > 55.0

    checks.append({
        "name": "working_point_BmBr_above_55pct",
        "passed": bmbr_ok,
        "detail": f"Bm/Br extracted: {bmbr_val}%. Must be > 55% to avoid demagnetization risk."
    })

    # Ke voltage margin check: Ke < 0.9 * Vdc = 0.9 * 36 = 32.4V
    ke_line = re.search(r'Ke\s*[=:≈]\s*([0-9]+(?:\.[0-9]+)?)\s*V', content, re.IGNORECASE)
    ke_val = float(ke_line.group(1)) if ke_line else None
    ke_ok = ke_val is not None and ke_val < 32.4

    checks.append({
        "name": "ke_voltage_margin_check",
        "passed": ke_ok,
        "detail": f"Ke extracted: {ke_val} V. Must be < 0.9×36 = 32.4V per SKILL.MD checklist."
    })

    # === CHECK 3: FOC Parameters — Temperature Correction ================
    # SKILL.MD: copper +0.4%/℃, so R_T = R × (1 + 0.004 × (T - 20))
    # Spec: R=0.38Ω, target T=85℃
    # R_85 = 0.38 × (1 + 0.004 × (85-20)) = 0.38 × (1 + 0.26) = 0.38 × 1.26 = 0.4788 Ω
    # SKILL.MD template uses R_75℃ = R × 1.22 as example, but 85℃ is the spec max temp
    # We check for R_85 ≈ 0.479 Ω (within ±0.015 tolerance)
    # Also accept if they compute at 75C: R_75 = 0.38 * (1 + 0.004*55) = 0.38 * 1.22 = 0.4636 Ω

    R_20 = 0.38
    T_max = 85
    T_ref = 20
    # SKILL.MD formula: +0.4%/℃
    R_corrected_85 = R_20 * (1 + 0.004 * (T_max - T_ref))  # = 0.4788
    R_corrected_75 = R_20 * (1 + 0.004 * 55)               # = 0.4636

    r_hot_match = re.search(
        r'R[_\s]*(75|85|hot|max|temp)[_\s℃°C]*\s*[=:≈]\s*([0-9]+\.[0-9]+)\s*[ΩΩohm]',
        content, re.IGNORECASE
    )
    r_hot_val = float(r_hot_match.group(2)) if r_hot_match else None

    # Also scan for any value near 0.479 or 0.464 in FOC section
    if r_hot_val is None:
        r_candidates = re.findall(r'0\.[4-5][0-9]{1,3}', content)
        for rc in r_candidates:
            rv = float(rc)
            if abs(rv - R_corrected_85) < 0.02 or abs(rv - R_corrected_75) < 0.02:
                r_hot_val = rv
                break

    temp_corr_ok = (r_hot_val is not None and
                    (abs(r_hot_val - R_corrected_85) < 0.025 or
                     abs(r_hot_val - R_corrected_75) < 0.025))

    checks.append({
        "name": "temperature_corrected_resistance_correct",
        "passed": temp_corr_ok,
        "detail": (
            f"Extracted R_hot: {r_hot_val} Ω. "
            f"Expected R@85℃={R_corrected_85:.4f}Ω or R@75℃={R_corrected_75:.4f}Ω "
            f"using SKILL.MD copper +0.4%/℃ formula."
        )
    })

    # === CHECK 4: Current loop bandwidth = R/L × 0.5 =====================
    # Spec: R=0.38Ω, L=4.2mH (using Ld as conservative)
    # bw_current = (R / L) * 0.5 = (0.38 / 0.0042) * 0.5 = 90.48 * 0.5 = 45.24 Hz
    # Use Lq=4.8mH: bw = (0.38/0.0048)*0.5 = 79.17*0.5 = 39.58 Hz
    # Accept 38~47 Hz (covers both Ld and Lq choices)

    R_val = 0.38
    Ld_val = 4.2e-3
    Lq_val = 4.8e-3
    bw_curr_Ld = (R_val / Ld_val) * 0.5
    bw_curr_Lq = (R_val / Lq_val) * 0.5

    bw_curr_match = re.search(
        r'(?:电流环.*?带宽|current.*?bandwidth|bw_curr|i[_-]loop.*?bw)\s*[=:≈~]*\s*([0-9]+(?:\.[0-9]+)?)\s*Hz',
        content, re.IGNORECASE
    )
    bw_curr_val = float(bw_curr_match.group(1)) if bw_curr_match else None

    # Broader scan
    if bw_curr_val is None:
        bw_candidates = re.findall(r'([0-9]+(?:\.[0-9]+)?)\s*Hz', content)
        for bc in bw_candidates:
            bv = float(bc)
            if 35.0 <= bv <= 50.0:
                bw_curr_val = bv
                break

    bw_curr_ok = (bw_curr_val is not None and 35.0 <= bw_curr_val <= 50.0)

    checks.append({
        "name": "current_loop_bandwidth_correct",
        "passed": bw_curr_ok,
        "detail": (
            f"Extracted current loop BW: {bw_curr_val} Hz. "
            f"Expected ~{bw_curr_Ld:.1f}Hz (Ld) or ~{bw_curr_Lq:.1f}Hz (Lq) "
            f"using SKILL.MD formula: R/L × 0.5."
        )
    })

    # === CHECK 5: Speed loop bandwidth = current loop / 10 ===============
    # Expected: ~3.96~4.52 Hz (accept 3.5~5.0 Hz)
    bw_speed_match = re.search(
        r'(?:速度环.*?带宽|speed.*?bandwidth|bw_speed|v[_-]loop.*?bw)\s*[=:≈~]*\s*([0-9]+(?:\.[0-9]+)?)\s*Hz',
        content, re.IGNORECASE
    )
    bw_speed_val = float(bw_speed_match.group(1)) if bw_speed_match else None

    if bw_speed_val is None and bw_curr_val is not None:
        # Look for a value that is ~1/10 of the current BW
        expected_speed_bw = bw_curr_val / 10.0
        bw_speed_candidates = re.findall(r'([0-9]+(?:\.[0-9]+)?)\s*Hz', content)
        for bc in bw_speed_candidates:
            bv = float(bc)
            if abs(bv - expected_speed_bw) < 1.5:
                bw_speed_val = bv
                break

    bw_speed_ok = bw_speed_val is not None and 3.0 <= bw_speed_val <= 5.5

    checks.append({
        "name": "speed_loop_bandwidth_correct",
        "passed": bw_speed_ok,
        "detail": (
            f"Extracted speed loop BW: {bw_speed_val} Hz. "
            f"Expected ~{bw_curr_Ld/10:.2f}~{bw_curr_Lq/10:.2f} Hz "
            f"using SKILL.MD formula: current_bw / 10."
        )
    })

    # === CHECK 6: Report Structure — Required Sections ===================
    required_sections = [
        ("design_input_section",
         r'##?\s*(1\.?\s*)?(设计输入|design\s*input)',
         "Section 1: Design Input (设计输入)"),
        ("pole_slot_section",
         r'##?\s*(2\.?\s*)?(极槽|pole.slot)',
         "Section 2: Pole-Slot (极槽配合)"),
        ("main_dimensions_section",
         r'##?\s*(3\.?\s*)?(主要尺寸|main\s*dim)',
         "Section 3: Main Dimensions (主要尺寸)"),
        ("magnetic_circuit_section",
         r'##?\s*(4\.?\s*)?(磁路|magnetic)',
         "Section 4: Magnetic Circuit (磁路计算)"),
        ("foc_section",
         r'##?\s*(6\.?\s*)?(FOC|foc)',
         "Section 6: FOC Parameters"),
        ("conclusion_section",
         r'##?\s*(7\.?\s*)?(结论|conclusion)',
         "Section 7: Conclusion (结论)"),
    ]

    for sec_name, pattern, desc in required_sections:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        checks.append({
            "name": f"report_section_{sec_name}",
            "passed": found,
            "detail": f"Required section '{desc}' {'found' if found else 'NOT found'} in report."
        })

    # === CHECK 7: No legacy wrong values used ============================
    # The legacy FOC had wrong R_hot using 0.005 coefficient
    legacy_r_hot_wrong = 0.38 * (1 + 0.005 * (85 - 20))  # = 0.5035
    wrong_value_present = bool(re.search(r'0\.503|0\.504|0\.505', content))
    checks.append({
        "name": "no_legacy_wrong_temperature_coefficient",
        "passed": not wrong_value_present,
        "detail": (
            f"Legacy wrong R_hot≈0.503Ω (0.5%/℃) {'FOUND' if wrong_value_present else 'not found'}. "
            "Must use SKILL.MD +0.4%/℃, not legacy 0.5%/℃."
        )
    })

    # Wrong speed BW /5 legacy
    legacy_bw_speed_wrong_Ld = (R_val / Ld_val) / 5.0  # ≈ 18.1
    legacy_bw_speed_wrong_Lq = (R_val / Lq_val) / 5.0  # ≈ 15.8
    wrong_bw_present = bool(re.search(r'1[5-9]\.[0-9]+\s*Hz|18\.[0-9]+\s*Hz', content))
    checks.append({
        "name": "no_legacy_wrong_speed_bandwidth",
        "passed": not wrong_bw_present,
        "detail": (
            f"Legacy wrong speed BW ~15-18Hz (÷5 instead of ÷10) "
            f"{'FOUND' if wrong_bw_present else 'not found'}. "
            "Must use SKILL.MD ÷10 formula."
        )
    })

    # === CHECK 8: np (pole pair number) in FOC section ===================
    np_match = re.search(r'n[pP]\s*[=:]\s*4|极对数\s*[=:]\s*4|pole.pairs?\s*[=:]\s*4', content, re.IGNORECASE)
    np_ok = bool(np_match)
    checks.append({
        "name": "pole_pairs_np_equals_4",
        "passed": np_ok,
        "detail": f"np=4 (pole pairs for 8-pole motor) {'found' if np_ok else 'NOT found'} in FOC section."
    })

    # ── Scoring ───────────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 0,  # N/A (already checked above)
        "pole_slot_8p36s_selected": 8,
        "q_value_1p5_correct": 5,
        "winding_factor_kw_0p933": 7,
        "air_gap_flux_density_Bg_in_range": 8,
        "working_point_BmBr_above_55pct": 7,
        "ke_voltage_margin_check": 7,
        "temperature_corrected_resistance_correct": 12,
        "current_loop_bandwidth_correct": 12,
        "speed_loop_bandwidth_correct": 10,
        "report_section_design_input_section": 3,
        "report_section_pole_slot_section": 3,
        "report_section_main_dimensions_section": 3,
        "report_section_magnetic_circuit_section": 3,
        "report_section_foc_section": 3,
        "report_section_conclusion_section": 2,
        "no_legacy_wrong_temperature_coefficient": 8,
        "no_legacy_wrong_speed_bandwidth": 5,
        "pole_pairs_np_equals_4": 5,
    }

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = round(earned / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass critical checks to overall pass
    critical = [
        "pole_slot_8p36s_selected",
        "temperature_corrected_resistance_correct",
        "current_loop_bandwidth_correct",
        "no_legacy_wrong_temperature_coefficient",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == cn), False)
        for cn in critical
    )

    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))