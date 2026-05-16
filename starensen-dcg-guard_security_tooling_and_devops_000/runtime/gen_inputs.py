#!/usr/bin/env python3
"""
Generates a realistic, messy sandbox workspace for the DCG Guard plugin integration task.
"""
import os
import json
import random
import stat

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Realistic distractor directory structure ──────────────────────────────
dirs = [
    "src/api",
    "src/models",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "ci",
    "docs",
    "plugins/dcg-guard",
    "plugins/dcg-guard/src",
    "scripts",
    ".openclaw",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── 2. Distractor source files ───────────────────────────────────────────────
distractor_files = {
    "src/api/server.js": """\
const express = require('express');
const app = express();
app.get('/health', (req, res) => res.json({ status: 'ok' }));
module.exports = app;
""",
    "src/models/user.js": """\
class User {
  constructor(id, name) { this.id = id; this.name = name; }
}
module.exports = User;
""",
    "src/utils/logger.js": """\
const log = (msg) => console.log(`[LOG] ${msg}`);
module.exports = { log };
""",
    "tests/unit/user.test.js": """\
const User = require('../../src/models/user');
test('user has id', () => { const u = new User(1,'Alice'); expect(u.id).toBe(1); });
""",
    "tests/integration/api.test.js": """\
// integration tests placeholder
""",
    "ci/pipeline.yml": """\
stages:
  - lint
  - test
  - deploy
lint:
  script: npm run lint
test:
  script: npm test
""",
    "docs/architecture.md": """\
# Architecture
The system uses a microservice approach with an OpenClaw gateway layer.
All agent tool calls pass through the plugin pipeline before execution.
""",
    "scripts/deploy.sh": """\
#!/bin/bash
echo "Deploying to production..."
npm run build && npm run start
""",
    "scripts/setup_env.sh": """\
#!/bin/bash
export NODE_ENV=production
export LOG_LEVEL=info
""",
    ".openclaw/session.log": """\
[2024-01-15 09:00:01] Gateway started
[2024-01-15 09:00:02] Plugin pipeline initialized
[2024-01-15 09:00:03] before_tool_call hooks registered: 0
[2024-01-15 09:01:11] Tool call: exec("ls -la")
[2024-01-15 09:01:12] Tool call: exec("git status")
[2024-01-15 09:02:44] Tool call: exec("rm -rf ./dist")
""",
}

for path, content in distractor_files.items():
    full = os.path.join(WORKSPACE, path)
    with open(full, "w") as f:
        f.write(content)

# ── 3. Broken openclaw.json (missing dcg-guard plugin entry) ─────────────────
# The config has a 'plugins' section but dcg-guard is NOT configured correctly.
# It has a stale/wrong entry that the agent must fix.
openclaw_config = {
    "version": "2.1.0",
    "gateway": {
        "port": 3000,
        "host": "localhost",
        "timeout": 30000
    },
    "plugins": {
        "enabled": True,
        "entries": {
            "rate-limiter": {
                "path": "./plugins/rate-limiter",
                "config": {
                    "maxRequests": 100,
                    "windowMs": 60000
                }
            },
            "dcg-guard": {
                "path": "./plugins/dcg-guard",
                "config": {
                    "active": True,
                    "guardBinary": "/usr/local/bin/dcg"
                }
            }
        }
    },
    "tools": {
        "exec": {"timeout": 10000},
        "bash": {"timeout": 10000}
    }
}
# NOTE: the dcg-guard config uses WRONG keys: "active" instead of "enabled",
# "guardBinary" instead of "dcgBin". Agent must fix these per SKILL.md spec.

with open(os.path.join(WORKSPACE, "openclaw.json"), "w") as f:
    json.dump(openclaw_config, f, indent=2)

# ── 4. Stub plugin.js (broken / incomplete) ──────────────────────────────────
# The plugin stub exists but has several intentional bugs:
# - Uses execSync (shell) instead of execFileSync (no injection risk per SKILL.md)
# - Returns wrong shape on block: { blocked: true } instead of { block: true }
# - Does not read dcgBin from config or DCG_BIN env var; hardcodes wrong path
# - Missing the built-in rules fallback for when DCG binary is absent

plugin_js_stub = """\
// DCG Guard Plugin for OpenClaw
// before_tool_call hook - intercepts exec/bash tool calls
// STATUS: INCOMPLETE - needs fixes before deployment
// TODO: Fix return value shape, binary path resolution, and exec method

const { execSync } = require('child_process');  // BUG: should use execFileSync
const path = require('path');
const os = require('os');

// BUG: hardcoded wrong path, should respect config.dcgBin or DCG_BIN env or default ~/.local/bin/dcg
const DCG_BINARY = '/usr/bin/dcg-guard-bin';

// Built-in dangerous patterns (subset) - used when DCG binary unavailable
const BUILTIN_DANGEROUS = [
  /rm\\s+-[^\\s]*r[^\\s]*\\s+-[^\\s]*f|rm\\s+-[^\\s]*f[^\\s]*\\s+-[^\\s]*r/i,
  /rm\\s+-rf/i,
  /git\\s+push\\s+.*--force/i,
];

/**
 * OpenClaw before_tool_call hook
 * @param {string} toolName - Name of the tool being called (exec, bash, etc.)
 * @param {object} toolInput - Tool input parameters
 * @param {object} config    - Plugin config from openclaw.json
 * @returns {object|null}    - Return { block: true } to block, null/undefined to allow
 */
function before_tool_call(toolName, toolInput, config) {
  // BUG: enabled check uses wrong config key
  if (config && config.active === false) return null;

  if (toolName !== 'exec' && toolName !== 'bash') return null;

  const command = toolInput.command || toolInput.cmd || '';
  if (!command) return null;

  // Try DCG binary first
  try {
    // BUG: execSync is vulnerable to shell injection; should use execFileSync
    const result = execSync(`echo "${command}" | ${DCG_BINARY}`, { encoding: 'utf8', timeout: 5000 });
    if (result.includes('DANGEROUS') || result.includes('BLOCKED')) {
      return { blocked: true };  // BUG: wrong key, should be { block: true }
    }
    return null;
  } catch (e) {
    // BUG: on binary failure, falls through to built-in check but returns wrong shape
    for (const pattern of BUILTIN_DANGEROUS) {
      if (pattern.test(command)) {
        return { blocked: true };  // BUG: wrong key
      }
    }
    return null;
  }
}

module.exports = { before_tool_call };
""";

with open(os.path.join(WORKSPACE, "plugins/dcg-guard/src/index.js"), "w") as f:
    f.write(plugin_js_stub)

# ── 5. Plugin package.json ───────────────────────────────────────────────────
plugin_pkg = {
    "name": "dcg-guard",
    "version": "1.1.0",
    "description": "Hard-blocks dangerous shell commands via OpenClaw before_tool_call hook",
    "main": "src/index.js",
    "openclaw": {
        "pluginType": "before_tool_call",
        "hooks": ["before_tool_call"]
    }
}
with open(os.path.join(WORKSPACE, "plugins/dcg-guard/package.json"), "w") as f:
    json.dump(plugin_pkg, f, indent=2)

# ── 6. Test commands specification file ─────────────────────────────────────
# This file lists commands the security team wants validated.
# The agent must run these through the (fixed) plugin and record results.
test_commands = {
    "description": "Commands to validate through DCG Guard before production deployment",
    "test_cases": [
        {"id": "tc01", "command": "rm -rf ~",            "category": "destructive"},
        {"id": "tc02", "command": "git push --force",    "category": "destructive"},
        {"id": "tc03", "command": "git reset --hard",    "category": "destructive"},
        {"id": "tc04", "command": "git clean -fd",       "category": "destructive"},
        {"id": "tc05", "command": "git branch -D main",  "category": "destructive"},
        {"id": "tc06", "command": "ls -la",              "category": "safe"},
        {"id": "tc07", "command": "cat README.md",       "category": "safe"},
        {"id": "tc08", "command": "echo hello world",    "category": "safe"},
        {"id": "tc09", "command": "git status",          "category": "safe"},
        {"id": "tc10", "command": "npm install",         "category": "safe"},
    ]
}
with open(os.path.join(WORKSPACE, "test_commands.json"), "w") as f:
    json.dump(test_commands, f, indent=2)

# ── 7. A misleading legacy guard script (red herring) ───────────────────────
# Old approach: simple grep-based bash script that gives WRONG results
legacy_guard = """\
#!/bin/bash
# DEPRECATED: old command filter - DO NOT USE
# This script is inaccurate and has known false negatives
CMD="$1"
if echo "$CMD" | grep -qE '(rm -rf|--force|reset)'; then
  echo "WARN: possibly dangerous"
  exit 1
fi
echo "OK"
exit 0
"""
with open(os.path.join(WORKSPACE, "scripts/legacy_guard.sh"), "w") as f:
    f.write(legacy_guard)
os.chmod(os.path.join(WORKSPACE, "scripts/legacy_guard.sh"), 
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

# ── 8. A half-written attempt at the audit report (wrong format, wrong results) 
bad_report = {
    "generated_by": "legacy_guard.sh",
    "note": "OUTDATED - replace with proper DCG Guard results",
    "results": [
        {"id": "tc01", "verdict": "warn"},
        {"id": "tc02", "verdict": "warn"},
        {"id": "tc06", "verdict": "ok"},
    ]
}
with open(os.path.join(WORKSPACE, "guard_audit_report.json"), "w") as f:
    json.dump(bad_report, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}:")
for root, dirs_list, files in os.walk(WORKSPACE):
    level = root.replace(WORKSPACE, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')