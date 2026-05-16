import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory scaffolding ──────────────────────────────────────────────────
dirs = [
    "deep-current",
    "deep-current-reports",
    "scripts",
    "biotech-intel/pipeline",
    "biotech-intel/regulatory",
    "biotech-intel/competitors",
    "biotech-intel/market",
    "internal-docs/strategy",
    "internal-docs/financials",
    "archive/2022",
    "archive/2023",
    "logs",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── copy the real CLI script from the cloned repo ─────────────────────────
import shutil
src = workspace / "deep-current-skill" / "scripts" / "deep-current.py"
dst = workspace / "scripts" / "deep-current.py"
if src.exists():
    shutil.copy(src, dst)

# ── distractor files ──────────────────────────────────────────────────────
distractor_files = {
    "biotech-intel/pipeline/phase3_tracker.csv": (
        "compound,sponsor,indication,phase,last_update\n"
        "BNT-221,BioNTech,NSCLC,Phase3,2024-01-10\n"
        "ARV-471,Arvinas,ER+BC,Phase3,2024-02-14\n"
        "Inavolisib,Genentech,PIK3CA,Phase3,2024-03-01\n"
    ),
    "biotech-intel/regulatory/fda_pdufa_dates.txt": (
        "2024-Q2 PDUFA dates:\n"
        "- Donanemab (Eli Lilly) Alzheimer's — Jun 2024\n"
        "- Pelacarsen (Novartis) — Aug 2024\n"
        "- Imetelstat (Geron) MDS — Jun 2024\n"
    ),
    "biotech-intel/competitors/competitor_map.json": json.dumps({
        "tier1": ["Moderna", "BioNTech", "Regeneron"],
        "tier2": ["Arvinas", "Relay Therapeutics", "Nurix"],
        "watch_list": ["Kymera", "C4 Therapeutics"]
    }, indent=2),
    "biotech-intel/market/addressable_markets.md": (
        "# TAM Estimates 2024\n"
        "- Oncology: $280B by 2030\n"
        "- Neurodegeneration: $95B by 2032\n"
        "- Rare Disease: $350B by 2031\n"
    ),
    "internal-docs/strategy/priorities_2024.md": (
        "# Strategic Priorities\n"
        "1. PROTAC competitive landscape\n"
        "2. ADC manufacturing capacity\n"
        "3. AI-driven target ID partnerships\n"
    ),
    "internal-docs/financials/q1_2024_burn.txt": (
        "Q1 2024 Research Spend: $4.2M\n"
        "Competitive Intel Budget: $180K\n"
        "Conference Travel: $42K\n"
    ),
    "archive/2022/old_targets.txt": "CDK4/6, KRAS G12C, TIGIT — deprioritized Q4 2022",
    "archive/2023/discontinued_threads.txt": (
        "Thread: TIGIT combination therapy — discontinued Jan 2023 (multiple trial failures)\n"
        "Thread: Sitravatinib — discontinued Mar 2023 (acquired)\n"
    ),
    "logs/session_2024-01-15.log": (
        "[INFO] Research session started\n"
        "[INFO] Fetched 12 sources\n"
        "[INFO] 3 threads updated\n"
        "[INFO] Session complete\n"
    ),
    "tmp/scratch_notes.txt": (
        "Look into: RAS(ON) inhibitors — Mirati data at AACR\n"
        "Follow up: Arvinas Q1 earnings call transcript\n"
        "Check: PROTAC patent landscape — WO2024-XXXX filings\n"
    ),
    "logs/cron_2024-02-01.log": (
        "[CRON] deep-current nightly job\n"
        "[CRON] Threads processed: 2\n"
        "[CRON] Report written: 2024-02-01.md\n"
    ),
    "biotech-intel/pipeline/protac_landscape.md": (
        "# PROTAC Pipeline Overview\n"
        "ARV-471 (Arvinas/Pfizer) — ER degrader, Phase 3\n"
        "ARV-766 (Arvinas) — AR degrader, Phase 2\n"
        "CC-94676 (BMS) — AR degrader, Phase 1\n"
        "NX-2127 (Nurix) — BTK/Ikaros degrader, Phase 1\n"
    ),
}

for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content)

