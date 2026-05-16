import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Skill scaffold (scripts + references already "exist" per SKILL.md) ────────

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

references_dir = WORKSPACE / "references"
references_dir.mkdir(parents=True, exist_ok=True)

# ─── init_project_docs.py ──────────────────────────────────────────────────────
(scripts_dir / "init_project_docs.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Initialize project documentation scaffold.\"\"\"
import argparse, json, sys
from pathlib import Path
from datetime import datetime

GREENFIELD_DOCS = [
    "docs/requirements.md",
    "docs/architecture.md",
    "docs/tasks.md",
    "docs/progress.md",
    "docs/change-log.md",
    "docs/traceability.md",
    "docs/test-results.md",
    "docs/g4-task-plan.md",
    "docs/adr/ADR-0001.md",
]

BROWNFIELD_EXTRA_DOCS = [
    "docs/as-is-architecture.md",
    "docs/dependency-map.md",
    "docs/risk-register.md",
    "docs/migration-strategy.md",
    "docs/characterization-tests.md",
    "docs/agent-handoff.md",
    "docs/validation-log.md",
]

AGENTS_MD = \"\"\"# AGENTS.md — Project Workflow Contract

## Project Mode
{mode}

## Execution Mode
autonomous

## Coding Agent
codex

## Fallback Agent
claude

## Gate Sequence
G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7

## Spec-Driven Requirement
No code without a spec. See docs/requirements.md.
\"\"\"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--mode", required=True, choices=["greenfield", "brownfield"])
    args = p.parse_args()

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)

    docs = list(GREENFIELD_DOCS)
    if args.mode == "brownfield":
        docs += BROWNFIELD_EXTRA_DOCS

    created = []
    for rel in docs:
        fp = root / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        if not fp.exists():
            fp.write_text(f"# {fp.stem}\\n\\n_To be completed._\\n")
            created.append(rel)

    agents_md = root / "AGENTS.md"
    agents_md.write_text(AGENTS_MD.format(mode=args.mode))

    orch_dir = root / ".orchestrator"
    orch_dir.mkdir(parents=True, exist_ok=True)

    status_file = orch_dir / "status.json"
    if not status_file.exists():
        status = {
            "schema_version": "1.0",
            "project_mode": args.mode,
            "gates": {
                f"G{i}": {"state": "PENDING", "notes": []}
                for i in range(8)
            }
        }
        status_file.write_text(json.dumps(status, indent=2))

    context_file = orch_dir / "context.json"
    context_file.write_text(json.dumps({
        "project_mode": args.mode,
        "execution_mode": "autonomous",
        "research_mode": False,
        "agent": "codex",
        "fallback_agent": "claude",
        "initialized_at": datetime.utcnow().isoformat()
    }, indent=2))

    print(f"[init_project_docs] Scaffolded {len(created)} docs for mode={args.mode}")
    print(f"[init_project_docs] AGENTS.md written")
    print(f"[init_project_docs] .orchestrator/status.json initialized")

if __name__ == "__main__":
    main()
