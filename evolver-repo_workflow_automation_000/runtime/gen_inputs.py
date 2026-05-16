import os
import json
import random
import string
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "skills/feishu-card",
    "skills/message",
    "skills/code-runner",
    "agents/trading-bot",
    "agents/risk-monitor",
    "logs/archive/2024-Q1",
    "logs/archive/2024-Q2",
    "config/envs",
    "docs/internal",
    "tests/unit",
    "assets/gep",          # exists but intentionally empty / wrong
    "memory",
    "history",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "skills/feishu-card/index.js": "module.exports = async (msg) => { console.log('feishu:', msg); };",
    "skills/feishu-card/package.json": json.dumps({"name": "feishu-card", "version": "1.0.0"}),
    "skills/message/index.js": "module.exports = async (msg) => { console.log('message:', msg); };",
    "skills/code-runner/index.js": "module.exports = async (code) => eval(code);",
    "agents/trading-bot/config.yaml": "model: gpt-4\nmax_tokens: 2000\ntemperature: 0.3\n",
    "agents/risk-monitor/alert_rules.json": json.dumps({"rules": [{"id": "r001", "threshold": 0.05}]}),
    "logs/archive/2024-Q1/run_001.log": "2024-01-15T10:00:00Z INFO Evolution started\n2024-01-15T10:01:05Z ERROR NullPointerException in strategy.js:42\n",
    "logs/archive/2024-Q1/run_002.log": "2024-01-20T09:30:00Z INFO Stable run, no errors detected\n",
    "logs/archive/2024-Q2/run_010.log": "2024-04-02T14:22:11Z WARN High load detected: 2.8\n2024-04-02T14:22:15Z INFO Backing off.\n",
    "config/envs/staging.env": "NODE_ENV=staging\nEVOLVE_LOAD_MAX=1.5\n",
    "docs/internal/architecture.md": "# Architecture\nThis document describes the internal architecture of the agent platform.\n",
    "tests/unit/strategy_test.js": "describe('strategy', () => { it('should select balanced', () => {}); });\n",
    "memory/snapshot_2024_q2.json": json.dumps({"agent": "trading-bot", "skills": ["code-runner"], "last_run": "2024-06-30"}),
    "history/events_archive_2024.jsonl": '{"id":"evt-0001","type":"boot","timestamp":"2024-01-01T00:00:00Z"}\n',
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── Intentionally broken / empty GEP asset files ───────────────────────────
# genes.json: wrong structure (array instead of object with 'genes' key, missing required fields)
bad_genes = [
    {"id": "g001"},   # missing name, description, type
    {"name": "retry-logic"},  # missing id, description, type
]
(WORKSPACE / "assets/gep/genes.json").write_text(json.dumps(bad_genes, indent=2))

# capsules.json: completely wrong format (plain string)
(WORKSPACE / "assets/gep/capsules.json").write_text('"this is not valid capsule data"')

# events.jsonl: has one malformed line
(WORKSPACE / "assets/gep/events.jsonl").write_text(
    '{"id":"ev-bootstrap-000","type":"init"}\n'
    'MALFORMED LINE - not json\n'
)

# ── Broken .env at root (wrong strategy value, missing required vars) ───────
(WORKSPACE / ".env").write_text(
    "# Production environment configuration\n"
    "NODE_ENV=production\n"
    "EVOLVE_LOAD_MAX=3.5\n"
    "EVOLVE_STRATEGY=aggressive\n"   # invalid strategy value
    # EVOLVE_ALLOW_SELF_MODIFY intentionally missing
    # EVOLVE_REPORT_TOOL intentionally missing
)

# ── Stub package.json for the evolver (simulates installed skill) ───────────
(WORKSPACE / "package.json").write_text(json.dumps({
    "name": "capability-evolver",
    "version": "2.3.1",
    "description": "Self-evolution engine for AI agents",
    "main": "index.js",
    "scripts": {"start": "node index.js"}
}, indent=2))

# ── index.js stub ───────────────────────────────────────────────────────────
(WORKSPACE / "index.js").write_text(
    "// Capability Evolver - main entry point\n"
    "const args = process.argv.slice(2);\n"
    "console.log('Evolver started with args:', args);\n"
)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(" ", p.relative_to(WORKSPACE))