#!/usr/bin/env python3
"""
Generate a realistic bioinformatics workspace with:
- A deeply nested directory structure
- Various intermediate files, logs, and results
- Some files to be trashed, some to be restored
"""

import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory structure ---
dirs = [
    "pipeline/alignment/sample_A",
    "pipeline/alignment/sample_B",
    "pipeline/alignment/sample_C",
    "pipeline/variant_calling/sample_A",
    "pipeline/variant_calling/sample_B",
    "pipeline/variant_calling/sample_C",
    "pipeline/qc/fastqc_reports",
    "pipeline/qc/multiqc",
    "pipeline/annotation",
    "pipeline/expression/counts",
    "pipeline/expression/deseq2",
    "pipeline/logs",
    "pipeline/tmp",
    "archive/old_runs",
    "configs",
    "scripts",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Helper ---
def write(path, content):
    Path(path).write_text(content)

# --- Distractor files (should NOT be trashed) ---
write(WORKSPACE / "configs/pipeline.yaml", "genome: hg38\nthreads: 8\nmemory: 32G\n")
write(WORKSPACE / "configs/samples.tsv", "sample_id\tgroup\nA\tcontrol\nB\ttreatment\nC\ttreatment\n")
write(WORKSPACE / "scripts/run_pipeline.sh", "#!/bin/bash\necho 'Running pipeline'\n")
write(WORKSPACE / "scripts/merge_vcf.py", "# Merges VCF files\nprint('merge')\n")
write(WORKSPACE / "archive/old_runs/run_2023_summary.txt", "Old run summary - 2023\nSamples: 10\n")

# --- Alignment BAM files (distractor, keep) ---
for sample in ["sample_A", "sample_B", "sample_C"]:
    write(WORKSPACE / f"pipeline/alignment/{sample}/{sample}.bam",
          f"@HD VN:1.6 SO:coordinate\n@SQ SN:chr1 LN:248956422\n# {sample} alignment\n")
    write(WORKSPACE / f"pipeline/alignment/{sample}/{sample}.bam.bai",
          f"# BAM index for {sample}\n")

# --- Variant calling results (distractor, keep) ---
for sample in ["sample_A", "sample_B", "sample_C"]:
    write(WORKSPACE / f"pipeline/variant_calling/{sample}/{sample}.vcf",
          f"##fileformat=VCFv4.2\n##sample={sample}\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")

# --- QC reports (distractor, keep) ---
write(WORKSPACE / "pipeline/qc/multiqc/multiqc_report.html", "<html><body>MultiQC Report</body></html>")
for sample in ["sample_A", "sample_B", "sample_C"]:
    write(WORKSPACE / f"pipeline/qc/fastqc_reports/{sample}_fastqc.html",
          f"<html><body>FastQC {sample}</body></html>")

# --- Expression results (distractor, keep) ---
write(WORKSPACE / "pipeline/expression/counts/raw_counts.tsv",
      "gene_id\tA\tB\tC\nGENE1\t100\t200\t150\nGENE2\t50\t80\t60\n")
write(WORKSPACE / "pipeline/expression/deseq2/deseq2_results.tsv",
      "gene_id\tlog2FC\tpadj\nGENE1\t1.5\t0.001\nGENE2\t-0.8\t0.04\n")

# =============================================================================
# FILES THAT MUST BE TRASHED (intermediate/scratch files the manager wants gone):
# These are in pipeline/tmp and pipeline/logs
# =============================================================================

# Temporary scratch files in pipeline/tmp (to be trashed)
tmp_files = [
    "pipeline/tmp/sample_A_sort_temp_001.bam",
    "pipeline/tmp/sample_A_sort_temp_002.bam",
    "pipeline/tmp/sample_B_sort_temp_001.bam",
    "pipeline/tmp/sample_B_sort_temp_002.bam",
    "pipeline/tmp/sample_C_sort_temp_001.bam",
    "pipeline/tmp/merge_intermediary.sam",
    "pipeline/tmp/dedup_metrics.txt",
]
for f in tmp_files:
    write(WORKSPACE / f, f"# Temporary file: {f}\n# Generated during pipeline run\n# Safe to delete\n")

# Log files in pipeline/logs (to be trashed)
log_files = [
    "pipeline/logs/alignment_run_001.log",
    "pipeline/logs/alignment_run_002.log",
    "pipeline/logs/variant_call_run_001.log",
    "pipeline/logs/variant_call_run_002.log",
    "pipeline/logs/qc_run_001.log",
]
for f in log_files:
    write(WORKSPACE / f, f"# Log file: {f}\n[INFO] Pipeline step completed\n[INFO] Exit code: 0\n")

# =============================================================================
# THE CRITICAL RESULTS FILE: accidentally trashed along with the others
# This file was supposed to be kept but the manager trashed it too.
# The agent must restore it after the other operations.
# =============================================================================
CRITICAL_FILE = WORKSPACE / "pipeline/annotation/final_annotation_report.tsv"
write(CRITICAL_FILE,
      "gene_id\tchromosome\tstart\tend\tstrand\tannotation\n"
      "GENE1\tchr1\t1000000\t1001500\t+\tprotein_coding\n"
      "GENE2\tchr3\t5500000\t5502000\t-\tlncRNA\n"
      "GENE3\tchr7\t12000000\t12005000\t+\tpseudogene\n")

print("Workspace generated successfully.")
print(f"Files to trash (tmp): {[str(WORKSPACE/f) for f in tmp_files]}")
print(f"Files to trash (logs): {[str(WORKSPACE/f) for f in log_files]}")
print(f"Critical file to trash then restore: {CRITICAL_FILE}")