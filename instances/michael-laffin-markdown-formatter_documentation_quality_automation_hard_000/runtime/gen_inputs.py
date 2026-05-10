import os
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure (distractors + real data) ──────────────────────────
dirs = [
    "docs/runbooks",
    "docs/guides",
    "docs/api",
    "docs/architecture",
    "docs/onboarding",
    "archive/old_guides",
    "archive/deprecated",
    "scripts",
    "config/templates",
    "reports",
    "assets/diagrams",
    "assets/screenshots",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files (non-markdown or clean, not to be processed) ───────────
distractor_files = {
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "config/templates/base.yaml": "version: 1\ndefault_style: github\n",
    "config/templates/ci.json": '{"lint": true, "format": "github"}\n',
    "assets/diagrams/arch.txt": "Service A -> Service B -> Service C\n",
    "archive/deprecated/old_format.txt": "This is a deprecated plain text file.\n",
    "archive/old_guides/legacy_notes.rst": "Legacy RST\n==========\n\nSome old content here.\n",
    "scripts/check_links.py": "# Link checker stub\nprint('checking...')\n",
    "reports/.gitkeep": "",
    "assets/screenshots/.gitkeep": "",
    "docs/api/swagger.json": '{"openapi": "3.0.0", "info": {"title": "API", "version": "1.0"}}\n',
    "docs/architecture/diagram.puml": "@startuml\nA -> B\n@enduml\n",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Messy markdown files (the real inputs) ──────────────────────────────────
# These are intentionally poorly formatted to trigger lint errors:
# - Mixed list markers (asterisk + dash + plus)
# - Multiple consecutive blank lines
# - Inconsistent heading levels (skipping h2 -> h4)
# - Trailing whitespace
# - Mixed emphasis styles
# - No blank line before/after code blocks

messy_docs = {}

messy_docs["docs/runbooks/incident_response.md"] = (
    "#  Incident Response Runbook\n"
    "\n"
    "\n"
    "\n"
    "### Overview   \n"                     # skipped h2, trailing spaces
    "This guide explains how to handle production incidents.\n"
    "\n"
    "* Check the alerting dashboard\n"
    "- Acknowledge the alert\n"             # mixed list markers
    "+ Escalate if unresolved\n"            # mixed list markers
    "\n"
    "\n"
    "#### Severity Levels   \n"
    "_Critical_: Full outage\n"             # underscore emphasis
    "*High*: Partial outage\n"              # asterisk emphasis
    "__Medium__: Degraded performance\n"    # double underscore
    "\n"
    "```\n"
    "ssh admin@prod-server\n"               # no language tag on fenced block
    "```\n"
    "\n"
    "\n"
    "### Post-Incident Steps\n"
    "* Write RCA document\n"
    "* Update runbook\n"
    "- Notify stakeholders\n"              # mixed again
)

messy_docs["docs/runbooks/deployment_checklist.md"] = (
    "# Deployment Checklist\n"
    "\n"
    "Ensure all steps are completed before deploying to production.\n"
    "\n"
    "\n"
    "\n"
    "## Pre-Deployment   \n"              # trailing whitespace
    "+ Merge feature branch\n"
    "+ Run all tests\n"
    "* Check code coverage\n"             # mixed marker
    "\n"
    "\n"
    "#### Configuration Checks\n"         # skipped h3
    "- Verify environment variables\n"
    "- Check secrets rotation\n"
    "+ Confirm database migrations\n"     # mixed
    "\n"
    "## Deployment Steps\n"
    "\n"
    "1. Tag the release\n"
    "2. Push to registry\n"
    "3.  Deploy to staging  \n"           # extra space, trailing
    "4. Run smoke tests\n"
    "\n"
    "\n"
    "## Post-Deployment\n"
    "__Verify__ metrics are nominal.\n"   # double underscore
    "_Check_ error rates in logs.\n"      # mixed emphasis
    "\n"
    "```bash\n"
    "kubectl rollout status deployment/app\n"
    "```\n"
)

messy_docs["docs/guides/onboarding_guide.md"] = (
    "#  New Engineer Onboarding\n"
    "\n"
    "\n"
    "## Week 1   \n"
    "\n"
    "* Set up development environment\n"
    "+ Install required tools\n"          # mixed
    "- Clone main repositories\n"         # mixed
    "\n"
    "\n"
    "\n"
    "### Day 1 Tasks\n"
    "\n"
    "_Meet your team_\n"
    "*Attend standup*\n"                  # mixed emphasis
    "\n"
    "#### Access Provisioning\n"         # heading level jump
    "- Request VPN access\n"
    "+ Request GitHub access\n"          # mixed
    "* Request AWS access\n"             # mixed
    "\n"
    "\n"
    "## Week 2\n"
    "\n"
    "Begin working on starter tickets.\n"
    "\n"
    "+ Pick up a `good-first-issue`\n"
    "- Pair with a buddy\n"              # mixed
    "\n"
    "```\n"
    "git clone git@github.com:company/repo.git\n"  # no language tag
    "```\n"
)

messy_docs["docs/guides/monitoring_guide.md"] = (
    "# Monitoring & Alerting Guide\n"
    "\n"
    "This document covers our observability stack.\n"
    "\n"
    "\n"
    "### Metrics Stack   \n"             # skipped h2, trailing spaces
    "\n"
    "We use Prometheus and Grafana.\n"
    "\n"
    "* Install Prometheus\n"
    "- Configure scrape targets\n"       # mixed
    "+ Set retention policy\n"          # mixed
    "\n"
    "\n"
    "#### Alert Rules   \n"
    "__High latency__: p99 > 500ms\n"   # double underscore
    "_High error rate_: > 1%\n"         # underscore
    "*Disk pressure*: > 80%\n"          # mixed emphasis
    "\n"
    "```\n"
    "promtool check rules alerts.yaml\n" # no language tag
    "```\n"
    "\n"
    "\n"
    "### Dashboards\n"
    "+ Create dashboard per service\n"
    "* Add SLO panels\n"                # mixed
    "- Share with team\n"
    "\n"
)

messy_docs["docs/onboarding/tools_setup.md"] = (
    "#   Developer Tools Setup\n"
    "\n"
    "\n"
    "\n"
    "## Required Tools   \n"
    "\n"
    "* Docker Desktop\n"
    "+ kubectl\n"                        # mixed
    "- Helm\n"
    "* Terraform\n"                      # mixed
    "\n"
    "\n"
    "### Installation\n"
    "\n"
    "#### macOS\n"
    "\n"
    "```\n"
    "brew install kubectl helm terraform\n"  # no language tag
    "```\n"
    "\n"
    "_Note_: Docker Desktop requires a separate download.\n"  # underscore
    "\n"
    "\n"
    "#### Linux\n"
    "\n"
    "```\n"
    "sudo apt-get install -y kubectl\n"  # no language tag
    "```\n"
    "\n"
    "\n"
    "## Optional Tools\n"
    "+ k9s (Kubernetes UI)\n"
    "* Lens (Kubernetes IDE)\n"         # mixed
    "- jq (JSON processor)\n"
    "\n"
    "__Tip__: Install `fzf` for fuzzy search integration.\n"  # double underscore
    "\n"
)

# Write all messy docs
for path, content in messy_docs.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print(f"Generated {len(messy_docs)} messy markdown files in workspace.")
print("Distractor files created:", len(distractor_files))
print("Workspace structure ready.")