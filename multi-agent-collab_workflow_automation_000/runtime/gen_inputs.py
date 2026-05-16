import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─── Create agent-sync skill directory structure ───────────────────────────
skill_dir = workspace / "agent-sync"
(skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
(skill_dir / "templates").mkdir(parents=True, exist_ok=True)
(skill_dir / "docs").mkdir(parents=True, exist_ok=True)
(skill_dir / "archive").mkdir(parents=True, exist_ok=True)

# Write init.sh script
init_sh = r"""#!/usr/bin/env bash
# Agent Sync Project Initializer
set -e

PROJECT_NAME="${1:-MyProject}"
TARGET_DIR="${2:-.}"

echo "Initializing Agent Sync project: $PROJECT_NAME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$SCRIPT_DIR/../templates"

# Copy templates
cp "$TEMPLATES_DIR/TASK.md"          "$TARGET_DIR/TASK.md"
cp "$TEMPLATES_DIR/CHANGELOG.md"     "$TARGET_DIR/CHANGELOG.md"
cp "$TEMPLATES_DIR/CONTEXT.md"       "$TARGET_DIR/CONTEXT.md"
cp "$TEMPLATES_DIR/WEEKLY-REPORT.md" "$TARGET_DIR/WEEKLY-REPORT.md"
cp "$TEMPLATES_DIR/llms.txt"         "$TARGET_DIR/llms.txt"

mkdir -p "$TARGET_DIR/archive"

# Update llms.txt with project name
sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$TARGET_DIR/llms.txt"
sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$TARGET_DIR/TASK.md"
sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$TARGET_DIR/CONTEXT.md"

echo "Done. Files created in $TARGET_DIR"
echo "  TASK.md, CHANGELOG.md, CONTEXT.md, WEEKLY-REPORT.md, llms.txt, archive/"
"""
(skill_dir / "scripts" / "init.sh").write_text(init_sh)
os.chmod(skill_dir / "scripts" / "init.sh", 0o755)

# Write templates
task_template = """# TASK.md — {{PROJECT_NAME}}

## In Progress

- [ ] Task placeholder 1
- [ ] Task placeholder 2

## Recent Completed

<!-- Completed tasks go here -->

## Backlog

- [ ] Future work placeholder
"""
(skill_dir / "templates" / "TASK.md").write_text(task_template)

changelog_template = """# CHANGELOG.md

<!-- Format: YYYY-MM-DD <description> #tag by <model-identity> -->
<!-- One line per entry. Example: -->
<!-- 2026-01-15 Refactored pipeline ingestion logic #refactor by sonnet -->

"""
(skill_dir / "templates" / "CHANGELOG.md").write_text(changelog_template)

context_template = """# CONTEXT.md — {{PROJECT_NAME}}

## Architecture Decisions

<!-- Record major technical decisions here -->

## Key Insights

<!-- Important findings and constraints -->

## Dependencies

<!-- External systems and their roles -->
"""
(skill_dir / "templates" / "CONTEXT.md").write_text(context_template)

weekly_template = """# WEEKLY-REPORT.md

## Period: {{WEEK}}

## Completed This Week

<!-- Summarize from CHANGELOG -->

## CHANGELOG by #tags

<!-- Aggregate entries by #tag -->

## Pattern Discovery

<!-- Operations repeated 3+ times → candidate skill -->

## Archived

<!-- List what was moved to archive/ -->
"""
(skill_dir / "templates" / "WEEKLY-REPORT.md").write_text(weekly_template)

llms_txt = """# llms.txt — Machine-readable project index
project: {{PROJECT_NAME}}
version: 1.0
hot: TASK.md, llms.txt
warm: CHANGELOG.md, CONTEXT.md
cold: archive/
"""
(skill_dir / "templates" / "llms.txt").write_text(llms_txt)

best_practices = """# Best Practices

## CHANGELOG Format
- One line per entry
- Format: `YYYY-MM-DD <description> #tag by <model-identity>`
- Allowed tags: #feature, #bugfix, #refactor, #deploy, #infra, #data, #review
- Agent identity examples: by opus, by sonnet, by flash, by gpt4, by gpt4o

## TASK.md
- Active tasks under "In Progress"
- Completed tasks MOVED (not duplicated) to "Recent Completed"
- Keep "Recent Completed" to last 10 entries max

## Self-Evolution Rule
- Count #tag occurrences across ALL CHANGELOG entries
- If a tag appears 3 or more times → mark in Pattern Discovery as candidate skill
- Candidate skill format: `[CANDIDATE SKILL] #tagname (N occurrences)`

## Archive Rule
- When generating weekly report, move CHANGELOG entries older than 7 days to archive/CHANGELOG-YYYY-MM-DD.md
- Keep current week in CHANGELOG.md
"""
(skill_dir / "docs" / "BEST-PRACTICES.md").write_text(best_practices)

# ─── Create the actual project: "DataPulse ETL Monitor" ───────────────────
project_dir = workspace / "datapulse-etl"
project_dir.mkdir(parents=True, exist_ok=True)

# Messy, incomplete TASK.md (tasks are done but not moved, format is wrong)
messy_task = """# TASK.md — DataPulse ETL Monitor

## In Progress

- [x] Set up Kafka consumer for transaction streams   ← COMPLETED but not moved
- [x] Write unit tests for dedup pipeline             ← COMPLETED but not moved
- [x] Deploy staging environment on k8s               ← COMPLETED but not moved
- [ ] Implement dead-letter queue retry logic
- [ ] Add Prometheus alerting rules for lag > 10s
- [ ] Document runbook for on-call engineers

## Backlog

- [ ] Evaluate Apache Flink for stream joins
- [ ] Cost analysis: S3 vs GCS for archival storage
"""
(project_dir / "TASK.md").write_text(messy_task)

# Messy, incomplete CHANGELOG.md (missing identity, wrong format, mixed tags)
messy_changelog = """# CHANGELOG

2026-06-02 bootstrapped kafka consumer skeleton #feature
2026-06-02 added dedup logic using bloom filter #feature by sonnet
2026-06-03 fixed offset commit race condition #bugfix
2026-06-03 deployed consumer to staging k8s cluster #deploy by sonnet
2026-06-04 added unit tests for dedup pipeline #feature by sonnet
2026-06-04 wrote Dockerfile for consumer service #infra
2026-06-05 tuned kafka partition count to 12 #infra by flash
2026-06-05 code review: dedup module approved #review by opus
2026-06-06 fixed memory leak in bloom filter impl #bugfix by sonnet
2026-06-06 refactored config loading to use env vars #refactor by sonnet
2026-06-07 redeployed to staging after config fix #deploy by flash
2026-06-07 reviewed alerting threshold proposal #review by opus
"""
(project_dir / "CHANGELOG.md").write_text(messy_changelog)

# Sparse CONTEXT.md
sparse_context = """# CONTEXT.md — DataPulse ETL Monitor

## Architecture Decisions

- Chose Kafka over RabbitMQ for partition scalability

## Key Insights

## Dependencies

- Kafka cluster: kafka.internal:9092
- PostgreSQL: pg.internal:5432
"""
(project_dir / "CONTEXT.md").write_text(sparse_context)

# No WEEKLY-REPORT.md yet (agent must create it)
# No llms.txt yet (agent may need to create/update it)

# ─── Distractor files to simulate real project noise ──────────────────────
(project_dir / "src").mkdir(exist_ok=True)
(project_dir / "src" / "consumer.py").write_text("""
# Kafka consumer for DataPulse ETL pipeline
import kafka
def run(): pass
""")
(project_dir / "src" / "dedup.py").write_text("""
# Bloom filter dedup logic
class BloomFilter: pass
""")
(project_dir / "src" / "config.py").write_text("""
import os
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
""")
(project_dir / "tests").mkdir(exist_ok=True)
(project_dir / "tests" / "test_dedup.py").write_text("def test_dedup(): assert True")
(project_dir / "tests" / "test_consumer.py").write_text("def test_consumer(): pass")
(project_dir / "infra").mkdir(exist_ok=True)
(project_dir / "infra" / "k8s-deployment.yaml").write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datapulse-consumer
""")
(project_dir / "infra" / "Dockerfile").write_text("""
FROM python:3.11-slim
COPY src/ /app/
CMD ["python", "/app/consumer.py"]
""")
(project_dir / "infra" / "prometheus-rules.yaml").write_text("""
# TODO: alerting rules for kafka lag
""")
(project_dir / "docs").mkdir(exist_ok=True)
(project_dir / "docs" / "architecture.md").write_text("# Architecture\nKafka → Consumer → Postgres")
(project_dir / "docs" / "runbook-draft.md").write_text("# On-Call Runbook DRAFT\n## TODO: fill in steps")
(project_dir / "archive").mkdir(exist_ok=True)
(project_dir / ".gitignore").write_text("*.pyc\n__pycache__/\n.env\n")
(project_dir / "pyproject.toml").write_text("""
[tool.poetry]
name = "datapulse-etl"
version = "0.1.0"
""")

# ─── Additional distractor: another project dir ───────────────────────────
other_dir = workspace / "legacy-pipeline"
other_dir.mkdir(exist_ok=True)
(other_dir / "CHANGELOG.md").write_text("# Old changelog\n2026-01-01 old stuff #deprecated\n")
(other_dir / "README.md").write_text("# Legacy Pipeline\nDeprecated. Do not use.")
(other_dir / "main.py").write_text("print('legacy')")

# ─── Write a mission brief (not a hint file, just business context) ───────
brief = """# Sprint Handover Brief
Project: DataPulse ETL Monitor
Sprint End: 2026-06-07
Team size: 3 agents (Lead, Engineer, Maintainer roles)

Items known to be completed this week:
- Kafka consumer setup
- Dedup pipeline with unit tests  
- Staging deployment

New items just added to backlog by engineering lead:
- Dead-letter queue retry logic (high priority)
- Prometheus alerting for lag threshold

Key decision made today by lead:
- Selected bloom filter (not Redis SET) for dedup because it reduces memory by 80% at 0.1% false-positive rate.
  This is locked in for v1.0. All future dedup work must extend BloomFilter class.

The collaboration documents are a mess. They need to be fixed and a weekly summary produced.
"""
(workspace / "SPRINT-HANDOVER-BRIEF.md").write_text(brief)

print("Workspace generated successfully.")
print("Structure:")
for p in sorted(workspace.rglob("*")):
    if ".git" not in str(p):
        indent = "  " * (len(p.relative_to(workspace).parts) - 1)
        print(f"{indent}{p.name}{'/' if p.is_dir() else ''}")