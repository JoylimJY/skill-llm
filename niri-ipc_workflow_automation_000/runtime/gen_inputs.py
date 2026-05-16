#!/usr/bin/env python3
"""
Generate the sandbox workspace for the Niri IPC task.
Creates the skill scripts, policy file, distractor files, and mock server infrastructure.
"""
import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "skills/niri-ipc/scripts",
    "skills/niri-ipc/references",
    "config/policies",
    "logs/compositor",
    "reports/archive",
    "tools/misc",
    "docs/wayland",
    "scripts/automation",
    "tmp/cache",
    "projects/alpha",
    "projects/beta",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "docs/wayland/overview.txt": "Wayland is a display server protocol...\nNiri is a scrollable-tiling compositor.\nSee https://github.com/YaLTeR/niri",
    "docs/wayland/keybinds.txt": "Mod+T: open terminal\nMod+W: close window\nMod+1..9: switch workspace",
    "config/old_layout.json": json.dumps({"workspaces": ["ws1", "ws2", "ws3"], "layout": "legacy"}, indent=2),
    "logs/compositor/session_2024-01-10.log": "niri started\noutput: eDP-1 2560x1600\nworkspace 1 active\n",
    "logs/compositor/session_2024-01-11.log": "niri started\noutput: eDP-1 2560x1600\nworkspace 2 active\n",
    "tools/misc/kill_all.sh": "#!/bin/bash\n# DO NOT USE IN PRODUCTION\nkillall -9 niri\n",
    "tools/misc/debug_socket.py": "# placeholder debug script\nprint('socket debug')\n",
    "reports/archive/layout_snapshot_old.json": json.dumps({"date": "2024-01-01", "windows": [], "note": "stale"}, indent=2),
    "scripts/automation/restart_compositor.sh": "#!/bin/bash\nniri msg action quit\n",
    "scripts/automation/backup_config.sh": "#!/bin/bash\ncp ~/.config/niri/config.kdl /tmp/niri_backup.kdl\n",
    "tmp/cache/niri_pid.txt": "12345\n",
    "projects/alpha/README_NOT_FOR_AGENT.txt": "Alpha project placeholder. Not relevant to window management.",
    "projects/beta/notes.txt": "Beta project uses Firefox and VSCode exclusively.",
}
for path, content in distractor_files.items():
    fpath = WORKSPACE / path
    fpath.write_text(content)

# ── References (IPC protocol doc - partial, realistic) ───────────────────────
ipc_ref = """\
# Niri IPC Protocol Reference

## Transport
Requests are sent as newline-terminated JSON over the Unix socket at $NIRI_SOCKET.
Each connection handles exactly one request-response pair (except event-stream).

## Request Format
Requests are JSON values:
- Simple string:  "Workspaces"
- String:         "Windows"
- String:         "FocusedWindow"
- String:         "Version"
- Object:         {"Action": {"FocusWindow": {"id": 42}}}
- Object:         {"Action": {"MoveWindowToWorkspace": {"window_id": 42, "reference": {"Index": 2}}}}
- Object:         {"Action": {"MoveWindowToWorkspace": {"window_id": 42, "reference": {"Name": "web"}}}}
- Object:         {"Action": {"FocusWorkspace": {"reference": {"Index": 1}}}}

## Response Format
{"Ok": <payload>} or {"Err": "description"}

## Workspace Reference
Can be {"Index": N} (1-based) or {"Name": "name_string"}.
"""
(WORKSPACE / "skills/niri-ipc/references/ipc.md").write_text(ipc_ref)

