#!/usr/bin/env python3
"""
Generate the sandbox workspace for the legal-research memory indexing task.
"""
import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create the scripts directory with real, working implementations ──────

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# index-memory.py  ── builds a JSON cache of all memory files
index_script = scripts_dir / "index-memory.py"
index_script.write_text("""\
#!/usr/bin/env python3
\"\"\"Build/update an incremental keyword index for memory files.\"\"\"
import os, json, re, hashlib, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
CACHE_DIR = ROOT / "memory" / "cache"
CACHE_FILE = CACHE_DIR / "index.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load existing cache
if CACHE_FILE.exists():
    with open(CACHE_FILE) as f:
        cache = json.load(f)
else:
    cache = {}

# Collect all target files
targets = []
root_memory = ROOT / "MEMORY.md"
if root_memory.exists():
    targets.append(root_memory)
for p in sorted((ROOT / "memory").rglob("*.md")):
    if "cache" not in p.parts:
        targets.append(p)

updated = 0
for path in targets:
    rel = str(path.relative_to(ROOT))
    mtime = path.stat().st_mtime
    sig = hashlib.md5(f"{rel}:{mtime}".encode()).hexdigest()
    if cache.get(rel, {}).get("sig") == sig:
        continue
    text = path.read_text(errors="replace")
    words = re.findall(r"[a-zA-Z]+", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    cache[rel] = {
        "sig": sig,
        "mtime": mtime,
        "size": len(text),
        "freq": freq,
        "path": rel,
    }
    updated += 1

with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)

print(f"Index updated: {updated} file(s) processed, {len(cache)} total in cache.")
""")

# search-memory.py  ── searches the JSON cache with keyword scoring + recency boost
search_script = scripts_dir / "search-memory.py"
search_script.write_text("""\
#!/usr/bin/env python3
\"\"\"Search the memory index with keyword scoring and recency boost.\"\"\"
import sys, json, re, argparse, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE_FILE = ROOT / "memory" / "cache" / "index.json"

parser = argparse.ArgumentParser()
parser.add_argument("query", help="Search query string")
parser.add_argument("--top", type=int, default=10, help="Number of top results")
args = parser.parse_args()

if not CACHE_FILE.exists():
    print("Index not found. Run scripts/index-memory.py first.", file=sys.stderr)
    sys.exit(1)

with open(CACHE_FILE) as f:
    cache = json.load(f)

query_words = re.findall(r"[a-zA-Z]+", args.query.lower())
now = time.time()
DAY = 86400

results = []
for rel, entry in cache.items():
    freq = entry.get("freq", {})
    score = sum(freq.get(w, 0) for w in query_words)
    if score == 0:
        continue
    age_days = (now - entry["mtime"]) / DAY
    if age_days <= 30:
        boost = 1.5
    elif age_days <= 90:
        boost = 1.2
    else:
        boost = 1.0
    final_score = score * boost
    results.append((final_score, rel))

results.sort(key=lambda x: -x[0])
top = results[:args.top]

if not top:
    print("No results found.")
else:
    for rank, (sc, rel) in enumerate(top, 1):
        print(f"{rank}. [{sc:.2f}] {rel}")
""")

os.chmod(index_script, 0o755)
os.chmod(search_script, 0o755)

# ── 2. Create MEMORY.md (root level) ─────────────────────────────────────────

(WORKSPACE / "MEMORY.md").write_text("""\
# General Office Memory

- Firm founded 2009
- Main office: Chicago
- Practice areas: corporate litigation, IP, employment law
- Senior partner: Harriet Oluwole
- IT contact: sysadmin@lawfirm.internal
""")

# ── 3. Create memory/**/*.md files ───────────────────────────────────────────

memory_dir = WORKSPACE / "memory"
memory_dir.mkdir(exist_ok=True)

# Helper: write file and adjust mtime
def write_mem(rel_path, content, age_days):
    p = memory_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    mtime = (datetime.now() - timedelta(days=age_days)).timestamp()
    os.utime(p, (mtime, mtime))

# ── Subdir: cases/patent ─────────────────────────────────────────────────────
write_mem("cases/patent/techcorp_v_innovate.md", """\
# TechCorp v. Innovate LLC (2022)

Patent dispute over semiconductor manufacturing process.
Key claim: infringement of US Patent 9,876,543.
Prior art search revealed similar processes published in IEEE 2018.
Outcome: settled; licensing agreement reached.
Keywords: patent, infringement, semiconductor, prior art, licensing
""", age_days=200)

write_mem("cases/patent/biolab_v_genex.md", """\
# BioLab Inc. v. GenEx Corp (2021)

Biotechnology patent case involving CRISPR gene-editing claims.
Defendant argued obviousness based on Zhang lab publications.
Injunction denied; damages awarded $4.2M.
Keywords: patent, biotech, CRISPR, obviousness, injunction
""", age_days=350)

# ── Subdir: cases/employment ─────────────────────────────────────────────────
write_mem("cases/employment/harrison_v_retailco.md", """\
# Harrison v. RetailCo (2023)

Wrongful termination claim. Plaintiff alleged retaliation for whistleblowing.
Key evidence: internal Slack messages, HR audit log.
Settlement: $180,000 plus reinstatement offer.
Keywords: employment, wrongful termination, whistleblower, retaliation, settlement
""", age_days=15)   # RECENT – should get 1.5x recency boost

write_mem("cases/employment/doe_v_bankgroup.md", """\
# Doe v. BankGroup Financial (2020)

Class action discrimination case, Title VII.
Certified class of 340 employees.
Jury verdict: $12M punitive damages.
Keywords: employment, discrimination, class action, Title VII, punitive damages
""", age_days=500)

