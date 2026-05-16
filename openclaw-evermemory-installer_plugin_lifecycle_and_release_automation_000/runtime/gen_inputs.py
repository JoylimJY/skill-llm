#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory Structure ---
dirs = [
    "scripts",
    "references",
    "src/core",
    "src/memory",
    "src/adapters",
    "tests/unit",
    "tests/integration",
    "config/environments",
    "config/slots",
    "dist",
    "logs",
    "benchmarks",
    "node_modules/.cache",
    "bin",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- package.json (realistic, with teams:dev and teams:release scripts) ---
package_json = {
    "name": "evermemory",
    "version": "0.3.1",
    "description": "EverMemory OpenClaw Plugin",
    "main": "src/core/index.js",
    "scripts": {
        "teams:dev": "node bin/gate-check.js --mode dev",
        "teams:release": "node bin/gate-check.js --mode release",
        "test": "node bin/run-tests.js",
        "lint": "node bin/lint.js",
        "build": "node bin/build.js"
    },
    "keywords": ["openclaw", "memory", "plugin"],
    "author": "EverMemory Team",
    "license": "MIT"
}
with open(os.path.join(workspace, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# --- Distractor files ---

# src/core/index.js
with open(os.path.join(workspace, "src/core/index.js"), "w") as f:
    f.write("""// EverMemory Core
const { MemoryAdapter } = require('../adapters/memory-adapter');
const { SlotBinder } = require('../memory/slot-binder');

class EverMemory {
  constructor(config) {
    this.config = config;
    this.adapter = new MemoryAdapter(config);
    this.slotBinder = new SlotBinder();
  }
  async initialize() {
    await this.slotBinder.bind('memory', 'evermemory');
    return this.adapter.connect();
  }
}
module.exports = { EverMemory };
""")

# src/memory/slot-binder.js
with open(os.path.join(workspace, "src/memory/slot-binder.js"), "w") as f:
    f.write("""// Slot Binder
class SlotBinder {
  bind(slot, plugin) {
    console.log(`Binding slot plugins.slots.${slot}=${plugin}`);
    return true;
  }
}
module.exports = { SlotBinder };
""")

# src/adapters/memory-adapter.js
with open(os.path.join(workspace, "src/adapters/memory-adapter.js"), "w") as f:
    f.write("""// Memory Adapter
class MemoryAdapter {
  constructor(config) { this.config = config; }
  connect() { return Promise.resolve(true); }
}
module.exports = { MemoryAdapter };
""")

# tests/unit/core.test.js
with open(os.path.join(workspace, "tests/unit/core.test.js"), "w") as f:
    f.write("""const { EverMemory } = require('../../src/core/index');
describe('EverMemory core', () => {
  it('should initialize', async () => {
    const em = new EverMemory({});
    const result = await em.initialize();
    expect(result).toBe(true);
  });
});
""")

# tests/integration/gateway.test.js
with open(os.path.join(workspace, "tests/integration/gateway.test.js"), "w") as f:
    f.write("""// Integration test for gateway slot binding
describe('Gateway integration', () => {
  it('should confirm slot binding', () => {
    // placeholder
    expect(true).toBe(true);
  });
});
""")

# config/environments/dev.json
with open(os.path.join(workspace, "config/environments/dev.json"), "w") as f:
    json.dump({
        "gateway": {"host": "localhost", "port": 7430},
        "plugin": {"slot": "memory", "name": "evermemory"},
        "recall_target": 0.95
    }, f, indent=2)

# config/environments/prod.json
with open(os.path.join(workspace, "config/environments/prod.json"), "w") as f:
    json.dump({
        "gateway": {"host": "gateway.prod.internal", "port": 7430},
        "plugin": {"slot": "memory", "name": "evermemory"},
        "recall_target": 0.95
    }, f, indent=2)

# config/slots/memory.json
with open(os.path.join(workspace, "config/slots/memory.json"), "w") as f:
    json.dump({
        "slot": "plugins.slots.memory",
        "current": "none",
        "candidates": ["evermemory", "simplemem"]
    }, f, indent=2)

# references/publish-and-install-playbook.md
with open(os.path.join(workspace, "references/publish-and-install-playbook.md"), "w") as f:
    f.write("""# Publish and Install Playbook

## Pre-publish Checklist
- [ ] `clawhub whoami` returns a valid user
- [ ] `npm whoami` returns a valid user
- [ ] `npm run teams:release` exits 0
- [ ] recall benchmark >= 0.90

## Install Plugin (Development)
Always use `--source local` with `--link` for development installs.
Always pass `--bind-slot` to register `plugins.slots.memory=evermemory`.
Always pass `--restart-gateway` to hot-reload the gateway with new bindings.

## Skill Publish
`publish_skill.sh` accepts `--version` and `--changelog`.

## Plugin Publish
Always use `--dry-run` first. If output looks correct, run without it.
Always capture stdout to an evidence artifact before declaring success.

## Failure Recovery
If gateway refuses to bind, check `openclaw gateway status` manually.
""")

# benchmarks/recall-results.json (distractor - outdated)
with open(os.path.join(workspace, "benchmarks/recall-results.json"), "w") as f:
    json.dump({
        "run_date": "2024-01-15",
        "recall": 0.87,
        "precision": 0.91,
        "note": "Pre-optimization run — do not use for release gate"
    }, f, indent=2)

# logs/install.log (distractor - old failed attempt)
with open(os.path.join(workspace, "logs/install.log"), "w") as f:
    f.write("""[2024-01-15 10:23:11] install_plugin.sh: started
[2024-01-15 10:23:12] ERROR: --bind-slot flag missing, slot not registered
[2024-01-15 10:23:12] WARN: gateway not restarted
[2024-01-15 10:23:13] install_plugin.sh: failed
""")

# dist/ distractor
with open(os.path.join(workspace, "dist/evermemory-0.3.1.tgz"), "w") as f:
    f.write("FAKE_ARCHIVE_CONTENT")

# node_modules/.cache distractor
with open(os.path.join(workspace, "node_modules/.cache/build-cache.json"), "w") as f:
    json.dump({"cached": True, "ts": 1705320191}, f)

# bin/gate-check.js — will be replaced by real mock in setup
with open(os.path.join(workspace, "bin/gate-check.js"), "w") as f:
    f.write("// placeholder replaced by setup\n")

# bin/run-tests.js
with open(os.path.join(workspace, "bin/run-tests.js"), "w") as f:
    f.write("console.log('All tests passed'); process.exit(0);\n")

# bin/lint.js
with open(os.path.join(workspace, "bin/lint.js"), "w") as f:
    f.write("console.log('Lint OK'); process.exit(0);\n")

# bin/build.js
with open(os.path.join(workspace, "bin/build.js"), "w") as f:
    f.write("console.log('Build OK'); process.exit(0);\n")

print("Workspace generated successfully.")