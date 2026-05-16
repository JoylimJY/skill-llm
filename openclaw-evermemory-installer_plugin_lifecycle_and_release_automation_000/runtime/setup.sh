#!/usr/bin/env bash
set -e

WORKSPACE=/workspace

# ── Audit log: every script call is appended here ──────────────────────────
AUDIT_LOG="$WORKSPACE/logs/audit_calls.log"
mkdir -p "$WORKSPACE/logs"
> "$AUDIT_LOG"

# ── gate-check.js: passes for both dev and release ─────────────────────────
cat > "$WORKSPACE/bin/gate-check.js" << 'GATECHECK'
const mode = process.argv[process.argv.indexOf('--mode') + 1];
if (!mode) { console.error('--mode required'); process.exit(1); }
console.log(`[teams:${mode}] All checks passed. recall=0.97 threshold=0.90 OK`);
process.exit(0);
GATECHECK

# ── Mock: openclaw CLI ──────────────────────────────────────────────────────
cat > /usr/local/bin/openclaw << 'OPENCLAW'
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "$(date -Iseconds) OPENCLAW $*" >> "$AUDIT_LOG"

SUBCOMMAND="$1"
shift

case "$SUBCOMMAND" in
  gateway)
    ACTION="$1"; shift
    if [ "$ACTION" = "status" ]; then
      echo "openclaw gateway: RUNNING | plugins_loaded=1 | slot_memory=evermemory"
    elif [ "$ACTION" = "restart" ]; then
      echo "openclaw gateway: restart triggered, applying bindings..."
      echo "openclaw gateway: RUNNING | slot_memory=evermemory BOUND"
    fi
    ;;
  plugins)
    ACTION="$1"; shift
    if [ "$ACTION" = "install" ]; then
      echo "openclaw plugins install: processing args: $*"
      # record flags
      LINK=false; BIND=false; RESTART=false; SOURCE=""; VALUE=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --link) LINK=true ;;
          --bind-slot) BIND=true ;;
          --restart-gateway) RESTART=true ;;
          --source) SOURCE="$2"; shift ;;
          --value) VALUE="$2"; shift ;;
        esac
        shift
      done
      echo "SOURCE=$SOURCE LINK=$LINK BIND=$BIND RESTART=$RESTART VALUE=$VALUE" >> "$AUDIT_LOG"
      echo "openclaw plugins install: evermemory installed OK (source=$SOURCE link=$LINK bind=$BIND restart=$RESTART)"
      if $BIND; then
        echo "plugins.slots.memory=evermemory → BOUND"
      fi
      if $RESTART; then
        echo "Gateway restarted with new bindings."
      fi
    elif [ "$ACTION" = "list" ]; then
      echo "evermemory@0.3.1 [active]"
    fi
    ;;
  *)
    echo "openclaw: unknown subcommand $SUBCOMMAND"
    exit 1
    ;;
esac
OPENCLAW
chmod +x /usr/local/bin/openclaw

# ── Mock: clawhub CLI ───────────────────────────────────────────────────────
cat > /usr/local/bin/clawhub << 'CLAWHUB'
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "$(date -Iseconds) CLAWHUB $*" >> "$AUDIT_LOG"

SUBCOMMAND="$1"
shift

case "$SUBCOMMAND" in
  whoami)
    echo "evermemory-bot (authenticated)"
    ;;
  login)
    echo "clawhub: logged in as evermemory-bot"
    ;;
  publish)
    VERSION=""; CHANGELOG=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --version) VERSION="$2"; shift ;;
        --changelog) CHANGELOG="$2"; shift ;;
      esac
      shift
    done
    if [ -z "$VERSION" ]; then
      echo "clawhub publish: ERROR --version is required" >&2; exit 1
    fi
    if [ -z "$CHANGELOG" ]; then
      echo "clawhub publish: ERROR --changelog is required" >&2; exit 1
    fi
    echo "clawhub publish: Uploading skill package v${VERSION}..."
    echo "clawhub publish: changelog: ${CHANGELOG}"
    echo "clawhub publish: SUCCESS artifact=evermemory-skill-${VERSION}.tar.gz uploaded to ClawHub"
    echo "CLAWHUB_PUBLISH version=$VERSION changelog=$CHANGELOG" >> "$AUDIT_LOG"
    ;;
  install)
    echo "clawhub install: installed skill OK"
    ;;
  *)
    echo "clawhub: unknown subcommand $SUBCOMMAND"
    exit 1
    ;;
esac
CLAWHUB
chmod +x /usr/local/bin/clawhub

# ── Wrap npm to also log and handle whoami + publish ───────────────────────
REAL_NPM=$(which npm)
cat > /usr/local/bin/npm << NPMWRAP
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "\$(date -Iseconds) NPM \$*" >> "\$AUDIT_LOG"

if [ "\$1" = "whoami" ]; then
  echo "evermemory-publisher"
  exit 0
fi

if [ "\$1" = "login" ]; then
  echo "Logged in as evermemory-publisher"
  exit 0
fi

# delegate everything else to real npm
exec $REAL_NPM "\$@"
NPMWRAP
chmod +x /usr/local/bin/npm

# ── scripts/install_plugin.sh ───────────────────────────────────────────────
mkdir -p "$WORKSPACE/scripts"
cat > "$WORKSPACE/scripts/install_plugin.sh" << 'INSTALL_SH'
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "$(date -Iseconds) install_plugin.sh $*" >> "$AUDIT_LOG"

SOURCE=""; VALUE=""; LINK=false; BIND_SLOT=false; RESTART_GATEWAY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)    SOURCE="$2"; shift ;;
    --value)     VALUE="$2"; shift ;;
    --link)      LINK=true ;;
    --bind-slot) BIND_SLOT=true ;;
    --restart-gateway) RESTART_GATEWAY=true ;;
    *) echo "install_plugin.sh: unknown arg $1" ;;
  esac
  shift
