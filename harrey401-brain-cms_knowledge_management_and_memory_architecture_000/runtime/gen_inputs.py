import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Create distractor files to simulate a real project ──────────────────
distractor_dirs = [
    "src/pipeline",
    "src/analysis",
    "data/raw",
    "data/processed",
    "reports/q1",
    "reports/q2",
    "config",
    "logs",
    "experiments/trial_001",
    "experiments/trial_002",
    "notebooks",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/pipeline/compound_screener.py": "# Screens compounds against protein targets\ndef screen(compound_id, target_id):\n    pass\n",
    "src/pipeline/docking_score.py": "# Computes docking scores\ndef dock(ligand, receptor):\n    return -7.4\n",
    "src/analysis/admet_predictor.py": "# ADMET property prediction\nclass ADMETPredictor:\n    def predict(self, smiles): return {}\n",
    "src/analysis/selectivity_filter.py": "# Filters by selectivity ratio\ndef filter_by_selectivity(compounds, ratio=10): return []\n",
    "data/raw/compounds_batch_001.csv": "compound_id,smiles,mw\nCPD001,CC(=O)Oc1ccccc1C(=O)O,180.16\nCPD002,c1ccc2ccccc2c1,128.17\n",
    "data/raw/targets_kinase_panel.csv": "target_id,name,organism\nKIN001,EGFR,Homo sapiens\nKIN002,BRAF,Homo sapiens\n",
    "data/processed/screening_results_2024.json": json.dumps({"hits": ["CPD001", "CPD007"], "hit_rate": 0.043}),
    "reports/q1/q1_summary.txt": "Q1 screening: 2300 compounds tested, 12 hits identified against EGFR panel.\n",
    "reports/q2/q2_progress.txt": "Q2: Lead optimization underway. Top compound CPD007 shows IC50=14nM.\n",
    "config/pipeline_config.yaml": "screen_mode: fast\ncpu_workers: 8\nlog_level: INFO\n",
    "logs/run_20240301.log": "[INFO] Pipeline started\n[INFO] Loaded 2300 compounds\n[INFO] Screening complete\n",
    "experiments/trial_001/params.json": json.dumps({"target": "EGFR", "method": "glide", "n_poses": 5}),
    "experiments/trial_002/params.json": json.dumps({"target": "BRAF", "method": "autodock", "n_poses": 10}),
    "notebooks/exploratory_analysis.py": "# EDA notebook\nimport pandas as pd\ndf = pd.read_csv('../data/raw/compounds_batch_001.csv')\n",
    "config/ollama_settings.json": json.dumps({"host": "localhost", "port": 11434, "timeout": 30}),
}
for path, content in distractor_files.items():
    fpath = workspace / path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── 2. Create memory/ directory structure with an existing INDEX.md skeleton ─
(workspace / "memory" / "schemas").mkdir(parents=True, exist_ok=True)

# Skeleton INDEX.md — deliberately incomplete (no schema entries, just header)
index_md = """\
# Memory Index (Hippocampus Router)
> Route topics to the correct semantic schema. Load schemas only when triggers match.

## Core Schemas

<!-- Agent: add your domain schema entries here -->

## Cross-Reference Map

<!-- Agent: add cross-link entries here -->
"""
(workspace / "memory" / "INDEX.md").write_text(index_md)

# Empty ANCHORS.md
(workspace / "memory" / "ANCHORS.md").write_text("# Anchors\n> High-significance permanent events.\n\n")

# ── 3. Pre-seed daily log files with [ANCHOR] tagged events ──────────────────
daily_log_2024_03_15 = """\
# Daily Log — 2024-03-15

## Session Summary
- Screened 500 compounds against EGFR target
- Reviewed ADMET predictions for lead series
- Discussed selectivity requirements with biology team

## Key Events
[ANCHOR] CPD007 confirmed as clinical candidate — IC50=14nM, selectivity ratio >100x vs off-targets
[ANCHOR] Go/No-Go decision: Phase I trial approved for CPD007 by steering committee

## Action Items
- Prepare IND filing documents
- Schedule PK/PD study with CRO partner
"""

daily_log_2024_03_22 = """\
# Daily Log — 2024-03-22

## Session Summary
- Reviewed CRO proposal for PK/PD study
- Updated compound library with new synthesis batch
- Ran docking campaign against BRAF mutant panel

## Key Events
[ANCHOR] BRAF-V600E resistance mechanism identified — mutation cluster at kinase hinge region
- Standard docking run completed (not anchor-worthy)

## Notes
- Next NREM cycle should capture the BRAF resistance finding
"""

(workspace / "memory" / "2024-03-15.md").write_text(daily_log_2024_03_15)
(workspace / "memory" / "2024-03-22.md").write_text(daily_log_2024_03_22)

