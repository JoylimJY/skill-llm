import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create realistic directory structure with distractor files
dirs = [
    "scripts",
    "catalog",
    "catalog/cache",
    "catalog/vet-results",
    "logs",
    "config",
    "reports/old",
    "reports/archive",
    "docs",
    "tmp",
    ".skill-hub",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "config/settings.yaml": "registry_url: https://clawhub.io\nauto_vet: false\nmax_results: 50\n",
    "config/categories.txt": "DevOps\nAI\nDataOps\nSecurity\nProductivity\nWeb\nDB\n",
    "logs/sync.log": "2024-01-10 12:00:01 INFO Sync started\n2024-01-10 12:00:05 INFO Fetched 3012 skills\n2024-01-10 12:00:07 INFO Done\n",
    "logs/install.log": "2024-01-09 09:15:22 INFO Installed: data-pipeline-runner\n2024-01-09 09:16:01 INFO Installed: sql-query-optimizer\n",
    "docs/CHANGELOG.md": "# Changelog\n## v1.0.0\n- Initial release\n## v0.9.0\n- Beta features\n",
    "docs/architecture.txt": "skill-hub uses a local SQLite catalog with remote sync.\nVetting is purely static analysis.\n",
    "tmp/scratch.json": json.dumps({"note": "temp file, ignore"}),
    "reports/old/report_2023.txt": "Old audit from 2023. Deprecated.\n",
    "reports/archive/q1_2024.txt": "Q1 2024 partial results. Incomplete.\n",
    ".skill-hub/last_sync": "2024-01-10T12:00:07Z\n",
    ".skill-hub/installed.json": json.dumps(["data-pipeline-runner", "sql-query-optimizer", "etl-transformer"]),
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# --- The primary catalog data (used by mock scripts) ---
catalog = [
    # DataOps skills — mix of scores
    {"slug": "data-pipeline-runner", "name": "Data Pipeline Runner", "category": "DataOps", "score": 91, "description": "Orchestrates multi-step ETL pipelines with retry logic.", "installed": True},
    {"slug": "sql-query-optimizer", "name": "SQL Query Optimizer", "category": "DataOps", "score": 78, "description": "Analyzes and rewrites SQL queries for performance.", "installed": True},
    {"slug": "etl-transformer", "name": "ETL Transformer", "category": "DataOps", "score": 65, "description": "Transforms raw CSV/JSON into normalized schemas.", "installed": True},
    {"slug": "stream-aggregator", "name": "Stream Aggregator", "category": "DataOps", "score": 82, "description": "Real-time aggregation of Kafka/Kinesis streams.", "installed": False},
    {"slug": "data-quality-checker", "name": "Data Quality Checker", "category": "DataOps", "score": 71, "description": "Validates datasets against schema rules.", "installed": False},
    {"slug": "sketchy-data-exporter", "name": "Sketchy Data Exporter", "category": "DataOps", "score": 23, "description": "Exports data to remote endpoints.", "installed": False},
    {"slug": "raw-scraper", "name": "Raw Scraper", "category": "DataOps", "score": 41, "description": "Scrapes data from arbitrary web sources.", "installed": False},
    # Other categories (distractors)
    {"slug": "k8s-deployer", "name": "K8s Deployer", "category": "DevOps", "score": 88, "description": "Deploys Kubernetes manifests with rollback.", "installed": False},
    {"slug": "ci-monitor", "name": "CI Monitor", "category": "DevOps", "score": 74, "description": "Monitors CI pipeline health.", "installed": False},
    {"slug": "gpt-assistant", "name": "GPT Assistant", "category": "AI", "score": 55, "description": "Wraps OpenAI API for prompt management.", "installed": False},
    {"slug": "llm-router", "name": "LLM Router", "category": "AI", "score": 67, "description": "Routes prompts to best LLM provider.", "installed": False},
    {"slug": "web-scraper", "name": "Web Scraper", "category": "Web", "score": 60, "description": "General web scraping toolkit.", "installed": False},
    {"slug": "db-migrator", "name": "DB Migrator", "category": "DB", "score": 85, "description": "Schema migration tool with rollback.", "installed": False},
]

with open(os.path.join(workspace, "catalog/catalog.json"), "w") as f:
    json.dump(catalog, f, indent=2)

# --- Vet results data (used by mock vet script) ---
vet_results = {
    "data-pipeline-runner": {
        "slug": "data-pipeline-runner",
        "passed": True,
        "score": 91,
        "code_checks": {"eval_exec": False, "shell_injection": False, "obfuscation": False, "network_access": False, "env_harvesting": False, "destructive_ops": False},
        "nlp_checks": {"hidden_instructions": False, "role_hijacking": False, "invisible_unicode": False, "exfiltration_prompts": False, "authority_escalation": False, "social_engineering": False},
        "summary": "No issues detected. Skill is safe.",
    },
    "sql-query-optimizer": {
        "slug": "sql-query-optimizer",
        "passed": True,
        "score": 78,
        "code_checks": {"eval_exec": False, "shell_injection": False, "obfuscation": False, "network_access": True, "env_harvesting": False, "destructive_ops": False},
        "nlp_checks": {"hidden_instructions": False, "role_hijacking": False, "invisible_unicode": False, "exfiltration_prompts": False, "authority_escalation": False, "social_engineering": False},
        "summary": "Minor: network_access flag detected (telemetry ping). Non-critical.",
    },
    "etl-transformer": {
        "slug": "etl-transformer",
        "passed": True,
        "score": 65,
        "code_checks": {"eval_exec": False, "shell_injection": False, "obfuscation": False, "network_access": False, "env_harvesting": False, "destructive_ops": False},
        "nlp_checks": {"hidden_instructions": False, "role_hijacking": False, "invisible_unicode": False, "exfiltration_prompts": False, "authority_escalation": False, "social_engineering": False},
        "summary": "No issues detected. Skill is safe.",
    },
    "stream-aggregator": {
        "slug": "stream-aggregator",
        "passed": True,
        "score": 82,
        "code_checks": {"eval_exec": False, "shell_injection": False, "obfuscation": False, "network_access": False, "env_harvesting": False, "destructive_ops": False},
        "nlp_checks": {"hidden_instructions": False, "role_hijacking": False, "invisible_unicode": False, "exfiltration_prompts": False, "authority_escalation": False, "social_engineering": False},
        "summary": "No issues detected. Skill is safe.",
    },
    "data-quality-checker": {
        "slug": "data-quality-checker",
        "passed": False,
        "score": 71,
        "code_checks": {"eval_exec": True, "shell_injection": False, "obfuscation": True, "network_access": False, "env_harvesting": False, "destructive_ops": False},
        "nlp_checks": {"hidden_instructions": True, "role_hijacking": False, "invisible_unicode": False, "exfiltration_prompts": False, "authority_escalation": False, "social_engineering": False},
        "summary": "FAIL: eval/exec usage, obfuscation detected, hidden_instructions found.",
    },
}

with open(os.path.join(workspace, "catalog/vet_data.json"), "w") as f:
    json.dump(vet_results, f, indent=2)

print("Workspace initialized successfully.")