#!/usr/bin/env python3
"""
Generate a realistic, messy bioinformatics project workspace for the sync task.
"""

import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Source directory: ~/bioproject/pipeline-docs
# ─────────────────────────────────────────────
source_root = workspace / "bioproject" / "pipeline-docs"

# Normal .md files to be synced
md_files = {
    "README.md": "# Pipeline Documentation\n\nThis pipeline processes genomic data.\n\n## Overview\n\nMain workflow for variant calling.\n",
    "setup.md": "# Setup Instructions\n\nInstall dependencies with conda.\n\n```bash\nconda env create -f environment.yml\n```\n",
    "usage.md": "# Usage Guide\n\nRun the pipeline:\n\n```bash\npython run_pipeline.py --input data/ --output results/\n```\n",
    "modules/alignment.md": "# Alignment Module\n\nUses BWA-MEM2 for read alignment.\n\n## Parameters\n\n- Threads: 8\n- Reference: hg38\n",
    "modules/variant-calling.md": "# Variant Calling\n\nGATK HaplotypeCaller pipeline.\n\n## Steps\n\n1. Mark duplicates\n2. Base recalibration\n3. HaplotypeCaller\n",
    "modules/qc.md": "# Quality Control\n\nFastQC + MultiQC reports.\n",
    "protocols/sample-prep.md": "# Sample Preparation Protocol\n\nDNA extraction using Qiagen kit.\n\n## Materials\n\n- Proteinase K\n- Buffer ATL\n",
    "protocols/sequencing.md": "# Sequencing Protocol\n\nIllumina NovaSeq 6000.\n\n## Settings\n\n- Read length: 150bp PE\n- Coverage: 30x\n",
    "results/benchmarks.md": "# Benchmark Results\n\n| Sample | Recall | Precision | F1 |\n|--------|--------|-----------|----|\n| NA12878 | 0.991 | 0.993 | 0.992 |\n",
    "results/validation.md": "# Validation Report\n\nValidated against Genome in a Bottle truth set.\n",
    "CHANGELOG.md": "# Changelog\n\n## v2.1.0\n- Added SV calling module\n\n## v2.0.0\n- Major refactor\n",
}

# Non-.md files (should NOT be synced)
non_md_files = {
    "environment.yml": "name: bioenv\ndependencies:\n  - python=3.10\n  - bwa=0.7.17\n",
    "run_pipeline.py": "#!/usr/bin/env python3\nprint('Running pipeline...')\n",
    "config.json": '{"threads": 8, "reference": "hg38", "output_dir": "results/"}\n',
    "modules/alignment.py": "# BWA alignment wrapper\ndef align(reads, ref): pass\n",
    "data/sample_list.txt": "sample1\nsample2\nsample3\n",
    "results/metrics.tsv": "sample\tcoverage\tmappability\nNA12878\t32.1\t0.987\n",
    "Snakefile": "rule all:\n    input: 'results/final.vcf'\n",
    "scripts/preprocess.sh": "#!/bin/bash\ntrimmomatic PE reads_R1.fq reads_R2.fq output_R1.fq output_R2.fq\n",
}

# Excluded directories with .md files inside (should NOT be synced)
excluded_md_files = {
    "node_modules/lodash/README.md": "# lodash\nUtility library\n",
    "node_modules/axios/CHANGELOG.md": "# Axios Changelog\n\n## 1.4.0\n",
    "__pycache__/module.md": "# cache note\nThis should be excluded.\n",
    ".git/COMMIT_EDITMSG.md": "# git message\nFix alignment bug\n",
    ".venv/lib/python3.10/site-packages/README.md": "# venv package\nShould not be synced.\n",
    ".clawhub/metadata.md": "# ClawHub Metadata\nInternal agent metadata. DO NOT SYNC.\n",
    ".learnings/session-2024.md": "# Learning Notes\nAgent learned X from session.\n",
}

# Create all source files
for rel_path, content in md_files.items():
    full_path = source_root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

for rel_path, content in non_md_files.items():
    full_path = source_root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

for rel_path, content in excluded_md_files.items():
    full_path = source_root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ─────────────────────────────────────────────
# 2. Target Obsidian Vault (exists but empty-ish)
# ─────────────────────────────────────────────
vault = workspace / "ObsidianVault"
vault.mkdir(parents=True, exist_ok=True)

# Vault has some existing notes (unrelated)
(vault / "Daily Notes").mkdir(exist_ok=True)
(vault / "Daily Notes" / "2024-01-15.md").write_text("# Daily Note\nToday I worked on variant calling.\n")
(vault / "Daily Notes" / "2024-01-16.md").write_text("# Daily Note\nReviewed pipeline benchmarks.\n")
(vault / "Personal").mkdir(exist_ok=True)
(vault / "Personal" / "goals.md").write_text("# Research Goals\n- Publish pipeline paper\n- Improve recall\n")

print("Workspace generated successfully.")
print(f"Source: {source_root}")
print(f"Vault:  {vault}")
print("\nExpected sync target subdirectory: BioPipeline2024")
print("Expected .md files to sync (11):")
for f in md_files:
    print(f"  {f}")
print("\nExcluded directories: node_modules, __pycache__, .git, .venv, .clawhub, .learnings")