# ── 4. Create the memory_brain/ scripts (Brain CMS scripts) ──────────────────
memory_brain = workspace / "memory_brain"

# index_memory.py — reads memory/*.md schemas and indexes them into LanceDB
index_memory_py = '''\
#!/usr/bin/env python3
"""
index_memory.py — Embed memory schemas into LanceDB vector store.
Reads all .md files from ../memory/ and indexes them.
"""
import os
import sys
import json
from pathlib import Path

try:
    import lancedb
    import numpy as np
    import requests
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

MEMORY_DIR = Path(__file__).parent.parent / "memory"
VECTOR_DIR = Path(__file__).parent / "vectorstore"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

def get_embedding(text: str) -> list:
    """Get embedding from Ollama or return deterministic fallback."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()["embedding"]
    except Exception:
        pass
    # Deterministic fallback: hash-based pseudo-embedding
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    vec = rng.randn(EMBED_DIM).tolist()
    norm = np.linalg.norm(vec)
    return (np.array(vec) / norm).tolist()

def main():
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    md_files = list(MEMORY_DIR.glob("*.md")) + list((MEMORY_DIR / "schemas").glob("*.md"))
    
    if not md_files:
        print("No .md files found in memory/")
        return

    db = lancedb.connect(str(VECTOR_DIR))
    
    records = []
    for fpath in md_files:
        text = fpath.read_text(encoding="utf-8")
        if len(text.strip()) < 20:
            continue
        embedding = get_embedding(text[:2000])
        records.append({
            "source": fpath.name,
            "text": text[:2000],
            "vector": embedding,
        })
        print(f"  Indexed: {fpath.name}")

    if not records:
        print("No indexable content found.")
        return

    import pyarrow as pa
    schema = pa.schema([
        pa.field("source", pa.string()),
        pa.field("text", pa.string()),
        pa.field("vector", pa.list_(pa.float64(), EMBED_DIM)),
    ])

    if "memory_schemas" in db.table_names():
        db.drop_table("memory_schemas")
    tbl = db.create_table("memory_schemas", data=records, schema=schema)
    print(f"\\nIndexed {len(records)} documents into LanceDB.")
    print(f"Vector store: {VECTOR_DIR}")

if __name__ == "__main__":
    main()
'''

# query_memory.py — semantic search over LanceDB
query_memory_py = '''\
#!/usr/bin/env python3
"""
query_memory.py — Semantic similarity search over indexed memory schemas.
Usage: python3 query_memory.py "query text" [--sources-only] [--top-k N]
"""
import sys
import os
import json
import argparse
from pathlib import Path

try:
    import lancedb
    import numpy as np
    import requests
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

VECTOR_DIR = Path(__file__).parent / "vectorstore"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

def get_embedding(text: str) -> list:
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()["embedding"]
    except Exception:
        pass
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    vec = rng.randn(EMBED_DIM).tolist()
    norm = np.linalg.norm(vec)
    return (np.array(vec) / norm).tolist()

def main():
    parser = argparse.ArgumentParser(description="Query memory vector store")
    parser.add_argument("query", type=str, help="Query text")
    parser.add_argument("--sources-only", action="store_true", help="Print only source filenames")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results")
    args = parser.parse_args()

    if not VECTOR_DIR.exists():
        print("Vector store not found. Run index_memory.py first.")
        sys.exit(1)

    db = lancedb.connect(str(VECTOR_DIR))
    if "memory_schemas" not in db.table_names():
        print("Table memory_schemas not found. Run index_memory.py first.")
        sys.exit(1)

    tbl = db.open_table("memory_schemas")
    query_vec = get_embedding(args.query)

    results = tbl.search(query_vec).limit(args.top_k).to_list()

    if args.sources_only:
        for r in results:
            print(r["source"])
    else:
        for i, r in enumerate(results):
            print(f"--- Result {i+1} ---")
            print(f"Source: {r[\'source\']}")
            print(f"Text preview: {r[\'text\'][:200]}")
            print()

if __name__ == "__main__":
    main()
'''

