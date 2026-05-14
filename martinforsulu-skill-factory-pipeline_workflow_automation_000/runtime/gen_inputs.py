#!/usr/bin/env python3
"""
Generate the sandbox workspace for the skill-factory evaluation task.
Creates a realistic partially-completed skill-factory workspace with distractor files.
"""

import os
import random
import stat
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

# ── Base skill-factory installation directory ──────────────────────────────
BASE_DIR = Path("/opt/skill-factory")
SCRIPTS_DIR = BASE_DIR / "scripts"
REFS_DIR = BASE_DIR / "references"

for d in [SCRIPTS_DIR, REFS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files in skill-factory installation ─────────────────────────
distractor_files = {
    BASE_DIR / "CHANGELOG.md": "# Changelog\n\n## v2.1.0\n- Added --to flag for stage targeting\n- Fixed idempotent re-run behavior\n\n## v2.0.0\n- Initial multi-agent pipeline\n",
    BASE_DIR / "VERSION": "2.1.0\n",
    BASE_DIR / "LICENSE": "MIT License\nCopyright (c) 2024 SkillFactory Authors\n",
    BASE_DIR / "config" / "defaults.yaml": "pipeline:\n  max_retries: 3\n  timeout_seconds: 300\nmodels:\n  market: gpt-4o\n  planner: gpt-4o\n  arch: gpt-4o\n  builder: gpt-4o-mini\n  auditor: gpt-4o\n  docs: gpt-4o-mini\n  pricer: gpt-4o-mini\n",
    BASE_DIR / "config" / "gates.yaml": "gates:\n  market: {file: market.md, non_empty: true}\n  planner: {file: plan.md, non_empty: true}\n  arch: {file: arch.md, non_empty: true}\n  builder: {file: skill/SKILL.md, non_empty: true}\n  auditor: {file: audit.md, non_empty: true}\n  docs: {file: docs_review.md, non_empty: true}\n  pricer: {file: pricing.md, non_empty: true}\n",
    BASE_DIR / "logs" / "pipeline.log": "[2024-01-15 09:00:00] Pipeline started\n[2024-01-15 09:01:23] Stage market: PASS\n[2024-01-15 09:03:45] Stage planner: PASS\n",
    REFS_DIR / "troubleshooting.md": "# Troubleshooting\n\n## Common Issues\n\n### Agent produces empty output\nRe-run the stage with `--from <stage> --to <stage>`.\n\n### Name too long\nThe planner must use hyphen-case names with max 32 characters.\nEdit SKILL.md frontmatter and fix the name field before re-running auditor.\n",
    REFS_DIR / "examples.md": "# Pipeline Examples\n\n## Running a single stage\n```bash\nbash pipeline.sh --workspace /tmp/sf-example --from builder --to builder\n```\n\n## Re-running from a failed stage\n```bash\nbash pipeline.sh --workspace /tmp/sf-example --from auditor\n```\n",
    SCRIPTS_DIR / "validate_skill.py": "#!/usr/bin/env python3\n# Utility: validate a skill directory structure\nimport sys\nfrom pathlib import Path\nskill_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('skill')\nprint('Validating:', skill_dir)\nprint('SKILL.md present:', (skill_dir / 'SKILL.md').exists())\n",
    SCRIPTS_DIR / "cleanup.sh": "#!/bin/bash\n# Remove all stage outputs except idea.md\nWS=${1:-/tmp/sf-workspace}\nrm -f \"$WS/market.md\" \"$WS/plan.md\" \"$WS/arch.md\" \"$WS/audit.md\"\nrm -f \"$WS/docs_review.md\" \"$WS/pricing.md\"\nrm -rf \"$WS/skill\"\necho 'Workspace cleaned (idea.md preserved).'\n",
}

for fpath, content in distractor_files.items():
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── The actual pipeline scripts (mocked) ──────────────────────────────────
# init_pipeline.py: Creates workspace with idea.md
init_pipeline_content = r'''#!/usr/bin/env python3
"""Initialize a skill-factory pipeline workspace."""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Initialize a skill-factory workspace")
    parser.add_argument("idea", help="The skill idea description")
    parser.add_argument("--workspace", required=True, help="Path to workspace directory")
    args = parser.parse_args()

    ws = Path(args.workspace)
    ws.mkdir(parents=True, exist_ok=True)

    idea_path = ws / "idea.md"
    idea_path.write_text(f"""# Skill Idea

{args.idea}

## Notes
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Edit this file before running the pipeline.
""")

    state_path = ws / ".pipeline_state"
    state_path.write_text(f"initialized: {datetime.now().isoformat()}\n")

    print(f"Workspace initialized at: {ws}")
    print(f"Idea written to: {idea_path}")
    print("Edit idea.md, then run pipeline.sh to start.")

if __name__ == "__main__":
    main()
'''

# pipeline.sh: The main orchestrator — mocked to simulate stage execution
pipeline_sh_content = r'''#!/bin/bash
# Mock skill-factory pipeline orchestrator
# Simulates agent execution by writing deterministic stage outputs

set -e

WORKSPACE=""
FROM_STAGE=""
TO_STAGE=""

# All valid stages in order
ALL_STAGES=("market" "planner" "arch" "builder" "auditor" "docs" "pricer")

usage() {
    echo "Usage: pipeline.sh --workspace <path> [--from <stage>] [--to <stage>]"
    echo "Stages: market planner arch builder auditor docs pricer"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace) WORKSPACE="$2"; shift 2 ;;
        --from) FROM_STAGE="$2"; shift 2 ;;
        --to) TO_STAGE="$2"; shift 2 ;;
        *) echo "Unknown argument: $1"; usage ;;
    esac
done

[[ -z "$WORKSPACE" ]] && { echo "ERROR: --workspace required"; usage; }
[[ ! -d "$WORKSPACE" ]] && { echo "ERROR: Workspace does not exist: $WORKSPACE"; exit 1; }

# Determine stage range
START_IDX=0
END_IDX=$((${#ALL_STAGES[@]} - 1))

if [[ -n "$FROM_STAGE" ]]; then
    found=false
    for i in "${!ALL_STAGES[@]}"; do
        if [[ "${ALL_STAGES[$i]}" == "$FROM_STAGE" ]]; then
            START_IDX=$i
            found=true
            break
        fi
    done
    $found || { echo "ERROR: Unknown stage '$FROM_STAGE'"; exit 1; }
fi

if [[ -n "$TO_STAGE" ]]; then
    found=false
    for i in "${!ALL_STAGES[@]}"; do
        if [[ "${ALL_STAGES[$i]}" == "$TO_STAGE" ]]; then
            END_IDX=$i
            found=true
            break
        fi
    done
    $found || { echo "ERROR: Unknown stage '$TO_STAGE'"; exit 1; }
fi

[[ $START_IDX -gt $END_IDX ]] && { echo "ERROR: --from stage must come before --to stage"; exit 1; }

run_stage() {
    local stage="$1"
    local ws="$2"
    local ts
    ts=$(date -Iseconds)

    echo "[pipeline] Running stage: $stage"
    # Delegate to the stage runner
    python3 /opt/skill-factory/scripts/_run_stage.py "$stage" "$ws"
    
    # Gate check
    case "$stage" in
        market)   gate_file="$ws/market.md" ;;
        planner)  gate_file="$ws/plan.md" ;;
        arch)     gate_file="$ws/arch.md" ;;
        builder)  gate_file="$ws/skill/SKILL.md" ;;
        auditor)  gate_file="$ws/audit.md" ;;
        docs)     gate_file="$ws/docs_review.md" ;;
        pricer)   gate_file="$ws/pricing.md" ;;
    esac

    if [[ ! -f "$gate_file" ]] || [[ ! -s "$gate_file" ]]; then
        echo "[pipeline] GATE FAILED: $gate_file missing or empty"
        exit 1
    fi

    echo "[pipeline] Stage $stage: PASS (gate: $gate_file)"
    echo "$stage: $ts" >> "$ws/.pipeline_state"
}

# Execute selected stages
for i in $(seq $START_IDX $END_IDX); do
    run_stage "${ALL_STAGES[$i]}" "$WORKSPACE"
done

echo "[pipeline] Done. Stages completed: ${ALL_STAGES[@]:$START_IDX:$((END_IDX - START_IDX + 1))}"
'''

# _run_stage.py: The actual mock stage logic
run_stage_content = r'''#!/usr/bin/env python3
"""
Mock stage runner for skill-factory pipeline.
Simulates agent behavior with deterministic outputs.
"""
import sys
import os
import re
from pathlib import Path
from datetime import datetime

def read_file(path):
    p = Path(path)
    return p.read_text() if p.exists() else ""

def write_file(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

def run_market(ws):
    idea = read_file(ws / "idea.md")
    write_file(ws / "market.md", f"""# Market Research Report

## Skill Idea Analysis
Based on: {idea[:100].strip()}

## Competitive Landscape
- Several CSV processing tools exist (pandas, csvkit, polars)
- No single skill integrates all transformation patterns into a structured agent workflow
- Strong demand in data engineering teams

## Target Audience
- Primary: Data engineers automating ETL pipelines
- Secondary: Backend developers handling CSV ingestion

## Demand Signals
- 2.3M monthly searches for "csv transform python"
- Active Stack Overflow questions: 15,000+
- GitHub stars on csvkit: 5,800+

## Verdict
GO — strong market need with clear differentiation opportunity.
""")

def run_planner(ws):
    idea = read_file(ws / "idea.md")
    market = read_file(ws / "market.md")
    write_file(ws / "plan.md", f"""# Product Plan

## Skill Name
csv-transform-pipeline

## Description
Automate CSV data transformation workflows with declarative rules and agent-driven execution.

## Trigger Scenarios
- "transform my CSV file"
- "clean and reshape CSV data"
- "apply transformation rules to CSV"
- "validate and normalize CSV columns"

## Capabilities
1. Column renaming and reordering
2. Data type coercion and validation
3. Row filtering with predicate expressions
4. Aggregation and pivot operations
5. Output format control (CSV, TSV, JSON)

## Files to Build
- SKILL.md (frontmatter + usage guide)
- scripts/transform.py (core transformation engine)
- scripts/validate.py (schema validation)
- references/transforms.md (transformation rule reference)
- references/examples.md (worked examples)

## Resource Directories
- scripts/
- references/
""")

def run_arch(ws):
    plan = read_file(ws / "plan.md")
    write_file(ws / "arch.md", f"""# Architecture Blueprint

## Directory Tree
```
skill/
├── SKILL.md
├── scripts/
│   ├── transform.py      # Core transformation engine
│   └── validate.py       # Schema validation utility
└── references/
    ├── transforms.md     # Rule reference documentation
    └── examples.md       # Worked transformation examples
```

## SKILL.md Sections
1. Frontmatter: name, description
2. Overview: what the skill does and when to use it
3. Usage: how to invoke transform.py and validate.py
4. Configuration: transformation rule format
5. Examples: 3 worked examples

## Script Descriptions

### transform.py
- Language: Python 3
- Inputs: --input <csv>, --rules <json>, --output <csv>
- Core logic: load rules JSON, apply column renames, type coercions, filters, write output
- Error handling: validates input file exists, rules are valid JSON, output dir exists

### validate.py
- Language: Python 3  
- Inputs: --input <csv>, --schema <json>
- Core logic: checks column names, data types, null constraints against schema
- Output: validation report to stdout with PASS/FAIL per column

## Reference Files

### transforms.md
- Complete rule grammar reference
- All supported transform operations with parameters
- Loaded by agents when constructing transformation rule sets

### examples.md
- 5 worked examples from raw CSV to transformed output
- Includes rule JSON snippets
- Loaded when user needs guidance on specific patterns

## Data Flow
User invokes skill → agent reads SKILL.md → agent calls transform.py with rules → 
optionally calls validate.py on output → result delivered to user
""")

def run_builder(ws):
    arch = read_file(ws / "arch.md")
    plan = read_file(ws / "plan.md")
    
    skill_dir = ws / "skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)

    # INTENTIONAL BUG: name is 35 characters (exceeds 32-char limit)
    # "csv-transform-pipeline-enterprise" = 35 chars
    write_file(skill_dir / "SKILL.md", """---
name: csv-transform-pipeline-enterprise
description: "Automate CSV data transformation workflows with declarative rules and agent-driven execution. Use when: transforming, cleaning, or reshaping CSV files programmatically."
---

# CSV Transform Pipeline

A skill for automating CSV data transformation using declarative rule sets.

## Overview

This skill provides two main utilities:
- `transform.py` — applies transformation rules to a CSV file
- `validate.py` — validates a CSV file against a schema

## When to Use

- User wants to rename columns, filter rows, or change data types in a CSV
- User needs to validate CSV structure before processing
- User wants to automate recurring CSV transformation tasks

## Usage

```bash
python3 scripts/transform.py --input data.csv --rules rules.json --output out.csv
python3 scripts/validate.py --input data.csv --schema schema.json
```

## Trigger Scenarios

- "transform my CSV file"
- "clean and reshape CSV data"  
- "apply transformation rules to CSV"
- "validate and normalize CSV columns"
""")

    write_file(skill_dir / "scripts" / "transform.py", '''#!/usr/bin/env python3
"""CSV Transformation Engine"""
import argparse
import json
import csv
import sys
from pathlib import Path

def apply_rules(rows, headers, rules):
    # Apply column renames
    if "rename" in rules:
        new_headers = [rules["rename"].get(h, h) for h in headers]
    else:
        new_headers = headers[:]
    
    # Apply filters
    filtered = []
    for row in rows:
        if "filter" in rules:
            keep = True
            for col, condition in rules["filter"].items():
                idx = headers.index(col) if col in headers else -1
                if idx >= 0:
                    val = row[idx]
                    if condition.get("not_empty") and not val.strip():
                        keep = False
            if not keep:
                continue
        filtered.append(row)
    
    return new_headers, filtered

def main():
    parser = argparse.ArgumentParser(description="Apply transformation rules to a CSV file")
    parser.add_argument("--input", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.rules) as f:
        rules = json.load(f)

    with open(args.input) as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    new_headers, transformed = apply_rules(rows, headers, rules)

    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(new_headers)
        writer.writerows(transformed)

    print(f"Transformed {len(transformed)} rows -> {args.output}")

if __name__ == "__main__":
    main()
''')

    write_file(skill_dir / "scripts" / "validate.py", '''#!/usr/bin/env python3
"""CSV Schema Validator"""
import argparse
import json
import csv
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Validate CSV against schema")
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.schema) as f:
        schema = json.load(f)

    with open(args.input) as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    errors = []
    expected_cols = schema.get("columns", [])
    for col_def in expected_cols:
        col_name = col_def["name"]
        if col_name not in headers:
            errors.append(f"FAIL: Column \'{col_name}\' missing")
        else:
            print(f"PASS: Column \'{col_name}\' present")

    if errors:
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("Validation PASSED")

