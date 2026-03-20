#!/bin/bash
set -e

# Ensure LibreOffice can run in headless mode
export SAL_USE_VCLPLUGIN=svp

# Create scripts directory structure expected by the skill
mkdir -p scripts/office

# Copy the soffice helper script from skill content
cat > scripts/office/soffice.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
import sys

def get_soffice_env():
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"
    return env

def run_soffice(args, **kwargs):
    env = get_soffice_env()
    return subprocess.run(["soffice"] + args, env=env, **kwargs)

if __name__ == "__main__":
    result = run_soffice(sys.argv[1:])
    sys.exit(result.returncode)
EOF

chmod +x scripts/office/soffice.py

echo "Setup complete"