"""))

# ─── gate_status.py ────────────────────────────────────────────────────────────
(scripts_dir / "gate_status.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Manage gate states in .orchestrator/status.json\"\"\"
import argparse, json, sys
from pathlib import Path

VALID_STATES = {"PENDING", "IN_PROGRESS", "PASS", "FAIL", "BLOCKED"}
VALID_GATES  = {f"G{i}" for i in range(8)}

GATE_SEQUENCE = ["G0","G1","G2","G3","G4","G5","G6","G7"]

BROWNFIELD_REQUIRED_DOCS = {
    "G1": ["docs/as-is-architecture.md", "docs/dependency-map.md"],
    "G2": ["docs/risk-register.md", "docs/migration-strategy.md", "docs/characterization-tests.md"],
}

def load(root):
    sf = Path(root) / ".orchestrator" / "status.json"
    if not sf.exists():
        print(f"ERROR: {sf} not found. Run init_project_docs.py first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(sf.read_text()), sf

def save(sf, data):
    sf.write_text(json.dumps(data, indent=2))

def cmd_set(args):
    data, sf = load(args.root)
    gate = args.gate
    state = args.state
    if gate not in VALID_GATES:
        print(f"ERROR: invalid gate {gate}", file=sys.stderr); sys.exit(1)
    if state not in VALID_STATES:
        print(f"ERROR: invalid state {state}", file=sys.stderr); sys.exit(1)

    # Precondition: prior gate must be PASS before setting current IN_PROGRESS/PASS
    gate_idx = GATE_SEQUENCE.index(gate)
    if state in ("IN_PROGRESS", "PASS") and gate_idx > 0:
        prev = GATE_SEQUENCE[gate_idx - 1]
        prev_state = data["gates"].get(prev, {}).get("state", "PENDING")
        if prev_state != "PASS":
            print(f"ERROR: Cannot set {gate}={state}: {prev} is {prev_state} (must be PASS)", file=sys.stderr)
            sys.exit(1)

    # Brownfield doc checks
    mode = data.get("project_mode", "greenfield")
    if mode == "brownfield" and state == "PASS" and gate in BROWNFIELD_REQUIRED_DOCS:
        root_path = Path(args.root)
        for doc in BROWNFIELD_REQUIRED_DOCS[gate]:
            doc_path = root_path / doc
            if not doc_path.exists():
                print(f"ERROR: brownfield gate {gate} requires {doc} to exist", file=sys.stderr)
                sys.exit(1)
            content = doc_path.read_text().strip()
            if content == "# " + doc_path.stem + "\\n\\n_To be completed._" or "_To be completed._" in content:
                print(f"ERROR: {doc} has not been updated (still placeholder)", file=sys.stderr)
                sys.exit(1)

    data["gates"][gate]["state"] = state
    if args.note:
        data["gates"][gate].setdefault("notes", []).append(args.note)
    save(sf, data)
    print(f"[gate_status] {gate} → {state}" + (f" | {args.note}" if args.note else ""))

def cmd_validate(args):
    data, sf = load(args.root)
    errors = []
    if "schema_version" not in data:
        errors.append("missing schema_version")
    if "gates" not in data:
        errors.append("missing gates key")
    else:
        for g in GATE_SEQUENCE:
            if g not in data["gates"]:
                errors.append(f"missing gate {g}")
            else:
                s = data["gates"][g].get("state")
                if s not in VALID_STATES:
                    errors.append(f"{g} has invalid state: {s}")
    if errors:
        print("VALIDATION FAILED:")
        for e in errors: print(f"  - {e}")
        sys.exit(1)
    else:
        print("[gate_status] Schema valid. All gates present with valid states.")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("set")
    s.add_argument("--root", required=True)
    s.add_argument("--gate", required=True)
    s.add_argument("--state", required=True)
    s.add_argument("--note", default="")

    v = sub.add_parser("validate")
    v.add_argument("--root", required=True)

    args = p.parse_args()
    if args.cmd == "set": cmd_set(args)
    elif args.cmd == "validate": cmd_validate(args)
    else: p.print_help()

if __name__ == "__main__":
    main()
"""))

