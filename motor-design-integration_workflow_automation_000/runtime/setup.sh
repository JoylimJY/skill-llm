#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying Python environment..."
python3 -c "import numpy, pandas; print('numpy:', numpy.__version__, 'pandas:', pandas.__version__)"

echo "Setup complete. Workspace ready for agent."
ls -la /workspace/project/specs/