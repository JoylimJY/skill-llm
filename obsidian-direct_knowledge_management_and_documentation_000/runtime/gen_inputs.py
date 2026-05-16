#!/usr/bin/env python3
"""Generate a realistic biomedical research Obsidian vault with messy, realistic content."""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

VAULT_PATH = Path("/home/ruslan/webdav/data/ruslain")

def make_timestamp(days_ago=0):
    dt = datetime.now() - timedelta(days=days_ago)
    return dt.isoformat(timespec='seconds')

def write_note(path, frontmatter_dict, body):
    """Write a note with frontmatter."""
    import yaml
    fm_yaml = yaml.dump(frontmatter_dict, default_flow_style=False, allow_unicode=True).strip()
    content = f"---\n{fm_yaml}\n---\n\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

# Create .obsidian config
obsidian_config = VAULT_PATH / ".obsidian"
obsidian_config.mkdir(parents=True, exist_ok=True)
(obsidian_config / "app.json").write_text('{"legacyEditor": false}')
(obsidian_config / "workspace.json").write_text('{"main": {"id": "main", "type": "leaf"}}')

# === FOLDER: Research/Protocols ===
write_note(
    VAULT_PATH / "Research" / "Protocols" / "PCR Protocol.md",
    {
        "created": make_timestamp(120),
        "modified": make_timestamp(30),
        "tags": ["protocol", "pcr", "molecular-biology"]
    },
    """# PCR Protocol

Standard PCR amplification protocol for our lab.

## Equipment
- Thermocycler (BioRad T100)
- Microcentrifuge
- Pipettes (P20, P200, P1000)

## Reagents
- Taq DNA Polymerase (NEB)
- dNTPs (10mM each)
- MgCl2 (25mM)
- Forward and Reverse primers (10µM)
- Template DNA

## Protocol Steps
1. Prepare master mix on ice
2. Add 2µL template to each reaction
3. Run thermocycler program: 95°C 5min, 35×(95°C 30s / 60°C 30s / 72°C 1min), 72°C 10min

## Troubleshooting
- No band: check primer Tm, increase MgCl2
- Smearing: reduce template or increase annealing temperature

## Summary
This is our standard PCR protocol used for all amplifications. Yields reliable results for fragments up to 3kb.
"""
)

write_note(
    VAULT_PATH / "Research" / "Protocols" / "Cell Culture SOP.md",
    {
        "created": make_timestamp(200),
        "modified": make_timestamp(5),
        "tags": ["protocol", "cell-culture", "sop"]
    },
    """# Cell Culture SOP

Standard operating procedures for cell culture maintenance.

## Cell Lines
- HEK293T
- MCF-7
- HeLa

## Media
DMEM + 10% FBS + 1% Pen/Strep

## Passaging Protocol
1. Aspirate media
2. Wash with PBS (5mL)
3. Add 1mL Trypsin, incubate 3min at 37°C
4. Neutralize with 9mL media
5. Centrifuge 300xg 5min
6. Resuspend at desired density

## Contamination Indicators
- Turbid media
- pH shift (color change)
- Visible particles

## Summary
Routine passaging every 3-4 days when cells reach 80% confluency.
"""
)

write_note(
    VAULT_PATH / "Research" / "Protocols" / "Western Blot Protocol.md",
    {
        "created": make_timestamp(90),
        "modified": make_timestamp(10),
        "tags": ["protocol", "western-blot", "protein-analysis"]
    },
    """# Western Blot Protocol

## Sample Preparation
- Lyse cells in RIPA buffer + protease inhibitors
- Quantify protein by BCA assay
- Load 20-30µg per lane

## Gel Electrophoresis
- Use 10% SDS-PAGE for proteins 30-100kDa
- Run at 120V in running buffer

## Transfer
- Semi-dry transfer, 25V, 30min
- PVDF membrane (pre-activated in methanol)

## Blocking & Antibodies
- Block 5% milk/TBST 1hr RT
- Primary antibody overnight 4°C
- Secondary HRP-conjugated 1hr RT

## Detection
ECL chemiluminescence

## Notes
For phospho-antibodies, use 5% BSA instead of milk for blocking.
"""
)

# === FOLDER: Research/Experiments ===
write_note(
    VAULT_PATH / "Research" / "Experiments" / "Experiment Log 2024-Q1.md",
    {
        "created": make_timestamp(180),
        "modified": make_timestamp(45),
        "tags": ["experiment", "log", "2024"]
    },
    """# Experiment Log 2024-Q1

## January
- 2024-01-10: PCR amplification of BRCA1 exon 11 - SUCCESS
- 2024-01-15: Western blot for p53 expression - bands visible at 53kDa
- 2024-01-22: Cell viability assay - IC50 calculated as 2.3µM

## February
- 2024-02-05: RNA extraction from MCF-7 cells - RIN > 8
- 2024-02-12: qPCR for GAPDH normalization - Ct values consistent
- 2024-02-20: Co-immunoprecipitation p53/MDM2 - positive interaction confirmed

## March
- 2024-03-01: Flow cytometry - apoptosis assay after drug treatment
- 2024-03-15: Microscopy imaging - confocal Z-stack BRCA1 nuclear localization
- 2024-03-28: Protein purification attempt 1 - low yield, protocol needs revision

## Key Findings
- Drug X shows selective cytotoxicity in BRCA1-mutant cells
- p53/MDM2 interaction disrupted by compound Y at 5µM
"""
)

