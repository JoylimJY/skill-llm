import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# --- Create realistic distractor files and a messy initial state ---

# Top-level workspace noise
distractor_dirs = [
    "projects/alpha/src",
    "projects/alpha/tests",
    "projects/beta/config",
    "notes/meeting-notes",
    "notes/research",
    "tools/legacy",
    "tools/deprecated",
    "downloads/archives",
    "scripts",   # The scripts dir exists but scripts are stubs/empty
    "Obsidian",  # Obsidian root exists but is incomplete
]

for d in distractor_dirs:
    Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# Distractor files in projects
Path(os.path.join(WORKSPACE, "projects/alpha/src/main.py")).write_text(
    "# legacy app\nprint('hello')\n"
)
Path(os.path.join(WORKSPACE, "projects/alpha/tests/test_main.py")).write_text(
    "# tests\ndef test_noop(): pass\n"
)
Path(os.path.join(WORKSPACE, "projects/beta/config/settings.yaml")).write_text(
    "debug: true\nversion: 0.1.0\n"
)
Path(os.path.join(WORKSPACE, "notes/meeting-notes/2024-01-15.md")).write_text(
    "## Meeting Notes\n- Discussed roadmap\n- Action items pending\n"
)
Path(os.path.join(WORKSPACE, "notes/research/openclaw-overview.md")).write_text(
    "# OpenClaw Overview\nA tool for managing gateways and channels.\n"
)
Path(os.path.join(WORKSPACE, "tools/legacy/old-sync.sh")).write_text(
    "#!/bin/bash\necho 'old sync script'\n"
)
Path(os.path.join(WORKSPACE, "tools/deprecated/cleanup.py")).write_text(
    "# deprecated cleanup\nimport os\n"
)
Path(os.path.join(WORKSPACE, "downloads/archives/v1.0.0.tar.gz.info")).write_text(
    "archive: openclaw-v1.0.0\n"
)

# The scripts directory has stub files (exist but are incomplete shells)
Path(os.path.join(WORKSPACE, "scripts/sync-docs.sh")).write_text(
    "#!/bin/bash\n# TODO: implement doc sync\nexit 0\n"
)
Path(os.path.join(WORKSPACE, "scripts/pick-daily-tip.sh")).write_text(
    "#!/bin/bash\n# TODO: implement tip picker\nexit 0\n"
)
Path(os.path.join(WORKSPACE, "scripts/send-daily-tip.sh")).write_text(
    "#!/bin/bash\n# TODO: implement tip sender\nexit 0\n"
)
Path(os.path.join(WORKSPACE, "scripts/README-scripts.txt")).write_text(
    "These scripts are managed by the coaching system.\n"
)

# Obsidian root exists but knowledge base is NOT set up
Path(os.path.join(WORKSPACE, "Obsidian/personal-notes.md")).write_text(
    "# Personal Notes\nRandom personal notes here.\n"
)
Path(os.path.join(WORKSPACE, "Obsidian/bookmarks.md")).write_text(
    "# Bookmarks\n- https://example.com\n"
)

# A misleading/wrong existing json file in Obsidian (wrong structure)
Path(os.path.join(WORKSPACE, "Obsidian/config.json")).write_text(
    json.dumps({"theme": "dark", "font_size": 14}, indent=2)
)

# A partial/wrong version of daily-tips.json at the WRONG location (trap)
Path(os.path.join(WORKSPACE, "Obsidian/daily-tips.json")).write_text(
    json.dumps({"wrong_key": "this is in the wrong place"}, indent=2)
)

# Distractor crontab-like file with WRONG times (trap for agents guessing)
Path(os.path.join(WORKSPACE, "tools/legacy/old-crontab.txt")).write_text(
    "0 7 * * * /scripts/send.sh\n"
    "0 21 * * * /scripts/pick.sh\n"
    "0 3 * * * /scripts/sync.sh\n"
)

# A partial openclaw docs directory with wrong structure
Path(os.path.join(WORKSPACE, "Obsidian/openclaw-notes")).mkdir(parents=True, exist_ok=True)
Path(os.path.join(WORKSPACE, "Obsidian/openclaw-notes/random.md")).write_text(
    "# Random note\nThis is NOT the correct knowledge base location.\n"
)

# Additional noise files
for i in range(1, 5):
    Path(os.path.join(WORKSPACE, f"downloads/archives/note_{i}.txt")).write_text(
        f"Archive note {i}: placeholder content\n"
    )

print(f"[gen_inputs] Workspace initialized at {WORKSPACE}")
print("[gen_inputs] Directory structure:")
for root, dirs, files in os.walk(WORKSPACE):
    level = root.replace(WORKSPACE, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')