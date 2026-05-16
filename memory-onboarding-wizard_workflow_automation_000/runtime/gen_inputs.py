import os
import random
import string
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Create a realistic OpenClaw project directory tree ──────────────────────
openclaw_ws = workspace / "openclaw_project"
openclaw_ws.mkdir(parents=True, exist_ok=True)

# Create the scripts directory with the actual wizard script
scripts_dir = openclaw_ws / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Write the actual memory-onboarding-wizard.py script
wizard_script = scripts_dir / "memory-onboarding-wizard.py"
wizard_content = '''#!/usr/bin/env python3
"""
Memory Onboarding Wizard — Bootstrap an OpenClaw agent memory system.
Built by GetAgentIQ — getagentiq.ai
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

DEFAULT_WORKSPACE = os.path.expanduser("~/.openclaw/workspace")

MEMORY_MD_TEMPLATE = """# Agent Long-Term Memory

## Identity
- Agent: OpenClaw
- Created: {today}

## Key Facts
<!-- Add important facts here -->

## Decisions
<!-- Log important decisions here -->

## Ongoing Context
<!-- Persistent context across sessions -->
"""

DAILY_MD_TEMPLATE = """# Daily Notes — {today}

## Session Log
<!-- Notes from today's sessions -->

## Tasks
- [ ] Review memory files
- [ ] Update MEMORY.md with new facts

## Observations
<!-- Raw observations from today -->
"""

HEARTBEAT_MD_TEMPLATE = """# Heartbeat Checklist

## Periodic Tasks
- [ ] Check for new messages
- [ ] Review pending tasks
- [ ] Update memory if needed
- [ ] Confirm user context is current

## Health Indicators
- Memory files: OK
- Daily notes: OK
- User profile: OK
"""

USER_MD_TEMPLATE = """# User Profile

## Name
{name}

## Timezone
{timezone}

## Main Use Case
{use_case}

## Preferences
<!-- Add user preferences here -->
"""

def ask(prompt, default):
    try:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default

def main():
    parser = argparse.ArgumentParser(description="Memory Onboarding Wizard")
    parser.add_argument(
        "--workspace",
        default=DEFAULT_WORKSPACE,
        help="Path to OpenClaw workspace directory",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip questions and use default values",
    )
    args = parser.parse_args()

    ws = Path(args.workspace)
    ws.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()

    print("\\n🧙 Memory Onboarding Wizard")
    print("=" * 40)

    # 1. MEMORY.md
    memory_file = ws / "MEMORY.md"
    if not memory_file.exists():
        memory_file.write_text(MEMORY_MD_TEMPLATE.format(today=today))
        print(f"✅ Created MEMORY.md")
    else:
        print(f"ℹ️  MEMORY.md already exists — skipped")

    # 2. memory/YYYY-MM-DD.md
    memory_dir = ws / "memory"
    memory_dir.mkdir(exist_ok=True)
    daily_file = memory_dir / f"{today}.md"
    if not daily_file.exists():
        daily_file.write_text(DAILY_MD_TEMPLATE.format(today=today))
        print(f"✅ Created memory/{today}.md")
    else:
        print(f"ℹ️  memory/{today}.md already exists — skipped")

    # 3. HEARTBEAT.md
    heartbeat_file = ws / "HEARTBEAT.md"
    if not heartbeat_file.exists():
        heartbeat_file.write_text(HEARTBEAT_MD_TEMPLATE)
        print(f"✅ Created HEARTBEAT.md")
    else:
        print(f"ℹ️  HEARTBEAT.md already exists — skipped")

    # 4. USER.md — ask 3 questions
    user_file = ws / "USER.md"
    if not user_file.exists():
        if args.non_interactive:
            name = "Default User"
            timezone = "UTC"
            use_case = "General assistant"
        else:
            print("\\n📋 Quick setup — 3 questions:\\n")
            name = ask("Your name", "User")
            timezone = ask("Your timezone (e.g. UTC, US/Eastern)", "UTC")
            use_case = ask("Main use case", "General assistant")

        user_file.write_text(
            USER_MD_TEMPLATE.format(name=name, timezone=timezone, use_case=use_case)
        )
        print(f"✅ Created USER.md")
    else:
        print(f"ℹ️  USER.md already exists — skipped")

    # 5. Validation
    print("\\n" + "=" * 40)
    print("📁 Validation:")
    all_ok = True
    for f in [memory_file, daily_file, heartbeat_file, user_file]:
        exists = f.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {f.relative_to(ws)}")
        if not exists:
            all_ok = False

    if all_ok:
        print("\\n✅ Memory system setup complete!")
    else:
        print("\\n❌ Some files are missing. Re-run the wizard.")
        sys.exit(1)

    # 6. Next steps
    print("\\n🚀 Next steps:")
    print("  1. Open MEMORY.md and add key facts about your project")
    print("  2. Review HEARTBEAT.md and customize your checklist")
    print("  3. Ask your agent: 'What do you remember about me?'")
    print()

if __name__ == "__main__":
    main()
'''
wizard_script.write_text(wizard_content)
wizard_script.chmod(0o755)

# ── Distractor files: realistic OpenClaw project clutter ────────────────────