write_note(
    VAULT_PATH / "Research" / "Experiments" / "Drug Screening Results.md",
    {
        "created": make_timestamp(60),
        "modified": make_timestamp(3),
        "tags": ["experiment", "drug-screening", "results", "oncology"]
    },
    """# Drug Screening Results

## Compound Library
Screened 48 compounds from NCI diversity set against MCF-7 and MDA-MB-231 cell lines.

## Hits (>50% inhibition at 10µM)
| Compound | MCF-7 IC50 | MDA-MB-231 IC50 | Selectivity |
|----------|-----------|-----------------|-------------|
| NSC-12345 | 1.2µM | 4.5µM | 3.75x |
| NSC-67890 | 0.8µM | 2.1µM | 2.6x |
| NSC-11111 | 3.4µM | 3.6µM | 1.1x (not selective) |

## Statistical Analysis
- n=3 independent experiments
- Errors = SEM
- p < 0.05 for all hits vs. control

## Notes
NSC-12345 shows promising selectivity for ER+ cells. Mechanism unknown.
"""
)

# === FOLDER: Research/Literature ===
write_note(
    VAULT_PATH / "Research" / "Literature" / "BRCA1 Mutation Review.md",
    {
        "created": make_timestamp(365),
        "modified": make_timestamp(60),
        "tags": ["literature", "review", "brca1", "cancer-genetics"]
    },
    """# BRCA1 Mutation Review

Summary of key literature on BRCA1 mutations in breast cancer.

## Key Papers
- Miki et al. 1994 - Original BRCA1 cloning
- Tavtigian et al. 1994 - BRCA2 identification
- Hall et al. 1990 - Linkage mapping to 17q21

## BRCA1 Function
- DNA double-strand break repair (HR pathway)
- Cell cycle checkpoint regulation
- Transcriptional activation

## Clinical Significance
- ~5-10% of breast cancers are hereditary
- BRCA1 carriers: 55-65% lifetime risk of breast cancer
- Associated with triple-negative breast cancer subtype

## Therapeutic Implications
- PARP inhibitors (olaparib) exploit synthetic lethality
- FDA approved for BRCA1/2-mutant cancers

## See Also
[[Drug Screening Results]]
[[Experiment Log 2024-Q1]]
"""
)

write_note(
    VAULT_PATH / "Research" / "Literature" / "p53 Pathway Overview.md",
    {
        "created": make_timestamp(300),
        "modified": make_timestamp(20),
        "tags": ["literature", "p53", "tumor-suppressor", "signaling"]
    },
    """# p53 Pathway Overview

## p53 as Guardian of the Genome
p53 (TP53) is mutated in ~50% of human cancers. Acts as transcription factor.

## Activation Signals
- DNA damage (ionizing radiation, UV)
- Oncogene activation (ARF pathway)
- Hypoxia
- Ribonucleotide depletion

## Key Downstream Targets
- CDKN1A (p21): cell cycle arrest
- BAX, PUMA: apoptosis
- MDM2: negative feedback loop

## MDM2-p53 Feedback Loop
MDM2 ubiquitinates p53 → proteasomal degradation
p53 activates MDM2 transcription → autoregulation

## Therapeutic Strategies
1. MDM2 inhibitors (Nutlin-3): reactivate p53 in WT tumors
2. APR-246: restore folded structure to mutant p53
3. Gene therapy approaches

## References
- Lane & Crawford 1979 - p53 discovery
- Vogelstein et al. 2000 - p53 review
"""
)

# === FOLDER: Projects ===
write_note(
    VAULT_PATH / "Projects" / "Grant Application Q2 2024.md",
    {
        "created": make_timestamp(50),
        "modified": make_timestamp(2),
        "tags": ["project", "grant", "funding", "2024"]
    },
    """# Grant Application Q2 2024

## Project Title
Synthetic Lethality Exploitation in BRCA1-Deficient Tumors

## Specific Aims
1. Characterize novel PARP inhibitor synergists from compound screen
2. Validate mechanism of action in cell-free system
3. In vivo efficacy in xenograft models

## Preliminary Data
- NSC-12345 shows 3.75x selectivity for BRCA1-mutant cells ([[Drug Screening Results]])
- Mechanism appears to involve replication fork stalling ([[Experiment Log 2024-Q1]])

## Timeline
Q2-Q3 2024: In vitro validation
Q4 2024: Mouse xenograft experiments
Q1 2025: Manuscript preparation

## Budget Notes
Personnel: 60%
Supplies: 30%
Indirect: 10%
"""
)