# ─── change_impact.py ──────────────────────────────────────────────────────────
(scripts_dir / "change_impact.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Analyze change request impact and emit TODOs.\"\"\"
import argparse, json
from pathlib import Path
from datetime import datetime

IMPACTED_DOCS = [
    "docs/change-log.md",
    "docs/traceability.md",
    "docs/risk-register.md",
    "docs/tasks.md",
    "docs/progress.md",
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--request", required=True)
    args = p.parse_args()

    root = Path(args.root)
    impact_id = f"CR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    print(f"[change_impact] Analyzing: {args.request}")
    print(f"[change_impact] Impact ID: {impact_id}")
    print()
    print("=== TODOS: Complete the following in impacted docs ===")
    for doc in IMPACTED_DOCS:
        fp = root / doc
        fp.parent.mkdir(parents=True, exist_ok=True)
        if not fp.exists():
            fp.write_text(f"# {Path(doc).stem}\\n\\n_To be completed._\\n")
        print(f"  TODO [{impact_id}] Update {doc} — reflect: {args.request}")

    # Write impact record
    impact_dir = root / ".orchestrator" / "change-impacts"
    impact_dir.mkdir(parents=True, exist_ok=True)
    impact_file = impact_dir / f"{impact_id}.json"
    impact_file.write_text(json.dumps({
        "id": impact_id,
        "request": args.request,
        "impacted_docs": IMPACTED_DOCS,
        "timestamp": datetime.utcnow().isoformat()
    }, indent=2))
    print()
    print(f"[change_impact] Impact record written to .orchestrator/change-impacts/{impact_id}.json")

if __name__ == "__main__":
    main()
"""))

# ─── run_gate.py ───────────────────────────────────────────────────────────────
(scripts_dir / "run_gate.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Execute a gate step with full enforcement of proprietary rules.\"\"\"
import argparse, json, subprocess, sys
from pathlib import Path
from datetime import datetime

VALID_STATES = {"PENDING", "IN_PROGRESS", "PASS", "FAIL", "BLOCKED"}
GATES_REQUIRING_SPEC_REF = {"G3", "G4"}
VALID_GATES = {f"G{i}" for i in range(8)}

def load_status(root):
    sf = Path(root) / ".orchestrator" / "status.json"
    if not sf.exists():
        print("ERROR: status.json missing. Run init_project_docs.py first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(sf.read_text()), sf

def save_status(sf, data):
    sf.write_text(json.dumps(data, indent=2))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--gate", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--fallback-agent", required=True)
    p.add_argument("--project-mode", required=True, choices=["greenfield", "brownfield"])
    p.add_argument("--execution-mode", required=True, choices=["autonomous", "gated"])
    p.add_argument("--research-mode", required=True, choices=["true","false"])
    p.add_argument("--task", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--validate-cmd", default="")
    p.add_argument("--ui-review-note", default="")
    p.add_argument("--spec-ref", default="")
    p.add_argument("--requires-browser-check", action="store_true")
    p.add_argument("--agent-dry-run", action="store_true")
    args = p.parse_args()

    gate = args.gate
    status = args.status
    root = Path(args.root)

    if gate not in VALID_GATES:
        print(f"ERROR: unknown gate {gate}", file=sys.stderr); sys.exit(1)
    if status not in VALID_STATES:
        print(f"ERROR: invalid status {status}", file=sys.stderr); sys.exit(1)

    # Rule: G3/G4 require --spec-ref
    if gate in GATES_REQUIRING_SPEC_REF and not args.spec_ref:
        print(f"ERROR: --spec-ref is required for {gate} tasks (implementation gates).", file=sys.stderr)
        sys.exit(1)

    # Rule: PASS requires at least one --validate-cmd
    if status == "PASS" and not args.validate_cmd:
        print("ERROR: status=PASS requires at least one --validate-cmd", file=sys.stderr)
        sys.exit(1)

    # Rule: PASS blocked when --agent-dry-run
    if status == "PASS" and args.agent_dry_run:
        print("ERROR: status=PASS is blocked when --agent-dry-run is used.", file=sys.stderr)
        sys.exit(1)

    # Rule: --requires-browser-check must include --ui-review-note
    if args.requires_browser_check and not args.ui_review_note:
        print("ERROR: --requires-browser-check requires --ui-review-note.", file=sys.stderr)
        sys.exit(1)

    # Rule: G4 PASS blocked until docs/g4-task-plan.md has no unchecked tasks
    if gate == "G4" and status == "PASS":
        g4plan = root / "docs" / "g4-task-plan.md"
        if g4plan.exists():
            content = g4plan.read_text()
            if "- [ ]" in content:
                print("ERROR: G4 PASS blocked — docs/g4-task-plan.md has unchecked tasks.", file=sys.stderr)
                sys.exit(1)

    # Run validate-cmd if provided
    validate_output = ""
    if args.validate_cmd:
        print(f"[run_gate] Running validate-cmd: {args.validate_cmd}")
        try:
            result = subprocess.run(
                args.validate_cmd, shell=True, capture_output=True, text=True, cwd=str(root)
            )
            validate_output = result.stdout + result.stderr
            print(validate_output)
            if result.returncode != 0 and status == "PASS":
                print(f"ERROR: validate-cmd failed (rc={result.returncode}). Cannot set PASS.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            validate_output = str(e)
            if status == "PASS":
                print(f"ERROR: validate-cmd exception: {e}", file=sys.stderr)
                sys.exit(1)

    # Update status.json
    data, sf = load_status(root)
    data["gates"][gate]["state"] = status
    data["gates"][gate].setdefault("notes", []).append(args.task)
    if args.spec_ref:
        data["gates"][gate]["spec_ref"] = args.spec_ref
    data["gates"][gate]["agent"] = args.agent
    data["gates"][gate]["fallback_agent"] = args.fallback_agent
    data["gates"][gate]["last_updated"] = datetime.utcnow().isoformat()
    save_status(sf, data)

    # Record validation log
    val_log = root / "docs" / "validation-log.md"
    val_log.parent.mkdir(parents=True, exist_ok=True)
    with open(val_log, "a") as f:
        f.write(f"\\n## {gate} | {status} | {datetime.utcnow().isoformat()}\\n")
        f.write(f"**Task:** {args.task}\\n")
        f.write(f"**Spec Ref:** {args.spec_ref or 'N/A'}\\n")
        f.write(f"**Validate Cmd:** {args.validate_cmd or 'N/A'}\\n")
        f.write(f"**UI Review Note:** {args.ui_review_note or 'N/A'}\\n")
        if validate_output:
            f.write(f"**Output:**\\n```\\n{validate_output.strip()}\\n```\\n")

    # Update agent-handoff.md
    handoff = root / "docs" / "agent-handoff.md"
    handoff.parent.mkdir(parents=True, exist_ok=True)
    with open(handoff, "a") as f:
        f.write(f"\\n## Handoff: {gate} | {status} | {datetime.utcnow().isoformat()}\\n")
        f.write(f"- Task: {args.task}\\n")
        f.write(f"- Agent: {args.agent} (fallback: {args.fallback_agent})\\n")
        f.write(f"- Spec Ref: {args.spec_ref or 'N/A'}\\n")

    print(f"[run_gate] {gate} set to {status} — task: {args.task}")

if __name__ == "__main__":
    main()
"""))

