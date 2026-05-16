#!/bin/bash
set -e

# Create a mock auto-responder CLI that validates and tests the config
cat > /usr/local/bin/auto-responder << 'MOCK_CLI'
#!/usr/bin/env python3
"""Mock auto-responder CLI for OpenClaw"""
import sys
import json
import os
import argparse
import pathlib

def find_agent_config():
    """Try to determine which agent's config to use"""
    workspace_base = pathlib.Path.home() / ".openclaw"
    configs = list(workspace_base.glob("workspace-*/auto-responder.json"))
    return configs

def validate_config(config_path):
    """Validate an auto-responder config file"""
    with open(config_path) as f:
        cfg = json.load(f)
    errors = []
    
    if "enabled" not in cfg:
        errors.append("Missing 'enabled' field")
    if not isinstance(cfg.get("enabled"), bool):
        errors.append("'enabled' must be boolean")
    if "globalCooldownMinutes" not in cfg:
        errors.append("Missing 'globalCooldownMinutes'")
    if not isinstance(cfg.get("globalCooldownMinutes"), (int, float)):
        errors.append("'globalCooldownMinutes' must be a number")
    if "topics" not in cfg or not isinstance(cfg.get("topics"), dict):
        errors.append("'topics' must be a dict")
    else:
        for tname, t in cfg["topics"].items():
            if "thread_ids" not in t:
                errors.append(f"Topic '{tname}' missing 'thread_ids'")
            elif not isinstance(t["thread_ids"], list):
                errors.append(f"Topic '{tname}' thread_ids must be a list")
            else:
                for tid in t["thread_ids"]:
                    if not isinstance(tid, int):
                        errors.append(f"Topic '{tname}' thread_ids must contain integers, got {type(tid).__name__}")
            if "keywords" not in t or not isinstance(t.get("keywords"), list):
                errors.append(f"Topic '{tname}' keywords must be a list")
            if "responseTemplate" not in t:
                errors.append(f"Topic '{tname}' missing 'responseTemplate'")
    
    return errors

parser = argparse.ArgumentParser(description="auto-responder CLI")
parser.add_argument("--once", action="store_true")
parser.add_argument("--hook", action="store_true")
parser.add_argument("--validate", type=str, help="Validate a config file")
parser.add_argument("--agent", type=str, help="Agent name")
args = parser.parse_args()

if args.validate:
    errors = validate_config(args.validate)
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Config valid.")
        sys.exit(0)

if args.once or args.hook:
    if args.agent:
        cfg_path = pathlib.Path.home() / ".openclaw" / f"workspace-{args.agent}" / "auto-responder.json"
        if cfg_path.exists():
            errors = validate_config(cfg_path)
            if errors:
                print(f"[auto-responder] Config errors for {args.agent}:", file=sys.stderr)
                for e in errors:
                    print(f"  {e}", file=sys.stderr)
                sys.exit(1)
            print(f"[auto-responder] Running for agent: {args.agent}")
        else:
            print(f"[auto-responder] No config found for agent {args.agent}", file=sys.stderr)
            sys.exit(1)
    else:
        configs = find_agent_config()
        print(f"[auto-responder] Found {len(configs)} agent config(s)")
    sys.exit(0)

print("auto-responder: use --once, --hook, or --validate")
MOCK_CLI

chmod +x /usr/local/bin/auto-responder

# Ensure cache directory exists
mkdir -p /root/.cache

echo "Setup complete. auto-responder CLI available."
auto-responder --help 2>/dev/null || true