#!/usr/bin/env bash
set -e

chmod +x /workspace/skills/bazi-pan/bazi.py

# Quick sanity check that the script runs
python3 /workspace/skills/bazi-pan/bazi.py 1990 8 15 14:30 > /dev/null && echo "bazi.py sanity check passed"