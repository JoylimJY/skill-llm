import os
import json
import stat
import textwrap
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    ".openclaw-tmp",
    "logs/build",
    "logs/ci",
    "config/network",
    "config/hosts",
    "assets/icons",
    "assets/docs",
    "projects/alpha",
    "projects/beta",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# also make the openclaw home dir (but NOT the bin subdir – agent must rely on scripts)
os.makedirs("/home/node/.openclaw", exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "logs/build/build-2024-01-15.log": "BUILD OK\nbrew install success\ngh release ok\n",
    "logs/ci/pipeline.log": "Pipeline started\nStep 1: checkout\nStep 2: compile\nStep 3: test\n",
    "config/network/vlans.conf": "[vlan10]\nsubnet=192.168.10.0/24\ngateway=192.168.10.1\n",
    "config/hosts/known_hosts": "mac-workstation.local ecdsa-sha2-nistp256 AAAA...\n",
    "config/hosts/ssh_config_template": "Host mac-*\n  User node\n  IdentityFile ~/.ssh/id_rsa\n",
    "assets/docs/onboarding.md": "# Onboarding\nPlease ask IT for SSH keys.\n",
    "assets/icons/placeholder.txt": "icon data placeholder\n",
    "projects/alpha/README.txt": "Alpha project - cross-platform build\nRequires brew and gh\n",
    "projects/beta/Makefile": "all:\n\t@echo 'build beta'\n",
    ".openclaw-tmp/stale-config.json": json.dumps({"version": "0.4.0", "remoteHost": "old@stale.local"}),
    "references/old-wrapper-notes.txt": "Old approach: manually copy binaries. Deprecated.\n",
    "config/network/firewall-rules.txt": "ALLOW 192.168.1.0/24 -> 192.168.1.50 port 22\nDENY ALL\n",
}
for relpath, content in distractors.items():
    full = os.path.join(WORKSPACE, relpath)
    with open(full, "w") as f:
        f.write(content)

# ── OpenClaw config (the real one the agent must discover) ────────────────────
# Exactly ONE remoteHost entry so host auto-discovery should work
openclaw_cfg = {
    "version": "0.6.1",
    "gateway": "linux-ci-node",
    "owners": [
        {
            "id": "mac-ops",
            "remoteHost": "mac-ops@mac-node.local",
            "platform": "darwin",
            "wolMac": "AA:BB:CC:DD:EE:FF",
            "tools": ["brew", "gh", "jq"]
        }
    ]
}
with open("/home/node/.openclaw/openclaw.json", "w") as f:
    json.dump(openclaw_cfg, f, indent=2)

# ── scripts/render-tool-map.sh ────────────────────────────────────────────────
# Reads openclaw.json, prints tool→host map, also extracts the single remoteHost
render_tool_map = r"""#!/usr/bin/env bash
# render-tool-map.sh  <path-to-openclaw.json>
set -euo pipefail

CONFIG="${1:-}"
if [[ -z "$CONFIG" || ! -f "$CONFIG" ]]; then
  echo "ERROR: openclaw config not found: $CONFIG" >&2
  exit 1
fi

echo "=== Tool Ownership Map ==="
# Parse with python3 (jq may not be available everywhere)
python3 - "$CONFIG" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1]))
owners = cfg.get("owners", [])
if len(owners) == 1:
    owner = owners[0]
    host = owner.get("remoteHost", "UNKNOWN")
    tools = owner.get("tools", [])
    print(f"Discovered single Mac owner: {host}")
    for t in tools:
        print(f"  {t} -> {host}")
else:
    for owner in owners:
        host = owner.get("remoteHost", "UNKNOWN")
        for t in owner.get("tools", []):
            print(f"  {t} -> {host}")
PYEOF
"""

