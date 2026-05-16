#!/usr/bin/env bash
set -e

# Install the mock aoi-squad CLI

cat > /usr/local/bin/aoi-squad << 'AOISQUAD_EOF'
#!/usr/bin/env python3
"""
Mock implementation of aoi-squad CLI for sandbox evaluation.
Implements the exact schema described in SKILL.md.
S-DNA: AOI-2026-0215-SDNA-SQUAD01
"""
import sys
import json
import argparse
import os
import pathlib
import datetime

SQUAD_NAMES_PATH = pathlib.Path.home() / ".openclaw" / "aoi" / "squad_names.json"

PRESETS = ["planner-builder-reviewer", "researcher-writer-editor", "builder-security-operator"]

DEFAULT_NAMES = {
    "planner-builder-reviewer": {
        "planner": "Cipher Aldren",
        "builder": "Forge Marek",
        "reviewer": "Prism Vael"
    },
    "researcher-writer-editor": {
        "researcher": "Nexus Oran",
        "writer": "Lumen Saya",
        "editor": "Slate Duvon"
    },
    "builder-security-operator": {
        "builder": "Forge Marek",
        "security": "Bastion Kira",
        "operator": "Relay Stenn"
    }
}

def load_names():
    if SQUAD_NAMES_PATH.exists():
        with open(SQUAD_NAMES_PATH) as f:
            return json.load(f)
    return {p: dict(DEFAULT_NAMES[p]) for p in PRESETS}

def save_names(data):
    SQUAD_NAMES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SQUAD_NAMES_PATH, "w") as f:
        json.dump(data, f, indent=2)

def cmd_preset_list():
    for p in PRESETS:
        print(p)

def cmd_team_show(preset):
    if preset not in PRESETS:
        print(f"Error: unknown preset '{preset}'", file=sys.stderr)
        sys.exit(1)
    names = load_names()
    team = names.get(preset, DEFAULT_NAMES[preset])
    print(json.dumps(team, indent=2))

def cmd_team_rename(preset, role, name):
    if preset not in PRESETS:
        print(f"Error: unknown preset '{preset}'", file=sys.stderr)
        sys.exit(1)
    names = load_names()
    if preset not in names:
        names[preset] = dict(DEFAULT_NAMES[preset])
    if role not in names[preset]:
        print(f"Error: unknown role '{role}' in preset '{preset}'", file=sys.stderr)
        sys.exit(1)
    names[preset][role] = name
    save_names(names)
    print(f"Renamed '{role}' in '{preset}' to '{name}'")

def cmd_run(preset, task):
    if preset not in PRESETS:
        print(f"Error: unknown preset '{preset}'", file=sys.stderr)
        sys.exit(1)
    names = load_names()
    team = names.get(preset, DEFAULT_NAMES[preset])
    report = {
        "schema_version": "1.0",
        "sdna": "AOI-2026-0215-SDNA-SQUAD01",
        "preset": preset,
        "task": task,
        "team": team,
        "status": "completed",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    print(json.dumps(report, indent=2))

def main():
    if len(sys.argv) < 2:
        print("Usage: aoi-squad <command> [options]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "preset" and len(sys.argv) >= 3 and sys.argv[2] == "list":
        cmd_preset_list()

    elif command == "team" and len(sys.argv) >= 3:
        subcmd = sys.argv[2]
        parser = argparse.ArgumentParser()
        parser.add_argument("--preset", required=True)
        if subcmd == "show":
            args = parser.parse_args(sys.argv[3:])
            cmd_team_show(args.preset)
        elif subcmd == "rename":
            parser.add_argument("--role", required=True)
            parser.add_argument("--name", required=True)
            args = parser.parse_args(sys.argv[3:])
            cmd_team_rename(args.preset, args.role, args.name)
        else:
            print(f"Unknown team subcommand: {subcmd}", file=sys.stderr)
            sys.exit(1)

    elif command == "run":
        parser = argparse.ArgumentParser()
        parser.add_argument("--preset", required=True)
        parser.add_argument("--task", required=True)
        args = parser.parse_args(sys.argv[2:])
        cmd_run(args.preset, args.task)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
AOISQUAD_EOF

chmod +x /usr/local/bin/aoi-squad

# Reset squad_names.json to defaults so the CLI manages it correctly
python3 - << 'PYEOF'
import json, pathlib

PRESETS = ["planner-builder-reviewer", "researcher-writer-editor", "builder-security-operator"]
DEFAULT_NAMES = {
    "planner-builder-reviewer": {
        "planner": "Cipher Aldren",
        "builder": "Forge Marek",
        "reviewer": "Prism Vael"
    },
    "researcher-writer-editor": {
        "researcher": "Nexus Oran",
        "writer": "Lumen Saya",
        "editor": "Slate Duvon"
    },
    "builder-security-operator": {
        "builder": "Forge Marek",
        "security": "Bastion Kira",
        "operator": "Relay Stenn"
    }
}

p = pathlib.Path.home() / ".openclaw" / "aoi" / "squad_names.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(DEFAULT_NAMES, indent=2))
print("squad_names.json reset to defaults.")
PYEOF

echo "aoi-squad CLI installed and configured."