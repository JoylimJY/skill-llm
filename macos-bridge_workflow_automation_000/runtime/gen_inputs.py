#!/usr/bin/env python3
"""
Generate the sandbox workspace for the macos-bridge evaluation task.
"""
import json
import os
import random
import stat

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "home/node/.openclaw/bin",
    "home/node/.openclaw/logs",
    "home/node/.openclaw/cache",
    "home/node/.openclaw/plugins/alpha",
    "home/node/.openclaw/plugins/beta",
    "scripts",
    "references",
    "etc/openclaw",
    "var/openclaw/runs",
    "var/openclaw/state",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "home/node/.openclaw/logs/install-2024-01-10.log": (
        "[INFO] previous run completed\n[WARN] imsg wrapper stale\n"
    ),
    "home/node/.openclaw/cache/tool-hashes.json": json.dumps(
        {"imsg": "abc123", "remindctl": "def456"}, indent=2
    ),
    "home/node/.openclaw/plugins/alpha/plugin.json": json.dumps(
        {"name": "alpha", "version": "0.1.0", "enabled": True}, indent=2
    ),
    "home/node/.openclaw/plugins/beta/plugin.json": json.dumps(
        {"name": "beta", "version": "0.2.1", "enabled": False}, indent=2
    ),
    "etc/openclaw/defaults.conf": (
        "log_level=info\nmax_retries=3\ntimeout=30\n"
    ),
    "var/openclaw/runs/run-001.json": json.dumps(
        {"run_id": "001", "status": "ok", "ts": "2024-01-10T08:00:00Z"}, indent=2
    ),
    "var/openclaw/state/daemon.pid": "12345\n",
    "tmp/scratch/old-install-attempt.sh": (
        "#!/bin/bash\n# orphaned install attempt – ignore\necho noop\n"
    ),
    "home/node/.openclaw/plugins/alpha/hooks.sh": (
        "#!/bin/bash\n# plugin alpha hook\n"
    ),
    "home/node/.openclaw/logs/verify-2024-01-09.log": (
        "[INFO] verify pass\n[INFO] 3 wrappers found\n"
    ),
}
for rel, content in distractors.items():
    path = os.path.join(WORKSPACE, rel)
    with open(path, "w") as f:
        f.write(content)

# ── openclaw.json (the key config the agent must read) ────────────────────────
# Channels: imsg=enabled, remindctl=enabled, memo=DISABLED, things=DISABLED,
#            peekaboo=enabled.
# remoteHost is set for imsg and remindctl (same host), peekaboo has a different
# host so there is NOT a single unique remoteHost → --default-host is needed.
openclaw_config = {
    "version": "0.6.2",
    "gateway": {
        "id": "lx-gateway-01",
        "bin": "/home/node/.openclaw/bin"
    },
    "channels": {
        "imsg": {
            "enabled": True,
            "remoteHost": "alice@192.168.1.50",
            "description": "iMessage bridge"
        },
        "remindctl": {
            "enabled": True,
            "remoteHost": "alice@192.168.1.50",
            "description": "Reminders bridge"
        },
        "memo": {
            "enabled": False,
            "remoteHost": "alice@192.168.1.50",
            "description": "Notes/memo bridge – disabled"
        },
        "things": {
            "enabled": False,
            "description": "Things3 bridge – disabled, no remoteHost"
        },
        "peekaboo": {
            "enabled": True,
            "remoteHost": "bob@192.168.1.75",
            "description": "Peekaboo camera bridge"
        }
    },
    "wol": {
        "mac-node.local": "AA:BB:CC:DD:EE:FF"
    }
}

config_path = os.path.join(WORKSPACE, "home/node/.openclaw/openclaw.json")
with open(config_path, "w") as f:
    json.dump(openclaw_config, f, indent=2)

# ── references/skill-readiness.md (distractor reference file) ────────────────
skill_readiness = """\
# Skill Readiness Rules

A wrapper-backed skill is publishable when:
1. All enabled channel wrappers exist in the target bin directory.
2. Each wrapper is executable and contains a valid SSH invocation.
3. The verify script exits 0 when run with --openclaw-config.

Do not publish a skill if disabled channels have wrappers installed.
Disabled channels must remain absent from the bin directory.
"""
with open(os.path.join(WORKSPACE, "references/skill-readiness.md"), "w") as f:
    f.write(skill_readiness)

# ── mock scripts (bodies written here; setup_script will chmod them) ──────────