write_note(
    VAULT_PATH / "Projects" / "Collaboration with Chen Lab.md",
    {
        "created": make_timestamp(75),
        "modified": make_timestamp(12),
        "tags": ["project", "collaboration", "structural-biology"]
    },
    """# Collaboration with Chen Lab

## Overview
Joint project with Prof. Chen's structural biology lab at MIT.

## Our Contribution
- Cell-based assays for compound validation
- Protein expression and purification
- Biochemical binding assays

## Chen Lab Contribution
- X-ray crystallography of target protein
- Cryo-EM structure determination
- Computational docking studies

## Shared Resources
- Compound library access
- HPC cluster time for MD simulations

## Meeting Notes
- 2024-02-15: Kickoff meeting, agreed on MTA terms
- 2024-03-20: Data sharing - Chen lab sent first crystal structure (PDB: 8XYZ)
- 2024-04-10: Review progress, manuscript outline drafted

## Next Steps
- Complete kinetic measurements by end of May
- Share raw data via Dropbox by June 1
"""
)

# === FOLDER: Personal ===
write_note(
    VAULT_PATH / "Personal" / "Lab Meeting Presentations.md",
    {
        "created": make_timestamp(150),
        "modified": make_timestamp(7),
        "tags": ["personal", "presentations", "lab-meeting"]
    },
    """# Lab Meeting Presentations

## Upcoming
- May 20, 2024: Drug screening results (30 min slot)
- July 15, 2024: Mid-year progress report

## Past Presentations
- Jan 2024: Introduction to compound library approach
- Nov 2023: Literature review - PARP inhibitor mechanisms
- Sep 2023: Preliminary cell line characterization

## Tips
- Use clear figures with large fonts
- State hypothesis upfront
- Always have backup slides for methods

## Resources
- Lab presentation template (Google Slides)
- Journal club schedule
"""
)

write_note(
    VAULT_PATH / "Personal" / "Conference Notes - AACR 2024.md",
    {
        "created": make_timestamp(25),
        "modified": make_timestamp(8),
        "tags": ["personal", "conference", "aacr", "2024"]
    },
    """# Conference Notes - AACR 2024

## Key Sessions Attended

### Session 1: PARP Inhibitor Resistance
- Speaker: Dr. Johnson, MD Anderson
- Main point: BRCAness score predicts response better than mutation alone
- Interesting: CDK12 mutations cause tandem duplications → functional BRCA1-like phenotype

### Session 2: Liquid Biopsy Advances
- ctDNA detection sensitivity now < 0.01% VAF
- Combined methylation + mutation calling improves specificity

### Session 3: Immune Checkpoint in TNBC
- PD-L1 IHC scoring inconsistencies between labs
- Tumor mutational burden (TMB) as alternative biomarker

## Networking
- Met Dr. Williams from Genentech - interesting pipeline compound in Phase I
- Prof. Martinez (Barcelona) - potential collaboration on EU grant

## Action Items
- Follow up with Dr. Williams re compound data sharing
- Download poster from AACR portal: #1234
- Add AACR abstract to Zotero
"""
)

# === FOLDER: Methods ===
write_note(
    VAULT_PATH / "Methods" / "Bioinformatics Pipeline.md",
    {
        "created": make_timestamp(100),
        "modified": make_timestamp(15),
        "tags": ["methods", "bioinformatics", "ngs", "pipeline"]
    },
    """# Bioinformatics Pipeline

## Overview
Standard pipeline for NGS data analysis in our lab.

## Steps
1. **Quality Control**: FastQC → MultiQC report
2. **Trimming**: Trimmomatic (ILLUMINACLIP, LEADING:3, TRAILING:3, SLIDINGWINDOW:4:15)
3. **Alignment**: BWA-MEM to hg38 reference
4. **Post-alignment**: Picard MarkDuplicates, GATK BaseRecalibrator
5. **Variant Calling**: GATK HaplotypeCaller (germline) or Mutect2 (somatic)
6. **Annotation**: ANNOVAR, VEP
7. **Filtering**: PASS variants, MAF < 0.01, coverage > 20x

## Software Versions
- BWA 0.7.17
- GATK 4.3.0
- Python 3.10 (for custom scripts)

## Output Files
- VCF (filtered variants)
- BAM (aligned reads)
- HTML reports

## Notes
Always use genome build hg38. Avoid hg19 for new projects.
"""
)

