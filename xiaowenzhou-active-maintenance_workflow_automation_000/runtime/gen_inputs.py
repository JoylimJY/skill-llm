import os
import random
import hashlib
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

BASE = Path("/root/.openclaw/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "MEMORY/fragments",
    "MEMORY/notes",
    "MEMORY/DECISIONS",
    "tmp/cache",
    "tmp/builds",
    "tmp/logs",
    "artifacts/old",
    "artifacts/recent",
    "data/raw",
    "data/processed",
    "config",
    "logs/system",
    "logs/audit",
]
for d in dirs:
    (BASE / d).mkdir(parents=True, exist_ok=True)

# ── Helper: set file mtime to N days ago ────────────────────────────────────
def age_file(path: Path, days: int):
    ts = (datetime.now() - timedelta(days=days)).timestamp()
    os.utime(path, (ts, ts))

# ── 1. TEMP files (some old, some recent) ───────────────────────────────────
old_temp_files = []
for i in range(6):
    p = BASE / "tmp/cache" / f"cache_{i:02d}.tmp"
    p.write_text(f"cache data {i} - stale entry from previous run\n" * 20)
    age_file(p, days=random.randint(4, 15))   # old → should be cleaned
    old_temp_files.append(p)

for i in range(3):
    p = BASE / "tmp/builds" / f"build_{i:02d}.artifact"
    p.write_text(f"build artifact {i}\n" * 10)
    age_file(p, days=random.randint(5, 10))   # old
    old_temp_files.append(p)

# Recent temp files that should NOT be deleted
for i in range(4):
    p = BASE / "tmp/logs" / f"recent_{i:02d}.log"
    p.write_text(f"recent log entry {i}\n")
    age_file(p, days=random.randint(0, 2))    # fresh → keep

# ── 2. MEMORY fragments (with exact duplicates) ─────────────────────────────
fragment_contents = [
    "Insight: Use lazy evaluation for large datasets to reduce memory footprint.",
    "Insight: Prefer immutable data structures when concurrency is required.",
    "Insight: Cache invalidation should be event-driven, not time-driven.",
    "Insight: Logging at DEBUG level in production degrades throughput by ~30%.",
    "Insight: Connection pools must be sized to (2 * CPU_cores + 1) for I/O bound workloads.",
]

# Write original fragments
for idx, content in enumerate(fragment_contents):
    p = BASE / "MEMORY/fragments" / f"frag_{idx:03d}.mem"
    p.write_text(content + "\n")
    age_file(p, days=1)

# Write EXACT duplicates (same content, different filenames)
duplicates_written = []
dup_pairs = [(0, "frag_000_copy.mem"), (2, "frag_002_dup.mem"), (4, "frag_004_duplicate.mem")]
for src_idx, dup_name in dup_pairs:
    p = BASE / "MEMORY/fragments" / dup_name
    p.write_text(fragment_contents[src_idx] + "\n")
    age_file(p, days=1)
    duplicates_written.append(dup_name)

# Write a near-duplicate (NOT exact — should NOT be removed)
near_dup = BASE / "MEMORY/fragments" / "frag_001_similar.mem"
near_dup.write_text("Insight: Prefer immutable data structures when concurrency is involved.\n")
age_file(near_dup, days=1)

# ── 3. Dense notes for distillation ─────────────────────────────────────────
dense_note = """
Session Log 2026-01-15:
Reviewed 47 pages of infrastructure docs. Key point: always use connection pooling.
Also reviewed logging strategy — DEBUG logs hurt perf. Checked caching — event-driven is best.
Team discussed immutability for concurrency safety. Long debate, consensus reached: immutable wins.
Additional: lazy eval saves memory. Confirmed by benchmarks on 3 separate systems.
Miscellaneous discussion about coffee machine maintenance schedule. Not relevant.
Side note: someone left the lights on in server room B. Facilities notified.
Another note: birthday cake for Alex on Friday. Unrelated to engineering.
Core finding: pool sizing formula is 2N+1 where N=CPU cores.
""".strip()
(BASE / "MEMORY/notes" / "session_2026_01_15.txt").write_text(dense_note + "\n")

