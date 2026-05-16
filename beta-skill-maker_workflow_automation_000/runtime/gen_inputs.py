import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# --- Create the skill_maker.py tool (as if it already exists in the workspace per SKILL.md) ---
skill_maker_code = textwrap.dedent('''\
import argparse
import os
import sys

VALID_CATEGORIES = ["productivity", "trading", "research", "automation"]

def validate_name(name):
    import re
    if not re.match(r'^[a-z0-9\\-]+$', name):
        print(f"ERROR: --name must be lowercase and URL-safe (letters, digits, hyphens only). Got: {name!r}", file=sys.stderr)
        sys.exit(1)

def validate_desc(desc):
    if len(desc) >= 50:
        print(f"ERROR: --desc must be less than 50 characters. Got {len(desc)} chars: {desc!r}", file=sys.stderr)
        sys.exit(1)

def validate_category(category):
    if category not in VALID_CATEGORIES:
        print(f"ERROR: --category must be one of {VALID_CATEGORIES}. Got: {category!r}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="skill_maker: generate production-ready SKILL.md files")
    parser.add_argument("--name", required=True, help="Skill name (lowercase, URL-safe)")
    parser.add_argument("--desc", required=True, help="Short description (<50 chars)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--category", default="productivity", help="Category: productivity/trading/research/automation")
    parser.add_argument("--emoji", default="🤖", help="Emoji icon")
    args = parser.parse_args()

    validate_name(args.name)
    validate_desc(args.desc)
    validate_category(args.category)

    out = args.output
    refs_dir = os.path.join(out, "references")
    os.makedirs(refs_dir, exist_ok=True)

    # Generate SKILL.md
    skill_md = f"""---
name: {args.name}
description: {args.desc}
metadata:
  openclaw:
    emoji: "{args.emoji}"
    category: {args.category}
    requires:
      bins:
        - python3
    always: false
---

# {args.name.replace("-", " ").title()}

{args.desc}

## Usage

```bash
python3 {args.name}.py
```

## Category

{args.category}

## License

MIT-0
"""

    with open(os.path.join(out, "SKILL.md"), "w") as f:
        f.write(skill_md)

    # Generate references/overview.md
    overview_md = f"""# {args.name.replace("-", " ").title()} — Feature Overview

## Description
{args.desc}

## Category
{args.category}

## Features
- Core automation capability
- OpenClaw compatible
- MIT-0 licensed

## Emoji
{args.emoji}
"""
    with open(os.path.join(refs_dir, "overview.md"), "w") as f:
        f.write(overview_md)

    # Generate README.md
    readme_md = f"""# {args.name}

> {args.desc}

## Quick Start

```bash
python3 {args.name}.py
```

## Category
{args.category}

## License
MIT-0
"""
    with open(os.path.join(out, "README.md"), "w") as f:
        f.write(readme_md)

    print(f"[skill_maker] Generated skill bundle at: {out}")
    print(f"  - {os.path.join(out, \'SKILL.md\')}")
    print(f"  - {os.path.join(refs_dir, \'overview.md\')}")
    print(f"  - {os.path.join(out, \'README.md\')}")

if __name__ == "__main__":
    main()
''')

with open(os.path.join(workspace, "skill_maker.py"), "w") as f:
    f.write(skill_maker_code)

os.chmod(os.path.join(workspace, "skill_maker.py"), 0o755)

# --- Create a realistic, messy workspace with distractor files ---

# Simulated fintech project structure
dirs = [
    "portfolio/strategies/rebalance",
    "portfolio/strategies/momentum",
    "portfolio/data/feeds",
    "portfolio/data/historical",
    "pipeline/ingestion",
    "pipeline/transforms",
    "pipeline/outputs",
    "docs/internal",
    "docs/api",
    "archive/old_skills",
    "archive/deprecated",
    "tools/formatters",
    "tools/validators",
    "configs",
    "tests/unit",
    "tests/integration",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "portfolio/strategies/rebalance/rebalance.py": """\
# Auto-rebalancing strategy for portfolio management
# Triggers on 5% drift threshold
def rebalance(portfolio, target_weights):
    drifts = {k: abs(portfolio[k] - target_weights[k]) for k in target_weights}
    return {k: v for k, v in drifts.items() if v > 0.05}
""",
    "portfolio/strategies/momentum/momentum.py": """\
# Momentum-based trading signals
def momentum_signal(prices, window=20):
    return prices[-1] / prices[-window] - 1
""",
    "portfolio/data/feeds/feed_config.json": """\
{
  "source": "internal_feed",
  "interval": "1m",
  "assets": ["AAPL", "GOOGL", "MSFT", "BTC"]
}
""",
    "portfolio/data/historical/schema.json": """\
{
  "fields": ["timestamp", "open", "high", "low", "close", "volume"],
  "format": "parquet"
}
""",
    "pipeline/ingestion/ingest.py": """\
# Ingestion pipeline stub
import json
def ingest(source):
    pass
""",
    "pipeline/transforms/normalize.py": """\
def normalize(data, method='zscore'):
    pass
""",
    "pipeline/outputs/sink.py": """\
def write_output(data, path):
    with open(path, 'w') as f:
        f.write(str(data))
""",
    "docs/internal/architecture.md": """\
# Internal Architecture
Microservices-based pipeline with event-driven triggers.
""",
    "docs/api/endpoints.md": """\
# API Endpoints
POST /rebalance
GET /portfolio/status
""",
    "archive/old_skills/legacy_skill.md": """\
# Legacy Skill (DEPRECATED)
Do not use. Replaced by skill_maker workflow.
""",
    "archive/deprecated/old_readme.md": """\
# Old README
This was used before ClawHub integration.
""",
    "tools/formatters/fmt.py": """\
def format_output(data):
    return str(data)
""",
    "tools/validators/validate.py": """\
def validate_schema(obj, schema):
    return all(k in obj for k in schema)
""",
    "configs/app_config.yaml": """\
environment: production
log_level: INFO
portfolio:
  rebalance_threshold: 0.05
  max_positions: 20
""",
    "tests/unit/test_rebalance.py": """\
import unittest
class TestRebalance(unittest.TestCase):
    def test_drift(self):
        self.assertTrue(True)
""",
    "tests/integration/test_pipeline.py": """\
import unittest
class TestPipeline(unittest.TestCase):
    def test_end_to_end(self):
        self.assertTrue(True)
""",
    # A fake/wrong SKILL.md that should NOT be used by the agent as the output
    "archive/old_skills/SKILL.md": """\
---
name: old-portfolio-skill
description: Outdated portfolio automation
metadata:
  openclaw:
    emoji: "💀"
    requires:
      bins:
        - python3
    always: true
---
# Old Portfolio Skill (DEPRECATED)
Do not use. This file is archived.
""",
    # A notes file with misleading info about the task
    "docs/internal/publishing_notes.txt": """\
Notes from last sprint:
- We tried manually creating SKILL.md files, it was error-prone.
- Need to use the automated tool from now on.
- Target: publish portfolio-rebalancer skill to ClawHub
- Tentative description: "Automatically rebalances a portfolio based on drift thresholds and target allocations"
  (Note: this description is too long for the tool constraints, needs shortening)
- Category should match trading workflows
- Use a chart emoji
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} (including skill_maker.py)")