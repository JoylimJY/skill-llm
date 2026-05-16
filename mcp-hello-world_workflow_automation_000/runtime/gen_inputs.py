import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic, deeply nested distractor structure simulating a QA/microservices project
dirs = [
    "services/auth-service/src",
    "services/auth-service/tests",
    "services/payment-service/src",
    "services/payment-service/config",
    "services/notification-service/src",
    "infrastructure/docker",
    "infrastructure/k8s",
    "qa/reports/archived",
    "qa/scripts",
    "docs/api",
    "docs/runbooks",
    "node_modules_backup/fake_module/lib",
    "mcp-skill/node_modules/.bin",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "services/auth-service/src/index.js": "// Auth service entry point\nconst express = require('express');\nconst app = express();\napp.listen(3001);\n",
    "services/auth-service/tests/auth.test.js": "describe('auth', () => { it('should login', () => {}); });\n",
    "services/payment-service/src/payment.js": "// Payment processing logic\nmodule.exports = { processPayment: async (amount) => ({ success: true, amount }) };\n",
    "services/payment-service/config/config.json": json.dumps({"env": "staging", "timeout": 5000, "retries": 3}, indent=2),
    "services/notification-service/src/notify.js": "// Notification dispatcher\nasync function send(msg) { console.log(msg); }\n",
    "infrastructure/docker/docker-compose.yml": "version: '3.8'\nservices:\n  auth:\n    image: node:22\n    ports:\n      - '3001:3001'\n",
    "infrastructure/k8s/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: qa-tools\n",
    "qa/reports/archived/report_2025_01.json": json.dumps({"date": "2025-01-15", "status": "passed", "tools_tested": ["legacy_add", "old_greet"], "results": [{"tool": "legacy_add", "result": "3 + 4 = 7"}, {"tool": "old_greet", "result": "Hello, World!"}]}, indent=2),
    "qa/scripts/run_checks.sh": "#!/bin/bash\necho 'Running QA checks...'\n# TODO: update to use new tool server\n",
    "docs/api/tool-server-api.md": "# Tool Server API\n\nThis document describes the legacy tool server API.\n\n## Endpoints\n- POST /add - Add two numbers\n- POST /greet - Greet a user\n\n## Deprecated\nThis REST API is deprecated. Use the new stdio-based protocol.\n",
    "docs/runbooks/incident-2025.md": "# Incident Report 2025-02\n\nThe tool server was unavailable for 2 hours due to misconfigured stdio transport.\n",
    "node_modules_backup/fake_module/lib/index.js": "// legacy backup - do not use\nmodule.exports = {};\n",
    "mcp-skill/node_modules/.bin/.placeholder": "# placeholder\n",
    "qa/audit_template.json": json.dumps({
        "NOTE": "THIS IS AN OUTDATED TEMPLATE - DO NOT USE",
        "tools": [],
        "test_results": {
            "add": "PENDING",
            "greet": "PENDING"
        }
    }, indent=2),
    "package.json": json.dumps({
        "name": "qa-workspace",
        "version": "0.1.0",
        "description": "QA workspace for microservices",
        "scripts": {
            "test": "echo 'no tests configured'"
        }
    }, indent=2),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# The key context file: a QA brief that describes what needs to be done
# in business terms only (no tool hints)
qa_brief = """# QA Audit Brief — Tool Server Verification

**Requested by:** Engineering Lead
**Priority:** High
**Deadline:** ASAP

## Background

Our team has adopted a new local tool-server skill package called `mcp-hello-world`.
Before we roll it out to all engineers, we need a formal audit that proves the server
works correctly and its tools produce the expected outputs.

## What We Need

Please produce a file called `tool_audit_report.json` in the workspace root that contains:

1. The list of all tools exposed by the server (discovered programmatically, not hardcoded).
2. The result of invoking the arithmetic tool with inputs **47** and **38**.
3. The result of invoking the greeting tool with the name **"审计员"**.

The report must capture the *exact* raw text output returned by each tool invocation.

## Notes

- The skill package is available as an npm package: `mcp-hello-world`
- Use whatever CLI tooling comes with the skill ecosystem
- The server should be started fresh for each tool invocation (stateless calls)
- Do NOT hardcode expected outputs — actually run the tools and capture real output
"""

with open(os.path.join(workspace, "QA_BRIEF.md"), "w") as f:
    f.write(qa_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")