#!/bin/bash
set -e

# ── Write the mock Feishu API server ────────────────────────────────────────
cat > /workspace/mock_feishu_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Local mock of a Feishu Document API for evaluation purposes.
Supports:
  GET  /docs/<doc_id>            -> returns document JSON
  POST /docs/<doc_id>/update     -> applies updates to document
  GET  /docs/<doc_id>/url        -> returns document URL
  GET  /docs/<doc_id>/history    -> returns update history
"""

import json
import os
import copy
import sys
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

STATE_DIR = "/workspace/mock_server_state"
HISTORY_FILE = "/workspace/mock_server_state/update_history.json"

os.makedirs(STATE_DIR, exist_ok=True)

def load_doc(doc_id):
    path = os.path.join(STATE_DIR, f"{doc_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_doc(doc_id, doc):
    path = os.path.join(STATE_DIR, f"{doc_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def append_history(entry):
    history = load_history()
    history.append(entry)
    save_history(history)

@app.route("/docs/<doc_id>", methods=["GET"])
def get_doc(doc_id):
    doc = load_doc(doc_id)
    if doc is None:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(doc)

@app.route("/docs/<doc_id>/url", methods=["GET"])
def get_url(doc_id):
    doc = load_doc(doc_id)
    if doc is None:
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"url": doc.get("url", f"http://localhost:8765/docs/{doc_id}")})

@app.route("/docs/<doc_id>/history", methods=["GET"])
def get_history(doc_id):
    history = load_history()
    doc_history = [h for h in history if h.get("doc_id") == doc_id]
    return jsonify({"history": doc_history})

@app.route("/docs", methods=["POST"])
def create_doc():
    """Create a new document."""
    data = request.get_json(force=True)
    doc_id = data.get("document_id")
    title = data.get("title", "Untitled")
    blocks = data.get("blocks", [])

    if not doc_id:
        import uuid
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    doc = {
        "document_id": doc_id,
        "title": title,
        "blocks": blocks,
        "url": f"http://localhost:8765/docs/{doc_id}"
    }
    save_doc(doc_id, doc)
    append_history({
        "doc_id": doc_id,
        "action": "create",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": data
    })
    return jsonify({"document_id": doc_id, "url": doc["url"]}), 201

@app.route("/docs/<doc_id>/update", methods=["POST"])
def update_doc(doc_id):
    """
    Update a document. Supported modes:
      - append:         add blocks at the end
      - insert_before:  insert blocks before a given block_id
      - insert_after:   insert blocks after a given block_id
      - replace_range:  replace blocks from start_block_id to end_block_id
      - replace_all:    replace all blocks
      - delete_range:   delete blocks from start_block_id to end_block_id
      - overwrite:      replace entire document including title (DESTRUCTIVE)
    """
    doc = load_doc(doc_id)
    if doc is None:
        return jsonify({"error": "Document not found"}), 404

    data = request.get_json(force=True)
    mode = data.get("mode")
    new_blocks = data.get("blocks", [])
    
    original_block_count = len(doc["blocks"])
    original_blocks_snapshot = copy.deepcopy(doc["blocks"])

    if mode == "append":
        doc["blocks"].extend(new_blocks)

    elif mode == "insert_before":
        target_id = data.get("target_block_id")
        idx = next((i for i, b in enumerate(doc["blocks"]) if b["block_id"] == target_id), None)
        if idx is None:
            return jsonify({"error": f"block_id {target_id} not found"}), 400
        doc["blocks"] = doc["blocks"][:idx] + new_blocks + doc["blocks"][idx:]

    elif mode == "insert_after":
        target_id = data.get("target_block_id")
        idx = next((i for i, b in enumerate(doc["blocks"]) if b["block_id"] == target_id), None)
        if idx is None:
            return jsonify({"error": f"block_id {target_id} not found"}), 400
        doc["blocks"] = doc["blocks"][:idx+1] + new_blocks + doc["blocks"][idx+1:]

    elif mode == "replace_range":
        start_id = data.get("start_block_id")
        end_id = data.get("end_block_id")
        start_idx = next((i for i, b in enumerate(doc["blocks"]) if b["block_id"] == start_id), None)
        end_idx = next((i for i, b in enumerate(doc["blocks"]) if b["block_id"] == end_id), None)
        if start_idx is None or end_idx is None:
            return jsonify({"error": "block_id not found"}), 400
        doc["blocks"] = doc["blocks"][:start_idx] + new_blocks + doc["blocks"][end_idx+1:]

    elif mode == "replace_all":
        doc["blocks"] = new_blocks

    elif mode == "delete_range":
        start_id = data.get("start_block_id")
        end_id = data.get("end_block_id")
        start_idx = next((i for i, b in enumerate(doc["blocks"]) if b["block_id"] == start_id), None)
        end_idx = next((i for i, b in enumerate(doc["blocks"]) if b["block_id"] == end_id), None)
        if start_idx is None or end_idx is None:
            return jsonify({"error": "block_id not found"}), 400
        doc["blocks"] = doc["blocks"][:start_idx] + doc["blocks"][end_idx+1:]

    elif mode == "overwrite":
        # DESTRUCTIVE: replaces title AND all blocks
        if "title" in data:
            doc["title"] = data["title"]
        doc["blocks"] = new_blocks

    else:
        return jsonify({"error": f"Unknown mode: {mode}. Valid modes: append, insert_before, insert_after, replace_range, replace_all, delete_range, overwrite"}), 400

    save_doc(doc_id, doc)
    append_history({
        "doc_id": doc_id,
        "action": "update",
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat(),
        "blocks_before": original_block_count,
        "blocks_after": len(doc["blocks"]),
        "payload": data
    })

    return jsonify({
        "success": True,
        "mode": mode,
        "blocks_before": original_block_count,
        "blocks_after": len(doc["blocks"]),
        "url": doc.get("url")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
PYEOF

chmod +x /workspace/mock_feishu_server.py

# Start the mock server in background
python3 /workspace/mock_feishu_server.py &
SERVER_PID=$!
echo "Mock Feishu server started with PID $SERVER_PID on port 8765"

# Wait for server to be ready
sleep 2
curl -s http://localhost:8765/docs/doc_onboarding_2024 > /dev/null && echo "Server is ready." || echo "Server may not be ready yet."

# Save PID for potential cleanup
echo $SERVER_PID > /workspace/.server_pid