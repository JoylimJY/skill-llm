#!/usr/bin/env python3
"""
Generate the sandbox workspace for the learning-loop biotech task.
Installs the learning-loop skill scripts and creates a realistic, messy workspace.
"""
import os
import json
import stat
import random
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Clone / install the learning-loop skill scripts ────────────────────────
# The SKILL.md says scripts already exist. We simulate this by creating them
# from the documented source (the scripts are part of the skill package).
# We'll create stub versions of all scripts that the agent needs,
# sourced directly from the documented behavior.

SKILL_DIR = WORKSPACE / "skill"
SKILL_DIR.mkdir(parents=True, exist_ok=True)

# ── 2. Create realistic distractor files ──────────────────────────────────────
distractors = {
    "pipeline/snakemake/Snakefile": "rule all:\n    input: expand('results/{sample}.vcf', sample=SAMPLES)\n",
    "pipeline/snakemake/config.yaml": "samples:\n  - SRR001\n  - SRR002\nreference: hg38\n",
    "pipeline/scripts/align.sh": "#!/bin/bash\nbwa mem $REF $FQ1 $FQ2 | samtools sort -o $OUT\n",
    "pipeline/scripts/call_variants.py": "import pysam\n# variant calling stub\n",
    "pipeline/results/.gitkeep": "",
    "docs/SOP_v2.md": "# Standard Operating Procedure\nVersion 2.0 — Draft\n",
    "docs/meeting_notes_2026-01.md": "## Jan Meeting\n- Discussed pipeline failures\n- Action: document lessons\n",
    "docs/meeting_notes_2026-02.md": "## Feb Meeting\n- Reviewed config drift issues\n- Action: enforce config policies\n",
    "reports/weekly_2026-W05.md": "# Week 5 Report\nEvents: 3 failures on config parsing\n",
    "reports/weekly_2026-W06.md": "# Week 6 Report\nEvents: 2 failures on environment variables\n",
    "config/pipeline.ini": "[defaults]\nthreads=8\nmemory=32G\n",
    "config/environment.yml": "name: bioinfo\ndependencies:\n  - python=3.11\n  - bwa=0.7.17\n",
    "config/broken_old.json": '{"version": "1.2", "settings": {bad json here}',
    "logs/2026-01-15.log": "ERROR: Missing reference index\nINFO: Reindexed hg38\nINFO: Pipeline completed\n",
    "logs/2026-02-01.log": "ERROR: Config key 'threads' missing\nWARN: Using default 4 threads\n",
    "logs/2026-02-10.log": "ERROR: Env var SNAKEMAKE_PROFILE not set\nINFO: Used fallback profile\n",
    "src/utils/file_helpers.py": "def safe_read(path):\n    try:\n        return open(path).read()\n    except:\n        return None\n",
    "src/utils/json_helpers.py": "import json\ndef load_safe(path):\n    with open(path) as f:\n        return json.load(f)\n",
    "tests/test_pipeline.py": "import pytest\ndef test_align_output():\n    assert True  # placeholder\n",
    ".gitignore": "*.pyc\n__pycache__/\n.snakemake/\nresults/\n",
}

for rel_path, content in distractors.items():
    full = WORKSPACE / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

# ── 3. Install the learning-loop skill scripts ─────────────────────────────────
# These scripts are described in SKILL.md as pre-existing in the workspace.
# We install the actual learning-loop package from the documented GitHub repo.
# Since we can't guarantee network, we write the key scripts from source.

SCRIPTS_DIR = WORKSPACE  # scripts run as: bash init.sh /workspace, etc.

