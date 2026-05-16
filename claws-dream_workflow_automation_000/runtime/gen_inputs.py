#!/usr/bin/env python3
"""
Generate a messy, realistic workspace simulating a biomedical research AI assistant
that has been accumulating memory over many months. The agent must:
1. Read MEMORY.md and apply archival rules (ALL conditions must be true)
2. Move stale entries to memory/archive.md
3. Mark consolidated daily logs with <!-- consolidated -->
4. Update memory/index.json with health stats
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "memory",
    "memory/episodes",
    "logs",
    "data/raw",
    "data/processed",
    "reports",
    "scripts",
    "refs",
    "tmp",
    "config",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)


# ── Helper: date strings ─────────────────────────────────────────────────────
TODAY = datetime(2026, 6, 15)

def date_str(days_ago):
    return (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def days_ago_str(n):
    return (TODAY - timedelta(days=n)).isoformat()


# ── MEMORY.md ────────────────────────────────────────────────────────────────
# Contains 10 entries with varied ages, importance markers, and relation links.
# We carefully craft entries so the archival boundary is non-trivial:
#
# SHOULD BE ARCHIVED (all 4 conditions met):
#   entry-001: 95 days, importance=0.20, no pin/permanent, not in episodes
#   entry-004: 110 days, importance=0.15, no pin/permanent, not in episodes
#   entry-007: 92 days, importance=0.25, no pin/permanent, not in episodes
#
# SHOULD NOT be archived (fails at least one condition):
#   entry-002: 95 days, importance=0.20, BUT marked 📌 PIN  → exempt
#   entry-003: 85 days (< 90), importance=0.20, no pin     → too recent
#   entry-005: 100 days, importance=0.35 (>= 0.3)          → importance too high
#   entry-006: 95 days, importance=0.20, marked ⚠️ PERMANENT → never archive
#   entry-008: 100 days, importance=0.20, BUT in episodes/ path → exempt
#   entry-009: 🔥 HIGH marker, 95 days, base=0.10 → effective=0.20 (still < 0.3, but not pin/perm; no pin marker... tricky!)
#            Wait: 🔥 HIGH gives 2x base weight: base=0.10 * 2 = 0.20, still < 0.3 → ARCHIVED
#            Actually let's make entry-009 have base=0.12 → effective 0.24, still < 0.3, so ARCHIVED
#            No wait — let's make entry-009 have base=0.10 * 2 = 0.20 < 0.3 → archived
#            Actually let's make entry-009 intentionally tricky: base weight 0.12, 🔥 HIGH → 0.24 < 0.3 → ARCHIVED
#            That makes 4 archived entries.
#   entry-010: 200 days old, importance=0.10, no special marker, BUT it IS in episodes/ → exempt
#
# ARCHIVED entries: entry-001, entry-004, entry-007, entry-009
# NOT archived: entry-002 (PIN), entry-003 (recent), entry-005 (high importance),
#               entry-006 (PERMANENT), entry-008 (episodes), entry-010 (episodes)

memory_md = f"""# Long-Term Memory

> Last consolidated: {date_str(7)}

## Research Findings

### entry-001
**Topic:** PCR contamination protocol — initial findings
**Last Referenced:** {date_str(95)}
**Base Importance:** 0.20
**Relations:** none
We observed that standard PCR protocols show 15% contamination rate in open-bench conditions.

### entry-002 📌 PIN
**Topic:** Sample labeling convention v2
**Last Referenced:** {date_str(95)}
**Base Importance:** 0.20
**Relations:** entry-005
All samples must use format BIO-YYYY-NNN. Pinned because mislabeling caused 3 retries.

### entry-003
**Topic:** Centrifuge maintenance window
**Last Referenced:** {date_str(85)}
**Base Importance:** 0.20
**Relations:** none
Centrifuge unit C-4 must be serviced every 60 days. Last service: {date_str(85)}.

### entry-004
**Topic:** Outdated reagent sourcing — vendor Alpha
**Last Referenced:** {date_str(110)}
**Base Importance:** 0.15
**Relations:** none
Vendor Alpha had 3-week lead times in Q1 2025. No longer relevant after switching to vendor Beta.

### entry-005
**Topic:** Cell viability assay threshold
**Last Referenced:** {date_str(100)}
**Base Importance:** 0.35
**Relations:** entry-002, entry-010
Cells below 80% viability should be discarded before downstream analysis. Critical threshold.

