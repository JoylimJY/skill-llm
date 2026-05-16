#!/usr/bin/env python3
"""
Generate a realistic, messy memory workspace for a biotech research team.
Simulates months of accumulated notes: bloated MEMORY.md, orphan files,
recursive nesting, stale completed tasks, and duplicate information.
"""

import os
import random
from datetime import datetime, timedelta, date

random.seed(42)

WORKSPACE = "/workspace"

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

today = date.today()
today_str = today.strftime("%Y-%m-%d")

# ── MEMORY.md — bloated, 300+ lines, covers way too many topics ─────────────
memory_md_lines = []
memory_md_lines.append("# Long-Term Memory\n")
memory_md_lines.append(f"_Last updated: {today_str}_\n\n")

memory_md_lines.append("## Key People\n")
memory_md_lines.append("- **Dr. Elena Vasquez** — Lead Scientist, CRISPR-editing expert, prefers async Slack\n")
memory_md_lines.append("- **Marcus Tren** — Bioinformatics lead, Python/R, runs weekly data syncs Mondays\n")
memory_md_lines.append("- **Priya Nair** — Lab manager, orders reagents, contact for equipment issues\n")
memory_md_lines.append("- **Tom Breck** — CTO, attends monthly project reviews, values concise summaries\n")
memory_md_lines.append("- **Sophie Lund** — External collaborator, Uppsala University, genomics specialist\n")
memory_md_lines.append("- **Raj Patel** — IP lawyer, patent filings, responds best via email\n")
memory_md_lines.append("- **Amy Chen** — Lab tech, assists with PCR and gel electrophoresis\n")
memory_md_lines.append("- **Carlos Vega** — Data engineer, manages the HPC cluster\n\n")

memory_md_lines.append("## Active Projects\n")
memory_md_lines.append("### Project Helix — Gene Therapy Candidate GX-7\n")
memory_md_lines.append("- Status: Phase 2 pre-clinical trials in progress\n")
memory_md_lines.append("- Lead: Dr. Vasquez\n")
memory_md_lines.append("- Key milestone: Submit IND amendment by Q3\n")
memory_md_lines.append("- Latest result: 73% knockout efficiency in HEK293 cells (run 2024-11-15)\n")
memory_md_lines.append("- Blocker: Delivery vector optimization pending vendor feedback (VectorCo)\n\n")
memory_md_lines.append("### Project Strand — Microbiome Diagnostic Panel\n")
memory_md_lines.append("- Status: Data analysis phase\n")
memory_md_lines.append("- Lead: Marcus Tren\n")
memory_md_lines.append("- 16S rRNA sequencing complete for cohort A (n=120)\n")
memory_md_lines.append("- Cohort B enrollment ongoing, target n=200\n")
memory_md_lines.append("- Key risk: Low diversity in control samples may skew results\n\n")
memory_md_lines.append("### Project Aurora — Protein Folding ML Model\n")
memory_md_lines.append("- Status: Model v2 training on HPC cluster\n")
memory_md_lines.append("- Lead: Carlos Vega + Sophie Lund (collaborative)\n")
memory_md_lines.append("- Training data: 14k validated structures from PDB\n")
memory_md_lines.append("- Current bottleneck: GPU quota on cluster, waiting for node allocation\n\n")

memory_md_lines.append("## Protocols & SOPs\n")
memory_md_lines.append("### CRISPR Knockout Protocol v3.2\n")
memory_md_lines.append("- Buffer: NEBuffer 3.1 at 37°C, 60 min incubation\n")
memory_md_lines.append("- gRNA design: Benchling, targeting exon 4\n")
memory_md_lines.append("- Cas9 source: NEB #M0386S\n")
memory_md_lines.append("- Electroporation: Neon system, 1400V / 10ms / 3 pulses\n")
memory_md_lines.append("- Validation: T7E1 assay + Sanger sequencing\n\n")
memory_md_lines.append("### Cell Culture Maintenance\n")
memory_md_lines.append("- HEK293T: DMEM + 10% FBS, passage every 3 days\n")
memory_md_lines.append("- iPSC line iPX-4: mTeSR1, Matrigel-coated, passage weekly\n")
memory_md_lines.append("- Cryopreservation: 90% FBS + 10% DMSO, slow-freeze protocol\n\n")
memory_md_lines.append("### DNA Extraction (Tissue)\n")
memory_md_lines.append("- Kit: Qiagen DNeasy Blood & Tissue\n")
memory_md_lines.append("- Lysis buffer: ATL + Proteinase K at 56°C overnight\n")
memory_md_lines.append("- Elution: 2x 100µL AE buffer\n\n")

