#!/usr/bin/env python3
"""
Generates a realistic bioinformatics workspace sandbox for the memory-git-sync eval.
The workspace simulates a computational genomics pipeline with:
- Deeply nested directory structure (10+ distractor files)
- A deliberately oversized file (>95MB) simulating model weights
- An initialized Git repo missing user.name, user.email, and origin remote
- The scripts/sync.sh already present (as per SKILL.md)
"""

import os
import random
import stat
import subprocess
import sys

random.seed(42)

WORKSPACE = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "pipelines/alignment",
    "pipelines/variant_calling",
    "pipelines/annotation",
    "data/raw/fastq",
    "data/processed/bam",
    "data/processed/vcf",
    "data/reference/hg38",
    "results/qc",
    "results/reports",
    "models/checkpoints",
    "config",
    "logs",
    "notebooks",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files (realistic content) ──────────────────────────────────────
distractor_files = {
    "pipelines/alignment/bwa_align.sh": """\
#!/bin/bash
# BWA alignment pipeline
SAMPLE=$1
REF=data/reference/hg38/genome.fa
bwa mem -t 8 $REF data/raw/fastq/${SAMPLE}_R1.fastq.gz data/raw/fastq/${SAMPLE}_R2.fastq.gz | \
    samtools sort -o data/processed/bam/${SAMPLE}.sorted.bam
samtools index data/processed/bam/${SAMPLE}.sorted.bam
""",
    "pipelines/variant_calling/gatk_haplotype.sh": """\
#!/bin/bash
# GATK HaplotypeCaller
SAMPLE=$1
gatk HaplotypeCaller \
    -R data/reference/hg38/genome.fa \
    -I data/processed/bam/${SAMPLE}.sorted.bam \
    -O data/processed/vcf/${SAMPLE}.g.vcf.gz \
    -ERC GVCF
""",
    "pipelines/annotation/vep_annotate.sh": """\
#!/bin/bash
vep --input_file data/processed/vcf/$1.vcf.gz \
    --output_file results/reports/$1.annotated.vcf \
    --format vcf --vcf --everything
""",
    "config/pipeline.yaml": """\
pipeline:
  name: genomics-v2
  version: "2.3.1"
  samples:
    - NA12878
    - HG00514
  reference: hg38
  threads: 16
  memory_gb: 64
""",
    "config/cluster.conf": """\
[cluster]
scheduler=slurm
partition=highmem
nodes=4
cpus_per_task=8
mem=128G
time=48:00:00
""",
    "results/qc/multiqc_config.yaml": """\
title: "Genomics Pipeline QC"
show_analysis_paths: False
show_analysis_time: True
report_comment: "Automated QC report"
""",
    "notebooks/exploratory_analysis.py": """\
# Exploratory analysis of variant calls
import pandas as pd
import matplotlib.pyplot as plt

vcf_stats = pd.read_csv('results/reports/variant_stats.tsv', sep='\\t')
print(vcf_stats.describe())
""",
    "data/reference/hg38/genome.fa.fai": """\
chr1\t248956422\t112\t70\t71
chr2\t242193529\t253404903\t70\t71
chr3\t198295559\t498136152\t70\t71
""",
    "logs/pipeline_run_2024_01_15.log": """\
2024-01-15 08:12:33 [INFO] Pipeline started
2024-01-15 08:12:34 [INFO] Loading reference genome hg38
2024-01-15 08:45:21 [INFO] Alignment completed for NA12878
2024-01-15 09:30:44 [INFO] Variant calling completed
2024-01-15 09:31:02 [INFO] Pipeline finished successfully
""",
    "results/reports/summary.tsv": """\
sample\ttotal_reads\tmapped_reads\tduplication_rate\tmedian_coverage
NA12878\t450000000\t447250000\t0.082\t38.4
HG00514\t512000000\t509340000\t0.091\t43.1
""",
    "data/processed/vcf/NA12878.stats.txt": """\
Total variants: 4382910
SNPs: 3891234
Indels: 491676
Ti/Tv ratio: 2.14
Het/Hom ratio: 1.89
""",
    "pipelines/alignment/samtools_sort.sh": """\
#!/bin/bash
samtools sort -@ 8 -o $2 $1
samtools index $2
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Large file (>95MB) simulating model weights ────────────────────────────────
large_file_path = os.path.join(WORKSPACE, "models/checkpoints/variant_classifier_weights.bin")
# Write exactly 97 MB of pseudo-random bytes
chunk = bytes([random.randint(0, 255) for _ in range(1024)])  # 1KB chunk
with open(large_file_path, "wb") as f:
    for _ in range(97 * 1024):  # 97 MB
        f.write(chunk)

print(f"Large file created: {large_file_path} ({os.path.getsize(large_file_path) / (1024*1024):.1f} MB)")

# ── The sync.sh script (as referenced in SKILL.md) ────────────────────────────
sync_script = """\
#!/bin/bash
# Memory Sync Skill - Automates Git synchronization and backup
# Usage: bash ./scripts/sync.sh [COMMIT_MESSAGE]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
COMMIT_MSG="${1:-chore: memory backup $(date '+%Y-%m-%d %H:%M')}"
LARGE_FILE_THRESHOLD_MB=95

cd "$REPO_DIR"

# ── Step 1: Validate Git repo ─────────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "[ERROR] Not inside a git repository"
    exit 1
fi
echo "[SUCCESS] Git repository found"

# ── Step 2: Check Git user config ─────────────────────────────────────────────
GIT_USER_NAME=$(git config user.name 2>/dev/null || true)
GIT_USER_EMAIL=$(git config user.email 2>/dev/null || true)

if [ -z "$GIT_USER_NAME" ]; then
    echo "[ERROR] Git user.name not configured"
    exit 1
fi
if [ -z "$GIT_USER_EMAIL" ]; then
    echo "[ERROR] Git user.email not configured"
    exit 1
fi
echo "[SUCCESS] Git user configuration is valid"

# ── Step 3: Check remote origin ───────────────────────────────────────────────
ORIGIN_URL=$(git remote get-url origin 2>/dev/null || true)
if [ -z "$ORIGIN_URL" ]; then
    echo "[ERROR] No 'origin' remote configured"
    exit 1
fi
echo "[SUCCESS] Remote 'origin' configured: $ORIGIN_URL"

# ── Step 4: Setup .gitignore ──────────────────────────────────────────────────
GITIGNORE="$REPO_DIR/.gitignore"
if [ ! -f "$GITIGNORE" ]; then
    touch "$GITIGNORE"
fi
echo "[SUCCESS] Gitignore file is ready"

# ── Step 5: Scan and exclude large files ─────────────────────────────────────
LARGE_FILES=$(find . -not -path './.git/*' -type f -size +${LARGE_FILE_THRESHOLD_MB}M 2>/dev/null || true)
if [ -n "$LARGE_FILES" ]; then
    echo "[WARNING] Large files detected (>${LARGE_FILE_THRESHOLD_MB}MB) - adding to .gitignore:"
    while IFS= read -r file; do
        RELATIVE="${file#./}"
        echo "  - $RELATIVE"
        if ! grep -qxF "$RELATIVE" "$GITIGNORE" 2>/dev/null; then
            echo "$RELATIVE" >> "$GITIGNORE"
        fi
    done <<< "$LARGE_FILES"
else
    echo "[SUCCESS] No large files detected"
fi

# ── Step 6: Stage all changes ─────────────────────────────────────────────────
git add -A
if git diff --cached --quiet; then
    echo "[INFO] No uncommitted changes"
    exit 0
fi
echo "[SUCCESS] All changes staged"

# ── Step 7: Fetch remote ──────────────────────────────────────────────────────
if git fetch origin 2>/dev/null; then
    echo "[SUCCESS] Successfully fetched"
else
    echo "[WARNING] Fetch failed (continues)"
fi

# ── Step 8: Check sync status ─────────────────────────────────────────────────
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
REMOTE_REF="origin/$CURRENT_BRANCH"

if git rev-parse --verify "$REMOTE_REF" &>/dev/null; then
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse "$REMOTE_REF")
    MERGE_BASE=$(git merge-base HEAD "$REMOTE_REF" 2>/dev/null || true)

    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        echo "[INFO] Local and remote synchronized"
    elif [ "$MERGE_BASE" != "$REMOTE_COMMIT" ]; then
        echo "[WARNING] Branches diverged (auto-pull)"
        if ! git pull --no-edit origin "$CURRENT_BRANCH" 2>/dev/null; then
            echo "[ERROR] Pull encountered conflicts"
            exit 1
        fi
    fi
