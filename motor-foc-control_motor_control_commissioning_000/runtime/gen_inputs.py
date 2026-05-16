import os
import json
import math

WORKSPACE = "/workspace"

# ---------- directory structure ----------
dirs = [
    "scripts",
    "references",
    "motor_data/spindle_A",
    "motor_data/spindle_B",
    "motor_data/archive",
    "config/drive",
    "config/safety",
    "logs/commissioning",
    "logs/fault",
    "test/bench",
    "test/simulation",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ---------- distractor files ----------
distractor_files = {
    "references/foc-quick-ref.md": """# FOC Quick Reference
| Parameter | Typical | Notes |
|-----------|---------|-------|
| Current loop BW | 100-500 Hz | |
| Speed loop BW | 10-50 Hz | |
| Switching freq | 8-25 kHz | |
| Dead time | 200-800 ns | |
""",
    "references/pm-materials.md": """# Permanent Magnet Materials
N35: Br=1.17T, Hc=890kA/m
N52: Br=1.45T, Hc=1032kA/m
SmCo28: Br=1.05T, Hc=800kA/m
""",
    "motor_data/spindle_A/nameplate.txt": """Model: SGMJV-04ADE6S
Rated Power: 400W
Rated Speed: 3000 rpm
Rated Torque: 1.27 Nm
Poles: 8
""",
    "motor_data/spindle_B/nameplate.txt": """Model: SGMJV-08ADE6S
Rated Power: 750W
Rated Speed: 3000 rpm
Rated Torque: 2.39 Nm
Poles: 8
""",
    "motor_data/archive/old_params.json": json.dumps({
        "note": "DEPRECATED - do not use",
        "R": 0.9,
        "L": 4.2e-3,
        "Kt": 0.12
    }, indent=2),
    "config/drive/inverter.cfg": """[INVERTER]
Vdc = 310.0
switching_freq_hz = 16000
dead_time_ns = 500
pwm_resolution_bits = 12
""",
    "config/safety/limits.cfg": """[SAFETY]
max_current_A = 25.0
max_speed_rpm = 6000
over_temp_C = 85
""",
    "logs/commissioning/session_2024_01.log": """2024-01-15 09:00:01 [INFO] Drive power on
2024-01-15 09:00:05 [INFO] Initial angle identification: OK
2024-01-15 09:01:00 [WARN] Speed overshoot 8%
2024-01-15 09:05:00 [INFO] Commissioning complete
""",
    "logs/fault/fault_history.csv": """timestamp,code,description
2024-01-10,E001,Overcurrent
2024-01-12,E003,Encoder loss
2024-01-14,E001,Overcurrent
""",
    "test/bench/results.csv": """test_id,speed_rpm,torque_Nm,efficiency
T001,1000,1.2,0.91
T002,2000,1.1,0.92
T003,3000,0.95,0.89
""",
    "test/simulation/sim_config.json": json.dumps({
        "solver": "runge-kutta-4",
        "dt": 1e-6,
        "duration": 0.5
    }, indent=2),
    "docs/commissioning_procedure.txt": """Step 1: Measure motor parameters (R, L, Psi_m)
Step 2: Run PI auto-tuner
Step 3: Verify current loop step response
Step 4: Verify speed loop step response
Step 5: Test MTPA at rated load
Step 6: Test flux weakening above base speed
""",
}

for rel_path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, rel_path), "w") as f:
        f.write(content)

