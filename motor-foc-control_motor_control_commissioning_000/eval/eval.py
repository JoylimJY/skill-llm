import sys
import json
import math
import os
from pathlib import Path

def load_result(workspace):
    """Find the commissioning config JSON file."""
    candidates = list(Path(workspace).rglob("commissioning_config.json"))
    if not candidates:
        return None, "File 'commissioning_config.json' not found anywhere in workspace"
    # Prefer files not in distractor locations
    return candidates[0], None

def check_svpwm_sector(result_data, checks):
    """Check SVPWM sector computation for operating points."""
    # Using SKILL.md sector_table logic
    def sv_sector(alpha, beta):
        a = beta
        b = alpha * 0.866 - beta * 0.5
        c = -alpha * 0.866 - beta * 0.5
        N = 0
        if a > 0: N |= 1
        if b > 0: N |= 2
        if c > 0: N |= 4
        sector_table = [0, 2, 6, 1, 4, 3, 5, 0]
        return sector_table[N]

    ops = {
        "OP1_low_speed":    (12.5, 8.3),
        "OP2_rated":        (95.0, 142.0),
        "OP3_flux_weakening": (118.0, 163.0),
    }
    expected_sectors = {k: sv_sector(v[0], v[1]) for k, v in ops.items()}

    try:
        svpwm_data = result_data.get("svpwm", {})
        all_ok = True
        details = []
        for op_id, exp_sector in expected_sectors.items():
            op_result = svpwm_data.get(op_id, {})
            got = op_result.get("sector")
            ok = (got == exp_sector)
            all_ok = all_ok and ok
            details.append(f"{op_id}: expected sector={exp_sector}, got={got}, {'OK' if ok else 'FAIL'}")
        checks.append({
            "name": "svpwm_sector_determination",
            "passed": all_ok,
            "detail": "; ".join(details)
        })
        return all_ok
    except Exception as e:
        checks.append({"name": "svpwm_sector_determination", "passed": False, "detail": str(e)})
        return False

def check_svpwm_duty(result_data, checks):
    """Check SVPWM Ta, Tb calculation for OP1 (sector 2)."""
    # OP1: alpha=12.5, beta=8.3, T=1/16000=62.5e-6, Udc=310
    # Sector 2: Ta=Y, Tb=-X
    # X=beta=8.3, Y=alpha*0.866+beta*0.5=12.5*0.866+8.3*0.5=10.825+4.15=14.975
    # Z=-alpha*0.866+beta*0.5=-10.825+4.15=-6.675
    # Sector for (12.5, 8.3): a=8.3>0 → N|=1; b=12.5*0.866-8.3*0.5=10.825-4.15=6.675>0 → N|=2; c=-10.825-4.15=-14.975<0 → N=3 → sector_table[3]=1
    # Let me recalc the sector:
    def sv_sector(alpha, beta):
        a = beta
        b = alpha * 0.866 - beta * 0.5
        c = -alpha * 0.866 - beta * 0.5
        N = 0
        if a > 0: N |= 1
        if b > 0: N |= 2
        if c > 0: N |= 4
        sector_table = [0, 2, 6, 1, 4, 3, 5, 0]
        return sector_table[N]

    alpha, beta = 12.5, 8.3
    T = 1.0 / 16000  # PWM period
    sector = sv_sector(alpha, beta)

    X = beta
    Y = alpha * 0.866 + beta * 0.5
    Z = -alpha * 0.866 + beta * 0.5

    Ta_raw, Tb_raw = 0.0, 0.0
    if sector == 1:
        Ta_raw, Tb_raw = Z, Y
    elif sector == 2:
        Ta_raw, Tb_raw = Y, -X
    elif sector == 3:
        Ta_raw, Tb_raw = -Z, X
    elif sector == 4:
        Ta_raw, Tb_raw = -X, Z
    elif sector == 5:
        Ta_raw, Tb_raw = X, -Y
    elif sector == 6:
        Ta_raw, Tb_raw = -Y, -Z

    T_sum = Ta_raw + Tb_raw
    if T_sum > T:
        Ta_raw = Ta_raw * T / T_sum
        Tb_raw = Tb_raw * T / T_sum

    exp_Ta = round(Ta_raw, 9)
    exp_Tb = round(Tb_raw, 9)

    try:
        svpwm_data = result_data.get("svpwm", {})
        op1 = svpwm_data.get("OP1_low_speed", {})
        got_Ta = op1.get("Ta_s")
        got_Tb = op1.get("Tb_s")

        tol = 1e-7  # 100ns tolerance
        ok_Ta = got_Ta is not None and abs(float(got_Ta) - exp_Ta) < tol
        ok_Tb = got_Tb is not None and abs(float(got_Tb) - exp_Tb) < tol
        passed = ok_Ta and ok_Tb
        checks.append({
            "name": "svpwm_Ta_Tb_OP1",
            "passed": passed,
            "detail": f"sector={sector}; exp Ta={exp_Ta:.3e}, got={got_Ta}; exp Tb={exp_Tb:.3e}, got={got_Tb}"
        })
        return passed
    except Exception as e:
        checks.append({"name": "svpwm_Ta_Tb_OP1", "passed": False, "detail": str(e)})
        return False