dense_note2 = """
Research Digest 2026-01-20:
Compiled reading list results. Lazy evaluation confirmed efficient. See fragment 000.
Cache invalidation: event-driven approach validated in production (3 case studies).
Immutability under concurrency: academic papers support this — 12 citations gathered.
Noise: weekly standup notes, parking lot discussion, catering order for Q1 offsite.
Key numbers: 30% throughput degradation from DEBUG logging (measured).
Pool sizing: 2*cores+1 validated across 5 cloud providers.
Random: need to update DNS records for dev environment. IT ticket filed.
""".strip()
(BASE / "MEMORY/notes" / "research_digest_2026_01_20.txt").write_text(dense_note2 + "\n")

# ── 4. Distractor files ──────────────────────────────────────────────────────
(BASE / "data/raw" / "dataset_alpha.csv").write_text("id,value\n1,foo\n2,bar\n3,baz\n")
(BASE / "data/raw" / "dataset_beta.csv").write_text("id,value\n4,qux\n5,quux\n")
(BASE / "data/processed" / "result_2026.json").write_text(json.dumps({"status": "processed", "count": 5}))
(BASE / "config" / "app.conf").write_text("[server]\nport=8080\nhost=localhost\n")
(BASE / "config" / "db.conf").write_text("[database]\nengine=sqlite\npath=/tmp/db.sqlite\n")
(BASE / "logs/system" / "syslog_jan.log").write_text("Jan 15 INFO kernel started\nJan 15 WARN disk usage 75%\n")
(BASE / "logs/audit" / "audit_2026.log").write_text("2026-01-01 AUDIT session_start user=kim\n")
(BASE / "artifacts/old" / "v1.0.tar.gz").write_text("fake tarball v1.0")
age_file(BASE / "artifacts/old" / "v1.0.tar.gz", days=60)
(BASE / "artifacts/recent" / "v2.0.tar.gz").write_text("fake tarball v2.0")
age_file(BASE / "artifacts/recent" / "v2.0.tar.gz", days=1)

# ── 5. nightly_optimizer.py  (functional but MISCONFIGURED) ─────────────────
optimizer_code = '''#!/usr/bin/env python3
"""
nightly_optimizer.py — OpenClaw Active Maintenance
Configure TEMP_DIRS, threshold, and days before running.
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from decision_logger import log_decision

# ── CONFIGURATION (edit before running) ─────────────────────────────────────
TEMP_DIRS = []          # directories to clean of aged temp files
threshold  = 95         # disk usage % that triggers a warning
days       = 30         # age in days: files older than this are removed
# ────────────────────────────────────────────────────────────────────────────

BASE       = Path(__file__).parent.parent
MEMORY_DIR = BASE / "MEMORY"
FRAG_DIR   = MEMORY_DIR / "fragments"
NOTES_DIR  = MEMORY_DIR / "notes"

RESULTS = {
    "cleaned_files":    [],
    "duplicates_removed": [],
    "distilled_notes":  [],
    "warnings":         [],
}

# ── 1. System Health Check ───────────────────────────────────────────────────
def check_disk():
    import shutil as sh
    total, used, free = sh.disk_usage("/")
    pct = (used / total) * 100
    if pct >= threshold:
        msg = f"WARN: Disk usage {pct:.1f}% exceeds threshold {threshold}%"
        RESULTS["warnings"].append(msg)
        print(msg)
    else:
        print(f"INFO: Disk usage {pct:.1f}% — OK (threshold={threshold}%)")

# ── 2. Auto-Cleanup ──────────────────────────────────────────────────────────
def cleanup_temp():
    cutoff = datetime.now() - timedelta(days=days)
    for dir_path in TEMP_DIRS:
        p = Path(dir_path)
        if not p.exists():
            print(f"SKIP: {dir_path} does not exist")
            continue
        for f in p.rglob("*"):
            if f.is_file():
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    RESULTS["cleaned_files"].append(str(f))
                    print(f"CLEAN: {f}")
                    f.unlink()

# ── 3. Memory Metabolism — Exact Deduplication ──────────────────────────────
def dedup_fragments():
    seen_hashes = {}
    if not FRAG_DIR.exists():
        return
    for frag in sorted(FRAG_DIR.iterdir()):
        if not frag.is_file():
            continue
        h = hashlib.md5(frag.read_bytes()).hexdigest()
        if h in seen_hashes:
            RESULTS["duplicates_removed"].append(frag.name)
            print(f"DEDUP: removing {frag.name} (duplicate of {seen_hashes[h]})")
            frag.unlink()
        else:
            seen_hashes[h] = frag.name

# ── 4. Memory Metabolism — Distillation ─────────────────────────────────────
def distill_notes():
    if not NOTES_DIR.exists():
        return
    for note_file in NOTES_DIR.iterdir():
        if not note_file.is_file():
            continue
        lines = note_file.read_text().splitlines()
        # Distillation rule: keep only lines that start with known signal words
        signal_words = ("Insight:", "Key", "Core", "key", "core",
                        "WARN", "INFO", "finding", "Finding",
                        "Confirmed", "confirmed", "validated", "Validated")
        distilled = [ln for ln in lines if any(ln.strip().startswith(sw) for sw in signal_words)]
        if distilled:
            out_path = NOTES_DIR / (note_file.stem + "_distilled.txt")
            out_path.write_text("\\n".join(distilled) + "\\n")
            RESULTS["distilled_notes"].append(out_path.name)
            print(f"DISTILL: {note_file.name} -> {out_path.name}")

# ── 5. Decision Logging ──────────────────────────────────────────────────────
def log_maintenance_decision():
    log_decision(
        title="Nightly Maintenance Cycle",
        summary=f"Cleaned {len(RESULTS[\'cleaned_files\'])} files, "
                f"removed {len(RESULTS[\'duplicates_removed\'])} duplicates, "
                f"distilled {len(RESULTS[\'distilled_notes\'])} notes.",
        details=RESULTS,
    )

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== OpenClaw Nightly Optimizer ===")
    check_disk()
    cleanup_temp()
    dedup_fragments()
    distill_notes()
    log_maintenance_decision()
    print("=== Done ===")
'''
(BASE / "scripts" / "nightly_optimizer.py").write_text(optimizer_code)

