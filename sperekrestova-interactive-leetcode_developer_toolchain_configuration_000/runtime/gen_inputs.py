import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

# Workspace root — we'll build under /home/devuser/workspace
workspace = Path("/home/devuser/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Deeply nested distractor structure ──────────────────────────────────────
dirs = [
    "docs/architecture",
    "docs/onboarding/legacy",
    "infra/mcp/configs/old",
    "infra/mcp/configs/draft",
    "infra/vscode",
    "scripts/setup",
    "scripts/teardown",
    "team/alice",
    "team/bob",
    "tools/linters",
    "tools/formatters",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files (wrong/partial/outdated configs) ──────────────────────

# Outdated MCP config with wrong package name, no version pin, wrong transport
(workspace / "infra/mcp/configs/old/mcp_server.json").write_text(json.dumps({
    "mcpServers": {
        "leetcode": {
            "command": "node",
            "args": ["leetcode-mcp-server"],
            "transport": "http"
        }
    }
}, indent=2))

# Draft config with @latest (wrong — should be pinned)
(workspace / "infra/mcp/configs/draft/mcp_config_draft.json").write_text(json.dumps({
    "mcpServers": {
        "leetcode": {
            "command": "npx",
            "args": ["-y", "@sperekrestova/interactive-leetcode-mcp@latest"]
        }
    }
}, indent=2))

# Wrong credentials template (wrong fields, wrong path hint)
(workspace / "infra/mcp/configs/old/credentials_template.json").write_text(json.dumps({
    "username": "",
    "password": "",
    "token": "",
    "created": ""
}, indent=2))

# Outdated onboarding doc referencing wrong steps
(workspace / "docs/onboarding/legacy/setup_guide.md").write_text("""# LeetCode Setup (OUTDATED - DO NOT USE)

1. Install leetcode-cli globally
2. Run `leetcode login`
3. Start coding immediately after login
4. Submit with `leetcode submit`

Language codes:
- Python -> python (NOTE: this is outdated)
- JavaScript -> js
""")

# Fake session flow document with wrong order
(workspace / "docs/architecture/session_flow_wrong.md").write_text("""# Session Flow (DRAFT - UNVERIFIED)

Step 1: Select a problem
Step 2: Call get_started
Step 3: Submit solution
Step 4: Authenticate if needed
""")

# Distractor credentials file with wrong permissions (will be 0644)
wrong_creds_path = workspace / "team/alice/sample_credentials.json"
wrong_creds_path.write_text(json.dumps({
    "LEETCODE_SESSION": "example_session_token",
    "csrftoken": "example_csrf",
    "created_at": "2024-01-01T00:00:00Z"
}, indent=2))
os.chmod(wrong_creds_path, 0o644)  # Wrong permissions intentionally

# Various distractor scripts
(workspace / "scripts/setup/install_node.sh").write_text("#!/bin/bash\nnvm install 18\n")
(workspace / "scripts/teardown/cleanup.sh").write_text("#!/bin/bash\nrm -rf ~/.leetcode\n")
(workspace / "tools/linters/eslint_config.json").write_text('{"extends": "eslint:recommended"}\n')
(workspace / "tools/formatters/prettier.json").write_text('{"semi": true, "singleQuote": false}\n')
(workspace / "team/bob/notes.txt").write_text("TODO: figure out which MCP version to use\n")
(workspace / "docs/architecture/overview.md").write_text("# System Architecture\n\nSee infra/mcp for MCP server config.\n")

# ── 3. The actual task brief ───────────────────────────────────────────────────
# This is the "messy" handover note the agent receives as context in the workspace.
# It describes what is NEEDED but intentionally has gaps and misinformation.
(workspace / "HANDOVER_NOTES.txt").write_text("""ONBOARDING HANDOVER - LeetCode Practice System Setup
======================================================

We are onboarding new devs onto our team's LeetCode practice system.
The setup requires three deliverables:

[A] MCP Server Configuration
    - File to create: mcp_server_config.json  (place it anywhere in workspace)
    - Should configure the LeetCode MCP server correctly for production use.
    - Someone mentioned we should NOT use @latest for stability reasons.
    - Old configs are in infra/mcp/configs/old/ but they may be outdated.

[B] Credential Store Bootstrap
    - Developers need a credentials file at the correct system path.
    - It should contain placeholder values for the three required fields.
    - File permissions matter for security — check what the spec says.
    - NOTE: The credentials template in infra/mcp/configs/old/ uses WRONG field names.

[C] Session Workflow Reference
    - File to create: session_workflow.json  (place it anywhere in workspace)
    - Document the mandatory ordered steps of a session as a JSON array of step names.
    - Also include the language submission mapping (what code to pass for each language).
    - The doc in docs/onboarding/legacy/ is OUTDATED — do not trust it.

Good luck. Check the SKILL.md for the authoritative spec.
""")

print("Workspace generated at", workspace)
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(" ", f)