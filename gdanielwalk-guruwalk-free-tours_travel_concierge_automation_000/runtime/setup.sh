#!/usr/bin/env bash
set -e

# ── Write the mock MCP server ─────────────────────────────────────────────────
cat > /mock_mcp_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock GuruWalk MCP server.
Mimics the real endpoint at /mcp with SSE-based MCP protocol (streamable HTTP).
Responds to: initialize, tools/list, tools/call
"""
import json
import threading
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

# ── Tour data (only returned when city slug is exactly "san-sebastian") ───────
TOURS_DATA = [
    {
        "title": "Old Town San Sebastian Free Tour",
        "url": "https://www.guruwalk.com/tours/san-sebastian-old-town-123",
        "meetpoint_address": "Plaza de la Constitución, 20003 Donostia, Gipuzkoa",
        "average_rating": 4.9,
        "duration": 120,
        "guru": {"name": "Amaia Zubieta"},
        "image_url": "https://cdn.guruwalk.com/img/tour-123.jpg",
        "events": [
            {
                "start_time": "2025-08-10T10:00:00Z",
                "available_spots": 8,
                "language": "en"
            },
            {
                "start_time": "2025-08-10T16:00:00Z",
                "available_spots": 0,
                "language": "en"
            },
            {
                "start_time": "2025-08-11T10:00:00Z",
                "available_spots": 5,
                "language": "en"
            }
        ]
    },
    {
        "title": None,
        "url": "https://www.guruwalk.com/tours/san-sebastian-ghost-456",
        "meetpoint_address": "Parte Vieja, Donostia",
        "average_rating": 4.7,
        "duration": 90,
        "guru": {"name": "Iñigo Etxeberria"},
        "image_url": "https://cdn.guruwalk.com/img/tour-456.jpg",
        "events": [
            {
                "start_time": "2025-08-11T11:00:00Z",
                "available_spots": 3,
                "language": "en"
            }
        ]
    },
    {
        "title": "Tour Gratuito por Donostia",
        "url": "https://www.guruwalk.com/tours/san-sebastian-spanish-789",
        "meetpoint_address": "Ayuntamiento de Donostia, Plaza de la Constitución",
        "average_rating": 4.95,
        "duration": 150,
        "guru": {"name": "Leire Aguirre"},
        "image_url": "https://cdn.guruwalk.com/img/tour-789.jpg",
        "events": [
            {
                "start_time": "2025-08-10T09:00:00Z",
                "available_spots": 12,
                "language": "es"
            },
            {
                "start_time": "2025-08-12T09:00:00Z",
                "available_spots": 7,
                "language": "es"
            }
        ]
    },
    {
        "title": "Gourmet & Pintxos Walking Tour",
        "url": "https://www.guruwalk.com/tours/san-sebastian-pintxos-321",
        "meetpoint_address": "Mercado de la Bretxa, Donostia",
        "average_rating": 4.85,
        "duration": 180,
        "guru": {"name": "Joseba Arrizabalaga"},
        "image_url": "https://cdn.guruwalk.com/img/tour-321.jpg",
        "events": [
            {
                "start_time": "2025-08-10T18:00:00Z",
                "available_spots": 6,
                "language": "en"
            },
            {
                "start_time": "2025-08-11T18:00:00Z",
                "available_spots": 0,
                "language": "en"
            },
            {
                "start_time": "2025-08-12T18:00:00Z",
                "available_spots": 4,
                "language": "en"
            }
        ]
    },
    {
        "title": "Fully Booked Tour (should be excluded)",
        "url": "https://www.guruwalk.com/tours/san-sebastian-full-999",
        "meetpoint_address": "Playa de la Concha, Donostia",
        "average_rating": 4.6,
        "duration": 60,
        "guru": {"name": "Miren Iturriaga"},
        "image_url": "https://cdn.guruwalk.com/img/tour-999.jpg",
        "events": [
            {
                "start_time": "2025-08-10T14:00:00Z",
                "available_spots": 0,
                "language": "en"
            }
        ]
    }
]

def make_jsonrpc_response(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

def handle_mcp_message(msg):
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return make_jsonrpc_response(req_id, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "guruwalk-mock", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        })

    elif method == "notifications/initialized":
        return None  # no response for notifications

    elif method == "tools/list":
        return make_jsonrpc_response(req_id, {
            "tools": [{
                "name": "search",
                "description": "Search GuruWalk free tours by city, date range, and language.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "language": {"type": "string"}
                    },
                    "required": ["city", "start_date", "end_date", "language"]
                }
            }]
        })

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        if tool_name == "search":
            city = args.get("city", "")
            # Only return tours for properly slugified city
            if city == "san-sebastian":
                tours_json = json.dumps(TOURS_DATA)
            else:
                tours_json = json.dumps([])
            return make_jsonrpc_response(req_id, {
                "content": [{"type": "text", "text": tours_json}]
            })
        else:
            return make_jsonrpc_response(req_id, {
                "content": [{"type": "text", "text": json.dumps([])}]
            })

    else:
        return make_jsonrpc_response(req_id, {"error": f"Unknown method: {method}"})


@app.route("/mcp", methods=["GET", "POST"])
def mcp_endpoint():
    # Support both single JSON-RPC and batch
    if request.method == "POST":
        data = request.get_json(force=True, silent=True)
        if data is None:
            return Response(json.dumps({"error": "bad request"}), status=400,
                            content_type="application/json")

        if isinstance(data, list):
            responses = []
            for msg in data:
                r = handle_mcp_message(msg)
                if r is not None:
                    responses.append(r)
            return Response(json.dumps(responses), content_type="application/json")
        else:
            r = handle_mcp_message(data)
            if r is None:
                return Response("", status=204)
            return Response(json.dumps(r), content_type="application/json")

    # GET: return server info
    return Response(json.dumps({"server": "guruwalk-mock", "status": "ok"}),
                    content_type="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
PYEOF

chmod +x /mock_mcp_server.py

# ── Start the mock server in background ──────────────────────────────────────
python3 /mock_mcp_server.py &
SERVER_PID=$!
echo "Mock MCP server started with PID $SERVER_PID on port 8765"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8765/mcp > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i/15)"
    sleep 1
done

# ── Write MCP server URL override hint into env ───────────────────────────────
echo "GURUWALK_MCP_URL=http://localhost:8765/mcp" >> /etc/environment
export GURUWALK_MCP_URL=http://localhost:8765/mcp

echo "Setup complete. Mock GuruWalk MCP server running at http://localhost:8765/mcp"