# ── Mock Niri socket server ───────────────────────────────────────────────────
# This Python script IS the mock Niri IPC server.
# It maintains stateful window/workspace data and handles mutations.
mock_server_py = r'''#!/usr/bin/env python3
"""
Mock Niri IPC socket server.
Listens on a Unix socket, handles Niri IPC protocol (newline-delimited JSON).
Maintains mutable state for windows and workspaces.
Writes state snapshots to /tmp/niri_mock_state.json after each mutation.
"""
import socket
import json
import os
import sys
import threading

SOCKET_PATH = os.environ.get("NIRI_SOCKET", "/tmp/niri_mock.sock")
STATE_PATH = "/tmp/niri_mock_state.json"

# Initial state
workspaces = [
    {"id": 1, "idx": 1, "name": "terminal", "output": "eDP-1", "is_active": True,  "is_focused": True,  "active_window_id": 101},
    {"id": 2, "idx": 2, "name": "web",      "output": "eDP-1", "is_active": False, "is_focused": False, "active_window_id": None},
    {"id": 3, "idx": 3, "name": "code",     "output": "eDP-1", "is_active": False, "is_focused": False, "active_window_id": None},
    {"id": 4, "idx": 4, "name": "media",    "output": "eDP-1", "is_active": False, "is_focused": False, "active_window_id": None},
]

windows = [
    {"id": 101, "title": "bash — Alacritty",         "app_id": "Alacritty",   "workspace_id": 1, "is_focused": True},
    {"id": 102, "title": "Mozilla Firefox",           "app_id": "firefox",     "workspace_id": 1, "is_focused": False},
    {"id": 103, "title": "Visual Studio Code",        "app_id": "code",        "workspace_id": 1, "is_focused": False},
    {"id": 104, "title": "Spotify — Linux",           "app_id": "spotify",     "workspace_id": 1, "is_focused": False},
    {"id": 105, "title": "nvim config.kdl — Alacritty","app_id": "Alacritty",  "workspace_id": 1, "is_focused": False},
    {"id": 106, "title": "Chromium",                  "app_id": "chromium",    "workspace_id": 1, "is_focused": False},
    {"id": 107, "title": "VLC media player",          "app_id": "vlc",         "workspace_id": 1, "is_focused": False},
    {"id": 108, "title": "Slack",                     "app_id": "slack",       "workspace_id": 1, "is_focused": False},
]

def save_state():
    with open(STATE_PATH, "w") as f:
        json.dump({"windows": windows, "workspaces": workspaces}, f, indent=2)

save_state()

def get_workspace_by_ref(ref):
    if "Index" in ref:
        idx = ref["Index"]
        for ws in workspaces:
            if ws["idx"] == idx:
                return ws
    elif "Name" in ref:
        name = ref["Name"].lower()
        for ws in workspaces:
            if ws["name"].lower() == name:
                return ws
    return None

def handle_request(data):
    try:
        req = json.loads(data.strip())
    except Exception as e:
        return json.dumps({"Err": f"parse error: {e}"})

    # Simple string requests
    if req == "Workspaces":
        return json.dumps({"Ok": {"Workspaces": workspaces}})
    elif req == "Windows":
        return json.dumps({"Ok": {"Windows": windows}})
    elif req == "FocusedWindow":
        focused = next((w for w in windows if w["is_focused"]), None)
        return json.dumps({"Ok": {"FocusedWindow": focused}})
    elif req == "Version":
        return json.dumps({"Ok": {"Version": {"version": "0.1.8-mock", "commit": "abc1234"}}})
    elif isinstance(req, dict) and "Action" in req:
        action = req["Action"]
        # FocusWindow
        if isinstance(action, dict) and "FocusWindow" in action:
            wid = action["FocusWindow"].get("id")
            target = next((w for w in windows if w["id"] == wid), None)
            if target is None:
                return json.dumps({"Err": f"window {wid} not found"})
            for w in windows:
                w["is_focused"] = (w["id"] == wid)
            save_state()
            return json.dumps({"Ok": None})
        # MoveWindowToWorkspace
        elif isinstance(action, dict) and "MoveWindowToWorkspace" in action:
            params = action["MoveWindowToWorkspace"]
            wid = params.get("window_id")
            ref = params.get("reference", {})
            target_ws = get_workspace_by_ref(ref)
            target_win = next((w for w in windows if w["id"] == wid), None)
            if target_win is None:
                return json.dumps({"Err": f"window {wid} not found"})
            if target_ws is None:
                return json.dumps({"Err": f"workspace not found: {ref}"})
            target_win["workspace_id"] = target_ws["id"]
            save_state()
            return json.dumps({"Ok": None})
        # FocusWorkspace
        elif isinstance(action, dict) and "FocusWorkspace" in action:
            ref = action["FocusWorkspace"].get("reference", {})
            target_ws = get_workspace_by_ref(ref)
            if target_ws is None:
                return json.dumps({"Err": f"workspace not found: {ref}"})
            for ws in workspaces:
                ws["is_focused"] = (ws["id"] == target_ws["id"])
                ws["is_active"] = (ws["id"] == target_ws["id"])
            save_state()
            return json.dumps({"Ok": None})
        # CloseWindow / close-focused
        elif action == "CloseWindow" or (isinstance(action, dict) and "CloseWindow" in action):
            if isinstance(action, dict) and "CloseWindow" in action:
                wid = action["CloseWindow"].get("id")
                windows[:] = [w for w in windows if w["id"] != wid]
            else:
                focused = next((w for w in windows if w["is_focused"]), None)
                if focused:
                    windows.remove(focused)
            save_state()
            return json.dumps({"Ok": None})
        else:
            # Unknown action - just ack
            save_state()
            return json.dumps({"Ok": None})
    else:
        return json.dumps({"Err": f"unknown request: {req!r}"})

def handle_client(conn):
    try:
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        lines = data.decode().strip().split("\n")
        for line in lines:
            if line.strip():
                resp = handle_request(line.strip())
                conn.sendall((resp + "\n").encode())
    except Exception as e:
        try:
            conn.sendall((json.dumps({"Err": str(e)}) + "\n").encode())
        except:
            pass
    finally:
        conn.close()

def run_server():
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCKET_PATH)
    srv.listen(32)
    os.chmod(SOCKET_PATH, 0o666)
    while True:
        try:
            conn, _ = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
            t.start()
        except Exception:
            pass

if __name__ == "__main__":
    run_server()
'''
mock_path = WORKSPACE / "skills/niri-ipc/scripts/mock_niri_server.py"
mock_path.write_text(mock_server_py)
mock_path.chmod(mock_path.stat().st_mode | stat.S_IEXEC)

