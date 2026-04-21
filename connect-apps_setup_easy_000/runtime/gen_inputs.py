import os

# Create a mock composio plugin directory structure
os.makedirs('.claude/plugins/composio-toolrouter', exist_ok=True)

# Create a mock plugin manifest
with open('.claude/plugins/composio-toolrouter/manifest.json', 'w') as f:
    f.write('{"name": "composio-toolrouter", "version": "1.0.0", "description": "Connect to external apps"}')

# Create a mock setup script
with open('.claude/plugins/composio-toolrouter/setup.py', 'w') as f:
    f.write('print("Composio Tool Router setup completed successfully")')

# Create a sample README with instructions
with open('README.md', 'w') as f:
    f.write('# Composio Setup\n\nTo verify setup:\n1. Install plugin\n2. Run setup\n3. Create verification file')