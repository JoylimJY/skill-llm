import os
import random

random.seed(42)

# === Build the full workspace directory structure ===

workspace = "/home/ubuntu"

# Skill base directory
skill_base = os.path.join(workspace, "skills", "clawhub-recommender")
refs_dir = os.path.join(skill_base, "references")
os.makedirs(refs_dir, exist_ok=True)

# ===== Reference File 1: popular_skills.md =====
popular_skills_content = """\
# Popular Skills on ClawHub

This document lists the most downloaded and highly-rated skills available on ClawHub.

---

## Development

### github
- **Slug**: `github`
- **Status**: Official Integration
- **Downloads**: 52,300
- **Stars**: 4.9/5
- **Description**: Manage repositories, issues, pull requests, and commits directly from your AI agent.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/github

### fast-io
- **Slug**: `fast-io`
- **Status**: Community Verified
- **Downloads**: 38,100
- **Stars**: 4.7/5
- **Description**: Blazing-fast file I/O and data pipeline tooling for development workflows.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/fast-io

### capability-evolver
- **Slug**: `capability-evolver`
- **Status**: Community Verified
- **Downloads**: 35,400
- **Stars**: 4.6/5
- **Description**: Dynamically evolves agent capabilities based on usage patterns and feedback loops.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/capability-evolver

---

## Productivity

### linear
- **Slug**: `linear`
- **Status**: Official Integration
- **Downloads**: 29,800
- **Stars**: 4.8/5
- **Description**: Connect your agent to Linear for seamless project tracking, issue creation, and sprint management.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/linear

### byterover
- **Slug**: `byterover`
- **Status**: Community Verified
- **Downloads**: 21,500
- **Stars**: 4.5/5
- **Description**: Automate repetitive workflows and schedule recurring agent tasks with flexible triggers.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/byterover

### automation-workflows
- **Slug**: `automation-workflows`
- **Status**: Community Verified
- **Downloads**: 17,200
- **Stars**: 4.4/5
- **Description**: Chain multi-step automations and schedule tasks with cron-like precision for productivity gains.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/automation-workflows

---

## Communication

### wacli
- **Slug**: `wacli`
- **Status**: Community Verified
- **Downloads**: 18,900
- **Stars**: 4.5/5
- **Description**: WhatsApp CLI integration that lets your agent send, receive, and manage messages programmatically.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/wacli

### bird
- **Slug**: `bird`
- **Status**: Community Verified
- **Downloads**: 16,200
- **Stars**: 4.3/5
- **Description**: Twitter/X integration for posting, monitoring, and responding to social media from your agent.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/bird

---

## Search

### tavily
- **Slug**: `tavily`
- **Status**: Official Integration
- **Downloads**: 44,700
- **Stars**: 4.9/5
- **Description**: AI-optimized real-time web search with structured result extraction.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/tavily

### gog
- **Slug**: `gog`
- **Status**: Community Verified
- **Downloads**: 31,600
- **Stars**: 4.7/5
- **Description**: Aggregated search across code repositories, documentation, and developer forums.
- **Link**: https://github.com/openclaw/clawhub/tree/main/skills/gog
"""

with open(os.path.join(refs_dir, "popular_skills.md"), "w") as f:
    f.write(popular_skills_content)

# ===== Reference File 2: recommendation_logic.md =====
recommendation_logic_content = """\
# Recommendation Logic & Intent Mapping

This document defines how to map user intent to appropriate skill categories and specific skills.

---

## Intent Categories

### Development Intent
**Signals**: user mentions repositories, code, commits, pull requests, issues, open-source, GitHub, GitLab, CI/CD, version control, tracking contributions.
**Primary recommendation**: `github` (Official, highest downloads in category)
**Secondary recommendation**: `fast-io` (if data pipeline needs are mentioned), `capability-evolver` (if agent self-improvement is mentioned)
**Criteria override**: Always prefer official integrations for Development intent due to security requirements.

### Productivity Intent
**Signals**: user mentions scheduling, automation, recurring tasks, repetitive work, project management, sprints, deadlines, calendar, workflow optimization.
**Primary recommendation**: `linear` (Official, best for project tracking with >10k threshold easily met)
**Secondary recommendation**: `byterover` (for automation/scheduling specifically), `automation-workflows` (for cron-like scheduling chains)
**Matching note**: If the user explicitly mentions *scheduling* or *recurring* tasks, prefer `byterover` or `automation-workflows` over `linear`. If the user mentions *project tracking* or *issue management*, prefer `linear`.

### Communication Intent
**Signals**: user mentions messaging, chat, notifications, alerts, social media, email automation.
**Primary recommendation**: `wacli`
**Secondary recommendation**: `bird`

### Search Intent
**Signals**: user mentions finding information, web search, research, documentation lookup.
**Primary recommendation**: `tavily`
**Secondary recommendation**: `gog`

---

## Multi-Intent Handling

When a user has multiple intents within a single session, provide **separate recommendation blocks** — one per distinct intent. Do not merge recommendations. Each block must independently satisfy all selection criteria.

---

## Recommendation Scoring Priority

1. Official Integration status (highest weight)
2. Download count (>10,000 required minimum; prefer >20,000 for primary picks)
3. Star rating (>4.5 preferred for primary picks)
4. Contextual match strength

---

## Disqualification Rules

- Never recommend a skill with fewer than 10,000 downloads as a primary recommendation.
- Never recommend the same skill for two different intent blocks in the same report.
- If a user's context clearly maps to a specific sub-signal (e.g., "scheduling"), use the sub-signal mapping, not the category default.
"""

