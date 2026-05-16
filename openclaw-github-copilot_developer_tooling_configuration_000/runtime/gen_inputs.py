import os
import stat
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor files (deeply nested, realistic dev-tooling project) ──────────
distractor_structure = {
    "src/core/engine.py": "# Core engine module\nclass Engine:\n    pass\n",
    "src/core/config.py": "# Configuration loader\nimport json\n\ndef load_config(path):\n    with open(path) as f:\n        return json.load(f)\n",
    "src/core/__init__.py": "",
    "src/plugins/linter.py": "# Linter plugin stub\nclass Linter:\n    def run(self, code): return []\n",
    "src/plugins/__init__.py": "",
    "src/utils/logger.py": "import logging\nlogger = logging.getLogger(__name__)\n",
    "src/utils/retry.py": "import time\ndef retry(fn, n=3):\n    for _ in range(n):\n        try: return fn()\n        except: time.sleep(1)\n",
    "src/utils/__init__.py": "",
    "tests/test_engine.py": "def test_placeholder(): assert True\n",
    "tests/test_config.py": "def test_config_load(): pass\n",
    "tests/conftest.py": "import pytest\n",
    "docs/architecture.md": "# Architecture\nThis document describes the system architecture.\n",
    "docs/api-reference.md": "# API Reference\nSee source code for details.\n",
    "infra/terraform/main.tf": "# Terraform placeholder\nresource \"null_resource\" \"placeholder\" {}\n",
    "infra/terraform/variables.tf": "variable \"region\" { default = \"us-east-1\" }\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "scripts/lint.sh": "#!/bin/bash\npython3 -m flake8 src/\n",
    "pyproject.toml": "[tool.poetry]\nname = \"ai-tooling\"\nversion = \"0.1.0\"\n",
    "Makefile": "test:\n\tpython3 -m pytest tests/\n\nlint:\n\tbash scripts/lint.sh\n",
}

for rel_path, content in distractor_structure.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ── mock openclaw binary state directory ─────────────────────────────────────
openclaw_state_dir = workspace / ".openclaw_state"
openclaw_state_dir.mkdir(exist_ok=True)

# Initial state: model exists, alias MISSING, no default set
initial_state = {
    "models": ["copilot-bridge/github-copilot", "local/ollama-llama3", "openai/gpt-4o"],
    "aliases": {},          # copilot-auto alias is MISSING — agent must create it
    "default_model": "",    # No default set — agent must activate copilot
    "auth": {
        "copilot-bridge/github-copilot": "valid"
    }
}
(openclaw_state_dir / "state.json").write_text(json.dumps(initial_state, indent=2))

# ── command audit log (agent's commands will be recorded by the mock) ─────────
(openclaw_state_dir / "command_log.jsonl").write_text("")

# ── skill scripts directory ───────────────────────────────────────────────────
# The SKILL.md says these scripts ALREADY EXIST in {baseDir}/scripts/
# We create them as mock implementations that interact with our state file

skills_scripts_dir = workspace / "skills" / "openclaw-github-copilot" / "scripts"
skills_scripts_dir.mkdir(parents=True, exist_ok=True)