# Stale/old memory files from a DIFFERENT workspace (red herring)
old_ws = workspace / "old_openclaw_backup"
old_ws.mkdir(parents=True, exist_ok=True)
(old_ws / "MEMORY.md").write_text("# Old Memory\n\nThis is an archived memory file.\n")
(old_ws / "USER.md").write_text("# Old User\nName: Archived User\n")

# Config files
(openclaw_ws / "config.yaml").write_text(
    "agent:\n  name: trading-bot\n  version: 0.4.2\n  log_level: INFO\n"
)
(openclaw_ws / ".env.example").write_text(
    "OPENCLAW_API_KEY=your-key-here\nOPENCLAW_ENV=production\n"
)

# Source files
src_dir = openclaw_ws / "src"
src_dir.mkdir(parents=True, exist_ok=True)
(src_dir / "agent_core.py").write_text(
    "# Core agent logic\nclass TradingAgent:\n    pass\n"
)
(src_dir / "market_feed.py").write_text(
    "# Market data feed handler\ndef fetch_prices():\n    pass\n"
)
(src_dir / "risk_engine.py").write_text(
    "# Risk management\nMAX_DRAWDOWN = 0.05\n"
)

# Logs directory
logs_dir = openclaw_ws / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
for i in range(3):
    d = (datetime.today() - timedelta(days=i+1)).strftime("%Y-%m-%d")
    (logs_dir / f"agent_{d}.log").write_text(
        f"[{d}] INFO Agent started\n[{d}] INFO Processing market data\n"
    )

# Tests
tests_dir = openclaw_ws / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
(tests_dir / "test_agent.py").write_text(
    "import pytest\ndef test_placeholder():\n    assert True\n"
)

# A misleading partial memory directory with wrong date file (red herring)
wrong_memory_dir = openclaw_ws / "memory"
wrong_memory_dir.mkdir(parents=True, exist_ok=True)
(wrong_memory_dir / "2020-01-01.md").write_text(
    "# Old Daily Note\nThis is a stale note from 2020.\n"
)

# Requirements and docs
(openclaw_ws / "requirements.txt").write_text(
    "requests>=2.28\npyyaml>=6.0\nclick>=8.0\n"
)
(openclaw_ws / "pyproject.toml").write_text(
    '[tool.poetry]\nname = "openclaw-trading"\nversion = "0.1.0"\n'
)

# A SKILL.md file as per the task context
skill_content = open("/dev/stdin").read() if False else """---
name: memory-onboarding-wizard
description: Bootstrap a new OpenClaw agent's memory system in one command. Sets up MEMORY.md, daily memory files, HEARTBEAT.md, and USER.md by asking 3 quick questions. Use when a user is setting up OpenClaw for the first time, when memory files are missing, or when asked to "set up my memory system", "initialize my agent", "bootstrap my agent", or "run the memory wizard". Solves the #1 OpenClaw pain point — agents waking up with no context about who they're serving.
---

# Memory Onboarding Wizard

> Built by **GetAgentIQ** — [getagentiq.ai](https://getagentiq.ai)
> *The home of premium OpenClaw skills, packs, and agent blueprints.*

One command to give your OpenClaw agent its memory. Walks through the complete memory system setup interactively.

## Quick Start

```bash
python3 scripts/memory-onboarding-wizard.py
```

Run from the OpenClaw workspace directory (default: `~/.openclaw/workspace`).

## What It Does

1. **MEMORY.md** — Creates long-term memory file with starter template if missing
2. **memory/YYYY-MM-DD.md** — Creates today's daily note file (creates `memory/` dir if needed)
3. **HEARTBEAT.md** — Creates a starter heartbeat checklist if missing
4. **USER.md** — Asks 3 quick questions (name, timezone, main use case) and writes them
5. **Validation** — Checks all files exist and prints a ✅ summary
6. **Next steps** — Suggests the first 3 things to try

## Options

```bash
python3 scripts/memory-onboarding-wizard.py --workspace /path/to/workspace
python3 scripts/memory-onboarding-wizard.py --non-interactive   # skip questions, use defaults
```

## Memory System Overview

| File | Purpose | When Loaded |
|------|---------|-------------|
| `MEMORY.md` | Long-term curated memory | Main sessions only |
| `memory/YYYY-MM-DD.md` | Daily raw notes | Every session |
| `HEARTBEAT.md` | Periodic task checklist | On heartbeat polls |
| `USER.md` | Who the agent is serving | Every session |

## After Setup

Your agent will read these files at the start of each session to maintain continuity. Update `MEMORY.md` with important events and decisions. Let daily files accumulate naturally.

---

## 🧠 Want the Full Memory Pack?

This wizard gets you started. The **GetAgentIQ Memory Pack** takes it further:

- **Auto-compaction** — keeps MEMORY.md lean and fast automatically
- **Semantic search** — find anything across all memory files instantly
- **Session recall** — 7-day keyword recall tester
- **Memory health dashboard** — health score + gap detection
- **Consolidation cron** — nightly memory distillation, runs while you sleep

👉 **Get the Memory Pack free:** [getagentiq.ai/memory-pack](https://getagentiq.ai)
Use code `CLAWHUB100` at checkout for 100% off.

*Built by GetAgentIQ — [getagentiq.ai](https://getagentiq.ai)*
"""

(openclaw_ws / "SKILL.md").write_text(skill_content)

print("Workspace generated at /workspace/openclaw_project")
print(f"Scripts available: {list(scripts_dir.iterdir())}")