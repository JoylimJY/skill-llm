import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# --- Deeply nested distractor structure ---
dirs = [
    "memory/tasks",
    "memory/logs",
    "memory/sessions",
    "ops/monitoring/raw",
    "ops/monitoring/processed",
    "ops/alerts",
    "ops/runbooks",
    "projects/ecommerce/backend",
    "projects/ecommerce/frontend",
    "projects/ecommerce/infra",
    "projects/legacy/archive",
    "skills/brainstorming",
    "skills/write-plan",
    "skills/doing-tasks",
    "skills/verify-task",
    "skills/dispatch-multiple-agents",
    "data/raw_logs/2024-01",
    "data/raw_logs/2024-02",
    "data/processed",
    "docs/architecture",
    "docs/runbooks",
]

for d in dirs:
    Path(f"{WORKSPACE}/{d}").mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# Old/irrelevant ongoing-tasks stub (wrong location, to mislead)
with open(f"{WORKSPACE}/memory/ongoing_tasks_old.txt", "w") as f:
    f.write("# DEPRECATED - do not use this file\n")
    f.write("Task: Fix login bug - DONE\n")
    f.write("Task: Update README - DONE\n")

# Some completed tasks in wrong format
with open(f"{WORKSPACE}/memory/tasks/completed-2024-01.md", "w") as f:
    f.write("## Completed Tasks January 2024\n\n")
    f.write("- [x] Database migration\n")
    f.write("- [x] API versioning update\n")
    f.write("- [x] Payment gateway integration\n")

# Random log files (distractors)
for i in range(3):
    with open(f"{WORKSPACE}/data/raw_logs/2024-01/app_{i}.log", "w") as f:
        f.write(f"2024-01-{i+1:02d} ERROR: NullPointerException in OrderService\n")
        f.write(f"2024-01-{i+1:02d} WARN:  Slow query detected (2300ms)\n")
        f.write(f"2024-01-{i+1:02d} INFO:  Health check passed\n")

# Runbook stub
with open(f"{WORKSPACE}/ops/runbooks/incident_response.md", "w") as f:
    f.write("# Incident Response Runbook\n\n")
    f.write("## Severity Levels\n")
    f.write("- P1: Site down\n- P2: Degraded performance\n- P3: Minor issues\n")

# A misleading 'plan' file that is incomplete and in wrong location
with open(f"{WORKSPACE}/projects/ecommerce/backend/rough_notes.md", "w") as f:
    f.write("# Rough Notes - Log Monitoring\n\n")
    f.write("Ideas:\n- Use grep to scan logs\n- Maybe cron?\n- Alert on 500 errors\n")
    f.write("- Need to check payment failures\n")
    f.write("TODO: Figure out how to actually do this\n")

# Old heartbeat config (distractor)
with open(f"{WORKSPACE}/memory/sessions/heartbeat_config.json", "w") as f:
    import json
    json.dump({
        "interval_minutes": 30,
        "last_run": "2024-01-15T08:00:00Z",
        "status": "unknown"
    }, f, indent=2)

# Architecture doc
with open(f"{WORKSPACE}/docs/architecture/system_overview.md", "w") as f:
    f.write("# E-Commerce Platform Architecture\n\n")
    f.write("## Components\n")
    f.write("- OrderService: Handles order lifecycle\n")
    f.write("- PaymentService: Stripe integration\n")
    f.write("- InventoryService: Stock management\n")
    f.write("- NotificationService: Email/SMS alerts\n\n")
    f.write("## Log Sources\n")
    f.write("- /var/log/app/*.log (application logs)\n")
    f.write("- /var/log/nginx/*.log (access logs)\n")
    f.write("- /var/log/postgres/*.log (DB query logs)\n")

# Skill stubs (exist but are empty, simulating real skill files)
for skill in ["brainstorming", "write-plan", "doing-tasks", "verify-task", "dispatch-multiple-agents"]:
    with open(f"{WORKSPACE}/skills/{skill}/README.md", "w") as f:
        f.write(f"# {skill}\nSkill implementation directory.\n")

# An old, incorrectly structured ongoing-tasks attempt (wrong fields, wrong emojis)
with open(f"{WORKSPACE}/memory/tasks/ongoing-tasks-draft.md", "w") as f:
    f.write("# Ongoing Tasks DRAFT\n\n")
    f.write("## Task: DB Backup\n")
    f.write("- status: ok\n")
    f.write("- frequency: daily\n")
    f.write("- last_run: 2024-02-01\n")

# Frontend distractor
with open(f"{WORKSPACE}/projects/ecommerce/frontend/bundle_stats.json", "w") as f:
    json.dump({"size_kb": 842, "chunks": 14, "unused_exports": 23}, f)

# Infra distractor
with open(f"{WORKSPACE}/projects/ecommerce/infra/terraform_notes.txt", "w") as f:
    f.write("# Terraform Notes\nDo not delete VPC until migration complete.\nRDS instance: db.t3.medium\n")

# Alert config (distractor, wrong format)
with open(f"{WORKSPACE}/ops/alerts/alert_rules.txt", "w") as f:
    f.write("rule: error_rate > 5% => page oncall\n")
    f.write("rule: latency_p99 > 2s => slack alert\n")

# Summary: workspace has no valid ongoing-tasks.md, no brainstorming doc, no write-plan doc
print("Workspace scaffold complete.")
print(f"Files created: {sum(1 for _ in Path(WORKSPACE).rglob('*') if _.is_file())}")