# ── scripts/install-wrapper.sh ────────────────────────────────────────────────
install_wrapper = r"""#!/usr/bin/env bash
# install-wrapper.sh  --target-dir DIR --tool TOOL --host user@host [--wake-host host --wake-mac MAC --wake-wait N --wake-retries N]
set -euo pipefail

TARGET_DIR=""
TOOL=""
HOST=""
WAKE_HOST=""
WAKE_MAC=""
WAKE_WAIT=15
WAKE_RETRIES=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir) TARGET_DIR="$2"; shift 2 ;;
    --tool)       TOOL="$2";       shift 2 ;;
    --host)       HOST="$2";       shift 2 ;;
    --wake-host)  WAKE_HOST="$2";  shift 2 ;;
    --wake-mac)   WAKE_MAC="$2";   shift 2 ;;
    --wake-wait)  WAKE_WAIT="$2";  shift 2 ;;
    --wake-retries) WAKE_RETRIES="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$TARGET_DIR" ]] && { echo "Missing --target-dir" >&2; exit 1; }
[[ -z "$TOOL" ]]       && { echo "Missing --tool" >&2; exit 1; }
[[ -z "$HOST" ]]       && { echo "Missing --host" >&2; exit 1; }

mkdir -p "$TARGET_DIR"
WRAPPER="$TARGET_DIR/$TOOL"

cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
# homebrew-bridge wrapper: $TOOL -> $HOST:/opt/homebrew/bin/$TOOL
# wake-host: ${WAKE_HOST:-none}  wake-mac: ${WAKE_MAC:-none}  wake-wait: ${WAKE_WAIT}  wake-retries: ${WAKE_RETRIES}
set -euo pipefail
exec ssh -o StrictHostKeyChecking=no "$HOST" "/opt/homebrew/bin/$TOOL" "\$@"
EOF

chmod +x "$WRAPPER"
echo "Installed wrapper: $WRAPPER -> $HOST:/opt/homebrew/bin/$TOOL"
"""

# ── scripts/install-homebrew-pack.sh ─────────────────────────────────────────
install_homebrew_pack = r"""#!/usr/bin/env bash
# install-homebrew-pack.sh  --target-dir DIR --tool T [--tool T2 ...] 
#   [--map tool=user@host] [--default-host user@host]
#   [--wake-map host=MAC] [--wake-wait N] [--wake-retries N]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_DIR=""
TOOLS=()
TOOL_MAP=()     # "tool=user@host"
DEFAULT_HOST=""
WAKE_MAP=()     # "host=MAC"
WAKE_WAIT=15
WAKE_RETRIES=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir)    TARGET_DIR="$2";       shift 2 ;;
    --tool)          TOOLS+=("$2");         shift 2 ;;
    --map)           TOOL_MAP+=("$2");      shift 2 ;;
    --default-host)  DEFAULT_HOST="$2";    shift 2 ;;
    --wake-map)      WAKE_MAP+=("$2");      shift 2 ;;
    --wake-wait)     WAKE_WAIT="$2";        shift 2 ;;
    --wake-retries)  WAKE_RETRIES="$2";    shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$TARGET_DIR" ]] && { echo "Missing --target-dir" >&2; exit 1; }
[[ ${#TOOLS[@]} -eq 0 ]] && { echo "No --tool specified" >&2; exit 1; }

mkdir -p "$TARGET_DIR"

# Build wake lookup: host -> MAC
declare -A WAKE_LOOKUP
for entry in "${WAKE_MAP[@]}"; do
  whost="${entry%%=*}"
  wmac="${entry#*=}"
  WAKE_LOOKUP["$whost"]="$wmac"
done

# Build tool->host lookup from --map
declare -A EXPLICIT_MAP
for entry in "${TOOL_MAP[@]}"; do
  t="${entry%%=*}"
  h="${entry#*=}"
  EXPLICIT_MAP["$t"]="$h"
done

for TOOL in "${TOOLS[@]}"; do
  # Resolve host
  HOST=""
  if [[ -n "${EXPLICIT_MAP[$TOOL]+_}" ]]; then
    HOST="${EXPLICIT_MAP[$TOOL]}"
  elif [[ -n "$DEFAULT_HOST" ]]; then
    HOST="$DEFAULT_HOST"
  else
    echo "ERROR: cannot resolve host for tool $TOOL" >&2
    exit 1
  fi

  # Extract hostname part for wake lookup
  HOSTNAME_PART="${HOST#*@}"

  WAKE_HOST_ARG=""
  WAKE_MAC_ARG=""
  if [[ -n "${WAKE_LOOKUP[$HOSTNAME_PART]+_}" ]]; then
    WAKE_HOST_ARG="$HOSTNAME_PART"
    WAKE_MAC_ARG="${WAKE_LOOKUP[$HOSTNAME_PART]}"
  fi

  ARGS=(--target-dir "$TARGET_DIR" --tool "$TOOL" --host "$HOST"
        --wake-wait "$WAKE_WAIT" --wake-retries "$WAKE_RETRIES")
  [[ -n "$WAKE_HOST_ARG" ]] && ARGS+=(--wake-host "$WAKE_HOST_ARG" --wake-mac "$WAKE_MAC_ARG")

  "$SCRIPT_DIR/install-wrapper.sh" "${ARGS[@]}"
done

echo "Pack installed: ${TOOLS[*]} -> $TARGET_DIR"
# Write manifest
python3 - "$TARGET_DIR" "${TOOLS[@]}" "$DEFAULT_HOST" "${WAKE_MAP[@]}" <<'PYEOF'
import json, sys, os
target = sys.argv[1]
tools  = []
i = 2
while i < len(sys.argv) and not sys.argv[i].startswith("mac-"):
    tools.append(sys.argv[i]); i += 1
default_host = sys.argv[i] if i < len(sys.argv) else ""
wake_maps = sys.argv[i+1:]
manifest = {
    "target_dir": target,
    "tools": tools,
    "default_host": default_host,
    "wake_maps": wake_maps,
}
with open(os.path.join(target, ".manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
PYEOF
"""

