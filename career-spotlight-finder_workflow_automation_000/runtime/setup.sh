#!/bin/bash
set -e

echo "=== Setup: career-spotlight-finder sandbox ==="

# Ensure pandoc is available
which pandoc && echo "pandoc OK: $(pandoc --version | head -1)" || echo "WARNING: pandoc not found"

# Ensure the workspace guides are executable/readable
chmod -R 644 /workspace/guides/*.md 2>/dev/null || true
chmod -R 644 /workspace/templates/*.md 2>/dev/null || true

# Ensure ~/.career-spotlight exists with correct permissions
mkdir -p ~/.career-spotlight/{analyses,copies,history}
chmod -R 755 ~/.career-spotlight

# Ensure python-docx is available (needed to have generated the .docx)
python3 -c "import docx; print('python-docx OK')" 2>/dev/null || echo "python-docx not available"

# Verify source materials exist
echo "=== Source Materials ==="
find /workspace/my_projects -type f | sort

echo "=== Pre-existing career-spotlight state ==="
find ~/.career-spotlight -type f | sort

echo "=== Guides available ==="
ls /workspace/guides/

echo "=== Templates available ==="
ls /workspace/templates/

echo "=== Setup complete ==="