#!/bin/bash
set -e

echo "=== Initializing OGP setup ==="

# Run ogp-install-skills if available (non-interactive, may fail gracefully)
ogp-install-skills 2>/dev/null || true

# Run ogp setup non-interactively - this may initialize the config directory
# We use timeout and pipe empty input to handle any interactive prompts
echo "" | timeout 10 ogp setup 2>/dev/null || true

# Ensure the ~/.ogp directory exists and has the pre-seeded files from gen_inputs
# (gen_inputs already wrote peers.json and config.json, but ogp setup might overwrite)
# Re-seed if ogp setup clobbered our files:
python3 - <<'PYEOF'
import json
from pathlib import Path

ogp_dir = Path.home() / ".ogp"
ogp_dir.mkdir(exist_ok=True)

# Re-seed peers.json with our test peers (approved status, no responsePolicy)
peers_data = [
    {
        "id": "a1b2c3d4e5f6a1b2",
        "displayName": "ResearchBot-Alpha",
        "status": "approved",
        "publicKey": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "federatedAt": "2026-03-01T10:00:00Z"
    },
    {
        "id": "9f8e7d6c5b4a9f8e",
        "displayName": "DataBot-Beta",
        "status": "approved",
        "publicKey": "9f8e7d6c5b4a9f8e7d6c5b4a9f8e7d6c",
        "federatedAt": "2026-03-15T14:00:00Z"
    },
    {
        "id": "deadbeef12345678",
        "displayName": "OldBot",
        "status": "revoked",
        "publicKey": "deadbeef12345678deadbeef12345678",
        "federatedAt": "2025-12-01T08:00:00Z"
    }
]
(ogp_dir / "peers.json").write_text(json.dumps(peers_data, indent=2))

# Ensure config.json exists but does NOT have agentComms section
config_path = ogp_dir / "config.json"
try:
    existing = json.loads(config_path.read_text())
except Exception:
    existing = {}

# Strip agentComms if ogp setup added any defaults, to keep the "messy" state
existing.pop("agentComms", None)
existing.setdefault("version", "0.2.24")
existing.setdefault("daemon", {"port": 8765, "host": "localhost"})
existing.setdefault("identity", {"displayName": "MyResearchAgent", "keyFile": "~/.ogp/identity.key"})

config_path.write_text(json.dumps(existing, indent=2))

print("OGP config re-seeded successfully.")
print(f"peers.json: {(ogp_dir / 'peers.json').read_text()[:200]}")
PYEOF

echo "=== Setup complete ==="
echo "Approved peers in federation:"
ogp federation list --status approved 2>/dev/null || cat ~/.ogp/peers.json | python3 -c "import json,sys; [print(f\"  {p['id']} ({p['displayName']})\") for p in json.load(sys.stdin) if p.get('status')=='approved']"