memory_md_lines.append("## Equipment & Resources\n")
memory_md_lines.append("- **PCR machines**: 3x Bio-Rad T100, 1x QuantStudio 6 (qPCR)\n")
memory_md_lines.append("- **Sequencing**: Illumina MiSeq (in-house), NovaSeq (send-out to GenCore)\n")
memory_md_lines.append("- **Flow cytometer**: BD FACSCanto II — book via LIMS at least 48hr ahead\n")
memory_md_lines.append("- **HPC cluster**: 64-node, SLURM scheduler, contact Carlos for allocation\n")
memory_md_lines.append("- **-80°C freezers**: 4 units, Box mapping in Quartzy. Freezer 3 compressor flagged for maintenance (reported 2023-08-10) — RESOLVED\n")
memory_md_lines.append("- **Liquid nitrogen**: Dewar refill every 2 weeks, Priya schedules\n")
memory_md_lines.append("- **Confocal**: Zeiss LSM 980, shared facility, core lab booking only\n\n")

memory_md_lines.append("## Vendor & Supplier Notes\n")
memory_md_lines.append("- **NEB**: Standard reagents, 2-day shipping, account #NEBxxx-biolab\n")
memory_md_lines.append("- **Thermo Fisher**: Primary plastics/consumables, net-30 terms\n")
memory_md_lines.append("- **VectorCo**: AAV vector production, 8-12 week lead time, contact: jsmith@vectorco.com\n")
memory_md_lines.append("- **GenCore**: Sequencing core, turnaround 5-7 days, use FTP for data pickup\n")
memory_md_lines.append("- **Benchling**: ELN subscription, 25 seats, renewal due 2025-01-15\n")
memory_md_lines.append("- **IDT**: Oligo synthesis, next-day for standard, 5-day for modified\n")
memory_md_lines.append("- **Sigma-Aldrich**: Chemicals, bulk orders via procurement form\n\n")

memory_md_lines.append("## Regulatory & Compliance\n")
memory_md_lines.append("- IBC approval: Protocol #IBC-2024-07 active, renewal due 2025-07-01\n")
memory_md_lines.append("- BSL-2 waste: Autoclave before disposal, log in safety binder\n")
memory_md_lines.append("- IACUC: No animal studies currently\n")
memory_md_lines.append("- Data: All human subject data in HIPAA-compliant server (/data/protected/)\n")
memory_md_lines.append("- Export control: Check with Raj before sharing IP with Sophie (Uppsala)\n\n")

memory_md_lines.append("## IT & Infrastructure\n")
memory_md_lines.append("- VPN: GlobalProtect, auto-connects on campus wifi\n")
memory_md_lines.append("- GitHub org: github.com/helix-biolab (private repos)\n")
memory_md_lines.append("- Slack workspace: helix-labs.slack.com\n")
memory_md_lines.append("- LIMS: LabArchives, all experiments must be logged within 24h\n")
memory_md_lines.append("- Backup: Nightly to /backup/, weekly off-site via Backblaze\n")
memory_md_lines.append("- 2FA: Mandatory for all accounts since 2024-03-01\n\n")

memory_md_lines.append("## Meeting Cadence\n")
memory_md_lines.append("- Monday 9am: Data sync (Marcus leads, bioinformatics team)\n")
memory_md_lines.append("- Tuesday 2pm: Project Helix standup (Dr. Vasquez)\n")
memory_md_lines.append("- Wednesday 11am: All-hands lab meeting\n")
memory_md_lines.append("- Monthly (last Thursday): CTO review with Tom Breck\n")
memory_md_lines.append("- Quarterly: External collaborator update (Sophie Lund)\n\n")

