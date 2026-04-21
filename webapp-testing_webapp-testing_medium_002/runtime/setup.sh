#!/bin/bash
set -e
echo 'Setting up environment...'
pip install playwright --quiet
python -m playwright install chromium
python -m playwright install-deps chromium
echo 'Setup complete.'