# copilot-status.sh — diagnoses the current state
copilot_status_sh = r"""#!/bin/bash
# copilot-status.sh: Diagnose Copilot configuration state
STATE_FILE="/workspace/.openclaw_state/state.json"
LOG_FILE="/workspace/.openclaw_state/command_log.jsonl"
PROBE=false

for arg in "$@"; do
    case $arg in
        --probe) PROBE=true ;;
    esac
done

echo "{\"cmd\": \"copilot-status.sh\", \"args\": \"$*\", \"ts\": $(date +%s)}" >> "$LOG_FILE"

MODEL="copilot-bridge/github-copilot"
ALIAS="copilot-auto"

# Check if model is registered
MODELS=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print('\n'.join(s['models']))")
DEFAULT=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(s['default_model'])")
ALIASES_JSON=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(json.dumps(s['aliases']))")

MODEL_EXISTS=$(echo "$MODELS" | grep -c "^${MODEL}$" || true)
ALIAS_EXISTS=$(echo "$ALIASES_JSON" | python3 -c "import json,sys; a=json.load(sys.stdin); print('yes' if '$ALIAS' in a else 'no')")
IS_DEFAULT=$([ "$DEFAULT" = "$MODEL" ] && echo "yes" || echo "no")

echo "=== OpenClaw Copilot Status ==="
echo "Model registered : $([ $MODEL_EXISTS -gt 0 ] && echo 'YES' || echo 'NO') ($MODEL)"
echo "Alias configured : $ALIAS_EXISTS ($ALIAS)"
echo "Current default  : ${DEFAULT:-<none>}"
echo "Copilot is default: $IS_DEFAULT"

if [ "$PROBE" = "true" ]; then
    AUTH=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(s['auth'].get('copilot-bridge/github-copilot','missing'))")
    echo "Auth status      : $AUTH"
fi
"""

(skills_scripts_dir / "copilot-status.sh").write_text(copilot_status_sh)

# copilot-activate.sh — sets copilot as default model
copilot_activate_sh = r"""#!/bin/bash
# copilot-activate.sh: Activate copilot-bridge/github-copilot as the default model
STATE_FILE="/workspace/.openclaw_state/state.json"
LOG_FILE="/workspace/.openclaw_state/command_log.jsonl"

echo "{\"cmd\": \"copilot-activate.sh\", \"args\": \"$*\", \"ts\": $(date +%s)}" >> "$LOG_FILE"

MODEL="copilot-bridge/github-copilot"

MODELS=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print('\n'.join(s['models']))")
MODEL_EXISTS=$(echo "$MODELS" | grep -c "^${MODEL}$" || true)

if [ $MODEL_EXISTS -eq 0 ]; then
    echo "ERROR: Model $MODEL is not registered. Run copilot-quickstart.sh first."
    exit 1
fi

python3 - <<'PYEOF'
import json
path = "/workspace/.openclaw_state/state.json"
with open(path) as f:
    state = json.load(f)
state["default_model"] = "copilot-bridge/github-copilot"
with open(path, "w") as f:
    json.dump(state, f, indent=2)
print("Default model set to copilot-bridge/github-copilot")
PYEOF
"""

(skills_scripts_dir / "copilot-activate.sh").write_text(copilot_activate_sh)

# copilot-quickstart.sh — the all-in-one wrapper
copilot_quickstart_sh = r"""#!/bin/bash
# copilot-quickstart.sh: All-in-one Copilot setup wrapper
STATE_FILE="/workspace/.openclaw_state/state.json"
LOG_FILE="/workspace/.openclaw_state/command_log.jsonl"
SCRIPTS_DIR="$(dirname "$0")"

PROBE=false
ACTIVATE=false
LOGIN=false

for arg in "$@"; do
    case $arg in
        --probe)    PROBE=true ;;
        --activate) ACTIVATE=true ;;
        --login)    LOGIN=true ;;
    esac
done

echo "{\"cmd\": \"copilot-quickstart.sh\", \"args\": \"$*\", \"ts\": $(date +%s)}" >> "$LOG_FILE"

if [ "$PROBE" = "true" ]; then
    bash "$SCRIPTS_DIR/copilot-status.sh" --probe
fi

if [ "$LOGIN" = "true" ]; then
    echo "INFO: --login requires interactive TTY; skipping in non-interactive mode."
fi

if [ "$ACTIVATE" = "true" ]; then
    bash "$SCRIPTS_DIR/copilot-activate.sh"
fi
"""

(skills_scripts_dir / "copilot-quickstart.sh").write_text(copilot_quickstart_sh)

