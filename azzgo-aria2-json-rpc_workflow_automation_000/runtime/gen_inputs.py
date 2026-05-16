#!/usr/bin/env python3
"""
Generate the workspace for the aria2-json-rpc skill evaluation task.
"""
import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Build the skill directory structure ──────────────────────────────────
skill_root = WORKSPACE / "skills" / "aria2-json-rpc"
scripts_dir = skill_root / "scripts"
examples_dir = scripts_dir / "examples"
refs_dir = skill_root / "references"

for d in [scripts_dir, examples_dir, refs_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── 2. Distractor directory tree ────────────────────────────────────────────
distractor_dirs = [
    WORKSPACE / "media_pipeline" / "ingest",
    WORKSPACE / "media_pipeline" / "transcode" / "hls",
    WORKSPACE / "media_pipeline" / "transcode" / "dash",
    WORKSPACE / "media_pipeline" / "archive",
    WORKSPACE / "media_pipeline" / "logs" / "2024",
    WORKSPACE / "ops" / "configs" / "nginx",
    WORKSPACE / "ops" / "configs" / "cdn",
    WORKSPACE / "ops" / "scripts" / "cron",
    WORKSPACE / "reports" / "weekly",
    WORKSPACE / "reports" / "monthly",
    WORKSPACE / "tmp" / "staging",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    WORKSPACE / "media_pipeline" / "ingest" / "manifest.json": json.dumps({
        "assets": ["movie_4k.mp4", "series_ep01.mp4", "trailer.mp4"],
        "source": "s3://media-bucket/raw",
        "priority": "high"
    }, indent=2),
    WORKSPACE / "media_pipeline" / "transcode" / "hls" / "profile.json": json.dumps({
        "codec": "h264", "bitrates": [1000, 2000, 4000]
    }, indent=2),
    WORKSPACE / "media_pipeline" / "archive" / "retention_policy.txt":
        "Keep completed downloads for 30 days.\nPurge error logs after 7 days.",
    WORKSPACE / "ops" / "configs" / "nginx" / "cdn.conf":
        "upstream aria2_backend { server 127.0.0.1:6800; }",
    WORKSPACE / "ops" / "configs" / "cdn" / "rules.yaml":
        "cache_ttl: 86400\nbandwidth_limit_mbps: 100",
    WORKSPACE / "ops" / "scripts" / "cron" / "cleanup.sh":
        "#!/bin/bash\nfind /tmp -mtime +7 -delete",
    WORKSPACE / "media_pipeline" / "logs" / "2024" / "download_history.log":
        "2024-01-15 10:00 - ubuntu-22.04.iso - COMPLETE\n2024-01-15 11:00 - centos-9.iso - ERROR\n",
    WORKSPACE / "reports" / "weekly" / "bandwidth_usage.csv":
        "date,downloaded_gb,uploaded_gb\n2024-01-15,120,45\n2024-01-16,98,32",
    WORKSPACE / "reports" / "monthly" / "asset_inventory.json": json.dumps({
        "total_assets": 1450, "total_size_tb": 23.4
    }, indent=2),
    WORKSPACE / "tmp" / "staging" / "pending_urls.txt":
        "https://cdn.example.com/episode_s01e01.mp4\nhttps://cdn.example.com/episode_s01e02.mp4\nhttps://cdn.example.com/episode_s01e03.mp4",
    WORKSPACE / "ops" / "configs" / "nginx" / "ratelimit.conf":
        "limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;",
    WORKSPACE / "media_pipeline" / "transcode" / "dash" / "segments.json": json.dumps({
        "segment_duration": 4, "total_segments": 1800
    }, indent=2),
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── 3. Write the actual skill scripts ───────────────────────────────────────

# config_loader.py
config_loader_src = '''#!/usr/bin/env python3
"""Configuration loader for aria2-json-rpc skill."""
import json
import os
import sys
from pathlib import Path


DEFAULTS = {
    "host": "localhost",
    "port": 6800,
    "path": None,
    "secret": None,
    "secure": False,
    "timeout": 30000,
}


class Aria2Config:
    def __init__(self):
        self._config = None

    def load(self):
        config = dict(DEFAULTS)

        # Priority 4: Defaults already set above
        # Priority 3: User config
        user_cfg = Path.home() / ".config" / "aria2-skill" / "config.json"
        if user_cfg.exists():
            try:
                with open(user_cfg) as f:
                    config.update(json.load(f))
            except Exception:
                pass

        # Priority 2: Skill directory config
        skill_cfg = Path(__file__).parent.parent / "config.json"
        if skill_cfg.exists():
            try:
                with open(skill_cfg) as f:
                    config.update(json.load(f))
            except Exception:
                pass

        # Priority 1: Environment variables
        env_map = {
            "ARIA2_RPC_HOST": ("host", str),
            "ARIA2_RPC_PORT": ("port", int),
            "ARIA2_RPC_PATH": ("path", str),
            "ARIA2_RPC_SECRET": ("secret", str),
            "ARIA2_RPC_SECURE": ("secure", lambda v: v.lower() == "true"),
        }
        for env_var, (key, cast) in env_map.items():
            val = os.environ.get(env_var)
            if val is not None:
                try:
                    config[key] = cast(val)
                except Exception:
                    pass

        self._config = config
        return config

    def get_endpoint_url(self):
        if self._config is None:
            self.load()
        c = self._config
        protocol = "https" if c.get("secure") else "http"
        path = c.get("path") or ""
        return f"{protocol}://{c[\'host\']}:{c[\'port\']}{path}"

    def show(self):
        if self._config is None:
            self.load()
        print("Current configuration:")
        for k, v in self._config.items():
            if k == "secret" and v:
                print(f"  {k}: ******")
            else:
                print(f"  {k}: {v}")

    def test(self):
        import urllib.request
        import urllib.error
        if self._config is None:
            self.load()
        url = self.get_endpoint_url()
        req_data = json.dumps({
            "jsonrpc": "2.0", "id": "test", "method": "aria2.getVersion", "params": []
        }).encode()
        req = urllib.request.Request(url, data=req_data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                if "result" in data:
                    print("✓ Connection successful")
                    return True
                else:
                    print(f"✗ Connection failed: {data}")
                    return False
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def init(self, scope="user"):
        if scope == "user":
            cfg_path = Path.home() / ".config" / "aria2-skill" / "config.json"
        else:
            cfg_path = Path(__file__).parent.parent / "config.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        if not cfg_path.exists():
            with open(cfg_path, "w") as f:
                json.dump(DEFAULTS, f, indent=2)
        print(f"Config initialized at: {cfg_path}")
        return str(cfg_path)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="show",
                        choices=["show", "test", "init"])
    parser.add_argument("--user", action="store_true")
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    cfg = Aria2Config()
    cfg.load()

    if args.command == "show":
        cfg.show()
    elif args.command == "test":
        success = cfg.test()
        sys.exit(0 if success else 1)
    elif args.command == "init":
        scope = "user" if args.user else "local"
        cfg.init(scope)


if __name__ == "__main__":
    main()
'''

# rpc_client.py – copied from SKILL.md exactly (truncated here; we write the actual full version)
rpc_client_src = r'''#!/usr/bin/env python3
"""JSON-RPC 2.0 client for aria2."""
import json
import urllib.request
import urllib.error
import sys
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
        return {
            "jsonrpc": "2.0",
            "id": self._generate_request_id(),
            "method": method,
            "params": params,
        }

    def _send_request(self, request):
        request_data = json.dumps(request).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url, data=request_data,
            headers={"Content-Type": "application/json",
                     "User-Agent": "aria2-json-rpc-client/1.0"})
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
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")

    def _parse_response(self, response, request_id):
        if not isinstance(response, dict):
            raise Exception("Invalid JSON-RPC response")
        if response.get("jsonrpc") != "2.0":
            raise Exception("Invalid JSON-RPC response: bad jsonrpc field")
        if response.get("id") != request_id:
            raise Exception(f"ID mismatch: expected {request_id}, got {response.get('id')}")
        if "error" in response:
            error = response["error"]
            raise Aria2RpcError(
                code=error.get("code", -1),
                message=error.get("message", "Unknown error"),
                data=error.get("data"),
                request_id=request_id)
        if "result" not in response:
            raise Exception("Missing result in response")
        return response["result"]

    def call(self, method, params=None):
        request = self._format_request(method, params)
        request_id = request["id"]
        try:
            response = self._send_request(request)
            return self._parse_response(response, request_id)
        except Aria2RpcError:
            raise
        except Exception as e:
            raise Exception(f"Failed to call {method}: {e}\nEndpoint: {self.endpoint_url}")

    def add_uri(self, uris, options=None, position=None):
        if isinstance(uris, str):
            uris = [uris]
        params = [uris]
        if options:
            params.append(options)
        if position is not None:
            params.append(position)
        return self.call("aria2.addUri", params)

    def tell_status(self, gid, keys=None):
        params = [gid]
        if keys:
            params.append(keys)
        return self.call("aria2.tellStatus", params)

    def remove(self, gid):
        return self.call("aria2.remove", [gid])

    def get_global_stat(self):
        return self.call("aria2.getGlobalStat", [])

    def pause(self, gid):
        return self.call("aria2.pause", [gid])

    def pause_all(self):
        return self.call("aria2.pauseAll", [])

    def unpause(self, gid):
        return self.call("aria2.unpause", [gid])

    def unpause_all(self):
        return self.call("aria2.unpauseAll", [])

    def tell_active(self, keys=None):
        params = []
        if keys:
            params.append(keys)
        return self.call("aria2.tellActive", params)

    def tell_waiting(self, offset=0, num=100, keys=None):
        params = [offset, num]
        if keys:
            params.append(keys)
        return self.call("aria2.tellWaiting", params)

    def tell_stopped(self, offset=0, num=100, keys=None):
        params = [offset, num]
        if keys:
            params.append(keys)
        return self.call("aria2.tellStopped", params)

    def get_option(self, gid):
        return self.call("aria2.getOption", [gid])

    def change_option(self, gid, options):
        return self.call("aria2.changeOption", [gid, options])

    def get_global_option(self):
        return self.call("aria2.getGlobalOption", [])

    def change_global_option(self, options):
        return self.call("aria2.changeGlobalOption", [options])

    def purge_download_result(self):
        return self.call("aria2.purgeDownloadResult", [])

    def remove_download_result(self, gid):
        return self.call("aria2.removeDownloadResult", [gid])

    def get_version(self):
        return self.call("aria2.getVersion", [])

    def list_methods(self):
        return self.call("system.listMethods", [])

    def multicall(self, calls):
        return self.call("system.multicall", [calls])

    def add_torrent(self, torrent, uris=None, options=None, position=None):
        if isinstance(torrent, str):
            if os.path.isfile(torrent):
                with open(torrent, "rb") as f:
                    torrent_bytes = f.read()
                torrent_base64 = base64.b64encode(torrent_bytes).decode("utf-8")
            else:
                torrent_base64 = torrent
        elif isinstance(torrent, bytes):
            torrent_base64 = base64.b64encode(torrent).decode("utf-8")
        else:
            raise ValueError("torrent must be file path, bytes, or base64 string")
        params = [torrent_base64]
        if uris:
            params.append(uris)
        elif options or position is not None:
            params.append([])
        if options:
            params.append(options)
        elif position is not None:
            params.append({})
        if position is not None:
            params.append(position)
        return self.call("aria2.addTorrent", params)


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
                try:
                    params.append(json.loads(arg))
                except json.JSONDecodeError:
                    try:
                        params.append(int(arg))
                    except ValueError:
                        params.append(arg)
            result = client.call(method, params)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except Aria2RpcError as e:
        print(f"aria2 error: {e}", file=sys.stderr)
        print(f"Code: {e.code}", file=sys.stderr)
        print(f"Message: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(scripts_dir / "config_loader.py").write_text(config_loader_src)
(scripts_dir / "rpc_client.py").write_text(rpc_client_src)

# Minimal example scripts (stubs that import correctly)
list_downloads_src = '''#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import Aria2Config
from rpc_client import Aria2RpcClient, Aria2RpcError

def format_size(b):
    if not b or b == "0": return "0 B"
    v = int(b)
    for u in ["B","KB","MB","GB","TB"]:
        if v < 1024: return f"{v:.2f} {u}"
        v /= 1024
    return f"{v:.2f} PB"

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    cfg = Aria2Config(); c = cfg.load()
    client = Aria2RpcClient(c)
    active = client.tell_active()
    waiting = client.tell_waiting(0, args.limit)
    stopped = client.tell_stopped(0, args.limit)
    print(f"Active: {len(active)}, Waiting: {len(waiting)}, Stopped: {len(stopped)}")
    for dl in active + waiting + stopped:
        gid = dl.get("gid","?")
        status = dl.get("status","?")
        files = dl.get("files",[])
        fn = os.path.basename(files[0].get("path","?")) if files else "?"
        print(f"  GID={gid} status={status} file={fn}")

if __name__ == "__main__":
    main()
'''
(examples_dir / "list-downloads.py").write_text(list_downloads_src)

pause_all_src = '''#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import Aria2Config
from rpc_client import Aria2RpcClient, Aria2RpcError

def main():
    cfg = Aria2Config(); c = cfg.load()
    client = Aria2RpcClient(c)
    result = client.pause_all()
    print(f"pauseAll: {result}")

if __name__ == "__main__":
    main()
'''
(examples_dir / "pause-all.py").write_text(pause_all_src)

set_options_src = '''#!/usr/bin/env python3
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import Aria2Config
from rpc_client import Aria2RpcClient, Aria2RpcError

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gid")
    parser.add_argument("--global", dest="is_global", action="store_true")
    parser.add_argument("--max-download-limit")
    args = parser.parse_args()
    cfg = Aria2Config(); c = cfg.load()
    client = Aria2RpcClient(c)
    options = {}
    if args.max_download_limit:
        options["max-download-limit"] = args.max_download_limit
    if args.is_global:
        r = client.change_global_option(options)
    else:
        r = client.change_option(args.gid, options)
    print(f"Result: {r}")

if __name__ == "__main__":
    main()
'''
(examples_dir / "set-options.py").write_text(set_options_src)

# ── 4. Task specification file (the "brief" given to the agent) ──────────────
task_brief = {
    "project": "MediaStream Asset Pipeline - Q2 Batch Download Audit",
    "description": (
        "We need to queue 3 media asset downloads for the new streaming season, "
        "then throttle the largest file to 512 KB/s to avoid saturating the office link, "
        "then clean up the completed batch from the download manager's memory, "
        "and finally save a JSON audit report."
    ),
    "asset_urls": [
        "http://cdn.internal/assets/season02/episode01_4k.mp4",
        "http://cdn.internal/assets/season02/episode02_4k.mp4",
        "http://cdn.internal/assets/season02/episode03_4k.mp4",
    ],
    "throttle_target": "episode01_4k.mp4",
    "throttle_speed_kbps": 512,
    "report_filename": "audit_report.json",
    "note": "The download manager RPC is available at localhost:7600"
}
(WORKSPACE / "task_brief.json").write_text(json.dumps(task_brief, indent=2))

# ── 5. Intentionally broken / misleading config files ───────────────────────
# Old stale config pointing to wrong port (agent should NOT use this blindly)
old_config = {
    "host": "localhost",
    "port": 6800,   # WRONG port - mock runs on 7600
    "secret": None,
    "secure": False,
    "timeout": 30000,
}
(skill_root / "config.json").write_text(json.dumps(old_config, indent=2))

# A random JSON in ops that looks like a config but is not
(WORKSPACE / "ops" / "configs" / "cdn" / "aria2_old.json").write_text(json.dumps({
    "host": "192.168.1.50",
    "port": 6800,
    "secret": "oldtoken",
    "note": "DEPRECATED - do not use"
}, indent=2))

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Task brief: {WORKSPACE / 'task_brief.json'}")