#!/usr/bin/env python3
"""
Generate a realistic Basic Memory workspace for a biotech research lab.
Simulates a messy real-world state with multiple entities needing lifecycle management.
"""

import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "research/active",
    "research/archive",
    "research/pipeline",
    "research/completed",
    "research/missed",
    "tasks/active",
    "tasks/completed",
    "meetings/active",
    "meetings/archive",
    "protocols/active",
    "protocols/archive",
    "grants/active",
    "grants/pipeline",
    "grants/archive",
    "notes",
    "contacts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Helper ──────────────────────────────────────────────────────────────────
def write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

# ════════════════════════════════════════════════════════════════════════════
# ENTITIES THE AGENT MUST ACT ON
# ════════════════════════════════════════════════════════════════════════════

# 1. CRISPR-Knockout Study  →  mark COMPLETED (move research/active → research/completed, status: active → completed, completed: "" → 2025-07-14)
write(WORKSPACE / "research/active/crispr-knockout-study.md", """\
---
title: CRISPR Knockout Study
type: research-initiative
status: active
started: 2024-11-01
completed:
lead: Dr. Chen
tags: [crispr, gene-editing, oncology]
---

# CRISPR Knockout Study

Investigating CRISPR-Cas9 knockout of BRCA2 in HER2+ cell lines to model homologous
recombination deficiency.

## Objectives
- [[protocol/cas9-delivery]] validated in vitro
- Off-target sequencing complete
- Phenotypic characterisation submitted to journal

## Relations
- related-to: [[research/active/brca2-expression-panel]]
- uses-protocol: [[protocols/active/cas9-delivery-v3]]
- led-by: [[contacts/dr-chen]]

## Observations
- [2025-06-30] All sequencing data received and QC-passed
- [2025-07-10] Manuscript accepted by Nature Methods
""")

# 2. Metabolomics Pilot  →  mark MISSED (deadline passed; move research/active → research/missed, status: active → missed)
write(WORKSPACE / "research/active/metabolomics-pilot.md", """\
---
title: Metabolomics Pilot
type: research-initiative
status: active
started: 2024-09-15
deadline: 2025-06-30
completed:
lead: Dr. Okafor
tags: [metabolomics, mass-spec, diabetes]
---

# Metabolomics Pilot

LC-MS/MS profiling of serum metabolites in T2D cohort. Funding window expired
before recruitment target was reached.

## Objectives
- Recruit 80 participants ← only 31 enrolled before deadline
- Run MS analysis
- Submit interim report to NIH

## Relations
- funded-by: [[grants/archive/nih-pilot-2024]]
- involves: [[contacts/dr-okafor]]

## Observations
- [2025-06-28] Recruitment closed — 31/80 target met
- [2025-06-30] NIH funding window lapsed; initiative cannot continue
""")

# 3. Protein-Folding ML Model  →  ALREADY in research/completed (agent should NOT move it, just report it)
write(WORKSPACE / "research/completed/protein-folding-ml-model.md", """\
---
title: Protein Folding ML Model
type: research-initiative
status: completed
started: 2024-03-01
completed: 2025-04-18
lead: Dr. Patel
tags: [machine-learning, alphafold, structural-biology]
---

# Protein Folding ML Model

Fine-tuned AlphaFold2 variant for predicting IDR conformations in disordered
proteins. Model weights published on Zenodo.

## Observations
- [2025-04-10] Model benchmark surpassed baselines on CASP15 targets
- [2025-04-18] Weights uploaded; DOI issued
""")

# 4. Organoid Drug-Screen  →  PAUSED / on-hold (frontmatter status update ONLY, NO folder move, status: active → paused)
write(WORKSPACE / "research/active/organoid-drug-screen.md", """\
---
title: Organoid Drug Screen
type: research-initiative
status: active
started: 2025-01-20
completed:
lead: Dr. Russo
tags: [organoids, drug-screening, colorectal]
---

# Organoid Drug Screen

High-throughput drug sensitivity profiling in patient-derived colorectal organoids.
Temporarily paused pending ethics amendment approval.

## Objectives
- Screen 240 compounds across 12 organoid lines
- Validate hits in PDX models

## Relations
- pending: [[grants/active/wellcome-organoid-grant]]
- led-by: [[contacts/dr-russo]]

## Observations
- [2025-07-01] Ethics amendment submitted
- [2025-07-08] Study paused pending IRB re-approval (expected 6-8 weeks)
""")

# 5. Epigenomics Pipeline  →  REACTIVATE (was wrongly archived; move research/archive → research/active, status: completed → active)
write(WORKSPACE / "research/archive/epigenomics-pipeline.md", """\
---
title: Epigenomics Pipeline
type: research-initiative
status: completed
started: 2025-02-10
completed: 2025-06-01
lead: Dr. Kim
tags: [epigenomics, atac-seq, pipeline]
---

# Epigenomics Pipeline

ATAC-seq + ChIP-seq data processing pipeline. Mistakenly archived — active
development is still ongoing for v2.0 feature branch.

## Objectives
- v1.0 released ✓
- v2.0 peak-calling improvements (IN PROGRESS)
- Integration with ENCODE metadata API

## Relations
- maintained-by: [[contacts/dr-kim]]
- uses: [[protocols/active/atac-seq-qc]]

## Observations
- [2025-06-01] v1.0 tagged and released (archived prematurely)
- [2025-07-05] Team confirmed v2.0 work ongoing — should not have been archived
""")