# ── niri.py wrapper script ────────────────────────────────────────────────────
niri_py = r'''#!/usr/bin/env python3
"""
niri.py — wrapper around niri IPC socket (mirrors `niri msg --json`)
Usage:
  niri.py version
  niri.py outputs
  niri.py workspaces
  niri.py windows
  niri.py focused-window
  niri.py event-stream [--lines N]
  niri.py action <action> [args...]
"""
import sys
import os
import json
import socket as _socket

SOCKET_PATH = os.environ.get("NIRI_SOCKET")
if not SOCKET_PATH:
    print("ERROR: NIRI_SOCKET is not set", file=sys.stderr)
    sys.exit(1)

def send_request(req):
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    payload = (json.dumps(req) + "\n").encode()
    s.sendall(payload)
    resp = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
        if resp.endswith(b"\n"):
            break
    s.close()
    return json.loads(resp.decode().strip())

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]
    if cmd == "version":
        r = send_request("Version")
        print(json.dumps(r, indent=2))
    elif cmd == "outputs":
        r = send_request("Outputs")
        print(json.dumps(r, indent=2))
    elif cmd == "workspaces":
        r = send_request("Workspaces")
        print(json.dumps(r, indent=2))
    elif cmd == "windows":
        r = send_request("Windows")
        print(json.dumps(r, indent=2))
    elif cmd == "focused-window":
        r = send_request("FocusedWindow")
        print(json.dumps(r, indent=2))
    elif cmd == "event-stream":
        lines_limit = None
        if "--lines" in args:
            idx = args.index("--lines")
            lines_limit = int(args[idx+1])
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.connect(SOCKET_PATH)
        s.sendall((json.dumps("EventStream") + "\n").encode())
        count = 0
        for line in s.makefile():
            print(line, end="")
            count += 1
            if lines_limit and count >= lines_limit:
                break
        s.close()
    elif cmd == "action":
        if len(args) < 2:
            print("Usage: niri.py action <action_name> [args]", file=sys.stderr)
            sys.exit(1)
        action_name = args[1]
        action_args = args[2:]
        # Map CLI action names to IPC action objects
        if action_name == "focus-workspace":
            idx = int(action_args[0])
            req = {"Action": {"FocusWorkspace": {"reference": {"Index": idx}}}}
        elif action_name == "move-window-to-workspace":
            idx = int(action_args[0])
            req = {"Action": {"MoveWindowToWorkspace": {"reference": {"Index": idx}}}}
        elif action_name == "focus-window":
            wid = int(action_args[0])
            req = {"Action": {"FocusWindow": {"id": wid}}}
        elif action_name == "close-window":
            req = {"Action": "CloseWindow"}
        elif action_name == "spawn":
            cmd_args = action_args
            if "--" in cmd_args:
                cmd_args = cmd_args[cmd_args.index("--")+1:]
            req = {"Action": {"Spawn": {"command": cmd_args}}}
        elif action_name == "load-config-file":
            req = {"Action": "LoadConfigFile"}
        else:
            req = {"Action": action_name}
        r = send_request(req)
        print(json.dumps(r, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
niri_py_path = WORKSPACE / "skills/niri-ipc/scripts/niri.py"
niri_py_path.write_text(niri_py)
niri_py_path.chmod(niri_py_path.stat().st_mode | stat.S_IEXEC)

# ── niri_ctl.py high-level helper ─────────────────────────────────────────────
niri_ctl_py = r'''#!/usr/bin/env python3
"""
niri_ctl.py — high-level Niri IPC helper (window matching by title/app_id substring)
Usage:
  niri_ctl.py list-windows [--query SUBSTR]
  niri_ctl.py focus SUBSTR
  niri_ctl.py close SUBSTR
  niri_ctl.py move-to-workspace SUBSTR WORKSPACE
  niri_ctl.py focus-workspace WORKSPACE
"""
import sys
import os
import json
import socket as _socket

