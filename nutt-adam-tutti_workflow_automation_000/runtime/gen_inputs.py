#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the Tutti multi-agent orchestration task.
Creates a realistic genomics pipeline project with distractor files.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Project directory structure ───────────────────────────────────────────────
dirs = [
    "src/variant_caller",
    "src/qc_reporter",
    "src/annotation_engine",
    "src/shared/utils",
    "src/shared/models",
    "tests/unit",
    "tests/integration",
    "data/samples",
    "data/references",
    "docs/api",
    "docs/pipeline",
    ".tutti/state",
    "scripts/deploy",
    "configs/environments",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor source files ────────────────────────────────────────────────────
distractor_files = {
    "src/variant_caller/__init__.py": '"""Variant caller module for chromosome analysis."""\n',
    "src/variant_caller/caller.py": (
        "import numpy as np\n\n"
        "class VariantCaller:\n"
        "    def __init__(self, reference_genome):\n"
        "        self.ref = reference_genome\n\n"
        "    def call_variants(self, chromosome, sample_bam):\n"
        "        \"\"\"Identify SNPs and indels on a given chromosome.\"\"\"\n"
        "        raise NotImplementedError\n"
    ),
    "src/qc_reporter/__init__.py": '"""QC reporting module."""\n',
    "src/qc_reporter/reporter.py": (
        "class QCReporter:\n"
        "    def __init__(self, threshold=0.95):\n"
        "        self.threshold = threshold\n\n"
        "    def generate_report(self, metrics):\n"
        "        return {k: v for k, v in metrics.items() if v >= self.threshold}\n"
    ),
    "src/annotation_engine/__init__.py": '"""Annotation engine for variant classification."""\n',
    "src/annotation_engine/annotator.py": (
        "DATABASES = ['clinvar', 'gnomad', 'cosmic']\n\n"
        "class Annotator:\n"
        "    def annotate(self, variant):\n"
        "        return {db: None for db in DATABASES}\n"
    ),
    "src/shared/utils/io.py": (
        "def read_vcf(path):\n"
        "    with open(path) as f:\n"
        "        return [l for l in f if not l.startswith('##')]\n"
    ),
    "src/shared/models/variant.py": (
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class Variant:\n"
        "    chrom: str\n"
        "    pos: int\n"
        "    ref: str\n"
        "    alt: str\n"
        "    qual: float\n"
    ),
    "tests/unit/test_caller.py": (
        "import pytest\n\n"
        "def test_caller_instantiation():\n"
        "    from src.variant_caller.caller import VariantCaller\n"
        "    vc = VariantCaller('hg38')\n"
        "    assert vc.ref == 'hg38'\n"
    ),
    "tests/integration/test_pipeline.py": (
        "def test_full_pipeline_smoke():\n"
        "    \"\"\"Smoke test: pipeline runs without crashing.\"\"\"\n"
        "    pass\n"
    ),
    "data/samples/sample_manifest.tsv": (
        "sample_id\tpatient_id\tbam_path\tstatus\n"
        "S001\tP101\tdata/bams/S001.bam\tprocessed\n"
        "S002\tP102\tdata/bams/S002.bam\tpending\n"
        "S003\tP103\tdata/bams/S003.bam\tprocessed\n"
    ),
    "data/references/hg38_chromosomes.txt": "\n".join(f"chr{i}" for i in range(1, 23)) + "\nchrX\nchrY\n",
    "docs/api/variant_caller_api.md": (
        "# Variant Caller API\n\n"
        "## Methods\n\n"
        "### call_variants(chromosome, sample_bam)\n"
        "Identify SNPs and indels for a given chromosome.\n"
    ),
    "docs/pipeline/architecture.md": (
        "# Pipeline Architecture\n\n"
        "Three main modules:\n"
        "1. Variant Caller\n"
        "2. QC Reporter\n"
        "3. Annotation Engine\n\n"
        "Modules communicate via shared VCF format.\n"
    ),
    "scripts/deploy/deploy_pipeline.sh": (
        "#!/bin/bash\n"
        "set -e\n"
        "echo 'Deploying genomics pipeline...'\n"
        "docker build -t genomics-pipeline .\n"
        "docker push registry.internal/genomics-pipeline:latest\n"
    ),
    "configs/environments/production.yaml": (
        "environment: production\n"
        "genome_build: hg38\n"
        "variant_caller:\n"
        "  min_quality: 30\n"
        "  min_depth: 10\n"
        "qc_reporter:\n"
        "  threshold: 0.95\n"
        "annotation_engine:\n"
        "  databases: [clinvar, gnomad, cosmic]\n"
    ),
    "configs/environments/staging.yaml": (
        "environment: staging\n"
        "genome_build: hg38\n"
        "variant_caller:\n"
        "  min_quality: 20\n"
        "  min_depth: 5\n"
    ),
    ".gitignore": (
        "*.pyc\n__pycache__/\n.env\n*.egg-info/\ndist/\nbuild/\n.tutti/\n"
    ),
    "pyproject.toml": (
        "[build-system]\n"
        "requires = ['setuptools>=65']\n"
        "build-backend = 'setuptools.backends.legacy:build'\n\n"
        "[project]\n"
        "name = 'genomics-pipeline'\n"
        "version = '0.3.1'\n"
        "requires-python = '>=3.10'\n"
    ),
    "Makefile": (
        "test:\n\tpytest tests/\n\nlint:\n\truff check src/\n\nformat:\n\tblack src/ tests/\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = WORKSPACE / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ─── Intentionally broken / incomplete stub configs ─────────────────────────────
# A broken partial tutti config that the agent must NOT use (wrong format)
broken_config = WORKSPACE / "tutti.toml.bak"
broken_config.write_text(
    "# Abandoned draft — DO NOT USE\n"
    "[agents]\n"
    "  vc = {name='vc', cmd='aider'}\n"  # wrong schema
)

# A stale state file to simulate prior partial run
stale_state = WORKSPACE / ".tutti" / "state" / "orphan-agent.json"
stale_state.write_text(json.dumps({
    "name": "orphan-agent",
    "status": "crashed",
    "pid": 99999,
    "worktree": "/tmp/orphan"
}))

# A snapshot JSON that should be referenced as inject_files target
snapshot_dir = WORKSPACE / "data" / "snapshots"
snapshot_dir.mkdir(parents=True, exist_ok=True)
(snapshot_dir / "chr17_context.json").write_text(json.dumps({
    "chromosome": "chr17",
    "sample_count": 42,
    "variants_found": 1873,
    "timestamp": "2024-06-01T00:00:00Z"
}))

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")