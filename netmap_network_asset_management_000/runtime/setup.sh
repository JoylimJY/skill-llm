#!/bin/bash
set -e

# Create the scripts directory if it doesn't exist
mkdir -p /workspace/scripts

# Create the mock netmap.py script that simulates real behavior
# This script operates on the actual ~/.config/netmap/devices.json database
cat > /workspace/scripts/netmap.py << 'NETMAP_SCRIPT'
#!/usr/bin/env python3
"""
netmap - Network device scanner and tracker
Manages device database at ~/.config/netmap/devices.json
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path.home() / ".config" / "netmap" / "devices.json"

def load_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        with open(DB_PATH) as f:
            return json.load(f)
    return {"devices": {}}

def save_db(db):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def cmd_scan(args):
    """Simulate a scan — in mock mode, just update last_seen for existing devices."""
    db = load_db()
    now = datetime.now().isoformat()
    subnet = getattr(args, 'subnet', None) or "192.168.1.0/24"
    deep = getattr(args, 'deep', False)
    
    print(f"Scanning subnet: {subnet}")
    if deep:
        print("Deep scan mode: port scanning enabled for device fingerprinting...")
    
    # Update last_seen for all existing devices (simulate rediscovery)
    for ip, dev in db["devices"].items():
        dev["last_seen"] = now
    
    save_db(db)
    count = len(db["devices"])
    print(f"Scan complete. Found {count} device(s).")
    if deep:
        print("Device types identified via port fingerprinting.")

def cmd_list(args):
    db = load_db()
    devices = db.get("devices", {})
    show_times = getattr(args, 'times', False)
    
    if not devices:
        print("No devices found. Run 'scan' first.")
        return
    
    print(f"{'IP':<18} {'MAC':<20} {'HOSTNAME':<28} {'VENDOR':<22} {'TYPE':<14} {'LABEL'}")
    print("-" * 120)
    for ip, dev in sorted(devices.items(), key=lambda x: tuple(int(p) for p in x[0].split('.'))):
        label = dev.get('label', '') or ''
        print(f"{dev['ip']:<18} {dev.get('mac',''):<20} {dev.get('hostname',''):<28} {dev.get('vendor',''):<22} {dev.get('type',''):<14} {label}")
        if show_times:
            print(f"  {'':>18} first_seen: {dev.get('first_seen','')}  last_seen: {dev.get('last_seen','')}")

def cmd_find(args):
    db = load_db()
    devices = db.get("devices", {})
    query = args.query.lower()
    
    found = []
    for ip, dev in devices.items():
        searchable = " ".join([
            dev.get('ip',''),
            dev.get('mac',''),
            dev.get('hostname',''),
            dev.get('vendor',''),
            dev.get('type',''),
            dev.get('label','') or ''
        ]).lower()
        if query in searchable:
            found.append(dev)
    
    if not found:
        print(f"No devices found matching '{args.query}'")
        return
    
    for dev in found:
        label = dev.get('label', '') or ''
        label_str = f"  [{label}]" if label else ""
        print(f"{dev['ip']:<18} {dev.get('mac',''):<20} {dev.get('hostname',''):<28} {dev.get('vendor',''):<20} {dev.get('type','')}{label_str}")

def cmd_label(args):
    db = load_db()
    devices = db.get("devices", {})
    identifier = args.identifier
    friendly_name = args.friendly_name
    
    # Try matching by IP first
    if identifier in devices:
        devices[identifier]['label'] = friendly_name
        save_db(db)
        print(f"Labeled {identifier} as '{friendly_name}'")
        return
    
    # Try matching by MAC address (case-insensitive)
    mac_query = identifier.upper()
    for ip, dev in devices.items():
        if dev.get('mac', '').upper() == mac_query:
            dev['label'] = friendly_name
            save_db(db)
            print(f"Labeled {dev['ip']} ({identifier}) as '{friendly_name}'")
            return
    
    print(f"Error: No device found with IP or MAC '{identifier}'", file=sys.stderr)
    sys.exit(1)

def cmd_new(args):
    db = load_db()
    devices = db.get("devices", {})
    minutes = getattr(args, 'minutes', 30)
    
    cutoff = datetime.now() - timedelta(minutes=minutes)
    
    new_devices = []
    for ip, dev in devices.items():
        first_seen_str = dev.get('first_seen', '')
        if first_seen_str:
            try:
                first_seen = datetime.fromisoformat(first_seen_str)
                if first_seen >= cutoff:
                    new_devices.append(dev)
            except ValueError:
                pass
    
    if not new_devices:
        print(f"No new devices found in the last {minutes} minute(s).")
        return
    
    print(f"Devices first seen in the last {minutes} minute(s):")
    for dev in sorted(new_devices, key=lambda d: d.get('first_seen','')):
        label = dev.get('label', '') or ''
        label_str = f"  [{label}]" if label else ""
        print(f"  {dev['ip']:<18} {dev.get('mac',''):<20} {dev.get('hostname',''):<28} {dev.get('vendor','')}{label_str}")

def cmd_export(args):
    db = load_db()
    print(json.dumps(db, indent=2))

def cmd_watch(args):
    import time
    interval = getattr(args, 'interval', 120)
    print(f"Watch mode: scanning every {interval}s. Press Ctrl+C to stop.")
    # In mock mode, just do one scan and exit for non-interactive use
    class ScanArgs:
        deep = False
        subnet = None
    cmd_scan(ScanArgs())

def main():
    parser = argparse.ArgumentParser(description='netmap - Network device scanner')
    subparsers = parser.add_subparsers(dest='command')
    
    # scan
    scan_p = subparsers.add_parser('scan')
    scan_p.add_argument('--deep', action='store_true')
    scan_p.add_argument('--subnet', type=str, default=None)
    
    # list
    list_p = subparsers.add_parser('list')
    list_p.add_argument('--times', action='store_true')
    
    # find
    find_p = subparsers.add_parser('find')
    find_p.add_argument('query')
    
    # label
    label_p = subparsers.add_parser('label')
    label_p.add_argument('identifier')
    label_p.add_argument('friendly_name')
    
    # new
    new_p = subparsers.add_parser('new')
    new_p.add_argument('--minutes', type=int, default=30)
    
    # export
    export_p = subparsers.add_parser('export')
    
    # watch
    watch_p = subparsers.add_parser('watch')
    watch_p.add_argument('--interval', type=int, default=120)
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'find':
        cmd_find(args)
    elif args.command == 'label':
        cmd_label(args)
    elif args.command == 'new':
        cmd_new(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'watch':
        cmd_watch(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
NETMAP_SCRIPT

chmod +x /workspace/scripts/netmap.py

# Copy the device database to the actual home config location
mkdir -p /root/.config/netmap
cp /workspace/.config/netmap/devices.json /root/.config/netmap/devices.json

echo "Setup complete."
echo "Device database installed at: /root/.config/netmap/devices.json"
echo "netmap script ready at: /workspace/scripts/netmap.py"
python3 /workspace/scripts/netmap.py list