# ─── generate_gate_prompt.py ───────────────────────────────────────────────────
(scripts_dir / "generate_gate_prompt.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
import argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gate", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--project-mode", required=True)
    p.add_argument("--execution-mode", required=True)
    p.add_argument("--research-mode", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--spec-ref", default="")
    args = p.parse_args()
    print(f"[generate_gate_prompt] Gate={args.gate} Agent={args.agent} Task={args.task}")
    print(f"  Prompt template for {args.project_mode}/{args.execution_mode}")
    if args.spec_ref:
        print(f"  Spec preamble from: {args.spec_ref}")
if __name__ == "__main__":
    main()
"""))

# ─── progress_dashboard.py ────────────────────────────────────────────────────
(scripts_dir / "progress_dashboard.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
import argparse, json
from pathlib import Path
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    args = p.parse_args()
    sf = Path(args.root) / ".orchestrator" / "status.json"
    if not sf.exists():
        print("No status.json found"); return
    data = json.loads(sf.read_text())
    print("=== Progress Dashboard ===")
    for g, info in data.get("gates", {}).items():
        print(f"  {g}: {info.get('state','?')}")
if __name__ == "__main__":
    main()
"""))

# ─── package_skill.py ─────────────────────────────────────────────────────────
(scripts_dir / "package_skill.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
import argparse, shutil
from pathlib import Path
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--skill-dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(out / "skill"), "zip", args.skill_dir)
    print(f"[package_skill] Packaged to {out}/skill.zip")
