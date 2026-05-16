#!/usr/bin/env python3
"""
Generate a realistic, messy sandbox workspace for the health-data skill evaluation.
Creates a synthetic Apple Health export.zip, the health-data script, and many distractor files.
"""

import os
import zipfile
import random
import string
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────

def rand_date(start, days):
    return (start + timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d %H:%M:%S +0000")

def rand_source():
    return random.choice(["iPhone", "Apple Watch Series 8", "Health App", "Garmin Connect"])

# ── 1. Build export.xml ───────────────────────────────────────────────────────

start_dt = datetime(2024, 1, 1)

records = []

# Step count records — 60 entries
for i in range(60):
    d = rand_date(start_dt, 180)
    end_d = rand_date(start_dt, 181)
    val = random.randint(200, 15000)
    src = rand_source()
    records.append(
        f'  <Record type="HKQuantityTypeIdentifierStepCount" '
        f'sourceName="{src}" unit="count" '
        f'startDate="{d}" endDate="{end_d}" value="{val}"/>'
    )

# Walking/Running Distance records — 30 entries
for i in range(30):
    d = rand_date(start_dt, 180)
    end_d = rand_date(start_dt, 181)
    val = round(random.uniform(50.0, 8000.0), 2)
    src = rand_source()
    records.append(
        f'  <Record type="HKQuantityTypeIdentifierDistanceWalkingRunning" '
        f'sourceName="{src}" unit="m" '
        f'startDate="{d}" endDate="{end_d}" value="{val}"/>'
    )

# Sleep analysis records — 25 entries
sleep_vals = ["HKCategoryValueSleepAnalysisAsleep", "HKCategoryValueSleepAnalysisInBed"]
for i in range(25):
    d = rand_date(start_dt, 180)
    end_d = rand_date(start_dt, 181)
    val = random.choice(sleep_vals)
    src = rand_source()
    records.append(
        f'  <Record type="HKCategoryTypeIdentifierSleepAnalysis" '
        f'sourceName="{src}" unit="" '
        f'startDate="{d}" endDate="{end_d}" value="{val}"/>'
    )

# Heart rate records — 40 entries
for i in range(40):
    d = rand_date(start_dt, 180)
    end_d = rand_date(start_dt, 181)
    val = random.randint(45, 120)
    src = rand_source()
    records.append(
        f'  <Record type="HKQuantityTypeIdentifierHeartRate" '
        f'sourceName="{src}" unit="count/min" '
        f'startDate="{d}" endDate="{end_d}" value="{val}"/>'
    )

# Active Energy records — 20 entries
for i in range(20):
    d = rand_date(start_dt, 180)
    end_d = rand_date(start_dt, 181)
    val = round(random.uniform(10.0, 500.0), 2)
    src = rand_source()
    records.append(
        f'  <Record type="HKQuantityTypeIdentifierActiveEnergyBurned" '
        f'sourceName="{src}" unit="Cal" '
        f'startDate="{d}" endDate="{end_d}" value="{val}"/>'
    )

random.shuffle(records)

export_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
export_xml += '<!DOCTYPE HealthData [\n'
export_xml += '<!ELEMENT HealthData (ExportDate,Me,Record*)>\n'
export_xml += ']>\n'
export_xml += '<HealthData locale="en_US">\n'
export_xml += f' <ExportDate value="{datetime(2024, 7, 1).strftime("%Y-%m-%d %H:%M:%S +0000")}"/>\n'
export_xml += ' <Me HKCharacteristicTypeIdentifierDateOfBirth="" HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexNotSet"/>\n'
for r in records:
    export_xml += r + "\n"
export_xml += "</HealthData>\n"

# ── 2. Build the health-data.sh script ────────────────────────────────────────

health_data_sh = r'''#!/usr/bin/env bash
# health-data.sh — Apple Health export analyzer
set -euo pipefail

PHI_BANNER="[PHI WARNING] This data contains Protected Health Information. Handle with care. Do not share or upload."

usage() {
  echo "Usage: health-data.sh <command> <export-path> [options]"
  echo "Commands: list-types | summary | export-json"
  exit 1
}

[[ $# -lt 2 ]] && usage

CMD="$1"
EXPORT_PATH="$2"
shift 2

# Resolve export.xml
TMPDIR_WORK=""
cleanup() { [[ -n "$TMPDIR_WORK" ]] && rm -rf "$TMPDIR_WORK"; }
trap cleanup EXIT

if [[ -f "$EXPORT_PATH" && "$EXPORT_PATH" == *.zip ]]; then
  TMPDIR_WORK=$(mktemp -d)
  unzip -q "$EXPORT_PATH" -d "$TMPDIR_WORK"
  XML_PATH=$(find "$TMPDIR_WORK" -name "export.xml" | head -1)
  [[ -z "$XML_PATH" ]] && { echo "zip does not contain export.xml"; exit 1; }
elif [[ -d "$EXPORT_PATH" ]]; then
  XML_PATH="$EXPORT_PATH/export.xml"
elif [[ -f "$EXPORT_PATH" && "$EXPORT_PATH" == *.xml ]]; then
  XML_PATH="$EXPORT_PATH"
else
  echo "no such file or directory: $EXPORT_PATH"; exit 1
fi

case "$CMD" in

  list-types)
    xmlstarlet sel -t -v "//Record/@type" "$XML_PATH" \
      | sort | uniq -c | sort -rn
    ;;

  summary)
    echo "$PHI_BANNER" >&2
    TOTAL=$(xmlstarlet sel -t -v "count(//Record)" "$XML_PATH")
    FIRST=$(xmlstarlet sel -t -v "(//Record/@startDate)[1]" "$XML_PATH")
    LAST=$(xmlstarlet sel -t -v "(//Record/@startDate)[last()]" "$XML_PATH")

    STEPS=$(xmlstarlet sel -t \
      -v "sum(//Record[@type='HKQuantityTypeIdentifierStepCount']/@value)" \
      "$XML_PATH" 2>/dev/null || echo 0)

    DIST=$(xmlstarlet sel -t \
      -v "sum(//Record[@type='HKQuantityTypeIdentifierDistanceWalkingRunning']/@value)" \
      "$XML_PATH" 2>/dev/null || echo 0)

    ASLEEP=$(xmlstarlet sel -t \
      -v "count(//Record[@type='HKCategoryTypeIdentifierSleepAnalysis'][@value='HKCategoryValueSleepAnalysisAsleep'])" \
      "$XML_PATH" 2>/dev/null || echo 0)

    INBED=$(xmlstarlet sel -t \
      -v "count(//Record[@type='HKCategoryTypeIdentifierSleepAnalysis'][@value='HKCategoryValueSleepAnalysisInBed'])" \
      "$XML_PATH" 2>/dev/null || echo 0)

    echo "=== Apple Health Summary ==="
    echo "Total records   : $TOTAL"
    echo "Date range      : $FIRST → $LAST"
    echo "Steps (total)   : $STEPS"
    echo "Distance (m)    : $DIST"
    echo "Sleep - Asleep  : $ASLEEP"
    echo "Sleep - In Bed  : $INBED"
    echo ""
    echo "--- Top 5 Sources ---"
    xmlstarlet sel -t -v "//Record/@sourceName" "$XML_PATH" \
      | sort | uniq -c | sort -rn | head -5
    ;;

  export-json)
    echo "$PHI_BANNER" >&2
    RECORD_TYPE="${1:-}"
    shift || true
    LIMIT=""
    OUT_FILE=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --limit) LIMIT="$2"; shift 2 ;;
        --out)   OUT_FILE="$2"; shift 2 ;;
        *) shift ;;
      esac
    done

    [[ -z "$RECORD_TYPE" ]] && { echo "export-json requires <record-type>"; exit 1; }

    COUNT=0
    WARNED=false
    EMIT=""

    emit_record() {
      local type="$1" src="$2" unit="$3" sd="$4" ed="$5" val="$6"
      printf '{"type":"%s","sourceName":"%s","unit":"%s","startDate":"%s","endDate":"%s","value":"%s"}' \
        "$type" "$src" "$unit" "$sd" "$ed" "$val"
    }

    TMP_JSON=$(mktemp)

    echo "[" > "$TMP_JSON"
    FIRST_RECORD=true
    while IFS= read -r line; do
      if [[ -z "$LIMIT" && "$WARNED" == false && "$COUNT" -ge 100000 ]]; then
        echo "[WARNING] Over 100,000 records emitted without --limit. Consider using --limit." >&2
        WARNED=true
      fi
      [[ -n "$LIMIT" && "$COUNT" -ge "$LIMIT" ]] && break
      TYPE_VAL=$(echo "$line" | grep -oP '(?<=type=")[^"]+')
      SRC_VAL=$(echo "$line" | grep -oP '(?<=sourceName=")[^"]+')
      UNIT_VAL=$(echo "$line" | grep -oP '(?<=unit=")[^"]+' || echo "")
      SD_VAL=$(echo "$line" | grep -oP '(?<=startDate=")[^"]+')
      ED_VAL=$(echo "$line" | grep -oP '(?<=endDate=")[^"]+')
      VAL_VAL=$(echo "$line" | grep -oP '(?<=value=")[^"]+' || echo "")
      if [[ "$FIRST_RECORD" == true ]]; then
        FIRST_RECORD=false
      else
        echo "," >> "$TMP_JSON"
      fi
      emit_record "$TYPE_VAL" "$SRC_VAL" "$UNIT_VAL" "$SD_VAL" "$ED_VAL" "$VAL_VAL" >> "$TMP_JSON"
      COUNT=$((COUNT + 1))
    done < <(xmlstarlet sel -t \
      -m "//Record[@type='$RECORD_TYPE']" \
      -v "concat('<r type=\"',@type,'\" sourceName=\"',@sourceName,'\" unit=\"',@unit,'\" startDate=\"',@startDate,'\" endDate=\"',@endDate,'\" value=\"',@value,'\"/>')" \
      -n "$XML_PATH")

    echo "]" >> "$TMP_JSON"

    if [[ -n "$OUT_FILE" ]]; then
      install -m 600 /dev/null "$OUT_FILE"
      cat "$TMP_JSON" > "$OUT_FILE"
      echo "Saved $COUNT records to $OUT_FILE" >&2
    else
      cat "$TMP_JSON"
    fi
    rm -f "$TMP_JSON"
    ;;

  *)
    usage
    ;;
esac
'''

# ── 3. Write files to workspace ────────────────────────────────────────────────

# Create directory structure
dirs = [
    WORKSPACE / "health-data",
    WORKSPACE / "projects" / "wellness_audit" / "raw_data",
    WORKSPACE / "projects" / "wellness_audit" / "processed",
    WORKSPACE / "projects" / "wellness_audit" / "reports",
    WORKSPACE / "archive" / "old_exports" / "2023",
    WORKSPACE / "archive" / "old_exports" / "2022",
    WORKSPACE / "tools" / "parsers",
    WORKSPACE / "tools" / "visualizers",
    WORKSPACE / "docs",
    WORKSPACE / "tmp" / "scratch",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Write health-data.sh
script_path = WORKSPACE / "health-data" / "health-data.sh"
script_path.write_text(health_data_sh)

# Build export.zip
zip_path = WORKSPACE / "projects" / "wellness_audit" / "raw_data" / "export.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("apple_health_export/export.xml", export_xml)

# ── 4. Distractor files ───────────────────────────────────────────────────────

distractors = {
    WORKSPACE / "projects" / "wellness_audit" / "raw_data" / "manifest.txt":
        "Wellness Audit Manifest\nParticipant ID: WA-2024-0042\nConsent form: signed 2024-01-15\nData collection window: 2024-01-01 to 2024-06-30\n",

    WORKSPACE / "projects" / "wellness_audit" / "raw_data" / "consent_form.txt":
        "I consent to the processing of my Apple Health data for occupational wellness research.\nSigned: Participant WA-2024-0042\nDate: 2024-01-15\n",

    WORKSPACE / "projects" / "wellness_audit" / "processed" / "placeholder.txt":
        "This folder will contain processed outputs.\n",

    WORKSPACE / "projects" / "wellness_audit" / "reports" / "template.txt":
        "Report Template v1.2\nFields: participant_id, period, steps_total, distance_m, sleep_asleep, sleep_inbed, sources\n",

    WORKSPACE / "archive" / "old_exports" / "2023" / "notes.txt":
        "2023 export was corrupted. Re-export attempted but failed. Use 2024 data only.\n",

    WORKSPACE / "archive" / "old_exports" / "2022" / "summary_OLD.txt":
        "Steps: 3,210,000 (approximate)\nSleep sessions: 312\nNOTE: This was computed manually and may be inaccurate.\n",

    WORKSPACE / "archive" / "old_exports" / "2022" / "sources_OLD.csv":
        "source,count\nApple Watch Series 6,15230\niPhone,8934\nGarmin Connect,1200\n",

    WORKSPACE / "tools" / "parsers" / "xml_parser_v1.py":
        "# DEPRECATED: Use health-data.sh instead\nimport xml.etree.ElementTree as ET\n# ... old parsing logic removed\n",

    WORKSPACE / "tools" / "parsers" / "json_converter.py":
        "# DEPRECATED: Use health-data.sh export-json instead\nimport json\n",

    WORKSPACE / "tools" / "visualizers" / "plot_steps.py":
        "# Requires matplotlib and a processed JSON file\n# Usage: python plot_steps.py steps.json\nimport json, sys\n",

    WORKSPACE / "docs" / "data_dictionary.txt":
        "HKQuantityTypeIdentifierStepCount: Number of steps taken\nHKCategoryTypeIdentifierSleepAnalysis: Sleep state analysis\nHKQuantityTypeIdentifierDistanceWalkingRunning: Distance walked or run (meters)\nHKQuantityTypeIdentifierHeartRate: Heart rate in BPM\n",

    WORKSPACE / "docs" / "project_charter.txt":
        "Project: Occupational Wellness Audit 2024\nGoal: Anonymized step and sleep analysis for cohort of consented employees.\nData retention: 90 days post-analysis.\nContact: wellness-team@example.internal\n",

    WORKSPACE / "tmp" / "scratch" / "test_run.log":
        "2024-07-01 09:12:33 INFO  Starting audit pipeline\n2024-07-01 09:12:34 ERROR Missing processed data directory\n2024-07-01 09:12:34 INFO  Retrying...\n",

    WORKSPACE / "tmp" / "scratch" / "bad_export_attempt.txt":
        "Attempted to parse export.zip manually with python zipfile — got garbled XML. Abandoning manual approach.\n",
}

for path, content in distractors.items():
    path.write_text(content)

print(f"Workspace prepared at {WORKSPACE}")
print(f"  export.zip : {zip_path}")
print(f"  health-data.sh : {script_path}")
print(f"  Distractor files: {len(distractors)}")