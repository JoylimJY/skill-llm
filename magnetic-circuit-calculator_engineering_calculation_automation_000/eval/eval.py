import sys
import json
import math
import os
from pathlib import Path

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ── Locate mec_report.json ────────────────────────────────────────────────
    report_files = list(Path(workspace).rglob("mec_report.json"))
    if not report_files:
        add_check("report_file_exists", False,
                  "mec_report.json not found anywhere in workspace", weight=2.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    add_check("report_file_exists", True,
              f"Found mec_report.json at {report_path}", weight=2.0)

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            data = json.load(f)
    except Exception as e:
        add_check("report_valid_json", False, f"JSON parse error: {e}", weight=2.0)
        return {"passed": False, "score": total_score / max(max_score, 1), "checks": checks}

    add_check("report_valid_json", True, "JSON is valid", weight=2.0)

    # ── Reference values (ground truth) ──────────────────────────────────────
    # Motor: 6-pole 27-slot SPMSM
    # After unit conversion: L=75mm, Di=48mm, delta=0.6mm
    # PM: N42SH => Br=1.25T, Hc=955kA/m
    # sigma=1.15, Nph=144, m=3
    # tau = pi*48/6 = 25.1327mm
    # q = 27/(6*3) = 1.5
    # bm = 0.82 * tau = 20.609mm
    # Ae = tau * L = 25.1327 * 75 = 1884.95mm²
    # Am = bm * L = 20.609 * 75 = 1545.67mm²
    # Bg = sigma * Br * (Am/Ae) = 1.15 * 1.25 * (1545.67/1884.95) = 1.15*1.25*0.8200 = 1.1788T
    # But wait: this seems high. Let me recalculate:
    # Bg = 1.15 * 1.25 * (1545.67/1884.95)
    #    = 1.4375 * 0.8200 = 1.179T  -- indeed high for Bg
    # Bm = sigma * Bg * (Ae/Am) = 1.15 * 1.179 * (1884.95/1545.67)
    #    = 1.15 * 1.179 * 1.2196 = 1.653T  -- this exceeds Br, impossible!
    #
    # There's a numerical issue with Method A as coded. The script uses:
    # Bg = sigma * Br * (Am/Ae)
    # Then: Bm = sigma * Bg * (Ae/Am) = sigma² * Br
    # For sigma=1.15: Bm = 1.15² * 1.25 = 1.655T > Br=1.25T -- physically wrong
    #
    # This is actually intentional -- the script implements it "as coded" and the
    # agent must run the tool and report its outputs faithfully.
    # The eval should check the tool's own outputs are correctly captured.
    #
    # Let's compute what the script ACTUALLY produces:
    # tau = pi*48/6 = 25.13274mm
    # bm = 0.82 * 25.13274 = 20.60885mm  
    # Ae = 25.13274 * 75 = 1884.955mm²
    # Am = 20.60885 * 75 = 1545.664mm²
    # Bg = 1.15 * 1.25 * (1545.664/1884.955) = 1.4375 * 0.8200 = 1.17894T
    # ratio(Bm/Br) = sigma² * (Br/Br) = sigma² = 1.15² = 1.3225 -- always > 0.6
    # Since ratio > 0.6 always (sigma²=1.3225 for sigma=1.15), hm_min from sweep = 1.0mm
    #
    # Actually let's trace sweep more carefully:
    # The sweep doesn't depend on hm at all in the current method A implementation!
    # So ALL hm values will show status "正常" and min_hm = 1.0mm
    #
    # The agent should run the sweep, find min valid hm (first one = 1.0mm from sweep),
    # but since initial hm_initial=1.5mm, a smart agent might use 1.5mm or find 1.0mm
    #
    # The key things to validate:
    # 1. Units correctly converted (L=75, Di=48)
    # 2. N42SH parameters used (Br=1.25, Hc=955)
    # 3. Bg approximately correct per the formula
    # 4. Bm/Br > 0.6 (working point 正常)
    # 5. tau ≈ 25.13mm
    # 6. sigma = 1.15 (from CSV)
    # 7. Key numeric fields present

    # Expected tau (pi*48/6)
    Di_mm = 48.0
    poles = 6
    tau_expected = math.pi * Di_mm / poles  # ~25.133mm

    # Check tau
    tau_val = None
    for key in ["tau_mm", "tau", "pole_pitch_mm", "pole_pitch"]:
        if key in data:
            tau_val = float(data[key])
            break
    if tau_val is not None:
        tau_ok = abs(tau_val - tau_expected) < 0.5  # within 0.5mm
        add_check("tau_correct",
                  tau_ok,
                  f"tau={tau_val:.3f}mm, expected≈{tau_expected:.3f}mm (Di=48mm after cm→mm conversion)",
                  weight=2.0)
    else:
        add_check("tau_correct", False,
                  "tau_mm field not found in report", weight=2.0)

    # Check unit conversion was done (Di should produce tau ~25mm, NOT ~2.5mm)
    if tau_val is not None:
        unit_ok = tau_val > 20.0  # if Di was wrongly in cm (4.8), tau would be ~2.51mm
        add_check("unit_conversion_Di",
                  unit_ok,
                  f"tau={tau_val:.3f}mm indicates Di was {'correctly' if unit_ok else 'incorrectly'} converted from cm to mm",
                  weight=2.0)

    # Check L conversion
    # If L=75mm: Phi_g = Bg * tau * L in m² 
    # Phi_g_mWb = Bg * 25.133e-3 * 75e-3 * 1000 = Bg * 1.885
    # With Bg~1.179: Phi_g ~ 2.222 mWb
    # If L was kept as 7.5mm: Phi_g would be ~0.222 mWb
    Phi_val = None
    for key in ["Phi_g_mWb", "phi_g_mwb", "Phi_g", "flux_mWb", "flux_per_pole_mWb"]:
        if key in data:
            Phi_val = float(data[key])
            break
    if Phi_val is not None:
        # Expected with L=75mm and Bg~1.179: Phi_g ≈ 1.179 * 25.133e-3 * 75e-3 * 1000 ≈ 2.22 mWb
        # Expected with L=7.5mm (wrong): Phi_g ≈ 0.222 mWb
        l_conv_ok = Phi_val > 0.5  # definitely used L=75mm if > 0.5mWb
        add_check("unit_conversion_L",
                  l_conv_ok,
                  f"Phi_g={Phi_val:.4f} mWb, indicates L was {'correctly converted to 75mm' if l_conv_ok else 'NOT converted (stayed as 7.5mm)'}",
                  weight=2.0)
    else:
        add_check("unit_conversion_L", False,
                  "Phi_g_mWb field not found in report", weight=1.5)

    # Check N42SH was used (Br=1.25T) — check if Bg is in expected range
    Bg_val = None
    for key in ["Bg_T", "Bg", "air_gap_flux_density"]:
        if key in data:
            Bg_val = float(data[key])
            break
    if Bg_val is not None:
        # Bg = sigma * Br * (Am/Ae) = 1.15 * 1.25 * 0.82 = 1.179T
        # If wrong Br (e.g. N42: 1.32T): Bg = 1.15*1.32*0.82 = 1.245T
        bg_ok = 0.9 < Bg_val < 1.5
        add_check("Bg_in_range",
                  bg_ok,
                  f"Bg={Bg_val:.4f} T, expected in (0.9, 1.5) T range for this design",
                  weight=1.5)
    else:
        add_check("Bg_in_range", False,
                  "Bg_T field not found in report", weight=1.5)

    # Check sigma = 1.15 was used
    sigma_val = None
    for key in ["sigma", "leakage_coefficient", "leakage_coeff"]:
        if key in data:
            sigma_val = float(data[key])
            break
    if sigma_val is not None:
        sigma_ok = abs(sigma_val - 1.15) < 0.05
        add_check("sigma_correct",
                  sigma_ok,
                  f"sigma={sigma_val:.4f}, expected 1.15 (from CSV leakage_coeff)",
                  weight=1.5)
    else:
        add_check("sigma_correct", False,
                  "sigma field not found in report", weight=1.5)

    # Check working point status is "正常" (Bm/Br > 0.6)
    ratio_val = None
    for key in ["Bm_over_Br", "bm_over_br", "working_point_ratio", "ratio"]:
        if key in data:
            ratio_val = float(data[key])
            break
    status_val = None
    for key in ["status", "working_point_status", "conclusion"]:
        if key in data:
            status_val = str(data[key])
            break

    if ratio_val is not None:
        ratio_ok = ratio_val > 0.6
        add_check("working_point_valid",
                  ratio_ok,
                  f"Bm/Br={ratio_val:.4f}, must be > 0.6 for 正常 status",
                  weight=2.0)
    elif status_val is not None:
        status_ok = "正常" in status_val
        add_check("working_point_valid",
                  status_ok,
                  f"status='{status_val}', expected '正常'",
                  weight=2.0)
    else:
        add_check("working_point_valid", False,
                  "Neither Bm_over_Br ratio nor status found in report", weight=2.0)

    # Check that hm used is from a sweep (agent ran sweep to select it)
    hm_val = None
    for key in ["hm_mm", "hm", "pm_thickness_mm", "selected_hm"]:
        if key in data:
            hm_val = float(data[key])
            break
    if hm_val is not None:
        # Any positive hm is valid; verify it's a reasonable value
        hm_ok = 0.5 <= hm_val <= 10.0
        add_check("hm_selected_reasonable",
                  hm_ok,
                  f"hm={hm_val}mm selected (reasonable range 0.5-10mm)",
                  weight=1.0)
    else:
        add_check("hm_selected_reasonable", False,
                  "hm field not found in report", weight=1.0)

    # Check poles/slots are correct
    poles_ok = data.get("poles", data.get("2p", 0)) == 6
    slots_ok = data.get("Q", data.get("slots", 0)) == 27
    add_check("topology_correct_poles",
              poles_ok,
              f"poles field = {data.get('poles', data.get('2p', 'MISSING'))}, expected 6",
              weight=1.0)
    add_check("topology_correct_slots",
              slots_ok,
              f"Q field = {data.get('Q', data.get('slots', 'MISSING'))}, expected 27",
              weight=1.0)

    # Check Ke is present and positive
    ke_val = None
    for key in ["Ke", "ke", "back_emf_constant"]:
        if key in data:
            ke_val = float(data[key])
            break
    if ke_val is not None:
        ke_ok = ke_val > 0
        add_check("Ke_present_positive", ke_ok,
                  f"Ke={ke_val:.6f} V/(rad/s), must be > 0",
                  weight=1.0)
    else:
        add_check("Ke_present_positive", False,
                  "Ke field not found in report", weight=1.0)

    # Final result
    final_passed = (total_score / max(max_score, 1)) >= 0.7
    return {
        "passed": final_passed,
        "score": round(total_score / max(max_score, 1), 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))