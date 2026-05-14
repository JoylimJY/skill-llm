import os
import json
import random

random.seed(42)

base = "/workspace"

# --- Deep distractor directory structure ---
dirs = [
    "infra/nginx/conf.d",
    "infra/nginx/logs",
    "infra/redis/config",
    "services/auth/middleware",
    "services/billing/models",
    "services/billing/controllers",
    "services/gateway/routes",
    "services/gateway/plugins",
    "monitoring/alerts",
    "monitoring/dashboards",
    "scripts/migrations",
    "scripts/cleanup",
    "docs/api",
    "docs/internal",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "infra/nginx/conf.d/default.conf": "server { listen 80; location / { proxy_pass http://gateway:3000; } }",
    "infra/nginx/logs/access.log": "192.168.1.1 - - [01/Jan/2024] \"GET /api/v1/data\" 200",
    "infra/redis/config/redis.conf": "maxmemory 256mb\nmaxmemory-policy allkeys-lru",
    "services/auth/middleware/jwt.js": "// JWT verification middleware\nmodule.exports = (req, res, next) => { next(); };",
    "services/billing/models/subscription.js": "// Subscription model\nconst tiers = ['free', 'basic', 'pro', 'enterprise'];",
    "services/billing/controllers/invoiceController.js": "// Invoice generation logic placeholder",
    "services/gateway/routes/v1.js": "// Route definitions for API v1",
    "services/gateway/plugins/logger.js": "// Request logging plugin",
    "monitoring/alerts/high_error_rate.yaml": "alert: HighErrorRate\nexpr: rate(http_errors[5m]) > 0.05",
    "monitoring/dashboards/overview.json": json.dumps({"title": "API Gateway Overview", "panels": []}),
    "scripts/migrations/001_add_users.sql": "ALTER TABLE users ADD COLUMN tier VARCHAR(20) DEFAULT 'free';",
    "scripts/cleanup/purge_old_logs.sh": "#!/bin/bash\nfind /var/log -name '*.log' -mtime +30 -delete",
    "docs/api/openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: Gateway API\n  version: 1.0.0",
    "docs/internal/rate_limit_notes.md": "# Rate Limit Notes\nWIP - ask engineering for current thresholds.",
    "tests/unit/auth.test.js": "describe('auth', () => { it('should validate tokens', () => {}); });",
    "tests/integration/gateway.test.js": "describe('gateway', () => { it('should route requests', () => {}); });",
}
for path, content in distractor_files.items():
    with open(os.path.join(base, path), "w") as f:
        f.write(content)

# --- The SKILL file: RateLimiter implementation ---
rate_limiter_src = r"""
class RateLimiter {
  constructor(options = {}) {
    this.tiers = options.tiers || {
      free: { requests: 10, window: 60000 },
      basic: { requests: 100, window: 60000 },
      pro: { requests: 1000, window: 60000 }
    };
    this.requests = new Map();
  }

  checkLimit(userId, tier = 'free') {
    const tierConfig = this.tiers[tier];
    if (!tierConfig) {
      return { allowed: false, reason: 'invalid_tier' };
    }

    const now = Date.now();
    const userRequests = this.requests.get(userId) || [];

    // Remove old requests outside window
    const validRequests = userRequests.filter(
      timestamp => now - timestamp < tierConfig.window
    );

    // Check if under limit
    if (validRequests.length >= tierConfig.requests) {
      const oldestRequest = validRequests[0];
      const resetIn = tierConfig.window - (now - oldestRequest);

      return {
        allowed: false,
        reason: 'rate_limit_exceeded',
        limit: tierConfig.requests,
        remaining: 0,
        resetIn: Math.ceil(resetIn / 1000)
      };
    }

    // Add current request
    validRequests.push(now);
    this.requests.set(userId, validRequests);

    return {
      allowed: true,
      limit: tierConfig.requests,
      remaining: tierConfig.requests - validRequests.length,
      resetIn: Math.ceil(tierConfig.window / 1000)
    };
  }

  resetUser(userId) {
    this.requests.delete(userId);
  }

  getStats(userId) {
    const userRequests = this.requests.get(userId) || [];
    return {
      totalRequests: userRequests.length,
      oldestRequest: userRequests[0] || null,
      newestRequest: userRequests[userRequests.length - 1] || null
    };
  }
}

module.exports = { RateLimiter };
"""
with open(os.path.join(base, "services/gateway/plugins/rateLimiter.js"), "w") as f:
    f.write(rate_limiter_src)

# --- The messy audit input: a JSON file with subscription users and request sequences ---
# Each entry: userId, tier (may be non-standard/custom), requestCount (how many times to call checkLimit)
# Some users are flagged for reset after audit.
# The agent must use custom tiers (not defaults) as specified in the audit config below.

audit_input = {
    "description": "Batch API audit for billing cycle 2024-Q1",
    "tier_config": {
        "starter": {"requests": 5, "window": 30000},
        "growth": {"requests": 20, "window": 30000},
        "scale": {"requests": 3, "window": 30000}
    },
    "users": [
        {"userId": "u_alice", "tier": "starter", "requestCount": 4},
        {"userId": "u_bob", "tier": "starter", "requestCount": 6},
        {"userId": "u_carol", "tier": "growth", "requestCount": 20},
        {"userId": "u_dave", "tier": "scale", "requestCount": 3},
        {"userId": "u_eve", "tier": "scale", "requestCount": 5},
        {"userId": "u_frank", "tier": "growth", "requestCount": 1},
        {"userId": "u_ghost", "tier": "phantom", "requestCount": 2}
    ],
    "reset_after_audit": ["u_bob", "u_eve"]
}

with open(os.path.join(base, "services/gateway/audit_input.json"), "w") as f:
    json.dump(audit_input, f, indent=2)

# --- A stale/incorrect legacy rate limit config (distractor) ---
legacy_config = {
    "tiers": {
        "free": {"requests": 10, "window": 60000},
        "basic": {"requests": 100, "window": 60000},
        "pro": {"requests": 1000, "window": 60000}
    },
    "note": "DEPRECATED - do not use for 2024 billing"
}
with open(os.path.join(base, "services/gateway/legacy_rate_config.json"), "w") as f:
    json.dump(legacy_config, f, indent=2)

# --- Partial/broken JS file (distractor) ---
with open(os.path.join(base, "services/gateway/plugins/oldThrottler.js"), "w") as f:
    f.write("// Old throttler - BROKEN, do not use\nconst limit = (req) => { throw new Error('not implemented'); };\n")

print("Workspace generated successfully.")