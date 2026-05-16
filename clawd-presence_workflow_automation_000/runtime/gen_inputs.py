import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Create the clawd-presence project structure ──────────────────────────────
dirs = [
    "scripts",
    "assets/monograms",
    "assets/themes",
    "config",
    "logs",
    "docs/internal",
    "docs/runbooks",
    "ops/monitoring",
    "ops/deployment",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Write the actual scripts (they must exist per SKILL.md) ──────────────────

# scripts/configure.py
configure_py = r'''#!/usr/bin/env python3
"""Configure clawd-presence agent identity and settings."""
import argparse
import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "presence.json"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Configure clawd-presence")
    parser.add_argument("--auto", action="store_true", help="Auto-detect from clawdbot")
    parser.add_argument("--letter", type=str, help="Monogram letter A-Z")
    parser.add_argument("--name", type=str, help="Agent display name")
    parser.add_argument("--timeout", type=int, help="Auto-idle timeout in seconds (0 to disable)")
    args = parser.parse_args()

    cfg = load_config()

    if args.auto:
        cfg["letter"] = "A"
        cfg["name"] = "AGENT"
        cfg["timeout"] = 300
        print("Auto-configured: letter=A, name=AGENT, timeout=300")
    else:
        if args.letter:
            letter = args.letter.upper()
            if len(letter) != 1 or not letter.isalpha():
                print("Error: --letter must be a single A-Z character")
                return 1
            cfg["letter"] = letter
        if args.name:
            cfg["name"] = args.name.upper()
        if args.timeout is not None:
            cfg["timeout"] = args.timeout

    save_config(cfg)
    print(f"Configuration saved: {cfg}")
    return 0

if __name__ == "__main__":
    exit(main())
'''

# scripts/status.py
status_py = r'''#!/usr/bin/env python3
"""Update clawd-presence agent status."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

STATE_PATH = Path(__file__).parent.parent / "config" / "state.json"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "presence.json"

VALID_STATES = {
    "idle":  {"color": "cyan",   "activity_optional": False},
    "work":  {"color": "green",  "activity_optional": False},
    "think": {"color": "yellow", "activity_optional": False},
    "alert": {"color": "red",    "activity_optional": False},
    "sleep": {"color": "blue",   "activity_optional": True},
}

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_state(state_data):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state_data, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: status.py <state> [activity]")
        print(f"Valid states: {', '.join(VALID_STATES.keys())}")
        return 1

    state = sys.argv[1].lower()
    if state not in VALID_STATES:
        print(f"Error: Invalid state '{state}'. Valid states: {', '.join(VALID_STATES.keys())}")
        return 1

    activity = sys.argv[2] if len(sys.argv) > 2 else None

    # sleep state takes no activity text
    if state == "sleep" and activity:
        print("Warning: 'sleep' state does not accept activity text. Ignoring.")
        activity = None

    cfg = load_config()
    state_data = {
        "state": state,
        "activity": activity,
        "color": VALID_STATES[state]["color"],
        "timestamp": datetime.utcnow().isoformat(),
        "agent_letter": cfg.get("letter", "?"),
        "agent_name": cfg.get("name", "UNKNOWN"),
    }

    save_state(state_data)
    act_str = f" - {activity}" if activity else ""
    print(f"[{state.upper()}]{act_str}")
    return 0

if __name__ == "__main__":
    exit(main())
'''

# scripts/display.py  (stub - would block, but agent doesn't need to run it)
display_py = r'''#!/usr/bin/env python3
"""Display clawd-presence on terminal. Run in dedicated terminal."""
import json
import time
from pathlib import Path

STATE_PATH = Path(__file__).parent.parent / "config" / "state.json"

def main():
    print("Clawd Presence Display - Press Ctrl+C to exit")
    try:
        while True:
            if STATE_PATH.exists():
                with open(STATE_PATH) as f:
                    s = json.load(f)
                print(f"\r[{s.get('agent_letter','?')}] {s.get('state','?').upper()} {s.get('activity') or ''}", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisplay stopped.")

if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "configure.py").write_text(configure_py)
(workspace / "scripts" / "status.py").write_text(status_py)
(workspace / "scripts" / "display.py").write_text(display_py)

# ── Create monogram letter files ─────────────────────────────────────────────
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    (workspace / "assets" / "monograms" / f"{ch}.txt").write_text(f"[{ch}]\n")

# ── Create a messy/outdated stale config that should be replaced ──────────────
stale_config = {
    "letter": "X",
    "name": "OLDBOT",
    "timeout": 999,
    "_stale": True,
    "_comment": "This config was auto-generated during initial boot and needs reconfiguration"
}
(workspace / "config" / "presence.json").write_text(json.dumps(stale_config, indent=2))

# Write a stale state too
stale_state = {
    "state": "idle",
    "activity": "stale state from previous session",
    "color": "cyan",
    "timestamp": "2024-01-01T00:00:00",
    "agent_letter": "X",
    "agent_name": "OLDBOT"
}
(workspace / "config" / "state.json").write_text(json.dumps(stale_state, indent=2))

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "docs/internal/architecture.md": "# Architecture\nThis system uses a state machine model...\n",
    "docs/internal/status_codes.md": "# Legacy Status Codes\nOLD codes: RUNNING=1, STOPPED=2, ERROR=3\n",
    "docs/runbooks/incident_response.md": "# Incident Response\nIf agent is unresponsive, check config/state.json\n",
    "ops/monitoring/alert_rules.yaml": "alerts:\n  - name: agent_stale\n    threshold: 600\n",
    "ops/deployment/deploy.sh": "#!/bin/bash\necho 'Deploying agent...'\n",
    "ops/deployment/agent_config_template.json": '{"letter": "PLACEHOLDER", "name": "PLACEHOLDER", "timeout": -1}\n',
    "tests/unit/test_configure.py": "# Unit tests - not for agent use\ndef test_placeholder(): pass\n",
    "tests/integration/test_status.py": "# Integration test stub\n# states = ['running', 'stopped', 'idle']\n",
    "logs/agent_2024_boot.log": "[2024-01-01 00:00:00] Agent boot sequence initiated\n[2024-01-01 00:00:01] Using letter=X, name=OLDBOT\n",
    "logs/agent_errors.log": "[2024-01-01 00:05:00] ERROR: state 'working' is not valid\n[2024-01-01 00:05:01] ERROR: state 'analyzing' is not valid\n",
    "assets/themes/dark.json": '{"background": "black", "foreground": "white"}\n',
    "assets/themes/light.json": '{"background": "white", "foreground": "black"}\n',
    "config/legacy_settings.ini": "[agent]\nletter=X\nname=OLDBOT\nmode=legacy\n",
}

for rel_path, content in distractors.items():
    full = workspace / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")