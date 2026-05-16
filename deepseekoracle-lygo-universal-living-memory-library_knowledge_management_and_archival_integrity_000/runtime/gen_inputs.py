#!/usr/bin/env python3
"""
Generate the adversarial sandbox workspace for the LYGO Living Memory Library task.
"""
import os
import json
import random
import hashlib
import datetime

random.seed(42)

BASE = "/workspace"

# ─────────────────────────────────────────────
# 1.  Directory structure
# ─────────────────────────────────────────────
dirs = [
    "references",
    "scripts",
    "archive/raw_logs",
    "archive/analysis",
    "archive/reports",
    "archive/deprecated",
    "scratch/temp",
    "scratch/drafts",
    "outputs",
    "outputs/mint",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ─────────────────────────────────────────────
# 2.  references/library_spec.md
#     (rules + file roles — the canonical spec)
# ─────────────────────────────────────────────
library_spec = """\
# LYGO Living Memory Library — Specification v1.1

## File Roles
| Role Tag         | Meaning                                              |
|------------------|------------------------------------------------------|
| CORE             | Essential, always retained in Master Archive         |
| SUPPORT          | Context files; retained if space permits             |
| ARCHIVE_ONLY     | Historical; never counted in the active Max20 index  |
| {FRAGILE}        | Needs manual review before archival; MUST be listed  |
|                  | separately in every audit report under fragile_flags |

## Max20 Rule
The active index (`core_files_index.json`) MUST contain ≤ 20 entries.
Any index with > 20 entries is immediately non-compliant and MUST be
trimmed during the compression workflow. Trimmed files go to ARCHIVE_ONLY.

## Audit Report Format (JSON)
An audit report MUST contain exactly these top-level keys:
  - "audit_timestamp"   : ISO-8601 string
  - "total_indexed"     : int  (number of files in the index at audit time)
  - "integrity"         : list of filenames MISSING from disk but in index
  - "drift"             : list of filenames on disk but NOT in the index
                          (search path: archive/ subtree only)
  - "fragile_flags"     : list of entries whose tag contains "{FRAGILE}"
  - "compliant"         : bool  (true iff total_indexed ≤ 20 AND integrity is empty)

## Compression Workflow
1. Load the current index.
2. Drop all entries tagged ARCHIVE_ONLY or with status "deprecated".
3. Keep all CORE entries.
4. If total remaining > 20, drop lowest-priority SUPPORT entries until ≤ 20.
5. {FRAGILE} entries MUST be retained in the compressed index with their
   tag preserved; do NOT silently strip the {FRAGILE} marker.
6. Write the new index to `core_files_index.json` (in-place).
7. Write a compression manifest to `outputs/compression_manifest.json`.

## Compression Manifest Format (JSON)
  - "compression_timestamp" : ISO-8601 string
  - "entries_before"        : int
  - "entries_after"         : int
  - "dropped_entries"       : list of filenames that were removed
  - "retained_fragile"      : list of {FRAGILE}-tagged filenames kept

## LYGO-MINT Anchor
After compression, mint the Master Archive by:
1. Collecting all filenames retained in the compressed index (sorted).
2. Computing SHA-256 of the sorted-filename concatenation string
   (filenames joined by newline "\\n").
3. Producing an Anchor Snippet JSON file at `outputs/mint/anchor_snippet.json`
   with keys:
     - "lygo_mint_label"   : "LYGO-MINT-ANCHOR"  (exact literal string)
     - "algorithm"         : "sha256"
     - "file_count"        : int
     - "hash"              : hex-digest string
     - "minted_at"         : ISO-8601 string
     - "source_index"      : "core_files_index.json"
"""
with open(os.path.join(BASE, "references/library_spec.md"), "w") as f:
    f.write(library_spec)

# ─────────────────────────────────────────────
# 3.  references/audit_protocol.md
# ─────────────────────────────────────────────
audit_protocol = """\
# Audit Protocol

## Steps
1. Load `references/core_files_index.json`.
2. For each entry, check whether the file exists under the workspace root.
3. Walk `archive/` subtree; collect filenames not present in the index → drift.
4. Collect entries tagged `{FRAGILE}` → fragile_flags.
5. Evaluate compliance: total_indexed ≤ 20 AND integrity list is empty.
6. Write report to `outputs/audit_report.json`.

## Invocation
    python scripts/audit_library.py --workspace /workspace

The script exits 0 on compliant, 1 on non-compliant.
"""
with open(os.path.join(BASE, "references/audit_protocol.md"), "w") as f:
    f.write(audit_protocol)

# ─────────────────────────────────────────────
# 4.  references/compression_protocol.md
# ─────────────────────────────────────────────
compression_protocol = """\
# Compression Protocol

Follow the Compression Workflow defined in library_spec.md §Compression Workflow.
After compression, invoke LYGO-MINT as defined in library_spec.md §LYGO-MINT Anchor.
Both the compression manifest and anchor snippet are mandatory deliverables.
"""
with open(os.path.join(BASE, "references/compression_protocol.md"), "w") as f:
    f.write(compression_protocol)

# ─────────────────────────────────────────────
# 5.  references/seal_220cupdate_excerpt.md
# ─────────────────────────────────────────────
seal_excerpt = """\
# SEAL-220C Update Excerpt
Effective v1.1: the {FRAGILE} tag supersedes the old REVIEW tag.
All REVIEW-tagged files must be re-tagged as {FRAGILE} before archival.
The Max20 limit is hard; no waivers are granted post-seal.
"""
with open(os.path.join(BASE, "references/seal_220cupdate_excerpt.md"), "w") as f:
    f.write(seal_excerpt)

# ─────────────────────────────────────────────
# 6.  Build realistic archive files (distractor files on disk)
# ─────────────────────────────────────────────
archive_files = [
    ("archive/raw_logs/run_001.log",        "Run 001 raw output data\nlines: 4020\nstatus: complete"),
    ("archive/raw_logs/run_002.log",        "Run 002 raw output data\nlines: 3812\nstatus: complete"),
    ("archive/raw_logs/run_003_partial.log","Run 003 PARTIAL — aborted at line 201"),
    ("archive/analysis/alpha_pipeline.py",  "# Alpha analysis pipeline v2\nprint('alpha')"),
    ("archive/analysis/beta_pipeline.py",   "# Beta analysis pipeline v1\nprint('beta')"),
    ("archive/analysis/gamma_notes.txt",    "Gamma experiment notes — inconclusive"),
    ("archive/analysis/delta_results.csv",  "sample,value\nA,1.2\nB,3.4\nC,0.9"),
    ("archive/reports/q1_summary.md",       "# Q1 Summary\nAll systems nominal."),
    ("archive/reports/q2_summary.md",       "# Q2 Summary\nDrift detected in run_003."),
    ("archive/reports/interim_findings.md", "# Interim\nFragile data points noted."),
    ("archive/deprecated/old_pipeline_v0.py","# DEPRECATED v0 — do not use"),
    ("archive/deprecated/legacy_index.json", json.dumps({"note": "old format", "files": []})),
    ("scratch/temp/scratch_notes.txt",       "TODO: review gamma_notes"),
    ("scratch/drafts/draft_report.md",       "# Draft — not finalized"),
]

for rel_path, content in archive_files:
    full = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ─────────────────────────────────────────────
# 7.  references/core_files_index.json
#     INTENTIONALLY BLOATED (25 entries > Max20)
#     Some entries have missing files (integrity drift)
#     Some entries tagged {FRAGILE}
#     Some tagged ARCHIVE_ONLY / deprecated
# ─────────────────────────────────────────────
entries = [
    # CORE — files that exist
    {"filename": "archive/raw_logs/run_001.log",        "role": "CORE",         "status": "active",     "tag": ""},
    {"filename": "archive/raw_logs/run_002.log",        "role": "CORE",         "status": "active",     "tag": ""},
    {"filename": "archive/analysis/alpha_pipeline.py",  "role": "CORE",         "status": "active",     "tag": ""},
    {"filename": "archive/analysis/beta_pipeline.py",   "role": "CORE",         "status": "active",     "tag": ""},
    {"filename": "archive/reports/q1_summary.md",       "role": "CORE",         "status": "active",     "tag": ""},
    {"filename": "archive/reports/q2_summary.md",       "role": "CORE",         "status": "active",     "tag": ""},
    # CORE — {FRAGILE} files that exist
    {"filename": "archive/raw_logs/run_003_partial.log","role": "CORE",         "status": "active",     "tag": "{FRAGILE}"},
    {"filename": "archive/analysis/gamma_notes.txt",    "role": "SUPPORT",      "status": "active",     "tag": "{FRAGILE}"},
    # SUPPORT — files that exist
    {"filename": "archive/analysis/delta_results.csv",  "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/reports/interim_findings.md", "role": "SUPPORT",      "status": "active",     "tag": ""},
    # ARCHIVE_ONLY — files that exist (should be dropped in compression)
    {"filename": "archive/deprecated/old_pipeline_v0.py","role": "ARCHIVE_ONLY","status": "deprecated", "tag": ""},
    {"filename": "archive/deprecated/legacy_index.json","role": "ARCHIVE_ONLY", "status": "deprecated", "tag": ""},
    # SUPPORT — deprecated status (should be dropped)
    {"filename": "archive/analysis/gamma_notes.txt",    "role": "SUPPORT",      "status": "deprecated", "tag": ""},  # duplicate intentional for noise
    # MISSING files (integrity failures — these do NOT exist on disk)
    {"filename": "archive/analysis/omega_pipeline.py",  "role": "CORE",         "status": "active",     "tag": ""},
    {"filename": "archive/reports/final_report_v3.md",  "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/raw_logs/run_004.log",        "role": "SUPPORT",      "status": "active",     "tag": ""},
    # Extra SUPPORT filler entries to push total > 20
    {"filename": "archive/analysis/epsilon_model.pkl",  "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/analysis/zeta_config.yaml",   "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/reports/methodology_v2.md",   "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/raw_logs/run_005.log",        "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/raw_logs/run_006.log",        "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/analysis/theta_viz.py",       "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/reports/calibration_log.md",  "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/analysis/iota_stats.R",       "role": "SUPPORT",      "status": "active",     "tag": ""},
    {"filename": "archive/raw_logs/run_007_partial.log","role": "SUPPORT",      "status": "active",     "tag": "{FRAGILE}"},
]

with open(os.path.join(BASE, "references/core_files_index.json"), "w") as f:
    json.dump({"version": "1.1", "entries": entries}, f, indent=2)

# ─────────────────────────────────────────────
# 8.  scripts/audit_library.py  (the existing script)
# ─────────────────────────────────────────────
audit_script = '''\
#!/usr/bin/env python3
"""
LYGO Living Memory Library — Audit Script (v1.1)
Usage: python scripts/audit_library.py --workspace /workspace
Reads references/core_files_index.json, produces outputs/audit_report.json.
Exit 0 = compliant, Exit 1 = non-compliant or error.
"""
import argparse, json, os, sys, datetime

def run_audit(workspace):
    index_path = os.path.join(workspace, "references", "core_files_index.json")
    out_path   = os.path.join(workspace, "outputs", "audit_report.json")

    with open(index_path) as f:
        data = json.load(f)
    entries = data.get("entries", [])

    total_indexed = len(entries)
    integrity     = []
    fragile_flags = []

    for e in entries:
        fname = e.get("filename", "")
        full  = os.path.join(workspace, fname)
        if not os.path.exists(full):
            integrity.append(fname)
        if "{FRAGILE}" in e.get("tag", ""):
            fragile_flags.append(fname)

    # Drift: files in archive/ not in index
    indexed_set = {e["filename"] for e in entries}
    drift = []
    archive_root = os.path.join(workspace, "archive")
    for root, dirs, files in os.walk(archive_root):
        for fn in files:
            abs_path = os.path.join(root, fn)
            rel_path = os.path.relpath(abs_path, workspace)
            if rel_path not in indexed_set:
                drift.append(rel_path)

    compliant = (total_indexed <= 20) and (len(integrity) == 0)

    report = {
        "audit_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_indexed":   total_indexed,
        "integrity":       integrity,
        "drift":           drift,
        "fragile_flags":   fragile_flags,
        "compliant":       compliant,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Audit complete. Compliant: {compliant}")
    sys.exit(0 if compliant else 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/workspace")
    args = parser.parse_args()
    run_audit(args.workspace)
'''
with open(os.path.join(BASE, "scripts/audit_library.py"), "w") as f:
    f.write(audit_script)

# ─────────────────────────────────────────────
# 9.  scripts/self_check.py
# ─────────────────────────────────────────────
self_check_script = '''\
#!/usr/bin/env python3
"""
LYGO Living Memory Library — Self-check / pack sanity (v1.1)
Usage: python scripts/self_check.py --workspace /workspace
Verifies that core_files_index.json is well-formed and ≤ 20 entries.
"""
import argparse, json, os, sys

def run_check(workspace):
    index_path = os.path.join(workspace, "references", "core_files_index.json")
    with open(index_path) as f:
        data = json.load(f)
    entries = data.get("entries", [])
    n = len(entries)
    if n > 20:
        print(f"FAIL: index has {n} entries (max 20)")
        sys.exit(1)
    print(f"OK: index has {n} entries")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/workspace")
    args = parser.parse_args()
    run_check(args.workspace)
'''
with open(os.path.join(BASE, "scripts/self_check.py"), "w") as f:
    f.write(self_check_script)

# ─────────────────────────────────────────────
# 10.  Distractor files (not in index, not in archive)
# ─────────────────────────────────────────────
distractors = [
    ("scratch/temp/tmp_42.bin",         "binary noise 42"),
    ("scratch/drafts/ideas.txt",         "random ideas placeholder"),
    ("scratch/temp/env_dump.txt",        "PATH=/usr/bin\nHOME=/root"),
    ("outputs/old_run.txt",              "legacy output — ignore"),
]
for rel, content in distractors:
    full = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Index entries: {len(entries)} (intentionally > 20 to force compression)")