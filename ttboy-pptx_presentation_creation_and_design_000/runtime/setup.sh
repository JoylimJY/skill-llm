#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/office/unpack.py
chmod +x /workspace/scripts/office/pack.py
chmod +x /workspace/scripts/office/soffice.py
chmod +x /workspace/scripts/add_slide.py
chmod +x /workspace/scripts/clean.py
chmod +x /workspace/scripts/thumbnail.py

# Ensure npm global packages are accessible
export NODE_PATH=$(npm root -g)

# Verify pptxgenjs is installed
node -e "require('pptxgenjs'); console.log('pptxgenjs OK');"

# Verify markitdown is installed
python3 -c "import markitdown; print('markitdown OK')"

# Verify react-icons and sharp for icon generation
node -e "require('react-icons/fa'); require('sharp'); console.log('react-icons + sharp OK');"

echo "Setup complete."