# init.sh — initializes memory/learning/ directory
INIT_SH = r"""#!/bin/bash
# Learning Loop - Initialize workspace
set -o pipefail
WORKSPACE="${1:-$(pwd)}"
LEARNING_DIR="$WORKSPACE/memory/learning"
mkdir -p "$LEARNING_DIR/weekly"
mkdir -p "$LEARNING_DIR/archive"

# Create events.jsonl if not exists
[ ! -f "$LEARNING_DIR/events.jsonl" ] && touch "$LEARNING_DIR/events.jsonl"

# Create parse-errors.jsonl
[ ! -f "$LEARNING_DIR/parse-errors.jsonl" ] && touch "$LEARNING_DIR/parse-errors.jsonl"

# Create rules.json with starter rules if not exists
if [ ! -f "$LEARNING_DIR/rules.json" ]; then
cat > "$LEARNING_DIR/rules.json" << 'RULES'
{
  "version": "1.4.0",
  "updated": "2026-02-01",
  "rules": [
    {
      "id": "R-001",
      "type": "MUST",
      "category": "memory",
      "rule": "Always append new events to events.jsonl immediately after a debugging session.",
      "reason": "Memory degrades rapidly; capturing immediately ensures no knowledge loss.",
      "created": "2026-02-01",
      "source_lesson": "L-000",
      "violations": 0,
      "last_checked": "2026-02-01",
      "last_validated": "2026-02-01",
      "validation_count": 1,
      "confidence_score": 0.9,
      "review_flagged": false
    },
    {
      "id": "R-002",
      "type": "NEVER",
      "category": "memory",
      "rule": "Never delete or edit historical events in events.jsonl.",
      "reason": "Events are append-only. Editing destroys audit trail and learning history.",
      "created": "2026-02-01",
      "source_lesson": "L-000",
      "violations": 0,
      "last_checked": "2026-02-01",
      "last_validated": "2026-02-01",
      "validation_count": 1,
      "confidence_score": 0.9,
      "review_flagged": false
    },
    {
      "id": "R-003",
      "type": "CHECK",
      "category": "config",
      "rule": "Validate all JSON config files with python3 json.load before using them in pipelines.",
      "reason": "Malformed configs cause silent failures deep in pipeline execution.",
      "created": "2026-02-01",
      "source_lesson": "L-000",
      "violations": 0,
      "last_checked": "2026-02-01",
      "last_validated": "2026-02-01",
      "validation_count": 1,
      "confidence_score": 0.9,
      "review_flagged": false
    }
  ]
}
RULES
fi

# Create lessons.json if not exists
[ ! -f "$LEARNING_DIR/lessons.json" ] && echo '{"version":"1.4.0","lessons":[]}' > "$LEARNING_DIR/lessons.json"

# Create metrics.json if not exists
if [ ! -f "$LEARNING_DIR/metrics.json" ]; then
cat > "$LEARNING_DIR/metrics.json" << 'METRICS'
{
  "version": "1.4.0",
  "started": "2026-02-01",
  "weekly": [],
  "totals": {
    "events": 0,
    "lessons": 0,
    "rules": 3,
    "total_violations": 0,
    "total_saves": 0,
    "total_applied": 0,
    "promoted": 0
  }
}
METRICS
fi

# Create pre-action-checklist.md
cat > "$LEARNING_DIR/pre-action-checklist.md" << 'CHECKLIST'
# Pre-Action Checklist

Before any risky action:
1. Check rules.json for relevant constraints
2. Validate all input files
3. Backup data before destructive operations
4. Confirm environment variables are set
CHECKLIST

# Create BOOT.md
cat > "$LEARNING_DIR/BOOT.md" << 'BOOT'
# BOOT.md - Session Quick Reference

1. Read rules.json - hard behavioral rules
2. Check confidence scores - rules < 0.5 need review
3. Before risky actions: check pre-action-checklist.md
4. After mistakes: append to events.jsonl
BOOT

echo "Initialized learning loop at $LEARNING_DIR"
"""

