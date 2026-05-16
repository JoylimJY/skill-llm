#!/bin/bash
set -e

cd /workspace

# Initialize a git repository so gitpython can read a commit hash
git config --global user.email "ci@mlops-audit.internal"
git config --global user.name "MLOps CI"
git init
git add .
git commit -m "initial: credit risk churn pipeline scaffold"

echo "Git repo initialized. HEAD commit: $(git rev-parse HEAD)"

# Make scripts executable
chmod +x src/train.py 2>/dev/null || true
chmod +x deploy/serve.sh 2>/dev/null || true

echo "Setup complete."