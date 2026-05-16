#!/usr/bin/env bash
set -e

echo "=== Setting up agent-sync sandbox ==="

# Ensure init.sh is executable
chmod +x /workspace/agent-sync/scripts/init.sh

# Create a minimal qmd shim so the agent can call it without it being installed
# (The SKILL.md references qmd, but the real tool isn't required for the core doc workflow)
cat > /usr/local/bin/qmd << 'EOF'
#!/usr/bin/env python3
"""Minimal qmd shim for agent-sync sandbox."""
import sys
import os
import glob

args = sys.argv[1:]
if not args:
    print("Usage: qmd <command> [args]")
    sys.exit(1)

cmd = args[0]

if cmd == "index":
    target = args[1] if len(args) > 1 else "."
    print(f"[qmd] Indexed {target}")
    md_files = glob.glob(f"{target}/**/*.md", recursive=True)
    for f in md_files:
        print(f"  + {f}")
    print("[qmd] Index complete.")

elif cmd == "query":
    query = " ".join(args[1:]) if len(args) > 1 else ""
    print(f"[qmd] Query: '{query}'")
    print("[qmd] Relevant fragments: See TASK.md and CHANGELOG.md for current state.")

else:
    print(f"[qmd] Unknown command: {cmd}")
    sys.exit(1)
EOF
chmod +x /usr/local/bin/qmd

echo "=== Setup complete ==="
echo "Workspace contents:"
ls /workspace/