# nrem.py — NREM sleep: compress daily logs, promote [ANCHOR] tags to ANCHORS.md
nrem_py = '''\
#!/usr/bin/env python3
"""
nrem.py — NREM sleep cycle.
1. Scans all daily log files (memory/YYYY-MM-DD.md)
2. Promotes [ANCHOR] tagged lines to memory/ANCHORS.md
3. Writes a compression summary to memory/nrem_report.md
"""
import re
import sys
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent.parent / "memory"
ANCHORS_FILE = MEMORY_DIR / "ANCHORS.md"
NREM_REPORT = MEMORY_DIR / "nrem_report.md"

DATE_PATTERN = re.compile(r"^\\d{4}-\\d{2}-\\d{2}\\.md$")
ANCHOR_PATTERN = re.compile(r"\\[ANCHOR\\]\\s*(.+)")

def main():
    print("=== NREM Sleep Cycle ===")
    
    daily_logs = [
        f for f in MEMORY_DIR.glob("*.md")
        if DATE_PATTERN.match(f.name)
    ]
    
    if not daily_logs:
        print("No daily logs found.")
        return

    # Load existing anchors
    existing_anchors = set()
    if ANCHORS_FILE.exists():
        content = ANCHORS_FILE.read_text()
        for line in content.splitlines():
            stripped = line.strip("- ").strip()
            if stripped:
                existing_anchors.add(stripped)

    new_anchors = []
    total_lines_scanned = 0

    for log_file in sorted(daily_logs):
        text = log_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        total_lines_scanned += len(lines)
        date_str = log_file.stem
        
        for line in lines:
            m = ANCHOR_PATTERN.search(line)
            if m:
                anchor_text = m.group(1).strip()
                entry = f"[{date_str}] {anchor_text}"
                if anchor_text not in existing_anchors and entry not in existing_anchors:
                    new_anchors.append((date_str, anchor_text, entry))
                    existing_anchors.add(anchor_text)

    # Append new anchors to ANCHORS.md
    if new_anchors:
        with ANCHORS_FILE.open("a") as f:
            f.write(f"\\n## Promoted by NREM — {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}\\n")
            for date_str, anchor_text, entry in new_anchors:
                f.write(f"- {entry}\\n")
        print(f"Promoted {len(new_anchors)} new anchors to ANCHORS.md")
    else:
        print("No new anchors found.")

    # Write NREM report
    report_lines = [
        f"# NREM Report — {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}",
        "",
        f"- Daily logs scanned: {len(daily_logs)}",
        f"- Total lines processed: {total_lines_scanned}",
        f"- New anchors promoted: {len(new_anchors)}",
        "",
        "## Promoted Anchors",
    ]
    for date_str, anchor_text, entry in new_anchors:
        report_lines.append(f"- {entry}")

    NREM_REPORT.write_text("\\n".join(report_lines) + "\\n")
    print(f"NREM report written to: {NREM_REPORT}")
    print("=== NREM Complete ===")

if __name__ == "__main__":
    main()
'''

# rem.py — REM sleep (LLM consolidation, simplified stub that works without Ollama)
rem_py = '''\
#!/usr/bin/env python3
"""
rem.py — REM sleep cycle.
Consolidates semantic schemas using LLM (Ollama llama3.2:3b).
Falls back to structural consolidation if Ollama is unavailable.
"""
import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent.parent / "memory"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
REM_REPORT = MEMORY_DIR / "rem_report.md"

def main():
    print("=== REM Sleep Cycle ===")
    schema_files = list(MEMORY_DIR.glob("*.md")) + list((MEMORY_DIR / "schemas").glob("*.md"))
    schema_files = [f for f in schema_files if not f.name.startswith("nrem") and not f.name.startswith("rem")]

    consolidated = []
    for f in schema_files:
        consolidated.append(f"- {f.name}: {len(f.read_text().splitlines())} lines")

    REM_REPORT.write_text(
        f"# REM Report — {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}\\n\\n"
        + "## Schemas Reviewed\\n"
        + "\\n".join(consolidated) + "\\n"
    )
    print(f"REM report written: {REM_REPORT}")
    print("=== REM Complete ===")

if __name__ == "__main__":
    main()
'''

(memory_brain / "index_memory.py").write_text(index_memory_py)
(memory_brain / "query_memory.py").write_text(query_memory_py)
(memory_brain / "nrem.py").write_text(nrem_py)
(memory_brain / "rem.py").write_text(rem_py)

# ── 5. Create a MEMORY.md (lean core) ──────────────────────────────────────
memory_md = """\
# MEMORY.md — Agent Core Context

## Identity
Research agent for pharma drug discovery pipeline.
Primary focus: kinase inhibitor program targeting EGFR and BRAF.

## Active Projects
- Lead optimization: CPD007 series
- Target panels: EGFR, BRAF-V600E mutant

## Contacts
- Biology lead: Dr. Sarah Chen
- CRO partner: Evotec GmbH

## Current Sprint
- IND filing preparation (deadline: 2024-04-15)
- PK/PD study design
"""
(workspace / "memory" / "MEMORY.md").write_text(memory_md)

# ── 6. Create a requirements.txt as extra distractor ──────────────────────
(workspace / "requirements.txt").write_text("lancedb\nnumpy\npyarrow\nrequests\n")

print("Workspace scaffold complete.")
print(f"Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")