if __name__ == "__main__":
    main()
''')

    write_file(skill_dir / "references" / "transforms.md", """# Transformation Rules Reference

## Rule File Format

Rules are expressed as a JSON object:

```json
{
  "rename": {"old_col": "new_col"},
  "filter": {"col_name": {"not_empty": true}},
  "types": {"amount": "float", "date": "date"}
}
```

## Supported Operations

### rename
Map old column names to new column names.

### filter
Apply per-column predicates. Supported predicates:
- `not_empty`: skip rows where this column is blank

### types
Coerce column values to a target type: `int`, `float`, `date`, `string`
""")

    write_file(skill_dir / "references" / "examples.md", """# Worked Examples

## Example 1: Rename Columns

Input CSV headers: `id, fname, lname, amt`
Rules:
```json
{"rename": {"fname": "first_name", "lname": "last_name", "amt": "amount"}}
```
Output headers: `id, first_name, last_name, amount`

## Example 2: Filter Empty Rows

```json
{"filter": {"email": {"not_empty": true}}}
```
Removes all rows where the `email` column is blank.

## Example 3: Combined Transform

```json
{
  "rename": {"dt": "date", "v": "value"},
  "filter": {"value": {"not_empty": true}},
  "types": {"value": "float"}
}
```
""")

def run_auditor(ws):
    skill_dir = ws / "skill"
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        write_file(ws / "audit.md", "# Audit\n\nERROR: skill/SKILL.md not found. Cannot audit.\n\nOVERALL: FAIL\n")
        return
    
    content = skill_md.read_text()
    
    # Check name length — this is the key gate
    name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else ""
    name_clean = name.strip('"\'')
    name_len = len(name_clean)
    
    if name_len > 32:
        write_file(ws / "audit.md", f"""# Quality Audit Report

## Audit Results

### 1. SKILL.md Completeness
FAIL — `name` field is {name_len} characters (max allowed: 32). Current value: `{name_clean}`
Required fix: Shorten the name to 32 characters or fewer using hyphen-case.

### 2. Trigger Accuracy  
PASS — Trigger scenarios are specific and well-defined.

### 3. Script Quality
PASS — Scripts have shebangs, argparse, error handling, real logic.

### 4. Reference Quality
PASS — Reference files are comprehensive with examples.

### 5. Internal Consistency
WARN — Name mismatch between SKILL.md frontmatter and plan.md.

### 6. Security Review
PASS — No injection risks, no hardcoded secrets detected.

### 7. Gap Analysis
WARN — Type coercion in transform.py not fully implemented.

## Required Fixes
1. [CRITICAL] Fix SKILL.md name: reduce from {name_len} to ≤32 characters.

OVERALL: FAIL
""")
    else:
        write_file(ws / "audit.md", f"""# Quality Audit Report

## Audit Results

### 1. SKILL.md Completeness
PASS — Frontmatter valid. name: `{name_clean}` ({name_len} chars, within 32-char limit). Description present.

### 2. Trigger Accuracy
PASS — Trigger scenarios are specific and well-defined.

### 3. Script Quality
PASS — Scripts have shebangs, argparse, error handling, real logic.

### 4. Reference Quality
PASS — Reference files are comprehensive with examples and rule grammar.

### 5. Internal Consistency
PASS — All files consistent with arch.md and plan.md specifications.

### 6. Security Review
PASS — No injection risks, no hardcoded secrets detected.

### 7. Gap Analysis
WARN — Type coercion in transform.py partially implemented; acceptable for v1.

## Summary
All critical items passed. One minor warning on type coercion — acceptable for initial release.

OVERALL: PASS
""")

def run_docs(ws):
    audit = read_file(ws / "audit.md")
    if "OVERALL: FAIL" in audit:
        write_file(ws / "docs_review.md", """# Documentation Review

BLOCKED — Audit returned OVERALL: FAIL. Documentation review cannot proceed until audit issues are resolved.

Please fix the issues listed in audit.md and re-run from the auditor stage:
```bash
bash pipeline.sh --workspace <workspace> --from auditor
```
""")
    else:
        write_file(ws / "docs_review.md", """# Documentation Review

## Overall Assessment
Documentation quality is GOOD. The SKILL.md is clear and well-structured.

## Detailed Feedback

### Clarity
PASS — The overview section clearly explains when to use the skill.

### Examples
PASS — Three worked examples in references/examples.md cover common use cases.

### Decision Guidance
WARN — Could add a section on when NOT to use this skill (e.g., very large files where streaming is needed).

### Suggested Rewrites

**Original (Usage section):**
> python3 scripts/transform.py --input data.csv --rules rules.json --output out.csv

**Improved:**
> ```bash
> # Basic transformation
> python3 scripts/transform.py --input raw_data.csv --rules my_rules.json --output clean_data.csv
>
> # With validation
> python3 scripts/validate.py --input clean_data.csv --schema expected_schema.json
> ```

## Verdict
APPROVED with minor suggestions.
""")

def run_pricer(ws):
    audit = read_file(ws / "audit.md")
    market = read_file(ws / "market.md")
    plan = read_file(ws / "plan.md")
    skill_md = read_file(ws / "skill" / "SKILL.md")
    
    write_file(ws / "pricing.md", """# Pricing and Positioning

## Quality Tier
**Standard** — Solid implementation with real logic, comprehensive references, and minor gaps acceptable for v1.

## Recommended Price
**$29 USD** — Rationale: The skill addresses a high-demand use case (CSV transformation) with production-ready scripts and clear documentation. Positioned above free CSV tools due to agent-native design. Below Pro tier due to partial type coercion implementation.

## Positioning Statement
The CSV Transform Pipeline skill gives data engineering teams a declarative, agent-driven approach to CSV transformation that eliminates repetitive scripting. Unlike generic pandas solutions, this skill integrates directly into agent workflows with structured rule files, making it auditable, repeatable, and maintainable by non-expert users.

## Key Selling Points
- Declarative JSON rules — no code required for common transformations
- Integrated schema validation with clear PASS/FAIL output
- Agent-native design: works seamlessly in automated pipelines
- Production-ready error handling and argparse CLI
- Comprehensive worked examples for immediate productivity

## Tags and Categories
**Tags:** csv, data-transform, etl, pipeline, data-engineering, automation
**Category:** Data Processing > File Transformation

## Launch Strategy
**Free Trial** — Offer a 14-day free trial for individual users. Bundle with the `data-pipeline-orchestrator` and `json-normalizer` skills at $69 for the Data Engineering Pack.
""")

def main():
    if len(sys.argv) != 3:
        print(f"Usage: _run_stage.py <stage> <workspace>")
        sys.exit(1)
    
    stage = sys.argv[1]
    ws = Path(sys.argv[2])
    
    stage_map = {
        "market": run_market,
        "planner": run_planner,
        "arch": run_arch,
        "builder": run_builder,
        "auditor": run_auditor,
        "docs": run_docs,
        "pricer": run_pricer,
    }
    
    if stage not in stage_map:
        print(f"ERROR: Unknown stage '{stage}'")
        sys.exit(1)
    
    stage_map[stage](ws)

if __name__ == "__main__":
    main()
'''

