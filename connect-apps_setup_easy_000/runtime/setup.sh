#!/bin/bash
# Mock the plugin installation system
mkdir -p /usr/local/bin
echo '#!/bin/bash' > /usr/local/bin/plugin
echo 'echo "Plugin $2 installed successfully"' >> /usr/local/bin/plugin
chmod +x /usr/local/bin/plugin

# Mock the composio-toolrouter command
echo '#!/bin/bash' > /usr/local/bin/composio-toolrouter
echo 'if [ "$1" = "setup" ]; then echo "Composio Tool Router setup completed successfully"; fi' >> /usr/local/bin/composio-toolrouter
chmod +x /usr/local/bin/composio-toolrouter