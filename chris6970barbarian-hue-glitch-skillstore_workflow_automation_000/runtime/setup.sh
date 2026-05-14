#!/bin/bash
set -e

echo "=== Setting up skillstore environment ==="

# Ensure ~/.openclaw/workspace/skills/ exists
mkdir -p ~/.openclaw/workspace/skills/

# Try to install skillstore from the openclaw/skills GitHub repo
SKILL_DIR="/opt/openclaw-skills"

if [ -d "$SKILL_DIR/skillstore" ]; then
    echo "Found skillstore in cloned repo"
    cd "$SKILL_DIR/skillstore"
    
    # Install npm dependencies if package.json exists
    if [ -f "package.json" ]; then
        npm install --prefer-offline 2>/dev/null || npm install
    fi
    
    # Make main.js executable and link it
    if [ -f "main.js" ]; then
        chmod +x main.js
        # Create a global wrapper script
        cat > /usr/local/bin/skillstore << 'EOF'
#!/bin/bash
node /opt/openclaw-skills/skillstore/main.js "$@"
EOF
        chmod +x /usr/local/bin/skillstore
        echo "skillstore installed at /usr/local/bin/skillstore"
    fi
else
    echo "skillstore directory not found in cloned repo, attempting direct install..."
    # Fallback: try npm global install if available
    cd /tmp
    git clone https://github.com/openclaw/skills.git openclaw-skills-fallback 2>/dev/null || true
    
    if [ -d "/tmp/openclaw-skills-fallback/skillstore" ]; then
        cp -r /tmp/openclaw-skills-fallback/skillstore /opt/skillstore-install
        cd /opt/skillstore-install
        npm install 2>/dev/null || true
        chmod +x main.js 2>/dev/null || true
        cat > /usr/local/bin/skillstore << 'EOF'
#!/bin/bash
node /opt/skillstore-install/main.js "$@"
EOF
        chmod +x /usr/local/bin/skillstore
        echo "skillstore installed via fallback"
    else
        echo "WARNING: Could not install skillstore from GitHub"
    fi
fi

# Verify installation
echo "=== Verifying skillstore ==="
which skillstore && skillstore known | head -5 || echo "skillstore not available in PATH"

echo "=== Setup complete ==="