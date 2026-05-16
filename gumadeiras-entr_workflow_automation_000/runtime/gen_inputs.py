import os
import random
import hashlib

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic bioinformatics project structure
dirs = [
    "src",
    "src/analysis",
    "src/utils",
    "src/preprocessing",
    "data/raw",
    "data/processed",
    "results/figures",
    "results/tables",
    "tests",
    "docs",
    "configs",
    "notebooks",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Python source files in src/ that should be watched
py_files_src = {
    "src/analysis/variant_caller.py": """\
# Variant calling pipeline
import hashlib

def call_variants(input_bam, reference):
    \"\"\"Call variants from BAM file against reference genome.\"\"\"
    pass

def filter_by_quality(variants, min_qual=20):
    return [v for v in variants if v.get('qual', 0) >= min_qual]
""",
    "src/analysis/alignment.py": """\
# Alignment module
def align_reads(fastq_path, reference_genome):
    \"\"\"Align reads to reference genome using BWA.\"\"\"
    pass

def compute_coverage(bam_path, regions=None):
    return {}
""",
    "src/utils/file_io.py": """\
# File I/O utilities
import os

def read_fasta(path):
    sequences = {}
    return sequences

def write_vcf(variants, output_path):
    pass
""",
    "src/utils/stats.py": """\
# Statistical utilities
import math

def mean(values):
    return sum(values) / len(values) if values else 0.0

def stdev(values):
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / len(values)) if values else 0.0
""",
    "src/preprocessing/trimmer.py": """\
# Read trimming module
def trim_adapters(reads, adapter_seq):
    return [r for r in reads if adapter_seq not in r]

def quality_trim(reads, min_qual=15):
    return reads
""",
    "src/preprocessing/normalizer.py": """\
# Normalization routines
def normalize_counts(counts, method='rpkm'):
    if method == 'rpkm':
        pass
    return counts
""",
}

# Distractor files that should NOT trigger the build (non-.py or outside src/)
distractor_files = {
    "data/raw/sample_001.fastq": "@READ001\nACGTACGTACGT\n+\nIIIIIIIIIIII\n",
    "data/raw/sample_002.fastq": "@READ002\nTTGCATGCATGC\n+\nHHHHHHHHHHHH\n",
    "data/processed/filtered_variants.vcf": "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\n",
    "results/figures/pca_plot.svg": "<svg></svg>",
    "results/tables/summary_stats.tsv": "sample\tmean_depth\tcoverage\nS001\t45.2\t98.1\n",
    "tests/test_alignment.py": """\
import pytest

def test_placeholder():
    assert True
""",
    "docs/pipeline_overview.md": "# Pipeline Overview\nThis pipeline processes genomic data.\n",
    "configs/pipeline.yaml": "reference: hg38\nmin_quality: 20\nthreads: 4\n",
    "notebooks/exploratory_analysis.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
    "configs/sample_manifest.csv": "sample_id,path,type\nS001,data/raw/sample_001.fastq,WGS\n",
    "src/analysis/__init__.py": "# Analysis package\n",
    "src/utils/__init__.py": "# Utils package\n",
    "src/preprocessing/__init__.py": "# Preprocessing package\n",
    "src/__init__.py": "# Source package\n",
}

# Write all source files
for path, content in {**py_files_src, **distractor_files}.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Write a build_manifest.sh script that generates a checksum manifest
build_manifest_sh = """\
#!/bin/bash
# Regenerates checksum manifest for all Python source files in src/
MANIFEST_FILE="/workspace/results/tables/checksums.md5"
find /workspace/src -name "*.py" | sort | xargs md5sum > "$MANIFEST_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Manifest rebuilt: $(wc -l < $MANIFEST_FILE) files" >> /workspace/build_log.txt
"""

with open(os.path.join(workspace, "build_manifest.sh"), "w") as f:
    f.write(build_manifest_sh)

os.chmod(os.path.join(workspace, "build_manifest.sh"), 0o755)

print("Workspace generated successfully.")
print(f"Python source files in src/: {len(py_files_src)}")
print(f"Distractor files: {len(distractor_files)}")