memory_md_lines.append("## Financial & Budget\n")
memory_md_lines.append("- Q4 2024 reagent budget: $85,000 remaining\n")
memory_md_lines.append("- Capital equipment freeze until Q1 2025\n")
memory_md_lines.append("- Grant: NIH R01 GM-334521, $450k/yr, ends 2026-09-30\n")
memory_md_lines.append("- Discretionary: Dr. Vasquez has $10k PI discretionary fund\n\n")

memory_md_lines.append("## Competitive Landscape\n")
memory_md_lines.append("- **GenThera Inc**: GX-9 candidate similar to ours, Phase 1 trial started Oct 2024\n")
memory_md_lines.append("- **Meridian Bio**: Strong microbiome diagnostics play, well-funded ($50M Series B)\n")
memory_md_lines.append("- **AlphaFold variants**: Multiple groups adapting for therapeutic design — watch Aurora project differentiation\n")
memory_md_lines.append("- Key advantage: Our delivery vector approach is proprietary (patent pending, Raj handling)\n\n")

memory_md_lines.append("## Key Decisions Log\n")
memory_md_lines.append("- 2024-09-15: Chose AAV9 over LNP delivery for GX-7 (better CNS penetration data)\n")
memory_md_lines.append("- 2024-08-01: Switched from 10X Genomics to in-house 16S for cost reasons\n")
memory_md_lines.append("- 2024-06-20: Dropped Project Iris (insufficient efficacy signal at IC50)\n")
memory_md_lines.append("- 2024-04-10: Hired Marcus Tren over external contractor (long-term capability building)\n\n")

memory_md_lines.append("## Known Issues & Blockers\n")
memory_md_lines.append("- VectorCo delivery delayed — expected Q1 2025 now\n")
memory_md_lines.append("- Freezer 3 compressor issue — RESOLVED 2023-09-15\n")
memory_md_lines.append("- Cohort B enrollment slower than projected (target was Oct 2024)\n")
memory_md_lines.append("- HPC node allocation: Carlos escalated to IT, awaiting resolution\n\n")

memory_md_lines.append("## Onboarding Notes\n")
memory_md_lines.append("- New hires must complete biosafety training (online, 2hr)\n")
memory_md_lines.append("- Badge access: Email facilities@helix.bio with PI approval\n")
memory_md_lines.append("- ELN access: IT tickets via help@helix.bio\n")
memory_md_lines.append("- Mentor assignment: First 2 weeks shadowing assigned mentor\n\n")

# Pad to ensure >300 lines
for i in range(50):
    memory_md_lines.append(f"<!-- padding line {i} -->\n")

memory_md_content = "".join(memory_md_lines)
write_file(f"{WORKSPACE}/MEMORY.md", memory_md_content)
print(f"MEMORY.md: {len(memory_md_lines)} lines")

# ── Daily notes: preserve these — YYYY-MM-DD.md ─────────────────────────────
past_dates = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in [3, 7, 14, 21, 30, 45]]
for d in past_dates:
    content = f"# {d}\n\n## Lab Notes\n- Routine experiments, no major issues.\n- Checked on Project Helix cultures.\n\n## TODOs\n- Review sequencing results from GenCore\n"
    write_file(f"{WORKSPACE}/memory/{d}.md", content)

# ── TODAY's daily note (already exists, agent should append to it) ───────────
today_daily_content = f"# {today_str}\n\n## Morning Check\n- Project Strand data analysis continuing.\n- Marcus running pipeline on cohort A samples.\n\n"
write_file(f"{WORKSPACE}/memory/{today_str}.md", today_daily_content)

