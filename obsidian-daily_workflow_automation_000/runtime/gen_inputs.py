import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic distractor directory structure ---
dirs = [
    "lab-notes/2024",
    "lab-notes/2025/raw",
    "lab-notes/2025/processed",
    "projects/protein-folding/data",
    "projects/protein-folding/scripts",
    "projects/gene-expression/figures",
    "references/papers",
    "references/protocols",
    "vault-backup/Daily Notes",
    "vault-backup/templates",
    "tools/analysis",
    "tools/plotting",
    "meeting-logs",
    "configs",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = [
    ("lab-notes/2024/experiment_log.csv", "date,sample,result\n2024-11-01,A1,0.82\n2024-11-02,A2,0.79\n"),
    ("lab-notes/2025/raw/gel_results.txt", "Lane 1: 250bp\nLane 2: 180bp\nLane 3: 210bp\n"),
    ("projects/protein-folding/data/sequences.fasta", ">seq1\nATGCGTACGT\n>seq2\nGCATTACGGT\n"),
    ("projects/protein-folding/scripts/fold.py", "# placeholder folding script\nimport sys\nprint('Running fold...')\n"),
    ("projects/gene-expression/figures/heatmap_notes.txt", "Color scale: blue=low, red=high\nRows: genes, Cols: samples\n"),
    ("references/papers/citations.bib", "@article{smith2024,\n  title={Protein Dynamics},\n  author={Smith, J.}\n}\n"),
    ("references/protocols/pcr_protocol.md", "# PCR Protocol\n1. Denature: 95C 30s\n2. Anneal: 60C 30s\n3. Extend: 72C 60s\n"),
    ("vault-backup/templates/daily_template.md", "# {{date}}\n\n## Tasks\n\n## Notes\n\n## References\n"),
    ("vault-backup/Daily Notes/2025-01-15.md", "- Morning standup\n- [ ] Review grant proposal\n- https://pubmed.ncbi.nlm.nih.gov\n"),
    ("meeting-logs/weekly_sync_2025-03.txt", "Attendees: Alice, Bob, Carol\nAgenda: sequencing results, budget\n"),
    ("configs/analysis_config.yaml", "threads: 4\nmemory: 16G\noutput_dir: /tmp/results\n"),
    ("tools/analysis/normalize.sh", "#!/bin/bash\necho 'Normalizing data...'\n"),
    ("tools/plotting/plot_expression.R", "library(ggplot2)\ndf <- read.csv('data.csv')\nggplot(df, aes(x=gene, y=expr)) + geom_bar()\n"),
]

for rel_path, content in distractors:
    fpath = workspace / rel_path
    fpath.write_text(content)

# --- The actual task input: a backlog file with notes to be entered ---
# This represents handwritten notes the researcher wants to digitize

# Compute specific past dates relative to "today" in the container
# We'll use fixed offset dates hardcoded so eval can find them deterministically
# We embed the dates as ISO strings and let the agent resolve them

backlog_content = """\
# Lab Notes Backlog - To Be Digitized

VAULT: ResearchVault
DAILY_NOTES_FOLDER: Daily Notes

=== ENTRIES TO ADD ===

[DATE: 3 days ago]
TYPE: task
CONTENT: Order new PCR reagents from supplier catalog

[DATE: 3 days ago]
TYPE: journal
CONTENT: Observed unexpected banding pattern in gel run #47

[DATE: yesterday]
TYPE: task
CONTENT: Schedule meeting with Dr. Chen about sequencing data

[DATE: yesterday]
TYPE: link
CONTENT: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9876543

[DATE: yesterday]
TYPE: log
CONTENT: Centrifuge calibration completed

[DATE: today]
TYPE: task
CONTENT: Analyze RNA-seq batch 12 results

[DATE: today]
TYPE: journal
CONTENT: New culture plates arrived, stored at 4C

[DATE: today]
TYPE: link
CONTENT: https://github.com/bioinformatics/rna-tools

=== END OF BACKLOG ===
"""

(workspace / "lab_backlog.txt").write_text(backlog_content)

# --- Also write a README-free note about what the researcher wants ---
# (No hints, just raw context)
task_brief = """\
Researcher: Dr. Maya Okonkwo
Lab: Molecular Biology Unit
Request: Migrate all entries from lab_backlog.txt into the digital daily notes system.
Vault has already been identified as 'ResearchVault' with notes stored in 'Daily Notes' subfolder.
After migration, verify all entries for 'yesterday' are searchable by running a content search for 'sequencing'.
"""

(workspace / "task_brief.txt").write_text(task_brief)

print("Workspace initialized.")
print(f"Files created in: {workspace}")