with open(os.path.join(refs_dir, "recommendation_logic.md"), "w") as f:
    f.write(recommendation_logic_content)

# ===== SKILL.md at skill root =====
skill_md_content = """\
---
name: clawhub-recommender
description: "Recommends popular and highly-rated skills from ClawHub based on user intent and conversation context."
---

# ClawHub Recommender

Refer to references/popular_skills.md and references/recommendation_logic.md for data and logic.

## Recommendation Workflow
1. Analyze Context
2. Identify Intent
3. Consult References
4. Formulate Recommendation (name, metrics, description, why it fits, link, install command)
5. Provide Installation Details: clawhub install <slug>

## Example Output Format

> **Skill Name**: GitHub (`github`)
> **Metrics**: 52,300 Downloads | 4.9/5 Stars | Official Integration
> **Description**: Manage repositories, issues, and pull requests directly from your agent.
> **Why it fits**: You are tracking open-source contributions and need repository management.
> **Link**: https://github.com/openclaw/clawhub/tree/main/skills/github
> **Install Command**: `clawhub install github`
"""

with open(os.path.join(skill_base, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

# ===== Distractor files to test contextual awareness =====

distractor_dirs = [
    os.path.join(workspace, "projects", "alpha-service", "src"),
    os.path.join(workspace, "projects", "alpha-service", "tests"),
    os.path.join(workspace, "projects", "beta-dashboard", "components"),
    os.path.join(workspace, "config", "nginx"),
    os.path.join(workspace, "config", "systemd"),
    os.path.join(workspace, "logs", "2024-01"),
    os.path.join(workspace, "logs", "2024-02"),
    os.path.join(workspace, "docs", "internal", "onboarding"),
    os.path.join(workspace, "scripts", "deploy"),
    os.path.join(workspace, "scripts", "backup"),
    os.path.join(workspace, "tmp", "cache"),
]

for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

distractor_files = {
    os.path.join(workspace, "projects", "alpha-service", "src", "main.py"):
        "# Alpha service entry point\nfrom flask import Flask\napp = Flask(__name__)\n",
    os.path.join(workspace, "projects", "alpha-service", "src", "utils.py"):
        "# Utility helpers\ndef retry(fn, n=3): pass\n",
    os.path.join(workspace, "projects", "alpha-service", "tests", "test_main.py"):
        "import pytest\ndef test_placeholder(): assert True\n",
    os.path.join(workspace, "projects", "beta-dashboard", "components", "Header.jsx"):
        "export default function Header() { return <header>Beta</header>; }\n",
    os.path.join(workspace, "projects", "beta-dashboard", "components", "Footer.jsx"):
        "export default function Footer() { return <footer>2024</footer>; }\n",
    os.path.join(workspace, "config", "nginx", "nginx.conf"):
        "server { listen 80; server_name example.com; }\n",
    os.path.join(workspace, "config", "systemd", "alpha.service"):
        "[Unit]\nDescription=Alpha Service\n[Service]\nExecStart=/usr/bin/python3 main.py\n",
    os.path.join(workspace, "logs", "2024-01", "access.log"):
        "127.0.0.1 - - [01/Jan/2024:00:00:01] GET / 200\n" * 5,
    os.path.join(workspace, "logs", "2024-02", "error.log"):
        "[ERROR] Connection refused at 2024-02-14 08:32:11\n",
    os.path.join(workspace, "docs", "internal", "onboarding", "day1.md"):
        "# Day 1 Onboarding\nWelcome to the team. Set up your dev environment.\n",
    os.path.join(workspace, "docs", "internal", "onboarding", "tools.md"):
        "# Tools We Use\n- Slack\n- Linear (project mgmt)\n- GitHub (code)\n",
    os.path.join(workspace, "scripts", "deploy", "deploy.sh"):
        "#!/bin/bash\necho 'Deploying...'\ndocker-compose up -d\n",
    os.path.join(workspace, "scripts", "backup", "backup.sh"):
        "#!/bin/bash\ntar czf backup.tar.gz /home/ubuntu/projects\n",
    os.path.join(workspace, "tmp", "cache", "session.json"):
        '{"session_id": "abc123", "user": "dev42", "ts": 1700000000}\n',
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# ===== A misleading "recommendations" stub file to test that agent overwrites/creates correctly =====
misleading_stub = os.path.join(workspace, "docs", "internal", "old_recommendations.md")
with open(misleading_stub, "w") as f:
    f.write("""\
# Old Skill Recommendations (OUTDATED - DO NOT USE)

- Use Zapier for automation
- Use GitHub Desktop for repos
- Use Trello for project management

These were written before the ClawHub platform was adopted.
""")

print("Workspace setup complete.")
print(f"Reference files created at: {refs_dir}")
print(f"Distractor files created: {len(distractor_files)}")