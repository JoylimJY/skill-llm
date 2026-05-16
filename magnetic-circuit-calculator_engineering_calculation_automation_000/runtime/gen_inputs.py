import os
import math
import textwrap

# Create workspace directory structure
os.makedirs("/workspace/scripts", exist_ok=True)
os.makedirs("/workspace/references", exist_ok=True)
os.makedirs("/workspace/design_inputs", exist_ok=True)
os.makedirs("/workspace/archive/old_designs", exist_ok=True)
os.makedirs("/workspace/reports/drafts", exist_ok=True)
os.makedirs("/workspace/simulations/maxwell_exports", exist_ok=True)
os.makedirs("/workspace/docs", exist_ok=True)

# ─── Create the actual mec_calculator_v2.py script ───────────────────────────
mec_v2_script = textwrap.dedent(r'''
#!/usr/bin/env python3
"""
mec_calculator_v2.py — Magnetic Equivalent Circuit Calculator (Enhanced)
Supports: iterative solving, PM library, hm sweep, slot comparison
"""

import argparse
import math
import sys

MU0 = 4 * math.pi * 1e-7  # H/m

PM_LIBRARY = {
    "N35":  {"Br": 1.17, "Hc": 890},
    "N42":  {"Br": 1.32, "Hc": 1003},
    "N42SH":{"Br": 1.25, "Hc": 955},
    "N48":  {"Br": 1.40, "Hc": 1050},
    "N52":  {"Br": 1.48, "Hc": 1114},
    "SmCo28": {"Br": 1.05, "Hc": 800},
}

def pole_pitch(Di, poles):
    return math.pi * Di / poles

def slots_per_pole_phase(Q, poles, m=3):
    q = Q / (poles * m)
    return q

def winding_factor(q):
    # Simplified: distributed winding Kw estimate
    # For fractional slot: approximate 0.866 for q~0.5, 0.945 for q=1
    if abs(q - 0.5) < 0.01:
        return 0.866
    elif abs(q - 1.0) < 0.01:
        return 0.955
    elif abs(q - 1.5) < 0.01:
        return 0.960
    elif abs(q - 2.0) < 0.01:
        return 0.966
    elif abs(q - 0.75) < 0.01:
        return 0.902
    elif abs(q - 2.5) < 0.01:
        return 0.957
    else:
        # Generic approximation
        return min(0.97, 0.866 + 0.1 * min(q, 1.0))

def calculate_Bg_method_A(Br, Am_mm2, sigma, delta_mm, Ae_mm2):
    """Method A: Bg = sigma * Br * Am / (delta * Ae) — simplified empirical"""
    # Note: delta here is in mm, Am and Ae in mm²  => dimensionless ratio
    Bg = sigma * Br * Am_mm2 / (delta_mm * Ae_mm2 / delta_mm)
    # Simplified: Bg = sigma * Br * (Am/Ae)
    Bg = sigma * Br * (Am_mm2 / Ae_mm2)
    return Bg

def calculate_working_point(Bg, Ae_mm2, Am_mm2, sigma, Br, Hc_kAm, hm_mm, F_core=0):
    """Calculate PM working point"""
    Bm = sigma * Bg * (Ae_mm2 / Am_mm2)
    # Hm from demagnetization curve (linear model): Bm = Br + mu0*mur * Hm
    # Simplified: Hm = Hc * (Bm/Br - 1)  [Hm is negative in 2nd quadrant]
    Hm = Hc_kAm * (Bm / Br - 1.0)  # kA/m, negative value expected
    ratio = Bm / Br
    return Bm, Hm, ratio

def flux_per_pole(Bg, tau_mm, L_mm):
    """Φg = Bg * τ * L (in Wb, converting mm² to m²)"""
    return Bg * (tau_mm * 1e-3) * (L_mm * 1e-3)

def compute_ke(Nph, Kw, Phi_g, poles, m=3):
    p = poles // 2
    # Ke = 2*pi*p*Nph*Kw*Phi_g  (V per rad/s, peak per pole pair)
    Ke = Nph * Kw * Phi_g * p * 2 * math.pi / (2 * math.pi)
    # Standard formula: Ke = sqrt(2)*4.44*f*Nph*Kw*Phi_g / (2*pi*n/60)
    # Simplified to: Ke = p * Nph * Kw * Phi_g  [V/(rad/s)]
    Ke = p * Nph * Kw * Phi_g
    return Ke

def working_point_status(ratio):
    if ratio > 0.6:
        return "正常", "继续优化"
    elif ratio >= 0.5:
        return "偏低", "建议增加 hm 至 4mm 重新计算"
    else:
        return "有退磁风险", "增加 hm、减小气隙、换高矫顽力牌号"

def run_calculation(poles, Q, L, delta, Di, hm, Br=1.25, Hc=955, bm=None,
                    sigma=1.2, Nph=120, m=3, silent=False):
    tau = pole_pitch(Di, poles)
    q = slots_per_pole_phase(Q, poles, m)
    Kw = winding_factor(q)

    if bm is None:
        # Default: bm = 0.8 * tau
        bm = 0.80 * tau

    Ae = tau * L       # mm²
    Am = bm * L        # mm²

    Bg = calculate_Bg_method_A(Br, Am, sigma, delta, Ae)
    Phi_g = flux_per_pole(Bg, tau, L)   # Wb
    Bm, Hm, ratio = calculate_working_point(Bg, Ae, Am, sigma, Br, Hc, hm)
    status, suggestion = working_point_status(ratio)
    Ke = compute_ke(Nph, Kw, Phi_g, poles, m)
    Kt = Ke  # For non-salient: Kt = Ke

    if not silent:
        print("===== 磁路计算结果 =====")
        print("【基本参数】")
        print(f"极距 τ = {tau:.2f} mm")
        print(f"每极每相槽数 q = {q:.4f}")
        print(f"绕组系数 Kw = {Kw:.4f}")
        print()
        print("【气隙磁场】")
        print(f"气隙磁密 Bg = {Bg:.4f} T")
        print(f"每极气隙磁通 Φg = {Phi_g*1000:.4f} mWb")
        print()
        print("【永磁体工作点】")
        print(f"永磁体截面积 Am = {Am:.2f} mm²")
        print(f"气隙截面积 Ae = {Ae:.2f} mm²")
        print(f"漏磁系数 σ = {sigma:.4f}")
        print(f"工作点 Bm/Br = {ratio*100:.2f}%")
        print(f"工作点 Bm = {Bm:.4f} T，Hm = {Hm:.2f} kA/m")
        print()
        print("【性能估算】")
        print(f"反电动势常数 Ke = {Ke:.6f} V/(rad/s)")
        print(f"转矩常数 Kt = {Kt:.6f} Nm/A")
        print()
        print("【结论】")
        print(f"工作点状态：{status}")
        print(f"建议：{suggestion}")
        print("=" * 25)

    return {
        "tau_mm": tau,
        "q": q,
        "Kw": Kw,
        "Bg_T": Bg,
        "Phi_g_mWb": Phi_g * 1000,
        "Am_mm2": Am,
        "Ae_mm2": Ae,
        "sigma": sigma,
        "Bm_T": Bm,
        "Hm_kAm": Hm,
        "Bm_over_Br": ratio,
        "Ke": Ke,
        "Kt": Kt,
        "status": status,
        "suggestion": suggestion,
    }

def sweep_hm(poles, Q, L, delta, Di, Br=1.25, Hc=955, bm=None,
             sigma=1.2, Nph=120, m=3, hm_range=None):
    if hm_range is None:
        hm_range = [round(1.0 + i * 0.5, 1) for i in range(10)]  # 1.0 to 5.5mm
    print("===== 永磁体厚度扫描 (hm sweep) =====")
    print(f"{'hm(mm)':<10} {'Bg(T)':<10} {'Bm/Br(%)':<12} {'状态'}")
    print("-" * 50)
    results = []
    for hm in hm_range:
        r = run_calculation(poles, Q, L, delta, Di, hm, Br, Hc, bm, sigma, Nph, m, silent=True)
        status_str = r["status"]
        print(f"{hm:<10.1f} {r['Bg_T']:<10.4f} {r['Bm_over_Br']*100:<12.2f} {status_str}")
        results.append((hm, r))
    print("-" * 50)
    # Find minimum hm where Bm/Br > 0.6
    valid = [(hm, r) for hm, r in results if r["Bm_over_Br"] > 0.6]
    if valid:
        min_hm, min_r = valid[0]
        print(f"\n最小合理 hm = {min_hm} mm (Bm/Br = {min_r['Bm_over_Br']*100:.2f}%)")
    else:
        print("\n警告：扫描范围内无合理工作点，请检查参数")
    return results

def compare_slots(poles, L, delta, Di, Br=1.25, Hc=955,
                  sigma=1.2, Nph=120, m=3, hm=3.0):
    slot_options = [
        int(poles * m * k / 2) for k in range(1, 7)
        if int(poles * m * k / 2) >= poles
    ]
    # Also add some fractional slot options
    extra = []
    for q_num in [1, 2, 3, 4, 5, 6]:
        Q = int(poles * m * q_num / 2)
        if Q not in slot_options and Q >= poles:
            extra.append(Q)
    slot_options = sorted(set(slot_options + extra))[:8]

    print(f"===== 极槽方案对比 ({poles}极) =====")
    print(f"{'Q(槽数)':<10} {'q':<8} {'Kw':<8} {'Bg(T)':<10} {'Bm/Br(%)':<12} {'状态'}")
    print("-" * 60)
    for Q in slot_options:
        r = run_calculation(poles, Q, L, delta, Di, hm, Br, Hc, None, sigma, Nph, m, silent=True)
        print(f"{Q:<10} {r['q']:<8.4f} {r['Kw']:<8.4f} {r['Bg_T']:<10.4f} {r['Bm_over_Br']*100:<12.2f} {r['status']}")
    print("-" * 60)

def main():
    parser = argparse.ArgumentParser(description="MEC Calculator v2")
    parser.add_argument("--poles",  type=int,   default=8)
    parser.add_argument("--Q",      type=int,   default=36)
    parser.add_argument("--L",      type=float, default=60.0)
    parser.add_argument("--delta",  type=float, default=0.5)
    parser.add_argument("--Di",     type=float, default=54.0)
    parser.add_argument("--hm",     type=float, default=3.0)
    parser.add_argument("--Br",     type=float, default=1.25)
    parser.add_argument("--Hc",     type=float, default=955.0)
    parser.add_argument("--bm",     type=float, default=None)
    parser.add_argument("--sigma",  type=float, default=1.2)
    parser.add_argument("--Nph",    type=int,   default=120)
    parser.add_argument("--m",      type=int,   default=3)
    parser.add_argument("--pm",     type=str,   default=None,
                        help="PM material name from library (e.g. N42SH)")
    parser.add_argument("--sweep_hm",      action="store_true")
    parser.add_argument("--compare_slots", action="store_true")
    args = parser.parse_args()

    # Override Br/Hc from library if --pm given
    if args.pm:
        if args.pm in PM_LIBRARY:
            args.Br = PM_LIBRARY[args.pm]["Br"]
            args.Hc = PM_LIBRARY[args.pm]["Hc"]
            print(f"[PM库] 使用牌号 {args.pm}: Br={args.Br}T, Hc={args.Hc}kA/m")
        else:
            print(f"[警告] 未知牌号 {args.pm}，使用手动输入值")

    if args.sweep_hm:
        sweep_hm(args.poles, args.Q, args.L, args.delta, args.Di,
                 args.Br, args.Hc, args.bm, args.sigma, args.Nph, args.m)
    elif args.compare_slots:
        compare_slots(args.poles, args.L, args.delta, args.Di,
                      args.Br, args.Hc, args.sigma, args.Nph, args.m, args.hm)
    else:
        run_calculation(args.poles, args.Q, args.L, args.delta, args.Di,
                        args.hm, args.Br, args.Hc, args.bm,
                        args.sigma, args.Nph, args.m)

if __name__ == "__main__":
    main()
''')

