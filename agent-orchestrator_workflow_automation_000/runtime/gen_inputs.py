import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ──────────────────────────────────────────────
# 1. Create the scripts/ directory with the
#    orchestrator helper scripts (pre-existing).
# ──────────────────────────────────────────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# scripts/create_agent.py
create_agent_script = '''\
#!/usr/bin/env python3
"""
create_agent.py  –  Bootstrap a new sub-agent workspace.

Usage:
    python3 scripts/create_agent.py <agent-name> --workspace <path>

Creates:
    <workspace>/<agent-name>/
        SKILL.md
        inbox/
        outbox/
        workspace/
        status.json          {"state": "pending", "started": null}
"""
import argparse
import json
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_name")
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()

    base = Path(args.workspace) / args.agent_name
    for sub in ["inbox", "outbox", "workspace"]:
        (base / sub).mkdir(parents=True, exist_ok=True)

    # Create placeholder SKILL.md (orchestrator must overwrite)
    skill_path = base / "SKILL.md"
    if not skill_path.exists():
        skill_path.write_text("# SKILL.md\\n# Orchestrator must populate this file.\\n")

    # Initialise status
    status_path = base / "status.json"
    status_path.write_text(json.dumps({"state": "pending", "started": None}, indent=2))

    print(f"[create_agent] Created agent workspace: {base}")

if __name__ == "__main__":
    main()
'''

(scripts_dir / "create_agent.py").write_text(create_agent_script)

