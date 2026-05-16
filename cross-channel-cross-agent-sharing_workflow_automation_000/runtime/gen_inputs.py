import os
import random
import textwrap
from datetime import date
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Directory skeleton (distractor files) ────────────────────────────────
dirs = [
    "data/raw", "data/processed", "data/interim",
    "notebooks", "reports", "configs",
    "scripts",          # scripts/ dir must exist (skill requirement)
    "memory",           # memory/ dir must exist (skill requirement)
    "src/pipeline", "src/utils", "tests",
    "docs/api", "docs/guides",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "data/raw/sequences_001.fasta": ">seq1\nATGCATGCATGC\n>seq2\nGGCCTTAAGGCC\n",
    "data/raw/metadata.csv": "sample_id,species,date\nS001,E.coli,2024-01-10\nS002,H.sapiens,2024-01-11\n",
    "data/processed/aligned.bam": "# placeholder BAM\n",
    "data/interim/temp_results.json": '{"status": "incomplete", "records": 0}\n',
    "notebooks/exploration.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4}\n',
    "reports/q1_summary.txt": "Q1 analysis pending.\n",
    "configs/pipeline.yaml": "steps:\n  - align\n  - annotate\n",
    "configs/env.cfg": "LOG_LEVEL=INFO\nMAX_THREADS=4\n",
    "src/pipeline/run.py": "# TODO: implement\n",
    "src/utils/helpers.py": "def noop(): pass\n",
    "tests/test_pipeline.py": "def test_placeholder(): assert True\n",
    "docs/api/endpoints.md": "# API docs placeholder\n",
    "docs/guides/onboarding.md": "# Onboarding placeholder\n",
}
for rel_path, content in distractor_files.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── 2. Existing TOOLS.md (stale / incomplete – agent must UPDATE it) ─────────
tools_md = textwrap.dedent("""\
    # Workspace Tools

    ## samtools
    - **Path:** /usr/bin/samtools
    - **Install:** apt-get install samtools
    - **Verify:** samtools --version
    - **Version:** 1.17
    - **Usage:** Manipulate SAM/BAM alignment files

    ## blast+
    - **Path:** /usr/bin/blastn
    - **Install:** apt-get install ncbi-blast+
    - **Verify:** blastn -version
    - **Version:** 2.14.0
    - **Usage:** Local nucleotide sequence alignment search
""")
(WORKSPACE / "TOOLS.md").write_text(tools_md)

# ── 3. Existing SKILL.md (workspace root – agent should ADD a new skill entry)
#    We place a *different* existing skill so agent must add/create one for biopython
skill_md = textwrap.dedent("""\
    ---
    name: blast-local-search
    description: Run local BLAST searches using workspace-installed blast+ binaries.
    ---

    # BLAST Local Search Skill

    ## Steps
    1. Prepare FASTA query file in data/raw/
    2. Run: blastn -query data/raw/sequences_001.fasta -db nt -out reports/blast_out.txt
    3. Parse reports/blast_out.txt for top hits
""")
(WORKSPACE / "SKILL.md").write_text(skill_md)

# ── 4. check_capability.sh already exists (per SKILL.md "scripts already exist")
check_cap = textwrap.dedent("""\
    #!/usr/bin/env bash
    # check_capability.sh <python-bin> <module1> [module2 ...]
    # Exits 0 if all modules importable, 1 otherwise.
    set -euo pipefail
    PYTHON_BIN="$1"
    shift
    FAILED=()
    for mod in "$@"; do
        if ! "$PYTHON_BIN" -c "import $mod" 2>/dev/null; then
            FAILED+=("$mod")
        fi
    done
    if [ ${#FAILED[@]} -eq 0 ]; then
        echo "OK: all modules verified"
        exit 0
    else
        echo "MISSING: ${FAILED[*]}"
        exit 1
    fi
""")
(WORKSPACE / "scripts" / "check_capability.sh").write_text(check_cap)

# ── 5. sessions_send mock (simulates sending to other agent sessions)
sessions_send = textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock sessions_send: logs invocation to /workspace/memory/sessions_send.log
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$TIMESTAMP | ARGS: $*" >> /workspace/memory/sessions_send.log
    echo "Session notification sent."
""")
(WORKSPACE / "scripts" / "sessions_send").write_text(sessions_send)

# ── 6. A stale memory log from a previous date (distractor) ──────────────────
old_log = textwrap.dedent("""\
    # Capability Log 2024-01-15

    ## blast+ installed
    - What changed: Installed NCBI blast+ suite
    - Verify: blastn -version
    - Caveats: Requires local nt database for full functionality
""")
(WORKSPACE / "memory" / "2024-01-15.md").write_text(old_log)

# ── 7. Additional distractor scripts ─────────────────────────────────────────
(WORKSPACE / "scripts" / "run_alignment.sh").write_text("#!/bin/bash\necho 'align'\n")
(WORKSPACE / "scripts" / "fetch_genome.sh").write_text("#!/bin/bash\necho 'fetch'\n")

print("Workspace scaffold created successfully.")
print(f"Today's date for memory log: {date.today().isoformat()}")