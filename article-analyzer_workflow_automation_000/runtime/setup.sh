#!/bin/bash
set -e

# Make mock tools executable and accessible
chmod +x /workspace/tools/web_fetch
chmod +x /workspace/tools/feishu_doc
chmod +x /workspace/tools/article_server.py

# Add tools to PATH
ln -sf /workspace/tools/web_fetch /usr/local/bin/web_fetch
ln -sf /workspace/tools/feishu_doc /usr/local/bin/feishu_doc

# Start the article server in the background
cd /workspace/tools
python3 article_server.py &
SERVER_PID=$!
echo "Article server started with PID $SERVER_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if nc -z localhost 8765 2>/dev/null; then
        echo "Article server is ready on port 8765"
        break
    fi
    sleep 1
done

# Verify server is serving
curl -s http://localhost:8765/article | head -5 || echo "WARNING: server health check failed"

echo "Setup complete."
echo "Article URL: http://localhost:8765/article"
echo "Tools available: web_fetch, feishu_doc"