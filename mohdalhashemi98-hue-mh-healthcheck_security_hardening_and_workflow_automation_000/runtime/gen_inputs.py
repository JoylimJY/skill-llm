import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create deeply nested distractor directory structure ---
dirs = [
    "src/api/routes",
    "src/api/middleware",
    "src/core/engine",
    "src/core/plugins",
    "config/environments",
    "config/secrets",
    "logs/archive",
    "logs/current",
    "tests/unit",
    "tests/integration",
    "scripts/deploy",
    "scripts/maintenance",
    "docs/internal",
    "memory",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/api/routes/payments.js": "// Payment routing logic\nmodule.exports = router;",
    "src/api/routes/users.js": "// User auth routes",
    "src/api/middleware/auth.js": "// JWT auth middleware",
    "src/core/engine/processor.py": "# Core processing engine\nclass Processor: pass",
    "src/core/plugins/loader.py": "# Plugin loader\nimport importlib",
    "config/environments/production.yml": "env: production\ndebug: false\nport: 8443",
    "config/environments/staging.yml": "env: staging\ndebug: true\nport: 8080",
    "config/secrets/vault.conf": "# DO NOT COMMIT\nvault_addr=https://vault.internal:8200",
    "logs/archive/2024-11-15.log": "[INFO] System started\n[WARN] High memory usage detected",
    "logs/archive/2024-12-01.log": "[INFO] Backup completed\n[INFO] 3 services restarted",
    "logs/current/app.log": "[INFO] 2025-01-10 API request processed\n[ERROR] Connection timeout",
    "tests/unit/test_processor.py": "import pytest\ndef test_basic(): assert 1 == 1",
    "tests/integration/test_api.py": "import requests\ndef test_health(): pass",
    "scripts/deploy/rollback.sh": "#!/bin/bash\necho 'Rolling back deployment...'",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\nfind /tmp -mtime +7 -delete",
    "docs/internal/architecture.md": "# Architecture\nThis system uses a microservices approach.",
    "data/raw/events_2025.csv": "timestamp,event_type,user_id\n2025-01-01,login,u001",
    "data/processed/summary.json": json.dumps({"total_events": 1500, "anomalies": 3}),
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- Create an OLD stale memory file (from a previous session, not today) ---
# This is a distractor - exists but is from a prior date
old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
old_memory = workspace / "memory" / f"{old_date}.md"
old_memory.write_text(f"""# Session Notes - {old_date}

## Initial setup
- Installed OpenClaw v1.2.0
- Configured gateway on port 3000
- No hardening steps taken yet

""")

# --- Create a MEMORY.md stub (long-term memory) ---
memory_md = workspace / "MEMORY.md"
memory_md.write_text("""# Long-term Memory

## System Profile
- Deployment: Dedicated remote server (VPS)
- OS: Linux (Ubuntu 22.04)
- Role: Headless OpenClaw gateway host
- Last audit: Never performed
- Risk posture: Not yet defined

## Preferences
- Update cadence: Unknown
- Backup status: Unknown
""")

# --- Create a mock openclaw state file showing one existing cron job ---
# The job `healthcheck:update-status` already exists with id=7
# `healthcheck:security-audit` does NOT exist yet
openclaw_state = workspace / ".openclaw_state.json"
state_data = {
    "version": "1.8.3",
    "update_available": True,
    "latest_version": "1.9.1",
    "channel": "stable",
    "gateway": {
        "status": "running",
        "bind": "127.0.0.1:3000",
        "identity": "fintech-dev-gateway-01"
    },
    "cron_jobs": [
        {
            "id": 7,
            "name": "healthcheck:update-status",
            "schedule": "0 9 * * 1",
            "command": "openclaw update status",
            "output_location": "/workspace/logs/current/update-status.log",
            "created": "2024-12-01T09:00:00Z"
        }
    ],
    "audit_results": {
        "deep": {
            "timestamp": "2025-07-08T10:00:00Z",
            "findings": [
                {"severity": "HIGH", "issue": "Gateway API token stored in plaintext config file", "file": "config/secrets/vault.conf"},
                {"severity": "HIGH", "issue": "OpenClaw file permissions on credentials directory too permissive (0755)", "file": "/workspace/.openclaw/creds"},
                {"severity": "MEDIUM", "issue": "Browser control enabled without 2FA on linked accounts"},
                {"severity": "MEDIUM", "issue": "OpenClaw log verbosity exposes request headers"},
                {"severity": "LOW", "issue": "Default session timeout not reduced from 24h"},
            ],
            "openclaw_version": "1.8.3",
            "fix_available": True
        }
    }
}
openclaw_state.write_text(json.dumps(state_data, indent=2))

print("Workspace generated successfully.")
print(f"Old memory file created: memory/{old_date}.md")
print("State file: .openclaw_state.json")