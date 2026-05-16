#!/bin/bash
set -e

# Write the mock MCP server
cat > /mock_mcp_server.py << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock MCP Streamable HTTP Server simulating DingTalk Calendar and Contacts APIs.
Implements JSON-RPC 2.0 over HTTP POST.
"""
import json
import time
from flask import Flask, request, Response
import threading

app = Flask(__name__)

# === Mock Data ===
USERS = {
    "Li Wei":    {"userId": "uid_liwei_001",   "name": "Li Wei",   "mobile": "138****0001"},
    "Zhang Min": {"userId": "uid_zhangmin_002", "name": "Zhang Min","mobile": "138****0002"},
    "Liu Yang":  {"userId": "uid_liuyang_003",  "name": "Liu Yang", "mobile": "138****0003"},
    "Chen Fang": {"userId": "uid_chenfang_004", "name": "Chen Fang","mobile": "138****0004"},
}

# 2026-07-14 timestamps (CST = UTC+8)
# 2026-07-14T13:00:00+08:00 = 1752469200000 ms
# 2026-07-14T18:00:00+08:00 = 1752487200000 ms

def ts(h, m=0):
    """Get ms timestamp for 2026-07-14 HH:MM CST"""
    # 2026-07-14T00:00:00+08:00 = 1752422400000
    base = 1752422400000
    return base + h * 3600000 + m * 60000

BUSY_SLOTS = {
    "uid_liwei_001": [
        {"startTime": ts(13, 0), "endTime": ts(14, 0)},
        {"startTime": ts(15, 0), "endTime": ts(16, 0)},
    ],
    "uid_zhangmin_002": [
        {"startTime": ts(13, 0), "endTime": ts(14, 30)},
        {"startTime": ts(16, 0), "endTime": ts(17, 0)},
    ],
}
# Free for BOTH: 14:30-15:00 (30 min), 15:00-16:00 Li Wei busy, so:
# Li Wei free: 14:00-15:00, 16:00+
# Zhang Min free: 14:30-16:00, 17:00+
# Both free: 14:30-15:00 only 30 min...
# Let's re-adjust for a clean 1-hour window:
# Li Wei busy: 13:00-14:00, 15:30-16:30
# Zhang Min busy: 13:00-14:30, 17:00-18:00
# Both free: 14:30-15:30 (1 hour!) ✓

BUSY_SLOTS = {
    "uid_liwei_001": [
        {"startTime": ts(13, 0), "endTime": ts(14, 0)},
        {"startTime": ts(15, 30), "endTime": ts(16, 30)},
    ],
    "uid_zhangmin_002": [
        {"startTime": ts(13, 0), "endTime": ts(14, 30)},
        {"startTime": ts(17, 0), "endTime": ts(18, 0)},
    ],
}

CREATED_EVENTS = {}
event_counter = [1]

CALENDAR_TOOLS = [
    {"name": "create_calendar_event", "description": "Create a calendar event"},
    {"name": "list_calendar_events", "description": "List calendar events"},
    {"name": "query_busy_status", "description": "Query busy status for users"},
    {"name": "query_available_meeting_room", "description": "Query available meeting rooms"},
    {"name": "add_meeting_room", "description": "Add meeting room to event"},
    {"name": "update_calendar_event", "description": "Update calendar event"},
    {"name": "delete_calendar_event", "description": "Delete calendar event"},
]

CONTACTS_TOOLS = [
    {"name": "search_user_by_key_word", "description": "Search user by keyword"},
    {"name": "get_user_info_by_user_ids", "description": "Get user info by user IDs"},
]

def handle_calendar_tool(name, args):
    if name == "list_tools":
        return {"tools": CALENDAR_TOOLS}
    
    elif name == "query_busy_status":
        user_ids = args.get("userIds", [])
        start_time = args.get("startTime")
        end_time = args.get("endTime")
        result = {}
        for uid in user_ids:
            slots = BUSY_SLOTS.get(uid, [])
            relevant = [s for s in slots if s["endTime"] > start_time and s["startTime"] < end_time]
            result[uid] = {"busySlots": relevant}
        return {"busyStatus": result, "success": True}
    
    elif name == "create_calendar_event":
        event_id = f"evt_{event_counter[0]:04d}"
        event_counter[0] += 1
        event = {
            "eventId": event_id,
            "summary": args.get("summary", ""),
            "startDateTime": args.get("startDateTime", ""),
            "endDateTime": args.get("endDateTime", ""),
            "description": args.get("description", ""),
            "attendees": args.get("attendees", []),
            "createdAt": int(time.time() * 1000),
            "status": "confirmed",
        }
        CREATED_EVENTS[event_id] = event
        # Persist to file for eval
        with open("/tmp/created_events.json", "w") as f:
            json.dump(CREATED_EVENTS, f, indent=2)
        return {"event": event, "success": True}
    
    elif name == "list_calendar_events":
        return {"events": list(CREATED_EVENTS.values()), "success": True}
    
    elif name == "update_calendar_event":
        event_id = args.get("eventId")
        if event_id in CREATED_EVENTS:
            for k, v in args.items():
                if k != "eventId":
                    CREATED_EVENTS[event_id][k] = v
            with open("/tmp/created_events.json", "w") as f:
                json.dump(CREATED_EVENTS, f, indent=2)
            return {"event": CREATED_EVENTS[event_id], "success": True}
        return {"error": "Event not found", "success": False}
    
    elif name == "delete_calendar_event":
        event_id = args.get("eventId")
        if event_id in CREATED_EVENTS:
            del CREATED_EVENTS[event_id]
            with open("/tmp/created_events.json", "w") as f:
                json.dump(CREATED_EVENTS, f, indent=2)
        return {"success": True}
    
    elif name == "query_available_meeting_room":
        return {"rooms": [{"roomId": "room_a101", "name": "A101 Conference Room", "capacity": 10}], "success": True}
    
    elif name == "add_meeting_room":
        event_id = args.get("eventId")
        room_ids = args.get("roomIds", [])
        if event_id in CREATED_EVENTS:
            CREATED_EVENTS[event_id]["rooms"] = room_ids
            with open("/tmp/created_events.json", "w") as f:
                json.dump(CREATED_EVENTS, f, indent=2)
            return {"success": True}
        return {"error": "Event not found", "success": False}
    
    return {"error": f"Unknown tool: {name}"}

def handle_contacts_tool(name, args):
    if name == "list_tools":
        return {"tools": CONTACTS_TOOLS}
    
    elif name == "search_user_by_key_word":
        keyword = args.get("keyWord", "")
        results = []
        for username, info in USERS.items():
            if keyword.lower() in username.lower():
                results.append(info)
        return {"users": results, "success": True}
    
    elif name == "get_user_info_by_user_ids":
        user_id_list = args.get("user_id_list", [])
        results = []
        for uid in user_id_list:
            for info in USERS.values():
                if info["userId"] == uid:
                    results.append(info)
        return {"users": results, "success": True}
    
    return {"error": f"Unknown tool: {name}"}

def make_jsonrpc_response(req_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})

def make_jsonrpc_error(req_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})

@app.route("/calendar", methods=["POST", "GET"])
def calendar_endpoint():
    if request.method == "GET":
        # SSE endpoint for MCP initialization
        def sse_stream():
            yield "data: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}\n\n"
        return Response(sse_stream(), mimetype="text/event-stream")
    
    try:
        body = request.get_json(force=True)
        req_id = body.get("id", 1)
        method = body.get("method", "")
        params = body.get("params", {})
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "dingtalk-calendar-mock", "version": "1.0.0"}
            }
            return Response(make_jsonrpc_response(req_id, result), mimetype="application/json")
        
        elif method == "tools/list":
            result = {"tools": CALENDAR_TOOLS}
            return Response(make_jsonrpc_response(req_id, result), mimetype="application/json")
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            tool_result = handle_calendar_tool(tool_name, tool_args)
            result = {"content": [{"type": "text", "text": json.dumps(tool_result)}]}
            return Response(make_jsonrpc_response(req_id, result), mimetype="application/json")
        
        else:
            return Response(make_jsonrpc_error(req_id, -32601, f"Method not found: {method}"), mimetype="application/json")
    
    except Exception as e:
        return Response(make_jsonrpc_error(0, -32700, str(e)), mimetype="application/json", status=500)

@app.route("/contacts", methods=["POST", "GET"])
def contacts_endpoint():
    if request.method == "GET":
        def sse_stream():
            yield "data: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}\n\n"
        return Response(sse_stream(), mimetype="text/event-stream")
    
    try:
        body = request.get_json(force=True)
        req_id = body.get("id", 1)
        method = body.get("method", "")
        params = body.get("params", {})
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "dingtalk-contacts-mock", "version": "1.0.0"}
            }
            return Response(make_jsonrpc_response(req_id, result), mimetype="application/json")
        
        elif method == "tools/list":
            result = {"tools": CONTACTS_TOOLS}
            return Response(make_jsonrpc_response(req_id, result), mimetype="application/json")
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            tool_result = handle_contacts_tool(tool_name, tool_args)
            result = {"content": [{"type": "text", "text": json.dumps(tool_result)}]}
            return Response(make_jsonrpc_response(req_id, result), mimetype="application/json")
        
        else:
            return Response(make_jsonrpc_error(req_id, -32601, f"Method not found: {method}"), mimetype="application/json")
    
    except Exception as e:
        return Response(make_jsonrpc_error(0, -32700, str(e)), mimetype="application/json", status=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18080, debug=False)
MOCK_SERVER_EOF

chmod +x /mock_mcp_server.py

# Start the mock server in the background
python3 /mock_mcp_server.py &
echo "Mock MCP server started (PID=$!)"

# Wait for it to be ready
sleep 3

# Verify it's responding
curl -s -X POST http://localhost:18080/calendar \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Calendar mock OK:', d.get('result',{}).get('serverInfo',{}).get('name','?'))"

curl -s -X POST http://localhost:18080/contacts \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Contacts mock OK:', d.get('result',{}).get('serverInfo',{}).get('name','?'))"

# Configure mcporter to use local mock servers
mcporter config add dingtalk-calendar --url "http://localhost:18080/calendar" 2>/dev/null || true
mcporter config add dingtalk-contacts --url "http://localhost:18080/contacts" 2>/dev/null || true

echo "mcporter configured."
mcporter config list 2>/dev/null || true

# Initialize empty events store
echo "{}" > /tmp/created_events.json

echo "Setup complete. Workspace ready."