def check_mtpa(result_data, checks):
    """Check MTPA Id calculation for all operating points."""
    # SKILL.md formula:
    # delta_L = Lq - Ld = 9.8e-3 - 6.2e-3 = 3.6e-3
    # k = Psi_m / (2 * delta_L) = 0.078 / (2 * 0.0036) = 10.8333...
    # Id_MTPA = -(k) + sqrt(k^2 + Iq^2)  then return -Id (Id must be negative)
    Ld = 6.2e-3
    Lq = 9.8e-3
    Psi_m = 0.078
    delta_L = Lq - Ld

    def mtpa_Id(Iq):
        k = Psi_m / (2.0 * delta_L)
        Id_pos = -k + math.sqrt(k*k + Iq*Iq)
        return -Id_pos  # negative (demagnetizing)

    test_cases = {
        "OP1_low_speed": 4.0,
        "OP2_rated": 18.0,
        "OP3_flux_weakening": 14.0,
    }
    expected = {k: round(mtpa_Id(v), 5) for k, v in test_cases.items()}

    try:
        mtpa_data = result_data.get("mtpa", {})
        all_ok = True
        details = []
        for op_id, exp_id in expected.items():
            op_result = mtpa_data.get(op_id, {})
            got = op_result.get("Id_MTPA_A")
            tol = 0.005  # 5mA tolerance
            ok = got is not None and abs(float(got) - exp_id) < tol
            all_ok = all_ok and ok
            details.append(f"{op_id}: exp Id_MTPA={exp_id:.5f}, got={got}, {'OK' if ok else 'FAIL'}")
        checks.append({
            "name": "mtpa_id_calculation",
            "passed": all_ok,
            "detail": "; ".join(details)
        })
        return all_ok
    except Exception as e:
        checks.append({"name": "mtpa_id_calculation", "passed": False, "detail": str(e)})
        return False

def check_flux_weakening_mode(result_data, checks):
    """Check flux weakening mode selection for OP3."""
    # OP3: V_mag_override = 201.5 V
    # V_lim = Vdc / sqrt(2) = 310 / sqrt(2) ≈ 219.203
    # V_mag = 201.5
    # ratio = 201.5 / 219.203 ≈ 0.9193
    # 0.85 < 0.9193 < 0.95 → transition zone
    # alpha = (201.5 - 219.203*0.85) / (219.203 * 0.10)
    # = (201.5 - 186.323) / 21.920 = 15.177 / 21.920 ≈ 0.6924
    # Mode should be "transition" or "flux_weakening_transition" (partial FW)
    Vdc = 310.0
    V_lim = Vdc / math.sqrt(2)
    V_mag_op3 = 201.5

    ratio = V_mag_op3 / V_lim
    if ratio < 0.85:
        expected_mode = "MTPA"
    elif ratio < 0.95:
        expected_mode = "transition"
    else:
        expected_mode = "flux_weakening"

    try:
        fw_data = result_data.get("flux_weakening", {})
        op3 = fw_data.get("OP3_flux_weakening", {})
        got_mode = op3.get("mode", "")
        # Accept various reasonable spellings of transition mode
        ok = expected_mode.lower() in got_mode.lower() or \
             ("trans" in got_mode.lower() and expected_mode == "transition") or \
             (got_mode.lower() in ["transition", "partial_fw", "fw_transition", "transitional"])
        checks.append({
            "name": "flux_weakening_mode_op3",
            "passed": ok,
            "detail": f"V_lim={V_lim:.3f}, V_mag={V_mag_op3}, ratio={ratio:.4f}; expected mode='{expected_mode}', got='{got_mode}'"
        })
        return ok
    except Exception as e:
        checks.append({"name": "flux_weakening_mode_op3", "passed": False, "detail": str(e)})
        return False

def check_v_lim(result_data, checks):
    """Check that V_lim = Vdc/sqrt(2) is correctly computed."""
    expected_v_lim = round(310.0 / math.sqrt(2), 4)
    try:
        fw_data = result_data.get("flux_weakening", {})
        got = fw_data.get("V_lim_V")
        tol = 0.01
        ok = got is not None and abs(float(got) - expected_v_lim) < tol
        checks.append({
            "name": "v_lim_computation",
            "passed": ok,
            "detail": f"expected V_lim={expected_v_lim}, got={got}"
        })
        return ok
    except Exception as e:
        checks.append({"name": "v_lim_computation", "passed": False, "detail": str(e)})
        return False