### entry-006 ⚠️ PERMANENT
**Topic:** Ethics committee approval number
**Last Referenced:** {date_str(95)}
**Base Importance:** 0.20
**Relations:** none
IRB Approval #BIO-2025-447 covers all human-adjacent tissue studies through 2027-12-31.

### entry-007
**Topic:** Failed antibody batch — lot 20240811
**Last Referenced:** {date_str(92)}
**Base Importance:** 0.25
**Relations:** none
Antibody lot 20240811 showed non-specific binding. Discarded. Do not reorder from that batch.

### entry-008
**Topic:** Project Prometheus — initial hypothesis
**Last Referenced:** {date_str(100)}
**Base Importance:** 0.20
**Relations:** entry-010
(Episode: memory/episodes/prometheus.md) Gene silencing approach targeting KRAS G12C mutation.

### entry-009 🔥 HIGH
**Topic:** Deprecated staining method — crystal violet
**Last Referenced:** {date_str(95)}
**Base Importance (base):** 0.12
**Relations:** none
Crystal violet staining replaced by fluorescent markers in 2024. This method is deprecated.

### entry-010
**Topic:** Project Helios — background context
**Last Referenced:** {date_str(200)}
**Base Importance:** 0.10
**Relations:** entry-005, entry-008
(Episode: memory/episodes/helios.md) Multi-year longitudinal study on neurodegeneration biomarkers.
"""

(WORKSPACE / "MEMORY.md").write_text(memory_md)


# ── Daily logs (unconsolidated) ──────────────────────────────────────────────
# Two recent daily logs that need to be marked consolidated after processing.

log1_date = date_str(1)
log1 = f"""# Daily Log — {log1_date}

## Interactions

- Discussed PCR contamination issue with Dr. Reyes. Referenced entry-001.
- Team agreed to update cell viability threshold entry-005 with new 82% cutoff.
- New finding: Flow cytometer FC-7 calibration drifts after 200 runs.

## Decisions
- Switched buffer solution from PBS to HBSS for live-cell imaging.
- Archived old staining protocol document from 2023.
"""

log2_date = date_str(2)
log2 = f"""# Daily Log — {log2_date}

## Interactions

- Reviewed Project Prometheus (entry-008) progress with PI.
- Confirmed IRB approval number (entry-006) still valid.
- Noted that vendor Beta now has 5-day lead times (improvement from Alpha).

## Decisions
- Added new SOP for CRISPR editing: use electroporation over viral vectors.
- Updated centrifuge schedule reference (entry-003).
"""

(WORKSPACE / f"memory/{log1_date}.md").write_text(log1)
(WORKSPACE / f"memory/{log2_date}.md").write_text(log2)


# ── memory/archive.md — pre-existing archive (some old entries already there) ──
archive_md = f"""# Memory Archive

> Entries archived due to staleness, low importance, or supersession.

<!-- archived: 2025-11-01 -->
### archived-001
**Topic:** Old qPCR primer design v1
**Archived On:** 2025-11-01
**Reason:** Superseded by v2 design.
Primer set used from 2024-01 to 2025-10. Tm values: 58-62°C.
"""

(WORKSPACE / "memory/archive.md").write_text(archive_md)


# ── memory/procedures.md ─────────────────────────────────────────────────────
procedures_md = """# Workflow Preferences

- Always use HBSS over PBS for live-cell work.
- Electroporation preferred for CRISPR delivery.
- Daily backup of raw data to /data/raw before processing.
"""
(WORKSPACE / "memory/procedures.md").write_text(procedures_md)


# ── memory/dream-log.md ──────────────────────────────────────────────────────
dream_log = f"""# Dream Log

