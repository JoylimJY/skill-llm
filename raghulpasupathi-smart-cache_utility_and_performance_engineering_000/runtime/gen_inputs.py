import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "src/core",
    "src/utils",
    "src/middleware",
    "tests/unit",
    "tests/integration",
    "config/env",
    "config/schemas",
    "docs/api",
    "docs/internal",
    "scripts/deploy",
    "scripts/bench",
    "lib/adapters",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "src/core/index.js":          "module.exports = require('./app');",
    "src/core/app.js":            "// main application bootstrap\nconst express = require('express');\n",
    "src/utils/logger.js":        "console.log('logger stub');",
    "src/middleware/auth.js":     "module.exports = (req, res, next) => next();",
    "tests/unit/app.test.js":     "describe('app', () => { it('starts', () => {}); });",
    "tests/integration/api.test.js": "// integration placeholder",
    "config/env/dev.json":        json.dumps({"env": "development", "port": 3000}),
    "config/env/prod.json":       json.dumps({"env": "production",  "port": 8080}),
    "config/schemas/cache.schema.json": json.dumps({
        "type": "object",
        "properties": {
            "strategy": {"type": "string"},
            "maxSize":  {"type": "integer"},
            "defaultTTL": {"type": "integer"}
        }
    }),
    "docs/api/endpoints.md":      "# API Endpoints\n\n- GET /health\n- POST /data\n",
    "docs/internal/architecture.md": "# Architecture\n\nMicroservices with Redis-backed cache layer.\n",
    "scripts/deploy/release.sh":  "#!/bin/bash\necho 'deploy script'",
    "scripts/bench/load_test.js": "// k6 load test placeholder\nexport default function() {}",
    "lib/adapters/redis.js":      "// redis adapter stub\nmodule.exports = {};",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The SmartCache implementation (as described in SKILL.md) ─────────────────
smart_cache_js = r"""
class SmartCache {
  constructor(options = {}) {
    this.strategy = options.strategy || 'lru';
    this.maxSize = options.maxSize || 500;
    this.defaultTTL = options.defaultTTL || 3600000;

    this.cache = new Map();
    this.accessCount = new Map();
    this.accessOrder = [];
  }

  set(key, value, ttl = this.defaultTTL) {
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      this.evict();
    }

    const entry = {
      value,
      expiresAt: Date.now() + ttl,
      createdAt: Date.now()
    };

    this.cache.set(key, entry);
    this.accessCount.set(key, 0);
    this.updateAccessOrder(key);

    return true;
  }

  get(key) {
    const entry = this.cache.get(key);

    if (!entry) {
      return { hit: false, value: null };
    }

    if (Date.now() > entry.expiresAt) {
      this.delete(key);
      return { hit: false, value: null, reason: 'expired' };
    }

    this.accessCount.set(key, (this.accessCount.get(key) || 0) + 1);
    this.updateAccessOrder(key);

    return { hit: true, value: entry.value };
  }

  delete(key) {
    this.cache.delete(key);
    this.accessCount.delete(key);
    this.accessOrder = this.accessOrder.filter(k => k !== key);
  }

  evict() {
    if (this.strategy === 'lru') {
      this.evictLRU();
    } else if (this.strategy === 'lfu') {
      this.evictLFU();
    }
  }

  evictLRU() {
    if (this.accessOrder.length > 0) {
      const keyToEvict = this.accessOrder[0];
      this.delete(keyToEvict);
    }
  }

  evictLFU() {
    let minCount = Infinity;
    let keyToEvict = null;

    for (const [key, count] of this.accessCount.entries()) {
      if (count < minCount) {
        minCount = count;
        keyToEvict = key;
      }
    }

    if (keyToEvict) {
      this.delete(keyToEvict);
    }
  }

  updateAccessOrder(key) {
    this.accessOrder = this.accessOrder.filter(k => k !== key);
    this.accessOrder.push(key);
  }

  clear() {
    this.cache.clear();
    this.accessCount.clear();
    this.accessOrder = [];
  }

  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      strategy: this.strategy,
      hitRate: this.calculateHitRate()
    };
  }

  calculateHitRate() {
    return Math.round((this.cache.size / this.maxSize) * 100);
  }
}

module.exports = { SmartCache };
"""

lib_cache_path = os.path.join(workspace, "lib/adapters/smart_cache.js")
with open(lib_cache_path, "w") as f:
    f.write(smart_cache_js)

# ── Scenario spec the agent must implement & report on ───────────────────────
# This file tells the agent WHAT scenarios to run, but NOT how.
scenario_spec = {
    "description": (
        "Run these three validation scenarios against the SmartCache module "
        "at lib/adapters/smart_cache.js and write results to cache_report.json."
    ),
    "scenarios": [
        {
            "id": "lfu_eviction",
            "description": (
                "Create an LFU cache with maxSize=3. "
                "Insert keys A, B, C. "
                "Call get() on A twice, get() on B once, do NOT call get() on C. "
                "Insert a new key D (forcing an eviction). "
                "Report which key was evicted."
            )
        },
        {
            "id": "ttl_expiry",
            "description": (
                "Create an LRU cache with defaultTTL=50 (milliseconds). "
                "Insert key X with value 'hello'. "
                "Immediately call get('X') — should hit. "
                "Wait 100 ms, then call get('X') again — should miss with reason 'expired'. "
                "Report both get results."
            )
        },
        {
            "id": "stats_check",
            "description": (
                "Create an LRU cache with maxSize=10. "
                "Insert 7 keys (K1..K7). "
                "Call getStats() and report the full stats object."
            )
        }
    ]
}

scenario_path = os.path.join(workspace, "scripts/bench/cache_scenarios.json")
with open(scenario_path, "w") as f:
    json.dump(scenario_spec, f, indent=2)

print("Workspace generated successfully.")
print(f"Scenario spec: {scenario_path}")
print(f"SmartCache module: {lib_cache_path}")