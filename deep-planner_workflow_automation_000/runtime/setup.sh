#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Confirm the .todolist directory and its contents are readable
echo "=== .todolist contents ==="
ls -la /workspace/.todolist/

echo "=== Setup complete ==="