# scripts/dissolve_agents.py
dissolve_agent_script = '''\
#!/usr/bin/env python3
"""
dissolve_agents.py  –  Archive and clean up agent workspaces.

Usage:
    python3 scripts/dissolve_agents.py --workspace <path> [--archive]

With --archive: moves each agent dir into <workspace>/_archive/
Without --archive: deletes agent workspace dirs.

Prints a summary of dissolved agents.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args()

    base = Path(args.workspace)
    archive_root = base / "_archive"
    dissolved = []

    for agent_dir in sorted(base.iterdir()):
        if not agent_dir.is_dir():
            continue
        if agent_dir.name.startswith("_"):
            continue
        status_file = agent_dir / "status.json"
        if not status_file.exists():
            continue
        try:
            state = json.loads(status_file.read_text()).get("state", "unknown")
        except Exception:
            state = "unknown"

        if args.archive:
            archive_root.mkdir(parents=True, exist_ok=True)
            dest = archive_root / agent_dir.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(agent_dir), str(dest))
            dissolved.append({"agent": agent_dir.name, "state": state, "action": "archived"})
        else:
            shutil.rmtree(agent_dir)
            dissolved.append({"agent": agent_dir.name, "state": state, "action": "deleted"})

    print(json.dumps({"dissolved": dissolved, "timestamp": datetime.utcnow().isoformat()}, indent=2))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "dissolve_agents.py").write_text(dissolve_agent_script)

# ──────────────────────────────────────────────
# 2. Create the SKILL.md for the orchestrator
# ──────────────────────────────────────────────
skill_md_content = """\
---
name: agent-orchestrator
description: |
  Meta-agent skill for orchestrating complex tasks through autonomous sub-agents. Decomposes macro tasks into subtasks, spawns specialized sub-agents with dynamically generated SKILL.md files, coordinates file-based communication, consolidates results, and dissolves agents upon completion.

  MANDATORY TRIGGERS: orchestrate, multi-agent, decompose task, spawn agents, sub-agents, parallel agents, agent coordination, task breakdown, meta-agent, agent factory, delegate tasks
---

# Agent Orchestrator

Orchestrate complex tasks by decomposing them into subtasks, spawning autonomous sub-agents, and consolidating their work.

## Core Workflow

### Phase 1: Task Decomposition

Analyze the macro task and break it into independent, parallelizable subtasks:

```
1. Identify the end goal and success criteria
2. List all major components/deliverables required
3. Determine dependencies between components
4. Group independent work into parallel subtasks
5. Create a dependency graph for sequential work
```

**Decomposition Principles:**
- Each subtask should be completable in isolation
- Minimize inter-agent dependencies
- Prefer broader, autonomous tasks over narrow, interdependent ones
- Include clear success criteria for each subtask

### Phase 2: Agent Generation

For each subtask, create a sub-agent workspace:

```bash
python3 scripts/create_agent.py <agent-name> --workspace <path>
```

This creates:
```
<workspace>/<agent-name>/
├── SKILL.md          # Generated skill file for the agent
├── inbox/            # Receives input files and instructions
├── outbox/           # Delivers completed work
├── workspace/        # Agent's working area
└── status.json       # Agent state tracking
```

**Generate SKILL.md dynamically** with:
- Agent's specific role and objective
- Tools and capabilities needed
- Input/output specifications
- Success criteria
- Communication protocol

See [references/sub-agent-templates.md](references/sub-agent-templates.md) for pre-built templates.

### Phase 3: Agent Dispatch

Initialize each agent by:

1. Writing task instructions to `inbox/instructions.md`
2. Copying required input files to `inbox/`
3. Setting `status.json` to `{"state": "pending", "started": null}`
4. Spawning the agent using the Task tool:

```python
# Spawn agent with its generated skill
Task(
    description=f"{agent_name}: {brief_description}",
    prompt=f\"""
    Read the skill at {agent_path}/SKILL.md and follow its instructions.
    Your workspace is {agent_path}/workspace/
    Read your task from {agent_path}/inbox/instructions.md
    Write all outputs to {agent_path}/outbox/
    Update {agent_path}/status.json when complete.
    \""",
    subagent_type="general-purpose"
)
```

### Phase 4: Monitoring (Checkpoint-based)

For fully autonomous agents, minimal monitoring is needed:

```python
# Check agent completion
def check_agent_status(agent_path):
    status = read_json(f"{agent_path}/status.json")
    return status.get("state") == "completed"
```

Periodically check `status.json` for each agent. Agents update this file upon completion.

### Phase 5: Consolidation

Once all agents complete:

1. **Collect outputs** from each agent's `outbox/`
2. **Validate deliverables** against success criteria
3. **Merge/integrate** outputs as needed
4. **Resolve conflicts** if multiple agents touched shared concerns
5. **Generate summary** of all work completed

```python
# Consolidation pattern
for agent in agents:
    outputs = glob(f"{agent.path}/outbox/*")
    validate_outputs(outputs, agent.success_criteria)
    consolidated_results.extend(outputs)
```

### Phase 6: Dissolution & Summary

After consolidation:

1. **Archive agent workspaces** (optional)
2. **Clean up temporary files**
3. **Generate final summary**:
   - What was accomplished per agent
   - Any issues encountered
   - Final deliverables location
   - Time/resource metrics

```python
python3 scripts/dissolve_agents.py --workspace <path> --archive
```

## File-Based Communication Protocol

See [references/communication-protocol.md](references/communication-protocol.md) for detailed specs.

**Quick Reference:**
- `inbox/` - Read-only for agent, written by orchestrator
- `outbox/` - Write-only for agent, read by orchestrator
- `status.json` - Agent updates state: `pending` → `running` → `completed` | `failed`

## Example: Research Report Task

```
Macro Task: "Create a comprehensive market analysis report"

Decomposition:
├── Agent: data-collector
│   └── Gather market data, competitor info, trends
├── Agent: analyst
│   └── Analyze collected data, identify patterns
├── Agent: writer
│   └── Draft report sections from analysis
└── Agent: reviewer
    └── Review, edit, and finalize report

Dependency: data-collector → analyst → writer → reviewer
```

## Sub-Agent Templates

Pre-built templates for common agent types in [references/sub-agent-templates.md](references/sub-agent-templates.md):

- **Research Agent** - Web search, data gathering
- **Code Agent** - Implementation, testing
- **Analysis Agent** - Data processing, pattern finding
- **Writer Agent** - Content creation, documentation
- **Review Agent** - Quality assurance, editing
- **Integration Agent** - Merging outputs, conflict resolution

## Best Practices

1. **Start small** - Begin with 2-3 agents, scale as patterns emerge
2. **Clear boundaries** - Each agent owns specific deliverables
3. **Explicit handoffs** - Use structured files for agent communication
4. **Fail gracefully** - Agents report failures; orchestrator handles recovery
5. **Log everything** - Status files track progress for debugging
"""

(workspace / "SKILL.md").write_text(skill_md_content)

# ──────────────────────────────────────────────
# 3. Create references/ directory with protocol docs
# ──────────────────────────────────────────────
refs_dir = workspace / "references"
refs_dir.mkdir(parents=True, exist_ok=True)

comm_protocol = """\
# File-Based Communication Protocol

Specification for how orchestrator and sub-agents communicate via files.

## Directory Structure

Each agent has a standardized workspace:

```
agent-workspace/
├── SKILL.md           # Agent's skill definition (read-only for agent)
├── inbox/             # Input from orchestrator → agent
│   ├── instructions.md    # Task description and requirements
│   └── [input files]      # Any files needed for the task
├── outbox/            # Output from agent → orchestrator
│   └── [deliverables]     # Task outputs
├── workspace/         # Agent's private working area
│   └── [temp files]       # Intermediate work products
└── status.json        # Agent state tracking
```

## Status File Specification

`status.json` tracks agent lifecycle:

```json
{
  "state": "pending|running|completed|failed",
  "started": "2024-01-15T10:30:00Z",
  "completed": "2024-01-15T11:45:00Z",
  "error": null,
  "progress": {
    "current_step": "analyzing_data",
    "steps_completed": 3,
    "total_steps": 5
  },
  "metrics": {
    "files_processed": 12,
    "outputs_generated": 4
  }
}
```

### State Transitions

```
pending → running → completed
                 ↘ failed
```

**State Definitions:**
- `pending`: Agent created but not yet started
- `running`: Agent actively working on task
- `completed`: Agent finished successfully
- `failed`: Agent encountered unrecoverable error

### Update Protocol

1. **Orchestrator sets** initial state to `pending`
2. **Agent updates** to `running` when starting work
3. **Agent updates** to `completed` or `failed` when done
4. **Orchestrator reads** to determine next action

## Inbox Protocol

### instructions.md Format

```markdown
# Task: {TASK_NAME}

## Objective
{Clear statement of what needs to be accomplished}

## Context
{Background information relevant to the task}

## Inputs Provided
- `input_file_1.txt` - Description of what this contains
- `data/` - Directory containing...

## Requirements
1. {Specific requirement 1}
2. {Specific requirement 2}

## Success Criteria
- [ ] {Measurable outcome 1}
- [ ] {Measurable outcome 2}

## Constraints
- {Time/resource constraints}
- {Quality standards}

## Output Expectations
- Place main deliverable in `outbox/{filename}`
- Include summary in `outbox/summary.md`
```

### File Transfer Rules

- Orchestrator copies all needed files to `inbox/`
- Agent treats `inbox/` as read-only
- Original files remain with orchestrator
- Large files: use references/paths instead of copies

## Outbox Protocol

### Required Outputs

Every agent must produce at minimum:
1. **Primary deliverable(s)** - The actual work product
2. **summary.md** - Brief summary of what was done

### Optional Outputs

- `changelog.md` - Detailed log of actions taken
- `issues.md` - Problems encountered and how resolved
- `metadata.json` - Structured data about outputs

### Output Naming Convention

```
outbox/
├── {primary_deliverable}.{ext}
├── summary.md
├── data/           # If multiple data outputs
│   ├── file1.csv
│   └── file2.json
└── metadata.json
```

## Workspace Protocol

The `workspace/` directory is the agent's private area:

- **Agent can create** any files needed for processing
- **Orchestrator ignores** this directory during collection
- **Cleanup optional** - agents may leave or clean workspace
- **Useful for** intermediate results, caches, temp files

## Error Handling

### Failure Protocol

When an agent fails:

1. Update `status.json`:
```json
{
  "state": "failed",
  "error": {
    "type": "ValidationError",
    "message": "Input file format invalid",
    "details": "Expected CSV, got JSON",
    "recoverable": true
  }
}
```

2. Write `outbox/error_report.md`:
```markdown
# Error Report

## Error Type
ValidationError

## Description
Input file format was invalid. Expected CSV format but received JSON.

## Attempted Recovery
Tried to convert JSON to CSV but data structure incompatible.

## Suggested Resolution
Provide input as CSV with columns: id, name, value

## Partial Work
Any completed work before failure is in outbox/partial/
```

### Recovery Options

Orchestrator can:
1. **Retry** - Re-run with same inputs
2. **Fix and retry** - Correct inputs and re-run
3. **Skip** - Mark as failed, continue with other agents
4. **Escalate** - Request human intervention

## Dependency Handling

When agents depend on each other's outputs:

### Manifest File

Orchestrator creates `inbox/dependencies.json`:

```json
{
  "depends_on": [
    {
      "agent": "data-collector",
      "outputs": ["outbox/data.json", "outbox/sources.md"],
      "copy_to": "inbox/source_data/"
    }
  ],
  "wait_for": ["data-collector", "schema-validator"]
}
```

### Sequential Execution

```python
# Orchestrator pattern for dependencies
def execute_with_dependencies(agent, dependencies):
    # Wait for all dependencies
    for dep in dependencies:
        while not is_completed(dep):
            wait()

    # Copy dependency outputs to agent inbox
    for dep in dependencies:
        copy_outputs(dep.outbox, agent.inbox)

    # Start agent
    spawn_agent(agent)
```

## Parallel Execution

Independent agents can run simultaneously:

```python
# Spawn all independent agents at once
parallel_agents = identify_independent_agents(task_graph)
for agent in parallel_agents:
    spawn_agent(agent)  # Non-blocking

# Wait for all to complete
while not all_completed(parallel_agents):
    check_status_periodically()
```

## Message Passing Pattern

For complex inter-agent communication:

### Shared Message Queue (Optional)

```
orchestrator-workspace/
└── messages/
    ├── {agent-a}_to_{agent-b}_001.json
    └── {agent-b}_to_{agent-a}_002.json
```

Message format:
```json
{
  "from": "agent-a",
  "to": "agent-b",
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "data_ready|question|answer|update",
  "content": { ... }
}
```

Note: For fully autonomous agents, prefer one-directional communication via inbox/outbox over message passing.
"""

(refs_dir / "communication-protocol.md").write_text(comm_protocol)

sub_agent_templates = """\
# Sub-Agent Templates

Pre-built SKILL.md templates for common agent types. Copy and customize as needed.

## Table of Contents

1. [Research Agent](#research-agent)
2. [Code Agent](#code-agent)
3. [Analysis Agent](#analysis-agent)
4. [Writer Agent](#writer-agent)
5. [Review Agent](#review-agent)
6. [Integration Agent](#integration-agent)

---

## Research Agent

```yaml
---
name: research-agent-{task_id}
description: |
  Autonomous research agent for gathering and organizing information.
---

# Research Agent

## Objective
{INSERT_OBJECTIVE}

## Tools Available
- Read: Read local files for context

## Workflow
1. Read `inbox/instructions.md`
2. Update `status.json` to `{"state": "running"}`
3. Execute research
4. Write `outbox/findings.md` and `outbox/summary.md`
5. Update `status.json` to `{"state": "completed"}`

## Success Criteria
- All required topics covered
- Findings organized and actionable

## Communication Protocol
- Read from: `inbox/`
- Write to: `outbox/`
- Status: `status.json`
```

---

## Code Agent

```yaml
---
name: code-agent-{task_id}
description: |
  Autonomous coding agent for implementation tasks.
---

# Code Agent

## Objective
{INSERT_OBJECTIVE}

## Tools Available
- Read/Write/Edit: File operations
- Bash: Execute commands, run tests

## Workflow
1. Read `inbox/instructions.md`
2. Update `status.json` to `{"state": "running"}`
3. Write implementation
4. Write `outbox/changelog.md` and `outbox/summary.md`
5. Update `status.json` to `{"state": "completed"}`

## Success Criteria
- All tests passing
- Clear documentation

## Communication Protocol
- Read from: `inbox/`
- Write to: `outbox/`
- Status: `status.json`
```

---

## Analysis Agent

```yaml
---
name: analysis-agent-{task_id}
description: |
  Autonomous analysis agent for processing data and generating insights.
---

# Analysis Agent

## Objective
{INSERT_OBJECTIVE}

## Tools Available
- Read: Read data files
- Bash: Run Python/analysis scripts
- Write: Output results

## Workflow
1. Read `inbox/instructions.md`
2. Read `inbox/data/` for input data
3. Update `status.json` to `{"state": "running"}`
4. Execute analysis
5. Write `outbox/analysis.md`, `outbox/insights.md`, `outbox/summary.md`
6. Update `status.json` to `{"state": "completed"}`

## Success Criteria
- All data processed accurately
- Insights are actionable

## Communication Protocol
- Read from: `inbox/`
- Write to: `outbox/`
- Status: `status.json`
```

---

## Writer Agent

```yaml
---
name: writer-agent-{task_id}
description: |
  Autonomous writing agent for creating documents and content.
---

# Writer Agent

## Objective
{INSERT_OBJECTIVE}

## Tools Available
- Read: Read input materials
- Write: Create content files

## Workflow
1. Read `inbox/instructions.md`
2. Update `status.json` to `{"state": "running"}`
3. Draft content
4. Write `outbox/draft.md` and `outbox/summary.md`
5. Update `status.json` to `{"state": "completed"}`

## Success Criteria
- Appropriate length
- Clear and well-organized

## Communication Protocol
- Read from: `inbox/`
- Write to: `outbox/`
- Status: `status.json`
```

---

## Review Agent

```yaml
---
name: review-agent-{task_id}
description: |
  Autonomous review agent for quality assurance and editing.
---

# Review Agent

## Objective
{INSERT_OBJECTIVE}

## Tools Available
- Read: Read content to review
- Write/Edit: Make corrections

## Workflow
1. Read `inbox/instructions.md`
2. Update `status.json` to `{"state": "running"}`
3. Execute review
4. Write `outbox/feedback.md`, `outbox/approved.json`, `outbox/summary.md`
5. Update `status.json` to `{"state": "completed"}`

## Success Criteria
- Issues clearly documented
- Clear approve/reject decision

## Communication Protocol
- Read from: `inbox/`
- Write to: `outbox/`
- Status: `status.json`
```

---

## Integration Agent

```yaml
---
name: integration-agent-{task_id}
description: |
  Autonomous integration agent for merging and consolidating work.
---

# Integration Agent

## Objective
{INSERT_OBJECTIVE}

## Tools Available
- Read: Read from multiple sources
- Write: Create unified outputs
- Bash: Run merge/diff tools

## Workflow
1. Read `inbox/instructions.md`
2. Read `inbox/manifest.json`
3. Update `status.json` to `{"state": "running"}`
4. Execute integration
5. Write `outbox/merge_report.md` and `outbox/summary.md`
6. Update `status.json` to `{"state": "completed"}`

## Success Criteria
- All inputs successfully merged
- No data loss

## Communication Protocol
- Read from: `inbox/`, other agent `outbox/` directories
- Write to: `outbox/`
- Status: `status.json`
```

---

## Customization Guide

When using these templates:
1. **Replace placeholders**: `{task_id}`, `{INSERT_OBJECTIVE}`
2. **Adjust tools**: Add/remove based on actual needs
3. **Customize outputs**: Match your consolidation expectations
4. **Add constraints**: Include any domain-specific rules
5. **Set success criteria**: Make them measurable and specific
"""

(refs_dir / "sub-agent-templates.md").write_text(sub_agent_templates)

# ──────────────────────────────────────────────
# 4. Create the legacy fintech codebase to audit
#    (messy, realistic inputs)
# ──────────────────────────────────────────────
legacy_dir = workspace / "legacy_payment_system"
legacy_dir.mkdir(parents=True, exist_ok=True)

# auth module
auth_dir = legacy_dir / "auth"
auth_dir.mkdir(parents=True, exist_ok=True)

(auth_dir / "login.py").write_text("""\
import hashlib, os

SECRET_KEY = "supersecret123"   # TODO: move to env
DB_PASSWORD = "admin1234"       # hardcoded — PCI-DSS violation

def authenticate(username, password):
    # MD5 is used for speed — legacy decision
    hashed = hashlib.md5(password.encode()).hexdigest()
    return hashed == "5f4dcc3b5aa765d61d8327deb882cf99"

def generate_token(user_id):
    return hashlib.md5(str(user_id).encode()).hexdigest()
""")

(auth_dir / "session.py").write_text("""\
import time

SESSION_TIMEOUT = 99999999   # effectively never expires — security risk

sessions = {}

def create_session(user_id):
    token = str(user_id) + str(time.time())
    sessions[token] = {"user_id": user_id, "created": time.time()}
    return token

def validate_session(token):
    # No expiry check performed
    return token in sessions
""")

# payment module
payment_dir = legacy_dir / "payment"
payment_dir.mkdir(parents=True, exist_ok=True)

(payment_dir / "processor.py").write_text("""\
import time, random

def process_payment(amount, card_number, cvv):
    # card_number and cvv logged to console — PCI-DSS violation
    print(f"Processing card {card_number} CVV {cvv} amount {amount}")
    time.sleep(random.uniform(0.5, 3.0))  # simulated delay — no timeout cap
    if amount > 10000:
        # no rate limiting — potential fraud vector
        pass
    return {"status": "approved", "ref": random.randint(100000, 999999)}

def refund(transaction_id, amount):
    # No authorization check — anyone can refund
    print(f"Refunding {amount} for tx {transaction_id}")
    return True
""")

(payment_dir / "card_store.py").write_text("""\
# Card data stored in plaintext CSV — major PCI-DSS violation
CARD_FILE = "/tmp/cards.csv"

def store_card(user_id, card_number, cvv, expiry):
    with open(CARD_FILE, "a") as f:
        f.write(f"{user_id},{card_number},{cvv},{expiry}\\n")

def load_cards(user_id):
    cards = []
    try:
        with open(CARD_FILE) as f:
            for line in f:
                uid, cn, cvv, exp = line.strip().split(",")
                if uid == str(user_id):
                    cards.append({"card": cn, "cvv": cvv, "exp": exp})
    except FileNotFoundError:
        pass
    return cards
""")

# reporting module
report_dir = legacy_dir / "reporting"
report_dir.mkdir(parents=True, exist_ok=True)

(report_dir / "daily_report.py").write_text("""\
import sqlite3, time

def generate_daily_report(date_str):
    # N+1 query problem — one DB call per transaction
    conn = sqlite3.connect("/tmp/payments.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions WHERE date=?", (date_str,))
    tx_ids = [row[0] for row in cursor.fetchall()]
    results = []
    for tx_id in tx_ids:
        # Separate query per transaction — O(n) DB calls
        cursor.execute("SELECT * FROM transactions WHERE id=?", (tx_id,))
        results.append(cursor.fetchone())
    conn.close()
    return results
""")

(report_dir / "audit_log.py").write_text("""\
import json, os

LOG_FILE = "/tmp/audit.log"

def log_action(user_id, action, details):
    # Logs written synchronously with no rotation — disk exhaustion risk
    entry = {"user": user_id, "action": action, "details": details}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\\n")

def get_logs(user_id=None):
    # Full file scan every time — no indexing
    logs = []
    try:
        with open(LOG_FILE) as f:
            for line in f:
                entry = json.loads(line)
                if user_id is None or entry["user"] == user_id:
                    logs.append(entry)
    except FileNotFoundError:
        pass
    return logs
""")

# infrastructure
infra_dir = legacy_dir / "infra"
infra_dir.mkdir(parents=True, exist_ok=True)

(infra_dir / "config.py").write_text("""\
# Centralised config — but everything is hardcoded
DATABASE_URL = "postgresql://admin:password123@prod-db.internal:5432/payments"
REDIS_URL = "redis://:nopassword@prod-cache.internal:6379"
SMTP_PASSWORD = "mailpass456"
ENCRYPTION_KEY = "0000000000000000"   # 16 zero bytes — trivially weak
DEBUG = True  # left on in production
""")

(infra_dir / "middleware.py").write_text("""\
def rate_limit_middleware(request):
    # Rate limiting disabled for 'performance' — vulnerability
    return True

def cors_middleware(request):
    # Wildcard CORS — allows any origin
    return {"Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"}
""")

# tests (sparse)
tests_dir = legacy_dir / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)

(tests_dir / "test_auth.py").write_text("""\
# Only happy-path tests — no security or edge-case coverage
def test_login_success():
    from auth.login import authenticate
    # Only tests the known hash, not injection or brute-force
    assert authenticate("admin", "password") == True
""")

(tests_dir / "test_payment.py").write_text("""\
# Missing tests for: refund auth, large amounts, card storage
def test_process_small_payment():
    pass  # not implemented
""")

# Additional distractor files to increase realism
(legacy_dir / "README_OLD.txt").write_text("Legacy payment system v1.2 - do not use in production\n")
(legacy_dir / "CHANGELOG.md").write_text("## v1.2\n- Added card storage\n- Performance tweaks\n\n## v1.1\n- Initial release\n")
(legacy_dir / "requirements.txt").write_text("flask==1.1.4\nsqlite3\nrequests==2.25.0\n")
(legacy_dir / ".env.example").write_text("DATABASE_URL=postgresql://user:pass@localhost/db\n")

# More distractor files at workspace root
(workspace / "project_notes.txt").write_text("Meeting notes: need to audit the payment system ASAP.\nCompliance deadline: end of quarter.\n")
(workspace / "old_orchestration_attempt.py").write_text("# This script was never finished\n# TODO: figure out how to spawn agents\n")
(workspace / "team_contacts.csv").write_text("name,role,email\nAlice,Lead Engineer,alice@fintech.example\nBob,Compliance,bob@fintech.example\n")

# ──────────────────────────────────────────────
# 5. Create the agents/ directory that should
#    be the agent workspace root (empty — agent
#    must create sub-agents here)
# ──────────────────────────────────────────────
agents_dir = workspace / "agents"
agents_dir.mkdir(parents=True, exist_ok=True)

# Deliberately leave agents/ empty so the agent has to populate it.
# Drop a single misleading file to increase difficulty.
(agents_dir / ".gitkeep").write_text("")

print("Workspace generated successfully.")
print(f"Root: {workspace}")