# The manifest writing logic above is fragile for edge cases; let's replace with a cleaner version
install_homebrew_pack = r"""#!/usr/bin/env bash
# install-homebrew-pack.sh  --target-dir DIR --tool T [--tool T2 ...] 
#   [--map tool=user@host] [--default-host user@host]
#   [--wake-map host=MAC] [--wake-wait N] [--wake-retries N]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_DIR=""
TOOLS=()
TOOL_MAP=()
DEFAULT_HOST=""
WAKE_MAP_ENTRIES=()
WAKE_WAIT=15
WAKE_RETRIES=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir)    TARGET_DIR="$2";            shift 2 ;;
    --tool)          TOOLS+=("$2");              shift 2 ;;
    --map)           TOOL_MAP+=("$2");           shift 2 ;;
    --default-host)  DEFAULT_HOST="$2";          shift 2 ;;
    --wake-map)      WAKE_MAP_ENTRIES+=("$2");   shift 2 ;;
    --wake-wait)     WAKE_WAIT="$2";             shift 2 ;;
    --wake-retries)  WAKE_RETRIES="$2";          shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$TARGET_DIR" ]] && { echo "Missing --target-dir" >&2; exit 1; }
[[ ${#TOOLS[@]} -eq 0 ]] && { echo "No --tool specified" >&2; exit 1; }

mkdir -p "$TARGET_DIR"

# Build associative arrays
declare -A WAKE_LOOKUP
for entry in "${WAKE_MAP_ENTRIES[@]}"; do
  whost="${entry%%=*}"
  wmac="${entry#*=}"
  WAKE_LOOKUP["$whost"]="$wmac"
done

declare -A EXPLICIT_MAP
for entry in "${TOOL_MAP[@]}"; do
  t="${entry%%=*}"
  h="${entry#*=}"
  EXPLICIT_MAP["$t"]="$h"
done

INSTALLED=()
for TOOL in "${TOOLS[@]}"; do
  HOST=""
  if [[ -n "${EXPLICIT_MAP[$TOOL]+_}" ]]; then
    HOST="${EXPLICIT_MAP[$TOOL]}"
  elif [[ -n "$DEFAULT_HOST" ]]; then
    HOST="$DEFAULT_HOST"
  else
    echo "ERROR: cannot resolve host for tool=$TOOL" >&2
    exit 1
  fi

  HOSTNAME_PART="${HOST#*@}"
  ARGS=(--target-dir "$TARGET_DIR" --tool "$TOOL" --host "$HOST"
        --wake-wait "$WAKE_WAIT" --wake-retries "$WAKE_RETRIES")
  if [[ -n "${WAKE_LOOKUP[$HOSTNAME_PART]+_}" ]]; then
    ARGS+=(--wake-host "$HOSTNAME_PART" --wake-mac "${WAKE_LOOKUP[$HOSTNAME_PART]}")
  fi

  "$SCRIPT_DIR/install-wrapper.sh" "${ARGS[@]}"
  INSTALLED+=("$TOOL")
done

# Write manifest JSON
MANIFEST_FILE="$TARGET_DIR/.manifest.json"
{
  echo "{"
  echo "  \"target_dir\": \"$TARGET_DIR\","
  echo "  \"default_host\": \"$DEFAULT_HOST\","
  echo "  \"wake_wait\": $WAKE_WAIT,"
  echo "  \"wake_retries\": $WAKE_RETRIES,"
  # tools array
  printf '  "tools": ['
  first=1
  for t in "${INSTALLED[@]}"; do
    [[ $first -eq 0 ]] && printf ','
    printf '"%s"' "$t"
    first=0
  done
  echo '],'
  # wake_maps array
  printf '  "wake_maps": ['
  first=1
  for e in "${WAKE_MAP_ENTRIES[@]}"; do
    [[ $first -eq 0 ]] && printf ','
    printf '"%s"' "$e"
    first=0
  done
  echo ']'
  echo "}"
} > "$MANIFEST_FILE"

echo "Pack installed. Manifest: $MANIFEST_FILE"
"""