# ---------- foc_pi_tuner.py mock script ----------
# This script exists in the workspace as stated in SKILL.md
# It prints PI parameters using the exact formulas from SKILL.md
foc_pi_tuner_content = r'''#!/usr/bin/env python3
"""
FOC PI Auto-Tuner Script
Usage: python scripts/foc_pi_tuner.py --R <R> --L <L> [--J <J>] [--Kt <Kt>]
       [--Ts_us <Ts_us>] [--poles <poles>] [--target_bw <bw>] [--plot]
"""

import argparse
import math
import sys
import json

def compute_current_loop(R, L, bw_factor=0.5, Ts_us=None):
    """Compute current loop PI gains using SKILL.md formulas."""
    omega_bw = (R / L) * bw_factor
    Kp = L * omega_bw
    Ki = R / L
    result = {
        "omega_bw_rad_s": round(omega_bw, 6),
        "Kp": round(Kp, 6),
        "Ki_continuous": round(Ki, 6),
    }
    if Ts_us is not None:
        Ts = Ts_us * 1e-6
        Ki_d = Ki * Ts / 2.0  # Tustin discretization
        result["Ts_s"] = Ts
        result["Ki_discrete_tustin"] = round(Ki_d, 9)
    return result

def compute_speed_loop(J, Kp_current_loop_bw, R, Kt, Ts_us=None):
    """Compute speed loop PI gains using SKILL.md formulas."""
    # speed loop BW = current loop BW / 10
    omega_bw_speed = Kp_current_loop_bw / 10.0
    Kp_speed = J * omega_bw_speed
    Tm = J * R / (Kt ** 2)
    Ki_speed = Kp_speed / Tm
    result = {
        "omega_bw_speed_rad_s": round(omega_bw_speed, 6),
        "Kp_speed": round(Kp_speed, 9),
        "Tm_s": round(Tm, 6),
        "Ki_speed": round(Ki_speed, 9),
    }
    return result

def main():
    parser = argparse.ArgumentParser(description="FOC PI Auto-Tuner")
    parser.add_argument("--R", type=float, required=True, help="Phase resistance (Ohm)")
    parser.add_argument("--L", type=float, required=True, help="Phase inductance (H)")
    parser.add_argument("--J", type=float, default=None, help="Rotor inertia (kg.m^2)")
    parser.add_argument("--Kt", type=float, default=None, help="Torque constant (Nm/A)")
    parser.add_argument("--Ts_us", type=float, default=None, help="Sampling period (us)")
    parser.add_argument("--poles", type=int, default=None, help="Number of poles")
    parser.add_argument("--target_bw", type=float, default=None, help="Target bandwidth (rad/s)")
    parser.add_argument("--plot", action="store_true", help="Generate Bode plot")
    parser.add_argument("--mode", type=str, default="auto", help="Mode: auto or interactive")
    args = parser.parse_args()

    bw_factor = 0.5
    if args.target_bw is not None:
        # back-calculate factor
        natural_bw = args.R / args.L
        bw_factor = args.target_bw / natural_bw

    current = compute_current_loop(args.R, args.L, bw_factor=bw_factor, Ts_us=args.Ts_us)
    
    output = {
        "motor_params": {"R": args.R, "L": args.L},
        "current_loop": current,
    }
    
    if args.J is not None and args.Kt is not None:
        speed = compute_speed_loop(
            args.J, current["omega_bw_rad_s"], args.R, args.Kt, Ts_us=args.Ts_us
        )
        output["speed_loop"] = speed
        output["motor_params"]["J"] = args.J
        output["motor_params"]["Kt"] = args.Kt

    if args.poles is not None:
        output["motor_params"]["poles"] = args.poles

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
'''

with open(os.path.join(WORKSPACE, "scripts/foc_pi_tuner.py"), "w") as f:
    f.write(foc_pi_tuner_content)

# ---------- Motor specification input file ----------
# This is the raw messy input the agent must process
motor_spec = {
    "_note": "Spindle motor parameters for CNC machining center - axis Z",
    "_source": "factory test report 2024-03",
    "motor_id": "IPMSM-Z-AXIS-001",
    "phase_resistance_ohm": 1.85,
    "phase_inductance_d_H": 6.2e-3,
    "phase_inductance_q_H": 9.8e-3,
    "flux_linkage_Wb": 0.078,
    "pole_pairs": 4,
    "rated_current_A": 18.0,
    "max_current_A": 25.0,
    "torque_constant_Nm_per_A": 0.18,
    "rotor_inertia_kg_m2": 8.5e-4,
    "rated_speed_rpm": 3000,
    "dc_bus_voltage_V": 310.0,
    "pwm_frequency_hz": 16000,
    "_operating_points": "See below - used for SVPWM and MTPA evaluation",
    "operating_points": [
        {
            "id": "OP1_low_speed",
            "description": "Low speed, light load",
            "V_alpha": 12.5,
            "V_beta": 8.3,
            "Iq_A": 4.0
        },
        {
            "id": "OP2_rated",
            "description": "Rated speed, rated torque",
            "V_alpha": 95.0,
            "V_beta": 142.0,
            "Iq_A": 18.0
        },
        {
            "id": "OP3_flux_weakening",
            "description": "Above base speed, high V_mag",
            "V_alpha": 118.0,
            "V_beta": 163.0,
            "Iq_A": 14.0,
            "V_mag_override": 201.5
        }
    ]
}

with open(os.path.join(WORKSPACE, "motor_data/spindle_A/ipmsm_z_axis_params.json"), "w") as f:
    json.dump(motor_spec, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")