#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the moses-roles governance onboarding task.
Creates a realistic, deeply nested directory structure with distractor files,
a partially-configured governance environment, and the pre-existing audit_stub.py.
"""

import os
import json
import stat
import random
from pathlib import Path

random.seed(42)

# ── Base directories ───────────────────────────────────────────────────────────
HOME = Path(os.path.expanduser("~"))
WORKSPACE = Path("/workspace")

# Governance state dir (declared in stateDirs, must exist but state.json is MISSING)
GOVERNANCE_DIR = HOME / ".openclaw" / "governance"
GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)

# Workspace dir
OPENCLAW_WORKSPACE = HOME / ".openclaw" / "workspace"
OPENCLAW_WORKSPACE.mkdir(parents=True, exist_ok=True)

# Skills dir with moses-governance bundle
SKILLS_DIR = OPENCLAW_WORKSPACE / "skills" / "moses-governance" / "scripts"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# ── Create audit_stub.py (pre-existing, as stated in SKILL.md) ────────────────
AUDIT_STUB = SKILLS_DIR / "audit_stub.py"
AUDIT_STUB.write_text("""\
#!/usr/bin/env python3
\"\"\"
MO§ES™ Audit Stub — moses-governance bundle
Logs governance events to ~/.openclaw/governance/audit_log.jsonl
\"\"\"
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="MO§ES Audit Logger")
    subparsers = parser.add_subparsers(dest="command")

    log_parser = subparsers.add_parser("log", help="Log a governance event")
    log_parser.add_argument("--action", required=True, help="Action type")
    log_parser.add_argument("--detail", required=True, help="Detail string")
    log_parser.add_argument("--agent", default="system", help="Agent identifier")

    args = parser.parse_args()

    if args.command != "log":
        print("Error: only 'log' subcommand is supported", file=sys.stderr)
        sys.exit(1)

    log_dir = Path(os.path.expanduser("~/.openclaw/governance"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "audit_log.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": args.action,
        "detail": args.detail,
        "agent": args.agent,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\\n")

    print(f"[audit_stub] Logged: action={args.action!r} detail={args.detail!r}")

if __name__ == "__main__":
    main()
""")
AUDIT_STUB.chmod(AUDIT_STUB.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Create a BROKEN/INCOMPLETE state.json (wrong schema, missing keys) ─────────
# The agent must REPLACE this with the correct structure.
BROKEN_STATE = GOVERNANCE_DIR / "state.json"
BROKEN_STATE.write_text(json.dumps({
    "version": "0.1",
    "last_updated": "2024-01-01",
    "active_mode": None,
    "notes": "placeholder — not yet configured"
}, indent=2))

# ── Create a stub AGENTS.md with wrong/incomplete content ─────────────────────
AGENTS_MD = OPENCLAW_WORKSPACE / "AGENTS.md"
AGENTS_MD.write_text("""\
# Agent Configuration
# TODO: fill in role definitions

Primary: TBD
Secondary: TBD
Observer: TBD
""")

# ── Distractor directory tree ─────────────────────────────────────────────────
# Simulate a realistic financial-services AI project with many irrelevant files.

distractor_structure = {
    WORKSPACE / "projects" / "doc_review" / "pipeline": [
        ("config.yaml", "pipeline:\n  version: 2\n  workers: 4\n  timeout: 300\n"),
        ("run_pipeline.sh", "#!/bin/bash\necho 'Starting doc review pipeline'\n"),
        ("requirements.txt", "langchain==0.1.0\nopenai==1.0.0\nfaiss-cpu==1.7.4\n"),
    ],
    WORKSPACE / "projects" / "doc_review" / "models": [
        ("embedding_config.json", json.dumps({"model": "text-embedding-ada-002", "dim": 1536}, indent=2)),
        ("classifier_weights.txt", "# placeholder for weights path\n/mnt/models/clf_v3.bin\n"),
    ],
    WORKSPACE / "projects" / "doc_review" / "data" / "raw": [
        ("sample_contract_001.txt", "THIS AGREEMENT is entered into as of January 1, 2024...\n"),
        ("sample_contract_002.txt", "WHEREAS, the parties desire to set forth their agreement...\n"),
        ("review_queue.csv", "id,filename,status,reviewer\n1,contract_001.txt,pending,\n2,contract_002.txt,pending,\n"),
    ],
    WORKSPACE / "projects" / "doc_review" / "data" / "processed": [
        ("extracted_clauses.jsonl", '{"id":1,"clause":"indemnification","text":"..."}\n'),
        ("risk_flags.json", json.dumps({"high": [], "medium": ["clause_3"], "low": ["clause_7"]}, indent=2)),
    ],
    WORKSPACE / "projects" / "compliance" / "policies": [
        ("aml_policy_v2.txt", "Anti-Money Laundering Policy\nVersion 2.0\n..."),
        ("kyc_checklist.md", "# KYC Checklist\n- [ ] ID verification\n- [ ] Address proof\n"),
        ("sanctions_list_partial.csv", "name,country,flag_date\nACME Corp,XX,2023-05-01\n"),
    ],
    WORKSPACE / "projects" / "compliance" / "reports": [
        ("q4_2023_audit_summary.pdf.txt", "Q4 2023 Audit Summary\nFindings: 3 minor, 0 major\n"),
        ("remediation_tracker.xlsx.txt", "Item,Owner,Due,Status\nFinding-1,Alice,2024-03-01,Open\n"),
    ],
    WORKSPACE / "infra" / "docker": [
        ("Dockerfile.review", "FROM python:3.11-slim\nRUN pip install langchain\n"),
        ("compose.yml", "version: '3.8'\nservices:\n  reviewer:\n    build: .\n"),
    ],
    WORKSPACE / "infra" / "k8s": [
        ("deployment.yaml", "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: doc-reviewer\n"),
        ("service.yaml", "apiVersion: v1\nkind: Service\nmetadata:\n  name: doc-reviewer-svc\n"),
    ],
    WORKSPACE / "scripts": [
        ("bootstrap.sh", "#!/bin/bash\necho 'Bootstrapping environment...'\n"),
        ("migrate_db.py", "#!/usr/bin/env python3\n# DB migration placeholder\nprint('migrating...')\n"),
        ("health_check.py", "#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n"),
    ],
    WORKSPACE / "docs" / "architecture": [
        ("system_overview.md", "# System Overview\nThe document review system uses a 3-tier architecture...\n"),
        ("data_flow.md", "# Data Flow\nRaw docs → Preprocessing → Embedding → Classification → Review\n"),
        ("agent_design_OLD.md", "# Legacy Agent Design\nSingle-agent approach — deprecated Q2 2024\n"),
    ],
    WORKSPACE / "docs" / "runbooks": [
        ("incident_response.md", "# Incident Response\n1. Page on-call\n2. Assess severity\n3. Escalate if P1\n"),
        ("deployment_guide.md", "# Deployment Guide\nSee infra/k8s for manifests.\n"),
    ],
}

for dirpath, files in distractor_structure.items():
    dirpath.mkdir(parents=True, exist_ok=True)
    for fname, content in files:
        fpath = dirpath / fname
        fpath.write_text(content)

# ── Write a task brief that the agent sees ────────────────────────────────────
# This gives business context without leaking SKILL.md rules.
BRIEF = WORKSPACE / "TASK_BRIEF.txt"
BRIEF.write_text("""\
=== GOVERNANCE ONBOARDING — DOCUMENT REVIEW AI SYSTEM ===

Context:
Our financial document review platform is deploying a coordinated multi-agent
AI system governed by the MO§ES™ Role Hierarchy framework. The framework has
been partially scaffolded but is not yet functional.

Your job is to complete the governance setup so the system can go live.

Deliverables:
1. The shared governance state file must be properly populated so all agents
   can load it before responding.

2. The agent coordination manifest must contain the exact role definitions
   required by the governance framework for all three roles.

3. During pre-launch testing, the Observer agent responded before Primary and
   Secondary had completed — a sequencing violation. This incident must be
   formally recorded using the audit logging system, referencing "Observer"
   as the agent that responded out of turn.

The framework skill documentation is available via the moses-roles skill.
All required scripts are already installed.
""")

print("Workspace generated successfully.")
print(f"  Governance dir:   {GOVERNANCE_DIR}")
print(f"  Audit stub:       {AUDIT_STUB}")
print(f"  Broken state:     {BROKEN_STATE}")
print(f"  Stub AGENTS.md:   {AGENTS_MD}")
print(f"  Task brief:       {BRIEF}")