#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the token-optimizer task.
This script installs the token-optimizer tool and sets up a realistic messy
workspace that simulates a poorly configured OpenClaw environment.
"""

import os
import json
import subprocess
import sys
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Clone the real token-optimizer from GitHub ──────────────────────────
print("[*] Cloning token-optimizer from GitHub...")
result = subprocess.run(
    ["git", "clone", "https://github.com/smartpeopleconnected/openclaw-token-optimizer", 
     str(WORKSPACE / "token-optimizer")],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"[!] git clone failed: {result.stderr}")
    sys.exit(1)
print("[+] Cloned successfully.")

# ── 2. Create a deeply nested distractor directory structure ────────────────
dirs = [
    "src/api/handlers",
    "src/api/middleware",
    "src/core/models",
    "src/core/utils",
    "src/services/billing",
    "src/services/analytics",
    "tests/unit",
    "tests/integration",
    "config/environments",
    "config/secrets",
    "docs/architecture",
    "scripts/deployment",
    "logs/2024",
    "logs/2025",
    ".github/workflows",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 3. Distractor files ─────────────────────────────────────────────────────
distractor_files = {
    "src/api/handlers/chat.py": '''"""Chat API handler - routes requests to AI models."""
import os

MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-5")  # EXPENSIVE - should be haiku
MAX_TOKENS = 8192

def handle_chat(prompt: str) -> str:
    """Process chat request."""
    # TODO: Add token counting
    return f"Response to: {prompt[:50]}"
''',
    "src/api/middleware/rate_limiter.py": '''"""Rate limiting middleware."""
REQUESTS_PER_MINUTE = 60
BURST_LIMIT = 100

class RateLimiter:
    def __init__(self):
        self.counts = {}
    
    def check(self, user_id: str) -> bool:
        return True  # TODO: implement
''',
    "src/core/models/billing.py": '''"""Billing model - tracks API usage costs."""
# Current monthly spend tracker
MONTHLY_BUDGET_USD = 1500.00  # Way too high!
DAILY_SPEND_USD = 52.43       # Yesterday's bill
ALERT_THRESHOLD = 0.8

class BillingTracker:
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
''',
    "src/core/utils/token_counter.py": '''"""Utility for counting tokens."""
def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4

def estimate_cost(tokens: int, model: str = "sonnet") -> float:
    """Estimate cost in USD."""
    rates = {
        "sonnet": 0.003,
        "opus": 0.015,
        "haiku": 0.00025
    }
    return tokens * rates.get(model, 0.003) / 1000
''',
    "src/services/billing/invoice.py": '''"""Invoice generation service."""
from datetime import datetime

class Invoice:
    def __init__(self, period: str, amount: float):
        self.period = period
        self.amount = amount
        self.generated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            "period": self.period,
            "amount": self.amount,
            "currency": "USD"
        }
''',
    "src/services/analytics/usage.py": '''"""Usage analytics service."""
# This month's AI API usage
USAGE_STATS = {
    "total_requests": 48291,
    "total_tokens_input": 12847293,
    "total_tokens_output": 3928471,
    "model_breakdown": {
        "claude-sonnet-4-5": 0.89,   # 89% of calls use expensive model!
        "claude-haiku-4-5": 0.08,
        "claude-opus-4-5": 0.03
    },
    "estimated_monthly_cost": 1487.23
}
''',
    "config/environments/production.env": '''# Production environment config
AI_MODEL=claude-sonnet-4-5
AI_HEARTBEAT_INTERVAL=30
AI_HEARTBEAT_PROVIDER=anthropic
MAX_CONTEXT_TOKENS=50000
CACHE_ENABLED=false
MONTHLY_BUDGET_ALERT=1500
DEBUG=false
''',
    "config/environments/staging.env": '''# Staging environment config
AI_MODEL=claude-sonnet-4-5
AI_HEARTBEAT_INTERVAL=60
AI_HEARTBEAT_PROVIDER=anthropic
MAX_CONTEXT_TOKENS=50000
CACHE_ENABLED=false
MONTHLY_BUDGET_ALERT=500
DEBUG=true
''',
    "tests/unit/test_billing.py": '''"""Unit tests for billing module."""
import pytest

def test_monthly_budget_tracking():
    """Test that monthly budget is correctly tracked."""
    # TODO: This test is failing because costs are too high
    expected_monthly = 50.00  # target after optimization
    actual_monthly = 1487.23  # current spend
    assert actual_monthly <= expected_monthly, f"Over budget: ${actual_monthly}"
''',
    "tests/integration/test_ai_routing.py": '''"""Integration tests for AI model routing."""
def test_simple_queries_use_haiku():
    """Simple queries should use Haiku, not Sonnet."""
    # This test will pass once token-optimizer is applied
    pass

def test_heartbeat_uses_local_provider():
    """Heartbeat should use local Ollama, not paid API."""
    # This test will pass once heartbeat is reconfigured
    pass
''',
    "docs/architecture/ai_cost_analysis.md": '''# AI Cost Analysis - Q4 2024

## Current Monthly Spend: $1,487.23

### Problem Areas
1. **Model Selection**: 89% of requests use Sonnet unnecessarily
2. **Heartbeat**: 8,640 heartbeat calls/month to Anthropic API ($0.17/day)
3. **Context Size**: Loading full 50KB context for every session
4. **No Caching**: Identical prompts re-processed every time

### Target: $50/month
- Route simple queries to Haiku (saves ~92%)
- Use local Ollama for heartbeats (saves 100%)
- Enable prompt caching (saves ~90% on repeated prompts)
''',
    "scripts/deployment/deploy.sh": '''#!/bin/bash
# Deployment script
set -e

echo "Deploying to production..."
# TODO: Add AI cost optimization before deploying
# The team needs to run the token optimizer first!

docker-compose up -d
echo "Deploy complete"
''',
    ".github/workflows/ci.yml": '''name: CI Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ -v
      # TODO: Add --no-color flag for token optimizer in CI
''',
    "logs/2025/cost_spike.log": '''2025-01-15 09:23:14 WARN  Daily AI cost: $52.43 (budget: $5.00)
2025-01-15 09:23:14 ERROR Budget exceeded by 948%
2025-01-15 09:23:15 INFO  Model: claude-sonnet-4-5 (should use haiku for this query)
2025-01-15 09:23:16 INFO  Context size: 51243 tokens (could be 8192)
2025-01-15 09:23:17 WARN  Heartbeat provider: anthropic (costly)
2025-01-15 14:45:22 ERROR Monthly projection: $1,487.23 (target: $50.00)
''',
    "requirements.txt": '''anthropic>=0.25.0
click>=8.0.0
requests>=2.31.0
python-dotenv>=1.0.0
rich>=13.0.0
colorama>=0.4.6
''',
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── 4. Create a MESSY, INCORRECT existing ~/.openclaw/openclaw.json ─────────
# This simulates the "before" state - expensive defaults
openclaw_dir = Path.home() / ".openclaw"
openclaw_dir.mkdir(parents=True, exist_ok=True)
(openclaw_dir / "backups").mkdir(parents=True, exist_ok=True)
(openclaw_dir / "workspace").mkdir(parents=True, exist_ok=True)
(openclaw_dir / "prompts").mkdir(parents=True, exist_ok=True)

bad_config = {
    "agents": {
        "defaults": {
            "model": {
                "primary": "anthropic/claude-sonnet-4-5"  # expensive!
            },
            "cache": {
                "enabled": False,   # no caching
                "ttl": "0m"
            }
        }
    },
    "heartbeat": {
        "provider": "anthropic",       # paying for heartbeats
        "model": "anthropic/claude-haiku-4-5",
        "interval": 30
    },
    "budgets": {
        "daily": 100.00,     # no real limit
        "monthly": 5000.00   # no real limit
    },
    "_comment": "Default config - NOT optimized. Costs ~$1500/month."
}

with open(openclaw_dir / "openclaw.json", "w") as f:
    json.dump(bad_config, f, indent=2)

print(f"[+] Created messy config at {openclaw_dir / 'openclaw.json'}")

# ── 5. Write a fake stale stats file to simulate prior usage ────────────────
stats = {
    "last_run": None,
    "optimizations_applied": 0,
    "estimated_savings_monthly": 0.0,
    "config_version": "unoptimized"
}
with open(openclaw_dir / "token-optimizer-stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print(f"[+] Created stats file at {openclaw_dir / 'token-optimizer-stats.json'}")

# ── 6. Print a summary ──────────────────────────────────────────────────────
print("\n[*] Workspace structure:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"    {p.relative_to(WORKSPACE)}")
print(f"\n[*] ~/.openclaw/ contents:")
for p in sorted(openclaw_dir.rglob("*")):
    print(f"    {p}")
print("\n[+] gen_inputs_script complete.")