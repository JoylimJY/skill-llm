#!/usr/bin/env python3
"""
Generate a messy, realistic biotech research workspace for the audit task.
"""
import os
import json
import stat
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path("/workspace")

# ── helpers ──────────────────────────────────────────────────────────────────
def write(path: Path, content: str, days_old: int = 0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if days_old:
        ts = (datetime.now() - timedelta(days=days_old)).timestamp()
        os.utime(path, (ts, ts))

# ── tier-rules.md ─────────────────────────────────────────────────────────────
write(WORKSPACE / "skills/workspace-audit/references/tier-rules.md", """\
# Tier Rules

## Promotion: WARM → HOT
A WARM file is promoted to HOT when ALL of the following are true:
- It has been referenced by 3 or more other workspace files
- It contains a section heading `## Status` or `## Summary`
- Its last-modified date is within the past 14 days

Promotion action: append a one-line summary entry to `MEMORY.md` under a `## Promoted Files` heading.

## Demotion: HOT → WARM
A root `.md` file (HOT) is demoted to WARM when:
- It has zero references from any other workspace file
- It has NOT been modified in the past 30 days

Demotion action: remove its summary line from `MEMORY.md`; ensure the file itself remains at root.

## Demotion: WARM → COLD
A WARM file (`memory/*.md`) is moved to `memory/archive/` when:
- Its filename matches the pattern `YYYY-MM-DD*.md` (daily note)
- Its last-modified date is older than 7 days

## Exceptions
- `MEMORY.md`, `TODO.md`, `USER.md` are permanently HOT — never demote.
- Files listed under `## pinned` in `local-overrides.md` are exempt from demotion.
""")

# ── local-overrides.md ────────────────────────────────────────────────────────
write(WORKSPACE / "skills/workspace-audit/references/local-overrides.md", """\
# Local Overrides

## sync-pairs
These file pairs must keep specific sections in sync. Report drift if their content differs.

- source: `projects/compound-x/STATUS.md` section `## Current Phase`
  target: `MEMORY.md` section `## Current Phase`

- source: `memory/reagents.md` section `## Approved Reagents`
  target: `projects/lab-protocols/approved-reagents.md` section `## Approved Reagents`

## pinned
- memory/reagents.md
""")

# ── Mock `cron` CLI ───────────────────────────────────────────────────────────
# The cron CLI lives at /usr/local/bin/cron and responds to `cron list`
CRON_DATA = [
    {
        "id": "cron-001",
        "schedule": "0 2 * * *",
        "message": "Audit workspace files including projects/compound-x/STATUS.md and memory/reagents.md"
    },
    {
        "id": "cron-002",
        "schedule": "0 6 * * 1",
        "message": "Weekly review: check projects/lab-protocols/approved-reagents.md for updates"
    },
    {
        "id": "cron-003",
        "schedule": "30 1 * * *",
        "message": "Backup memory/daily-notes.md and memory/archive/ to cold storage"
    },
    {
        "id": "cron-004",
        "schedule": "0 3 * * *",
        "message": "Sync projects/genomics/pipeline.md with lab LIMS — file does NOT exist yet"
    },
]
CRON_JSON = json.dumps(CRON_DATA, indent=2)

cron_script = f"""\
#!/usr/bin/env python3
import sys, json
data = {CRON_JSON!r}
args = sys.argv[1:]
if args and args[0] == "list":
    print(data)
else:
    print("Usage: cron list", file=sys.stderr)
    sys.exit(1)
"""
cron_bin = Path("/usr/local/bin/cron")
cron_bin.write_text(cron_script)
cron_bin.chmod(cron_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── HOT files (root .md) ──────────────────────────────────────────────────────
write(WORKSPACE / "MEMORY.md", """\
# Memory

## Workspace Structure
```
workspace/
  MEMORY.md
  TODO.md
  USER.md
  memory/
    reagents.md
    daily-notes.md
    archive/
  projects/
    compound-x/
    lab-protocols/
    genomics/
```

## Current Phase
Phase 2 — Lead Optimisation (updated 2024-01-15)

## Promoted Files
(none yet)

## Notes
- Compound-X trials ongoing
- Reagent list approved by QA on 2024-01-10
""")

write(WORKSPACE / "TODO.md", """\
# TODO

- [ ] Review Compound-X Phase 2 data
- [x] Archive old daily notes
- [ ] Update approved reagents list
- [x] Setup genomics pipeline — DONE 2024-01-05
""")

write(WORKSPACE / "USER.md", """\
# User Profile

Name: Dr. Elena Vasquez
Role: Principal Investigator
Focus: Compound-X lead optimisation, genomics QC
""")

# HOT file that should be demoted (zero references, old)
write(WORKSPACE / "OLD-PROTOCOLS.md", """\
# Old Protocols (Deprecated)

These protocols were superseded in 2023. No longer referenced.

## Buffer Prep v1
- Use 50mM Tris pH 7.4
- 150mM NaCl
""", days_old=45)

# ── WARM files ────────────────────────────────────────────────────────────────
# reagents.md — referenced by cron and local-overrides; should NOT be archived (pinned)
write(WORKSPACE / "memory/reagents.md", """\
# Reagents

## Approved Reagents
- DMSO (Sigma D2650)
- Tris-HCl pH 8.0
- Compound-X batch CX-2024-003
- EDTA 0.5M

## Pending Approval
- Novel excipient NE-7 (under review)
""")

# daily notes — old enough to archive
write(WORKSPACE / "memory/2024-01-05-notes.md", """\
# Daily Notes 2024-01-05

- Ran gel electrophoresis on samples A1-A8
- Results inconclusive, retry tomorrow
""", days_old=20)

write(WORKSPACE / "memory/2024-01-08-notes.md", """\
# Daily Notes 2024-01-08

- Compound-X IC50 measured: 12nM
- Protocol followed: projects/lab-protocols/approved-reagents.md
""", days_old=14)

write(WORKSPACE / "memory/2024-01-09-notes.md", """\
# Daily Notes 2024-01-09

- Team meeting: decided to advance to Phase 2
- See projects/compound-x/STATUS.md for updated status
""", days_old=13)

# recent daily note — should NOT be archived (< 7 days)
write(WORKSPACE / "memory/2024-01-15-notes.md", """\
# Daily Notes 2024-01-15

- QA sign-off on reagents received
- Compound-X Phase 2 kick-off
""", days_old=3)

# daily-notes.md referenced by cron — but it's a single file, not a daily pattern
write(WORKSPACE / "memory/daily-notes.md", """\
# Daily Notes Aggregate

Summary file for quick reference. See archive for individual days.
""")

# A WARM file eligible for PROMOTION: referenced by 3+ files, has ## Summary, recently modified
write(WORKSPACE / "memory/compound-x-summary.md", """\
# Compound-X Summary

## Summary
Compound-X is the lead candidate in our kinase inhibitor programme.
IC50: 12nM, selectivity index > 100.

## Status
Phase 2 trials initiated January 2024.
Target completion: Q3 2024.
""", days_old=2)

# ── Projects ──────────────────────────────────────────────────────────────────
# compound-x/STATUS.md — referenced by cron, local-overrides, daily notes
write(WORKSPACE / "projects/compound-x/STATUS.md", """\
# Compound-X Project Status

## Current Phase
Phase 2 — Lead Optimisation (updated 2024-01-15)

## Milestones
- [x] Phase 1 complete
- [ ] Phase 2 in-vivo studies
- [ ] Regulatory submission

## References
- See memory/compound-x-summary.md for full summary
- Protocols: projects/lab-protocols/approved-reagents.md
- Team notes: memory/2024-01-09-notes.md
""")

# lab-protocols/approved-reagents.md — referenced by cron, STATUS, daily notes
# DRIFT introduced: list differs from memory/reagents.md ## Approved Reagents
write(WORKSPACE / "projects/lab-protocols/approved-reagents.md", """\
# Approved Reagents

## Approved Reagents
- DMSO (Sigma D2650)
- Tris-HCl pH 8.0
- Compound-X batch CX-2024-003
- Phosphate Buffered Saline (PBS)

## Notes
Approved by QA 2024-01-10. Next review: 2024-04-10.
""")

# genomics/pipeline.md — referenced by cron-004 but DOES NOT EXIST (broken link)
# (intentionally not created)

# distractor files
write(WORKSPACE / "projects/genomics/README.md", """\
# Genomics Project

Pipeline under development. See pipeline.md for details.
""")

write(WORKSPACE / "projects/compound-x/assay-data.json", """\
{
  "compound": "Compound-X",
  "batch": "CX-2024-003",
  "assay": "kinase-inhibition",
  "IC50_nM": 12,
  "n_replicates": 3,
  "date": "2024-01-08",
  "analyst": "Dr. Vasquez",
  "protocol_ref": "projects/lab-protocols/approved-reagents.md"
}
""")

write(WORKSPACE / "projects/compound-x/experiment-log.md", """\
# Experiment Log

| Date       | Experiment         | Result   | Protocol |
|------------|--------------------|----------|---------|
| 2024-01-05 | Gel electrophoresis | Inconclusive | N/A |
| 2024-01-08 | IC50 assay          | 12nM     | projects/lab-protocols/approved-reagents.md |

See memory/compound-x-summary.md for summary.
See projects/compound-x/STATUS.md for phase status.
""")

write(WORKSPACE / "projects/lab-protocols/buffer-prep.md", """\
# Buffer Preparation Protocols

## Buffer A
- 50mM Tris pH 7.4
- 150mM NaCl

## References
- memory/reagents.md for approved reagents
- projects/compound-x/STATUS.md for current compound status
""")

write(WORKSPACE / "projects/lab-protocols/cell-viability.md", """\
# Cell Viability Assay

Standard MTT assay for IC50 determination.

## Reagents
See memory/reagents.md (Approved Reagents section).

## Protocol
1. Seed 5000 cells/well in 96-well plate
2. Add compound at 10 concentrations
3. Incubate 72h
4. Add MTT reagent, read at 570nm
""")

write(WORKSPACE / "memory/archive/2023-12-01-notes.md", """\
# Daily Notes 2023-12-01

- Initial screening of compound library
- 47 hits identified
""")

write(WORKSPACE / "memory/archive/2023-12-15-notes.md", """\
# Daily Notes 2023-12-15

- Counter-screening complete
- Compound-X shortlisted
""")

# An orphaned file — not referenced by anything
write(WORKSPACE / "memory/temp-calculations.md", """\
# Temp Calculations

Scratch work for dilution series. No longer needed.
Completed 2024-01-03.
""", days_old=15)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")