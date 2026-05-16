import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

NOTES_ROOT = Path("/home/node/.openclaw/workspace/notes")

# Create all required subdirectories
for subdir in ["ideas", "projects", "daily", "misc"]:
    (NOTES_ROOT / subdir).mkdir(parents=True, exist_ok=True)

# ── Helper ──────────────────────────────────────────────────────────────────
def write_note(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# ── Distractor notes (unrelated tags, varied content) ────────────────────────

# ideas/
write_note(NOTES_ROOT / "ideas" / "ml-pipeline-ideas.md", """\
---
tags: [machine-learning, pipeline, draft]
created: 2025-11-10
---

# ML Pipeline Ideas

- Use feature stores for real-time inference
- Explore ONNX for cross-framework export
""")

write_note(NOTES_ROOT / "ideas" / "cloud-cost-reduction.md", """\
---
tags: [cloud, cost, infra]
created: 2025-12-01
---

# Cloud Cost Reduction

Spot instances for batch jobs. Reserved capacity for prod.
""")

write_note(NOTES_ROOT / "ideas" / "team-offsite-agenda.md", """\
---
tags: [team, offsite, planning]
created: 2026-01-15
---

# Team Offsite Agenda

Morning: strategy session
Afternoon: lab tours
""")

# projects/
write_note(NOTES_ROOT / "projects" / "genome-sequencer-v2.md", """\
---
tags: [research, genomics, sequencing]
created: 2025-09-03
---

# Genome Sequencer v2

Upgraded flow cells. Throughput increased by 40%.

## Notes

- Requires new buffer solution B7
- Compatible with Illumina adapters only
""")

write_note(NOTES_ROOT / "projects" / "crispr-cas9-trial-1.md", """\
---
tags: [research, crispr, experiment]
created: 2025-10-14
---

# CRISPR-Cas9 Trial 1

Initial delivery via lipid nanoparticles. Efficiency: 61%.

## Observations

- Off-target edits detected in exon 7
- Temperature sensitivity noted at 37°C
""")

write_note(NOTES_ROOT / "projects" / "lab-equipment-inventory.md", """\
---
tags: [lab, equipment, admin]
created: 2025-11-20
---

# Lab Equipment Inventory

| Item | Count | Status |
|------|-------|--------|
| Centrifuge | 3 | Operational |
| PCR Machine | 2 | One under maintenance |
""")

write_note(NOTES_ROOT / "projects" / "pcr-optimization.md", """\
---
tags: [research, pcr, protocol]
created: 2025-12-09
---

# PCR Optimization

Annealing temp sweep: 52°C to 62°C. Best result at 58°C.

## Primer Design

- GC content: 50-60%
- Tm difference < 5°C between pairs
""")

# daily/
write_note(NOTES_ROOT / "daily" / "2026-01-10.md", """\
# 2026-01-10

- 09:15 — Reviewed sequencing data from last week
- 14:30 — Meeting with Dr. Chen about trial 2 setup
""")

write_note(NOTES_ROOT / "daily" / "2026-02-03.md", """\
# 2026-02-03

- 08:45 — Checked culture plates
- 11:00 — Submitted grant renewal documents
""")

write_note(NOTES_ROOT / "daily" / "2026-03-01.md", """\
# 2026-03-01

- 10:00 — CRISPR delivery efficiency results reviewed
- 15:45 — Ordered new reagents: catalog #LS-4421
""")

# misc/
write_note(NOTES_ROOT / "misc" / "conference-notes-ismb2025.md", """\
---
tags: [conference, bioinformatics, networking]
created: 2025-07-22
---

# ISMB 2025 Conference Notes

Key talks:
- Single-cell RNA-seq advances
- Protein structure prediction benchmarks

Contacts: Dr. Yuki Tanaka (yuki@biox.org)
""")

write_note(NOTES_ROOT / "misc" / "vendor-contacts.md", """\
---
tags: [admin, vendors, contacts]
created: 2025-08-05
---

# Vendor Contacts

- ThermoFisher rep: sales@thermofisher.example.com
- Sigma-Aldrich: reagents@sigma.example.com
""")

write_note(NOTES_ROOT / "misc" / "reading-list.md", """\
---
tags: [reading, papers, biology]
created: 2026-01-28
---

# Reading List

- [ ] "Base editing: precision chemistry on the genome" — Nature 2023
- [ ] "Cas12a nuclease improves HDR efficiency" — Cell 2024
- [x] "Off-target analysis via GUIDE-seq" — Genome Biol 2022
""")

print("Sandbox workspace generated successfully.")
print(f"Notes root: {NOTES_ROOT}")
print(f"Total notes created: {len(list(NOTES_ROOT.rglob('*.md')))}")