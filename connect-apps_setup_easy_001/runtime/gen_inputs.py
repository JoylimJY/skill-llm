import os

# Create a mock plugin directory structure
os.makedirs('.claude/plugins', exist_ok=True)

# Create a sample config file that might exist
with open('.claude/config.json', 'w') as f:
    f.write('{"plugins_enabled": false, "version": "1.0.0"}')

# Create a mock composio directory for checking installation
os.makedirs('.composio', exist_ok=True)
with open('.composio/setup_status.txt', 'w') as f:
    f.write('not_configured')

print('Mock environment created for plugin setup task')