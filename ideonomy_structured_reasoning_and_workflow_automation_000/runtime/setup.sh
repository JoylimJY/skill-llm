#!/bin/bash
set -e

echo "=== Setup: Verifying ideonomy installation ==="
ideonomy --help > /dev/null 2>&1 && echo "ideonomy OK" || echo "WARNING: ideonomy not found"

echo "=== Setup: Listing workspace ==="
ls /workspace/consulting/internal/

echo "=== Setup complete ==="