# ════════════════════════════════════════════════════════════════════════════
# DISTRACTOR FILES (≥10) — realistic noise
# ════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "research/active/brca2-expression-panel.md", """\
---
title: BRCA2 Expression Panel
type: research-initiative
status: active
started: 2025-03-01
lead: Dr. Chen
tags: [brca2, expression, panel]
---

# BRCA2 Expression Panel

Quantitative RT-PCR panel for BRCA2 isoform expression across 6 cell lines.
""")

write(WORKSPACE / "research/pipeline/single-cell-atlas.md", """\
---
title: Single Cell Atlas
type: research-initiative
status: pipeline
started:
lead: Dr. Okafor
tags: [single-cell, atlas, multi-omics]
---

# Single Cell Atlas

Proposed 10x Genomics atlas of tumour microenvironment. Awaiting funding decision.
""")

write(WORKSPACE / "tasks/active/submit-ethics-amendment.md", """\
---
title: Submit Ethics Amendment
type: task
status: active
due: 2025-07-15
assigned: Dr. Russo
---

# Submit Ethics Amendment

File amendment form with IRB for organoid drug screen expansion.
""")

write(WORKSPACE / "tasks/active/order-cas9-reagents.md", """\
---
title: Order CAS9 Reagents
type: task
status: active
due: 2025-07-20
assigned: Lab Manager
---

# Order CAS9 Reagents

Restock Cas9 protein and guide RNA synthesis kits.
""")

write(WORKSPACE / "tasks/completed/setup-sequencing-pipeline.md", """\
---
title: Setup Sequencing Pipeline
type: task
status: completed
due: 2025-04-01
completed: 2025-03-28
assigned: Dr. Kim
---

# Setup Sequencing Pipeline

Configured Nextflow pipeline for ATAC-seq processing.
""")

write(WORKSPACE / "meetings/active/lab-meeting-2025-07-09.md", """\
---
title: Lab Meeting 2025-07-09
type: meeting
status: active
date: 2025-07-09
---

# Lab Meeting Notes

- CRISPR knockout results presented
- Organoid screen pause discussed
- Epigenomics v2.0 roadmap reviewed
""")

write(WORKSPACE / "protocols/active/cas9-delivery-v3.md", """\
---
title: CAS9 Delivery Protocol v3
type: protocol
status: active
version: 3.0
---

# CAS9 Delivery Protocol v3

Electroporation-based delivery of Cas9 RNP complexes into suspension cell lines.
""")

write(WORKSPACE / "protocols/active/atac-seq-qc.md", """\
---
title: ATAC-seq QC Protocol
type: protocol
status: active
version: 1.2
---

# ATAC-seq QC Protocol

FastQC + TSS enrichment scoring for ATAC-seq libraries.
""")

write(WORKSPACE / "grants/active/wellcome-organoid-grant.md", """\
---
title: Wellcome Organoid Grant
type: grant
status: active
amount: 250000
pi: Dr. Russo
deadline: 2025-12-01
---

# Wellcome Organoid Grant

Wellcome Trust grant supporting organoid drug screen programme.
""")

write(WORKSPACE / "grants/archive/nih-pilot-2024.md", """\
---
title: NIH Pilot 2024
type: grant
status: completed
amount: 75000
pi: Dr. Okafor
completed: 2025-06-30
---

# NIH Pilot Grant 2024

Small R21 pilot grant for metabolomics work. Funding period ended June 2025.
""")

write(WORKSPACE / "contacts/dr-chen.md", """\
---
title: Dr. Chen
type: contact
role: Principal Investigator
department: Oncology
---

# Dr. Chen

PI for CRISPR and BRCA2 projects.
""")

write(WORKSPACE / "contacts/dr-okafor.md", """\
---
title: Dr. Okafor
type: contact
role: Senior Researcher
department: Metabolomics
---

# Dr. Okafor
""")

write(WORKSPACE / "contacts/dr-kim.md", """\
---
title: Dr. Kim
type: contact
role: Bioinformatics Lead
department: Computational Biology
---

# Dr. Kim
""")

write(WORKSPACE / "contacts/dr-russo.md", """\
---
title: Dr. Russo
type: contact
role: Senior Researcher
department: Oncology
---

# Dr. Russo
""")

write(WORKSPACE / "notes/lab-inventory-2025-q2.md", """\
---
title: Lab Inventory Q2 2025
type: note
status: active
---

# Lab Inventory Q2 2025

Reagent stock levels as of June 2025.
""")

write(WORKSPACE / "notes/publication-tracker.md", """\
---
title: Publication Tracker
type: note
status: active
---

# Publication Tracker

| Initiative | Journal | Status |
|---|---|---|
| CRISPR Knockout | Nature Methods | Accepted |
| Protein Folding ML | eLife | Published |
""")

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*.md')))}")