#!/usr/bin/env python3
"""
Generate a realistic MD post-processing sandbox workspace.
All random operations use fixed seeds for determinism.
"""

import os
import random
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "simulation/run01",
    "simulation/run02",
    "simulation/raw_data",
    "analysis/rmsd",
    "analysis/energy",
    "analysis/hbond",
    "analysis/rmsf",
    "parameters/mdp",
    "parameters/topol",
    "scripts",
    "results",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Helper: write a realistic XVG file ───────────────────────────────────────
def write_xvg(path, title, xlabel, ylabel, data_rows, extra_sets=None):
    """data_rows: list of tuples (time, val1[, val2, ...])"""
    lines = [
        f'# This file was created by GROMACS (mock)',
        f'@ title "{title}"',
        f'@ xaxis label "{xlabel}"',
        f'@ yaxis label "{ylabel}"',
        f'@ TYPE xy',
    ]
    if extra_sets:
        for i, label in enumerate(extra_sets):
            lines.append(f'@ s{i} legend "{label}"')
    for row in data_rows:
        lines.append("    ".join(f"{v:.6f}" for v in row))
    Path(path).write_text("\n".join(lines) + "\n")

# ── Fake simulation files ─────────────────────────────────────────────────────
# .tpr binary placeholder
(workspace / "simulation/run01/md.tpr").write_bytes(b'\x00GROMACS_TPR_MOCK\x00' * 8)

# .xtc trajectory placeholder (raw binary)
(workspace / "simulation/run01/md.xtc").write_bytes(b'\x00GROMACS_XTC_MOCK\x00' * 32)

# topology
topol_top = """; GROMACS topology (mock)
[ defaults ]
; nbfunc  comb-rule  gen-pairs  fudgeLJ  fudgeQQ
  1       2          yes        0.5      0.8333

[ moleculetype ]
; Name  nrexcl
Protein_chain_A  3

[ atoms ]
; nr  type  resnr  residu  atom  cgnr  charge  mass
  1   CT    1      MET     N     1     -0.3    14.007
  2   CT    1      MET     CA    2      0.1    12.011

[ molecules ]
; Compound  #mols
Protein_chain_A  1
SOL              10245
"""
(workspace / "parameters/topol/topol.top").write_text(topol_top)

# .ndx index file with groups
ndx_content = """[ System ]
 1 2 3 4 5 6 7 8 9 10

[ Protein ]
 1 2 3 4 5 6

[ Backbone ]
 1 3 5

[ C-alpha ]
 2 4 6

[ Water ]
 7 8 9 10

[ non-Protein ]
 7 8 9 10
"""
(workspace / "simulation/run01/index.ndx").write_text(ndx_content)

# .mdp parameter files (distractors)
nvt_mdp = """; NVT equilibration
integrator  = md
nsteps      = 50000
dt          = 0.002
tcoupl      = V-rescale
tau_t       = 0.1
ref_t       = 300
"""
(workspace / "parameters/mdp/nvt.mdp").write_text(nvt_mdp)

npt_mdp = """; NPT equilibration
integrator  = md
nsteps      = 50000
dt          = 0.002
pcoupl      = Parrinello-Rahman
tau_p       = 2.0
ref_p       = 1.0
"""
(workspace / "parameters/mdp/npt.mdp").write_text(npt_mdp)

md_mdp = """; Production MD
integrator  = md
nsteps      = 5000000
dt          = 0.002
nstout      = 5000
nstxout-compressed = 5000
"""
(workspace / "parameters/mdp/md.mdp").write_text(md_mdp)

# .edr energy file placeholder
(workspace / "simulation/run01/md.edr").write_bytes(b'\x00EDR_MOCK\x00' * 16)

# .log file
log_content = """
               GROMACS - gmx mdrun, version 2024.1
          :-)  Copyright (c) 1991-2024 The GROMACS Development Team  (-:

...
           Started mdrun on node 0 Fri Jan  1 00:00:00 2025

Step 0, time 0 (ps), lambda 0
...
Step 5000000, time 10000 (ps), lambda 0

  <======  ###############  ==>
  <====  A V E R A G E S  ====>
  <==  ###############  ======>

  Statistics over 5000001 steps using 10001 frames

  Energies (kJ/mol)
           Bond          Angle
    4.23183e+02    3.08123e+03

  Temperature (K)
    2.99987e+02

 gcq#304: "Must not write too much or too little." (Ira Glass)
"""
(workspace / "simulation/run01/md.log").write_text(log_content)

# Distractor analysis files (pre-existing, not what we want)
# Fake RMSF file
rmsf_data = [(i, 0.05 + 0.03 * np.sin(i * 0.3) + 0.01 * np.random.randn()) for i in range(1, 51)]
write_xvg(
    workspace / "analysis/rmsf/rmsf_backbone.xvg",
    "RMS fluctuation", "Residue", "RMSF (nm)",
    rmsf_data
)

# Fake energy file
times = np.linspace(0, 10000, 1001)
energy_data = [(-2.3e5 + 500 * np.random.randn() + t * 0.1, ) for t in times]
write_xvg(
    workspace / "analysis/energy/potential.xvg",
    "Potential Energy", "Time (ps)", "Potential (kJ/mol)",
    [(times[i], energy_data[i][0]) for i in range(len(times))]
)

# Fake hbond distractor
hb_data = [(t, int(12 + 3 * np.random.randn())) for t in times]
write_xvg(
    workspace / "analysis/hbond/hbond_number.xvg",
    "Hydrogen Bonds", "Time (ps)", "Number",
    hb_data
)

# run02 distractors
(workspace / "simulation/run02/nvt.tpr").write_bytes(b'\x00TPR_NVT\x00' * 4)
(workspace / "simulation/run02/npt.tpr").write_bytes(b'\x00TPR_NPT\x00' * 4)

# scripts directory distractor
(workspace / "scripts/old_analysis.sh").write_text("""#!/bin/bash
# Old analysis script - deprecated
echo "Running old analysis..."
gmx rmsf -s md.tpr -f md.xtc -o rmsf.xvg
""")

# results placeholder
(workspace / "results/notes.txt").write_text(
    "Simulation completed. 10 ns production run at 300K/1bar.\n"
    "System: 285 residues, ~45000 atoms including solvent.\n"
    "Need to post-process trajectory and run conformational analysis.\n"
)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")