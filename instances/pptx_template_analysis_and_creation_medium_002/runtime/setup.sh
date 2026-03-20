#!/bin/bash

# Create scripts directory structure
mkdir -p scripts/office

# Copy the soffice.py helper from the skill content
cat > scripts/office/soffice.py << 'EOF'
"""Helper for running LibreOffice in sandboxed environments"""
import os
import socket
import subprocess
import tempfile
from pathlib import Path

def get_soffice_env():
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"
    return env

def run_soffice(args, **kwargs):
    env = get_soffice_env()
    return subprocess.run(["soffice"] + args, env=env, **kwargs)
EOF

# Create thumbnail script
cat > scripts/thumbnail.py << 'EOF'
import sys
import subprocess
from pathlib import Path

def create_thumbnails(pptx_path, output_prefix="thumbnails", cols=3):
    pptx_path = Path(pptx_path)
    if not pptx_path.exists():
        print(f"File {pptx_path} not found")
        return
    
    # Convert to PDF first
    from scripts.office.soffice import run_soffice
    pdf_path = pptx_path.with_suffix('.pdf')
    result = run_soffice(["--headless", "--convert-to", "pdf", str(pptx_path)])
    
    if result.returncode == 0 and pdf_path.exists():
        # Convert PDF to images
        subprocess.run(["pdftoppm", "-jpeg", "-r", "150", str(pdf_path), output_prefix])
        print(f"Created thumbnail images from {pptx_path}")
    else:
        print(f"Failed to convert {pptx_path} to PDF")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_thumbnails(sys.argv[1])
    else:
        print("Usage: python scripts/thumbnail.py presentation.pptx")
EOF

# Make scripts executable
chmod +x scripts/*.py
chmod +x scripts/office/*.py