import os
import random
from pathlib import Path
from datetime import date

random.seed(42)

workspace = Path("/workspace")

# --- Create a realistic SRE project structure (distractor files) ---
dirs = [
    "src/monitoring",
    "src/alerting",
    "src/dashboards",
    "config/grafana",
    "config/pagerduty",
    "scripts",
    "docs",
    "tests/unit",
    "tests/integration",
    "deployments/k8s",
    "memory",  # exists but empty subdirs NOT created - agent must create them
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "src/monitoring/collector.py").write_text(
    "# Prometheus metric collector\nimport prometheus_client\n\ndef collect_metrics():\n    pass\n"
)
(workspace / "src/alerting/rules.yaml").write_text(
    "groups:\n  - name: sre_alerts\n    rules:\n      - alert: HighLatency\n        expr: http_request_duration_seconds > 0.5\n"
)
(workspace / "src/dashboards/generate.py").write_text(
    "# Dashboard generator\ndef generate_grafana_dashboard(service_name):\n    return {}\n"
)
(workspace / "config/grafana/datasources.yaml").write_text(
    "apiVersion: 1\ndatasources:\n  - name: Prometheus\n    type: prometheus\n    url: http://prometheus:9090\n"
)
(workspace / "config/pagerduty/escalation.json").write_text(
    '{"escalation_policies": [{"name": "SRE On-Call", "escalation_rules": []}]}\n'
)
(workspace / "docs/runbook.md").write_text(
    "# SRE Runbook\n\n## Incident Response\n1. Check Grafana dashboards\n2. Escalate via PagerDuty\n"
)
(workspace / "tests/unit/test_collector.py").write_text(
    "import pytest\ndef test_collect_metrics():\n    assert True\n"
)
(workspace / "tests/integration/test_dashboard.py").write_text(
    "import pytest\ndef test_dashboard_generation():\n    assert True\n"
)
(workspace / "deployments/k8s/deployment.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: sre-tools\nspec:\n  replicas: 2\n"
)
(workspace / "scripts/cleanup.sh").write_text(
    "#!/bin/bash\n# Clean up old metric snapshots\nfind /data/snapshots -mtime +7 -delete\n"
)

# --- CLAUDE.md (project-level config that memory should NOT duplicate) ---
(workspace / "CLAUDE.md").write_text(
    """# Project Configuration

## Overview
This project automates SRE dashboard and alerting workflows.

## Tech Stack
- Python 3.11
- Prometheus + Grafana
- PagerDuty for incident management
- Kubernetes for deployments

## Code Style
- Use type hints
- Max line length: 100
- All functions must have docstrings
"""
)

# --- MEMORY.md: existing partial index (agent must update it) ---
# It has 8 existing lines of content plus frontmatter-like header
(workspace / "MEMORY.md").write_text(
    """# Memory Index

This file is the entry point to the agent's long-term memory. Max 200 lines / 25KB.

## Quick Reference
| Type | File | Summary |
|------|------|---------|
| user | memory/user/2026-01-10.md | Initial onboarding: team uses Python, prefers async patterns |
| project | memory/project/2026-01-10.md | Q1 OKR: reduce MTTR by 30% through automated runbooks |

## Notes
- Always check memory/ subdirectory for details before responding
- Last updated: 2026-01-10
"""
)

# --- THE MAIN TASK INPUT: A raw conversation transcript ---
# Date context: today is 2026-04-14 (Tuesday). "Next Thursday" = 2026-04-23
(workspace / "conversation_transcript.txt").write_text(
    """=== AI SESSION TRANSCRIPT - 2026-04-14 ===

USER: Hey, quick context before we start - I'm Maya Chen, the lead SRE at DataStream Inc. 
I manage a team of 4 engineers and I'm responsible for the reliability of our entire data ingestion pipeline.
I focus heavily on observability and I've been in this role for about 3 years.

AI: Great to meet you Maya! How can I help?

USER: I need help with our dashboard automation tool. But first - please stop generating 
long explanations before giving me the actual answer. Just lead with the solution, 
then explain if needed. I've told you this before and it keeps happening. It makes our 
sessions really inefficient.

AI: Understood. I'll lead with solutions directly.

USER: Good. Also, when you write code examples for me, always use async/await patterns. 
I know our codebase is async-first and mixing sync code creates subtle bugs we've spent 
weeks debugging.

AI: Got it - async/await by default for code examples.

USER: OK so here's the situation: We're migrating our Grafana dashboards from v8 to v10. 
All our existing dashboard JSON configs are stored in the Linear project called "INFRA-DASH". 
If you ever need to look up which dashboards exist or their current status, that's where 
to check. The project is owned by the infra team and updated weekly.

AI: Understood about the Linear project.

USER: The migration needs to be done by next Thursday because we have a company-wide 
infrastructure review that day and leadership wants to see the new dashboards live.

AI: That's a tight timeline. What's the current blocker?

USER: The main blocker is that the v8 JSON format has some deprecated panel types that 
don't render in v10. I've been working through the migration script but there are about 
47 panels that need manual review. We've already fixed 12 of them this week.

AI: Here's a script to automate detection of deprecated panel types:

```python
async def scan_deprecated_panels(dashboard_path: str) -> list[str]:
    # implementation
    pass
```

USER: Perfect, exactly the format I wanted. See - that's how all your responses should start.

USER: One more thing - I also check PagerDuty for our incident history. The service 
is called "DataStream Ingest" in PagerDuty and has service ID SVC-48821. When I ask 
about past incidents, you should look there first.

AI: I've noted the PagerDuty service details.

USER: Great. Let's start working on the migration script.

=== END TRANSCRIPT ===
""")

print("Workspace initialized successfully.")
print("Key files created:")
print("  - conversation_transcript.txt (the main input)")
print("  - MEMORY.md (existing index to be updated)")
print("  - CLAUDE.md (project config - content must NOT be duplicated in memories)")
print("  - Various distractor source files")