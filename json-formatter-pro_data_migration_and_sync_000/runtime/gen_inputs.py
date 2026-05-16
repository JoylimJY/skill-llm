#!/usr/bin/env python3
"""
Generate a realistic financial trading-system config workspace.
Deterministic: fixed seeds throughout.
"""
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "legacy_exports/trading/configs",
    "legacy_exports/trading/snapshots",
    "legacy_exports/risk/configs",
    "legacy_exports/risk/snapshots",
    "legacy_exports/archive",
    "pipeline/staging",
    "pipeline/normalized",      # Agent should write formatted output HERE (or elsewhere - eval uses rglob)
    "pipeline/logs",
    "reports/daily",
    "reports/monthly",
    "scripts",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Helper to write raw text (possibly invalid JSON) ---
def write_raw(path, content):
    with open(path, "w") as f:
        f.write(content)

def write_json(path, data, indent=None):
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
        f.write("\n")

# ---------------------------------------------------------------
# DISTRACTOR FILES (not the target inputs)
# ---------------------------------------------------------------

# 1. A perfectly valid but unrelated system log in JSON
write_json(os.path.join(workspace, "pipeline/logs/pipeline_run_20240101.json"), {
    "run_id": "pr-001",
    "status": "completed",
    "duration_ms": 4523,
    "records_processed": 10000
}, indent=2)

# 2. A CSV distractor
write_raw(os.path.join(workspace, "reports/daily/positions_2024-01-15.csv"),
    "ticker,quantity,price\nAAPL,100,182.50\nGOOGL,50,141.20\n")

# 3. A shell script distractor
write_raw(os.path.join(workspace, "scripts/run_pipeline.sh"),
    "#!/bin/bash\necho 'Running pipeline...'\n")

# 4. A plain-text doc
write_raw(os.path.join(workspace, "docs/README.txt"),
    "This folder contains legacy exports from the Alpha trading system.\n")

# 5. A deeply nested valid JSON (distractor - already "normalized")
write_json(os.path.join(workspace, "reports/monthly/summary_jan2024.json"), {
    "month": "2024-01",
    "total_trades": 58291,
    "pnl": {"realized": 120500.50, "unrealized": -3200.10},
    "top_instruments": ["ES", "NQ", "CL"]
}, indent=2)

# 6. Archive distractor
write_raw(os.path.join(workspace, "legacy_exports/archive/old_schema_v1.txt"),
    "Schema version 1.0 - deprecated\n")

# 7. A minified but VALID JSON distractor
write_raw(os.path.join(workspace, "legacy_exports/trading/snapshots/snap_20231201.json"),
    '{"snapshot_id":"s-001","timestamp":"2023-12-01T09:00:00Z","values":[1,2,3]}')

# 8. Another distractor JSON with indent=2 (not sorted)
write_json(os.path.join(workspace, "legacy_exports/risk/snapshots/risk_snap_20240110.json"), {
    "zebra_metric": 9.9,
    "alpha_metric": 1.1,
    "model_version": "2.3.1"
}, indent=2)

# 9. Empty-ish distractor
write_raw(os.path.join(workspace, "pipeline/staging/.gitkeep"), "")

# 10. A Python script distractor
write_raw(os.path.join(workspace, "scripts/validate_schema.py"),
    "# Schema validator stub\nimport json\n\ndef validate(data):\n    pass\n")

# ---------------------------------------------------------------
# THE ACTUAL TARGET INPUT FILES (messy, from legacy system)
# These are in legacy_exports/trading/configs and legacy_exports/risk/configs
# ---------------------------------------------------------------

# --- VALID configs (should be formatted with 4-space indent + sort-keys) ---

# trading_config_A.json — valid, but minified and keys NOT sorted
write_raw(
    os.path.join(workspace, "legacy_exports/trading/configs/trading_config_A.json"),
    '{"zebra_threshold":0.05,"asset_class":"equity","max_position":5000,"broker_id":"BRK-42","currency":"USD","risk_limit":10000,"enabled":true}'
)

# trading_config_B.json — valid, ugly indentation (3 spaces, no sort)
write_raw(
    os.path.join(workspace, "legacy_exports/trading/configs/trading_config_B.json"),
    '{\n   "venue": "NYSE",\n   "order_type": "LIMIT",\n   "timeout_ms": 3000,\n   "retry_count": 3,\n   "session_id": "SES-99"\n}\n'
)

# risk_config_A.json — valid, nested, keys not sorted
write_raw(
    os.path.join(workspace, "legacy_exports/risk/configs/risk_config_A.json"),
    json.dumps({
        "model_name": "VaR-95",
        "window_days": 252,
        "confidence": 0.95,
        "parameters": {
            "volatility_floor": 0.01,
            "correlation_cap": 0.99,
            "decay_factor": 0.94
        },
        "enabled": True
    })  # minified, no indent
)

# --- INVALID configs (broken JSON — should be reported as invalid) ---

# trading_config_BAD1.json — trailing comma (invalid JSON)
write_raw(
    os.path.join(workspace, "legacy_exports/trading/configs/trading_config_BAD1.json"),
    '{\n  "instrument": "AAPL",\n  "quantity": 100,\n  "price": 182.50,\n}'
)

# risk_config_BAD1.json — unclosed bracket
write_raw(
    os.path.join(workspace, "legacy_exports/risk/configs/risk_config_BAD1.json"),
    '{\n  "alert_threshold": 0.02,\n  "notification_targets": ["email", "slack"\n}'
)

# risk_config_BAD2.json — completely malformed
write_raw(
    os.path.join(workspace, "legacy_exports/risk/configs/risk_config_BAD2.json"),
    'NOT JSON AT ALL {{{ broken ;;; data'
)

print("Workspace generated successfully.")
print("Target config files:")
print("  VALID:   legacy_exports/trading/configs/trading_config_A.json")
print("  VALID:   legacy_exports/trading/configs/trading_config_B.json")
print("  VALID:   legacy_exports/risk/configs/risk_config_A.json")
print("  INVALID: legacy_exports/trading/configs/trading_config_BAD1.json")
print("  INVALID: legacy_exports/risk/configs/risk_config_BAD1.json")
print("  INVALID: legacy_exports/risk/configs/risk_config_BAD2.json")