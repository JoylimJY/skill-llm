#!/bin/bash
set -e

chmod +x /workspace/scripts/notify.sh
chmod +x /workspace/scripts/check_db.sh 2>/dev/null || true

# Start the mock server that records all openclaw calls
cat > /tmp/mock_server.py << 'MOCK_EOF'
#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)
LOG_FILE = "/tmp/openclaw_calls.jsonl"

@app.route('/record', methods=['POST'])
def record():
    data = request.get_json(force=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + "\n")
    return jsonify({"recorded": True, "entry": data})

@app.route('/calls', methods=['GET'])
def calls():
    calls = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
    return jsonify(calls)

@app.route('/reset', methods=['POST'])
def reset():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return jsonify({"reset": True})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=19876, debug=False)
MOCK_EOF

python3 /tmp/mock_server.py &
MOCK_PID=$!
echo $MOCK_PID > /tmp/mock_server.pid

# Wait for mock server to be ready
for i in $(seq 1 20); do
    if curl -s http://127.0.0.1:19876/calls > /dev/null 2>&1; then
        echo "Mock server ready."
        break
    fi
    sleep 0.5
done

echo "Setup complete. Mock server PID: $MOCK_PID"