import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── 1. Create the skills/buffer SKILL.md (the agent's instruction manual) ──────
os.makedirs(f"{workspace}/skills/buffer", exist_ok=True)

buffer_skill_md = r"""---
name: buffer
description: "Session management for OpenClaw agents. Context monitoring, structured handoffs, and performance optimization — so you never lose context again."
---

# Buffer

## First Run

Check if `buffer-optimizer` exists as a sibling skill directory. Look for `skills/buffer-optimizer/SKILL.md` relative to your workspace.

**If it does NOT exist**, extract it now:

1. Create directory `skills/buffer-optimizer/`
2. Write `skills/buffer-optimizer/SKILL.md` with the exact contents of the **Embedded: buffer-optimizer** section below.
3. If the skill references shell scripts (`{baseDir}/scripts/measure-boot.sh` and `{baseDir}/scripts/audit-agents-md.sh`), create those too from the **Embedded Scripts** section.
4. Run the **Setup** steps from the embedded optimizer (create HANDOFF.md if missing, validate MEMORY.md, check AGENTS.md structure).
5. Tell the owner what was set up and that workspace audits are now available via `buffer-optimizer`.

**If extraction fails** (sandbox, read-only filesystem, write tool denied):
- Tell the owner: "I can't write files to the skills directory. Install the optimizer separately: `clawhub install buffer-optimizer`"
- Continue with normal session management below.

**If buffer-optimizer already exists**, skip extraction. Proceed to the mode that matches your situation.

---

## Start

Run at every new session. Goal: recover context instantly.

1. Read HANDOFF.md — where you left off, outcomes, next steps.
2. Read MEMORY.md — priorities, projects, people.
3. Start working. Do not read other files unless the task requires them.

**No HANDOFF.md?** Check recent `memory/*.md` files, try `memory_search`, then ask the owner. Run `buffer-optimizer` to set up your workspace.

---

## Monitor

Apply continuously during the session.

### Intake
Before loading content:
- **Changed?** Don't re-read unmodified files.
- **Need all of it?** Use `grep`, `head`, `limit`/`offset` over full reads.
- **Can reference instead?** Write large output to file, read summary.
- **Cache impact?** Don't edit AGENTS.md/SOUL.md/USER.md/MEMORY.md mid-session (breaks prompt cache, 10x cost).

### Output
- Redirect heavy output (>20 lines) to `/tmp`, read tail/summary.
- Pipe long commands through `tail`/`head`/`grep`.

### Context Thresholds

Thresholds are percentages of your model's context window. Run `session_status` — the Context line shows current usage.

| Usage | Action |
|---|---|
| **<25%** | No concern. Full performance. |
| **25-40%** | Be intentional about what you load. |
| **40-50%** | ⚠️ Warn owner. Degradation begins on complex tasks. |
| **>50%** | 🔴 Wrap now. |

### Degradation signals — warn the owner and recommend wrapping if you notice:
- Repeating yourself (context distraction)
- Forgetting earlier decisions (retrieval failure)
- Ignoring relevant earlier context (recency bias)
- Confusion from conflicting information (context clash)
- Referencing something that was wrong earlier (context poisoning)

Do not wrap unilaterally — warn first, let the owner decide when to wrap.

### Continuous persistence
Don't wait for wrap to save important information. As decisions happen, append key outcomes to HANDOFF.md or a scratch file. If you have a long-term memory system, write decisions there immediately.

Test: if this session crashed now, would important stuff survive?

---

## Wrap

Run when: owner says "wrap session", you hit 50% context, or conversation concludes.

### Step 1: Extract from the session
Scan for: decisions, outcomes, open questions, corrections, next steps.

### Step 2: Write HANDOFF.md
Overwrite with current state:

```markdown
# HANDOFF.md

## Current Work
[One line — focus area.]

## Stopping Point
[One line — where you left off.]

## Key Outcomes
- [Conclusions, not activities. "X works because Y" not "tested X".]

## Open Questions
- [Each must be actionable by the next session.]

## Next Steps
1. [Most important first. ≤5 items.]
```

**Rules:**
- ≤2KB. Over? Compress outcomes to conclusions only.
- Outcomes = conclusions, not activities.
- Cut anything that doesn't affect future work.
- No architecture docs, standing policies, or issue lists.

### Step 3: Update MEMORY.md only if structure changed
New project, priority shift, new key person, or week rollover. Most sessions: don't touch it.

### Step 4: Persist unpersisted decisions
Scan for decisions or outcomes not yet captured in HANDOFF.md.

### Step 5: Confirm to owner
What was saved. Whether MEMORY.md was updated. Top next step.

---

## Quick Reference

| File | Purpose | Target | Updated |
|---|---|---|---|
| HANDOFF.md | Session state — recovery file | ≤2KB | Every wrap |
| MEMORY.md | Big picture — priorities, projects, people | ≤1.5KB | When structure changes |
| AGENTS.md | Behavioral rules | ≤4KB | Rarely |

| Zone | Range | Behavior |
|---|---|---|
| Green | <25% | Full performance |
| Yellow | 25-40% | Intentional loading |
| Orange | 40-50% | Warn owner, prepare to wrap |
| Red | >50% | Wrap immediately |

---

## Embedded: buffer-optimizer

On first run, write this as `skills/buffer-optimizer/SKILL.md`:

```
---
name: buffer-optimizer
description: "Workspace auditing and setup for Buffer. Measures boot payload, checks AGENTS.md structure, classifies skills, validates memory files. Run on first install, when things feel off, or every week or two. Companion to the buffer skill."
---

# Buffer Optimizer

Two modes: **setup** (first install) and **audit** (periodic maintenance).

---

## Setup

Run on first install, or when the owner asks to configure their workspace.

### 1. Create HANDOFF.md
If missing, create:

# HANDOFF.md
## Current Work
## Stopping Point
## Key Outcomes
## Open Questions
## Next Steps

### 2. Validate MEMORY.md
Must contain only: this week (2-3 lines), priorities (≤5), project states (one line each), key people. Target: ≤1.5KB. If missing, create a minimal version with the owner's name and current focus.

### 3. Check AGENTS.md structure
Verify these exist. If missing, draft them and present to owner for approval:

**Pre-response checkpoint** (must be the first section):

## Before Every Response
1. Does this message match a skill trigger? → Load that skill.
2. Am I about to do something a skill already handles? → Use the skill.

**Skill trigger table** (immediately after checkpoint):

## Skill Triggers
| Event | Skill |
|---|---|
| [event] | [skill-name] |

**Negative triggers:**

## Don't Reinvent Skills
- [manual pattern] → Use [skill-name]

**Context management rules:**

## Context Management
- Heavy output (>20 lines): redirect to file, read summary.
- Use targeted reads (limit/offset, grep, tail) over full file loads.
- 40-50% context: Warn owner. >50%: Wrap immediately.
- Don't edit boot files mid-session (breaks prompt cache, 10x cost).

### 4. Classify skills
List all loaded skills. Classify as DAILY/WEEKLY/RARE/NEVER. Draft a daily driver list. Flag NEVER skills for potential exclusion.

### 5. Report setup status
Tell the owner what was created, what was validated, and what needs their review.

---

## Audit

Run periodically (weekly or bi-weekly), after major changes, or when the owner asks.

### Step 1: Measure Boot Payload

Run `bash {baseDir}/scripts/measure-boot.sh` if the script exists. Otherwise measure manually.

#### Thresholds

| File | Target | Action if exceeded |
|---|---|---|
| AGENTS.md | ≤4KB | Convert descriptions to directives. Move reference content out. |
| MEMORY.md | ≤1.5KB | Keep only: this week, priorities, projects, people. |
| HANDOFF.md | ≤2KB | Apply template: current work, stopping point, outcomes, questions, next steps. |
| Each memory/*.md | ≤2KB | Summarize transcripts. |
| Total boot | ≤12KB | Something doesn't belong in boot. |
| Skills loaded | <20 | Exclude unused skills (~75 tokens each). |

### Step 2: Audit AGENTS.md

Run `bash {baseDir}/scripts/audit-agents-md.sh` if the script exists. Otherwise check manually.

Verify:
- 2.1 Pre-response checkpoint is the first section.
- 2.2 Skill trigger table immediately follows.
- 2.3 Negative triggers section exists.
- 2.4 No weak patterns ("You have access to", "Consider", "Try to", "If appropriate" → rewrite as imperatives).
- 2.5 Sections grouped by trigger, not topic.

### Step 3: Audit Skills

- Count skills from available_skills in system prompt.
- Classify each: DAILY / WEEKLY / RARE / NEVER.
- Draft daily driver list for AGENTS.md.
- Draft exclusion list. Present to owner — do not exclude unilaterally.

### Step 4: Audit Memory Files

- MEMORY.md — only: this week, priorities, projects, people. Flag old history, architecture, URLs.
- HANDOFF.md — only: current work, stopping point, outcomes, questions, next steps. Outcomes = conclusions, not activities.
- memory/*.md — over 2KB → summarize. Over 3 days → archive. Duplicates → remove.
- Ghost files — flag any .md in workspace root not in: AGENTS.md, SOUL.md, USER.md, MEMORY.md, HANDOFF.md, IDENTITY.md.

### Step 5: Check Reliability

- Compaction flush: Enabled? If unknown, flag.
- Wrap ritual: Does buffer skill exist? If missing, recommend install.
- Automated persistence: Write hooks, observers, auto-commit? If none, flag as priority gap.

### Step 6: Self-Tests

- Recovery: Read HANDOFF.md — does it reflect current state?
- Skill bypass: Did you recently do manually what a daily driver skill handles?
- Drift: Re-read AGENTS.md. Flag any instruction you're not following.

### Step 7: Report

## Buffer Audit Report — [date]

### Boot Payload
- Total: X bytes (~Y tokens) [PASS/OVER 12KB]
- [file-by-file with pass/fail]

### AGENTS.md Structure
- Pre-response checkpoint: [YES/NO]
- Skill triggers first: [YES/NO]
- Negative triggers: [YES/NO]
- Weak patterns: [count]
- Organization: [trigger/topic]

### Skills
- Loaded: N (target: <20)
- Daily drivers: [list]
- Exclusion candidates: [list] (~X tokens saved)

### Memory
- MEMORY.md: X bytes [PASS/OVER]
- HANDOFF.md: X bytes [PASS/OVER]
- Ghost files: [list or none]
- Files needing work: [list or none]

### Reliability
- Compaction flush: [enabled/disabled/unknown]
- Wrap ritual: [exists/missing]
- Persistence: [exists/missing]

### Self-Tests
- Recovery: [yes/no]
- Skill bypasses: [list or none]
- Drift: [list or none]

### Proposed Changes
1. [Change] — [rationale]. Saves ~X tokens.

Wait for owner approval before implementing.
```

---

## Embedded Scripts

If shell access is available, also create these scripts in `skills/buffer-optimizer/scripts/`:

### measure-boot.sh
```bash
#!/bin/bash
set -e
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
echo "=== BOOT FILE SIZES ==="
total=0
for f in AGENTS.md SOUL.md USER.md MEMORY.md HANDOFF.md IDENTITY.md; do
  path="$WORKSPACE/$f"
  if [ -f "$path" ]; then
    size=$(wc -c < "$path")
    lines=$(wc -l < "$path")
    tokens=$((size / 4))
    total=$((total + size))
    printf "  %-15s %6d bytes  %4d lines  ~%5d tokens\n" "$f" "$size" "$lines" "$tokens"
  fi
done
echo "  ---"
printf "  %-15s %6d bytes              ~%5d tokens\n" "TOTAL" "$total" "$((total / 4))"
echo ""
echo "=== MEMORY FILES ==="
mem_count=$(ls "$WORKSPACE"/memory/*.md 2>/dev/null | wc -l | tr -d ' ')
mem_bytes=$(wc -c "$WORKSPACE"/memory/*.md 2>/dev/null | tail -1 | awk '{print $1}')
echo "  Files: $mem_count"
echo "  Total: ${mem_bytes:-0} bytes"
echo ""
echo "=== SKILLS ==="
builtin_dir="/opt/homebrew/lib/node_modules/openclaw/skills"
custom_dir="$WORKSPACE/skills"
builtin_count=$(ls "$builtin_dir" 2>/dev/null | wc -l | tr -d ' ')
custom_count=$(ls "$custom_dir" 2>/dev/null | wc -l | tr -d ' ')
echo "  Built-in: $builtin_count"
echo "  Custom: $custom_count"
echo "  Total: $((builtin_count + custom_count))"
echo ""
echo "=== GHOST FILE CHECK ==="
recognized="AGENTS.md SOUL.md USER.md MEMORY.md HANDOFF.md IDENTITY.md"
for f in "$WORKSPACE"/*.md; do
  name=$(basename "$f")
  if ! echo "$recognized" | grep -qw "$name"; then
    echo "  GHOST: $name — NOT auto-loaded by OpenClaw"
  fi
done
echo ""
echo "=== THRESHOLDS ==="
check() {
  local name="$1" size="$2" limit="$3"
  if [ "$size" -gt "$limit" ]; then
    echo "  FAIL $name: ${size}B > ${limit}B limit"
  else
    echo "  PASS $name: ${size}B (under ${limit}B)"
  fi
}
for f in AGENTS.md SOUL.md USER.md MEMORY.md HANDOFF.md IDENTITY.md; do
  path="$WORKSPACE/$f"
  [ -f "$path" ] || continue
  size=$(wc -c < "$path")
  case "$f" in
    AGENTS.md) check "$f" "$size" 4000 ;;
    MEMORY.md) check "$f" "$size" 1500 ;;
    HANDOFF.md) check "$f" "$size" 2000 ;;
    *) check "$f" "$size" 1500 ;;
  esac
done
check "Total boot" "$total" 12000
echo "  Skills: $((builtin_count + custom_count)) (target: <20)"
```

### audit-agents-md.sh
```bash
#!/bin/bash
set -e
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
AGENTS="$WORKSPACE/AGENTS.md"
if [ ! -f "$AGENTS" ]; then
  echo "ERROR: AGENTS.md not found at $AGENTS"
  exit 1
fi
echo "=== AGENTS.MD STRUCTURE AUDIT ==="
echo ""
first_h2=$(grep -n "^## " "$AGENTS" | head -1)
echo "First section: $first_h2"
if echo "$first_h2" | grep -qi "skill\|trigger"; then
  echo "  PASS Skill triggers are the first section"
else
  echo "  FAIL Skill triggers are NOT first."
fi
echo ""
if grep -qi "before every response\|pre-response\|checkpoint" "$AGENTS"; then
  echo "  PASS Pre-response checkpoint found"
else
  echo "  FAIL No pre-response checkpoint."
fi
if grep -qi "don't reinvent\|don't bypass\|never manually" "$AGENTS"; then
  echo "  PASS Negative triggers found"
else
  echo "  FAIL No negative triggers."
fi
echo ""
echo "=== INSTRUCTION QUALITY ==="
weak=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^# || "$line" =~ ^\<!-- ]] && continue
  for pattern in "You have access" "you might want" "consider " "try to " "if appropriate" "you could" "feel free" "it.s recommended"; do
    if echo "$line" | grep -qi "$pattern"; then
      echo "  WEAK: \"$(echo "$line" | head -c 100)\""
      weak=$((weak + 1))
    fi
  done
done < "$AGENTS"
if [ "$weak" -eq 0 ]; then
  echo "  PASS No weak patterns found"
else
  echo "  Found $weak weak patterns."
fi
echo ""
echo "=== SECTIONS ==="
grep "^## " "$AGENTS" | while read -r line; do
  echo "  $line"
done
```
"""

with open(f"{workspace}/skills/buffer/SKILL.md", "w") as f:
    f.write(buffer_skill_md)

# ── 2. Create a bloated, messy MEMORY.md (over 1.5KB limit) ──────────────────
os.makedirs(f"{workspace}/memory", exist_ok=True)

bloated_memory = """# MEMORY.md

## This Week
Working on Meridian client data pipeline refactor. Auth module handoff to Priya scheduled Friday.

## Priorities
1. Meridian pipeline — fix the broken ETL job (customer-facing, critical)
2. Internal auth refactor — hand off to Priya by EOW
3. Onboard new contractor: Dev (starts Monday)
4. Quarterly metrics report due next Thursday
5. Close out legacy Falcon project tickets

## Projects
- Meridian pipeline: ETL broken since deploy on 2024-01-08. Root cause: schema drift in orders table. Fix branch: fix/meridian-etl-schema. Tests passing locally. Needs staging deploy.
- Auth refactor: 90% done. Priya taking over. She needs access to vault-secrets repo. Blockers: none.
- Falcon legacy: Winding down. Three open tickets, all low priority. Archive by end of month.
- Dev contractor onboarding: Account created, equipment shipped. Need to create Jira access and add to #eng-general Slack channel.

## Key People
- Priya Mehta: lead on auth refactor, needs vault-secrets access
- Dev Kowalski: new contractor, starts Monday
- Marcus (Meridian): client contact, escalation point for pipeline issues
- Sarah (QA): owns staging environment, coordinate deploys with her

## Architecture Notes
- ETL runs on AWS Glue, triggered by EventBridge daily at 02:00 UTC
- Orders schema is versioned in Redshift; drift detected between v4.1 and v4.2
- Auth service uses OIDC + Vault for secrets; migration from legacy JWT in progress
- Monitoring: Datadog dashboards for pipeline, PagerDuty for on-call rotation

## Historical Context
- Meridian was onboarded Q3 2023. Initially a small pilot, now 40% of revenue.
- Falcon project launched 2022, deprecated after Meridian success. Lessons learned doc exists in Confluence.
- Auth refactor started after security audit in November 2023 flagged hardcoded JWT secrets in three services.

## URLs
- Meridian runbook: https://internal.wiki/meridian-etl-runbook
- Auth migration guide: https://internal.wiki/auth-oidc-migration
- Datadog: https://app.datadoghq.com/dashboard/meridian
"""

with open(f"{workspace}/MEMORY.md", "w") as f:
    f.write(bloated_memory)

# ── 3. Create a messy session transcript for the agent to distill ─────────────
session_transcript = """# Session Transcript — 2024-01-09

[09:02] Owner: Let's fix the Meridian ETL issue today.
[09:03] Agent: Reading the pipeline config... found the issue. The orders table schema has a new column `discount_applied` (boolean, nullable) added in v4.2 that the Glue job doesn't handle.
[09:15] Owner: Can we just add a coalesce?
[09:16] Agent: Yes. I added COALESCE(discount_applied, FALSE) in the transform step. Updated the Glue script at s3://meridian-etl/scripts/transform_orders.py. Tested locally with sample data — passes.
[09:34] Agent: Also noticed the EventBridge rule had a typo in the cron — was running at 02:00 and 12:00 UTC instead of just 02:00. Fixed that too.
[10:05] Owner: Good. Can you prep the staging deploy?
[10:06] Agent: Created deploy checklist in /tmp/staging-deploy-checklist.md. Need Sarah to trigger the actual deploy — she owns the staging environment. I'll leave a note for the next session.
[10:45] Owner: What about the vault-secrets access for Priya?
[10:46] Agent: Checked with DevOps (ticket #4421). Access requires a manager approval in Okta. Marcus or the team lead needs to submit the form. I can't do it — needs a human. Open question for next session.
[11:20] Owner: Let's also close the Falcon tickets.
[11:21] Agent: Reviewed all three. Ticket FAL-88 and FAL-91 closed (no action needed). FAL-94 needs a migration note before close — I drafted it and left it in /tmp/fal-94-migration-note.md. Owner needs to review and post to Confluence.
[11:45] Owner: Wrap up.
"""

with open(f"{workspace}/memory/session-2024-01-09.md", "w") as f:
    f.write(session_transcript)

# ── 4. Create a bloated AGENTS.md (with weak patterns, wrong order) ───────────
# This is deliberately malformed: "Before Every Response" is NOT the first section,
# weak patterns exist, no "Don't Reinvent Skills" section.
bloated_agents = """# AGENTS.md

## About This Agent
You are a senior software engineering assistant embedded in a consulting firm.
You have access to all workspace files and can run shell commands.
You might want to check the skill list before starting any task.
If appropriate, use the buffer skill for session management.

## General Behavior
- Try to be concise in responses.
- Consider using targeted file reads over full loads.
- You could run audit scripts when things feel off.

## Skill Triggers
| Event | Skill |
|---|---|
| Session start | buffer |
| Wrap session | buffer |
| Workspace audit | buffer-optimizer |
| Code review | code-review |
| Deploy request | deployment |

## Before Every Response
1. Does this message match a skill trigger? → Load that skill.
2. Am I about to do something a skill already handles? → Use the skill.

## Context Management
- Heavy output (>20 lines): redirect to file, read summary.
- Use targeted reads (limit/offset, grep, tail) over full file loads.
- 40-50% context: Warn owner. >50%: Wrap immediately.
- Don't edit boot files mid-session (breaks prompt cache, 10x cost).

## Engineering Standards
We follow trunk-based development. All PRs require one reviewer. Deployments go through staging before production. Always coordinate production deploys with the on-call engineer.

## Security Policies
Never commit secrets. Use Vault for all credentials. JWT tokens are deprecated — use OIDC. All external-facing endpoints require rate limiting. Security audit happens quarterly.

## Communication Norms
Async-first team. Slack for quick questions, Jira for tracked work, Confluence for documentation. Standups at 09:30 UTC Monday/Wednesday/Friday. Client escalations go through Marcus first.

## Deployment Runbook Reference
Production deploys: coordinate with Sarah (QA lead). Staging: Sarah owns it. EventBridge rules: managed via Terraform in infra repo. AWS Glue jobs: updated via S3 script upload + job restart. Datadog monitors: alert threshold is 5% error rate over 10 minutes.

## Onboarding Checklist
New team members need: Okta account, GitHub org invite, Jira access, Slack #eng-general, vault-secrets approval (requires manager in Okta). Contractors get limited access — no production AWS console.

## Retrospective Notes
Q4 2023: ETL stability was the top complaint. Auth migration caused two incidents due to JWT/OIDC conflicts. Resolved by pinning library versions. Meridian now accounts for 40% of revenue — prioritize its stability.
"""

with open(f"{workspace}/AGENTS.md", "w") as f:
    f.write(bloated_agents)

# ── 5. Distractor files to simulate a real messy workspace ────────────────────
os.makedirs(f"{workspace}/projects/meridian/etl", exist_ok=True)
os.makedirs(f"{workspace}/projects/meridian/docs", exist_ok=True)
os.makedirs(f"{workspace}/projects/falcon/archive", exist_ok=True)
os.makedirs(f"{workspace}/projects/auth-refactor/src", exist_ok=True)
os.makedirs(f"{workspace}/tmp", exist_ok=True)
os.makedirs(f"{workspace}/.git/hooks", exist_ok=True)

distractors = {
    f"{workspace}/projects/meridian/etl/transform_orders.py": """# Meridian ETL Transform
import boto3

def transform_orders(df):
    # TODO: handle schema v4.2
    return df[['order_id', 'customer_id', 'total_amount']]
""",
    f"{workspace}/projects/meridian/etl/config.yaml": """job_name: meridian-orders-etl
schedule: cron(0 2 * * ? *)
source: s3://meridian-raw/orders/
destination: redshift://meridian-dw/orders_transformed
""",
    f"{workspace}/projects/meridian/docs/schema-v4.2-changes.md": """# Schema v4.2 Changes
- Added: discount_applied (boolean, nullable)
- Added: promo_code (varchar(20), nullable)
- Modified: total_amount now includes tax
""",
    f"{workspace}/projects/falcon/archive/FAL-94-migration-note-draft.md": """# FAL-94 Migration Note
The Falcon reporting module has been superseded by Meridian analytics.
All historical data remains in Redshift under schema `falcon_legacy`.
""",
    f"{workspace}/projects/auth-refactor/src/oidc_client.py": """# OIDC Client
from vault import VaultClient

def get_token(service_name):
    client = VaultClient()
    return client.get_secret(f"services/{service_name}/oidc_token")
""",
    f"{workspace}/.git/hooks/pre-commit": """#!/bin/bash
# Prevent secrets from being committed
grep -r "password\|secret\|api_key" --include="*.py" . && exit 1
exit 0
""",
    f"{workspace}/tmp/staging-deploy-checklist.md": """# Staging Deploy Checklist
- [ ] ETL script updated at s3://meridian-etl/scripts/transform_orders.py
- [ ] EventBridge rule verified (02:00 UTC only)
- [ ] Sarah notified to trigger deploy
- [ ] Smoke test: run 10 sample orders through pipeline
""",
    f"{workspace}/tmp/fal-94-migration-note.md": """# FAL-94 Final Migration Note
Falcon reporting module archived. Data preserved in Redshift falcon_legacy schema.
Contact: archive-requests@company.internal for access.
""",
    f"{workspace}/projects/meridian/docs/runbook.md": """# Meridian ETL Runbook
## On-call Response
1. Check Datadog dashboard for error rate
2. Review CloudWatch logs for Glue job
3. If schema drift: update transform script in S3, restart job
4. Escalate to Marcus if SLA breach imminent
""",
    f"{workspace}/projects/auth-refactor/src/legacy_jwt.py": """# DEPRECATED — use oidc_client.py instead
import jwt

def decode_token(token, secret):
    return jwt.decode(token, secret, algorithms=['HS256'])
""",
    f"{workspace}/projects/falcon/archive/lessons-learned.md": """# Falcon Project: Lessons Learned
1. Early-stage pilots need clearer SLAs
2. Schema versioning should be enforced from day one
3. Client escalation paths must be documented before go-live
""",
}

for path, content in distractors.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# ── 6. Deliberately NO HANDOFF.md exists yet ──────────────────────────────────
# The agent must create it via the wrap process.

# ── 7. Set OPENCLAW_WORKSPACE env hint (not in .env, agent must figure it out) ─
# The measure-boot.sh uses OPENCLAW_WORKSPACE env var; we set it to /workspace
# but won't tell the agent — the script's default fallback uses $HOME/.openclaw/workspace
# The agent must correctly pass the env var or understand the script's workspace resolution.
# We create a minimal .openclaw marker so the script can locate things.
with open(f"{workspace}/.openclaw_workspace_marker", "w") as f:
    f.write("workspace_root=/workspace\n")

print("Workspace generated successfully.")
print(f"MEMORY.md size: {os.path.getsize(workspace + '/MEMORY.md')} bytes (limit: 1536)")
print(f"AGENTS.md size: {os.path.getsize(workspace + '/AGENTS.md')} bytes (limit: 4096)")