SOCKET_PATH = os.environ.get("NIRI_SOCKET")
if not SOCKET_PATH:
    print("ERROR: NIRI_SOCKET is not set", file=sys.stderr)
    sys.exit(1)

def send_request(req):
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    payload = (json.dumps(req) + "\n").encode()
    s.sendall(payload)
    resp = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
        if resp.endswith(b"\n"):
            break
    s.close()
    return json.loads(resp.decode().strip())

def get_windows():
    r = send_request("Windows")
    if "Ok" in r and "Windows" in r["Ok"]:
        return r["Ok"]["Windows"]
    return []

def get_workspaces():
    r = send_request("Workspaces")
    if "Ok" in r and "Workspaces" in r["Ok"]:
        return r["Ok"]["Workspaces"]
    return []

def match_windows(query):
    query = query.lower()
    wins = get_windows()
    return [w for w in wins if query in w.get("title","").lower() or query in w.get("app_id","").lower()]

def resolve_workspace(ws_ref):
    """Resolve workspace by index (int string) or name (str)."""
    try:
        idx = int(ws_ref)
        return {"Index": idx}
    except ValueError:
        return {"Name": ws_ref}

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    cmd = args[0]

    if cmd == "list-windows":
        query = None
        if "--query" in args:
            idx = args.index("--query")
            query = args[idx+1]
        wins = get_windows()
        if query:
            wins = [w for w in wins if query.lower() in w.get("title","").lower() or query.lower() in w.get("app_id","").lower()]
        print(json.dumps(wins, indent=2))

    elif cmd == "focus":
        if len(args) < 2:
            print("Usage: niri_ctl.py focus SUBSTR", file=sys.stderr); sys.exit(1)
        matches = match_windows(args[1])
        if not matches:
            print(f"No window matching '{args[1]}'", file=sys.stderr); sys.exit(1)
        win = matches[0]
        r = send_request({"Action": {"FocusWindow": {"id": win["id"]}}})
        print(json.dumps(r, indent=2))

    elif cmd == "close":
        if len(args) < 2:
            print("Usage: niri_ctl.py close SUBSTR", file=sys.stderr); sys.exit(1)
        matches = match_windows(args[1])
        if not matches:
            print(f"No window matching '{args[1]}'", file=sys.stderr); sys.exit(1)
        win = matches[0]
        send_request({"Action": {"FocusWindow": {"id": win["id"]}}})
        r = send_request({"Action": "CloseWindow"})
        print(json.dumps(r, indent=2))

    elif cmd == "move-to-workspace":
        if len(args) < 3:
            print("Usage: niri_ctl.py move-to-workspace SUBSTR WORKSPACE", file=sys.stderr); sys.exit(1)
        substr = args[1]
        ws_ref_str = args[2]
        matches = match_windows(substr)
        if not matches:
            print(f"No window matching '{substr}'", file=sys.stderr); sys.exit(1)
        ref = resolve_workspace(ws_ref_str)
        results = []
        for win in matches:
            r = send_request({"Action": {"MoveWindowToWorkspace": {"window_id": win["id"], "reference": ref}}})
            results.append({"window_id": win["id"], "title": win["title"], "result": r})
        print(json.dumps(results, indent=2))

    elif cmd == "focus-workspace":
        if len(args) < 2:
            print("Usage: niri_ctl.py focus-workspace WORKSPACE", file=sys.stderr); sys.exit(1)
        ref = resolve_workspace(args[1])
        r = send_request({"Action": {"FocusWorkspace": {"reference": ref}}})
        print(json.dumps(r, indent=2))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