# ---------- render-tool-map.sh ----------
render_tool_map = r"""#!/bin/bash
# mock: render-tool-map.sh  <openclaw-config>
set -euo pipefail
CONFIG="${1:-}"
if [[ -z "$CONFIG" ]]; then
  echo "Usage: render-tool-map.sh <openclaw-config>" >&2
  exit 1
fi
if [[ ! -f "$CONFIG" ]]; then
  echo "Config not found: $CONFIG" >&2
  exit 1
fi

# Print auto-discovered enabled tools from config
echo "=== Auto-discovered enabled macOS-backed channels ==="
python3 - "$CONFIG" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1]))
channels = cfg.get("channels", {})
SUPPORTED = {"imsg","remindctl","memo","things","peekaboo"}
for tool, info in channels.items():
    if tool in SUPPORTED and info.get("enabled", False):
        host = info.get("remoteHost","<unknown>")
        print(f"  {tool:12s} => {host}")
PYEOF

echo ""
echo "=== WoL map ==="
python3 - "$CONFIG" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1]))
for node, mac in cfg.get("wol",{}).items():
    print(f"  {node} => {mac}")
PYEOF
# Record that render was called, for eval
echo "render-tool-map CALLED CONFIG=$CONFIG" >> /tmp/macos-bridge-audit.log
"""

# ---------- install-macos-pack.sh ----------
install_macos_pack = r"""#!/bin/bash
# mock: install-macos-pack.sh
set -euo pipefail

TARGET_DIR=""
OPENCLAW_CONFIG=""
DEFAULT_HOST=""
WAKE_MAP=""
WAKE_WAIT=""
WAKE_RETRIES=""
TOOL_OVERRIDE=""
MAP_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir)       TARGET_DIR="$2";       shift 2 ;;
    --openclaw-config)  OPENCLAW_CONFIG="$2";  shift 2 ;;
    --default-host)     DEFAULT_HOST="$2";     shift 2 ;;
    --wake-map)         WAKE_MAP="$2";         shift 2 ;;
    --wake-wait)        WAKE_WAIT="$2";        shift 2 ;;
    --wake-retries)     WAKE_RETRIES="$2";     shift 2 ;;
    --tool)             TOOL_OVERRIDE="$2";    shift 2 ;;
    --map)              MAP_OVERRIDE="$2";     shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$TARGET_DIR" ]]; then echo "--target-dir required" >&2; exit 1; fi
if [[ -z "$OPENCLAW_CONFIG" ]]; then echo "--openclaw-config required" >&2; exit 1; fi
if [[ -z "$DEFAULT_HOST" ]]; then echo "--default-host required" >&2; exit 1; fi

# Reject --tool or --map when config is provided (auto-discovery mode)
if [[ -n "$TOOL_OVERRIDE" ]] && [[ -f "$OPENCLAW_CONFIG" ]]; then
  echo "ERROR: --tool must not be used when --openclaw-config is present (auto-discovery)" >&2
  exit 2
fi
if [[ -n "$MAP_OVERRIDE" ]] && [[ -f "$OPENCLAW_CONFIG" ]]; then
  echo "ERROR: --map must not be used when --openclaw-config is present (auto-discovery)" >&2
  exit 2
fi

mkdir -p "$TARGET_DIR"

# Determine enabled tools from config
ENABLED_TOOLS=$(python3 - "$OPENCLAW_CONFIG" <<'PYEOF'
import json, sys
SUPPORTED = {"imsg","remindctl","memo","things","peekaboo"}
cfg = json.load(open(sys.argv[1]))
for tool, info in cfg.get("channels",{}).items():
    if tool in SUPPORTED and info.get("enabled", False):
        print(tool)
PYEOF
)

# Install a wrapper for each enabled tool
for TOOL in $ENABLED_TOOLS; do
  # Resolve host: config remoteHost > default-host
  HOST=$(python3 - "$OPENCLAW_CONFIG" "$TOOL" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1]))
tool = sys.argv[2]
info = cfg.get("channels",{}).get(tool,{})
rh = info.get("remoteHost","")
print(rh if rh else "")
PYEOF
)
  if [[ -z "$HOST" ]]; then
    HOST="$DEFAULT_HOST"
  fi

  WRAPPER="$TARGET_DIR/$TOOL"
  cat > "$WRAPPER" <<EOF
#!/bin/bash
# SSH wrapper for $TOOL → $HOST
exec ssh "$HOST" "$TOOL" "\$@"
EOF
  chmod +x "$WRAPPER"
  echo "[install-macos-pack] installed $TOOL → $HOST"
done

# Log invocation details for eval
{
  echo "install-macos-pack CALLED"
  echo "  TARGET_DIR=$TARGET_DIR"
  echo "  OPENCLAW_CONFIG=$OPENCLAW_CONFIG"
  echo "  DEFAULT_HOST=$DEFAULT_HOST"
  echo "  WAKE_MAP=$WAKE_MAP"
  echo "  WAKE_WAIT=$WAKE_WAIT"
  echo "  WAKE_RETRIES=$WAKE_RETRIES"
  echo "  TOOL_OVERRIDE=$TOOL_OVERRIDE"
  echo "  MAP_OVERRIDE=$MAP_OVERRIDE"
} >> /tmp/macos-bridge-audit.log

echo "[install-macos-pack] done"
"""