# ── mock openclaw binary ──────────────────────────────────────────────────────
# Placed in /usr/local/bin so it's on PATH
openclaw_bin = r"""#!/bin/bash
# Mock openclaw CLI — simulates the real openclaw binary behavior
STATE_FILE="/workspace/.openclaw_state/state.json"
LOG_FILE="/workspace/.openclaw_state/command_log.jsonl"

log_cmd() {
    echo "{\"cmd\": \"openclaw\", \"args\": \"$*\", \"ts\": $(date +%s)}" >> "$LOG_FILE"
}

log_cmd "$@"

if [ "$1" = "models" ]; then
    case "$2" in
        list)
            # openclaw models list --plain
            python3 -c "
import json
with open('$STATE_FILE') as f:
    s = json.load(f)
for m in s['models']:
    print(m)
"
            ;;
        aliases)
            if [ "$3" = "list" ]; then
                python3 -c "
import json
with open('$STATE_FILE') as f:
    s = json.load(f)
aliases = s.get('aliases', {})
if not aliases:
    print('(no aliases configured)')
else:
    for k, v in aliases.items():
        print(f'{k} -> {v}')
"
            fi
            ;;
        status)
            # openclaw models status --plain
            python3 -c "
import json
with open('$STATE_FILE') as f:
    s = json.load(f)
default = s.get('default_model', '')
if default:
    print(f'default_model: {default}')
else:
    print('default_model: <none>')
aliases = s.get('aliases', {})
for k, v in aliases.items():
    if v == default:
        print(f'resolved_via_alias: {k}')
"
            ;;
        set)
            # openclaw models set <model-or-alias>
            TARGET="$3"
            python3 - "$TARGET" <<'PYEOF'
import json, sys
target = sys.argv[1]
path = "/workspace/.openclaw_state/state.json"
with open(path) as f:
    state = json.load(f)

aliases = state.get("aliases", {})
models = state.get("models", [])

# Resolve alias -> model
if target in aliases:
    resolved = aliases[target]
elif target in models:
    resolved = target
else:
    print(f"ERROR: Unknown model or alias: {target}", file=sys.stderr)
    sys.exit(1)

state["default_model"] = resolved
with open(path, "w") as f:
    json.dump(state, f, indent=2)
print(f"Default model set to: {resolved}")
PYEOF
            ;;
        alias)
            # openclaw models alias create <alias> <model>
            if [ "$3" = "create" ]; then
                ALIAS_NAME="$4"
                MODEL_NAME="$5"
                python3 - "$ALIAS_NAME" "$MODEL_NAME" <<'PYEOF'
import json, sys
alias_name = sys.argv[1]
model_name = sys.argv[2]
path = "/workspace/.openclaw_state/state.json"
with open(path) as f:
    state = json.load(f)
if model_name not in state["models"]:
    print(f"ERROR: Model {model_name} not found", file=sys.stderr)
    sys.exit(1)
state.setdefault("aliases", {})[alias_name] = model_name
with open(path, "w") as f:
    json.dump(state, f, indent=2)
print(f"Alias '{alias_name}' -> '{model_name}' created")
PYEOF
            fi
            ;;
        auth)
            if [ "$3" = "login-github-copilot" ]; then
                echo "INFO: GitHub Copilot auth — device flow would start here (requires interactive TTY)."
                echo "INFO: Auth already valid in this environment; no action needed."
            fi
            ;;
        *)
            echo "Unknown subcommand: $2"
            exit 1
            ;;
    esac
else
    echo "Usage: openclaw models <list|aliases|status|set|alias|auth> [options]"
    exit 1
fi
"""

# Write the mock binary to workspace (will be installed in setup_script)
(workspace / ".openclaw_state" / "openclaw_bin.sh").write_text(openclaw_bin)

# ── task context file (gives agent the scenario without hints) ────────────────
task_context = {
    "team": "Platform Engineering",
    "issue": "AI coding assistant bridge is not configured as the team default",
    "skill_base_dir": str(workspace / "skills" / "openclaw-github-copilot"),
    "note": "The skill scripts are in the scripts/ subdirectory of the skill base dir"
}
(workspace / "task_context.json").write_text(json.dumps(task_context, indent=2))

print("Workspace generated successfully.")
print(f"State file: {openclaw_state_dir / 'state.json'}")
print(f"Scripts dir: {skills_scripts_dir}")