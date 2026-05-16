#!/bin/bash
set -e

echo "=== Setting up NDRC Oil Price Monitor sandbox ==="

# Make the monitor script executable
chmod +x /workspace/oil-price-monitor/oil_price_monitor.py

# Start a mock NDRC HTTP server (Flask) as background process
# This serves fake oil price announcements so --test and --recent work offline
cat > /tmp/mock_ndrc_server.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""Mock NDRC news server for testing."""
from flask import Flask, Response
app = Flask(__name__)

MOCK_HTML = """<!DOCTYPE html>
<html>
<head><title>国家发改委 - 新闻发布</title></head>
<body>
<div class="news-list">
  <ul>
    <li class="news-item">
      <a href="/xwdt/xwfb/202604/t20260407_1234567.html">
        国家发展改革委关于2026年第1次成品油价格调整的公告
      </a>
      <span class="date">2026-04-07</span>
    </li>
    <li class="news-item">
      <a href="/xwdt/xwfb/202604/t20260407_1234568.html">
        汽油、柴油价格每吨分别上调300元和290元
      </a>
      <span class="date">2026-04-07</span>
    </li>
    <li class="news-item">
      <a href="/xwdt/xwfb/202603/t20260321_1234000.html">
        关于天然气价格政策的通知（非成品油）
      </a>
      <span class="date">2026-03-21</span>
    </li>
  </ul>
</div>
</body>
</html>"""

@app.route("/xwdt/xwfb/")
@app.route("/xwdt/xwfb/<path:path>")
def news(path=""):
    return Response(MOCK_HTML, mimetype="text/html; charset=utf-8")

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5099, debug=False)
MOCK_EOF

python3 /tmp/mock_ndrc_server.py &
MOCK_PID=$!
echo "Mock NDRC server started (PID=$MOCK_PID) on port 5099"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:5099/health > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

echo "=== Sandbox ready ==="
echo ""
echo "Task: Configure the oil-price-monitor and produce a windows report."
echo "Workspace: /workspace"
echo "Skill dir: /workspace/oil-price-monitor/"