#!/bin/bash
set -e

WORKSPACE="/workspace"
SKILL_BASE="$WORKSPACE/skills/aria2-json-rpc"
SCRIPTS_DIR="$SKILL_BASE/scripts"
EXAMPLES_DIR="$SCRIPTS_DIR/examples"
REFS_DIR="$SKILL_BASE/references"

# ── Write the mock aria2 RPC server ──────────────────────────────────────────
cat > "$WORKSPACE/mock_aria2_server.py" << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock aria2 JSON-RPC server.
Reads/writes state from /workspace/mock_aria2_state.json
Supports: addUri, tellStatus, tellActive, tellWaiting, tellStopped,
          pause, unpause, remove, removeDownloadResult, purgeDownloadResult,
          changeOption, getOption, getGlobalOption, changeGlobalOption,
          getGlobalStat, getVersion, pauseAll, unpauseAll, system.listMethods
"""
import json
import sys
import os
import random
import string
from flask import Flask, request, jsonify

STATE_FILE = "/workspace/mock_aria2_state.json"
app = Flask(__name__)

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def gen_gid():
    return ''.join(random.choices('0123456789abcdef', k=16))

def strip_token(params):
    """Remove auth token from params if present."""
    if params and isinstance(params[0], str) and params[0].startswith("token:"):
        return params[1:]
    return params

def handle_method(method, params):
    state = load_state()
    params = strip_token(params or [])

    if method == "aria2.getVersion":
        return state["version"]

    elif method == "system.listMethods":
        return ["aria2.addUri","aria2.addTorrent","aria2.addMetalink","aria2.remove",
                "aria2.pause","aria2.pauseAll","aria2.unpause","aria2.unpauseAll",
                "aria2.tellStatus","aria2.tellActive","aria2.tellWaiting","aria2.tellStopped",
                "aria2.getGlobalStat","aria2.getOption","aria2.changeOption",
                "aria2.getGlobalOption","aria2.changeGlobalOption",
                "aria2.purgeDownloadResult","aria2.removeDownloadResult","system.listMethods",
                "system.multicall"]

    elif method == "aria2.getGlobalStat":
        downloads = state["downloads"]
        num_active = sum(1 for d in downloads.values() if d["status"] == "active")
        num_waiting = sum(1 for d in downloads.values() if d["status"] in ("waiting","paused"))
        num_stopped = sum(1 for d in downloads.values() if d["status"] in ("complete","error","removed"))
        return {
            "downloadSpeed": state["global_stat"]["downloadSpeed"],
            "uploadSpeed": "0",
            "numActive": str(num_active),
            "numWaiting": str(num_waiting),
            "numStopped": str(num_stopped),
            "numStoppedTotal": str(num_stopped)
        }

    elif method == "aria2.addUri":
        # params[0] = [url, ...], params[1] = options (optional)
        uris = params[0]
        options = params[1] if len(params) > 1 and isinstance(params[1], dict) else {}
        gid = gen_gid()
        state["downloads"][gid] = {
            "gid": gid,
            "status": "active",
            "totalLength": "1073741824",
            "completedLength": "0",
            "downloadSpeed": "1048576",
            "uploadSpeed": "0",
            "files": [{"path": f"/downloads/{uris[0].split('/')[-1]}", "length": "1073741824", "selected": "true"}],
            "errorCode": "0",
            "errorMessage": ""
        }
        state["options"][gid] = {"max-download-limit": "0", "max-upload-limit": "0", "split": "5"}
        # apply options if given
        if options:
            for k, v in options.items():
                state["options"][gid][k] = str(v)
        save_state(state)
        return gid

    elif method == "aria2.tellStatus":
        gid = params[0]
        if gid not in state["downloads"]:
            raise ValueError(f"GID not found: {gid}")
        dl = dict(state["downloads"][gid])
        if len(params) > 1 and isinstance(params[1], list):
            return {k: dl[k] for k in params[1] if k in dl}
        return dl

    elif method == "aria2.tellActive":
        keys = params[0] if params and isinstance(params[0], list) else None
        result = []
        for dl in state["downloads"].values():
            if dl["status"] == "active":
                if keys:
                    result.append({k: dl[k] for k in keys if k in dl})
                else:
                    result.append(dict(dl))
        return result

    elif method == "aria2.tellWaiting":
        offset = params[0] if len(params) > 0 else 0
        num = params[1] if len(params) > 1 else 100
        keys = params[2] if len(params) > 2 and isinstance(params[2], list) else None
        waiting = [dl for dl in state["downloads"].values() if dl["status"] in ("waiting","paused")]
        # Handle negative offset
        if offset < 0:
            waiting = waiting[max(0, len(waiting)+offset):]
        else:
            waiting = waiting[offset:offset+num]
        if keys:
            return [{k: d[k] for k in keys if k in d} for d in waiting]
        return [dict(d) for d in waiting]

    elif method == "aria2.tellStopped":
        offset = params[0] if len(params) > 0 else 0
        num = params[1] if len(params) > 1 else 100
        keys = params[2] if len(params) > 2 and isinstance(params[2], list) else None
        stopped = [dl for dl in state["downloads"].values() if dl["status"] in ("complete","error","removed")]
        if offset < 0:
            stopped = stopped[max(0, len(stopped)+offset):]
        else:
            stopped = stopped[offset:offset+num]
        if keys:
            return [{k: d[k] for k in keys if k in d} for d in stopped]
        return [dict(d) for d in stopped]

    elif method == "aria2.pause":
        gid = params[0]
        if gid not in state["downloads"]:
            raise ValueError(f"GID not found: {gid}")
        if state["downloads"][gid]["status"] != "active":
            raise ValueError(f"Download is not active: {gid}")
        state["downloads"][gid]["status"] = "paused"
        state["downloads"][gid]["downloadSpeed"] = "0"
        save_state(state)
        return gid

    elif method == "aria2.pauseAll":
        for dl in state["downloads"].values():
            if dl["status"] == "active":
                dl["status"] = "paused"
                dl["downloadSpeed"] = "0"
        save_state(state)
        return "OK"

    elif method == "aria2.unpause":
        gid = params[0]
        if gid not in state["downloads"]:
            raise ValueError(f"GID not found: {gid}")
        if state["downloads"][gid]["status"] != "paused":
            raise ValueError(f"Download is not paused: {gid}")
        state["downloads"][gid]["status"] = "active"
        save_state(state)
        return gid

    elif method == "aria2.unpauseAll":
        for dl in state["downloads"].values():
            if dl["status"] == "paused":
                dl["status"] = "active"
        save_state(state)
        return "OK"

    elif method == "aria2.remove":
        gid = params[0]
        if gid not in state["downloads"]:
            raise ValueError(f"GID not found: {gid}")
        status = state["downloads"][gid]["status"]
        if status in ("complete", "error", "removed"):
            raise ValueError({"code": 1, "message": f"GID#{gid} cannot be removed. Use removeDownloadResult for stopped/complete downloads."})
        state["downloads"][gid]["status"] = "removed"
        save_state(state)
        return gid

    elif method == "aria2.removeDownloadResult":
        gid = params[0]
        if gid not in state["downloads"]:
            raise ValueError(f"GID not found: {gid}")
        status = state["downloads"][gid]["status"]
        if status not in ("complete", "error", "removed"):
            raise ValueError(f"GID#{gid} is not stopped. Status: {status}")
        state["removed_results"].append(gid)
        del state["downloads"][gid]
        save_state(state)
        return "OK"

    elif method == "aria2.purgeDownloadResult":
        to_remove = [gid for gid, dl in state["downloads"].items() 
                     if dl["status"] in ("complete", "error", "removed")]
        for gid in to_remove:
            state["removed_results"].append(gid)
            del state["downloads"][gid]
        save_state(state)
        return "OK"

    elif method == "aria2.getOption":
        gid = params[0]
        return state["options"].get(gid, {})

    elif method == "aria2.changeOption":
        gid = params[0]
        options = params[1]
        if gid not in state["downloads"]:
            raise ValueError(f"GID not found: {gid}")
        if gid not in state["options"]:
            state["options"][gid] = {}
        for k, v in options.items():
            state["options"][gid][k] = str(v)
        save_state(state)
        return "OK"

    elif method == "aria2.getGlobalOption":
        return state["global_options"]

    elif method == "aria2.changeGlobalOption":
        options = params[0]
        for k, v in options.items():
            state["global_options"][k] = str(v)
        save_state(state)
        return "OK"

    else:
        raise ValueError(f"Unknown method: {method}")

@app.route("/jsonrpc", methods=["POST"])
def jsonrpc():
    req = request.get_json()
    method = req.get("method")
    params = req.get("params", [])
    req_id = req.get("id")
    try:
        result = handle_method(method, params)
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": result})
    except Exception as e:
        msg = str(e)
        return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": 1, "message": msg}})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6800, debug=False)
MOCK_SERVER_EOF

chmod +x "$WORKSPACE/mock_aria2_server.py"

# ── Write the config_loader.py script ────────────────────────────────────────
cat > "$SCRIPTS_DIR/config_loader.py" << 'CONFIG_EOF'
#!/usr/bin/env python3
"""
Configuration loader for aria2-json-rpc skill.
Loads config from environment variables, skill directory config.json, user config, or defaults.
"""
import os
import json
import sys
import urllib.request
import urllib.error

DEFAULTS = {
    "host": "localhost",
    "port": 6800,
    "path": "/jsonrpc",
    "secret": None,
    "secure": False,
    "timeout": 30000
}

class Aria2Config:
    def __init__(self):
        self._config = None

    def load(self):
        config = dict(DEFAULTS)

        # Priority 3: User config
        user_config_path = os.path.expanduser("~/.config/aria2-skill/config.json")
        if os.path.isfile(user_config_path):
            try:
                with open(user_config_path) as f:
                    user_cfg = json.load(f)
                config.update(user_cfg)
            except Exception:
                pass

        # Priority 2: Skill directory config
        skill_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        if os.path.isfile(skill_config_path):
            try:
                with open(skill_config_path) as f:
                    skill_cfg = json.load(f)
                config.update(skill_cfg)
            except Exception:
                pass

        # Priority 1: Environment variables (highest)
        if os.environ.get("ARIA2_RPC_HOST"):
            config["host"] = os.environ["ARIA2_RPC_HOST"]
        if os.environ.get("ARIA2_RPC_PORT"):
            config["port"] = int(os.environ["ARIA2_RPC_PORT"])
        if os.environ.get("ARIA2_RPC_PATH"):
            config["path"] = os.environ["ARIA2_RPC_PATH"]
        if os.environ.get("ARIA2_RPC_SECRET"):
            config["secret"] = os.environ["ARIA2_RPC_SECRET"]
        if os.environ.get("ARIA2_RPC_SECURE"):
            config["secure"] = os.environ["ARIA2_RPC_SECURE"].lower() == "true"

        self._config = config
        return config

    def get_endpoint_url(self):
        if not self._config:
            self.load()
        c = self._config
        protocol = "https" if c.get("secure") else "http"
        path = c.get("path") or ""
        return f"{protocol}://{c['host']}:{c['port']}{path}"

    def init(self, scope="user"):
        if scope == "user":
            config_dir = os.path.expanduser("~/.config/aria2-skill")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "config.json")
        else:
            skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(skill_dir, "config.json")

        default_config = {
            "host": "localhost",
            "port": 6800,
            "path": "/jsonrpc",
            "secret": None,
            "secure": False,
            "timeout": 30000
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2)
        print(f"Config initialized at: {config_path}")
        return config_path

    def show(self):
        config = self.load()
        print("Current configuration:")
        for k, v in config.items():
            if k == "secret" and v:
                print(f"  {k}: ******")
            else:
                print(f"  {k}: {v}")
        print(f"Endpoint: {self.get_endpoint_url()}")

    def test(self):
        config = self.load()
        endpoint = self.get_endpoint_url()
        print(f"Testing connection to {endpoint}...")
        try:
            payload = json.dumps({"jsonrpc":"2.0","id":"test","method":"aria2.getVersion","params":[]}).encode()
            req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type":"application/json"})
            resp = urllib.request.urlopen(req, timeout=config.get("timeout",30000)/1000.0)
            data = json.loads(resp.read())
            if "result" in data:
                print(f"✓ Connection successful! aria2 version: {data['result'].get('version','?')}")
                return True
            else:
                print(f"✗ Connection failed: {data.get('error','Unknown error')}")
                return False
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

def main():
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("show")
    subparsers.add_parser("test")
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--user", action="store_true")
    init_parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    loader = Aria2Config()
    if args.command == "show":
        loader.show()
    elif args.command == "test":
        success = loader.test()
        sys.exit(0 if success else 1)
    elif args.command == "init":
        scope = "user" if args.user else "local"
        loader.init(scope)
    else:
        loader.show()

if __name__ == "__main__":
    main()
CONFIG_EOF

chmod +x "$SCRIPTS_DIR/config_loader.py"

# ── Write rpc_client.py ───────────────────────────────────────────────────────
# (Already provided in SKILL.md content; copy it verbatim)
cat > "$SCRIPTS_DIR/rpc_client.py" << 'RPC_EOF'
#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import sys
import time
import base64
import os
from typing import Any, Dict, List, Optional, Union

class Aria2RpcError(Exception):
    def __init__(self, code, message, data=None, request_id=None):
        self.code = code
        self.message = message
        self.data = data
        self.request_id = request_id
        super().__init__(f"aria2 RPC error [{code}]: {message}")

class Aria2RpcClient:
    def __init__(self, config):
        self.config = config
        self.request_counter = 0
        self.endpoint_url = self._build_endpoint_url()

    def _build_endpoint_url(self):
        protocol = "https" if self.config.get("secure", False) else "http"
        host = self.config["host"]
        port = self.config["port"]
        path = self.config.get("path") or ""
        return f"{protocol}://{host}:{port}{path}"

    def _generate_request_id(self):
        self.request_counter += 1
        return f"aria2-rpc-{self.request_counter}"

    def _inject_token(self, params):
        secret = self.config.get("secret")
        if secret:
            return [f"token:{secret}"] + params
        return params

    def _format_request(self, method, params=None):
        if params is None:
            params = []
        if method.startswith("aria2."):
            params = self._inject_token(params)
        return {"jsonrpc": "2.0", "id": self._generate_request_id(), "method": method, "params": params}

    def _send_request(self, request):
        request_data = json.dumps(request).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url, data=request_data,
            headers={"Content-Type": "application/json", "User-Agent": "aria2-json-rpc-client/1.0"})
        timeout_sec = self.config.get("timeout", 30000) / 1000.0
        try:
            response = urllib.request.urlopen(req, timeout=timeout_sec)
            return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode("utf-8"))
            except:
                raise Exception(f"HTTP error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise Exception(f"Network error: {e.reason}")

    def _parse_response(self, response, request_id):
        if not isinstance(response, dict):
            raise Exception("Invalid JSON-RPC response")
        if "error" in response:
            error = response["error"]
            raise Aria2RpcError(code=error.get("code",-1), message=error.get("message","Unknown"), data=error.get("data"), request_id=request_id)
        if "result" not in response:
            raise Exception("Invalid JSON-RPC response: missing result")
        return response["result"]

    def call(self, method, params=None):
        request = self._format_request(method, params)
        request_id = request["id"]
        response = self._send_request(request)
        return self._parse_response(response, request_id)

    def add_uri(self, uris, options=None, position=None):
        if isinstance(uris, str): uris = [uris]
        params = [uris]
        if options: params.append(options)
        if position is not None: params.append(position)
        return self.call("aria2.addUri", params)

    def tell_status(self, gid, keys=None):
        params = [gid]
        if keys: params.append(keys)
        return self.call("aria2.tellStatus", params)

    def tell_active(self, keys=None):
        params = []
        if keys: params.append(keys)
        return self.call("aria2.tellActive", params)

    def tell_waiting(self, offset=0, num=100, keys=None):
        params = [offset, num]
        if keys: params.append(keys)
        return self.call("aria2.tellWaiting", params)

    def tell_stopped(self, offset=0, num=100, keys=None):
        params = [offset, num]
        if keys: params.append(keys)
        return self.call("aria2.tellStopped", params)

    def pause(self, gid): return self.call("aria2.pause", [gid])
    def pause_all(self): return self.call("aria2.pauseAll", [])
    def unpause(self, gid): return self.call("aria2.unpause", [gid])
    def unpause_all(self): return self.call("aria2.unpauseAll", [])
    def remove(self, gid): return self.call("aria2.remove", [gid])
    def remove_download_result(self, gid): return self.call("aria2.removeDownloadResult", [gid])
    def purge_download_result(self): return self.call("aria2.purgeDownloadResult", [])
    def get_option(self, gid): return self.call("aria2.getOption", [gid])
    def change_option(self, gid, options): return self.call("aria2.changeOption", [gid, options])
    def get_global_option(self): return self.call("aria2.getGlobalOption", [])
    def change_global_option(self, options): return self.call("aria2.changeGlobalOption", [options])
    def get_global_stat(self): return self.call("aria2.getGlobalStat", [])
    def get_version(self): return self.call("aria2.getVersion", [])
    def list_methods(self): return self.call("system.listMethods", [])
    def purge_download_result(self): return self.call("aria2.purgeDownloadResult", [])

    def add_torrent(self, torrent, uris=None, options=None, position=None):
        if isinstance(torrent, str) and os.path.isfile(torrent):
            with open(torrent, "rb") as f:
                torrent = base64.b64encode(f.read()).decode("utf-8")
        elif isinstance(torrent, bytes):
            torrent = base64.b64encode(torrent).decode("utf-8")
        params = [torrent]
        if uris: params.append(uris)
        elif options or position is not None: params.append([])
        if options: params.append(options)
        elif position is not None: params.append({})
        if position is not None: params.append(position)
        return self.call("aria2.addTorrent", params)

    def multicall(self, calls):
        return self.call("system.multicall", [calls])

def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config_loader import Aria2Config
    try:
        config_loader = Aria2Config()
        config = config_loader.load()
        client = Aria2RpcClient(config)
        if len(sys.argv) == 1:
            print("Testing aria2 JSON-RPC client...")
            stats = client.get_global_stat()
            print("✓ Connection successful")
            print(json.dumps(stats, indent=2))
        else:
            method = sys.argv[1]
            params = []
            for arg in sys.argv[2:]:
                try: params.append(json.loads(arg))
                except json.JSONDecodeError:
                    try: params.append(int(arg))
                    except ValueError: params.append(arg)
            result = client.call(method, params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except Aria2RpcError as e:
        print(f"aria2 error [{e.code}]: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
RPC_EOF

chmod +x "$SCRIPTS_DIR/rpc_client.py"

# ── Write stub example scripts ────────────────────────────────────────────────
for script in list-downloads.py pause-all.py add-torrent.py monitor-downloads.py set-options.py; do
    if [ ! -f "$EXAMPLES_DIR/$script" ]; then
        echo "#!/usr/bin/env python3" > "$EXAMPLES_DIR/$script"
        echo "print('stub')" >> "$EXAMPLES_DIR/$script"
        chmod +x "$EXAMPLES_DIR/$script"
    fi
done

# ── Write SKILL.md reference files ───────────────────────────────────────────
mkdir -p "$REFS_DIR"
cat > "$REFS_DIR/execution-guide.md" << 'GUIDE_EOF'
# Execution Guide for AI Agents

ALWAYS use python3 scripts, never raw curl.
Use config_loader.py test before any command.

Command Mapping:
- Download: python3 scripts/rpc_client.py aria2.addUri '["URL"]'
- Status: python3 scripts/rpc_client.py aria2.tellStatus GID
- Active: python3 scripts/rpc_client.py aria2.tellActive
- Stopped: python3 scripts/rpc_client.py aria2.tellStopped 0 100
- Pause: python3 scripts/rpc_client.py aria2.pause GID
- Unpause: python3 scripts/rpc_client.py aria2.unpause GID
- Remove active: python3 scripts/rpc_client.py aria2.remove GID
- Remove completed: python3 scripts/rpc_client.py aria2.removeDownloadResult GID
- Change option: python3 scripts/rpc_client.py aria2.changeOption GID '{"max-download-limit":"512000"}'
- Purge: python3 scripts/rpc_client.py aria2.purgeDownloadResult
GUIDE_EOF

# ── Set environment variables for the mock server ─────────────────────────────
export ARIA2_RPC_HOST=localhost
export ARIA2_RPC_PORT=6800
export ARIA2_RPC_PATH=/jsonrpc

# ── Start the mock aria2 server in the background ────────────────────────────
cd "$WORKSPACE"
python3 mock_aria2_server.py &
SERVER_PID=$!
echo "Mock aria2 server started with PID $SERVER_PID"

# Wait for server to be ready
for i in $(seq 1 20); do
    if curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:6800/jsonrpc \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":"ping","method":"aria2.getVersion","params":[]}' | grep -q "200"; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

echo "Setup complete. Workspace at $WORKSPACE"
echo "Skill at $SKILL_BASE"