# confidence-decay.sh — Ebbinghaus decay
CONFIDENCE_DECAY_SH = r"""#!/bin/bash
# Learning Loop - Confidence Decay (v1.4.0)
# Applies Ebbinghaus-inspired exponential decay to rule and lesson confidence scores.
# Formula: max(0.3, confidence * exp(-0.05 * days_since_validation))
# Usage: bash confidence-decay.sh [workspace-dir] [--dry-run]
set -o pipefail

WORKSPACE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *) [ -z "$WORKSPACE" ] && WORKSPACE="$1"; shift ;;
    esac
done

WORKSPACE="${WORKSPACE:-$(pwd)}"
LEARNING_DIR="$WORKSPACE/memory/learning"
RULES_FILE="$LEARNING_DIR/rules.json"
LESSONS_FILE="$LEARNING_DIR/lessons.json"

python3 - "$RULES_FILE" "$LESSONS_FILE" "$DRY_RUN" << 'PYTHON'
import json, sys, math, fcntl
from datetime import datetime, date

rules_path = sys.argv[1]
lessons_path = sys.argv[2]
dry_run = sys.argv[3].lower() == "true"

today = date.today()

def decay_confidence(confidence, last_validated_str):
    try:
        last_validated = date.fromisoformat(last_validated_str)
        days = (today - last_validated).days
        if days < 1:
            return confidence
        decayed = confidence * math.exp(-0.05 * days)
        return round(max(0.3, decayed), 4)
    except Exception:
        return confidence

# Process rules
try:
    with open(rules_path, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        rules_data = json.load(f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
except Exception as e:
    print(f"ERROR loading rules: {e}")
    sys.exit(1)

stale_rules = []
for rule in rules_data.get("rules", []):
    old_confidence = rule.get("confidence_score", 0.9)
    last_validated = rule.get("last_validated", str(today))
    new_confidence = decay_confidence(old_confidence, last_validated)
    if not dry_run:
        rule["confidence_score"] = new_confidence
        if new_confidence < 0.5:
            rule["review_flagged"] = True
            stale_rules.append(rule["id"])
    print(f"  Rule {rule['id']}: {old_confidence:.4f} -> {new_confidence:.4f} ({(today - date.fromisoformat(last_validated)).days if last_validated else 0} days)")

if not dry_run:
    with open(rules_path, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(rules_data, f, indent=2)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# Process lessons
try:
    with open(lessons_path, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        lessons_data = json.load(f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
except Exception as e:
    print(f"ERROR loading lessons: {e}")
    sys.exit(1)

for lesson in lessons_data.get("lessons", []):
    old_confidence = lesson.get("confidence_score", 0.9)
    last_validated = lesson.get("last_validated", str(today))
    new_confidence = decay_confidence(old_confidence, last_validated)
    if not dry_run:
        lesson["confidence_score"] = new_confidence
        if new_confidence < 0.5:
            lesson["review_flagged"] = True
    print(f"  Lesson {lesson['id']}: {old_confidence:.4f} -> {new_confidence:.4f}")

if not dry_run:
    with open(lessons_path, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(lessons_data, f, indent=2)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

if stale_rules:
    print(f"\nStale rules (confidence < 0.5): {stale_rules}")
print(f"\nDry run: {dry_run}")
PYTHON
"""

# promote-rules.sh — promote lessons with 3+ applications and confidence >= 0.9
PROMOTE_RULES_SH = r"""#!/bin/bash
# Learning Loop - Promote Lessons to Rules
# Promotes lessons with times_applied >= 3 AND confidence_score >= 0.9
# Usage: bash promote-rules.sh [workspace-dir]
set -o pipefail

WORKSPACE="${1:-$(pwd)}"
LEARNING_DIR="$WORKSPACE/memory/learning"
RULES_FILE="$LEARNING_DIR/rules.json"
LESSONS_FILE="$LEARNING_DIR/lessons.json"

python3 - "$RULES_FILE" "$LESSONS_FILE" << 'PYTHON'
import json, sys, fcntl
from datetime import date

rules_path = sys.argv[1]
lessons_path = sys.argv[2]
today = str(date.today())

# Load rules
try:
    with open(rules_path, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        rules_data = json.load(f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
except Exception as e:
    print(f"ERROR loading rules: {e}"); sys.exit(1)

# Load lessons
try:
    with open(lessons_path, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        lessons_data = json.load(f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
except Exception as e:
    print(f"ERROR loading lessons: {e}"); sys.exit(1)

rules = rules_data.get("rules", [])
lessons = lessons_data.get("lessons", [])

# Determine next rule ID
existing_ids = [r["id"] for r in rules]
max_num = 0
for rid in existing_ids:
    try:
        num = int(rid.replace("R-", ""))
        max_num = max(max_num, num)
    except: pass

promoted = 0
for lesson in lessons:
    # Skip already promoted
    if lesson.get("promoted_to_rule"):
        continue
    # Check thresholds: times_applied >= 3 AND confidence_score >= 0.9
    if lesson.get("times_applied", 0) >= 3 and lesson.get("confidence_score", 0) >= 0.9:
        max_num += 1
        new_rule_id = f"R-{max_num:03d}"
        new_rule = {
            "id": new_rule_id,
            "type": lesson.get("rule_type", "MUST"),
            "category": lesson.get("category", "general"),
            "rule": lesson.get("action", lesson.get("lesson", "")),
            "reason": lesson.get("context", ""),
            "created": today,
            "source_lesson": lesson["id"],
            "violations": 0,
            "last_checked": today,
            "last_validated": today,
            "validation_count": 0,
            "confidence_score": lesson.get("confidence_score", 0.9),
            "review_flagged": False
        }
        rules.append(new_rule)
        lesson["promoted_to_rule"] = new_rule_id
        promoted += 1
        print(f"Promoted {lesson['id']} -> {new_rule_id}: {lesson.get('lesson','')[:60]}")

rules_data["rules"] = rules
rules_data["updated"] = today

with open(rules_path, "w") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    json.dump(rules_data, f, indent=2)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

with open(lessons_path, "w") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    json.dump(lessons_data, f, indent=2)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

print(f"\nPromoted {promoted} lesson(s) to rules.")
print(f"Total rules: {len(rules)}")
PYTHON
"""

