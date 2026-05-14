#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/root/clawd"

# ─── Make rss.js executable ───────────────────────────────────────────────────
chmod +x "$WORKSPACE/skills/rss-reader/scripts/rss.js"

# ─── Install Node dependencies for rss-reader ────────────────────────────────
cd "$WORKSPACE/skills/rss-reader"
npm install --prefer-offline 2>/dev/null || npm install

# ─── Start a local HTTP server to serve mock RSS XML feeds ───────────────────
# Write the server script
cat > /tmp/mock_rss_server.js << 'SERVEREOF'
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

const FEED_DIR = '/root/clawd/tmp/mock_feeds';
const PORT = 18080;

const ROUTES = {
  '/competitors.xml': path.join(FEED_DIR, 'competitors.xml'),
  '/clinical.xml':    path.join(FEED_DIR, 'clinical.xml'),
  '/regulatory.xml':  path.join(FEED_DIR, 'regulatory.xml'),
};

http.createServer((req, res) => {
  const filePath = ROUTES[req.url];
  if (filePath && fs.existsSync(filePath)) {
    res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8' });
    res.end(fs.readFileSync(filePath));
  } else {
    res.writeHead(404);
    res.end('Not Found: ' + req.url);
  }
}).listen(PORT, '127.0.0.1', () => {
  console.log('Mock RSS server running on http://127.0.0.1:' + PORT);
});
SERVEREOF

# Start the mock server in the background
node /tmp/mock_rss_server.js &
MOCK_PID=$!
echo "Mock RSS server PID: $MOCK_PID"

# Wait for the server to be ready
for i in $(seq 1 10); do
  if curl -sf http://127.0.0.1:18080/competitors.xml > /dev/null 2>&1; then
    echo "Mock RSS server is up and serving feeds."
    break
  fi
  sleep 0.5
done

# Verify all three feeds are reachable
curl -sf http://127.0.0.1:18080/competitors.xml > /dev/null && echo "competitors.xml: OK"
curl -sf http://127.0.0.1:18080/clinical.xml    > /dev/null && echo "clinical.xml: OK"
curl -sf http://127.0.0.1:18080/regulatory.xml  > /dev/null && echo "regulatory.xml: OK"

echo "Setup complete."