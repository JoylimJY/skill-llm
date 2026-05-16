#!/bin/bash
set -e

echo "=== Setting up sandbox environment ==="

# Make scripts executable
chmod +x /workspace/scripts/scan_repos.py
chmod +x /workspace/scripts/update_kb.py

# Configure git identity (required for commits)
git config --global user.email "sandbox@test.local"
git config --global user.name "Sandbox Agent"
git config --global init.defaultBranch main

# ── Create a real bare git repo that can be cloned locally ──────────────────
BARE_DIR="/workspace/bare_remotes/ml-utils.git"
rm -rf "$BARE_DIR"
mkdir -p "$BARE_DIR"
git init --bare "$BARE_DIR"

# Create a temp working tree to populate the bare repo
TEMP_WORK="/tmp/ml-utils-init"
rm -rf "$TEMP_WORK"
mkdir -p "$TEMP_WORK"
cd "$TEMP_WORK"
git init
git remote add origin "$BARE_DIR"

# Add some realistic content
mkdir -p src tests
cat > src/models.py << 'PYEOF'
# ML utility models
class LinearModel:
    def fit(self, X, y): pass
    def predict(self, X): pass
PYEOF

cat > src/preprocessing.py << 'PYEOF'
# Data preprocessing utilities
def normalize(data): return data
def split(data, ratio=0.8): return data[:int(len(data)*ratio)], data[int(len(data)*ratio):]
PYEOF

cat > tests/test_models.py << 'PYEOF'
def test_linear_model():
    from src.models import LinearModel
    m = LinearModel()
    assert m is not None
PYEOF

cat > requirements.txt << 'EOF'
numpy>=1.21
scikit-learn>=0.24
EOF

cat > .git/description << 'EOF'
Machine learning utility library with preprocessing and model training helpers
EOF

git add .
git commit -m "Initial commit: ml-utils library"
git push origin main

# Clean up temp work tree
cd /
rm -rf "$TEMP_WORK"

# ── Ensure the github_repos directory has proper git repos ──────────────────
# Fix auth-service .git to be a minimal valid git repo
AUTH_REPO="/workspace/github_repos/auth-service"
cd "$AUTH_REPO"
if [ ! -f ".git/HEAD" ]; then
    git init
    git add .
    git commit -m "Initial commit"
fi

# Fix data-pipeline .git similarly
DATA_REPO="/workspace/github_repos/data-pipeline"
cd "$DATA_REPO"
if [ ! -f ".git/HEAD" ]; then
    git init
    git add .
    git commit -m "Initial commit"
fi

echo "=== Bare remote ml-utils.git is ready at: $BARE_DIR ==="
echo "=== Setup complete ==="