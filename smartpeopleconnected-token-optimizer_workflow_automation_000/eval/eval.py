#!/usr/bin/env python3
"""
Evaluation script for the token-optimizer task.
Checks that the agent:
1. Applied all cost optimizations (model routing to haiku, cache enabled, budget limits)
2. Configured heartbeat to use Ollama (local provider)
3. Created at least one timestamped backup in ~/.openclaw/backups/
"""

import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    openclaw_config_path = Path.home() / ".openclaw" / "openclaw.json"
    backups_dir = Path.home() / ".openclaw" / "backups"

    # ── Check 1: openclaw.json exists ──────────────────────────────────────
    config_exists = openclaw_config_path.exists()
    checks.append({
        "name": "openclaw.json exists",
        "passed": config_exists,
        "detail": str(openclaw_config_path) + (" found" if config_exists else " NOT FOUND")
    })

    config = {}
    if config_exists:
        try:
            with open(openclaw_config_path) as f:
                config = json.load(f)
        except Exception as e:
            checks.append({
                "name": "openclaw.json is valid JSON",
                "passed": False,
                "detail": f"Failed to parse: {e}"
            })
            config = {}
    
    # ── Check 2: Model routed to Haiku (not Sonnet/Opus) ──────────────────
    try:
        primary_model = config["agents"]["defaults"]["model"]["primary"]
        is_haiku = "haiku" in primary_model.lower()
        checks.append({
            "name": "Model routing: primary model is Haiku",
            "passed": is_haiku,
            "detail": f"agents.defaults.model.primary = '{primary_model}' (expected something containing 'haiku')"
        })
    except (KeyError, TypeError) as e:
        checks.append({
            "name": "Model routing: primary model is Haiku",
            "passed": False,
            "detail": f"Key missing in config: {e}. Config keys: {list(config.keys())}"
        })

    # ── Check 3: Caching enabled ───────────────────────────────────────────
    try:
        cache_enabled = config["agents"]["defaults"]["cache"]["enabled"]
        checks.append({
            "name": "Caching enabled",
            "passed": cache_enabled is True,
            "detail": f"agents.defaults.cache.enabled = {cache_enabled} (expected true)"
        })
    except (KeyError, TypeError) as e:
        checks.append({
            "name": "Caching enabled",
            "passed": False,
            "detail": f"Key missing in config: {e}"
        })

    # ── Check 4: Heartbeat provider is Ollama (not Anthropic) ─────────────
    try:
        heartbeat_provider = config["heartbeat"]["provider"]
        is_ollama = heartbeat_provider.lower() == "ollama"
        checks.append({
            "name": "Heartbeat provider set to Ollama",
            "passed": is_ollama,
            "detail": f"heartbeat.provider = '{heartbeat_provider}' (expected 'ollama')"
        })
    except (KeyError, TypeError) as e:
        checks.append({
            "name": "Heartbeat provider set to Ollama",
            "passed": False,
            "detail": f"Key missing in config: {e}"
        })

    # ── Check 5: Heartbeat model is the Ollama model ──────────────────────
    try:
        heartbeat_model = config["heartbeat"]["model"]
        is_ollama_model = "ollama" in heartbeat_model.lower()
        checks.append({
            "name": "Heartbeat model uses Ollama provider prefix",
            "passed": is_ollama_model,
            "detail": f"heartbeat.model = '{heartbeat_model}' (expected an ollama/ model)"
        })
    except (KeyError, TypeError) as e:
        checks.append({
            "name": "Heartbeat model uses Ollama provider prefix",
            "passed": False,
            "detail": f"Key missing in config: {e}"
        })

    # ── Check 6: Daily budget is a sensible low value (≤ 10 USD) ──────────
    try:
        daily_budget = float(config["budgets"]["daily"])
        # Original was $100/day, optimized should be $5/day per docs
        is_low_budget = daily_budget <= 10.0
        checks.append({
            "name": "Daily budget is set to a cost-limiting value (≤ $10)",
            "passed": is_low_budget,
            "detail": f"budgets.daily = {daily_budget} (expected ≤ 10.0, original was 100.0)"
        })
    except (KeyError, TypeError, ValueError) as e:
        checks.append({
            "name": "Daily budget is set to a cost-limiting value (≤ $10)",
            "passed": False,
            "detail": f"Key missing or invalid in config: {e}"
        })

    # ── Check 7: Monthly budget is a sensible low value (≤ 500 USD) ───────
    try:
        monthly_budget = float(config["budgets"]["monthly"])
        # Original was $5000/month, optimized should be $200/month per docs
        is_low_monthly = monthly_budget <= 500.0
        checks.append({
            "name": "Monthly budget is set to a cost-limiting value (≤ $500)",
            "passed": is_low_monthly,
            "detail": f"budgets.monthly = {monthly_budget} (expected ≤ 500.0, original was 5000.0)"
        })
    except (KeyError, TypeError, ValueError) as e:
        checks.append({
            "name": "Monthly budget is set to a cost-limiting value (≤ $500)",
            "passed": False,
            "detail": f"Key missing or invalid in config: {e}"
        })

    # ── Check 8: A backup was created in ~/.openclaw/backups/ ─────────────
    try:
        if backups_dir.exists():
            backup_files = list(backups_dir.glob("*"))
            # Filter to only files (not dirs)
            backup_files = [f for f in backup_files if f.is_file()]
            has_backup = len(backup_files) > 0
            checks.append({
                "name": "Backup created in ~/.openclaw/backups/",
                "passed": has_backup,
                "detail": f"Found {len(backup_files)} backup file(s): {[f.name for f in backup_files[:3]]}"
            })
        else:
            checks.append({
                "name": "Backup created in ~/.openclaw/backups/",
                "passed": False,
                "detail": "Backups directory does not exist"
            })
    except Exception as e:
        checks.append({
            "name": "Backup created in ~/.openclaw/backups/",
            "passed": False,
            "detail": f"Error checking backups: {e}"
        })

    # ── Check 9: The config is NOT the original bad config ─────────────────
    # The original had model = "anthropic/claude-sonnet-4-5"
    try:
        primary_model = config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "")
        was_not_modified = "sonnet" in primary_model.lower()
        checks.append({
            "name": "Config was actually modified from original (not dry-run only)",
            "passed": not was_not_modified,
            "detail": f"primary model is '{primary_model}' (if still 'sonnet', --apply was never used)"
        })
    except Exception as e:
        checks.append({
            "name": "Config was actually modified from original (not dry-run only)",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Scoring ────────────────────────────────────────────────────────────
    critical_checks = [
        "Model routing: primary model is Haiku",
        "Heartbeat provider set to Ollama",
        "Caching enabled",
        "Backup created in ~/.openclaw/backups/",
        "Config was actually modified from original (not dry-run only)",
    ]
    
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    
    # Critical checks must ALL pass for overall pass
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    score = passed_count / total_count if total_count > 0 else 0.0
    overall_passed = critical_passed and (passed_count >= 7)

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)