# ── currents.json with pre-seeded threads (mix of stale and active) ────────
# Dates:
now = datetime.utcnow()
ninety_five_days_ago = (now - timedelta(days=95)).strftime("%Y-%m-%dT%H:%M:%SZ")
eighty_days_ago      = (now - timedelta(days=80)).strftime("%Y-%m-%dT%H:%M:%SZ")
thirty_days_ago      = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
five_days_ago        = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
two_days_ago         = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

currents = {
    "threads": [
        {
            "id": "protac-degrader-landscape",
            "title": "PROTAC Degrader Landscape",
            "status": "active",
            "created": ninety_five_days_ago,
            "updated": ninety_five_days_ago,
            "notes": [],
            "sources": [],
            "findings": []
        },
        {
            "id": "kras-g12d-inhibitors",
            "title": "KRAS G12D Inhibitors",
            "status": "active",
            "created": eighty_days_ago,
            "updated": eighty_days_ago,
            "notes": [
                {
                    "date": eighty_days_ago,
                    "text": "Initial survey of KRAS G12D covalent inhibitors — MRTX1133 lead compound"
                }
            ],
            "sources": [],
            "findings": []
        },
        {
            "id": "adc-manufacturing-bottlenecks",
            "title": "ADC Manufacturing Bottlenecks",
            "status": "active",
            "created": thirty_days_ago,
            "updated": thirty_days_ago,
            "notes": [],
            "sources": [
                {
                    "url": "https://www.fiercepharma.com/manufacturing/adc-capacity",
                    "desc": "Overview of ADC CMO capacity constraints",
                    "date": thirty_days_ago
                }
            ],
            "findings": []
        },
        {
            "id": "ai-drug-discovery-partnerships",
            "title": "AI Drug Discovery Partnerships",
            "status": "paused",
            "created": eighty_days_ago,
            "updated": eighty_days_ago,
            "notes": [],
            "sources": [],
            "findings": []
        },
        {
            "id": "donanemab-alzheimers-launch",
            "title": "Donanemab Alzheimers Launch",
            "status": "active",
            "created": five_days_ago,
            "updated": five_days_ago,
            "notes": [],
            "sources": [],
            "findings": []
        }
    ]
}

(workspace / "deep-current" / "currents.json").write_text(
    json.dumps(currents, indent=2)
)

# ── an OLD report already in deep-current-reports (from 16 days ago) ──────
old_report_date = (now - timedelta(days=16)).strftime("%Y-%m-%d")
old_report = f"""# Deep Current — {old_report_date}
## KRAS Wars: G12D Joins the Battlefront
New covalent inhibitor data from MRTX1133 trials shows promising response rates in pancreatic cancer.
See [MRTX1133 phase 1 results](https://www.nejm.org/doi/10.1056/NEJMoa2307002) and
[Mirati AACR poster](https://www.abstractsonline.com/pp8/mirati-kras).

## ADC Capacity Crunch Hits Mid-Size Biotechs
Lonza and Samsung Biologics are booked through 2026.
Sources: [FiercePharma ADC report](https://www.fiercepharma.com/manufacturing/adc-capacity),
[BioSpace CMO roundup](https://www.biospace.com/article/cmo-adc-capacity/).
"""
(workspace / "deep-current-reports" / f"{old_report_date}.md").write_text(old_report)

# ── a RECENT report (3 days ago) already in deep-current-reports ──────────
recent_report_date = (now - timedelta(days=3)).strftime("%Y-%m-%d")
recent_report = f"""# Deep Current — {recent_report_date}
## Donanemab's Rocky Road to Market
FDA advisory panel review scheduled for June 2024.
[Lilly press release](https://investor.lilly.com/donanemab-fda) and
[STAT News analysis](https://www.statnews.com/2024/donanemab-panel).

## AI Partnerships: Novo Nordisk Bets Big on Isomorphic
Deal valued at $1.2B with milestone payments tied to IND filings.
See [Reuters exclusive](https://www.reuters.com/novo-isomorphic-deal) and
[Isomorphic blog](https://www.isomorphiclabs.com/articles/novo-deal).
"""
(workspace / "deep-current-reports" / f"{recent_report_date}.md").write_text(recent_report)

print("Workspace initialized.")
print(f"Threads created: {len(currents['threads'])}")
print(f"Reports pre-populated: {old_report_date}, {recent_report_date}")
print(f"Stale thread (>90d, no recent notes): protac-degrader-landscape")
print(f"Active threads with recent activity: kras-g12d-inhibitors, adc-manufacturing-bottlenecks, donanemab-alzheimers-launch")