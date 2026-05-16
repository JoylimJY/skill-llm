import os
import random
import json
import hashlib
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# Create directory structure mimicking an OpenClaw workspace
dirs = [
    "scripts",
    "memory",
    "memory/archive",
    "logs",
    "config",
    "data/raw",
    "data/processed",
    "reports",
    "tmp",
    "backup",
]
for d in dirs:
    Path(f"{WORKSPACE}/{d}").mkdir(parents=True, exist_ok=True)

# ── memory-dedup.py ───────────────────────────────────────────────────────────
dedup_script = r'''#!/usr/bin/env python3
"""
memory-dedup.py  — SHA-256 dedup indexing for OpenClaw memory files
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path

INDEX_FILENAME = ".index.json"
MAX_CHUNK_SIZE = 500  # max_chunk_size


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, size: int = MAX_CHUNK_SIZE):
    chunks = []
    for i in range(0, len(text), size):
        chunks.append(text[i : i + size])
    return chunks


def load_index(index_path: Path) -> dict:
    if index_path.exists():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_index(index_path: Path, index: dict):
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def index_directory(memory_dir: Path, index: dict) -> dict:
    """Index all .md / .txt files; skip unchanged (same sha256)."""
    seen_files = set()
    new_count = 0
    skip_count = 0
    total_chunks = 0

    for fpath in sorted(memory_dir.glob("**/*.md")) :
        rel = str(fpath.relative_to(memory_dir))
        seen_files.add(rel)
        content = fpath.read_text(encoding="utf-8", errors="replace")
        file_hash = compute_sha256(content)

        if rel in index and index[rel].get("file_hash") == file_hash:
            skip_count += 1
            total_chunks += len(index[rel].get("chunks", []))
            continue

        chunks = chunk_text(content)
        chunk_hashes = [compute_sha256(c) for c in chunks]
        # dedup: drop chunks whose hash already exists elsewhere in index
        existing_hashes = set()
        for v in index.values():
            for ch in v.get("chunk_hashes", []):
                existing_hashes.add(ch)

        deduped_chunks = []
        deduped_hashes = []
        for c, h in zip(chunks, chunk_hashes):
            if h not in existing_hashes:
                deduped_chunks.append(c)
                deduped_hashes.append(h)
                existing_hashes.add(h)

        index[rel] = {
            "file_hash": file_hash,
            "chunks": deduped_chunks,
            "chunk_hashes": deduped_hashes,
        }
        new_count += 1
        total_chunks += len(deduped_chunks)

    return index, seen_files, new_count, skip_count, total_chunks


def clean_index(memory_dir: Path, index: dict, seen_files: set) -> tuple:
    """Remove entries for files that no longer exist."""
    stale_keys = [k for k in index if k not in seen_files]
    for k in stale_keys:
        del index[k]
    return index, stale_keys


def search_index(index: dict, keyword: str) -> list:
    results = []
    for rel, data in index.items():
        for chunk in data.get("chunks", []):
            if keyword.lower() in chunk.lower():
                results.append({"file": rel, "snippet": chunk[:200]})
    return results


def stats_index(index: dict) -> dict:
    total_files = len(index)
    total_chunks = sum(len(v.get("chunks", [])) for v in index.values())
    total_unique_hashes = len(
        set(h for v in index.values() for h in v.get("chunk_hashes", []))
    )
    return {
        "indexed_files": total_files,
        "total_chunks": total_chunks,
        "unique_chunk_hashes": total_unique_hashes,
    }


def main():
    parser = argparse.ArgumentParser(description="Memory Dedup Indexer")
    parser.add_argument("memory_dir", help="Path to memory directory")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--search", metavar="KEYWORD", help="Search keyword in index")
    parser.add_argument(
        "--clean", action="store_true", help="Clean stale entries from index"
    )
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir).resolve()
    if not memory_dir.is_dir():
        print(f"Error: {memory_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    index_path = memory_dir / INDEX_FILENAME
    index = load_index(index_path)

    # Always re-index first
    index, seen_files, new_count, skip_count, total_chunks = index_directory(
        memory_dir, index
    )

    if args.clean:
        index, stale_keys = clean_index(memory_dir, index, seen_files)
        if stale_keys:
            print(f"Cleaned {len(stale_keys)} stale entries: {stale_keys}")
        else:
            print("No stale entries found.")

    save_index(index_path, index)

    if args.stats:
        s = stats_index(index)
        print(f"=== Memory Index Stats ===")
        print(f"Indexed files    : {s['indexed_files']}")
        print(f"Total chunks     : {s['total_chunks']}")
        print(f"Unique hashes    : {s['unique_chunk_hashes']}")
        print(f"New/updated files: {new_count}")
        print(f"Skipped (cached) : {skip_count}")
    elif args.search:
        results = search_index(index, args.search)
        if results:
            print(f"Found {len(results)} result(s) for '{args.search}':")
            for r in results:
                print(f"  [{r['file']}] {r['snippet']}")
        else:
            print(f"No results for '{args.search}'.")
    elif not args.clean:
        print(
            f"Indexed {new_count} new/updated file(s), skipped {skip_count} unchanged. "
            f"Total chunks: {total_chunks}"
        )


if __name__ == "__main__":
    main()
'''