# export-rules.sh is already provided verbatim in SKILL.md — write it exactly
EXPORT_RULES_SH = r"""#!/bin/bash
# Learning Loop - Rule Exporter for Cross-Agent Sharing (v1.4.0)
set -o pipefail

SCRIPT_NAME="export-rules.sh"
VERSION="1.4.0"

WORKSPACE=""
OUTPUT_FILE=""
CATEGORY_FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        --category) CATEGORY_FILTER="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: bash export-rules.sh [workspace-dir] [options]"
            exit 0 ;;
        -*)
            echo "Unknown option: $1"; exit 1 ;;
        *)
            if [ -z "$WORKSPACE" ]; then WORKSPACE="$1"; fi
            shift ;;
    esac
done

WORKSPACE="${WORKSPACE:-$(pwd)}"
LEARNING_DIR="$WORKSPACE/memory/learning"
RULES_FILE="$LEARNING_DIR/rules.json"

if [[ ! -d "$WORKSPACE" ]]; then
    echo "ERROR: Workspace does not exist: $WORKSPACE"; exit 1
fi

if [[ "$WORKSPACE" =~ ^/(etc|bin|sbin|usr|System|Library|Applications) ]]; then
    echo "ERROR: Cannot use system directory as workspace: $WORKSPACE"; exit 1
fi

if [ ! -f "$RULES_FILE" ]; then
    echo "ERROR: rules.json not found at $RULES_FILE"; exit 1
fi

AGENT_HANDLE="${AGENT_HANDLE:-$(whoami)}"
EXPORT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

python3 - "$RULES_FILE" "$AGENT_HANDLE" "$EXPORT_TIMESTAMP" "$CATEGORY_FILTER" "$SCRIPT_NAME" << 'PYTHON'
import json, sys, hashlib, fcntl
from datetime import datetime

rules_path = sys.argv[1]
agent_handle = sys.argv[2]
export_timestamp = sys.argv[3]
category_filter = sys.argv[4] if len(sys.argv) > 4 else ""
script_name = sys.argv[5] if len(sys.argv) > 5 else ""

def calculate_rule_hash(rule):
    content = json.dumps(rule, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def sanitize_rule(rule):
    keep_fields = {
        "id", "type", "category", "rule", "reason",
        "created", "source_lesson", "confidence_score",
        "last_validated", "validation_count"
    }
    return {k: v for k, v in rule.items() if k in keep_fields}

try:
    with open(rules_path, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        rules_data = json.load(f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"ERROR: Could not load rules.json: {e}", file=sys.stderr)
    sys.exit(1)

all_rules = rules_data.get("rules", [])

if category_filter:
    rules = [r for r in all_rules if r.get("category") == category_filter]
    filter_applied = True
else:
    rules = all_rules
    filter_applied = False

categories = {}
rule_types = {}
for r in all_rules:
    cat = r.get("category", "unknown")
    rtype = r.get("type", "UNKNOWN")
    categories[cat] = categories.get(cat, 0) + 1
    rule_types[rtype] = rule_types.get(rtype, 0) + 1

export = {
    "metadata": {
        "export_version": "1.4.0",
        "export_format": "learning-loop-rules",
        "agent_handle": agent_handle,
        "exported_at": export_timestamp,
        "source_workspace": rules_path.replace("/memory/learning/rules.json", ""),
        "filter_applied": filter_applied,
        "filter_category": category_filter if category_filter else None,
        "total_rules_in_source": len(all_rules),
        "exported_rules_count": len(rules)
    },
    "statistics": {
        "categories": categories,
        "rule_types": rule_types,
        "avg_confidence": round(
            sum(r.get("confidence_score", 0.9) for r in rules) / len(rules), 2
        ) if rules else 0
    },
    "rules": []
}

for rule in rules:
    rule_export = sanitize_rule(rule)
    rule_export["_hash"] = calculate_rule_hash(rule_export)
    rule_export["_original_id"] = rule.get("id")
    export["rules"].append(rule_export)

manifest_content = json.dumps(export["metadata"], sort_keys=True) + json.dumps(export["rules"], sort_keys=True)
export["metadata"]["manifest_hash"] = hashlib.sha256(manifest_content.encode('utf-8')).hexdigest()[:16]

print(json.dumps(export, indent=2))

print(f"\nExport complete:", file=sys.stderr)
print(f"  Rules exported: {len(rules)} / {len(all_rules)} total", file=sys.stderr)
print(f"  Agent: {agent_handle}", file=sys.stderr)
print(f"  Manifest hash: {export['metadata']['manifest_hash']}", file=sys.stderr)
if filter_applied:
    print(f"  Filter: category = '{category_filter}'", file=sys.stderr)
PYTHON

exit_code=$?
exit $exit_code
"""

