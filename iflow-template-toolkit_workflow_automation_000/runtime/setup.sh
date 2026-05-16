#!/bin/bash
set -e

# Ensure toolkit is on PYTHONPATH
export PYTHONPATH="/skills/iflow-template-toolkit"

# Make workspace writable
chmod -R 777 /workspace

# Verify toolkit is importable
python3 -c "
import sys
sys.path.insert(0, '/skills/iflow-template-toolkit')
from src import TemplateEngine, render_template, init_translator, t
print('iflow-template-toolkit: OK')
"

echo "Setup complete."