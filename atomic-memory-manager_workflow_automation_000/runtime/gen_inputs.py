import os
import random

random.seed(42)

base = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "memory",
    "experiments/phase1",
    "experiments/phase2",
    "experiments/phase2/raw",
    "lab_protocols",
    "reports/q1",
    "reports/q2",
    "scripts",
    "collaborators",
    "data/sequencing",
    "data/proteomics",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── MEMORY.md — curated long-term memory ────────────────────────────────────
memory_md = """\
# Long-Term Memory

## Project Preferences
- Primary analysis pipeline: Nextflow on HPC cluster (not local)
- Data format standard: FASTQ + BAM, never raw BCL
- Report cadence: biweekly to PI, weekly internal standups

## Collaborators
- Basel lab lead: Dr. Ingrid Hoffmann (i.hoffmann@unibas.ch)
- External sequencing partner: GenomX Ltd (account #GX-8821)

## Phase 2 Decisions
- Target protein confirmed: KRAS G12C mutant isoform (agreed 2025-06-10 steering call)
- Animal model: PDX mouse (not syngeneic)
- Primary readout: tumor volume + ctDNA fraction

## Recurring Workflows
- Every new sample batch: register in LIMS before sequencing
- Post-sequencing QC threshold: Q30 ≥ 85%
"""
with open(os.path.join(base, "MEMORY.md"), "w") as f:
    f.write(memory_md)

# ── Daily notes ─────────────────────────────────────────────────────────────
daily_june10 = """\
# 2025-06-10

## Steering Committee Call
- Attendees: Dr. Hoffmann, PI Chen, Omar (PM), Lena (bioinformatics)
- Confirmed Phase 2 target: KRAS G12C mutant isoform
- PDX model approved; syngeneic rejected due to immunogenicity concerns
- Action: Omar to register PDX cohort in LIMS by 2025-06-13

## Sample Status
- Batches 1-6 fully sequenced and archived
- Batch 7 in prep, expected ready mid-June

## Notes
- Lena raised concern about frequentist stats for small n; no decision yet
"""
with open(os.path.join(base, "memory/2025-06-10.md"), "w") as f:
    f.write(daily_june10)

daily_june12 = """\
# 2025-06-12

## Bioinformatics Sync
- Nextflow pipeline v2.3.1 deployed on HPC
- Q30 scores for batches 4-6: 87%, 89%, 91% — all passing threshold
- Lena to present PCA plots Friday

## Admin
- GenomX invoice #INV-20250612 received; send to finance
- Reminder: Q2 report draft due 2025-06-30

## Misc
- Coffee machine on 3rd floor broken again
"""
with open(os.path.join(base, "memory/2025-06-12.md"), "w") as f:
    f.write(daily_june12)

# ── Distractor files ─────────────────────────────────────────────────────────

# Experiment logs
exp_log1 = """\
sample_id,batch,Q30,passed
S001,5,87.2,True
S002,5,85.1,True
S003,5,82.3,False
S004,6,90.1,True
"""
with open(os.path.join(base, "experiments/phase2/raw/batch5_qc.csv"), "w") as f:
    f.write(exp_log1)

exp_log2 = """\
sample_id,batch,Q30,passed
S010,6,91.3,True
S011,6,88.7,True
"""
with open(os.path.join(base, "experiments/phase2/raw/batch6_qc.csv"), "w") as f:
    f.write(exp_log2)

# Protocol files
with open(os.path.join(base, "lab_protocols/pdx_implantation_v3.txt"), "w") as f:
    f.write("PDX Implantation Protocol v3\n\nStep 1: Thaw cells at 37C\nStep 2: ...\n")

with open(os.path.join(base, "lab_protocols/dna_extraction_qiagen.txt"), "w") as f:
    f.write("DNA Extraction Protocol (Qiagen DNeasy)\n\nFor tissue samples up to 25mg.\n")

# Reports
with open(os.path.join(base, "reports/q1/q1_summary.txt"), "w") as f:
    f.write("Q1 Summary: Completed Phase 1 screening. 12 targets evaluated, 1 advanced.\n")

with open(os.path.join(base, "reports/q2/q2_draft_outline.txt"), "w") as f:
    f.write("Q2 Report Outline\n1. Phase 2 kickoff\n2. Sample processing\n3. Preliminary data\n")

# Scripts
with open(os.path.join(base, "scripts/run_nextflow.sh"), "w") as f:
    f.write("#!/bin/bash\nnextflow run main.nf -profile hpc --input samplesheet.csv\n")

with open(os.path.join(base, "scripts/qc_filter.py"), "w") as f:
    f.write("import pandas as pd\ndf = pd.read_csv('qc.csv')\nprint(df[df['Q30'] >= 85])\n")

# Collaborator files
with open(os.path.join(base, "collaborators/basel_lab_contacts.txt"), "w") as f:
    f.write("Basel Collaborators:\n- Dr. Ingrid Hoffmann (PI liaison)\n- Marco Bauer (lab tech)\n")

with open(os.path.join(base, "collaborators/genomx_contract.txt"), "w") as f:
    f.write("GenomX Ltd\nContract start: 2025-01-01\nAccount: GX-8821\nSLA: 14 days turnaround\n")

# Data placeholders
with open(os.path.join(base, "data/sequencing/batch7_manifest.txt"), "w") as f:
    f.write("Batch 7 Manifest\nSamples: S020-S031\nPrep date: 2025-06-13\nStatus: PREP\n")

with open(os.path.join(base, "data/proteomics/kras_g12c_abundance.tsv"), "w") as f:
    f.write("gene\tcondition\tabundance\nKRAS\tG12C_mutant\t4.23\nKRAS\twildtype\t1.00\n")

# Experiment phase 1 distractor
with open(os.path.join(base, "experiments/phase1/screening_results.csv"), "w") as f:
    f.write("target,hits,advanced\nKRAS,12,1\nBRAF,8,0\nEGFR,15,0\n")

print("Workspace generated successfully.")