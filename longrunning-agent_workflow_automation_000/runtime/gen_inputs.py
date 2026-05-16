import os
import json
import random
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── 1. Create a realistic genomics pipeline project directory ─────────────────
project_dir = WORKSPACE / "genomics-pipeline"
project_dir.mkdir(exist_ok=True)

# Distractor files — deeply nested, realistic noise
distractor_structure = [
    "docs/architecture/pipeline_overview.md",
    "docs/architecture/data_flow.md",
    "docs/meetings/2024-03-01_kickoff.txt",
    "docs/meetings/2024-03-15_review.txt",
    "src/utils/file_parser.py",
    "src/utils/validators.py",
    "src/alignment/bwa_wrapper.sh",
    "src/alignment/samtools_sort.sh",
    "src/variant_calling/gatk_haplotype.sh",
    "src/variant_calling/bcftools_filter.sh",
    "src/qc/fastqc_runner.py",
    "src/qc/multiqc_aggregator.py",
    "config/reference_genome.yaml",
    "config/pipeline_params.yaml",
    "config/cluster_resources.yaml",
    "data/raw/.gitkeep",
    "data/interim/.gitkeep",
    "data/processed/.gitkeep",
    "results/plots/.gitkeep",
    "results/reports/.gitkeep",
    "tests/test_validators.py",
    "tests/test_file_parser.py",
    "scripts/download_reference.sh",
    "scripts/setup_conda_env.sh",
    "logs/run_2024-03-10.log",
    "logs/run_2024-03-11.log",
]

for rel_path in distractor_structure:
    full_path = project_dir / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    if not full_path.exists():
        if full_path.suffix in (".py",):
            full_path.write_text(f"# Placeholder: {rel_path}\n\ndef placeholder():\n    pass\n")
        elif full_path.suffix in (".sh",):
            full_path.write_text(f"#!/bin/bash\n# Placeholder: {rel_path}\necho 'not implemented'\n")
        elif full_path.suffix in (".yaml",):
            full_path.write_text(f"# Config placeholder\nkey: value\n")
        elif full_path.suffix in (".log",):
            full_path.write_text(f"[INFO] Log for {rel_path}\n[INFO] Pipeline ran successfully.\n")
        else:
            full_path.write_text(f"Placeholder content for {rel_path}\n")

# ── 2. CLAUDE.md — project instructions ──────────────────────────────────────
claude_md = project_dir / "CLAUDE.md"
claude_md.write_text("""\
# Genomics Pipeline Project

## Overview
This project automates a multi-stage whole-genome sequencing (WGS) analysis pipeline.
Each task corresponds to one pipeline stage. Tasks must be completed in dependency order.

## Workflow
Follow the longrunning-agent workflow:
1. Read progress.txt to understand what has already been done.
2. Select the next incomplete task (passes: false) whose dependencies are all complete (passes: true).
3. Implement the task by creating or modifying the relevant file(s) listed in the task description.
4. Update progress.txt with a timestamped entry describing what was done.
5. Mark the task passes: true in task.json.
6. Make a git commit with a descriptive message referencing the task id.

## Important
- Only work on ONE task per session.
- Do not mark a task complete unless its dependency tasks are all passes: true.
""")

# ── 3. task.json — complex dependency graph, one unblocked task ───────────────
#
# Dependency graph (arrows = "depends on"):
#   task-1 (DONE)
#   task-2 (DONE) -> task-1
#   task-3 (DONE) -> task-1
#   task-4 (NOT DONE, BLOCKED) -> task-2, task-3, task-5   <-- blocked by task-5
#   task-5 (NOT DONE, UNBLOCKED) -> task-2, task-3          <-- THE ONE to do
#   task-6 (NOT DONE, BLOCKED) -> task-4, task-5
#   task-7 (NOT DONE, BLOCKED) -> task-5
#
# Only task-5 is unblocked (its dependencies task-2, task-3 are both done).

tasks = {
    "tasks": [
        {
            "id": "task-1",
            "description": "Download and index reference genome (hg38) into data/raw/reference/",
            "priority": 1,
            "dependencies": [],
            "passes": True
        },
        {
            "id": "task-2",
            "description": "Run FastQC quality control on all raw FASTQ files and store reports in results/reports/fastqc/",
            "priority": 2,
            "dependencies": ["task-1"],
            "passes": True
        },
        {
            "id": "task-3",
            "description": "Trim adapter sequences using Trimmomatic and save trimmed reads to data/interim/trimmed/",
            "priority": 2,
            "dependencies": ["task-1"],
            "passes": True
        },
        {
            "id": "task-4",
            "description": "Align trimmed reads to reference genome using BWA-MEM and produce data/interim/aligned/sample.bam",
            "priority": 3,
            "dependencies": ["task-2", "task-3", "task-5"],
            "passes": False
        },
        {
            "id": "task-5",
            "description": "Generate MultiQC aggregate report from FastQC results and save to results/reports/multiqc_report.html",
            "priority": 3,
            "dependencies": ["task-2", "task-3"],
            "passes": False
        },
        {
            "id": "task-6",
            "description": "Sort and index BAM file, producing data/interim/aligned/sample.sorted.bam and its .bai index",
            "priority": 4,
            "dependencies": ["task-4", "task-5"],
            "passes": False
        },
        {
            "id": "task-7",
            "description": "Produce final QC summary document at results/reports/qc_summary.txt consolidating all QC metrics",
            "priority": 4,
            "dependencies": ["task-5"],
            "passes": False
        }
    ]
}

task_json_path = project_dir / "task.json"
task_json_path.write_text(json.dumps(tasks, indent=2))

# ── 4. progress.txt — realistic prior session log ────────────────────────────
base_time = datetime(2024, 3, 10, 9, 0, 0)

def ts(offset_minutes):
    return (base_time + timedelta(minutes=offset_minutes)).strftime("[%Y-%m-%d %H:%M:%S]")

progress_entries = [
    f"{ts(0)} Started session",
    f"{ts(5)} Initialized project directory and git repository",
    f"{ts(10)} Completed task: Download and index reference genome (task-1)",
    f"{ts(11)} Committed: task-1 complete",
    f"{ts(30)} Started session",
    f"{ts(35)} Completed task: Run FastQC quality control (task-2)",
    f"{ts(36)} Committed: task-2 complete",
    f"{ts(55)} Started session",
    f"{ts(60)} Completed task: Trim adapter sequences using Trimmomatic (task-3)",
    f"{ts(61)} Committed: task-3 complete",
]

progress_path = project_dir / "progress.txt"
progress_path.write_text("\n".join(progress_entries) + "\n")

# ── 5. init.sh — optional environment setup ──────────────────────────────────
init_sh = project_dir / "init.sh"
init_sh.write_text("""\
#!/bin/bash
# Environment setup for genomics pipeline
echo "Initializing genomics pipeline environment..."
mkdir -p data/raw/reference data/interim/trimmed data/interim/aligned results/reports/fastqc
echo "Environment ready."
""")
init_sh.chmod(0o755)

# ── 6. Initialize git repo ────────────────────────────────────────────────────
subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
subprocess.run(
    ["git", "commit", "-m", "chore: initial project scaffold after task-3"],
    cwd=project_dir, check=True, capture_output=True
)

print(f"Workspace prepared at: {project_dir}")
print("Task-5 is the only unblocked incomplete task.")
print("Agent must: create output file, update progress.txt, set task-5 passes:true, git commit.")