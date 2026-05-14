import os
import random
import json
import yaml
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    ".claude",
    "src/api",
    "src/core",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "config",
    "scripts",
    "docs",          # docs/ exists but is EMPTY — agent must write here
    "data/raw",
    "data/processed",
    ".github/workflows",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── .claude/settings.json  (with the required env var for agent teams) ───────
settings = {
    "env": {
        "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
    },
    "permissions": {
        "allow": ["Bash", "Read", "Write", "WebSearch", "WebFetch"]
    }
}
(workspace / ".claude/settings.json").write_text(json.dumps(settings, indent=2))

# ── SKILL.md in .claude/commands/ ───────────────────────────────────────────
commands_dir = workspace / ".claude/commands"
commands_dir.mkdir(parents=True, exist_ok=True)

skill_content = """\
---
name: solo-swarm
description: Launch 3 parallel research agents (market, users, tech) to investigate an idea from multiple angles simultaneously. Use when user says "swarm research", "parallel research", "investigate fast", "3 agents", "team research", or wants faster alternative to /research. Produces research.md. Do NOT use for solo research (use /research) or idea scoring (use /validate).
license: MIT
metadata:
  author: fortunto2
  version: "1.6.0"
  openclaw:
    emoji: "🐝"
allowed-tools: Read, Grep, Glob, Bash, WebSearch, WebFetch, Write, mcp__solograph__web_search, mcp__solograph__kb_search, mcp__solograph__project_info, mcp__solograph__codegraph_query, mcp__solograph__codegraph_explain, mcp__solograph__project_code_search, mcp__solograph__session_search
argument-hint: "[idea name or description]"
---

# /swarm

Create an agent team to research "$ARGUMENTS" from multiple perspectives in parallel.

## Team Structure

Spawn 3 teammates, each with a distinct research focus:

### 1. Market Researcher
Focus: competitors, market size, pricing models, business models.
- Search for direct and indirect competitors
- Find market reports with TAM/SAM/SOM figures
- Analyze pricing strategies and monetization
- Identify market gaps and opportunities
- Check Product Hunt, G2, Capterra for existing products

### 2. User Researcher
Focus: pain points, user sentiment, feature requests.
- Search Reddit for user discussions (`site:reddit.com <query>` via WebSearch, or MCP `web_search` if available)
- Search Hacker News for tech community opinions (`site:news.ycombinator.com`)
- If MCP `session_search` available: check if this idea was researched before in past sessions
- Find app reviews and ratings
- Extract direct user quotes about frustrations
- Identify unmet needs and feature requests

### 3. Technical Analyst
Focus: feasibility, tech stack, existing solutions, implementation complexity.
- Search GitHub for open-source alternatives (`site:github.com <query>`)
- Evaluate tech stack options
- If MCP `project_info` available: check existing projects for reusable code
- If MCP `codegraph_explain` available: get architecture overview of similar existing projects
- If MCP `codegraph_query` available: find shared packages across projects
- If MCP `project_code_search` available: search for reusable patterns, services, infrastructure across existing projects
- Assess implementation complexity and timeline

## Search Backends

Teammates should use available search tools:
- **WebSearch** (built-in) — broad discovery, market reports, always available
- **WebFetch** — scrape specific URLs for details, always available
- **MCP `web_search`** (if available) — additional search with engine routing
- **MCP `kb_search`** (if available) — search local knowledge base for related research

**Domain filtering:** use `site:github.com`, `site:reddit.com` etc. for targeted results.

## Coordination

- Each teammate writes findings to a shared task list
- Require plan approval before teammates start deep research
- After all complete, synthesize findings into `research.md`
- Use the research.md format from `/research` skill

## Output

After team completes, the lead should:
1. Synthesize findings from all 3 teammates
2. Write `research.md` to `docs/` in the current project directory
3. Provide GO / NO-GO / PIVOT recommendation
4. Suggest next step: `/validate <idea>`

## Common Issues

### Agent team not available
**Cause:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var not set.
**Fix:** Ensure `.claude/settings.json` has `"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}`.

### Teammates produce overlapping findings
**Cause:** Research areas not clearly separated.
**Fix:** Each teammate has a distinct focus (market/users/tech). The lead synthesizes and deduplicates findings.

### Web search returns limited results
**Cause:** No additional search backends configured.
**Fix:** Teammates fall back to WebSearch (built-in) which is always available. For richer results with engine routing (Reddit, GitHub, YouTube), set up SearXNG and configure solograph MCP.
"""
(commands_dir / "swarm.md").write_text(skill_content)

