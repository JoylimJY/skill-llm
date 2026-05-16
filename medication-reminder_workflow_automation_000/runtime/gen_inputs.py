import os
import stat
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# Create a realistic deeply-nested directory structure with distractor files
distractor_dirs = [
    "scripts",
    "patient_records/jordan",
    "patient_records/alex",
    "patient_records/archive/2023",
    "patient_records/archive/2022",
    "clinical_notes/week1",
    "clinical_notes/week2",
    "admin/billing",
    "admin/insurance",
    "logs/system",
    "logs/audit",
    "config/profiles",
    "config/backups",
    "exports/csv",
    "exports/pdf_queue",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files that look plausible but are irrelevant noise
distractors = {
    "patient_records/jordan/intake_log.txt": (
        "2024-01-10: Metformin 500mg - NOT YET LOGGED\n"
        "2024-01-11: Lisinopril 10mg - NOT YET LOGGED\n"
        "This is a manual note, not the system record.\n"
    ),
    "patient_records/jordan/profile.json": json.dumps({
        "name": "Jordan",
        "dob": "1978-03-15",
        "conditions": ["Type 2 Diabetes", "Hypertension"],
        "medications_prescribed": [
            {"name": "metformin", "dose": "500mg", "frequency": "twice-daily"},
            {"name": "lisinopril", "dose": "10mg", "frequency": "once-daily"},
            {"name": "aspirin", "dose": "81mg", "frequency": "once-daily"},
        ]
    }, indent=2),
    "patient_records/alex/profile.json": json.dumps({
        "name": "Alex",
        "dob": "1990-07-22",
        "conditions": ["Asthma"],
        "medications_prescribed": [
            {"name": "albuterol", "dose": "90mcg", "frequency": "as-needed"}
        ]
    }, indent=2),
    "patient_records/archive/2023/summary.txt": "Annual medication review 2023. Archived.",
    "patient_records/archive/2022/summary.txt": "Annual medication review 2022. Archived.",
    "clinical_notes/week1/notes.txt": "Jordan responded well to metformin. Continue current dosage.",
    "clinical_notes/week2/notes.txt": "Blood pressure stable on lisinopril 10mg.",
    "admin/billing/invoice_jan.txt": "Invoice #1042 - Medication management service - $120.00",
    "admin/insurance/coverage.json": json.dumps({"provider": "BlueCross", "plan": "Gold", "copay": 20}),
    "logs/system/startup.log": "System initialized at 2024-01-01 08:00:00\nAll services nominal.",
    "logs/audit/access.log": "2024-01-10 09:00: admin accessed patient records\n2024-01-10 09:05: admin updated medication list",
    "config/profiles/default.json": json.dumps({"theme": "clinical", "language": "en", "timezone": "UTC"}),
    "config/backups/last_backup.txt": "Last backup: 2024-01-09 23:00 UTC\nStatus: SUCCESS",
    "exports/csv/medications_export_old.csv": "name,dose,frequency\nmetformin,1000mg,once-daily\n",
    "exports/pdf_queue/pending.txt": "No PDFs queued.",
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# The actual tool script lives at scripts/script.sh
# Per rules, we do NOT create it here — it already exists on the system.
# However we do create a SKILL.md reference file so the agent can read documentation.
skill_md = workspace / "SKILL.md"
skill_md.write_text("""\
---
name: "medication-reminder"
version: "3.0.0"
description: "Track medications with dosing schedules and intake history. Use when managing prescriptions."
author: "BytesAgain"
homepage: "https://bytesagain.com"
---

# medication-reminder

Track medications with dosing schedules and intake history. Use when managing prescriptions.

## Commands

### `add`

```bash
scripts/script.sh add <med dose frequency>
```

### `list`

```bash
scripts/script.sh list
```

### `take`

```bash
scripts/script.sh take <med>
```

### `history`

```bash
scripts/script.sh history <days>
```

### `schedule`

```bash
scripts/script.sh schedule
```

### `due`

```bash
scripts/script.sh due
```

## Data Storage

Data stored in `~/.local/share/medication-reminder/`.

---

*Powered by BytesAgain | bytesagain.com | hello@bytesagain.com*
""")

# Create the actual scripts/script.sh — this IS the tool implementation
# The skill says scripts already exist; we implement it faithfully here
script_content = r"""#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="$HOME/.local/share/medication-reminder"
MEDS_FILE="$DATA_DIR/medications.json"
HIST_FILE="$DATA_DIR/history.json"

mkdir -p "$DATA_DIR"

# Initialize files if missing
[[ -f "$MEDS_FILE" ]] || echo '[]' > "$MEDS_FILE"
[[ -f "$HIST_FILE" ]] || echo '[]' > "$HIST_FILE"

CMD="${1:-}"
shift || true

case "$CMD" in
  add)
    MED="$1"
    DOSE="$2"
    FREQ="$3"
    EXISTING=$(jq --arg m "$MED" 'map(select(.name == $m)) | length' "$MEDS_FILE")
    if [[ "$EXISTING" -gt 0 ]]; then
      echo "Medication '$MED' already exists."
      exit 1
    fi
    jq --arg m "$MED" --arg d "$DOSE" --arg f "$FREQ" \
      '. += [{"name": $m, "dose": $d, "frequency": $f, "added": (now | todate)}]' \
      "$MEDS_FILE" > "$MEDS_FILE.tmp" && mv "$MEDS_FILE.tmp" "$MEDS_FILE"
    echo "Added $MED ($DOSE, $FREQ)"
    ;;
  list)
    jq -r '.[] | "\(.name) - \(.dose) - \(.frequency)"' "$MEDS_FILE"
    ;;
  take)
    MED="$1"
    EXISTS=$(jq --arg m "$MED" 'map(select(.name == $m)) | length' "$MEDS_FILE")
    if [[ "$EXISTS" -eq 0 ]]; then
      echo "Medication '$MED' not found."
      exit 1
    fi
    jq --arg m "$MED" \
      '. += [{"name": $m, "taken_at": (now | todate)}]' \
      "$HIST_FILE" > "$HIST_FILE.tmp" && mv "$HIST_FILE.tmp" "$HIST_FILE"
    echo "Recorded intake of $MED"
    ;;
  history)
    DAYS="${1:-7}"
    CUTOFF=$(date -d "$DAYS days ago" +%s 2>/dev/null || date -v-"${DAYS}d" +%s)
    jq --argjson c "$CUTOFF" \
      '[.[] | select((.taken_at | fromdateiso8601) >= $c)]' \
      "$HIST_FILE"
    ;;
  schedule)
    jq -r '.[] | "[\(.frequency)] \(.name) \(.dose)"' "$MEDS_FILE"
    ;;
  due)
    # Show medications not yet taken today
    TODAY=$(date +%Y-%m-%d)
    TAKEN_TODAY=$(jq -r --arg t "$TODAY" \
      '[.[] | select(.taken_at | startswith($t)) | .name] | unique | .[]' \
      "$HIST_FILE" 2>/dev/null || echo "")
    jq -r '.[] | .name' "$MEDS_FILE" | while read -r MED; do
      if ! echo "$TAKEN_TODAY" | grep -qx "$MED"; then
        echo "DUE: $MED"
      fi
    done
    ;;
  *)
    echo "Unknown command: $CMD"
    echo "Usage: $0 {add|list|take|history|schedule|due}"
    exit 1
    ;;
esac
"""

script_path = workspace / "scripts" / "script.sh"
script_path.write_text(script_content)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")
print(f"Key files: SKILL.md, scripts/script.sh, patient_records/jordan/profile.json")