# ── Subdir: research/ip ───────────────────────────────────────────────────────
write_mem("research/ip/patent_strategy_notes.md", """\
# Patent Strategy Research Notes

Continuation applications can extend patent family lifecycle.
Inter partes review (IPR) increasingly used to challenge validity.
Post-grant review window: 9 months from grant.
Trade secret vs patent trade-off analysis needed for client XYZ.
Keywords: patent, IPR, continuation, trade secret, strategy
""", age_days=20)   # RECENT – recency boost 1.5x

write_mem("research/ip/trademark_overview.md", """\
# Trademark Law Overview

Distinctiveness spectrum: arbitrary, fanciful, suggestive, descriptive, generic.
Likelihood of confusion: DuPont factors.
Madrid Protocol for international trademark registration.
Keywords: trademark, distinctiveness, Madrid Protocol, DuPont
""", age_days=180)

# ── Subdir: research/contracts ────────────────────────────────────────────────
write_mem("research/contracts/force_majeure_analysis.md", """\
# Force Majeure Clause Analysis (COVID-19 Context)

Multiple clients invoked force majeure during 2020-2021.
Courts split on pandemic as qualifying event.
Recommended language: include epidemic/pandemic explicitly.
Keywords: contract, force majeure, pandemic, COVID, clause
""", age_days=400)

write_mem("research/contracts/indemnification_templates.md", """\
# Indemnification Clause Templates

Broad form vs limited form indemnification.
Anti-indemnity statutes vary by state.
Insurance requirements should mirror indemnity scope.
Keywords: contract, indemnification, insurance, clause, template
""", age_days=60)   # 60 days – recency boost 1.2x

# ── Subdir: clients ────────────────────────────────────────────────────────────
write_mem("clients/acme_corporation.md", """\
# Acme Corporation – Client Profile

Industry: Manufacturing
Open matters: 3 (2 patent, 1 employment)
Billing rate: $450/hr partner, $280/hr associate
Last contact: Q3 review meeting
Keywords: client, manufacturing, patent, employment, billing
""", age_days=30)   # exactly 30 days – still in boost window

write_mem("clients/northstar_ventures.md", """\
# NorthStar Ventures – Client Profile

Industry: Venture capital
Open matters: 1 (IP due diligence for Series B)
Preferred contact: Sarah Kim <skim@northstar.vc>
Keywords: client, venture capital, IP, due diligence, Series B
""", age_days=75)   # 75 days – 1.2x boost

write_mem("clients/globex_pharma.md", """\
# Globex Pharma – Client Profile

Industry: Pharmaceutical
Open matters: 2 (patent prosecution, regulatory compliance)
Note: NDA requires partner approval before disclosure.
Keywords: client, pharma, patent, NDA, regulatory
""", age_days=5)   # VERY RECENT – 1.5x boost

# ── Subdir: admin ──────────────────────────────────────────────────────────────
write_mem("admin/billing_procedures.md", """\
# Billing Procedures

Invoices generated on 15th of each month.
Contingency fee matters tracked separately in CaseManagePro.
Write-off approval required above $5,000.
Keywords: billing, invoice, contingency, write-off, admin
""", age_days=90)   # exactly 90 days – still in 1.2x window

write_mem("admin/court_deadlines_2024.md", """\
# Court Deadlines Tracker 2024

Matter 1024: Response due 2024-03-15 (patent)
Matter 1089: Discovery close 2024-04-01 (employment)
Matter 1102: Brief due 2024-05-10 (IP appeal)
Keywords: deadline, court, patent, employment, appeal
""", age_days=10)   # RECENT

# ── 4. Distractor files (non-.md, wrong dirs) ─────────────────────────────────

# JSON config distractor
(WORKSPACE / "config.json").write_text(json.dumps({
    "firm": "Hartwell & Associates",
    "version": "2.1.0",
    "features": ["billing", "search", "calendar"]
}, indent=2))

# CSV distractor
(WORKSPACE / "clients_export.csv").write_text(
    "id,name,industry\n1,Acme Corp,Manufacturing\n2,NorthStar,VC\n"
)

# Nested non-memory distractor
distractors_dir = WORKSPACE / "archive" / "old_notes"
distractors_dir.mkdir(parents=True, exist_ok=True)
(distractors_dir / "scratch.txt").write_text("Old scratch notes, not indexed.\npatent infringement notes 2019\n")
(distractors_dir / "todo.md").write_text("# TODO\n- Review TechCorp file\n- Call Acme\n")  # NOT under memory/ or MEMORY.md

# Another distractor
(WORKSPACE / "notes.txt").write_text("Random notes file, not part of memory system.\n")

# ── 5. Create SKILL.md ──────────────────────────────────────────────────────────
(WORKSPACE / "SKILL.md").write_text("""\
---
name: search-memory
description: Local-first memory search and indexing for Openclaw. Use when you need to (1) index memory files, (2) search memory from the CLI, or (3) wire a slash command for memory lookup.
---

# Search Memory

## Overview

Index local memory files and run fast keyword search with recency boost.

## Quick Start

1) Build/update index (incremental cache):
```bash
scripts/index-memory.py
```

2) Search the index:
```bash
scripts/search-memory.py "your query" --top 5
```

## Notes

- Index includes `MEMORY.md` plus `memory/**/*.md`.
- Cache lives under `memory/cache/`.
- Search uses keyword scoring + recency boost (last 30/90 days).
""")

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")