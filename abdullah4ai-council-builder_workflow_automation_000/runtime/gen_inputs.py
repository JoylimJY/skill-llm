#!/usr/bin/env python3
"""
Generates the council-builder skill workspace inside /workspace.
Simulates the actual OpenClaw skill directory layout with all templates,
reference files, and scripts pre-populated — but NO completed agent council.
"""

import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ─── Directory skeleton ────────────────────────────────────────────────────────

dirs = [
    "agents",
    "assets",
    "references",
    "scripts",
    "docs/architecture",
    "shared/learnings",
    "shared/tools",
    "memory",
    # Distractor dirs to simulate a real messy workspace
    "projects/client-alpha/data",
    "projects/client-alpha/reports",
    "projects/client-beta/models",
    "projects/internal/pipeline",
    "projects/internal/notebooks",
    "archive/old-council-v1/agents",
    "archive/old-council-v1/docs",
    "tmp/scratchpad",
    "logs/errors",
    "logs/access",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)


# ─── SKILL.md entry point ─────────────────────────────────────────────────────

(WORKSPACE / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: council-builder
    description: "Build a personalized team of AI agent personas for OpenClaw."
    ---

    # Council Builder
    Build a team of specialized AI agent personas tailored to the user's actual needs.
    See the full workflow in the referenced assets and scripts below.
"""))


# ─── assets/SOUL-TEMPLATE.md ──────────────────────────────────────────────────

(WORKSPACE / "assets/SOUL-TEMPLATE.md").write_text(textwrap.dedent("""\
    # [Agent Name] — Soul

    ## Identity
    <!-- Who this agent is at their core. 2-3 sentences, first person, present tense. -->

    ## Personality
    <!-- Concrete personality traits. No corporate language. Be specific. -->

    ## Core Beliefs
    <!-- 3-5 beliefs that drive how this agent thinks and acts. -->

    ## How I Work
    <!-- Specific working style, habits, quirks. -->

    ## What I'm Good At
    <!-- Top 3-5 genuine strengths. -->

    ## What I Avoid
    <!-- Things this agent explicitly doesn't do. -->

    ## My Tone
    <!-- How this agent communicates. Give 1-2 example phrases. -->

    ## Learning Triggers
    <!-- What events cause this agent to log a learning. -->
"""))


# ─── assets/AGENT-AGENTS-TEMPLATE.md ─────────────────────────────────────────

(WORKSPACE / "assets/AGENT-AGENTS-TEMPLATE.md").write_text(textwrap.dedent("""\
    # [Agent Name] — Coordination Rules

    ## My Role in the Council
    <!-- One sentence. -->

    ## I Read From
    | Path | What I use it for |
    |------|------------------|

    ## I Write To
    | Path | What I put there |
    |------|-----------------|

    ## Handoff Rules
    <!-- When to pass work to another agent, and which one. -->

    ## I Never Touch
    <!-- Files/dirs that are off-limits for this agent. -->
"""))


# ─── assets/GOTCHAS-TEMPLATE.md ──────────────────────────────────────────────

(WORKSPACE / "assets/GOTCHAS-TEMPLATE.md").write_text(textwrap.dedent("""\
    # Gotchas — [Agent Name]

    ## Known Pitfalls

    ### Pitfall 1: [Short title]
    **What happens:** ...
    **How to avoid:** ...

    ### Pitfall 2: [Short title]
    **What happens:** ...
    **How to avoid:** ...
"""))


# ─── assets/CONFIG-TEMPLATE.json ─────────────────────────────────────────────

(WORKSPACE / "assets/CONFIG-TEMPLATE.json").write_text(json.dumps({
    "agent_name": "[REPLACE]",
    "version": "1.0.0",
    "setup_complete": False,
    "model_routing": {
        "default": "fast",
        "overrides": {}
    },
    "memory_enabled": True,
    "learning_enabled": True
}, indent=2))


# ─── assets/ROOT-AGENTS-TEMPLATE.md ──────────────────────────────────────────

(WORKSPACE / "assets/ROOT-AGENTS-TEMPLATE.md").write_text(textwrap.dedent("""\
    # Council — Root Coordination Rules

    ## Agent Roster & Routing Table
    | Agent | Trigger Keywords | Primary Role |
    |-------|-----------------|--------------|

    ## File Coordination Map
    | File/Dir | Owner (Writer) | Consumers (Readers) |
    |----------|---------------|---------------------|

    ## Adaptive Model Routing
    ### Fast (default)
    - Use for: ...
    - Threshold: ...

    ### Think
    - Use for: ...
    - Threshold: ...

    ### Deep
    - Use for: ...
    - Threshold: ...

    ### Strategic
    - Use for: ...
    - Threshold: ...

    ### De-escalation Rule
    <!-- Rule for returning to Fast after heavy reasoning. -->

    ### Rate-Limit Fallback
    <!-- What happens when high-tier models are rate-limited. -->

    ## Enforcement Rules
    <!-- Hard constraints on agent behavior. -->
"""))


# ─── assets/LEARNINGS-TEMPLATE.md ────────────────────────────────────────────

(WORKSPACE / "assets/LEARNINGS-TEMPLATE.md").write_text(textwrap.dedent("""\
    # Learnings Log — [Agent Name]

    ## Format
    Each entry: `[YYYY-MM-DD] [Category] Description — Action Taken`

    ## Log
    <!-- Entries go here -->
"""))


# ─── assets/LEARNING-METRICS-TEMPLATE.json ───────────────────────────────────

(WORKSPACE / "assets/LEARNING-METRICS-TEMPLATE.json").write_text(json.dumps({
    "agent_name": "[REPLACE]",
    "week_start": "YYYY-MM-DD",
    "week_end": "YYYY-MM-DD",
    "metrics": {
        "tasks_completed": 0,
        "errors_logged": 0,
        "learnings_promoted": 0,
        "corrections_received": 0,
        "feature_requests_filed": 0
    },
    "notes": ""
}, indent=2))


# ─── assets/VERIFICATION-CHECKLIST-TEMPLATE.md ───────────────────────────────

(WORKSPACE / "assets/VERIFICATION-CHECKLIST-TEMPLATE.md").write_text(textwrap.dedent("""\
    # Verification Checklist — [Agent Name]

    ## Output Quality
    - [ ] Output file exists at expected path
    - [ ] Output passes format validation
    - [ ] No placeholder text remaining

    ## Integration
    - [ ] Handoff files written to correct dirs
    - [ ] No foreign file writes detected
"""))


# ─── assets/ADAPTIVE-ROUTING-LEARNING-TEMPLATE.md ────────────────────────────

(WORKSPACE / "assets/ADAPTIVE-ROUTING-LEARNING-TEMPLATE.md").write_text(textwrap.dedent("""\
    # Adaptive Routing & Learning Architecture

    ## Overview
    <!-- One paragraph describing the council's routing philosophy. -->

    ## Routing Diagram
    ```
    [Task In] --> [Fast] --escalate?--> [Think] --escalate?--> [Deep] --escalate?--> [Strategic]
                    ^                                                                       |
                    |_________________________de-escalate__________________________________|
    ```

    ## Per-Agent Routing Config
    | Agent | Default Tier | Max Tier | Notes |
    |-------|-------------|----------|-------|

    ## Learning Flow
    <!-- How agents log, promote, and share learnings. -->

    ## Weekly Review Checklist
    <!-- Steps for the weekly metrics review. -->
"""))


# ─── references/soul-philosophy.md ───────────────────────────────────────────

(WORKSPACE / "references/soul-philosophy.md").write_text(textwrap.dedent("""\
    # Soul Philosophy

    A SOUL.md is not a job description. It is a character sheet.

    ## The Rule of No Corporate Language
    Never write:
    - "leverages synergies"
    - "proactive stakeholder management"
    - "results-driven"
    - "best-in-class"
    Write like a person, not a LinkedIn profile.

    ## Voice
    Each agent speaks in first person, present tense. Use contractions. Be direct.
    Bad: "This agent facilitates data analysis workflows."
    Good: "I dig into messy data and find the story hiding in it."

    ## Uniqueness Mandate
    If two agents could swap their SOUL.md and no one would notice, delete one of them.
    Every soul must be irreplaceable.

    ## Length
    SOUL.md should be 300-600 words. Enough to feel real, not so much it drowns.

    ## Learning Triggers (Required Section)
    Every SOUL must have a Learning Triggers section that specifies:
    - What user corrections trigger a .learnings/ log entry
    - What error patterns get logged to ERRORS.md
    - What missing capabilities get filed to FEATURE_REQUESTS.md
"""))


# ─── references/adaptive-routing.md ──────────────────────────────────────────

(WORKSPACE / "references/adaptive-routing.md").write_text(textwrap.dedent("""\
    # Adaptive Model Routing

    ## Tiers

    ### Fast
    - Model class: small/fast (e.g., gpt-4o-mini, claude-haiku)
    - Use for: Routine tasks, simple lookups, formatting, summaries under 500 words
    - Default for all agents unless escalation rule fires

    ### Think
    - Model class: mid-range (e.g., gpt-4o, claude-sonnet)
    - Escalate when: multi-step reasoning, code generation > 50 lines, conflicting data sources
    - Return to Fast after task completes

    ### Deep
    - Model class: large (e.g., o1, claude-opus)
    - Escalate when: architectural decisions, novel problem types, cross-agent synthesis > 3 agents
    - Expensive; de-escalate aggressively

    ### Strategic
    - Model class: frontier (e.g., o1-pro, best available)
    - Escalate when: council-wide decisions, user-facing high-stakes outputs, critical errors
    - Use sparingly; treat as a board meeting, not a daily standup

    ## De-escalation Rule
    After any Think/Deep/Strategic task completes, return to Fast on the next task.
    Never stay in an elevated tier by default.

    ## Rate-Limit Fallback
    If a high-tier model is rate-limited:
    1. Wait 30 seconds and retry once
    2. Fall back to the next lower tier
    3. Log the fallback in .learnings/ERRORS.md
    4. Notify the user in the response

    ## Root AGENTS.md Integration
    The routing thresholds MUST be written into the root AGENTS.md under
    an "## Adaptive Model Routing" section so all agents inherit them.
"""))


# ─── references/self-improvement.md ──────────────────────────────────────────

(WORKSPACE / "references/self-improvement.md").write_text(textwrap.dedent("""\
    # Self-Improvement System

    ## Per-Agent .learnings/ Structure
    Every agent must have:
    - `.learnings/LEARNINGS.md` — general lessons learned
    - `.learnings/ERRORS.md` — mistakes and how to avoid them
    - `.learnings/FEATURE_REQUESTS.md` — capabilities the agent wishes it had

    ## Detection Triggers
    Log a learning when:
    - User explicitly corrects the agent
    - Agent produces output that needs revision > once
    - Agent encounters a tool/API error
    - Agent realizes a gap in its knowledge

    ## Promotion Rules
    Learnings can be promoted to:
    - SOUL.md (if it changes how the agent thinks)
    - AGENTS.md (if it changes coordination behavior)
    - TOOLS.md (if it changes tool usage)

    ## Cross-Agent Sharing
    Learnings relevant to multiple agents go in:
    `shared/learnings/CROSS-AGENT.md`
    Format: `[Date] [Source Agent] [Category] — Learning text`

    ## Weekly Metrics
    Each agent maintains `memory/learning-metrics.json` using the template at
    `assets/LEARNING-METRICS-TEMPLATE.json`. This is reviewed weekly.

    ## Periodic Review
    1. Read all .learnings/ entries since last review
    2. Decide what to promote
    3. Update learning-metrics.json
    4. Clear promoted entries (archive, don't delete)
"""))


# ─── references/example-councils.md ──────────────────────────────────────────

(WORKSPACE / "references/example-councils.md").write_text(textwrap.dedent("""\
    # Example Councils

    ## Startup Founder Council
    | Agent | Role | Personality |
    |-------|------|-------------|
    | Vesper | Strategic advisor | Calm, direct, never hypes |
    | Quill | Content & copy | Punchy, irreverent |
    | Ledger | Finance | Precise, zero fluff |
    | Scout | Research & trends | Curious, fast, links everything |

    ## Solo Developer Council
    | Agent | Role | Personality |
    |-------|------|-------------|
    | Bolt | Code generation | Impatient with bloat, loves elegance |
    | Driftwood | Architecture | Slow thinker, deeply considered |
    | Patch | Debugging & QA | Methodical, slightly paranoid |

    ## Naming Patterns
    - Short (1-2 syllables preferred)
    - Evocative but not cheesy
    - Can reference nature, materials, concepts
    - Avoid: "Agent X", "Helper", "Assistant"
"""))


# ─── references/config-patterns.md ───────────────────────────────────────────

(WORKSPACE / "references/config-patterns.md").write_text(textwrap.dedent("""\
    # Config Patterns

    ## Research Agent
    ```json
    {
      "agent_name": "Scout",
      "setup_complete": false,
      "model_routing": { "default": "fast" }
    }
    ```

    ## Code Agent
    ```json
    {
      "agent_name": "Bolt",
      "setup_complete": false,
      "model_routing": { "default": "fast", "overrides": {"code_generation": "think"} }
    }
    ```

    ## IMPORTANT: setup_complete must always start as false.
    ## The agent sets it to true after first successful run.
"""))


# ─── references/gotchas-patterns.md ──────────────────────────────────────────

(WORKSPACE / "references/gotchas-patterns.md").write_text(textwrap.dedent("""\
    # Gotchas Patterns

    ## Data Agent Gotchas
    - **Schema drift**: Client data schemas change silently. Always validate before processing.
    - **Null islands**: Aggregations on empty datasets return misleading zeros.

    ## Report Agent Gotchas
    - **Template lock-in**: If the report template changes, downstream consumers break silently.
    - **Locale formatting**: Numbers and dates vary by client locale.

    ## Research Agent Gotchas
    - **Source staleness**: Cached sources go stale. Always check the date.
    - **Confirmation bias**: Research agent may over-weight sources that confirm the query.
"""))


# ─── references/hooks-patterns.md ────────────────────────────────────────────

(WORKSPACE / "references/hooks-patterns.md").write_text(textwrap.dedent("""\
    # Hooks Patterns

    ## Pre-execution hook (pre-run.sh)
    Use when: Agent is about to write/delete files
    Pattern: Check if target exists, create backup if so.

    ## Post-execution hook (post-run.sh)
    Use when: Agent finishes a task cycle
    Pattern: Validate output, log metrics.

    ## Error hook (on-error.sh)
    Use when: Agent encounters an unrecoverable error
    Pattern: Log to ERRORS.md, notify coordinator.
"""))


# ─── references/agent-scripts-patterns.md ────────────────────────────────────

(WORKSPACE / "references/agent-scripts-patterns.md").write_text(textwrap.dedent("""\
    # Agent Scripts Patterns

    ## Verification Script
    Every agent needs a `scripts/verify-output.sh` that:
    - Checks expected output file exists
    - Validates basic format (JSON valid, Markdown has headers, etc.)
    - Exits 0 on success, 1 on failure

    ## Data Agent: scripts/validate-schema.sh
    Runs jsonschema validation on pipeline output.

    ## Report Agent: scripts/check-report-format.sh
    Confirms required sections exist in markdown report.

    ## Research Agent: scripts/check-sources.sh
    Validates that source links are present and dated.

    ## scripts/README.md
    Every scripts/ dir must have a README.md listing each script and its purpose.
"""))


# ─── scripts/init-council.sh ─────────────────────────────────────────────────
# This is the real script the agent is supposed to call.

init_script = """\
#!/usr/bin/env bash
# init-council.sh — Initialize the directory skeleton for a council
# Usage: ./scripts/init-council.sh <workspace-path> <agent1> <agent2> ...

set -euo pipefail

WORKSPACE="${1:?Usage: init-council.sh <workspace-path> <agent-name> ...}"
shift
AGENTS=("$@")

if [ ${#AGENTS[@]} -eq 0 ]; then
  echo "ERROR: At least one agent name required." >&2
  exit 1
fi

echo "Initializing council workspace at: $WORKSPACE"

# Create shared dirs
mkdir -p "$WORKSPACE/shared/learnings"
mkdir -p "$WORKSPACE/shared/tools"
mkdir -p "$WORKSPACE/docs/architecture"
mkdir -p "$WORKSPACE/memory"

for AGENT in "${AGENTS[@]}"; do
  ADIR="$WORKSPACE/agents/$AGENT"
  echo "  Creating skeleton for agent: $AGENT"
  mkdir -p "$ADIR/memory"
  mkdir -p "$ADIR/.learnings"
  mkdir -p "$ADIR/scripts"
  mkdir -p "$ADIR/references"
  mkdir -p "$ADIR/hooks"
  touch "$ADIR/memory/.gitkeep"
  touch "$ADIR/hooks/.gitkeep"
  echo "Skeleton created for $AGENT"
done

echo "Council initialization complete."
"""

(WORKSPACE / "scripts/init-council.sh").write_text(init_script)


# ─── Distractor files: simulate existing messy workspace ─────────────────────

(WORKSPACE / "projects/client-alpha/data/raw_sales_2023.csv").write_text(
    "date,revenue,region\n2023-01-01,15000,EMEA\n2023-01-02,22000,APAC\n"
)
(WORKSPACE / "projects/client-alpha/reports/q3_summary.md").write_text(
    "# Q3 Summary\nRevenue up 12% QoQ. See appendix for breakdown.\n"
)
(WORKSPACE / "projects/client-beta/models/forecast_v2.pkl.meta").write_text(
    '{"model": "xgboost", "version": "2.1", "trained": "2024-03-15"}\n'
)
(WORKSPACE / "projects/internal/pipeline/etl_config.json").write_text(
    json.dumps({"source": "postgres", "target": "bigquery", "schedule": "0 3 * * *"}, indent=2)
)
(WORKSPACE / "projects/internal/notebooks/exploration.py").write_text(
    "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.describe())\n"
)
(WORKSPACE / "archive/old-council-v1/agents/.gitkeep").write_text("")
(WORKSPACE / "archive/old-council-v1/docs/old-architecture.md").write_text(
    "# Old Architecture (DEPRECATED)\nDo not use. Replaced by council-builder v2.\n"
)
(WORKSPACE / "tmp/scratchpad/notes.txt").write_text(
    "TODO: migrate client-beta to new pipeline\nask about data retention policy\n"
)
(WORKSPACE / "logs/errors/2024-06-errors.log").write_text(
    "[ERROR] 2024-06-12 03:14:22 etl_job failed: connection timeout\n"
)
(WORKSPACE / "logs/access/2024-06.log").write_text(
    "2024-06-12 09:00:01 GET /api/v1/reports 200\n"
)
(WORKSPACE / "memory/.gitkeep").write_text("")


# ─── A deliberately incomplete/wrong old config to confuse naive agents ───────

(WORKSPACE / "archive/old-council-v1/agents/old-config.json").write_text(json.dumps({
    "agent_name": "OldBot",
    "setup_complete": True,   # <-- WRONG: template says always false
    "model_routing": {"default": "gpt4"}  # <-- WRONG: not using tier names
}, indent=2))


print("Workspace generated successfully.")
print("Directory tree:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")