'''
niri_ctl_path = WORKSPACE / "skills/niri-ipc/scripts/niri_ctl.py"
niri_ctl_path.write_text(niri_ctl_py)
niri_ctl_path.chmod(niri_ctl_path.stat().st_mode | stat.S_IEXEC)

# ── niri_socket.py raw socket helper ─────────────────────────────────────────
niri_socket_py = r'''#!/usr/bin/env python3
"""
niri_socket.py — low-level Niri socket communication
Usage:
  niri_socket.py raw '<JSON_REQUEST>'
  niri_socket.py stdin                  (one JSON request per line on stdin)
  niri_socket.py event-stream
"""
import sys
import os
import json
import socket as _socket

SOCKET_PATH = os.environ.get("NIRI_SOCKET")
if not SOCKET_PATH:
    print("ERROR: NIRI_SOCKET is not set", file=sys.stderr)
    sys.exit(1)

def send_one(req_str):
    req_str = req_str.strip()
    if not req_str:
        return None
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    s.sendall((req_str + "\n").encode())
    resp = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
        if resp.endswith(b"\n"):
            break
    s.close()
    return resp.decode().strip()

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    cmd = args[0]

    if cmd == "raw":
        if len(args) < 2:
            print("Usage: niri_socket.py raw '<JSON>'", file=sys.stderr); sys.exit(1)
        result = send_one(args[1])
        print(result)

    elif cmd == "stdin":
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            result = send_one(line)
            if result:
                print(result)

    elif cmd == "event-stream":
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.connect(SOCKET_PATH)
        s.sendall((json.dumps("EventStream") + "\n").encode())
        for line in s.makefile():
            print(line, end="", flush=True)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
'''
niri_socket_path = WORKSPACE / "skills/niri-ipc/scripts/niri_socket.py"
niri_socket_path.write_text(niri_socket_py)
niri_socket_path.chmod(niri_socket_path.stat().st_mode | stat.S_IEXEC)

# ── Workspace policy document (the task specification) ───────────────────────
# This is the "business requirement" the agent must implement
policy = {
    "version": "1.0",
    "description": "Workspace assignment policy for developer workstation",
    "rules": [
        {
            "workspace": "web",
            "assign_if_app_id_contains": ["firefox", "chromium"],
            "rationale": "All browser windows belong on the web workspace"
        },
        {
            "workspace": "code",
            "assign_if_app_id_contains": ["code", "nvim", "vim"],
            "assign_if_title_contains": ["Visual Studio Code", "nvim"],
            "rationale": "All editor/IDE windows belong on the code workspace"
        },
        {
            "workspace": "media",
            "assign_if_app_id_contains": ["spotify", "vlc"],
            "rationale": "All media players belong on the media workspace"
        },
        {
            "workspace": "terminal",
            "assign_if_app_id_contains": ["alacritty", "kitty", "foot"],
            "rationale": "Terminal emulators stay on the terminal workspace"
        }
    ],
    "unmatched_policy": "leave_in_place",
    "note": "Slack and similar communication apps are not covered by this policy version"
}
policy_path = WORKSPACE / "config/policies/workspace_policy.json"
policy_path.write_text(json.dumps(policy, indent=2))

# ── Extra distractor: a stale/wrong policy ────────────────────────────────────
stale_policy = {
    "version": "0.9-DEPRECATED",
    "rules": [{"workspace": "misc", "assign_if_app_id_contains": ["everything"]}],
    "note": "DO NOT USE - superseded by workspace_policy.json"
}
(WORKSPACE / "config/policies/workspace_policy_OLD.json").write_text(json.dumps(stale_policy, indent=2))

# ── Placeholder for expected output (agent must create this) ──────────────────
# The agent must create: workspace_audit.json
# We do NOT pre-create it, and we do NOT hint at its format here.

print("Workspace generated successfully.")
print(f"Policy: {policy_path}")
print(f"Mock server: {mock_path}")
print(f"Skill scripts: {WORKSPACE / 'skills/niri-ipc/scripts/'}")