with open("/workspace/scripts/mec_calculator_v2.py", "w") as f:
    f.write(mec_v2_script)

# ─── Create the basic mec_calculator.py (stub) ───────────────────────────────
mec_v1_script = textwrap.dedent('''
#!/usr/bin/env python3
"""mec_calculator.py — Basic version. Use v2 for full features."""
print("This is the basic version. Please use mec_calculator_v2.py for full features.")
''')
with open("/workspace/scripts/mec_calculator.py", "w") as f:
    f.write(mec_v1_script)

# ─── Create references/steel_pm_materials.md ─────────────────────────────────
pm_materials_md = textwrap.dedent('''
# 硅钢片和永磁体牌号参数库

## 永磁体牌号 (NdFeB)

| 牌号    | Br (T) | Hc (kA/m) | BHmax (kJ/m³) | 最高工作温度 |
|---------|--------|-----------|----------------|-------------|
| N35     | 1.17   | 890       | 263-287        | 80°C        |
| N42     | 1.32   | 1003      | 318-342        | 80°C        |
| N42SH   | 1.25   | 955       | 302-326        | 150°C       |
| N48     | 1.40   | 1050      | 366-390        | 80°C        |
| N52     | 1.48   | 1114      | 398-422        | 80°C        |
| SmCo28  | 1.05   | 800       | 212-228        | 250°C       |

## 硅钢片牌号

| 牌号         | 厚度(mm) | 铁损 W/kg @1.5T,50Hz |
|-------------|---------|----------------------|
| 35WW300     | 0.35    | 3.00                 |
| 35WW250     | 0.35    | 2.50                 |
| 50WW470     | 0.50    | 4.70                 |
| 50WW600     | 0.50    | 6.00                 |
''')
with open("/workspace/references/steel_pm_materials.md", "w") as f:
    f.write(pm_materials_md)