# ── Distractor source files ──────────────────────────────────────────────────
(workspace / "src/api/routes.py").write_text("""\
# API routes for the main service
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    return jsonify({'status': 'ok'})

@api_bp.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    return jsonify({'results': [], 'query': query})
""")

(workspace / "src/core/engine.py").write_text("""\
# Core research engine stub
class ResearchEngine:
    def __init__(self, topic):
        self.topic = topic
        self.findings = []

    def add_finding(self, agent, content):
        self.findings.append({'agent': agent, 'content': content})

    def synthesize(self):
        return '\\n'.join(f['content'] for f in self.findings)
""")

(workspace / "src/utils/formatters.py").write_text("""\
def format_markdown_section(title, content):
    return f'## {title}\\n\\n{content}\\n'

def format_quote(text, source):
    return f'> {text}\\n> — {source}\\n'
""")

(workspace / "tests/unit/test_engine.py").write_text("""\
import pytest
# Unit tests for core engine
def test_add_finding():
    pass
""")

(workspace / "tests/integration/test_search.py").write_text("""\
import requests
# Integration tests for search endpoints
def test_search_endpoint():
    pass
""")

(workspace / "config/app.yaml").write_text("""\
app:
  name: research-platform
  version: 0.1.0
  debug: false
search:
  timeout: 30
  max_results: 10
""")

(workspace / "scripts/run_dev.sh").write_text("""\
#!/bin/bash
echo 'Starting dev server...'
python -m flask run --port 5000
""")

(workspace / "data/raw/sample_queries.json").write_text(json.dumps([
    {"id": 1, "query": "AI code review tools 2024", "category": "market"},
    {"id": 2, "query": "automated PR review github", "category": "tech"},
    {"id": 3, "query": "developer pain points code review", "category": "user"},
], indent=2))

(workspace / "data/processed/market_notes.txt").write_text("""\
DRAFT NOTES - NOT FINAL
Market size TBD
Competitors: CodeRabbit, Reviewpad, Codacy
Pricing: unclear
""")

(workspace / ".github/workflows/ci.yml").write_text("""\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest tests/
""")

(workspace / "config/search_backends.yaml").write_text("""\
# Search backend configuration
backends:
  websearch:
    enabled: true
    default: true
  mcp_solograph:
    enabled: false
    endpoint: null
  searxng:
    enabled: false
    endpoint: null
""")

# ── Intentionally broken/incomplete previous research attempt ────────────────
(workspace / "data/raw/old_research_attempt.txt").write_text("""\
INCOMPLETE - DO NOT USE
Started research on AI code review tools but ran out of time.
Didn't finish market analysis.
No user research done.
No technical analysis.
No recommendation made.
File should be at: ??? (forgot where to put it)
""")

# ── A misleading file in root docs/ that is NOT a valid research.md ──────────
(workspace / "docs/.gitkeep").write_text("")

# ── Project idea brief (the task trigger) ────────────────────────────────────
(workspace / "idea_brief.txt").write_text("""\
IDEA: AI-powered code review assistant for small dev teams

We want to build a SaaS tool that automatically reviews pull requests
using LLMs, flags potential bugs, suggests improvements, and learns
from team coding style over time.

Target: small engineering teams (2-15 devs) who can't afford a dedicated
QA engineer but want consistent code quality.

Monetization: subscription, $20-50/dev/month tier.

We need fast research on this idea before our investor meeting next week.
Use the team research approach — we need market, user, and technical
angles covered simultaneously.
""")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")