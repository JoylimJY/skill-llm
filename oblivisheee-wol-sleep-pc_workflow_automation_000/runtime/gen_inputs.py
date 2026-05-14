import os
import stat
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "docs/network",
    "docs/hardware",
    "config/legacy",
    "config/templates",
    "scripts",
    "tests/unit",
    "tests/integration",
    "tools/monitor",
    "tools/deploy",
    "logs/archive",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "docs/network/topology.md":          "# Network Topology\nSee diagrams folder.",
    "docs/network/vlan_notes.txt":        "VLAN 10: management\nVLAN 20: workstations",
    "docs/hardware/specs.md":             "# Hardware Specs\nWorkstation: Dell Precision 5820",
    "docs/hardware/bios_settings.txt":    "Enable WOL in BIOS: Power Management > Wake on LAN = Enabled",
    "config/legacy/old_config.json":      json.dumps({"mac": "00:00:00:00:00:00", "broadcast": "0.0.0.0"}),
    "config/templates/example.json":      json.dumps({"mac": "XX:XX:XX:XX:XX:XX", "broadcast": "X.X.X.255", "port": 0}),
    "tests/unit/test_placeholder.py":     "# placeholder\ndef test_noop(): pass\n",
    "tests/integration/test_net.py":      "# integration placeholder\n",
    "tools/monitor/ping_check.sh":        "#!/bin/bash\nping -c1 $1 && echo UP || echo DOWN\n",
    "tools/deploy/push_config.sh":        "#!/bin/bash\necho 'deploy'\n",
    "logs/archive/2024-01-15.log":        "INFO: system started\nINFO: all services nominal\n",
    ".gitignore":                          "*.pyc\n__pycache__/\n.env\nconfig.json\n~/.config/\n",
    "README.md":                           "# wol-sleep-pc\nSee scripts/ for details.",
}
for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── REAL scripts that the agent will invoke ────────────────────────────────
# send_wol.py — loads config, accepts CLI flags, logs invocation
wol_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """Send a Wake-on-LAN magic packet."""
    import argparse, json, socket, struct, pathlib, datetime

    DEFAULT_CONFIG = pathlib.Path.home() / ".config" / "wol-sleep-pc" / "config.json"
    LOG_FILE = pathlib.Path("/tmp/wol_invocations.log")

    def load_config():
        if DEFAULT_CONFIG.exists():
            with DEFAULT_CONFIG.open() as f:
                return json.load(f)
        return {}

    def send_magic_packet(mac: str, broadcast: str, port: int):
        mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
        magic = b\'\\xff\' * 6 + mac_bytes * 16
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                s.sendto(magic, (broadcast, port))
            except OSError:
                pass  # ignore broadcast permission errors in container

    def main():
        cfg = load_config()
        parser = argparse.ArgumentParser(description="Send WOL magic packet")
        parser.add_argument("--mac",       default=cfg.get("mac",       "00:00:00:00:00:00"))
        parser.add_argument("--broadcast", default=cfg.get("broadcast", "255.255.255.255"))
        parser.add_argument("--port",      type=int, default=cfg.get("port", 9))
        args = parser.parse_args()

        send_magic_packet(args.mac, args.broadcast, args.port)

        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": "WOL",
            "mac": args.mac,
            "broadcast": args.broadcast,
            "port": args.port,
        }
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(entry) + "\\n")
        print(f"WOL packet sent to {args.mac} via {args.broadcast}:{args.port}")

    if __name__ == "__main__":
        main()
''')

# send_sleep.py — loads config sleep_mac field, accepts CLI flags, logs invocation
sleep_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """Send a Sleep-on-LAN (inverted-MAC) magic packet."""
    import argparse, json, socket, pathlib, datetime

    DEFAULT_CONFIG = pathlib.Path.home() / ".config" / "wol-sleep-pc" / "config.json"
    LOG_FILE = pathlib.Path("/tmp/sol_invocations.log")

    def load_config():
        if DEFAULT_CONFIG.exists():
            with DEFAULT_CONFIG.open() as f:
                return json.load(f)
        return {}

    def send_sleep_packet(mac: str, broadcast: str, port: int):
        mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
        magic = b\'\\xff\' * 6 + mac_bytes * 16
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                s.sendto(magic, (broadcast, port))
            except OSError:
                pass

    def main():
        cfg = load_config()
        parser = argparse.ArgumentParser(description="Send SOL (inverted-MAC) packet")
        parser.add_argument("--mac",       default=cfg.get("sleep_mac",  "00:00:00:00:00:00"))
        parser.add_argument("--broadcast", default=cfg.get("broadcast",  "255.255.255.255"))
        parser.add_argument("--port",      type=int, default=cfg.get("port", 9))
        args = parser.parse_args()

        send_sleep_packet(args.mac, args.broadcast, args.port)

        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": "SOL",
            "mac": args.mac,
            "broadcast": args.broadcast,
            "port": args.port,
        }
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(entry) + "\\n")
        print(f"SOL packet sent to {args.mac} via {args.broadcast}:{args.port}")

    if __name__ == "__main__":
        main()
''')

(WORKSPACE / "scripts" / "send_wol.py").write_text(wol_script)
(WORKSPACE / "scripts" / "send_sleep.py").write_text(sleep_script)

# ── Intentionally broken / stale legacy config at wrong location ──────────
# This is a trap: agent might use this instead of the correct ~/.config path
legacy_cfg = WORKSPACE / "config" / "legacy" / "wol_config.json"
legacy_cfg.write_text(json.dumps({
    "mac": "AA:BB:CC:DD:EE:FF",
    "broadcast": "10.0.0.255",
    "port": 7,
    "note": "DEPRECATED - do not use"
}, indent=2))

# ── A partial, malformed config at another wrong location ─────────────────
partial_cfg = WORKSPACE / "config" / "wol_settings.json"
partial_cfg.write_text('{"mac": "24:4B:FE:CA:90:99"}')  # missing sleep_mac, broadcast, port

print("Workspace initialised.")