if __name__ == "__main__":
    main()
"""))

# ─── update_docs_step.py (fallback utility) ────────────────────────────────────
(scripts_dir / "update_docs_step.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Fallback utility for recovery/manual bookkeeping only.\"\"\"
import argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--doc", required=True)
    p.add_argument("--content", required=True)
    args = p.parse_args()
    from pathlib import Path
    fp = Path(args.root) / args.doc
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "a") as f:
        f.write("\\n" + args.content + "\\n")
    print(f"[update_docs_step] Appended to {args.doc}")
if __name__ == "__main__":
    main()
"""))

# ─── run_gate.py ──────────────────────────────────────────────────────────────
# (already written above)

# ─── references ───────────────────────────────────────────────────────────────
(references_dir / "spec-driven-development.md").write_text(textwrap.dedent("""\
# Spec-Driven Development

## Spec Template

Every feature spec must contain:
- **What**: Description of what is being built
- **Why**: Business justification
- **Acceptance Criteria**: Testable pass/fail conditions
- **Constraints**: Technical and scope limits
- **Out of Scope**: Explicit exclusions

## Enforcement Rules

1. No implementation without a written spec.
2. Spec must be approved before G2.
3. All G3/G4 run_gate calls must reference the spec via --spec-ref.
4. Coding agent prompts must include spec preamble.
5. Any implementation without spec reference = automatic FAIL.

## Spec Reference Format

`docs/requirements.md#<section-anchor>`
"""))

(references_dir / "gate-checklists.md").write_text(textwrap.dedent("""\
# Gate Checklists

## G0 — Intake
- [ ] Project mission defined
- [ ] Stakeholders identified

## G1 — Planning Complete
- [ ] All questionnaire answers collected
- [ ] DoD defined
- [ ] Brownfield: as-is architecture documented

## G2 — Architecture Approved
- [ ] Architecture baseline written
- [ ] ADR-0001 authored
- [ ] Brownfield: migration strategy + risk register complete

## G3 — First Slice Delivered
- [ ] Spec exists and is approved
- [ ] Implementation references spec
- [ ] Unit tests pass

## G4 — Full Build Complete
- [ ] All g4-task-plan.md tasks checked
- [ ] Integration tests pass
- [ ] Spec acceptance criteria verified

## G5 — Security/Quality Gate
- [ ] Security scan complete
- [ ] Code review done

## G6 — Release Readiness
- [ ] Deployment notes written
- [ ] Rollback plan documented

## G7 — Handover
- [ ] Final docs review
- [ ] Backlog items captured
"""))

(references_dir / "planning-questionnaire.md").write_text(textwrap.dedent("""\
# Planning Questionnaire

Required answers before G1:
1. What is the project mission?
2. What are the top 3 user journeys?
3. What is the v1 scope?
4. What is the hosting target?
5. What is the stack preference?
6. What is the project_mode? (greenfield/brownfield)
7. What is the execution_mode? (autonomous/gated)
8. What is the definition of done?
9. What are the acceptance tests?
"""))

(references_dir / "modes.md").write_text(textwrap.dedent("""\
# Modes

## project_mode
- greenfield: Build from scratch
- brownfield: Onboard and modernize existing system

## execution_mode
- autonomous: Proceed automatically when gates pass
- gated: Pause at every gate for user approval
"""))

(references_dir / "testing-matrix.md").write_text(textwrap.dedent("""\
# Testing Matrix

Per gate progression:
- lint/type/build checks
- unit/integration/e2e (as applicable)
- API contract sanity (if API exists)
- security baseline
- docs sync verification
"""))

(references_dir / "codex-runbook.md").write_text(textwrap.dedent("""\
# Codex Runbook

## Command Patterns

Use PTY/background for long runs.
Each run executes ONE task, not the whole project.

## Validation Loop

1. verify spec exists
2. launch coding agent
3. agent updates docs
4. run verification
5. record gate status
"""))

