#!/usr/bin/env bash
set -e

# Ensure the skill-list.py script is executable
chmod +x /root/.openclaw/workspace/skills/all-skill-list/scripts/skill-list.py

# Verify the stale cache is in place (sanity check)
python3 - <<'PYEOF'
import pickle
from pathlib import Path
cache_path = Path("/root/.openclaw/workspace/skills/all-skill-list/scripts/skills_cache.pickle")
assert cache_path.exists(), "Cache file missing!"
with open(cache_path, "rb") as f:
    data = pickle.load(f)
dirs = data["skill_dirs"]
assert "old-skill-alpha" in dirs, "Stale cache not seeded correctly"
assert "image-resizer" not in dirs, "Stale cache should NOT contain image-resizer yet"
print(f"✅ Stale cache verified. Cached dirs: {dirs}")
PYEOF

echo "✅ Setup complete. Workspace ready for agent."