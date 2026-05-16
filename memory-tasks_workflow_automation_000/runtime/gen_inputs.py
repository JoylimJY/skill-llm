#!/usr/bin/env python3
"""
Build the initial sandbox workspace for the drug-discovery pipeline task-tracking exam.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "memory/schema",
    "memory/notes",
    "tasks",
    "research/assays",
    "research/compounds",
    "research/reports",
    "pipeline/stages",
    "pipeline/logs",
    "admin/hr",
    "admin/finance",
    "docs/protocols",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

(WORKSPACE / "research/assays/IC50_batch_2024Q3.csv").write_text(
    "compound_id,IC50_nM,std_dev\nCPD-001,12.4,0.8\nCPD-002,340.1,15.2\nCPD-003,7.9,0.3\n"
)

(WORKSPACE / "research/compounds/lead_series_A.sdf").write_text(
    "$$$$\nCPD-001\n  Mrv2211\n\n  0  0  0     0  0            999 V3000\n$$$$\n"
)

(WORKSPACE / "research/reports/q3_progress.txt").write_text(
    "Q3 Progress Report\nTotal compounds screened: 450\nHits identified: 12\nLead series A advancing to ADMET profiling.\n"
)

(WORKSPACE / "pipeline/stages/stage_definitions.json").write_text(
    json.dumps({
        "stages": ["target_id", "hit_id", "lead_opt", "candidate_selection", "IND_enabling"],
        "current_stage": "lead_opt"
    }, indent=2)
)

(WORKSPACE / "pipeline/logs/run_2024_10_15.log").write_text(
    "[INFO] Docking run started: 450 compounds\n[INFO] Completed: 448/450\n[WARN] 2 compounds failed energy minimization\n[INFO] Top 12 hits exported to results/\n"
)

(WORKSPACE / "admin/hr/team_roster.csv").write_text(
    "name,role,department\nDr. Sarah Lin,Principal Scientist,Chemistry\nDr. Kwame Asante,Assay Lead,Biology\nPriya Mehta,Data Scientist,Informatics\n"
)

(WORKSPACE / "admin/finance/budget_q4.txt").write_text(
    "Q4 Budget Allocation\nExternal CRO: $450,000\nConsumables: $120,000\nCompute: $35,000\n"
)

(WORKSPACE / "docs/protocols/ADMET_SOP_v3.md").write_text(
    "# ADMET Screening SOP v3\n\n## Scope\nStandard operating procedure for ADMET profiling of lead compounds.\n\n## Steps\n1. Receive compound plates from Chemistry\n2. Run solubility assay (nephelometry)\n3. Run Caco-2 permeability\n4. Run hERG inhibition assay\n5. Report to project team\n"
)

(WORKSPACE / "docs/protocols/crystallography_protocol.md").write_text(
    "# X-ray Crystallography Protocol\n\nUsed for structure-based drug design. Contact Dr. Lin for crystal preparation.\n"
)

(WORKSPACE / "research/reports/competitor_landscape.txt").write_text(
    "Competitor Analysis — Target KRAS-G12C\nCompany A: Phase II (oral inhibitor)\nCompany B: Pre-clinical (covalent)\nOur position: Lead optimization, 18-month gap to closest competitor\n"
)

(WORKSPACE / "memory/notes/project_overview.md").write_text(
    "---\ntitle: KRAS-G12C Project Overview\ntype: note\n---\n\n# KRAS-G12C Project Overview\n\nThis project aims to develop a covalent KRAS-G12C inhibitor for NSCLC.\n\n## Key Goals\n- Identify a clinical candidate by Q2 2026\n- Achieve >10-fold selectivity over wild-type KRAS\n"
)

# ── BROKEN / INCOMPLETE schema note (agent must fix/replace it) ──────────────
# Intentionally wrong: missing required fields, wrong path implication by content
(WORKSPACE / "memory/schema/Task.md").write_text(
    "---\ntitle: Task\ntype: schema\n---\n\n# Task (INCOMPLETE - DO NOT USE)\n\nThis schema stub was never finished.\n"
)

# ── Raw research briefs the agent must convert to Task notes ─────────────────

(WORKSPACE / "pipeline/stages/work_brief_ADMET.txt").write_text(
    """WORK BRIEF — ADMET PROFILING CAMPAIGN