# Write the scripts
write_file = lambda p, c: (p.parent.mkdir(parents=True, exist_ok=True), p.write_text(c))

(SCRIPTS_DIR / "init_pipeline.py").write_text(init_pipeline_content)
(SCRIPTS_DIR / "pipeline.sh").write_text(pipeline_sh_content)
(SCRIPTS_DIR / "_run_stage.py").write_text(run_stage_content)

# Make scripts executable
for f in [SCRIPTS_DIR / "pipeline.sh", SCRIPTS_DIR / "init_pipeline.py", SCRIPTS_DIR / "_run_stage.py"]:
    f.chmod(f.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── The partially-completed workspace at /tmp/sf-csv-tool ─────────────────
WS = Path("/tmp/sf-csv-tool")
WS.mkdir(parents=True, exist_ok=True)

# idea.md — the original idea
(WS / "idea.md").write_text("""# Skill Idea

## Core Concept
A skill for transforming CSV files using declarative rule sets. The agent should be able to rename columns, filter rows, coerce data types, and produce clean output CSVs without requiring the user to write code.

## Target Users
Data engineers and backend developers who regularly process CSV exports from databases, SaaS tools, or data warehouses.

## Key Differentiator
Agent-native design: transformation rules are expressed as structured JSON, making them auditable, version-controllable, and repeatable across different datasets with the same schema.

## Notes
- Created: 2024-03-10 14:30:00
- The pipeline was initialized for internal platform team use.
- Priority: HIGH — needed for Q2 release.
""")

# market.md — stage 1 complete
(WS / "market.md").write_text("""# Market Research Report

## Skill Idea Analysis
CSV transformation skill for data engineering teams.

## Competitive Landscape
- Several CSV processing tools exist (pandas, csvkit, polars)
- No single skill integrates all transformation patterns into a structured agent workflow
- Strong demand in data engineering teams

## Target Audience
- Primary: Data engineers automating ETL pipelines
- Secondary: Backend developers handling CSV ingestion

## Demand Signals
- 2.3M monthly searches for "csv transform python"
- Active Stack Overflow questions: 15,000+
- GitHub stars on csvkit: 5,800+

## Verdict
GO — strong market need with clear differentiation opportunity.
""")

# plan.md — stage 2 complete
(WS / "plan.md").write_text("""# Product Plan

## Skill Name
csv-transform-pipeline

## Description
Automate CSV data transformation workflows with declarative rules and agent-driven execution.

## Trigger Scenarios
- "transform my CSV file"
- "clean and reshape CSV data"
- "apply transformation rules to CSV"
- "validate and normalize CSV columns"

## Capabilities
1. Column renaming and reordering
2. Data type coercion and validation
3. Row filtering with predicate expressions
4. Aggregation and pivot operations
5. Output format control (CSV, TSV, JSON)

## Files to Build
- SKILL.md (frontmatter + usage guide)
- scripts/transform.py (core transformation engine)
- scripts/validate.py (schema validation)
- references/transforms.md (transformation rule reference)
- references/examples.md (worked examples)

## Resource Directories
- scripts/
- references/
""")

# arch.md — stage 3 complete
(WS / "arch.md").write_text("""# Architecture Blueprint

## Directory Tree
```
skill/
├── SKILL.md
├── scripts/
│   ├── transform.py      # Core transformation engine
│   └── validate.py       # Schema validation utility
└── references/
    ├── transforms.md     # Rule reference documentation
    └── examples.md       # Worked transformation examples
```

## SKILL.md Sections
1. Frontmatter: name, description
2. Overview: what the skill does and when to use it
3. Usage: how to invoke transform.py and validate.py
4. Configuration: transformation rule format
5. Examples: 3 worked examples

## Script Descriptions

### transform.py
- Language: Python 3
- Inputs: --input <csv>, --rules <json>, --output <csv>
- Core logic: load rules JSON, apply column renames, type coercions, filters, write output
- Error handling: validates input file exists, rules are valid JSON, output dir exists

### validate.py
- Language: Python 3
- Inputs: --input <csv>, --schema <json>
- Core logic: checks column names, data types, null constraints against schema
- Output: validation report to stdout with PASS/FAIL per column

## Reference Files

### transforms.md
- Complete rule grammar reference
- All supported transform operations with parameters
- Loaded by agents when constructing transformation rule sets

### examples.md
- 5 worked examples from raw CSV to transformed output
- Includes rule JSON snippets
- Loaded when user needs guidance on specific patterns

## Data Flow
User invokes skill → agent reads SKILL.md → agent calls transform.py with rules →
optionally calls validate.py on output → result delivered to user
""")

# .pipeline_state — shows stages 1-3 done
(WS / ".pipeline_state").write_text("""initialized: 2024-03-10T14:30:00
market: 2024-03-10T14:31:45
planner: 2024-03-10T14:34:12
arch: 2024-03-10T14:37:55
""")

# Distractor files in workspace to confuse agents
(WS / "notes.txt").write_text("""Team notes - 2024-03-10

- Market research looks solid, GO verdict confirmed
- Planner produced a clean plan.md with good trigger scenarios
- Architecture review done - arch.md approved by senior engineer
- Builder is next - need to run it

TODO: 
- Run remaining pipeline stages
- Check audit results
- Don't forget pricing needs to go to marketing team
""")

(WS / "scratch" / "old_idea.md").parent.mkdir(exist_ok=True)
(WS / "scratch" / "old_idea.md").write_text("""# Old Idea (DISCARDED)
CSV merger tool - merge multiple CSV files by key column.
Discarded: too narrow, replaced with broader transform approach.
""")

(WS / "scratch" / "name_ideas.txt").write_text("""Skill name brainstorm:
- csv-transform-enterprise-pipeline (too long!)
- csv-pipeline (too generic)
- csv-transform-pipeline (good - within limit)
- data-csv-transformer (possible)
""")

print("Workspace generation complete.")
print(f"Skill-factory base: {BASE_DIR}")
print(f"Task workspace: {WS}")
print(f"\nContents of {WS}:")
for f in sorted(WS.rglob("*")):
    print(f"  {f.relative_to(WS)}")