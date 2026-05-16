#!/bin/bash
set -e

# Ensure .openclaw directories are accessible
chmod -R 755 /workspace/.openclaw

# Create a simple mock web_search command that returns "no results" 
# (agent should use the pre-gathered comp data from the JSON file)
cat > /usr/local/bin/web_search << 'EOF'
#!/bin/bash
echo "[mock] web_search: results already gathered in raw-comps JSON file."
EOF
chmod +x /usr/local/bin/web_search

echo "Setup complete."