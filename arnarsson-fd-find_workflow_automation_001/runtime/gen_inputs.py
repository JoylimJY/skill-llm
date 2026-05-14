import os
import random
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory structure ---
dirs = [
    "src/core",
    "src/utils",
    "src/legacy",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "docs/internal",
    "build/objects",
    "build/intermediates",
    "cache/session",
    "cache/query",
    "scripts",
    "config",
    "vendor/lib",
    "vendor/headers",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- .gitignore: ignore build/ and cache/ ---
gitignore_content = "build/\ncache/\n*.log\n"
(WORKSPACE / ".gitignore").write_text(gitignore_content)

# We'll use touch -d to control mtime.
# Time categories (relative to "now"):
#   - "hot":    changed 2 days ago  --> within 4d AND before 1d --> MATCH
#   - "hot2":   changed 3 days ago  --> within 4d AND before 1d --> MATCH
#   - "recent": changed 12 hours ago --> within 4d but NOT before 1d --> NO MATCH
#   - "old":    changed 10 days ago  --> NOT within 4d --> NO MATCH
#   - "edge":   changed exactly 1d ago --> borderline; fd uses strict < so "before 1d" means > 1d ago; 1d ago = 24h exactly — treat as NO MATCH to be safe, use 25h for hot boundary
# Let's be safe: hot = 2d ago, hot2 = 3d ago, recent = 6h ago, old = 8d ago

def make_file(path: Path, content: str, age_hours: int):
    """Create file and set its mtime to age_hours ago."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    # Use touch to set mtime
    dt = datetime.now() - timedelta(hours=age_hours)
    ts = dt.strftime("%Y%m%d%H%M.%S")
    subprocess.run(["touch", "-t", ts, str(path)], check=True)

# SIZE CONSTRAINT: under 100k (100000 bytes)
small_content = lambda name: f"# intermediate artifact: {name}\n" + "x" * random.randint(100, 5000)
large_content = lambda name: f"# large artifact: {name}\n" + "x" * 120000  # > 100k

# ─────────────────────────────────────────────────────────────────
# TARGET FILES: .tmp, in build/ or cache/ (gitignored!), 
#               mtime in window [1d, 4d] ago, size < 100k
# ─────────────────────────────────────────────────────────────────
target_files = [
    (WORKSPACE / "build/objects/module_a.tmp",        small_content("module_a"),   48),   # 2d ago
    (WORKSPACE / "build/intermediates/link_pass.tmp", small_content("link_pass"),  60),   # 2.5d ago
    (WORKSPACE / "cache/session/query_cache.tmp",     small_content("query_cache"),72),   # 3d ago
    (WORKSPACE / "cache/query/prefetch.tmp",          small_content("prefetch"),   80),   # ~3.3d ago
    (WORKSPACE / "build/objects/abi_check.tmp",       small_content("abi_check"),  50),   # ~2d ago
]

for path, content, age_h in target_files:
    make_file(path, content, age_h)

# ─────────────────────────────────────────────────────────────────
# DECOY 1: .tmp files OUTSIDE gitignored dirs (fd would find without -I)
#          but OUTSIDE the time window → should NOT be included
# ─────────────────────────────────────────────────────────────────
make_file(WORKSPACE / "src/core/old_stub.tmp",        small_content("old_stub"),   200)   # ~8d ago
make_file(WORKSPACE / "src/utils/fresh_stub.tmp",     small_content("fresh_stub"), 6)     # 6h ago (too recent)

# ─────────────────────────────────────────────────────────────────
# DECOY 2: .tmp files in gitignored dirs but OUTSIDE time window
# ─────────────────────────────────────────────────────────────────
make_file(WORKSPACE / "build/objects/ancient.tmp",    small_content("ancient"),    240)   # 10d ago
make_file(WORKSPACE / "cache/query/newborn.tmp",      small_content("newborn"),    3)     # 3h ago

# ─────────────────────────────────────────────────────────────────
# DECOY 3: .tmp files in gitignored dirs, in time window, but TOO LARGE
# ─────────────────────────────────────────────────────────────────
make_file(WORKSPACE / "build/intermediates/bloated.tmp", large_content("bloated"), 54)   # in window but >100k

# ─────────────────────────────────────────────────────────────────
# DECOY 4: Different extensions (not .tmp) in gitignored dirs, in window, small
# ─────────────────────────────────────────────────────────────────
make_file(WORKSPACE / "build/objects/module_a.o",     small_content("obj"),        48)
make_file(WORKSPACE / "cache/session/data.cache",     small_content("data"),       70)
make_file(WORKSPACE / "build/intermediates/notes.txt",small_content("notes"),      55)

# ─────────────────────────────────────────────────────────────────
# DISTRACTOR: regular source files with normal mtimes
# ─────────────────────────────────────────────────────────────────
regular = [
    ("src/core/main.py",        "# main module\nprint('hello')\n",     2),
    ("src/utils/helpers.py",    "# helpers\n",                          1),
    ("src/legacy/compat.c",     "/* compat layer */\n",                 5),
    ("tests/unit/test_core.py", "# unit tests\n",                       1),
    ("tests/integration/run.sh","#!/bin/bash\necho test\n",             3),
    ("docs/api/openapi.yaml",   "openapi: 3.0.0\n",                     4),
    ("docs/internal/notes.md",  "# internal\n",                         2),
    ("scripts/deploy.sh",       "#!/bin/bash\n",                        1),
    ("config/settings.json",    '{"env": "prod"}\n',                    1),
    ("vendor/lib/utils.js",     "// vendor lib\n",                      10),
    ("vendor/headers/api.h",    "// api header\n",                      7),
]
for rel, content, age_h in regular:
    make_file(WORKSPACE / rel, content, age_h * 24)

print("Workspace generated successfully.")
print("\nTarget files (should appear in audit_manifest.txt):")
for path, _, _ in target_files:
    print(f"  {path}")