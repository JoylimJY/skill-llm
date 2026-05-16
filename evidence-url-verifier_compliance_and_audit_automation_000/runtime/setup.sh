#!/bin/bash
set -e

# Write the mock Flask server script
cat > /tmp/mock_evidence_server.py << 'PYEOF'
from flask import Flask, Response
import sys

app = Flask(__name__)

@app.route('/real-report')
def real_report():
    content = "SECURITY ASSESSMENT REPORT\nDate: 2024-03-01\nScope: Internal network\nResult: 0 critical findings, 2 medium findings resolved."
    return Response(content, status=200, mimetype='text/plain')

@app.route('/placeholder-page')
def placeholder_page():
    content = "This is a placeholder document. Content will be added soon. lorem ipsum dolor sit amet."
    return Response(content, status=200, mimetype='text/html')

@app.route('/missing-resource')
def missing_resource():
    return Response("Not Found", status=404, mimetype='text/plain')

@app.route('/pdf-as-text')
def pdf_as_text():
    content = b"%PDF-1.4 binary content here representing a firewall config export"
    return Response(content, status=200, mimetype='application/pdf')

@app.route('/valid-json-report')
def valid_json_report():
    import json
    data = {"report": "access_review", "date": "2024-01-15", "total_users": 42, "anomalies": 0}
    return Response(json.dumps(data), status=200, mimetype='application/json')

@app.route('/lorem-ipsum-page')
def lorem_ipsum_page():
    content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. This document is not finalized."
    return Response(content, status=200, mimetype='text/html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18923)
PYEOF

# Start mock server in background
python3 /tmp/mock_evidence_server.py &
SERVER_PID=$!
echo "Mock evidence server started with PID $SERVER_PID on port 18923"

# Wait for server to be ready
sleep 2

# Verify server is up
curl -sf http://localhost:18923/real-report > /dev/null && echo "Server is ready" || echo "WARNING: Server may not be ready"