Assigned to: Priya Mehta
Priority: High

What needs doing:
Run full ADMET profiling on the 12 hits from the Q3 docking campaign (see IC50_batch_2024Q3.csv).
We need solubility, permeability, metabolic stability, and hERG data for all 12 compounds.

Concrete steps needed:
1. Pull hit list from Q3 docking results and confirm 12 compound IDs
2. Request compound plates from Chemistry store (contact Dr. Lin)
3. Run nephelometry solubility assay per SOP v3
4. Run Caco-2 permeability assay per SOP v3
5. Run metabolic stability (HLM/RLM) — outsource to CRO BioAssay Partners
6. Run hERG patch-clamp assay
7. Compile data into ADMET report and present to project team

Currently on step: 1
Started: 2024-10-14

Key context for resumption:
- Hit list is in research/assays/IC50_batch_2024Q3.csv
- SOP is docs/protocols/ADMET_SOP_v3.md
- CRO contact: contracts/BioAssay_Partners_MSA.pdf
- Priya is sole owner; escalate blockers to Dr. Asante
"""
)

(WORKSPACE / "pipeline/stages/work_brief_crystallography.txt").write_text(
    """WORK BRIEF — CRYSTAL STRUCTURE OF LEAD COMPOUND CPD-001
Assigned to: Dr. Sarah Lin
Priority: High

What needs doing:
Obtain a co-crystal structure of CPD-001 bound to KRAS-G12C to guide next round of lead optimization.
This is blocking the medicinal chemistry team from designing the next analogue series.

BLOCKED BY:
- CPD-001 resupply delayed — Chemistry needs 50 mg pure material; current stock is 8 mg.
- Crystal soaking conditions not yet optimized for this scaffold class.

Steps:
1. Confirm CPD-001 resupply ETA with synthesis team (target: 50 mg)
2. Optimize crystal soaking conditions using existing 8 mg stock (buffer screen)
3. Mount crystals and collect diffraction data at Diamond Light Source (beamtime booked Nov 3)
4. Process diffraction data with DIALS/CCP4
5. Refine and deposit structure; share with MedChem team

Currently on step: 2
Started: 2024-10-10
"""
)

(WORKSPACE / "pipeline/stages/work_brief_selectivity.txt").write_text(
    """WORK BRIEF — SELECTIVITY PANEL FOR LEAD SERIES A
Assigned to: Dr. Kwame Asante
Priority: Medium

What needs doing:
Run a 50-kinase selectivity panel on the top 3 leads (CPD-001, CPD-002, CPD-003) to confirm
>10-fold selectivity over wild-type KRAS and off-target kinase profile.

Steps:
1. Confirm panel design with Dr. Lin (which 50 kinases, which concentrations)
2. Prepare compound dilution plates (10-point dose-response)
3. Ship plates to Eurofins kinase panel service
4. Receive and QC raw data from Eurofins
5. Analyse selectivity data; flag any off-target hits >50% inhibition at 1 µM
6. Write selectivity report for IND package

Currently on step: 1
Started: 2024-10-16
"""
)

# ── A stub note showing wrong usage (to mislead naive agents) ────────────────
(WORKSPACE / "tasks/WRONG_EXAMPLE.md").write_text(
    """---
title: Wrong Example
type: Task
status: active
---

# Wrong Example

This note uses type: Task (capital T) in frontmatter directly,
and has NO observation fields in the body.
Also missing steps array and current_step in frontmatter.
DO NOT copy this pattern.
"""
)

print("Workspace scaffold generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")