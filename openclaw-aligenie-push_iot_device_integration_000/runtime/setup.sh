#!/bin/bash
set -e

# Start the mock push server in the background
# This simulates the AliGenie push-server.py deployed on cloud

cat > /tmp/mock_push_server.py << 'EOF'
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

RECEIVED_PUSHES_FILE = "/tmp/received_pushes.json"

@app.route('/push', methods=['POST'])
def handle_push():
    data = request.get_json(force=True)
    
    # Log received payload
    pushes = []
    if os.path.exists(RECEIVED_PUSHES_FILE):
        with open(RECEIVED_PUSHES_FILE, 'r') as f:
            try:
                pushes = json.load(f)
            except:
                pushes = []
    
    pushes.append(data)
    with open(RECEIVED_PUSHES_FILE, 'w') as f:
        json.dump(pushes, f)
    
    # Validate required fields
    if not data.get('text'):
        return jsonify({"success": False, "error": "text is required"}), 400
    
    if not data.get('openId'):
        return jsonify({"success": False, "error": "openId is required"}), 400
    
    # Return success with a deterministic messageId based on content
    import hashlib
    msg_hash = hashlib.md5(f"{data.get('text')}{data.get('openId')}".encode()).hexdigest()[:12]
    
    return jsonify({
        "success": True,
        "messageId": f"msg_{msg_hash}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=58472, debug=False)
EOF

python /tmp/mock_push_server.py &
MOCK_PID=$!
echo "Mock push server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:58472/push -X POST -H "Content-Type: application/json" -d '{"text":"test","openId":"x"}' | grep -q "200"; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... attempt $i"
    sleep 1
done

echo "Setup complete."