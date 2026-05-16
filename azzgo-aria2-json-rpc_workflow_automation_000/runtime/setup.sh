#!/bin/bash
set -e

# ── Make scripts executable ──────────────────────────────────────────────────
chmod +x /workspace/skills/aria2-json-rpc/scripts/rpc_client.py
chmod +x /workspace/skills/aria2-json-rpc/scripts/config_loader.py
chmod +x /workspace/skills/aria2-json-rpc/scripts/examples/*.py

# ── Start mock aria2 RPC server on port 7600 ─────────────────────────────────
cat > /tmp/mock_aria2_server.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""
Mock aria2 JSON-RPC server for evaluation.
Runs on port 7600. Tracks state across requests.
"""
import json
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Shared state
lock = threading.Lock()
downloads = {}          # gid -> download dict
purged_gids = []        # gids removed by purgeDownloadResult
option_changes = {}     # gid -> options dict from changeOption calls
global_option_changes = {}  # options from changeGlobalOption calls

VALID_METHODS = [
    "aria2.addUri", "aria2.addTorrent", "aria2.addMetalink",
    "aria2.remove", "aria2.pause", "aria2.pauseAll",
    "aria2.unpause", "aria2.unpauseAll",
    "aria2.tellStatus", "aria2.tellActive", "aria2.tellWaiting", "aria2.tellStopped",
    "aria2.getGlobalStat", "aria2.getOption", "aria2.changeOption",
    "aria2.getGlobalOption", "aria2.changeGlobalOption",
    "aria2.purgeDownloadResult", "aria2.removeDownloadResult",
    "aria2.getVersion", "system.listMethods", "system.multicall",
]

def make_gid():
    return uuid.uuid4().hex[:16]

def handle_method(method, params):
    global downloads, purged_gids, option_changes, global_option_changes

    # Strip token from params for aria2.* methods
    if method.startswith("aria2.") and params and isinstance(params[0], str) and params[0].startswith("token:"):
        params = params[1:]

    with lock:
        if method == "aria2.getVersion":
            return {"version": "1.36.0", "enabledFeatures": ["BitTorrent", "Metalink", "Async DNS"]}

        elif method == "system.listMethods":
            return VALID_METHODS

        elif method == "aria2.addUri":
            # params[0] = list of URIs, params[1] = options (optional)
            uris = params[0] if params else []
            options = params[1] if len(params) > 1 else {}
            gid = make_gid()
            uri = uris[0] if uris else "unknown"
            import os
            filename = os.path.basename(uri.split("?")[0]) or "file"
            downloads[gid] = {
                "gid": gid,
                "status": "complete",   # Simulate already completed
                "uris": uris,
                "filename": filename,
                "totalLength": "104857600",
                "completedLength": "104857600",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [{"path": f"/downloads/{filename}", "length": "104857600", "selected": "true"}],
                "errorCode": None,
                "errorMessage": None,
                "options": options,
            }
            return gid

        elif method == "aria2.tellStatus":
            gid = params[0] if params else None
            if gid in purged_gids:
                return {"error": {"code": 1, "message": "GID not found"}}
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            dl = dict(downloads[gid])
            # Merge option_changes
            if gid in option_changes:
                dl["options"] = {**dl.get("options", {}), **option_changes[gid]}
            return dl

        elif method == "aria2.tellActive":
            keys = params[0] if params else None
            result = []
            for gid, dl in downloads.items():
                if dl["status"] == "active" and gid not in purged_gids:
                    d = dict(dl)
                    if keys:
                        d = {k: d[k] for k in keys if k in d}
                    result.append(d)
            return result

        elif method == "aria2.tellWaiting":
            offset = params[0] if len(params) > 0 else 0
            num = params[1] if len(params) > 1 else 100
            result = []
            for gid, dl in downloads.items():
                if dl["status"] == "waiting" and gid not in purged_gids:
                    result.append(dict(dl))
            return result[offset:offset+num] if offset >= 0 else result[offset:]

        elif method == "aria2.tellStopped":
            offset = params[0] if len(params) > 0 else 0
            num = params[1] if len(params) > 1 else 100
            result = []
            for gid, dl in downloads.items():
                if dl["status"] in ("complete", "error", "removed") and gid not in purged_gids:
                    result.append(dict(dl))
            if offset < 0:
                return result[offset:][:num]
            return result[offset:offset+num]

        elif method == "aria2.getGlobalStat":
            active = sum(1 for d in downloads.values() if d["status"] == "active" and d["gid"] not in purged_gids)
            waiting = sum(1 for d in downloads.values() if d["status"] == "waiting" and d["gid"] not in purged_gids)
            stopped = sum(1 for d in downloads.values() if d["status"] in ("complete","error","removed") and d["gid"] not in purged_gids)
            return {
                "numActive": str(active),
                "numWaiting": str(waiting),
                "numStopped": str(stopped),
                "downloadSpeed": "0",
                "uploadSpeed": "0",
            }

        elif method == "aria2.changeOption":
            gid = params[0]
            options = params[1] if len(params) > 1 else {}
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            # Store the option changes
            if gid not in option_changes:
                option_changes[gid] = {}
            option_changes[gid].update(options)
            # Also update on download itself for easy access
            downloads[gid].setdefault("options", {}).update(options)
            return "OK"

        elif method == "aria2.changeGlobalOption":
            options = params[0] if params else {}
            global_option_changes.update(options)
            return "OK"

        elif method == "aria2.getOption":
            gid = params[0]
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            dl = downloads[gid]
            opts = dict(dl.get("options", {}))
            if gid in option_changes:
                opts.update(option_changes[gid])
            return opts

        elif method == "aria2.getGlobalOption":
            return dict(global_option_changes)

        elif method == "aria2.purgeDownloadResult":
            to_purge = [gid for gid, dl in downloads.items()
                        if dl["status"] in ("complete", "error", "removed")]
            for gid in to_purge:
                purged_gids.append(gid)
            return "OK"

        elif method == "aria2.removeDownloadResult":
            gid = params[0]
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            if downloads[gid]["status"] not in ("complete", "error", "removed"):
                raise Exception("Download not in stopped state")
            purged_gids.append(gid)
            return "OK"

        elif method == "aria2.pause":
            gid = params[0]
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            downloads[gid]["status"] = "paused"
            return gid

        elif method == "aria2.pauseAll":
            for dl in downloads.values():
                if dl["status"] == "active":
                    dl["status"] = "paused"
            return "OK"

        elif method == "aria2.unpause":
            gid = params[0]
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            downloads[gid]["status"] = "active"
            return gid

        elif method == "aria2.unpauseAll":
            for dl in downloads.values():
                if dl["status"] == "paused":
                    dl["status"] = "active"
            return "OK"

        elif method == "aria2.remove":
            gid = params[0]
            if gid not in downloads:
                raise Exception(f"GID {gid} not found")
            if downloads[gid]["status"] in ("complete", "error", "removed"):
                raise Exception("Download is already stopped; use removeDownloadResult")
            downloads[gid]["status"] = "removed"
            return gid

        elif method == "system.multicall":
            calls = params[0] if params else []
            results = []
            for call in calls:
                mname = call.get("methodName")
                mparams = call.get("params", [])
                try:
                    r = handle_method(mname, mparams)
                    results.append([r])
                except Exception as e:
                    results.append({"faultCode": -1, "faultString": str(e)})
            return results

        else:
            raise Exception(f"Unknown method: {method}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress access logs

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", [])
            try:
                result = handle_method(method, params)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except Exception as e:
                response = {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -1, "message": str(e)}}
        except Exception as e:
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": f"Parse error: {e}"}}

        body_out = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_out)))
        self.end_headers()
        self.wfile.write(body_out)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"mock aria2 server running"}')


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 7600), Handler)
    print("Mock aria2 RPC server listening on port 7600", flush=True)
    server.serve_forever()
MOCK_EOF

python3 /tmp/mock_aria2_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 10); do
    if curl -s -X POST http://localhost:7600 \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":"ping","method":"aria2.getVersion","params":[]}' \
        | grep -q "version"; then
        echo "Mock server ready."
        break
    fi
    sleep 0.5
done

# Set the environment variable so skill scripts point to correct port
# (agent should discover this from task_brief.json or config the skill correctly)
export ARIA2_RPC_PORT=7600

# Update the skill's local config.json to point to port 7600
python3 -c "
import json
cfg_path = '/workspace/skills/aria2-json-rpc/config.json'
with open(cfg_path) as f:
    cfg = json.load(f)
cfg['port'] = 7600
with open(cfg_path, 'w') as f:
    json.dump(cfg, f, indent=2)
print('Updated config.json to port 7600')
"

echo "Setup complete. Workspace ready."