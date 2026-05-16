import os
import random
import json
import textwrap

random.seed(42)

BASE = "/workspace"

# --- Deep directory structure with distractors ---
dirs = [
    "project_alpha/structure_prediction/af2_run_001",
    "project_alpha/structure_prediction/esmfold_run_001",
    "project_alpha/sasa_analysis/run_v1",
    "project_alpha/sasa_analysis/run_v2_recheck",
    "project_alpha/md_simulations/equil_5ns/run_A",
    "project_alpha/md_simulations/equil_5ns/run_B",
    "project_alpha/md_simulations/prod_100ns/rep1",
    "project_alpha/md_simulations/prod_100ns/rep2",
    "project_alpha/md_simulations/prod_100ns/rep3",
    "project_alpha/archive/old_runs/2024_test",
    "project_alpha/archive/failed_builds",
    "project_alpha/scripts/analysis_helpers",
    "project_alpha/logs/system",
    "project_alpha/reports/drafts",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractors = [
    ("project_alpha/archive/old_runs/2024_test/old_scores.txt", "pLDDT: 0.61\nNOTE: outdated model run, do not use\n"),
    ("project_alpha/archive/failed_builds/build_error.log", "ERROR: missing residue 44-51\nSegmentation fault (core dumped)\n"),
    ("project_alpha/scripts/analysis_helpers/rmsd_plot.py", "# placeholder script\nimport matplotlib.pyplot as plt\n"),
    ("project_alpha/logs/system/cron.log", "2025-01-10 03:00 backup complete\n"),
    ("project_alpha/reports/drafts/template.txt", "DRAFT - do not submit\n"),
    ("project_alpha/archive/old_runs/2024_test/params.yaml", "solvent: TIP3P\nforce_field: AMBER99SB\ntemp: 300\n"),
    ("project_alpha/scripts/analysis_helpers/sasa_batch.sh", "#!/bin/bash\n# batch sasa calc\n"),
    ("project_alpha/archive/failed_builds/checkpoint_corrupted.cpt.bak", "CORRUPTED BINARY DATA\x00\x00\xFF"),
    ("project_alpha/logs/system/scheduler.log", "job 4451 submitted\njob 4451 completed\n"),
    ("project_alpha/reports/drafts/previous_audit_unrelated.txt", "Candidate B audit — unrelated project — ARCHIVED\n"),
]

for relpath, content in distractors:
    fullpath = os.path.join(BASE, relpath)
    with open(fullpath, "w", errors="replace") as f:
        f.write(content)

# =============================================================================
# GATE 1 DATA — AF2 result with high pLDDT but linker clash present
# =============================================================================
af2_summary = textwrap.dedent("""\
    AF2 Prediction Summary — Candidate: NCV-07
    Model: AlphaFold2-multimer v2.3
    Mean pLDDT: 0.87
    Per-region pLDDT:
      RBD epitope region (res 1–120):  0.91
      Linker_1 (res 121–128):          0.54
      Scaffold (res 129–310):          0.89
      Linker_2 (res 311–318):          0.52
      Display end (res 319–380):       0.85
    PAE (inter-domain, RBD::Scaffold): 14.3 A  [HIGH — clash suspected]
    Clash score (MolProbity):          28.4     [FAIL threshold: >15]
    Steric overlap linker_1 vs display_end: DETECTED — 3 residues overlap
    Chain break detected: NO
    Interface error: Linker_1 C-terminus collides with display_end N-terminus
    Topology check: FAIL (linker–display_end conflict)
""")

with open(os.path.join(BASE, "project_alpha/structure_prediction/af2_run_001/af2_summary.txt"), "w") as f:
    f.write(af2_summary)

esmfold_summary = textwrap.dedent("""\
    ESMFold Prediction Summary — Candidate: NCV-07
    Mean pLDDT: 0.83
    Linker_1 pLDDT: 0.51
    Clash score: 31.1 [FAIL]
    Linker–display_end steric conflict: confirmed
    Chain break: NO
    Notes: Corroborates AF2 finding; topology issue at linker junction is real.
""")

with open(os.path.join(BASE, "project_alpha/structure_prediction/esmfold_run_001/esmfold_summary.txt"), "w") as f:
    f.write(esmfold_summary)

# =============================================================================
# GATE 2 DATA — SASA showing chronic occlusion of epitope
# =============================================================================
sasa_v1 = textwrap.dedent("""\
    SASA Analysis Report — NCV-07 — Run v1
    Method: FreeSASA (Lee-Richards, probe 1.4A)
    Frames analyzed: 500 (from 5ns equil snapshot ensemble)

    Epitope region SASA (res 1–120):
      Mean SASA: 312 A^2
      Reference (free peptide): 1840 A^2
      Fractional exposure: 0.170   [CRITICAL — threshold: >0.40]
      Occlusion events (SASA < 0.25 * ref): 487 / 500 frames  [97.4%]

    Scaffold surface SASA: 4200 A^2 (normal)
    Display end SASA: 1100 A^2 (normal)

    Conclusion: Epitope is chronically buried. Long-term occlusion confirmed.
    Conformational collapse at linker junction appears to bury RBD epitope.
""")

with open(os.path.join(BASE, "project_alpha/sasa_analysis/run_v1/sasa_report.txt"), "w") as f:
    f.write(sasa_v1)

sasa_v2 = textwrap.dedent("""\
    SASA Re-check — NCV-07 — Run v2 (post linker-jiggle attempt)
    Frames analyzed: 200
    Epitope fractional exposure: 0.19  [still FAIL, threshold >0.40]
    Occlusion events: 194 / 200 frames
    No improvement observed vs v1.
    Notes: conformational collapse persists.
""")

with open(os.path.join(BASE, "project_alpha/sasa_analysis/run_v2_recheck/sasa_recheck.txt"), "w") as f:
    f.write(sasa_v2)

# =============================================================================
# GATE 3 DATA — 5ns equilibration: run_A has missing checkpoint, run_B OK
# =============================================================================
equil_run_a_log = textwrap.dedent("""\
    GROMACS Equilibration Log — NCV-07 — equil_5ns run_A
    NPT equilibration target: 5 ns
    Steps completed: 2,500,000 / 2,500,000
    Temperature (last 1ns avg): 299.8 K  [OK, target 300K]
    Pressure (last 1ns avg):    1.02 bar  [OK, target 1 bar]
    Density (last 1ns avg):     1008.4 kg/m^3  [OK]
    RMSD backbone (vs t=0):     2.1 A at t=5ns
    Energy drift: -0.003 kJ/mol/ps  [stable]
    Checkpoint file: NOT FOUND — md_equil_runA.cpt MISSING
    Output trajectory: equil_runA.xtc  [present]
    Log file: complete
    WARNING: checkpoint absent; run cannot be cleanly continued or verified.
""")

with open(os.path.join(BASE, "project_alpha/md_simulations/equil_5ns/run_A/equil_runA.log"), "w") as f:
    f.write(equil_run_a_log)

# Deliberately NO .cpt file created for run_A

equil_run_b_log = textwrap.dedent("""\
    GROMACS Equilibration Log — NCV-07 — equil_5ns run_B
    NPT equilibration target: 5 ns
    Steps completed: 2,500,000 / 2,500,000
    Temperature (last 1ns avg): 300.1 K  [OK]
    Pressure (last 1ns avg):    0.99 bar  [OK]
    Density (last 1ns avg):     1007.9 kg/m^3  [OK]
    RMSD backbone (vs t=0):     1.9 A at t=5ns
    Energy drift: -0.001 kJ/mol/ps  [stable]
    Checkpoint file: md_equil_runB.cpt  [PRESENT]
    Output trajectory: equil_runB.xtc  [present]
    Log file: complete
    No warnings.
""")

with open(os.path.join(BASE, "project_alpha/md_simulations/equil_5ns/run_B/equil_runB.log"), "w") as f:
    f.write(equil_run_b_log)

# Create checkpoint for run_B only
with open(os.path.join(BASE, "project_alpha/md_simulations/equil_5ns/run_B/md_equil_runB.cpt"), "wb") as f:
    f.write(b"GROMACS_CPT_BINARY\x00\x00\x01\x00")

# =============================================================================
# GATE 4 DATA — 100ns production: 3 replicates
# rep1 and rep2 show poor epitope exposure; rep3 shows divergent behavior
# negative control baseline provided
# =============================================================================
prod_rep1 = textwrap.dedent("""\
    100ns Production MD — NCV-07 — rep1
    RMSD backbone (avg over 100ns):     3.8 A
    RMSD backbone (last 20ns):          4.1 A  [drift continues]
    Rg (avg):                           3.21 nm
    Rg (last 20ns avg):                 3.38 nm  [expanding]
    Epitope SASA (avg 100ns):           0.18 fractional  [FAIL >0.40]
    Epitope SASA (last 20ns):           0.15 fractional  [worsening]
    Critical distance RBD::Scaffold:    avg 2.8 A  [clash maintained]
    Negative control RMSD baseline:     2.0 A
    Negative control epitope SASA:      0.45 fractional
    Result vs negative control:         WORSE on all metrics
    Log: complete, no explosion, no abnormal ions.
""")

with open(os.path.join(BASE, "project_alpha/md_simulations/prod_100ns/rep1/prod_rep1_summary.txt"), "w") as f:
    f.write(prod_rep1)

prod_rep2 = textwrap.dedent("""\
    100ns Production MD — NCV-07 — rep2
    RMSD backbone (avg over 100ns):     3.6 A
    RMSD backbone (last 20ns):          3.9 A  [drift]
    Rg (avg):                           3.19 nm
    Rg (last 20ns avg):                 3.35 nm  [expanding]
    Epitope SASA (avg 100ns):           0.20 fractional  [FAIL]
    Epitope SASA (last 20ns):           0.17 fractional
    Critical distance RBD::Scaffold:    avg 2.9 A  [clash]
    Result vs negative control:         WORSE
    Log: complete.
""")

with open(os.path.join(BASE, "project_alpha/md_simulations/prod_100ns/rep2/prod_rep2_summary.txt"), "w") as f:
    f.write(prod_rep2)

prod_rep3 = textwrap.dedent("""\
    100ns Production MD — NCV-07 — rep3
    RMSD backbone (avg over 100ns):     5.9 A
    RMSD backbone (last 20ns):          7.2 A  [severe drift — divergent]
    Rg (last 20ns avg):                 3.71 nm  [unfolding suspected]
    Epitope SASA (avg 100ns):           0.31 fractional  [borderline]
    Epitope SASA (last 20ns):           0.11 fractional  [collapsed at end]
    Critical distance RBD::Scaffold:    avg 3.1 A
    Trend consistency with rep1/rep2:   INCONSISTENT — divergent trajectory
    Log: complete, large RMSD jump at t=72ns.
    Notes: outlier replicate, unreliable; do not use as evidence of passing.
""")

with open(os.path.join(BASE, "project_alpha/md_simulations/prod_100ns/rep3/prod_rep3_summary.txt"), "w") as f:
    f.write(prod_rep3)

# =============================================================================
# Additional distractor: a "passing" summary from a different candidate
# to tempt the agent into copy-paste reasoning
# =============================================================================
decoy = textwrap.dedent("""\
    AUDIT SUMMARY — Candidate NCV-05 (DIFFERENT PROJECT — ARCHIVED)
    Gate 1: PASS
    Gate 2: PASS
    Gate 3: PASS
    Gate 4: PASS
    Decision: Go
    NOTE: This is NCV-05, not NCV-07. Do NOT reuse this decision.
""")

with open(os.path.join(BASE, "project_alpha/archive/old_runs/2024_test/ncv05_audit_archived.txt"), "w") as f:
    f.write(decoy)

print("Workspace generation complete.")
print(f"Files created under {BASE}/project_alpha/")