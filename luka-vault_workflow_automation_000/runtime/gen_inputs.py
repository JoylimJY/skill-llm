import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# 1. Create a realistic nested directory structure with distractor files
# -------------------------------------------------------------------
dirs = [
    "data/raw/biotech",
    "data/raw/pharma",
    "data/processed",
    "data/archive/2022",
    "data/archive/2023",
    "reports/q1",
    "reports/q2",
    "config",
    "scripts/legacy",
    "notes",
    "exports",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files (irrelevant configs, old reports, etc.)
distractor_files = {
    "config/db_config.yaml": "host: localhost\nport: 5432\ndb: biotrack\n",
    "config/logging.conf": "[loggers]\nkeys=root\n[handlers]\nkeys=consoleHandler\n",
    "data/archive/2022/old_report.csv": "company,stage,funding\nAlpha Bio,Series A,12M\nBeta Pharma,Seed,3M\n",
    "data/archive/2023/market_summary.txt": "Global biotech market grew 8% in 2023.\nKey drivers: mRNA, CRISPR, AI drug discovery.\n",
    "data/processed/cleaned_leads.json": json.dumps([
        {"company": "NovaBio", "focus": "oncology", "founded": 2019},
        {"company": "GenVault", "focus": "genomics", "founded": 2021},
    ], indent=2),
    "reports/q1/pipeline_review.txt": "Q1 pipeline: 14 prospects identified, 3 warm leads.\n",
    "reports/q2/competitive_landscape.txt": "Emerging CRISPR startups dominate Series A activity.\n",
    "notes/interview_notes.txt": "Dr. Patel mentioned SynthCell as a breakout candidate.\n",
    "notes/raw_links.txt": "https://www.nature.com/biotech\nhttps://www.fiercebiotech.com\n",
    "exports/contacts.csv": "name,email,org\nJane Doe,jane@novabio.com,NovaBio\nAlex Chen,alex@synthcell.io,SynthCell\n",
    "scripts/legacy/old_scraper.py": "# deprecated scraper\nimport requests\nprint('deprecated')\n",
    "data/raw/pharma/pharma_notes.txt": "Pfizer subsidiary exploring RNA therapeutics.\nRoche partnering with 2 Swiss startups.\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# -------------------------------------------------------------------
# 2. CREATE THE PROBLEM: Source intelligence documents for ingestion
#    These are the messy raw "sources" the agent must feed into the system.
# -------------------------------------------------------------------

source_dir = workspace / "data/raw/biotech"

# Source 1: A markdown intelligence brief
(source_dir / "emerging_biotech_brief.md").write_text(
    """# Emerging Biotech Startups — Intelligence Brief

## SynthCell Technologies
- Founded: 2020, Cambridge MA
- Focus: Synthetic biology for targeted drug delivery
- Funding: $28M Series A (2023)
- Key personnel: Dr. Alicia Mercer (CEO), Dr. Rajan Patel (CSO)
- Status: Pre-clinical trials for oncology pipeline
- Confidence: HIGH

## NovaPlex Genomics
- Founded: 2021, San Diego CA  
- Focus: Multi-cancer early detection via cfDNA
- Funding: $15M Seed (2022), rumored Series A in Q3 2024
- Key personnel: Dr. Ivan Sorokin (CEO)
- Status: Clinical validation in progress
- Confidence: MEDIUM — funding round unconfirmed

## OrbiCell
- Founded: 2019, Boston MA
- Focus: CAR-T cell therapy automation platform
- Funding: $52M Series B (2023)
- Key personnel: Dr. Yuki Tanaka (CEO)
- Status: IND filed, Phase 1 starting Q4 2024
- Confidence: HIGH

## GlycoShift
- Founded: 2022, Austin TX
- Focus: Glycan-targeted antibodies for autoimmune disease
- Funding: $8M Seed (2023)
- Confidence: LOW — very early stage, limited public information
"""
)

# Source 2: A CSV of startup signals
(source_dir / "startup_signals.csv").write_text(
    "startup,signal,date,confidence\n"
    "SynthCell Technologies,Published Nature Biotechnology paper on lipid nanoparticles,2024-01-15,HIGH\n"
    "NovaPlex Genomics,CEO interviewed on STAT News podcast,2024-02-10,MEDIUM\n"
    "OrbiCell,Hired 3 ex-Novartis CAR-T scientists,2024-03-01,HIGH\n"
    "GlycoShift,LinkedIn activity spike — 5 new hires in 1 month,2024-03-20,LOW\n"
    "SynthCell Technologies,Partnership rumored with Roche,2024-04-01,LOW\n"
)

# Source 3: A plain-text analyst note
(source_dir / "analyst_notes.txt").write_text(
    "ANALYST NOTE — Q1 2024 Scan\n\n"
    "SynthCell and OrbiCell both showing strong signal velocity. "
    "Cross-reference: SynthCell's lipid nanoparticle work may overlap with OrbiCell's delivery challenges. "
    "NovaPlex funding confirmation needed before upgrading confidence. "
    "GlycoShift is a wildcard — monitor for Series A announcement.\n\n"
    "Action items:\n"
    "- Verify NovaPlex Series A via Crunchbase / PitchBook\n"
    "- Confirm SynthCell-Roche partnership via official press release\n"
    "- Schedule expert call on GlycoShift glycan platform\n"
)

print("Workspace initialized with distractor files and source intelligence documents.")
print(f"Source files written to: {source_dir}")