# ─── THE ACTUAL TASK INPUT: messy CSV with motor parameters ──────────────────
# Motor: 6-pole 27-slot surface-mounted PMSM
# Parameters given in mixed/wrong units to force conversion:
#   - L given in cm (not mm) → must convert
#   - Hc given in A/m (not kA/m) → must convert
#   - Di given in cm → must convert
#   - hm_initial too small (will need sweep to find valid one)

messy_csv = textwrap.dedent('''\
# EV Traction Motor Pre-Design Parameters
# Project: EV-Axle-Gen3
# Revision: draft_v0.3
# WARNING: units are mixed — engineer's raw notes
# DO NOT USE WITHOUT UNIT CONVERSION

parameter,value,unit,notes
poles,6,-,number of poles (2p=6)
slots,27,-,Q=27 stator slots
phases,3,-,m=3
core_length,7.5,cm,"NEEDS CONVERSION: given in cm, calculator expects mm"
air_gap,0.6,mm,delta
stator_inner_dia,4.8,cm,"NEEDS CONVERSION: given in cm, calculator expects mm"
pm_grade,N42SH,-,look up from PM library
pm_thickness_initial,1.5,mm,starting hm for sweep (likely too small)
pm_width_fraction,0.82,-,"bm = fraction * tau, compute from Di and poles"
leakage_coeff,1.15,-,sigma for surface-mounted type
turns_per_phase,144,-,Nph
''')
with open("/workspace/design_inputs/motor_params_draft.csv", "w") as f:
    f.write(messy_csv)

