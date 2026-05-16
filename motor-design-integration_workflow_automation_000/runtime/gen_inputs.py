import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── directory structure ────────────────────────────────────────────────────
dirs = [
    "project/specs",
    "project/magnetic",
    "project/foc",
    "project/legacy",
    "project/simulation_results",
    "project/winding",
    "project/archive/v0.1",
    "project/archive/v0.2",
    "project/tools/scripts",
    "project/tools/templates",
    "docs/references",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── MAIN INPUT: motor requirements ────────────────────────────────────────
requirements = """\
# Motor Design Requirements — Project HVAC-Fan-350
# Customer: AeroCool Systems Inc.
# Date: 2024-01-15

[Specification]
rated_power_W       = 350
rated_speed_rpm     = 2500
rated_torque_Nm     = 1.34
bus_voltage_V       = 36
rated_current_A     = 11.2
max_outer_dia_mm    = 75
max_length_mm       = 100
max_temp_C          = 85
control_mode        = FOC

[Magnetic Material]
# NdFeB grade N38SH
Br_T                = 1.22
Hc_kApm             = 915
magnet_thickness_mm = 3.5
magnet_width_mm     = 20

[Geometry]
air_gap_mm          = 0.6
stator_inner_dia_mm = 65
iron_stack_len_mm   = 70

[Winding - preliminary]
# These are PRELIMINARY - subject to change after pole-slot selection
turns_per_slot      = 24
parallel_paths      = 2

[Winding Resistance - measured at 20C]
phase_resistance_ohm = 0.38

[Winding Inductance]
d_axis_inductance_mH = 4.2
q_axis_inductance_mH = 4.8
"""
with open(os.path.join(workspace, "project/specs/requirements.txt"), "w") as f:
    f.write(requirements)

# ── Candidate pole-slot table (some invalid, some valid) ──────────────────
pole_slot_csv = """\
candidate_id,poles_2p,slots_Q,phases,notes
A,4,12,3,low slot count
B,6,18,3,standard
C,8,36,3,preferred by factory
D,8,24,3,alternative
E,10,30,3,high pole
F,4,24,3,high q
G,6,36,3,another option
H,8,48,3,dense winding
I,2,12,3,high speed
J,6,9,3,unusual
K,8,6,3,INVALID too few slots
L,4,4,3,INVALID q<1
"""
with open(os.path.join(workspace, "project/specs/pole_slot_candidates.csv"), "w") as f:
    f.write(pole_slot_csv)

# ── Partial magnetic calc (intentionally incomplete/wrong format) ──────────
mag_partial = """\
MAGNETIC CIRCUIT PRELIMINARY NOTES
===================================
Last updated: 2023-11-02 (OUTDATED - do not use directly)

Air gap flux density estimate (rough):
  Bg_rough = Br * hm / (hm + delta * Kc)
  where Kc (Carter factor) ~ 1.15 (assumed)

Old working point: Bm/Br ~ 58% (8-pole 24-slot design, SUPERSEDED)

Note: Final values must come from full MEC calculation per current spec.
Do NOT use these values in the report.

Stray factor: ksf = 1.15
Leakage: sigma = 0.12
"""
with open(os.path.join(workspace, "project/magnetic/mag_prelim_notes.txt"), "w") as f:
    f.write(mag_partial)

# ── Legacy FOC config with WRONG formulas ─────────────────────────────────
legacy_foc = """\
// FOC Configuration - LEGACY v0.1 (DO NOT USE)
// WARNING: Temperature correction formula below is INCORRECT
// It uses +0.5%/C which is wrong for copper windings

#define POLE_PAIRS      4
#define R_PHASE_20C     0.38f   // Ohm
#define L_D_mH          4.2f
#define L_Q_mH          4.8f
#define KE_V_RAD_S      0.0f    // Not calculated yet

// WRONG temperature correction (legacy):
// R_hot = R_20C * (1 + 0.005 * (T_hot - 20))  // <-- WRONG, 0.5%/C

// WRONG bandwidth (legacy):
// current_bw_Hz = R / L;  // <-- WRONG, missing 0.5 factor
// speed_bw_Hz   = current_bw_Hz / 5.0;  // <-- WRONG, should be /10
"""
with open(os.path.join(workspace, "project/foc/foc_legacy_v01.c"), "w") as f:
    f.write(legacy_foc)

# ── Distractor: old simulation results ────────────────────────────────────
sim_old = """\
Maxwell 2D Simulation Results - ARCHIVE (8-pole 24-slot, OLD GEOMETRY)
Bg_sim = 0.72 T
T_cog_pk = 0.035 Nm
T_avg = 1.21 Nm
P_fe_50Hz = 12.3 W
THD_emf = 4.2%
NOTE: These results are for the OLD geometry. Discard for current design.
"""
with open(os.path.join(workspace, "project/simulation_results/maxwell_archive_8p24s.txt"), "w") as f:
    f.write(sim_old)

# ── Distractor: winding table (wrong slot count) ──────────────────────────
winding_old = """\
Winding Layout - 8p24s (DEPRECATED)
Slot 1: +A  Slot 2: +A  Slot 3: +B  ...
Coil pitch: 3 slots
End turn estimate: 15mm
"""
with open(os.path.join(workspace, "project/winding/layout_8p24s_deprecated.txt"), "w") as f:
    f.write(winding_old)

# ── Distractor: generic motor formulas (incorrect Kw formula) ─────────────
generic_formulas = """\
Generic Motor Formulas Reference
=================================
Torque = Kt * I
Power = T * omega
Ke = V_phase / omega  (approx, ignores winding factor)
Kt = 3/2 * np * psi_m  (dq frame)

NOTE: These are generic approximations. Use workflow-specific
calculations for actual design work.
"""
with open(os.path.join(workspace, "docs/references/generic_motor_formulas.txt"), "w") as f:
    f.write(generic_formulas)

# ── Distractor: project management file ───────────────────────────────────
pm_file = """\
Project Timeline - HVAC-Fan-350
================================
Week 1: Requirements review
Week 2-3: Electromagnetic design
Week 4: Prototype winding
Week 5-6: Dynamometer testing
Week 7: FOC tuning
Week 8: Final report
"""
with open(os.path.join(workspace, "project/specs/project_timeline.txt"), "w") as f:
    f.write(pm_file)

# ── Distractor: archive notes ─────────────────────────────────────────────
for ver, note in [("v0.1", "Initial sizing only, no validation"),
                  ("v0.2", "Added magnetic calc but used wrong Br value (1.18T)")]:
    with open(os.path.join(workspace, f"project/archive/{ver}/design_notes.txt"), "w") as f:
        f.write(f"Archive {ver}: {note}\n")

# ── Distractor: winding resistance measurement log ────────────────────────
meas_log = """\
Resistance Measurement Log
===========================
Sample A: 0.376 Ohm (Phase A-B, 20C)
Sample B: 0.382 Ohm (Phase A-B, 20C)
Sample C: 0.381 Ohm (Phase A-B, 20C)
Average: 0.380 Ohm -> use 0.38 Ohm in design
"""
with open(os.path.join(workspace, "project/magnetic/resistance_measurement_log.txt"), "w") as f:
    f.write(meas_log)

# ── Distractor: Python script with wrong temperature formula ─────────────
wrong_temp_script = """\
# DO NOT USE - incorrect temperature coefficient
def resistance_at_temp(R_20, T):
    # Wrong: uses 0.39% per degree (NTC resistor formula, not copper)
    return R_20 * (1 + 0.0039 * (T - 20))

if __name__ == '__main__':
    print(resistance_at_temp(0.38, 75))
"""
with open(os.path.join(workspace, "project/tools/scripts/wrong_temp_correction.py"), "w") as f:
    f.write(wrong_temp_script)

# ── Distractor: slot fill table ───────────────────────────────────────────
slot_fill = """\
Slot Fill Rate Guidelines
==========================
Manual winding:   40-50%
Semi-auto:        50-60%
Auto needle:      55-65%
Target this project: 50%

Slot dimensions (8p36s geometry):
  Slot width (avg): 4.8 mm
  Slot depth: 12.5 mm
  Slot area: ~55 mm^2
  Usable area @ 50%: 27.5 mm^2
"""
with open(os.path.join(workspace, "project/winding/slot_fill_reference.txt"), "w") as f:
    f.write(slot_fill)

# ── Distractor: Maxwell mesh config ───────────────────────────────────────
mesh_cfg = """\
# Maxwell 2D mesh settings reference (from previous project)
air_gap_mesh_mm    = 0.08
magnet_mesh_mm     = 0.15
stator_tooth_mm    = 0.20
stator_yoke_mm     = 0.50
air_box_mm         = 2.00
expected_elements  = 80000-150000
"""
with open(os.path.join(workspace, "project/simulation_results/mesh_config_reference.txt"), "w") as f:
    f.write(mesh_cfg)

# ── Distractor: tools template (empty placeholders) ───────────────────────
template_empty = """\
# Report Template Placeholder
# This file intentionally left empty pending design inputs.
# See SKILL.md for correct output format.
"""
with open(os.path.join(workspace, "project/tools/templates/report_placeholder.md"), "w") as f:
    f.write(template_empty)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        rel = os.path.relpath(os.path.join(root, fname), workspace)
        print(f"  {rel}")