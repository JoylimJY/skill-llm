#!/bin/bash

# Create mock Rube executable that returns predefined responses
cat > /usr/local/bin/rube << 'EOF'
#!/bin/bash

if [[ "$1" == "slack" && "$2" == "find-channels" ]]; then
    cat /workspace/rube_responses/slack_channels.json
elif [[ "$1" == "slack" && "$2" == "send-message" ]]; then
    cat /workspace/rube_responses/message_post.json
else
    echo '{"error": "Unknown command"}'
fi
EOF

chmod +x /usr/local/bin/rube

# Verify rube is working
echo "Testing Rube mock..."
rube slack find-channels