# ── scripts/verify-homebrew-pack.sh ──────────────────────────────────────────
verify_homebrew_pack = r"""#!/usr/bin/env bash
# verify-homebrew-pack.sh  --target-dir DIR
set -euo pipefail

TARGET_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir) TARGET_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done
[[ -z "$TARGET_DIR" ]] && { echo "Missing --target-dir" >&2; exit 1; }

MANIFEST="$TARGET_DIR/.manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
  echo "FAIL: manifest not found at $MANIFEST" >&2
  exit 1
fi

echo "=== Verify Homebrew Pack: $TARGET_DIR ==="

TOOLS=$(python3 -c "import json,sys; d=json.load(open('$MANIFEST')); print(' '.join(d['tools']))")
ALL_OK=1
for TOOL in $TOOLS; do
  WRAPPER="$TARGET_DIR/$TOOL"
  if [[ -f "$WRAPPER" && -x "$WRAPPER" ]]; then
    # Check it references /opt/homebrew/bin
    if grep -q "/opt/homebrew/bin/$TOOL" "$WRAPPER"; then
      echo "  OK  $TOOL"
    else
      echo "  FAIL  $TOOL  (missing /opt/homebrew/bin reference)"
      ALL_OK=0
    fi
  else
    echo "  FAIL  $TOOL  (wrapper missing or not executable)"
    ALL_OK=0
  fi
done

REPORT_FILE="$TARGET_DIR/.verify-report.json"
python3 - "$TARGET_DIR" "$MANIFEST" "$ALL_OK" <<'PYEOF'
import json, sys, os, stat
target = sys.argv[1]
manifest_path = sys.argv[2]
all_ok = sys.argv[3] == "1"
manifest = json.load(open(manifest_path))
tools = manifest.get("tools", [])
results = []
for t in tools:
    wp = os.path.join(target, t)
    exists = os.path.isfile(wp)
    executable = exists and bool(os.stat(wp).st_mode & stat.S_IXUSR)
    has_ref = False
    if exists:
        content = open(wp).read()
        has_ref = f"/opt/homebrew/bin/{t}" in content
    results.append({"tool": t, "wrapper_exists": exists, "executable": executable, "homebrew_ref": has_ref})

report = {
    "target_dir": target,
    "all_ok": all_ok and all(r["wrapper_exists"] and r["executable"] and r["homebrew_ref"] for r in results),
    "tools": results,
    "wake_wait": manifest.get("wake_wait"),
    "wake_retries": manifest.get("wake_retries"),
    "wake_maps": manifest.get("wake_maps", []),
    "default_host": manifest.get("default_host", ""),
}
with open(os.path.join(target, ".verify-report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
PYEOF

if [[ $ALL_OK -eq 1 ]]; then
  echo "Pack verification: PASSED"
else
  echo "Pack verification: FAILED" >&2
  exit 1
fi
"""

# Write the scripts
scripts = {
    "scripts/render-tool-map.sh": render_tool_map,
    "scripts/install-wrapper.sh": install_wrapper,
    "scripts/install-homebrew-pack.sh": install_homebrew_pack,
    "scripts/verify-homebrew-pack.sh": verify_homebrew_pack,
}
for relpath, content in scripts.items():
    full = os.path.join(WORKSPACE, relpath)
    with open(full, "w") as f:
        f.write(content)
    os.chmod(full, 0o755)

# ── references/skill-readiness.md ────────────────────────────────────────────
skill_readiness = """# Skill Readiness Rules for Homebrew-Backed Wrappers

A Homebrew-backed wrapper is publishable when:
1. The wrapper file exists at the declared target-dir path.
2. The wrapper is executable.
3. The wrapper invokes `/opt/homebrew/bin/<tool>` over SSH on the remote Mac.
4. Wake-on-LAN metadata is embedded if a WoL MAC address is declared.
5. The verify script passes without errors.
"""
with open(os.path.join(WORKSPACE, "references/skill-readiness.md"), "w") as f:
    f.write(skill_readiness)

print("Workspace generated successfully.")
print("OpenClaw config written to /home/node/.openclaw/openclaw.json")
print("Scripts written to /workspace/scripts/")