# ── Tasks directory: mix of active, recently-done, stale-done ───────────────
# Task 1: Active
write_file(f"{WORKSPACE}/memory/tasks/optimize-delivery-vector.md",
"""# Task: Optimize Delivery Vector
status: active
created: """ + (today - timedelta(days=5)).strftime("%Y-%m-%d") + """
assigned: Dr. Vasquez

## Description
Evaluate AAV9 vs AAV-PHP.B for CNS delivery efficiency in GX-7 construct.

## Steps
- [ ] Run side-by-side transduction assay
- [ ] Analyze tropism data
- [ ] Report to Tom Breck
""")

# Task 2: Active
write_file(f"{WORKSPACE}/memory/tasks/enroll-cohort-b.md",
"""# Task: Enroll Cohort B
status: active
created: """ + (today - timedelta(days=20)).strftime("%Y-%m-%d") + """
assigned: Priya Nair

## Description
Complete enrollment for microbiome study cohort B. Target n=200.

## Steps
- [ ] Contact referring physicians
- [ ] Screen 40 additional candidates
- [x] IRB amendment approved
""")

# Task 3: Done, OLD (>14 days ago) — SHOULD BE PRUNED
done_old_date = (today - timedelta(days=20)).strftime("%Y-%m-%d")
write_file(f"{WORKSPACE}/memory/tasks/setup-hpc-account.md",
f"""# Task: Setup HPC Account for New Hire
status: done
created: {(today - timedelta(days=35)).strftime("%Y-%m-%d")}
completed: {done_old_date}
assigned: Carlos Vega

## Description
Create SLURM account for Amy Chen on the HPC cluster.

## Result
Done. Amy can now submit jobs.
""")

# Task 4: Done, OLD (>14 days) — SHOULD BE PRUNED
done_old_date2 = (today - timedelta(days=18)).strftime("%Y-%m-%d")
write_file(f"{WORKSPACE}/memory/tasks/benchling-renewal.md",
f"""# Task: Renew Benchling License
status: done
created: {(today - timedelta(days=40)).strftime("%Y-%m-%d")}
completed: {done_old_date2}
assigned: Priya Nair

## Description
Renew annual Benchling ELN subscription before expiry on 2024-01-15.

## Result
Renewed. 25 seats confirmed, billing updated.
""")

# Task 5: Done, RECENT (<14 days) — should NOT be pruned
done_recent_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
write_file(f"{WORKSPACE}/memory/tasks/order-neb-reagents.md",
f"""# Task: Order NEB Reagents for Q4
status: done
created: {(today - timedelta(days=10)).strftime("%Y-%m-%d")}
completed: {done_recent_date}
assigned: Priya Nair

## Description
Place Q4 reagent order: Cas9 (M0386S x10), T4 Ligase x5, buffer sets.

## Result
Order placed, PO#4421, expected delivery in 2 days.
""")

# Task 6: Done, RECENT (<14 days) — should NOT be pruned
done_recent_date2 = (today - timedelta(days=3)).strftime("%Y-%m-%d")
write_file(f"{WORKSPACE}/memory/tasks/fix-QuantStudio-calibration.md",
f"""# Task: Fix QuantStudio 6 Calibration
status: done
created: {(today - timedelta(days=8)).strftime("%Y-%m-%d")}
completed: {done_recent_date2}
assigned: Amy Chen

## Description
Recalibrate QuantStudio 6 after failed ROX reference check.

## Result
Calibration complete. ROX signal normal. Logged in LIMS.
""")

# ── Orphan / poorly-named files ──────────────────────────────────────────────
write_file(f"{WORKSPACE}/memory/notes-2.md",
"""# Notes
- GenThera Inc running GX-9 Phase 1 trials starting Oct 2024
- Meridian Bio raised $50M Series B for microbiome diagnostics
- AlphaFold variants being adapted by multiple groups
- Our AAV delivery vector is proprietary — key differentiator
- Watch patent application progress with Raj
""")

write_file(f"{WORKSPACE}/memory/bm-marketing-ideas.md",
"""# BM Marketing Ideas
- Present Aurora model at ASHG 2025 as thought leadership
- White paper on AAV9 delivery efficiency advantages
- Target rare disease patient advocacy groups for GX-7 awareness
- LinkedIn posts on microbiome diagnostics advances
- Conference: ASGCT May 2025 — submit abstract for Helix project
""")

