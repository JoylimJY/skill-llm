import json
import os
import random
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "data", "output", "logs", "config", "archive",
    "src/pipeline", "src/analysis", "reports/q1", "reports/q2",
    "team/contacts", "team/onboarding", "protocols/sop",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractors = {
    "config/app_settings.yaml": "environment: production\ndebug: false\nretries: 3\n",
    "config/db_config.json": json.dumps({"host": "localhost", "port": 5432, "db": "labdb"}),
    "logs/pipeline_run_2024.log": "INFO 2024-01-10 Pipeline started\nERROR 2024-01-10 Sample batch 7 failed\nINFO 2024-01-10 Retry succeeded\n",
    "logs/analysis_errors.log": "WARNING: Outlier detected in plate B3\nERROR: Missing control sample\n",
    "src/pipeline/preprocess.py": "def preprocess(data):\n    return data.strip()\n",
    "src/pipeline/validate.py": "def validate(record):\n    return record is not None\n",
    "src/analysis/stats.py": "import math\ndef mean(xs): return sum(xs)/len(xs)\n",
    "src/analysis/plot.py": "# placeholder for matplotlib plots\n",
    "reports/q1/summary.csv": "sample_id,result,pass\nS001,0.82,yes\nS002,0.45,no\nS003,0.91,yes\n",
    "reports/q2/summary.csv": "sample_id,result,pass\nS101,0.77,yes\nS102,0.55,yes\n",
    "team/contacts/researchers.csv": "name,email\nAlice Novak,anovak@lab.example\nBen Osei,bosei@lab.example\n",
    "team/onboarding/checklist.txt": "1. Read SOP documents\n2. Set up VPN\n3. Request lab access\n",
    "protocols/sop/centrifuge_protocol.txt": "Spin at 3000rpm for 10min at 4C\n",
    "archive/old_notes.txt": "These notes are deprecated. See new system.\n",
}
for rel, content in distractors.items():
    (workspace / rel).write_text(content)

# ── pre-seed the palace JSON ──────────────────────────────────────────────
# We build a palace that looks like it was initialized by loci init,
# then partially populated. Some memories are OLD (200 days ago) → low weight.
# Some are FRESH (today) → high weight.

now_utc = datetime.now(timezone.utc)

def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def decayed_weight(base, days, rate=0.05):
    return base * math.exp(-rate * days)

old_date = now_utc - timedelta(days=200)
fresh_date = now_utc

# IDs that will be referenced in task
STALE_ID_1 = "aabbcc11"
STALE_ID_2 = "aabbcc22"
STALE_ID_3 = "aabbcc33"
FRESH_ID_1  = "ddee1122"
FRESH_ID_2  = "ddee3344"

palace = {
    "version": "1.0",
    "created": iso(now_utc - timedelta(days=365)),
    "lastWalk": iso(now_utc - timedelta(days=30)),
    "config": {
        "defaultDecayRate": 0.05,
        "domains": {
            "work": {"capacity": 50, "description": "Work-related memories"},
            "knowledge": {"capacity": 100, "description": "Facts and learnings"},
            "people": {"capacity": 30, "description": "People and relationships"},
            "tools": {"capacity": 40, "description": "Tools and configurations"},
            "preferences": {"capacity": 20, "description": "User preferences"},
            "archive": {"capacity": 200, "description": "Long-term storage"}
        }
    },
    "memories": {
        STALE_ID_1: {
            "id": STALE_ID_1,
            "domain": "work",
            "content": "Q3 2023: decided to use legacy HPLC method for compound separation",
            "tags": ["hplc", "legacy", "q3-2023"],
            "links": [],
            "baseWeight": 1.0,
            "weight": round(decayed_weight(1.0, 200), 8),
            "created": iso(old_date),
            "lastAccessed": iso(old_date),
            "accessCount": 1
        },
        STALE_ID_2: {
            "id": STALE_ID_2,
            "domain": "knowledge",
            "content": "Plate reader calibration offset was +0.03 AU in batch 5 — now corrected",
            "tags": ["calibration", "plate-reader", "batch-5"],
            "links": [],
            "baseWeight": 1.0,
            "weight": round(decayed_weight(1.0, 200), 8),
            "created": iso(old_date),
            "lastAccessed": iso(old_date),
            "accessCount": 2
        },
        STALE_ID_3: {
            "id": STALE_ID_3,
            "domain": "tools",
            "content": "Old Jenkins CI at ci-legacy.lab.internal — decommissioned",
            "tags": ["ci", "jenkins", "decommissioned"],
            "links": [],
            "baseWeight": 0.8,
            "weight": round(decayed_weight(0.8, 200), 8),
            "created": iso(old_date),
            "lastAccessed": iso(old_date),
            "accessCount": 1
        },
        FRESH_ID_1: {
            "id": FRESH_ID_1,
            "domain": "work",
            "content": "Project Helix milestone 2 approved — targeting Q2 2025 delivery",
            "tags": ["helix", "milestone", "q2-2025"],
            "links": [],
            "baseWeight": 1.0,
            "weight": 1.0,
            "created": iso(fresh_date),
            "lastAccessed": iso(fresh_date),
            "accessCount": 1
        },
        FRESH_ID_2: {
            "id": FRESH_ID_2,
            "domain": "people",
            "content": "Dr. Elena Vasquez joined as lead bioinformatician, contact: evasquez@lab.example",
            "tags": ["team", "bioinformatics", "contact"],
            "links": [],
            "baseWeight": 1.0,
            "weight": 1.0,
            "created": iso(fresh_date),
            "lastAccessed": iso(fresh_date),
            "accessCount": 1
        }
    }
}

palace_path = workspace / "data" / "lab_palace.json"
palace_path.write_text(json.dumps(palace, indent=2))

# ── task instruction file (business context only, no hints) ──────────────
task_file = workspace / "TASK_BRIEF.txt"
task_file.write_text(
    "Lab Knowledge Consolidation Task\n"
    "=================================\n"
    "Palace file: /workspace/data/lab_palace.json\n"
    "Output directory: /workspace/output/\n"
    "\n"
    "See task prompt for full requirements.\n"
)

print("Workspace seeded successfully.")
print(f"Palace file: {palace_path}")
print(f"Stale IDs (expect pruned): {STALE_ID_1}, {STALE_ID_2}, {STALE_ID_3}")
print(f"Fresh IDs (expect kept):   {FRESH_ID_1}, {FRESH_ID_2}")