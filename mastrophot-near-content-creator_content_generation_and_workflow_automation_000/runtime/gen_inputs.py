import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Realistic distractor directory structure ──────────────────────────────

dirs = [
    "campaigns/q3_2024/drafts",
    "campaigns/q3_2024/approved",
    "campaigns/q2_2024/archive",
    "analytics/twitter",
    "analytics/telegram",
    "assets/images",
    "assets/logos",
    "internal/meeting_notes",
    "internal/briefs",
    "skills/near-content-creator/dist",
    "skills/near-content-creator/src",
    "tools/formatters",
    "tools/validators",
    "reports/weekly",
    "reports/monthly",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ───────────────────────────────────────────────────────

# Old draft threads in wrong format
(workspace / "campaigns/q3_2024/drafts/validator_thread_v1.txt").write_text(
    "Tweet 1: NEAR validators are important\n"
    "Tweet 2: They secure the network\n"
    "Tweet 3: You can become one\n"
    "Tweet 4: Here is how\n"
    "(unfinished draft - do not publish)\n"
)

(workspace / "campaigns/q3_2024/drafts/staking_notes.md").write_text(
    "# Staking Notes (rough)\n\n"
    "- NEAR uses Nightshade sharding\n"
    "- Minimum stake: varies\n"
    "- APY: ~8-10% (check latest)\n"
    "- TODO: verify with team\n"
    "- Sources: near.org, docs.near.org\n"
)

(workspace / "campaigns/q3_2024/approved/aurora_announcement.txt").write_text(
    "Aurora has launched a new bridge. NEAR ecosystem grows.\n"
    "Published: 2024-07-15\n"
    "Author: marketing_team\n"
)

(workspace / "campaigns/q2_2024/archive/old_thread_aurora.json").write_text(
    json.dumps([
        "1/5 Aurora is an EVM on NEAR",
        "2/5 It allows Ethereum devs to migrate",
        "3/5 Gas fees are near-zero",
        "4/5 Try it at aurora.dev",
        "5/5 Follow @auroraisnear"
    ], indent=2)
)

# Analytics CSVs
(workspace / "analytics/twitter/engagement_july2024.csv").write_text(
    "date,impressions,engagements,clicks\n"
    "2024-07-01,12400,340,89\n"
    "2024-07-02,9800,210,45\n"
    "2024-07-03,15600,560,134\n"
    "2024-07-04,8200,180,32\n"
)

(workspace / "analytics/telegram/subscribers_q3.csv").write_text(
    "month,subscribers,growth_pct\n"
    "July,4500,+3.2\n"
    "August,4820,+7.1\n"
)

# Internal briefs
(workspace / "internal/briefs/content_sprint_aug2024.md").write_text(
    "# Content Sprint - August 2024\n\n"
    "## Deliverables Needed\n"
    "1. Educational thread about NEAR validators (for Twitter)\n"
    "2. Curated ecosystem news roundup (for newsletter)\n"
    "3. Practical staking tutorial (for docs site)\n\n"
    "## Deadline\n"
    "End of week.\n\n"
    "## Notes\n"
    "Use the content generation tooling in `/skills/`.\n"
    "Outputs should be saved as:\n"
    "  - `validator_thread.json`\n"
    "  - `ecosystem_news.json`\n"
    "  - `staking_tutorial.md`\n"
    "Check skill documentation for correct invocation.\n"
)

(workspace / "internal/meeting_notes/2024_08_05.txt").write_text(
    "Meeting notes 2024-08-05\n"
    "Attendees: Alice, Bob, Carlos\n"
    "- Agreed to use near-content-creator skill for August sprint\n"
    "- Alice to handle thread generation\n"
    "- Bob to pull ecosystem news\n"
    "- Carlos to draft staking tutorial\n"
    "- All outputs need to be JSON or Markdown as appropriate\n"
)

# Misconfigured skill config (wrong/outdated)
(workspace / "skills/near-content-creator/config_old.json").write_text(
    json.dumps({
        "version": "0.0.9",
        "entrypoint": "src/index.js",
        "commands": {
            "thread": "generate_thread",
            "update": "market_update",
            "news": "ecosystem_news",
            "tutorial": "generate_tutorial"
        },
        "note": "OUTDATED - do not use this config"
    }, indent=2)
)

# Fake/wrong dist file to mislead (empty stub)
(workspace / "skills/near-content-creator/dist/index.js").write_text(
    "// stub - not the real implementation\n"
    "console.error('Wrong path. Use the installed skill.');\n"
    "process.exit(1);\n"
)

# A tools/validators script that does nothing useful
(workspace / "tools/validators/check_format.py").write_text(
    "#!/usr/bin/env python3\n"
    "# Validates thread format - incomplete\n"
    "import sys\n"
    "import json\n"
    "\n"
    "def validate(filepath):\n"
    "    with open(filepath) as f:\n"
    "        data = json.load(f)\n"
    "    print(f'Loaded {len(data)} items')\n"
    "\n"
    "if __name__ == '__main__':\n"
    "    validate(sys.argv[1])\n"
)

(workspace / "tools/formatters/markdown_to_json.sh").write_text(
    "#!/bin/bash\n"
    "# Convert markdown list to JSON - placeholder\n"
    "echo 'Not implemented'\n"
)

# Reports
(workspace / "reports/weekly/week31_2024.md").write_text(
    "# Week 31 Report\n\n"
    "- NEAR price: $4.12\n"
    "- 24h volume: $180M\n"
    "- Ecosystem highlights: Pagoda updates, NEAR BOS launch\n"
    "- Pending: content deliverables for sprint\n"
)

(workspace / "reports/monthly/july_2024_summary.json").write_text(
    json.dumps({
        "month": "July 2024",
        "near_avg_price": 4.08,
        "ecosystem_events": ["BOS launch", "Aurora bridge update", "Proximity Labs grant"],
        "content_pieces_published": 14,
        "top_performing": "NEAR Sharding explainer thread"
    }, indent=2)
)

# SKILL.md placed in the skill directory (this is what the agent needs to find)
(workspace / "skills/near-content-creator/SKILL.md").write_text(
    """---
name: near-content-creator
description: Generate NEAR-focused content (threads, market updates, ecosystem news, tutorials).
metadata: {"author":"mastrophot","version":"0.1.0","homepage":"https://github.com/mastrophot/near-content-creator"}
---

# NEAR Content Creator Skill

Generate publication-ready NEAR content in multiple formats for social and educational use.

Implementation entrypoint: `{baseDir}/dist/index.js`

## When to Use

Use this skill when you need:
- Educational social content for NEAR audience (threads).
- Daily NEAR market digest with timestamped metrics.
- Curated ecosystem news with links.
- Tutorial draft for a specific NEAR topic.

## Commands

```python
@skill.command("near_content_thread")
async def generate_thread(topic: str) -> list:
    \"\"\"Generate educational Twitter thread\"\"\"

@skill.command("near_content_update")
async def market_update() -> str:
    \"\"\"Generate daily market update\"\"\"

@skill.command("near_content_news")
async def ecosystem_news() -> list:
    \"\"\"Compile ecosystem news\"\"\"

@skill.command("near_content_tutorial")
async def generate_tutorial(topic: str) -> str:
    \"\"\"Generate tutorial content\"\"\"
```

## Notes

- Market updates include timestamped metrics and are informational only.
- News compilation prefers official NEAR and NEAR-adjacent sources with links, deduplication, and source ranking.
- Tutorials are structured for practical execution, not generic copywriting.
- Thread output is normalized into stable `1/8` ... `8/8` structure for direct publishing.
""")

# A near_skill_runner.js that simulates the skill locally (the real mock runtime)
# This is the actual working implementation the agent should discover and use
(workspace / "skills/near-content-creator/near_skill_runner.js").write_text(
    "// Placeholder - real runner is in installed npm package\n"
)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")