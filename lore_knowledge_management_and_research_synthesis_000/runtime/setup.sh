#!/bin/bash
set -e

# Write the mock Lore MCP server
cat > /mock_lore_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock Lore MCP server — records all tool calls to /tmp/lore_calls.jsonl
Implements: ingest, search, retain, research, get_source
"""
import json
import time
import hashlib
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

CALLS_LOG = "/tmp/lore_calls.jsonl"
INGESTED = {}  # hash -> record
RETAINED = []

def log_call(tool: str, payload: dict, response: dict):
    with open(CALLS_LOG, "a") as f:
        f.write(json.dumps({
            "tool": tool,
            "payload": payload,
            "response": response,
            "ts": time.time()
        }) + "\n")

@app.post("/tools/ingest")
async def ingest(request: Request):
    body = await request.json()
    # Validate required fields
    missing = [f for f in ["content", "title", "project", "source_url", "source_name"] if not body.get(f)]
    if missing:
        resp = {"error": f"Missing required fields: {missing}", "success": False}
        log_call("ingest", body, resp)
        raise HTTPException(status_code=400, detail=resp)
    
    content_hash = hashlib.sha256(body["content"].encode()).hexdigest()[:16]
    if content_hash in INGESTED:
        resp = {"success": True, "deduplicated": True, "source_id": INGESTED[content_hash]["source_id"]}
    else:
        source_id = f"src_{len(INGESTED)+1:04d}"
        INGESTED[content_hash] = {
            "source_id": source_id,
            "title": body["title"],
            "project": body["project"],
            "source_url": body["source_url"],
            "source_name": body["source_name"],
            "source_type": body.get("source_type", "document"),
            "participants": body.get("participants", []),
            "content": body["content"]
        }
        resp = {"success": True, "deduplicated": False, "source_id": source_id}
    
    log_call("ingest", body, resp)
    return JSONResponse(resp)

@app.post("/tools/retain")
async def retain(request: Request):
    body = await request.json()
    missing = [f for f in ["content", "project"] if not body.get(f)]
    if missing:
        resp = {"error": f"Missing required fields: {missing}", "success": False}
        log_call("retain", body, resp)
        raise HTTPException(status_code=400, detail=resp)
    
    retain_id = f"ret_{len(RETAINED)+1:04d}"
    RETAINED.append({
        "retain_id": retain_id,
        "content": body["content"],
        "project": body["project"],
        "tags": body.get("tags", [])
    })
    resp = {"success": True, "retain_id": retain_id}
    log_call("retain", body, resp)
    return JSONResponse(resp)

@app.post("/tools/search")
async def search(request: Request):
    body = await request.json()
    query = body.get("query", "")
    mode = body.get("mode", "hybrid")
    project = body.get("project", "")
    
    # Return mock search results based on what's been ingested
    results = []
    for h, doc in INGESTED.items():
        if project and doc["project"] != project:
            continue
        results.append({
            "source_id": doc["source_id"],
            "title": doc["title"],
            "snippet": doc["content"][:200],
            "score": 0.85
        })
    
    resp = {"success": True, "query": query, "mode": mode, "results": results[:5]}
    log_call("search", body, resp)
    return JSONResponse(resp)

@app.post("/tools/research")
async def research(request: Request):
    body = await request.json()
    resp = {
        "success": True,
        "synthesis": "Users consistently report confusion during initial onboarding, particularly around Workspace vs Project naming and the hidden Getting Started checklist.",
        "sources_consulted": list(INGESTED.keys())[:3]
    }
    log_call("research", body, resp)
    return JSONResponse(resp)

@app.post("/tools/get_source")
async def get_source(request: Request):
    body = await request.json()
    source_id = body.get("source_id")
    include_content = body.get("include_content", False)
    for h, doc in INGESTED.items():
        if doc["source_id"] == source_id:
            result = dict(doc)
            if not include_content:
                result.pop("content", None)
            resp = {"success": True, "document": result}
            log_call("get_source", body, resp)
            return JSONResponse(resp)
    resp = {"error": f"source_id {source_id} not found", "success": False}
    log_call("get_source", body, resp)
    raise HTTPException(status_code=404, detail=resp)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/state")
def state():
    return {"ingested": INGESTED, "retained": RETAINED}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7892, log_level="warning")
PYEOF

python3 /mock_lore_server.py &
SERVER_PID=$!
echo $SERVER_PID > /tmp/mock_lore_server.pid

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:7892/health > /dev/null 2>&1; then
        echo "Mock Lore MCP server is up on port 7892"
        break
    fi
    sleep 1
done

# Write a helper config file the agent can discover
cat > /workspace/lore_mcp_config.json << 'CFEOF'
{
  "lore_mcp_base_url": "http://localhost:7892",
  "tools": {
    "ingest": "POST /tools/ingest",
    "retain": "POST /tools/retain",
    "search": "POST /tools/search",
    "research": "POST /tools/research",
    "get_source": "POST /tools/get_source"
  },
  "project": "acme-onboarding"
}
CFEOF

echo "Setup complete."