# ── 6. decision_logger.py ────────────────────────────────────────────────────
logger_code = '''#!/usr/bin/env python3
"""
decision_logger.py — OpenClaw Decision Logging
Writes structured JSON decision records to MEMORY/DECISIONS/.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

DECISIONS_DIR = Path(__file__).parent.parent / "MEMORY" / "DECISIONS"

def log_decision(title: str, summary: str = "", details: dict = None):
    """
    Log a maintenance decision.

    Parameters
    ----------
    title   : Short title for the decision (used in filename).
    summary : Human-readable summary string.
    details : Arbitrary dict of structured results.
    """
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now()
    slug = title.lower().replace(" ", "_")[:40]
    filename = f"{ts.strftime(\'%Y%m%d_%H%M%S\')}_{slug}.json"
    record = {
        "timestamp": ts.isoformat(),
        "title":     title,
        "summary":   summary,
        "details":   details or {},
    }
    out = DECISIONS_DIR / filename
    out.write_text(json.dumps(record, indent=2))
    print(f"LOGGED: {out}")
    return str(out)
'''
(BASE / "scripts" / "decision_logger.py").write_text(logger_code)

# ── 7. Expose old_temp_files manifest for eval ──────────────────────────────
manifest = {
    "old_temp_files": [str(f) for f in old_temp_files],
    "recent_temp_files": [
        str(BASE / "tmp/logs" / f"recent_{i:02d}.log") for i in range(4)
    ],
    "duplicate_fragments": [str(BASE / "MEMORY/fragments" / n) for _, n in dup_pairs],
    "original_fragments":  [str(BASE / "MEMORY/fragments" / f"frag_{i:03d}.mem") for i in range(5)],
    "near_dup_fragment":   str(near_dup),
}
(BASE / "config" / ".eval_manifest.json").write_text(json.dumps(manifest, indent=2))

print("Workspace generated successfully.")
print(f"  Old temp files (should be cleaned): {len(old_temp_files)}")
print(f"  Duplicate fragments (should be deduped): {len(dup_pairs)}")