def check_pi_current_loop(result_data, checks):
    """Check current loop PI params using SKILL.md exact formulas."""
    R, L = 1.85, 6.2e-3
    bw_factor = 0.5
    omega_bw = (R / L) * bw_factor
    Kp_exp = round(L * omega_bw, 6)
    Ki_cont_exp = round(R / L, 4)
    Ts = 1.0 / 16000
    Ki_d_exp = round(R / L * Ts / 2.0, 9)  # Tustin

    try:
        pi_data = result_data.get("pi_parameters", {}).get("current_loop", {})
        got_Kp = pi_data.get("Kp")
        got_Ki_d = pi_data.get("Ki_discrete")

        tol_Kp = 0.001
        tol_Ki = 1e-7
        ok_Kp = got_Kp is not None and abs(float(got_Kp) - Kp_exp) < tol_Kp
        ok_Ki = got_Ki_d is not None and abs(float(got_Ki_d) - Ki_d_exp) < tol_Ki
        passed = ok_Kp and ok_Ki
        checks.append({
            "name": "pi_current_loop_gains",
            "passed": passed,
            "detail": f"exp Kp={Kp_exp}, got={got_Kp}; exp Ki_d={Ki_d_exp:.3e}, got={got_Ki_d}"
        })
        return passed
    except Exception as e:
        checks.append({"name": "pi_current_loop_gains", "passed": False, "detail": str(e)})
        return False

def check_pi_speed_loop(result_data, checks):
    """Check speed loop PI params."""
    R, L = 1.85, 6.2e-3
    J = 8.5e-4
    Kt = 0.18
    bw_factor = 0.5
    omega_bw_current = (R / L) * bw_factor
    omega_bw_speed = omega_bw_current / 10.0
    Kp_speed_exp = round(J * omega_bw_speed, 9)
    Tm = J * R / (Kt ** 2)
    Ki_speed_exp = round(Kp_speed_exp / Tm, 9)

    try:
        pi_data = result_data.get("pi_parameters", {}).get("speed_loop", {})
        got_Kp = pi_data.get("Kp")
        got_Ki = pi_data.get("Ki")

        tol = 1e-6
        ok_Kp = got_Kp is not None and abs(float(got_Kp) - Kp_speed_exp) < tol
        ok_Ki = got_Ki is not None and abs(float(got_Ki) - Ki_speed_exp) < tol
        passed = ok_Kp and ok_Ki
        checks.append({
            "name": "pi_speed_loop_gains",
            "passed": passed,
            "detail": f"exp Kp_speed={Kp_speed_exp:.3e}, got={got_Kp}; exp Ki_speed={Ki_speed_exp:.3e}, got={got_Ki}"
        })
        return passed
    except Exception as e:
        checks.append({"name": "pi_speed_loop_gains", "passed": False, "detail": str(e)})
        return False

def check_clarke_transform(result_data, checks):
    """Check Clarke transform result for OP2 three-phase currents."""
    # Clarke: Ialpha = Ia, Ibeta = (Ia + 2*Ib)/sqrt(3)
    # OP2 doesn't have phase currents in input, but the agent should demonstrate
    # Clarke formula knowledge. Check if clarke_formula field is correct.
    # We embed a specific verification: the agent must apply Clarke to given test currents.
    # Let's check the "clarke_verification" section if present.
    test_Ia = 10.0
    test_Ib = -5.0
    exp_alpha = test_Ia  # Ialpha = Ia
    exp_beta = round((test_Ia + 2 * test_Ib) / math.sqrt(3), 6)  # SKILL.md formula

    try:
        cv = result_data.get("clarke_verification", {})
        if not cv:
            checks.append({
                "name": "clarke_transform_formula",
                "passed": False,
                "detail": "No 'clarke_verification' section found in output"
            })
            return False
        got_alpha = cv.get("I_alpha")
        got_beta = cv.get("I_beta")
        tol = 0.001
        ok_alpha = got_alpha is not None and abs(float(got_alpha) - exp_alpha) < tol
        ok_beta = got_beta is not None and abs(float(got_beta) - exp_beta) < tol
        passed = ok_alpha and ok_beta
        checks.append({
            "name": "clarke_transform_formula",
            "passed": passed,
            "detail": f"Input: Ia=10, Ib=-5; exp alpha={exp_alpha}, got={got_alpha}; exp beta={exp_beta:.6f}, got={got_beta}"
        })
        return passed
    except Exception as e:
        checks.append({"name": "clarke_transform_formula", "passed": False, "detail": str(e)})
        return False

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # Find result file
    result_path, err = load_result(workspace)
    if result_path is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": err}]
        }))
        return

    checks.append({"name": "file_exists", "passed": True, "detail": str(result_path)})

    try:
        with open(result_path) as f:
            result_data = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False, "detail": str(e)}]
        }))
        return

    checks.append({"name": "file_parseable", "passed": True, "detail": "Valid JSON"})

    # Run all checks
    check_svpwm_sector(result_data, checks)
    check_svpwm_duty(result_data, checks)
    check_mtpa(result_data, checks)
    check_flux_weakening_mode(result_data, checks)
    check_v_lim(result_data, checks)
    check_pi_current_loop(result_data, checks)
    check_pi_speed_loop(result_data, checks)
    check_clarke_transform(result_data, checks)

    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    overall = score >= 0.75

    print(json.dumps({
        "passed": overall,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()