done

echo "install_plugin.sh: source=$SOURCE link=$LINK bind_slot=$BIND_SLOT restart_gateway=$RESTART_GATEWAY value=$VALUE"

if [ -z "$SOURCE" ]; then
  echo "ERROR: --source required" >&2; exit 1
fi

case "$SOURCE" in
  local)
    openclaw plugins install --source local $( $LINK && echo '--link' ) $( $BIND_SLOT && echo '--bind-slot' ) $( $RESTART_GATEWAY && echo '--restart-gateway' )
    ;;
  archive)
    openclaw plugins install --source archive --value "$VALUE" $( $BIND_SLOT && echo '--bind-slot' ) $( $RESTART_GATEWAY && echo '--restart-gateway' )
    ;;
  spec)
    openclaw plugins install --source spec --value "$VALUE" $( $BIND_SLOT && echo '--bind-slot' ) $( $RESTART_GATEWAY && echo '--restart-gateway' )
    ;;
esac

# Record install flags to state file
mkdir -p /workspace/logs
cat > /workspace/logs/last_install.json << INSTALLJSON
{
  "source": "$SOURCE",
  "link": $LINK,
  "bind_slot": $BIND_SLOT,
  "restart_gateway": $RESTART_GATEWAY,
  "value": "$VALUE"
}
INSTALLJSON

echo "install_plugin.sh: done"
INSTALL_SH
chmod +x "$WORKSPACE/scripts/install_plugin.sh"

# ── scripts/verify_install.sh ───────────────────────────────────────────────
cat > "$WORKSPACE/scripts/verify_install.sh" << 'VERIFY_SH'
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "$(date -Iseconds) verify_install.sh $*" >> "$AUDIT_LOG"

echo "verify_install.sh: checking openclaw gateway status..."
GW=$(openclaw gateway status)
echo "$GW"

if echo "$GW" | grep -q "slot_memory=evermemory"; then
  echo "verify_install.sh: [OK] slot binding confirmed: plugins.slots.memory=evermemory"
  SLOT_OK=true
else
  echo "verify_install.sh: [FAIL] slot binding not found"
  SLOT_OK=false
fi

echo "verify_install.sh: checking recall benchmark..."
RECALL=0.97
echo "verify_install.sh: recall=$RECALL (threshold=0.90) [OK]"

cat > /workspace/logs/verify_result.json << VERIFYJSON
{
  "gateway_running": true,
  "slot_memory_bound": $SLOT_OK,
  "recall": $RECALL,
  "recall_ok": true
}
VERIFYJSON

echo "verify_install.sh: verification complete"
VERIFY_SH
chmod +x "$WORKSPACE/scripts/verify_install.sh"

# ── scripts/publish_skill.sh ────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/publish_skill.sh" << 'PUBSKILL_SH'
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "$(date -Iseconds) publish_skill.sh $*" >> "$AUDIT_LOG"

VERSION=""; CHANGELOG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)   VERSION="$2"; shift ;;
    --changelog) CHANGELOG="$2"; shift ;;
    *) echo "publish_skill.sh: unknown arg $1" ;;
  esac
  shift
done

if [ -z "$VERSION" ]; then
  echo "ERROR: --version required" >&2; exit 1
fi
if [ -z "$CHANGELOG" ]; then
  echo "ERROR: --changelog required" >&2; exit 1
fi

echo "publish_skill.sh: checking clawhub auth..."
clawhub whoami
echo "publish_skill.sh: publishing skill v$VERSION to ClawHub..."
clawhub publish --version "$VERSION" --changelog "$CHANGELOG"

cat > /workspace/logs/skill_publish_result.json << SKILLPUBJSON
{
  "version": "$VERSION",
  "changelog": "$CHANGELOG",
  "artifact": "evermemory-skill-${VERSION}.tar.gz",
  "status": "published"
}
SKILLPUBJSON

echo "publish_skill.sh: skill published successfully"
PUBSKILL_SH
chmod +x "$WORKSPACE/scripts/publish_skill.sh"

# ── scripts/publish_plugin.sh ───────────────────────────────────────────────
cat > "$WORKSPACE/scripts/publish_plugin.sh" << 'PUBPLUGIN_SH'
#!/usr/bin/env bash
AUDIT_LOG="/workspace/logs/audit_calls.log"
echo "$(date -Iseconds) publish_plugin.sh $*" >> "$AUDIT_LOG"

DRY_RUN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    *) echo "publish_plugin.sh: unknown arg $1" ;;
  esac
  shift
done

echo "publish_plugin.sh: checking npm auth..."
npm whoami

if $DRY_RUN; then
  echo "publish_plugin.sh: [DRY-RUN] npm publish --dry-run"
  npm pack --dry-run 2>/dev/null || true
  echo "publish_plugin.sh: DRY-RUN complete. Would publish evermemory@0.3.1 to npm registry."
  ARTIFACT="evermemory-0.3.1-dry-run.tgz"
  STATUS="dry-run"
else
  echo "publish_plugin.sh: publishing to npm..."
  ARTIFACT="evermemory-0.3.1.tgz"
  STATUS="published"
fi

cat > /workspace/logs/plugin_publish_result.json << PLUGPUBJSON
{
  "dry_run": $DRY_RUN,
  "artifact": "$ARTIFACT",
  "status": "$STATUS"
}
PLUGPUBJSON

echo "publish_plugin.sh: done (dry_run=$DRY_RUN)"
PUBPLUGIN_SH
chmod +x "$WORKSPACE/scripts/publish_plugin.sh"

echo "Setup complete. Mock environment ready."