(references_dir / "gate-prompts.md").write_text(textwrap.dedent("""\
# Gate Prompts

Use generate_gate_prompt.py to generate gate-specific prompts.
Always include spec preamble.
"""))

(references_dir / "manual-test-templates.md").write_text(textwrap.dedent("""\
# Manual Test Templates

## API endpoint smoke test
curl -s http://localhost:8080/health | jq .

## DB connectivity
python -c "import sqlite3; sqlite3.connect(':memory:').execute('SELECT 1')"
"""))

(references_dir / "research-playbook.md").write_text(textwrap.dedent("""\
# Research Playbook

When research_mode=true:
1. Produce docs/research-notes.md
2. Include architecture recommendation before G2
"""))

# ─── Distractor files (realistic legacy financial ETL project) ─────────────────
legacy_dir = WORKSPACE / "legacy-etl"
legacy_dir.mkdir(parents=True, exist_ok=True)

(legacy_dir / "pipeline.py").write_text(textwrap.dedent("""\
# Legacy ETL pipeline - DO NOT MODIFY without change review
import csv, sqlite3

def extract(filepath):
    with open(filepath) as f:
        return list(csv.DictReader(f))

def transform(rows):
    return [{k.strip().lower(): v.strip() for k,v in r.items()} for r in rows]

def load(rows, db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS trades (id TEXT, amount REAL, ccy TEXT)")
    conn.executemany("INSERT INTO trades VALUES (:id,:amount,:ccy)", rows)
    conn.commit()
"""))

(legacy_dir / "config.ini").write_text(textwrap.dedent("""\
[database]
path = /var/data/trades.db
timeout = 30

[pipeline]
batch_size = 500
retry_count = 3
source_dir = /mnt/sftp/incoming
"""))

(legacy_dir / "README_old.txt").write_text("Legacy pipeline. Written 2019. Last touched 2021.\n")

data_dir = legacy_dir / "data" / "samples"
data_dir.mkdir(parents=True, exist_ok=True)
(data_dir / "trades_jan.csv").write_text("id,amount,ccy\nT001,15000.00,USD\nT002,8500.50,EUR\n")
(data_dir / "trades_feb.csv").write_text("id,amount,ccy\nT003,22000.00,GBP\nT004,4400.00,USD\n")

tests_dir = legacy_dir / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
(tests_dir / "test_pipeline.py").write_text(textwrap.dedent("""\
def test_transform_strips_whitespace():
    from pipeline import transform
    rows = [{"  id ": "T001", " amount ": " 100 ", " ccy ": " USD "}]
    result = transform(rows)
    assert result[0]["id"] == "T001"
    assert result[0]["amount"] == "100"
"""))

(legacy_dir / "requirements.txt").write_text("pandas==1.5.3\nsqlalchemy==1.4.46\n")
(legacy_dir / "Makefile").write_text("test:\n\tpytest tests/\n\nlint:\n\tblack --check .\n")

# More distractors
infra_dir = WORKSPACE / "infra"
infra_dir.mkdir(parents=True, exist_ok=True)
(infra_dir / "deploy.sh").write_text("#!/bin/bash\necho 'deploy placeholder'\n")
(infra_dir / "terraform.tfvars").write_text('environment = "prod"\nregion      = "eu-west-1"\n')

ci_dir = WORKSPACE / ".github" / "workflows"
ci_dir.mkdir(parents=True, exist_ok=True)
(ci_dir / "ci.yml").write_text(textwrap.dedent("""\
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest legacy-etl/tests/
"""))

(WORKSPACE / "notes.txt").write_text("TODO: migrate pipeline to new platform\nTODO: update docs\n")
(WORKSPACE / "CODEOWNERS").write_text("* @platform-team\n")

print("Workspace scaffold complete.")
print(f"Workspace root: {WORKSPACE}")