Path(f"{WORKSPACE}/scripts/memory-dedup.py").write_text(dedup_script, encoding="utf-8")

# ── memory-watcher.py ─────────────────────────────────────────────────────────
watcher_script = r'''#!/usr/bin/env python3
"""
memory-watcher.py — Real-time file watcher for OpenClaw memory
"""
import sys
import time
import subprocess
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("watchdog not installed. Run: pip3 install watchdog")
    sys.exit(1)

DEBOUNCE_SECONDS = 1.5

class MemoryHandler(FileSystemEventHandler):
    def __init__(self, memory_dir):
        self.memory_dir = memory_dir
        self._pending = {}

    def _schedule(self, event_type, path):
        self._pending[path] = (event_type, time.time())

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule("modified", event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule("created", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule("deleted", event.src_path)

    def flush(self):
        now = time.time()
        ready = [p for p, (et, t) in self._pending.items() if now - t >= DEBOUNCE_SECONDS]
        if ready:
            print(f"[watcher] Re-indexing after changes: {ready}")
            subprocess.run([sys.executable, __file__.replace("memory-watcher.py","memory-dedup.py"), self.memory_dir, "--clean"])
            for p in ready:
                del self._pending[p]


def main():
    if len(sys.argv) < 2:
        print("Usage: memory-watcher.py <memory_dir>")
        sys.exit(1)
    memory_dir = sys.argv[1]
    handler = MemoryHandler(memory_dir)
    observer = Observer()
    observer.schedule(handler, memory_dir, recursive=True)
    observer.start()
    print(f"[watcher] Watching {memory_dir} ...")
    try:
        while True:
            time.sleep(0.5)
            handler.flush()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
'''
Path(f"{WORKSPACE}/scripts/memory-watcher.py").write_text(watcher_script, encoding="utf-8")

