#!/bin/bash
set -e

echo "=== BaZi Partner Sandbox Setup ==="

# Verify the bazi tools are installed and accessible
echo "Checking bazi_analyze..."
python3 -c "import subprocess; result = subprocess.run(['bazi_analyze', '--help'], capture_output=True, text=True); print('bazi_analyze found')" 2>/dev/null || \
python3 -c "
import importlib.util, sys
# Try to find installed entry points
import pkg_resources
installed = [p.project_name for p in pkg_resources.working_set]
print('Installed packages:', [p for p in installed if 'bazi' in p.lower()])
"

# Make sure SOUL.md is writable
chmod 666 /workspace/SOUL.md

# Verify Python3 and tools availability
python3 --version

# List what bazi tools are available
echo "=== Available bazi entry points ==="
python3 -c "
import pkg_resources
for ep_group in ['console_scripts']:
    try:
        eps = list(pkg_resources.iter_entry_points(ep_group))
        bazi_eps = [ep for ep in eps if 'bazi' in ep.name.lower()]
        for ep in bazi_eps:
            print(f'  {ep.name} -> {ep.module_name}')
    except Exception as e:
        print(f'Error listing entry points: {e}')
" 2>/dev/null || echo "Entry point listing unavailable"

# Try to find the MCP server script
python3 -c "
import importlib
try:
    import mcp_bazi_partner
    print('mcp_bazi_partner module found at:', mcp_bazi_partner.__file__)
except ImportError:
    try:
        import bazi_partner
        print('bazi_partner module found')
    except ImportError:
        print('Module not found under expected names, checking installed files...')
        import pkg_resources, os
        try:
            dist = pkg_resources.get_distribution('mcp-bazi-partner')
            print('Distribution found:', dist.location)
        except Exception as e2:
            print('Distribution lookup failed:', e2)
" 2>/dev/null || true

echo "=== Workspace contents ==="
ls -la /workspace/

echo "=== Setup complete ==="