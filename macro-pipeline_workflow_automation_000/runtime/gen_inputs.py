#!/usr/bin/env python3
"""
Generates the initial sandbox workspace for the genome-qc pipeline task.
Creates a realistic, deeply nested project structure with distractor files.
Does NOT create the files the agent is supposed to create (PIPELINE.md, HEARTBEAT.md).
"""
import os
import random
from pathlib import Path

random.seed(42)

HOME = Path("/home/bioagent")

# ── 1. Create the project directory structure (distractor files) ──────────────
project_dir = HOME / "Documents" / "proyectos" / "genome-qc"
project_dir.mkdir(parents=True, exist_ok=True)

# Existing project files (distractors)
(project_dir / "README.md").write_text(
    "# Genome QC Project\n\nThis project processes raw FASTQ files through a QC pipeline.\n"
)

(project_dir / "config.yaml").write_text(
    "reference_genome: hg38\nmin_quality: 20\nthreads: 8\noutput_format: vcf\n"
)

scripts_dir = project_dir / "scripts"
scripts_dir.mkdir(exist_ok=True)

(scripts_dir / "run_fastqc.sh").write_text(
    "#!/bin/bash\nfastqc $1 -o ./results/fastqc/\necho 'FastQC done'\n"
)

(scripts_dir / "trim_adapters.sh").write_text(
    "#!/bin/bash\ntrimmomatic PE $1 $2 \\\n  output_R1_paired.fastq output_R1_unpaired.fastq \\\n  output_R2_paired.fastq output_R2_unpaired.fastq \\\n  ILLUMINACLIP:adapters.fa:2:30:10\n"
)

(scripts_dir / "align_reads.sh").write_text(
    "#!/bin/bash\nbwa mem hg38.fa $1 $2 | samtools sort -o aligned.bam\nsamtools index aligned.bam\n"
)

(scripts_dir / "variant_call.sh").write_text(
    "#!/bin/bash\ngatk HaplotypeCaller -R hg38.fa -I aligned.bam -O variants.vcf\n"
)

(scripts_dir / "generate_report.sh").write_text(
    "#!/bin/bash\npython3 report_generator.py --input ./results/ --output report.html\n"
)

data_dir = project_dir / "data" / "raw"
data_dir.mkdir(parents=True, exist_ok=True)

for i in range(1, 4):
    (data_dir / f"sample_{i:02d}_R1.fastq.gz").write_text(f"# FASTQ placeholder for sample {i} R1\n")
    (data_dir / f"sample_{i:02d}_R2.fastq.gz").write_text(f"# FASTQ placeholder for sample {i} R2\n")

results_dir = project_dir / "results"
results_dir.mkdir(exist_ok=True)
(results_dir / ".gitkeep").write_text("")

(project_dir / ".gitignore").write_text("*.bam\n*.bai\n*.tmp\nresults/\n__pycache__/\n")

# Distractor: a malformed/old pipeline attempt (NOT in the correct format)
(project_dir / "OLD_WORKFLOW.txt").write_text(
    "Step 1: Run FastQC on raw reads\nStep 2: Trim adapters\nStep 3: Align\nStep 4: Call variants\nStep 5: Report\n"
    "NOTE: This is outdated, do not use\n"
)

# ── 2. Create the openclaw workspace structure ────────────────────────────────
# The CORRECT location for HEARTBEAT.md is ~/.openclaw/workspace-agent-bio-01/
# We create the parent but NOT the agent workspace dir, so the agent must create it
openclaw_dir = HOME / ".openclaw"
openclaw_dir.mkdir(exist_ok=True)

# Create a DIFFERENT agent workspace as a distractor
distractor_workspace = HOME / ".openclaw" / "workspace-agent-legacy"
distractor_workspace.mkdir(exist_ok=True)
(distractor_workspace / "HEARTBEAT.md").write_text(
    "# HEARTBEAT — agent-legacy\n\n> This is an OLD heartbeat for a deprecated agent.\n\n## Pipeline activo: NONE\n"
)
(distractor_workspace / "notes.txt").write_text(
    "Legacy agent - decommissioned 2024-01-15\n"
)

# Create openclaw global config (distractor)
(openclaw_dir / "openclaw.json").write_text(
    '{\n  "agents": [\n    {"id": "agent-bio-01", "name": "BioInformatics Agent", "model": "claude-3-5-sonnet"},\n'
    '    {"id": "agent-legacy", "name": "Legacy Agent", "status": "inactive"}\n  ],\n'
    '  "crons": []\n}\n'
)

# ── 3. Create a second project as a distractor ────────────────────────────────
other_project = HOME / "Documents" / "proyectos" / "proteomics-analysis"
other_project.mkdir(parents=True, exist_ok=True)
(other_project / "README.md").write_text("# Proteomics Analysis\n\nSeparate project, ignore.\n")
(other_project / "PIPELINE.md").write_text(
    "# PIPELINE — Proteomics: Mass Spec Processing\n"
    "# Proyecto: ~/Documents/proyectos/proteomics-analysis/\n"
    "# Objetivo: Process mass spectrometry data\n"
    "# Creado: 2024-03-01\n\n"
    "## Step 1: Data Import [✅ COMPLETED]\n"
    "- engine: claude-code\n"
    "- description: Import raw mzML files\n"
    "- verify: ls data/processed/*.mzML | wc -l\n"
    "- artifacts: processed mzML files\n\n"
    "## Step 2: Peak Detection [✅ COMPLETED]\n"
    "- engine: claude-code\n"
    "- depends_on: [1]\n"
    "- description: Run peak detection algorithm\n"
    "- verify: test -f results/peaks.tsv\n"
    "- artifacts: peaks.tsv\n"
)

# ── 4. Create git repo in genome-qc project ───────────────────────────────────
os.system(f"cd {project_dir} && git init -q && git config user.email 'bio@lab.org' && git config user.name 'BioLab' && git add -A && git commit -q -m 'initial: project scaffold'")

print("Workspace generated successfully.")
print(f"Project dir: {project_dir}")
print(f"OpenClaw dir: {openclaw_dir}")
print("Files that MUST be created by agent:")
print(f"  - {project_dir}/PIPELINE.md")
print(f"  - {HOME}/.openclaw/workspace-agent-bio-01/HEARTBEAT.md")