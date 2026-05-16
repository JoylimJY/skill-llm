#!/bin/bash
set -e

echo "[setup] Starting Ollama mock server..."

# Create the Ollama mock server script
cat > /tmp/ollama_mock.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""
Mock Ollama server for neon-soul testing.
Responds to all Ollama API endpoints neon-soul.mjs needs.
"""
import json
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

MOCK_MODEL = "llama3:8b"

# Realistic soul-synthesis-style responses
SIGNAL_RESPONSES = [
    "precision over speed",
    "transparency about uncertainty",
    "deep focus as a working mode",
    "quality over velocity",
    "openness about limitations",
    "sustained concentration",
]

PRINCIPLE_RESPONSES = [
    "The agent consistently chooses methodical analysis over rapid responses, demonstrating a core commitment to accuracy.",
    "Transparency about uncertainty appears as a recurring behavioral pattern across multiple interaction contexts.",
    "Deep focus is the agent's preferred cognitive mode, actively protected from interruption.",
]

AXIOM_RESPONSES = [
    "Precision supersedes speed in all analytical work.",
    "Transparency about uncertainty is foundational to trustworthy interaction.",
    "Deep, sustained focus produces superior outcomes over fragmented attention.",
]

request_count = 0

class OllamaMockHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tags":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "models": [
                    {
                        "name": MOCK_MODEL,
                        "model": MOCK_MODEL,
                        "modified_at": "2024-03-01T00:00:00Z",
                        "size": 4661224676,
                        "digest": "sha256:abc123mock",
                        "details": {"family": "llama", "parameter_size": "8B", "quantization_level": "Q4_0"}
                    }
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global request_count
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/generate", "/api/chat"):
            request_count += 1
            prompt_text = ""
            if "prompt" in payload:
                prompt_text = payload["prompt"].lower()
            elif "messages" in payload:
                msgs = payload["messages"]
                if msgs:
                    prompt_text = str(msgs[-1].get("content", "")).lower()

            # Generate contextually appropriate mock responses
            if "signal" in prompt_text or "extract" in prompt_text or "pattern" in prompt_text:
                idx = request_count % len(SIGNAL_RESPONSES)
                response_text = f"Signal identified: {SIGNAL_RESPONSES[idx]}. This pattern appears consistently across multiple sessions and reflects a stable behavioral disposition."
            elif "principle" in prompt_text or "generalize" in prompt_text:
                idx = request_count % len(PRINCIPLE_RESPONSES)
                response_text = PRINCIPLE_RESPONSES[idx]
            elif "axiom" in prompt_text or "compress" in prompt_text or "core" in prompt_text:
                idx = request_count % len(AXIOM_RESPONSES)
                response_text = AXIOM_RESPONSES[idx]
            elif "tension" in prompt_text or "conflict" in prompt_text:
                response_text = "No significant tensions detected between the identified patterns."
            elif "dimension" in prompt_text or "soulcraft" in prompt_text:
                response_text = "This pattern relates to the cognitive and epistemic dimensions of identity."
            else:
                response_text = f"Analysis complete. The agent demonstrates consistent behavioral patterns across {request_count} evaluated sessions, suggesting stable identity formation."

            stream = payload.get("stream", True)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if stream:
                # Stream response token by token (simplified)
                words = response_text.split()
                for i, word in enumerate(words):
                    chunk = {
                        "model": MOCK_MODEL,
                        "created_at": "2024-03-01T00:00:00Z",
                        "response": word + (" " if i < len(words) - 1 else ""),
                        "done": False
                    }
                    self.wfile.write((json.dumps(chunk) + "\n").encode())
                    self.wfile.flush()
                # Final chunk
                final = {
                    "model": MOCK_MODEL,
                    "created_at": "2024-03-01T00:00:00Z",
                    "response": "",
                    "done": True,
                    "total_duration": 500000000,
                    "eval_count": len(words)
                }
                self.wfile.write((json.dumps(final) + "\n").encode())
            else:
                response = {
                    "model": MOCK_MODEL,
                    "created_at": "2024-03-01T00:00:00Z",
                    "response": response_text,
                    "done": True,
                    "total_duration": 500000000,
                    "eval_count": len(response_text.split())
                }
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 11434), OllamaMockHandler)
    print(f"[ollama-mock] Listening on http://0.0.0.0:11434", flush=True)
    server.serve_forever()
MOCK_EOF

chmod +x /tmp/ollama_mock.py

# Start mock server in background
python3 /tmp/ollama_mock.py &
OLLAMA_PID=$!
echo "[setup] Ollama mock PID: $OLLAMA_PID"

# Wait for mock to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "[setup] Ollama mock is ready."
        break
    fi
    sleep 1
done

# Install neon-soul
echo "[setup] Installing neon-soul..."
cd /workspace
npm install neon-soul 2>&1 | tail -5 || echo "[setup] npm install attempted"

# Verify installation
NEON_PATH=$(node -e "require.resolve('neon-soul/scripts/neon-soul.mjs')" 2>/dev/null || \
            node -e "const p=require.resolve('neon-soul'); console.log(p.replace('/index.js','/scripts/neon-soul.mjs'))" 2>/dev/null || \
            find /workspace/node_modules -name "neon-soul.mjs" 2>/dev/null | head -1 || \
            find /usr/lib/node_modules -name "neon-soul.mjs" 2>/dev/null | head -1)

echo "[setup] neon-soul.mjs path: ${NEON_PATH}"

# Store the path for agent use
echo "NEON_SOUL_SCRIPT=${NEON_PATH}" > /workspace/.neon-env
echo "[setup] Environment ready."
echo "[setup] Workspace contents:"
ls /workspace/