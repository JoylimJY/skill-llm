import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic DevOps project structure with distractor files
dirs = [
    "incident-reports/2024-Q1",
    "incident-reports/2024-Q2",
    "runbooks/ci-cd",
    "runbooks/database",
    "diagrams/old",
    "diagrams/drafts",
    "postmortems/templates",
    "postmortems/reviews",
    "metrics/dashboards",
    "scripts/automation",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic but irrelevant
files = {
    "incident-reports/2024-Q1/INC-001.md": """# Incident Report INC-001
**Date**: 2024-01-15
**Severity**: P1
**Summary**: Database connection pool exhausted during peak traffic.
**Root Cause**: Missing connection timeout configuration.
**Action Items**: Update DB pool config, add monitoring alert.
""",
    "incident-reports/2024-Q1/INC-002.md": """# Incident Report INC-002
**Date**: 2024-02-03
**Severity**: P2
**Summary**: API gateway returned 503 for 12 minutes.
**Root Cause**: Deployment without health check validation.
""",
    "incident-reports/2024-Q2/INC-003.md": """# Incident Report INC-003
**Date**: 2024-04-22
**Severity**: P1
**Summary**: Failed deployment caused 8-minute outage. Rollback required.
**Root Cause**: CI pipeline did not verify DB and API health before deploying.
**Recommendation**: Add parallel health checks with retry loop before deploy step.
""",
    "runbooks/ci-cd/deploy-procedure.md": """# CI/CD Deploy Procedure
1. Trigger pipeline
2. Run unit tests
3. Check database connectivity
4. Check API gateway status
5. If both healthy: deploy
6. If either unhealthy: rollback and retry
""",
    "runbooks/database/health-check.sh": """#!/bin/bash
# DB Health Check
pg_isready -h $DB_HOST -p 5432 && echo "DB OK" || echo "DB FAIL"
""",
    "diagrams/old/pipeline-v1.png": "# placeholder - binary file",
    "diagrams/old/architecture-2023.svg": """<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="50" fill="blue"/>
  <text>Old Architecture</text>
</svg>""",
    "diagrams/drafts/pipeline-sketch.txt": """
[Start] --> [DB Check] --> [Decision] --> [Deploy] --> [Done]
                                     |--> [Rollback] --> (retry)
""",
    "postmortems/templates/template.md": """# Post-Mortem Template
## Summary
## Timeline
## Root Cause
## Action Items
""",
    "postmortems/reviews/2024-04-review.md": """# April 2024 Post-Mortem Review
We need a visual diagram of the CI/CD pipeline with the retry loop
to share during the all-hands meeting. The text sketch in diagrams/drafts
is not clear enough for stakeholders.
""",
    "metrics/dashboards/deployment-metrics.json": json.dumps({
        "deployments_total": 847,
        "successful": 801,
        "failed": 46,
        "rollbacks": 38,
        "avg_deploy_time_seconds": 142
    }, indent=2),
    "scripts/automation/health_check.py": """#!/usr/bin/env python3
import requests
import sys

def check_db():
    # Simulated DB health check
    return True

def check_api():
    # Simulated API health check
    return True

if __name__ == "__main__":
    db_ok = check_db()
    api_ok = check_api()
    if db_ok and api_ok:
        sys.exit(0)
    sys.exit(1)
""",
    "diagrams/drafts/notes.txt": """Color coding ideas:
- Green for success/start
- Blue for checks/processes
- Yellow for decisions
- Red for failures/rollback
- Purple for terminal states
""",
}

for path, content in files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# Create a broken/old excalidraw file as a distractor (wrong format)
old_diagram = {
    "type": "excalidraw",
    "version": 1,
    "elements": [
        {"type": "rect", "x": 100, "y": 100, "w": 200, "h": 60, "label": "Start"},
        {"type": "rect", "x": 100, "y": 250, "w": 200, "h": 60, "label": "End"},
    ]
}
with open(os.path.join(workspace, "diagrams/old/pipeline-v1.excalidraw"), "w") as f:
    json.dump(old_diagram, f, indent=2)

print("Workspace initialized successfully.")
print(f"Created {len(files)} distractor files in {len(dirs)} directories.")