#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
SESSIONS_DIR="$WORKSPACE/.openclaw/agents/main/sessions"
SESSIONS_JSON="$WORKSPACE/.openclaw/agents/main/sessions.json"
SCAN_SCRIPT="$WORKSPACE/skills/session-cleanup/scripts/scan_sessions.sh"

# ── Create the real scan_sessions.sh script ──────────────────────────────────
cat > "$SCAN_SCRIPT" << 'SCAN_EOF'
#!/usr/bin/env bash
# scan_sessions.sh — OpenClaw session scanner
set -euo pipefail

SESSIONS_DIR="$HOME/.openclaw/agents/main/sessions"
SESSIONS_JSON="$HOME/.openclaw/agents/main/sessions.json"

# Allow override via env for testing
if [ -n "${OPENCLAW_SESSIONS_DIR:-}" ]; then
    SESSIONS_DIR="$OPENCLAW_SESSIONS_DIR"
fi
if [ -n "${OPENCLAW_SESSIONS_JSON:-}" ]; then
    SESSIONS_JSON="$OPENCLAW_SESSIONS_JSON"
fi

if [ "${1:-}" != "scan" ]; then
    echo "Usage: $0 scan" >&2
    exit 1
fi

NOW_EPOCH=$(date +%s)
STALE_THRESHOLD=$((72 * 3600))

# Read sessions.json
if [ ! -f "$SESSIONS_JSON" ]; then
    echo '{"error": "sessions.json not found"}' >&2
    exit 1
fi

# Use node for JSON parsing (required binary per SKILL.md)
node - "$SESSIONS_DIR" "$SESSIONS_JSON" "$NOW_EPOCH" "$STALE_THRESHOLD" << 'NODE_EOF'
const fs = require('fs');
const path = require('path');

const sessionsDir  = process.argv[2];
const sessionsJson = process.argv[3];
const nowEpoch     = parseInt(process.argv[4], 10);
const staleThresh  = parseInt(process.argv[5], 10);

const db = JSON.parse(fs.readFileSync(sessionsJson, 'utf8'));
const registeredIds = new Set(db.sessions.map(s => s.id));

// Disk .jsonl files
const diskFiles = fs.readdirSync(sessionsDir)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => f.replace(/\.jsonl$/, ''));

// Orphans: on disk but not registered
const orphanFiles = diskFiles.filter(id => !registeredIds.has(id));

// Stale: registered, not protected, updatedAt > 72h ago
const staleSessions = db.sessions
    .filter(s => {
        if (s.protected) return false;
        if (s.id === 'agent:main:main') return false;
        const updatedEpoch = Math.floor(new Date(s.updatedAt).getTime() / 1000);
        return (nowEpoch - updatedEpoch) > staleThresh;
    })
    .map(s => ({ id: s.id, updatedAt: s.updatedAt, sizeKb: s.sizeKb }));

// Protected sessions
const protectedSessions = db.sessions
    .filter(s => {
        if (s.id === 'agent:main:main') return true;
        if (s.protected) return true;
        const updatedEpoch = Math.floor(new Date(s.updatedAt).getTime() / 1000);
        return (nowEpoch - updatedEpoch) <= staleThresh;
    })
    .map(s => ({ id: s.id, updatedAt: s.updatedAt }));

// Orphan sizes
const orphanDetails = orphanFiles.map(id => {
    const fp = path.join(sessionsDir, id + '.jsonl');
    let sizeKb = 0;
    try { sizeKb = Math.ceil(fs.statSync(fp).size / 1024); } catch(e) {}
    return { id, sizeKb };
});

// Total reclaimable KB
const orphanKb = orphanDetails.reduce((s, o) => s + o.sizeKb, 0);
const staleKb  = staleSessions.reduce((s, o) => s + (o.sizeKb || 0), 0);
const totalKb  = orphanKb + staleKb;

const result = {
    registeredCount:   db.sessions.length,
    diskJsonlCount:    diskFiles.length,
    orphanFiles:       orphanDetails,
    staleSessions:     staleSessions,
    protectedSessions: protectedSessions,
    reclaimableKb:     totalKb,
};

process.stdout.write(JSON.stringify(result, null, 2) + '\n');
NODE_EOF
SCAN_EOF

chmod +x "$SCAN_SCRIPT"

# ── Symlink ~/.openclaw to workspace location for the scan script ─────────────
# The scan script defaults to $HOME/.openclaw; set env vars to override
# We'll also create a wrapper that sets the env vars so agents can call it
WRAPPER="$WORKSPACE/skills/session-cleanup/scripts/scan_sessions_local.sh"
cat > "$WRAPPER" << WRAPPER_EOF
#!/usr/bin/env bash
export OPENCLAW_SESSIONS_DIR="$SESSIONS_DIR"
export OPENCLAW_SESSIONS_JSON="$SESSIONS_JSON"
exec "$SCAN_SCRIPT" "\$@"
WRAPPER_EOF
chmod +x "$WRAPPER"

# Also set up ~/.openclaw symlink so the default path works too
if [ ! -e "$HOME/.openclaw" ]; then
    ln -s "$WORKSPACE/.openclaw" "$HOME/.openclaw"
fi

echo "✅ scan_sessions.sh installed and ready."
echo "   Test: $SCAN_SCRIPT scan"
echo "   Or:   $WRAPPER scan"