# ─── Distractor files ─────────────────────────────────────────────────────────

# Old design (different topology, wrong data)
with open("/workspace/archive/old_designs/motor_v1_params.txt", "w") as f:
    f.write("poles=4\nslots=24\nL=80mm\nBr=1.1T\nHc=850kA/m\nNOTE: obsolete design, do not use\n")

with open("/workspace/archive/old_designs/notes.txt", "w") as f:
    f.write("V1 design had thermal issues at 150C. Switched to N42SH grade.\n")

# Maxwell export files (distractors)
with open("/workspace/simulations/maxwell_exports/mesh_report.txt", "w") as f:
    f.write("Maxwell 2D mesh: 45320 elements\nSolver: magnetostatic\nConvergence: 0.12%\n")

with open("/workspace/simulations/maxwell_exports/flux_density_map.dat", "w") as f:
    f.write("# x, y, Bx, By\n# (placeholder - not yet simulated)\n0.0 0.0 0.0 0.0\n")

# Draft reports (empty/wrong)
with open("/workspace/reports/drafts/prelim_calc_WRONG.txt", "w") as f:
    f.write("Preliminary calc (WRONG - used cm without conversion):\n")
    f.write("tau = pi*4.8/6 = 2.51 mm  <-- WRONG, Di should be 48mm\n")
    f.write("DO NOT SUBMIT THIS\n")

# Docs
with open("/workspace/docs/design_checklist.md", "w") as f:
    f.write("## Pre-Design Checklist\n- [ ] Unit conversion verified\n- [ ] PM grade confirmed\n- [ ] hm sweep completed\n- [ ] Report generated\n")

with open("/workspace/docs/project_brief.txt", "w") as f:
    f.write("EV-Axle-Gen3 motor design.\nTarget Ke = 0.03-0.08 V/(rad/s).\nDeadline: end of sprint.\n")

with open("/workspace/references/design_guidelines.txt", "w") as f:
    f.write("Surface-mounted PMSM: sigma range 1.10-1.25\nIPM: sigma range 1.20-1.40\nAlways verify Bm/Br > 0.6 for healthy working point\n")

with open("/workspace/scripts/post_process.py", "w") as f:
    f.write("#!/usr/bin/env python3\n# Post-processing placeholder\nprint('No data to process yet')\n")

with open("/workspace/design_inputs/thermal_estimate.csv", "w") as f:
    f.write("component,loss_W,temp_rise_C\nstator_winding,45,38\npm_magnets,8,12\nbearing,3,5\n")

print("Workspace generated successfully.")
print("Task: Analyze motor_params_draft.csv, convert units, perform hm sweep,")
print("find minimum valid hm (Bm/Br > 0.6), run full calc, save mec_report.json")