## Consolidation Report — {date_str(7)}
- Processed 2 daily logs
- Added 1 new entry
- Updated 2 entries
- Archived 1 entry
- Health Score: 0.71
"""
(WORKSPACE / "memory/dream-log.md").write_text(dream_log)


# ── memory/index.json — OUTDATED, needs to be updated by agent ───────────────
# This is the stale state BEFORE the current consolidation pass.
# Agent must update it with fresh health stats.
index_data = {
    "last_consolidated": date_str(7),
    "total_entries": 10,
    "archived_count": 1,
    "health": {
        "overall": 0.71,
        "freshness": 0.80,
        "coverage": 0.75,
        "coherence": 0.50,
        "efficiency": 0.65,
        "reachability": 0.60
    },
    "entries": {
        "entry-001": {"last_referenced": date_str(95), "importance": 0.20, "relations": []},
        "entry-002": {"last_referenced": date_str(95), "importance": 0.20, "relations": ["entry-005"], "pin": True},
        "entry-003": {"last_referenced": date_str(85), "importance": 0.20, "relations": []},
        "entry-004": {"last_referenced": date_str(110), "importance": 0.15, "relations": []},
        "entry-005": {"last_referenced": date_str(100), "importance": 0.35, "relations": ["entry-002", "entry-010"]},
        "entry-006": {"last_referenced": date_str(95), "importance": 0.20, "relations": [], "permanent": True},
        "entry-007": {"last_referenced": date_str(92), "importance": 0.25, "relations": []},
        "entry-008": {"last_referenced": date_str(100), "importance": 0.20, "relations": ["entry-010"], "episode": "memory/episodes/prometheus.md"},
        "entry-009": {"last_referenced": date_str(95), "importance_base": 0.12, "high_marker": True, "relations": []},
        "entry-010": {"last_referenced": date_str(200), "importance": 0.10, "relations": ["entry-005", "entry-008"], "episode": "memory/episodes/helios.md"}
    },
    "milestones": {
        "first_dream": date_str(180),
        "current_streak": 7,
        "total_entries_milestone": 10
    }
}

(WORKSPACE / "memory/index.json").write_text(json.dumps(index_data, indent=2))


# ── Episodes ─────────────────────────────────────────────────────────────────
(WORKSPACE / "memory/episodes/prometheus.md").write_text(
    "# Project Prometheus\n\nGene silencing targeting KRAS G12C mutation. Phase 1 in progress.\n"
)
(WORKSPACE / "memory/episodes/helios.md").write_text(
    "# Project Helios\n\nLongitudinal neurodegeneration biomarker study. Year 3 of 5.\n"
)


# ── Distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "data/raw/sample_batch_001.csv").write_text(
    "sample_id,viability,date\nBIO-2026-001,85%,2026-06-10\nBIO-2026-002,79%,2026-06-11\n"
)
(WORKSPACE / "data/raw/sample_batch_002.csv").write_text(
    "sample_id,viability,date\nBIO-2026-003,91%,2026-06-12\nBIO-2026-004,88%,2026-06-13\n"
)
(WORKSPACE / "data/processed/qpcr_results.tsv").write_text(
    "gene\tct_value\tsample\nKRAS\t28.4\tBIO-2026-001\nTP53\t31.2\tBIO-2026-002\n"
)
(WORKSPACE / "reports/q1_summary.md").write_text(
    "# Q1 2026 Research Summary\n\nAll targets met. Flow cytometry improved 12%.\n"
)
(WORKSPACE / "reports/q2_draft.md").write_text(
    "# Q2 2026 Draft\n\nPending final data from Helios cohort 3.\n"
)
(WORKSPACE / "scripts/run_analysis.sh").write_text(
    "#!/bin/bash\npython3 analysis.py --input data/raw --output data/processed\n"
)
(WORKSPACE / "scripts/backup.sh").write_text(
    "#!/bin/bash\ncp -r data/raw /backups/$(date +%Y%m%d)/\n"
)
(WORKSPACE / "config/lab_settings.json").write_text(
    json.dumps({"centrifuge_rpm": 3000, "incubator_temp_c": 37, "co2_percent": 5.0}, indent=2)
)
(WORKSPACE / "tmp/scratch_notes.txt").write_text(
    "TODO: check buffer pH before assay\nReminder: order more pipette tips\n"
)
(WORKSPACE / "refs/antibody_catalog.md").write_text(
    "# Antibody Catalog\n\n- Anti-KRAS G12C: vendor Beta, cat# BT-4421\n- Anti-TP53: vendor Gamma, cat# GM-8834\n"
)
(WORKSPACE / "logs/system.log").write_text(
    "[2026-06-14 09:12:01] Analysis pipeline completed\n[2026-06-14 11:45:22] Backup completed\n"
)

print("Workspace generated successfully.")
print(f"Workspace root: {WORKSPACE}")
print("\nKey files created:")
print("  MEMORY.md (10 entries, varied archival eligibility)")
print(f"  memory/{log1_date}.md (unconsolidated daily log)")
print(f"  memory/{log2_date}.md (unconsolidated daily log)")
print("  memory/archive.md (pre-existing archive)")
print("  memory/index.json (stale, needs updating)")