write_note(
    VAULT_PATH / "Methods" / "Statistical Analysis Guide.md",
    {
        "created": make_timestamp(220),
        "modified": make_timestamp(50),
        "tags": ["methods", "statistics", "r", "guide"]
    },
    """# Statistical Analysis Guide

## Tests by Data Type

### Continuous Normally Distributed
- 2 groups: Student's t-test (unpaired) or Welch's t-test
- >2 groups: One-way ANOVA + Tukey's HSD

### Non-Normal / Ordinal
- 2 groups: Mann-Whitney U
- >2 groups: Kruskal-Wallis + Dunn's test

### Survival Data
- Log-rank test
- Cox proportional hazards model

## Multiple Testing Correction
Always apply Benjamini-Hochberg FDR for genomics data.
Bonferroni for targeted hypothesis testing.

## R Packages
- ggplot2: visualization
- survival: survival analysis
- limma: differential expression
- edgeR: count data

## Reporting Standards
- State exact test used
- Report effect size + confidence interval
- n = biological replicates (not technical)
"""
)

# === ROOT LEVEL NOTES ===
write_note(
    VAULT_PATH / "Lab Inbox.md",
    {
        "created": make_timestamp(10),
        "modified": make_timestamp(1),
        "tags": ["inbox", "todo"]
    },
    """# Lab Inbox

## Urgent
- Review NSC-12345 dose-response data before Friday meeting
- Order antibodies for next western blot panel
- Schedule lab safety training for new rotation student

## This Week
- Write methods section for grant application
- Analyze flow cytometry data from March experiment
- Reply to Dr. Chen's email about protein structure

## Backlog
- Update bioinformatics pipeline documentation
- Create protocol for new mass spec workflow
- Literature review on ferroptosis mechanisms

## Notes
Random ideas go here until categorized.
"""
)

write_note(
    VAULT_PATH / "Meeting Notes.md",
    {
        "created": make_timestamp(200),
        "modified": make_timestamp(4),
        "tags": ["meetings", "notes"]
    },
    """# Meeting Notes

## PI Meeting - 2024-04-15
- Discussed grant application progress
- NSC-12345 data looks promising, needs replication
- Suggested adding xenograft experiment to aims

## Lab Meeting - 2024-04-08
- Rotation student presenting confocal data
- Discussed imaging analysis pipeline improvements
- Action: upgrade ImageJ macro for batch processing

## Department Seminar - 2024-04-03
- Dr. Smith presented on ferroptosis regulation
- Key takeaway: GPX4 inhibition + RSL3 as novel combination

## Journal Club - 2024-03-25
- Discussed Nature paper on CRISPR base editing
- Interesting application for BRCA1 variant classification
"""
)

# The KEY note that the agent must find, read, and edit:
# "PCR Protocol" needs a "Key Takeaways" section added via replace-section
# It currently has a "Summary" section which the agent should update

# Create the target note for the task - Protein Purification Protocol
# This note exists but is INCOMPLETE - it's missing key sections
write_note(
    VAULT_PATH / "Research" / "Protocols" / "Protein Purification Protocol.md",
    {
        "created": make_timestamp(45),
        "modified": make_timestamp(20),
        "tags": ["protocol", "protein-purification", "biochemistry"]
    },
    """# Protein Purification Protocol

## Overview
Protocol for recombinant protein expression and purification from E. coli.

## Expression
- Transform BL21(DE3) with pET28a vector
- Grow in LB + kanamycin to OD600 = 0.6
- Induce with 0.5mM IPTG for 4hr at 30°C

## Lysis
- Resuspend pellet in lysis buffer (50mM Tris pH 8, 300mM NaCl, 10mM imidazole)
- Sonicate 3×30s on ice
- Centrifuge 15,000xg 30min 4°C

## Affinity Chromatography (His-tag)
- Load onto Ni-NTA resin equilibrated in lysis buffer
- Wash: 20mM imidazole, 5 column volumes
- Elute: 250mM imidazole

## Size Exclusion Chromatography
- Concentrate to <2mL using Amicon Ultra (30kDa cutoff)
- Run on Superdex 200 in SEC buffer
- Collect peak fractions

## Quality Control
- SDS-PAGE: check purity (>90% for downstream assays)
- Bradford/BCA: determine concentration
- Dynamic light scattering: check for aggregation

## Troubleshooting
- Protein in pellet after lysis: use 8M urea for denaturing purification
- Low yield: optimize IPTG concentration, induction temperature
- Aggregation: add 5% glycerol, reduce concentration

## Results Log
- 2024-03-28 Attempt 1: 0.2mg/mL final yield (low)
- Needs optimization
"""
)

print("Vault generated successfully at:", VAULT_PATH)
print("Notes created:")
for f in sorted(VAULT_PATH.rglob("*.md")):
    print(f"  {f.relative_to(VAULT_PATH)}")