# ── memory-archive.sh ─────────────────────────────────────────────────────────
archive_script = '''#!/bin/bash
# memory-archive.sh — Quarterly archival of old memory files
MEMORY_DIR="${1:-./memory}"
ARCHIVE_DIR="${MEMORY_DIR}/archive"
ARCHIVE_AGE_DAYS=90
mkdir -p "$ARCHIVE_DIR"
find "$MEMORY_DIR" -maxdepth 1 -name "*.md" -mtime +${ARCHIVE_AGE_DAYS} | while read f; do
    tar -czf "${ARCHIVE_DIR}/$(basename $f .md)-$(date +%Y%m%d).tar.gz" -C "$(dirname $f)" "$(basename $f)"
    rm "$f"
    echo "Archived: $f"
done
echo "Archive complete."
'''
Path(f"{WORKSPACE}/scripts/memory-archive.sh").write_text(archive_script, encoding="utf-8")

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "config/settings.yaml": "agent_name: OpenClaw\nversion: 1.0.0\nlog_level: info\n",
    "config/db.conf": "[database]\nhost=localhost\nport=5432\nname=openclaw_db\n",
    "logs/agent.log": "2026-03-01 10:00:00 INFO Agent started\n2026-03-01 10:00:05 INFO Memory loaded\n",
    "logs/error.log": "2026-02-28 09:55:00 ERROR IndexError: list index out of range\n",
    "data/raw/experiment_001.csv": "sample_id,value,label\n1,0.92,positive\n2,0.11,negative\n3,0.77,positive\n",
    "data/raw/experiment_002.csv": "sample_id,value,label\n4,0.55,neutral\n5,0.88,positive\n",
    "data/processed/results.json": '{"total": 5, "positive": 3, "negative": 1, "neutral": 1}',
    "reports/q1_summary.txt": "Q1 2026 Summary: 1200 experiments processed, 340 anomalies flagged.\n",
    "tmp/scratch.txt": "temporary notes - do not index\n",
    "backup/config_backup.yaml": "agent_name: OpenClaw\nversion: 0.9.9\n",
}
for rel, content in distractors.items():
    p = Path(f"{WORKSPACE}/{rel}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ── Memory files (the actual content to index) ────────────────────────────────
# 12 research-note memory files; some have duplicate content (same text = same hash)
memory_contents = {
    # Unique files
    "compound_alpha_synthesis.md": (
        "# Compound Alpha Synthesis\n\n"
        "Synthesis route for Compound Alpha involves a three-step esterification process.\n"
        "Key catalyst: palladium on carbon (Pd/C) at 60°C for 4 hours.\n"
        "Yield observed: 87% in batch run B-204.\n"
        "Solvent system: ethyl acetate / hexane 3:1 ratio.\n"
        "Notes: ensure nitrogen atmosphere throughout; moisture sensitive.\n"
        "Next step: scale up to 10g batch and verify purity via HPLC.\n"
    ),
    "compound_beta_toxicity.md": (
        "# Compound Beta Toxicity Profile\n\n"
        "In-vitro cytotoxicity study on HeLa cell line.\n"
        "IC50 measured at 2.3 µM for Compound Beta.\n"
        "Selectivity index: SI > 10 against normal fibroblasts.\n"
        "Mechanism: suspected apoptosis induction via caspase-3 pathway.\n"
        "Replicate experiments confirm reproducibility (n=6, p<0.01).\n"
        "Safety margin acceptable for further in-vivo studies.\n"
    ),
    "protein_binding_assay.md": (
        "# Protein Binding Assay Results\n\n"
        "Equilibrium dialysis method used for plasma protein binding.\n"
        "Compound Alpha: 94.2% bound, primarily to albumin.\n"
        "Compound Beta: 78.5% bound.\n"
        "Free fraction (fu) Compound Alpha: 0.058.\n"
        "Free fraction (fu) Compound Beta: 0.215.\n"
        "Implications: Compound Beta has higher free fraction, potentially better CNS penetration.\n"
    ),
    "analytical_method_validation.md": (
        "# Analytical Method Validation — HPLC\n\n"
        "Method: reverse-phase HPLC with UV detection at 254 nm.\n"
        "Column: C18, 150x4.6mm, 5µm particle size.\n"
        "Mobile phase A: 0.1% formic acid in water.\n"
        "Mobile phase B: 0.1% formic acid in acetonitrile.\n"
        "Gradient: 5% B to 95% B over 12 minutes.\n"
        "Linearity: R² = 0.9998 over 0.1–100 µg/mL range.\n"
        "LOD: 0.05 µg/mL; LOQ: 0.1 µg/mL.\n"
    ),
    "stability_study_alpha.md": (
        "# Stability Study — Compound Alpha\n\n"
        "Accelerated stability conditions: 40°C / 75% RH for 6 months.\n"
        "T=0: purity 99.8% (HPLC)\n"
        "T=1 month: purity 99.5%\n"
        "T=3 months: purity 98.9%\n"
        "T=6 months: purity 97.1%\n"
        "Degradation products identified: two minor peaks at RT 4.2 and 7.8 min.\n"
        "Conclusion: stable for 6 months under ICH Q1A conditions.\n"
    ),
    "in_vivo_pk_study.md": (
        "# In-Vivo Pharmacokinetics Study\n\n"
        "Species: Sprague-Dawley rats, 250-300g, n=6 per group.\n"
        "Dose: 10 mg/kg IV bolus and 30 mg/kg oral gavage.\n"
        "Compound Alpha IV: t1/2 = 2.1 h, Vd = 0.8 L/kg, CL = 15 mL/min/kg.\n"
        "Compound Alpha PO: Cmax = 1.2 µg/mL, Tmax = 1.5 h, AUC = 4.8 µg·h/mL.\n"
        "Oral bioavailability F = 34%.\n"
        "Blood samples collected at 0.25, 0.5, 1, 2, 4, 8, 24 h post-dose.\n"
        "palladium contamination check: below ICP-MS LOQ of 0.5 ppm.\n"
    ),
    "formulation_notes.md": (
        "# Formulation Development Notes\n\n"
        "Target: oral solid dosage form (tablet) for Compound Alpha.\n"
        "Excipients screened: MCC, HPMC, croscarmellose sodium, magnesium stearate.\n"
        "Preferred formulation F3: 50mg active, 100mg MCC, 30mg HPMC K4M, 10mg croscarmellose, 2mg Mg stearate.\n"
        "Dissolution: >85% release in 30 min (USP Apparatus II, 900mL 0.1N HCl, 50 rpm).\n"
        "Hardness: 8-12 kP, friability <0.5%.\n"
        "Scale-up to 1000-tablet batch planned for Q2 2026.\n"
    ),
    "regulatory_strategy.md": (
        "# Regulatory Strategy — IND Filing\n\n"
        "Target submission: IND application Q3 2026, US FDA.\n"
        "Package includes: pharmacology, toxicology, CMC, and clinical protocol.\n"
        "Pre-IND meeting requested for April 2026.\n"
        "Key outstanding items: 28-day GLP tox study, genotoxicity battery (Ames + MN).\n"
        "Reference compounds: similar scaffolds approved under 505(b)(2) pathway.\n"
        "Estimated timeline to Phase I FIH: 18 months from IND acceptance.\n"
    ),
    # Duplicate content files (same text as compound_alpha_synthesis.md)
    "compound_alpha_synthesis_copy1.md": (
        "# Compound Alpha Synthesis\n\n"
        "Synthesis route for Compound Alpha involves a three-step esterification process.\n"
        "Key catalyst: palladium on carbon (Pd/C) at 60°C for 4 hours.\n"
        "Yield observed: 87% in batch run B-204.\n"
        "Solvent system: ethyl acetate / hexane 3:1 ratio.\n"
        "Notes: ensure nitrogen atmosphere throughout; moisture sensitive.\n"
        "Next step: scale up to 10g batch and verify purity via HPLC.\n"
    ),
    "compound_alpha_synthesis_copy2.md": (
        "# Compound Alpha Synthesis\n\n"
        "Synthesis route for Compound Alpha involves a three-step esterification process.\n"
        "Key catalyst: palladium on carbon (Pd/C) at 60°C for 4 hours.\n"
        "Yield observed: 87% in batch run B-204.\n"
        "Solvent system: ethyl acetate / hexane 3:1 ratio.\n"
        "Notes: ensure nitrogen atmosphere throughout; moisture sensitive.\n"
        "Next step: scale up to 10g batch and verify purity via HPLC.\n"
    ),
    # Another duplicate pair
    "protein_binding_assay_dup.md": (
        "# Protein Binding Assay Results\n\n"
        "Equilibrium dialysis method used for plasma protein binding.\n"
        "Compound Alpha: 94.2% bound, primarily to albumin.\n"
        "Compound Beta: 78.5% bound.\n"
        "Free fraction (fu) Compound Alpha: 0.058.\n"
        "Free fraction (fu) Compound Beta: 0.215.\n"
        "Implications: Compound Beta has higher free fraction, potentially better CNS penetration.\n"
    ),
    # Stale file that will be deleted BEFORE the agent runs (simulating purged records)
    "old_batch_record_q3_2025.md": (
        "# Batch Record Q3 2025 — ARCHIVED\n\n"
        "This record pertains to batch B-099, produced in Q3 2025.\n"
        "All QC parameters met at time of production.\n"
        "This file is retained only for regulatory traceability.\n"
        "Do not use for active research; superseded by Q4 2025 data.\n"
    ),
}

for fname, content in memory_contents.items():
    p = Path(f"{WORKSPACE}/memory/{fname}")
    p.write_text(content, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Memory files created: {len(memory_contents)}")
print(f"Distractor files created: {len(distractors)}")

# Pre-build a STALE index that already contains old_batch_record_q3_2025.md
# so the agent must --clean it after deleting that file
import hashlib, json

def compute_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size)]

stale_index = {}
for fname, content in memory_contents.items():
    chunks = chunk_text(content)
    stale_index[fname] = {
        "file_hash": compute_sha256(content),
        "chunks": chunks,
        "chunk_hashes": [compute_sha256(c) for c in chunks],
    }

# Save the stale index
index_path = Path(f"{WORKSPACE}/memory/.index.json")
with open(index_path, "w", encoding="utf-8") as f:
    json.dump(stale_index, f, ensure_ascii=False, indent=2)

# NOW delete the stale file to simulate it being removed before the agent arrives
Path(f"{WORKSPACE}/memory/old_batch_record_q3_2025.md").unlink()

print("Stale index written and old_batch_record_q3_2025.md deleted.")
print("Agent must detect and clean this orphaned index entry.")