# ── Duplicate information: people info scattered ─────────────────────────────
write_file(f"{WORKSPACE}/memory/team-contacts.md",
"""# Team Contacts
- Elena Vasquez: evasquez@helix.bio, ext 201
- Marcus Tren: mtren@helix.bio, ext 215
- Priya Nair: pnair@helix.bio, ext 207
- Tom Breck: tbreck@helix.bio (CTO)
- Amy Chen: achen@helix.bio, ext 230
- Carlos Vega: cvega@helix.bio, ext 218
- Sophie Lund: sophie.lund@uu.se (external)
- Raj Patel: raj.patel@patentfirm.com (external)
""")

# ── Recursive nesting bug artifact ───────────────────────────────────────────
os.makedirs(f"{WORKSPACE}/memory/memory/memory", exist_ok=True)
write_file(f"{WORKSPACE}/memory/memory/memory/stray-note.md",
"""# Stray Note
This file ended up here due to an indexer bug. Should not exist.
- Some random project note that duplicates info elsewhere
""")
write_file(f"{WORKSPACE}/memory/memory/memory/another-stray.md",
"""# Another Stray
More orphaned content from the recursive nesting bug.
""")

# ── Additional distractor files (realistic lab notes, not problematic) ───────
write_file(f"{WORKSPACE}/memory/protocol-crispr.md",
"""# CRISPR Protocol Notes
Detailed bench notes for CRISPR knockout runs.
- Run 2024-11-15: 73% knockout HEK293, conditions as per SOP v3.2
- Run 2024-11-08: 61% knockout, suboptimal - gRNA concentration too low
- Run 2024-10-29: 68% knockout, standard conditions
""")

write_file(f"{WORKSPACE}/memory/sequencing-log.md",
"""# Sequencing Log
Tracking all sequencing submissions to GenCore.

| Date | Sample | Type | Status |
|------|--------|------|--------|
| 2024-11-10 | GX7-batch3 | Sanger | Returned |
| 2024-11-01 | Cohort-A-16S | MiSeq | Returned |
| 2024-10-15 | iPX4-genome | WGS | Returned |
""")

write_file(f"{WORKSPACE}/memory/aurora-ml-notes.md",
"""# Aurora ML Model Notes
- Architecture: Transformer-based, 180M params
- Training set: 14k PDB structures, filtered at 30% sequence identity
- Val loss: 0.342 (v1), 0.287 (v2 in training)
- Sophie Lund contributing 2k additional structures from Uppsala
- Target: Beat AlphaFold2 on rare disease target structures
""")

write_file(f"{WORKSPACE}/memory/strand-analysis.md",
"""# Project Strand Analysis Notes
- 16S rRNA V4 region amplification
- QIIME2 pipeline, SILVA 138 classifier
- Alpha diversity (Shannon): cohort A mean 3.42, std 0.71
- Beta diversity: PERMANOVA p<0.01 between case/control
- Key taxa enriched in cases: Prevotella, Fusobacterium
""")

# ── Root-level distractor files ───────────────────────────────────────────────
write_file(f"{WORKSPACE}/lab-calendar.md",
"""# Lab Calendar
## November 2024
- Nov 18: All-hands meeting, Q4 review
- Nov 25: CTO review with Tom Breck
- Nov 28: Thanksgiving — lab closed
## December 2024
- Dec 5: IBC annual review
- Dec 20: Lab holiday party
""")

write_file(f"{WORKSPACE}/procurement.md",
"""# Procurement Tracker
| Item | Vendor | PO# | Status |
|------|--------|-----|--------|
| Cas9 M0386S x10 | NEB | PO4421 | Ordered |
| T4 Ligase x5 | NEB | PO4421 | Ordered |
| Matrigel 10ml | Corning | PO4398 | Delivered |
""")

# Print summary
total_files = 0
for root, dirs, files in os.walk(WORKSPACE):
    for f in files:
        total_files += 1
        print(f"  {os.path.join(root, f)}")
print(f"\nTotal files created: {total_files}")
print(f"Today's date: {today_str}")