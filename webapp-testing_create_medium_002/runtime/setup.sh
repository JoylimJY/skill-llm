#!/bin/bash
set -eux

# Setup backend dependencies (nothing external, pure python)

# Setup frontend dependencies
cd frontend
npm install --legacy-peer-deps
cd ..

# Install Playwright browsers
python -m playwright install chromium
