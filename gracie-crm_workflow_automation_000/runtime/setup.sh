#!/bin/bash
set -e

# Make crm.py executable
chmod +x /root/StudioBrain/00_SYSTEM/skills/gracie-crm/crm.py

# Verify Python can parse crm.py without errors
python3 -c "import ast; ast.parse(open('/root/StudioBrain/00_SYSTEM/skills/gracie-crm/crm.py').read())" \
  && echo "crm.py syntax OK" || echo "crm.py syntax ERROR"

echo "Setup complete. CRM workspace ready."