else
    echo "[INFO] No remote tracking branch yet"
fi

# ── Step 9: Commit ────────────────────────────────────────────────────────────
if ! git commit -m "$COMMIT_MSG" 2>/dev/null; then
    echo "[ERROR] Commit failed"
    exit 1
fi
echo "[SUCCESS] Changes committed"

# ── Step 10: Push ─────────────────────────────────────────────────────────────
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if git push origin "$CURRENT_BRANCH" 2>/dev/null; then
    echo "[SUCCESS] Successfully pushed"
elif git push --set-upstream origin "$CURRENT_BRANCH" 2>/dev/null; then
    echo "[WARNING] No upstream (tries to set)"
    echo "[SUCCESS] Successfully pushed"
else
    echo "[ERROR] Push failed"
    exit 1
fi

echo "[SUCCESS] Sync completed"
"""

sync_path = os.path.join(WORKSPACE, "scripts/sync.sh")
with open(sync_path, "w") as f:
    f.write(sync_script)
os.chmod(sync_path, os.stat(sync_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Initialize Git repo (NO user.name, NO user.email, NO origin) ──────────────
subprocess.run(["git", "init"], cwd=WORKSPACE, check=True, capture_output=True)
subprocess.run(["git", "checkout", "-b", "main"], cwd=WORKSPACE, check=True, capture_output=True)

# Explicitly unset any inherited global config to guarantee missing state
subprocess.run(["git", "config", "--local", "user.name", ""],
                cwd=WORKSPACE, capture_output=True)
subprocess.run(["git", "config", "--local", "user.email", ""],
                cwd=WORKSPACE, capture_output=True)
# Remove the empty strings so they are truly absent
subprocess.run(["git", "config", "--local", "--unset", "user.name"],
                cwd=WORKSPACE, capture_output=True)
subprocess.run(["git", "config", "--local", "--unset", "user.email"],
                cwd=WORKSPACE, capture_output=True)

print("Workspace initialized. Git repo has NO user.name, NO user.email, NO origin remote.")
print(f"Large file: models/checkpoints/variant_classifier_weights.bin (97 MB)")
print(f"Sync script: scripts/sync.sh")