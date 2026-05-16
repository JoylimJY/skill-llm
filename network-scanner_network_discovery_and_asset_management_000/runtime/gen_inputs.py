#!/usr/bin/env python3
"""
Build the initial sandbox workspace with the network-scanner skill scripts,
distractor files, and a realistic messy environment.
"""

import os
import stat
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── scripts/scan.py ── (the actual skill implementation) ──────────────────────
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

scan_py = r'''#!/usr/bin/env python3
"""
Network Scanner - Discover devices on local/remote networks using nmap.
Safety checks prevent scanning public IPs or blocklisted ranges.
"""

import argparse
import ipaddress
import json
import os
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "network-scanner" / "networks.json"

DEFAULT_CONFIG = {
    "networks": {
        "home": {
            "cidr": "192.168.1.0/24",
            "dns": "192.168.1.1",
            "description": "Home Network"
        },
        "office": {
            "cidr": "10.0.0.0/24",
            "dns": "10.0.0.1",
            "description": "Office Network"
        }
    },
    "blocklist": [
        {
            "cidr": "10.99.0.0/24",
            "reason": "No private route from this host"
        }
    ]
}

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

MAC_VENDORS = {
    "AA:BB:CC": "Ubiquiti",
    "11:22:33": "Synology",
    "DE:AD:BE": "Unknown",
    "00:50:56": "VMware",
    "52:54:00": "QEMU/KVM",
    "08:00:27": "VirtualBox",
    "02:42": "Docker",
}


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Config parse error: {e}", file=sys.stderr)
            sys.exit(1)
    return {"networks": {}, "blocklist": []}


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✓ Config written to {CONFIG_PATH}")


def is_private(network_str):
    try:
        net = ipaddress.ip_network(network_str, strict=False)
        return any(net.subnet_of(r) or net.overlaps(r) for r in PRIVATE_RANGES)
    except ValueError:
        return False


def is_blocklisted(cidr, config):
    try:
        target = ipaddress.ip_network(cidr, strict=False)
        for entry in config.get("blocklist", []):
            blocked = ipaddress.ip_network(entry["cidr"], strict=False)
            if target.overlaps(blocked):
                return entry
    except ValueError:
        pass
    return None


def has_private_route(cidr):
    """Check if the route to the target uses a private gateway."""
    try:
        target_ip = str(ipaddress.ip_network(cidr, strict=False).network_address)
        result = subprocess.run(
            ["ip", "route", "get", target_ip],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        # look for 'via X.X.X.X' in the route
        via_match = re.search(r'via\s+(\S+)', output)
        if via_match:
            gw = via_match.group(1)
            return is_private(gw + "/32")
        # if no via, direct route on a local interface - also ok
        if "dev" in output and result.returncode == 0:
            return True
        return False
    except Exception:
        return False


def get_vendor(mac):
    if not mac or mac == "N/A":
        return "Unknown"
    mac_upper = mac.upper()
    prefix6 = mac_upper[:8]
    prefix4 = mac_upper[:5]
    for key, vendor in MAC_VENDORS.items():
        if mac_upper.startswith(key.upper()):
            return vendor
    return "Unknown"


def reverse_dns(ip, dns_server=None):
    try:
        cmd = ["dig", "+short", "-x", ip]
        if dns_server:
            cmd += [f"@{dns_server}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        hostname = result.stdout.strip().rstrip(".")
        return hostname if hostname else ip
    except Exception:
        return ip


def run_nmap(cidr, use_sudo=True):
    """Run nmap and parse results. Returns list of device dicts."""
    cmd = []
    if use_sudo:
        cmd.append("sudo")
    cmd += ["nmap", "-sn", "--host-timeout", "3s", cidr]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout
    except subprocess.TimeoutExpired:
        print("❌ nmap timed out", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("❌ nmap not found", file=sys.stderr)
        return []

    devices = []
    current_ip = None
    current_mac = None
    current_vendor = None

    for line in output.splitlines():
        ip_match = re.search(r'Nmap scan report for (?:[\w.-]+ \()?(\d+\.\d+\.\d+\.\d+)\)?', line)
        if ip_match:
            if current_ip:
                devices.append({
                    "ip": current_ip,
                    "mac": current_mac or "N/A",
                    "vendor": current_vendor or "Unknown"
                })
            current_ip = ip_match.group(1)
            current_mac = None
            current_vendor = None

        mac_match = re.search(r'MAC Address: ([0-9A-F:]{17})\s*(?:\((.+)\))?', line, re.IGNORECASE)
        if mac_match:
            current_mac = mac_match.group(1).upper()
            current_vendor = mac_match.group(2) if mac_match.group(2) else get_vendor(current_mac)

    if current_ip:
        devices.append({
            "ip": current_ip,
            "mac": current_mac or "N/A",
            "vendor": current_vendor or "Unknown"
        })

    return devices


def scan_network(cidr, dns_server=None, network_name=None, description=None,
                 use_sudo=True, output_json=False):
    print(f"✓ Scanning {cidr}...", file=sys.stderr)
    devices_raw = run_nmap(cidr, use_sudo=use_sudo)

    devices = []
    for d in devices_raw:
        hostname = reverse_dns(d["ip"], dns_server)
        devices.append({
            "ip": d["ip"],
            "hostname": hostname,
            "mac": d["mac"],
            "vendor": d["vendor"]
        })

    scan_time = datetime.now()
    desc = description or network_name or cidr

    if output_json:
        result = {
            "network": desc,
            "cidr": cidr,
            "devices": devices,
            "scanned_at": scan_time.isoformat(),
            "device_count": len(devices)
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n### {desc}")
        print(f"*Last scan: {scan_time.strftime('%Y-%m-%d %H:%M')}*\n")
        print("| IP | Name | MAC | Vendor |")
        print("|----|------|-----|--------|")
        for d in devices:
            print(f"| {d['ip']} | {d['hostname']} | {d['mac']} | {d['vendor']} |")
        print(f"\n*{len(devices)} devices found*")


def cmd_init_config():
    if CONFIG_PATH.exists():
        print(f"⚠ Config already exists at {CONFIG_PATH}")
        answer = input("Overwrite? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return
    save_config(DEFAULT_CONFIG)
    print("✓ Example config created. Edit it to add your networks.")


def cmd_list(config):
    networks = config.get("networks", {})
    if not networks:
        print("No networks configured. Run --init-config to create an example config.")
        return
    print("Configured networks:")
    for name, info in networks.items():
        desc = info.get("description", "")
        cidr = info.get("cidr", "")
        print(f"  {name}: {cidr}  ({desc})")
    blocklist = config.get("blocklist", [])
    if blocklist:
        print("\nBlocklisted ranges:")
        for entry in blocklist:
            print(f"  {entry['cidr']}  — {entry.get('reason','')}")


def main():
    parser = argparse.ArgumentParser(description="Network Scanner")
    parser.add_argument("target", nargs="?", help="CIDR or named network")
    parser.add_argument("--dns", help="DNS server for reverse lookups")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Output as JSON")
    parser.add_argument("--init-config", action="store_true",
                        help="Create example config file")
    parser.add_argument("--list", action="store_true",
                        help="List configured networks")
    parser.add_argument("--no-sudo", action="store_true",
                        help="Run nmap without sudo (may miss MACs)")
    args = parser.parse_args()

    config = load_config()

    if args.init_config:
        cmd_init_config()
        return

    if args.list:
        cmd_list(config)
        return

    if not args.target:
        # auto-detect: try to get default gateway subnet
        print("No target specified. Use --list to see configured networks or pass a CIDR/name.",
              file=sys.stderr)
        sys.exit(1)

    target = args.target
    networks = config.get("networks", {})
    use_sudo = not args.no_sudo

    # Resolve named network
    if target in networks:
        net_info = networks[target]
        cidr = net_info["cidr"]
        dns = args.dns or net_info.get("dns")
        desc = net_info.get("description", target)

        # Check blocklist even for named networks
        blocked = is_blocklisted(cidr, config)
        if blocked:
            print(f"❌ BLOCKED: {cidr} is blocklisted — {blocked.get('reason','')}")
            sys.exit(1)

        # Trusted network — skip route verification
        scan_network(cidr, dns_server=dns, network_name=target, description=desc,
                     use_sudo=use_sudo, output_json=args.output_json)
        return

    # Ad-hoc CIDR
    cidr = target

    # Check public IP
    if not is_private(cidr):
        print(f"❌ BLOCKED: Target {cidr} is a PUBLIC IP range")
        sys.exit(1)

    # Check blocklist
    blocked = is_blocklisted(cidr, config)
    if blocked:
        print(f"❌ BLOCKED: {cidr} is blocklisted — {blocked.get('reason','')}")
        sys.exit(1)

    # Route verification for ad-hoc CIDRs
    if not has_private_route(cidr):
        print(f"❌ BLOCKED: No private route found to {cidr}. Add it to your config as a trusted network to skip this check.")
        sys.exit(1)

    dns = args.dns
    scan_network(cidr, dns_server=dns, use_sudo=use_sudo, output_json=args.output_json)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(scripts_dir, "scan.py"), "w") as f:
    f.write(scan_py)
os.chmod(os.path.join(scripts_dir, "scan.py"), 0o755)

# ── Distractor files ──────────────────────────────────────────────────────────

# docs/
docs_dir = os.path.join(workspace, "docs")
os.makedirs(docs_dir, exist_ok=True)

with open(os.path.join(docs_dir, "network_topology.md"), "w") as f:
    f.write("# Network Topology\n\nDraft topology map for the lab environment.\n\n")
    f.write("- Lab segment: 10.0.1.0/24\n- DMZ segment: 172.16.0.0/24\n")
    f.write("- RESTRICTED (no direct route): 10.99.0.0/24\n")

with open(os.path.join(docs_dir, "asset_register.csv"), "w") as f:
    f.write("ip,hostname,department,owner\n")
    f.write("10.0.1.1,lab-gw,IT,ops-team\n")
    f.write("10.0.1.50,lab-server01,Engineering,dev-team\n")
    f.write("172.16.0.1,dmz-fw,Security,sec-team\n")

with open(os.path.join(docs_dir, "scan_schedule.txt"), "w") as f:
    f.write("Weekly scan schedule:\n")
    f.write("  Monday 02:00 UTC - lab\n")
    f.write("  Wednesday 02:00 UTC - dmz\n")
    f.write("  SKIP: 10.99.0.0/24 (no route available)\n")

# config-drafts/
drafts_dir = os.path.join(workspace, "config-drafts")
os.makedirs(drafts_dir, exist_ok=True)

# Intentionally malformed / incomplete config drafts as distractors
with open(os.path.join(drafts_dir, "networks_draft_v1.json"), "w") as f:
    # Wrong schema: missing "networks" wrapper, flat structure
    json.dump({
        "lab": {"cidr": "10.0.1.0/24", "description": "Lab Network"},
        "dmz": {"cidr": "172.16.0.0/24", "description": "DMZ Network"}
    }, f, indent=2)

with open(os.path.join(drafts_dir, "networks_draft_v2.json"), "w") as f:
    # Another wrong schema: blocklist mixed into networks
    json.dump({
        "networks": {
            "lab": {"cidr": "10.0.1.0/24"},
            "dmz": {"cidr": "172.16.0.0/24"},
            "blocked_10_99": {"cidr": "10.99.0.0/24", "blocked": True}
        }
    }, f, indent=2)

with open(os.path.join(drafts_dir, "old_scan_output.txt"), "w") as f:
    f.write("Stale scan from 2024-11-01\n")
    f.write("10.0.1.1 - lab-gateway\n10.0.1.50 - lab-server01\n")

# scripts/
with open(os.path.join(scripts_dir, "archive_scan.py"), "w") as f:
    f.write("# Deprecated: old scan archiver\n# Do not use\n")

with open(os.path.join(scripts_dir, "helpers.sh"), "w") as f:
    f.write("#!/bin/bash\n# Helper utilities (unused)\n")

# inventory/
inv_dir = os.path.join(workspace, "inventory")
os.makedirs(inv_dir, exist_ok=True)

with open(os.path.join(inv_dir, "previous_lab_scan.json"), "w") as f:
    # Old format - missing required keys, distractor
    json.dump({
        "hosts": ["10.0.1.1", "10.0.1.50"],
        "date": "2024-11-01",
        "count": 2
    }, f, indent=2)

with open(os.path.join(inv_dir, "dmz_notes.txt"), "w") as f:
    f.write("DMZ: firewall at .1, proxy at .10\n")
    f.write("Do not scan 10.99.0.0/24 — there's no route from this jump host!\n")

# reports/
reports_dir = os.path.join(workspace, "reports")
os.makedirs(reports_dir, exist_ok=True)

with open(os.path.join(reports_dir, "q4_audit.md"), "w") as f:
    f.write("# Q4 Network Audit\n\n## Coverage\n- Lab: covered\n- DMZ: covered\n")
    f.write("- 10.99 range: EXCLUDED (unreachable)\n")

# automation/
auto_dir = os.path.join(workspace, "automation")
os.makedirs(auto_dir, exist_ok=True)

with open(os.path.join(auto_dir, "cron_scan.sh"), "w") as f:
    f.write("#!/bin/bash\n# Placeholder - needs to be wired up\n")
    f.write("# python3 /workspace/scripts/scan.py lab --json > /workspace/inventory/lab_inventory.json\n")
    f.write("# python3 /workspace/scripts/scan.py dmz --json > /workspace/inventory/dmz_inventory.json\n")

with open(os.path.join(auto_dir, "scan_config_notes.txt"), "w") as f:
    f.write("Requirements from IT Manager (2024-12-10):\n")
    f.write("- Named network 'lab' => 10.0.1.0/24, description: Lab Network\n")
    f.write("- Named network 'dmz' => 172.16.0.0/24, description: DMZ Network\n")
    f.write("- Block 10.99.0.0/24 - reason: No private route from this host\n")
    f.write("- Weekly JSON inventory of lab segment -> lab_inventory.json\n")
    f.write("- Network list for audit -> network_list.txt\n")

print("Workspace initialized successfully.")
print(f"Files created under {workspace}")