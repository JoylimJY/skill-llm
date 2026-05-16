#!/bin/bash
set -e

# Write the mock AdBlock DNS API server
cat > /workspace/mock_adblock_api.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock AdBlock DNS Stats API server.
Simulates the real server's API endpoints as documented in SKILL.md.
Maintains stateful whitelist/blacklist in memory.
Responds correctly to /check based on blocklist.txt + runtime additions.
"""
from flask import Flask, request, jsonify
import json
import os
import threading

app = Flask(__name__)

DATA_DIR = "/workspace/skills/adblock/data"

# In-memory state
_whitelist = set()
_custom_blacklist = set()
_base_blocklist = set()

def load_initial_state():
    global _whitelist, _custom_blacklist, _base_blocklist
    wl_path = os.path.join(DATA_DIR, "whitelist.txt")
    if os.path.exists(wl_path):
        with open(wl_path) as f:
            _whitelist = set(line.strip() for line in f if line.strip())

    cb_path = os.path.join(DATA_DIR, "custom-blacklist.txt")
    if os.path.exists(cb_path):
        with open(cb_path) as f:
            _custom_blacklist = set(line.strip() for line in f if line.strip())

    bl_path = os.path.join(DATA_DIR, "blocklist.txt")
    if os.path.exists(bl_path):
        with open(bl_path) as f:
            _base_blocklist = set(line.strip() for line in f if line.strip())

load_initial_state()

@app.route('/stats', methods=['GET'])
def stats():
    stats_path = os.path.join(DATA_DIR, "stats.json")
    with open(stats_path) as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/check', methods=['GET'])
def check():
    domain = request.args.get('domain', '').strip().lower()
    if not domain:
        return jsonify({"error": "domain parameter required"}), 400
    
    all_blocked = _base_blocklist | _custom_blacklist
    is_whitelisted = domain in _whitelist
    is_blocked = (domain in all_blocked) and not is_whitelisted
    
    result = {
        "domain": domain,
        "blocked": is_blocked,
        "whitelisted": is_whitelisted,
        "response": "0.0.0.0" if is_blocked else "forwarded"
    }
    return jsonify(result)

@app.route('/whitelist/add', methods=['POST'])
def whitelist_add():
    data = request.get_json()
    if not data or 'domain' not in data:
        return jsonify({"error": "domain required"}), 400
    domain = data['domain'].strip().lower()
    _whitelist.add(domain)
    # Persist to file
    wl_path = os.path.join(DATA_DIR, "whitelist.txt")
    with open(wl_path, 'w') as f:
        for d in sorted(_whitelist):
            f.write(d + '\n')
    return jsonify({"success": True, "domain": domain, "action": "whitelisted"})

@app.route('/blacklist/add', methods=['POST'])
def blacklist_add():
    data = request.get_json()
    if not data or 'domain' not in data:
        return jsonify({"error": "domain required"}), 400
    domain = data['domain'].strip().lower()
    _custom_blacklist.add(domain)
    # Persist to file
    cb_path = os.path.join(DATA_DIR, "custom-blacklist.txt")
    with open(cb_path, 'w') as f:
        for d in sorted(_custom_blacklist):
            f.write(d + '\n')
    return jsonify({"success": True, "domain": domain, "action": "blacklisted"})

@app.route('/whitelist', methods=['GET'])
def whitelist_view():
    return jsonify({"whitelist": sorted(_whitelist)})

@app.route('/update', methods=['POST'])
def update():
    return jsonify({"success": True, "message": "Blocklists updated", "domains": len(_base_blocklist)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8053, debug=False)
PYEOF

chmod +x /workspace/mock_adblock_api.py

# Start the mock server in background
python3 /workspace/mock_adblock_api.py &
MOCK_PID=$!
echo $MOCK_PID > /workspace/mock_api.pid
echo "Mock AdBlock DNS API started on port 8053 (PID: $MOCK_PID)"

# Wait for it to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8053/stats > /dev/null 2>&1; then
        echo "Mock API is ready."
        break
    fi
    sleep 1
done

echo "Setup complete."