# ---------- verify-macos-pack.sh ----------
verify_macos_pack = r"""#!/bin/bash
# mock: verify-macos-pack.sh
set -euo pipefail

TARGET_DIR=""
OPENCLAW_CONFIG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir)      TARGET_DIR="$2";      shift 2 ;;
    --openclaw-config) OPENCLAW_CONFIG="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$TARGET_DIR" ]]; then echo "--target-dir required" >&2; exit 1; fi

PASS=1

if [[ -n "$OPENCLAW_CONFIG" && -f "$OPENCLAW_CONFIG" ]]; then
  # Only check enabled macOS-backed tools
  TOOLS_TO_CHECK=$(python3 - "$OPENCLAW_CONFIG" <<'PYEOF'
import json, sys
SUPPORTED = {"imsg","remindctl","memo","things","peekaboo"}
cfg = json.load(open(sys.argv[1]))
for tool, info in cfg.get("channels",{}).items():
    if tool in SUPPORTED and info.get("enabled", False):
        print(tool)
PYEOF
)
else
  # Without config: check ALL supported tools (strict mode)
  TOOLS_TO_CHECK="imsg remindctl memo things peekaboo"
fi

echo "=== Verifying macOS bridge pack ==="
for TOOL in $TOOLS_TO_CHECK; do
  WRAPPER="$TARGET_DIR/$TOOL"
  if [[ -x "$WRAPPER" ]]; then
    echo "  [OK]   $TOOL"
  else
    echo "  [FAIL] $TOOL – wrapper missing or not executable"
    PASS=0
  fi
done

# Also check that disabled tools do NOT have wrappers
if [[ -n "$OPENCLAW_CONFIG" && -f "$OPENCLAW_CONFIG" ]]; then
  DISABLED_TOOLS=$(python3 - "$OPENCLAW_CONFIG" <<'PYEOF'
import json, sys
SUPPORTED = {"imsg","remindctl","memo","things","peekaboo"}
cfg = json.load(open(sys.argv[1]))
for tool, info in cfg.get("channels",{}).items():
    if tool in SUPPORTED and not info.get("enabled", False):
        print(tool)
PYEOF
)
  for TOOL in $DISABLED_TOOLS; do
    WRAPPER="$TARGET_DIR/$TOOL"
    if [[ -e "$WRAPPER" ]]; then
      echo "  [FAIL] $TOOL – disabled but wrapper exists"
      PASS=0
    else
      echo "  [OK]   $TOOL (disabled, correctly absent)"
    fi
  done
fi

{
  echo "verify-macos-pack CALLED"
  echo "  TARGET_DIR=$TARGET_DIR"
  echo "  OPENCLAW_CONFIG=$OPENCLAW_CONFIG"
} >> /tmp/macos-bridge-audit.log

if [[ "$PASS" -eq 1 ]]; then
  echo "=== VERIFICATION PASSED ==="
  exit 0
else
  echo "=== VERIFICATION FAILED ==="
  exit 1
fi
"""

# ---------- install-wrapper.sh ----------
install_wrapper = r"""#!/bin/bash
# mock: install-wrapper.sh  (single wrapper helper)
set -euo pipefail
echo "[install-wrapper] $@"
"""

scripts = {
    "scripts/render-tool-map.sh": render_tool_map,
    "scripts/install-macos-pack.sh": install_macos_pack,
    "scripts/verify-macos-pack.sh": verify_macos_pack,
    "scripts/install-wrapper.sh": install_wrapper,
}
for rel, body in scripts.items():
    path = os.path.join(WORKSPACE, rel)
    with open(path, "w") as f:
        f.write(body)

print("Workspace generated successfully.")