# Write all scripts
scripts = {
    "init.sh": INIT_SH,
    "confidence-decay.sh": CONFIDENCE_DECAY_SH,
    "promote-rules.sh": PROMOTE_RULES_SH,
    "export-rules.sh": EXPORT_RULES_SH,
}

for name, content in scripts.items():
    p = WORKSPACE / name
    p.write_text(content)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 4. Create the messy input data the agent must process ─────────────────────
# We create a "research_findings.md" doc that documents historical pipeline lessons
# — raw, unstructured — that the agent must convert into proper events and lessons.
# We deliberately create lessons that are ALMOST ready for promotion (need one more
# application), and some that ARE ready, to test discrimination.

RESEARCH_FINDINGS = """# Research Pipeline Lessons - Unstructured Notes
# Bioinfo Team - Q1 2026

## Finding A: Config Validation Gaps (CRITICAL - seen 5 times)
Every time we hand off configs between pipeline stages without validation, 
we get cryptic downstream errors. We've learned to always validate JSON 
configs with python3 json.load before passing them to any pipeline tool.
This has saved us 4 times already (Jan 6, Jan 14, Jan 22, Feb 3).
Context: Bioinformatics pipeline config files are complex and easily corrupted.
Trigger: Any pipeline stage that reads a JSON config file.
Action: Always run python3 -c "import json; json.load(open('config.json'))" before using any config.
Category: config
Rule type: MUST
Times applied: 4
Confidence: 0.95

## Finding B: Environment Variable Failures (seen 3 times)
Missing SNAKEMAKE_PROFILE env var causes silent fallback to default 8-core profile,
which overloads shared HPC nodes. Must always check env vars exist before running.
Saved 3 runs (Jan 10, Jan 28, Feb 8).
Context: HPC shared cluster environment requires explicit profile selection.
Trigger: Any snakemake execution on HPC.
Action: Always run 'test -n "$SNAKEMAKE_PROFILE"' before snakemake commands.
Category: config
Rule type: CHECK
Times applied: 3
Confidence: 0.9

## Finding C: Index File Staleness (still testing - seen 1 time)
BWA index files go stale after reference genome updates. We learned this once.
Still testing whether this is consistently true.
Category: shell
Times applied: 1
Confidence: 0.6

## Finding D: Conda Environment Lock Files (seen 2 times - not ready yet)
Always pin exact conda package versions in environment.yml.
Category: config
Times applied: 2
Confidence: 0.85
"""

(WORKSPACE / "research_findings.md").write_text(RESEARCH_FINDINGS)

# Create a stale_rules_context.md explaining what the agent needs to do
# (business language, no technical hints)
TASK_CONTEXT = """# Partner Lab Knowledge Sharing - Action Required

The computational biology team has accumulated critical pipeline lessons over Q1 2026.
We need to:
1. Set up the persistent knowledge management system in this workspace
2. Record our research findings as structured entries in the system  
3. Run the weekly maintenance cycle to formalize proven findings into hard policies
4. Export our "config" category policies for the partner lab at Nexigen Genomics

The research_findings.md file contains our raw notes. The exported policies should
go into a file called partner-export.json in this workspace.

Contact: pi@biolab.example.com
"""

(WORKSPACE / "TASK_CONTEXT.md").write_text(TASK_CONTEXT)

print("Workspace generated successfully.")
print(f"Workspace: {WORKSPACE}")
print(f"Scripts installed: {list(scripts.keys())}")
print(f"Distractor files: {len(distractors)}")