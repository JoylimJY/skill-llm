import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create the canonical skill directory structure
skill_dir = workspace / "skills" / "network-device-scanner" / "scripts"
skill_dir.mkdir(parents=True, exist_ok=True)

# Create a realistic scan.py that outputs deterministic "scan results" 
# in a raw, structured but non-Markdown format that the agent must process
scan_py_content = '''#!/usr/bin/env python3
"""
Network Device Scanner - scan.py
Scans LAN for active devices and open ports.
"""
import json
import sys

# Simulated scan results (deterministic for testing environment)
SCAN_RESULTS = [
    {
        "ip": "192.168.1.1",
        "mac": "e4:68:a3:11:22:33",
        "open_ports": [80, 443, 23],
        "hostname": "gateway"
    },
    {
        "ip": "192.168.1.42",
        "mac": "94:e6:f7:aa:bb:cc",
        "open_ports": [22, 80, 8080, 443],
        "hostname": "devserver"
    },
    {
        "ip": "192.168.1.77",
        "mac": "40:31:3c:de:ad:01",
        "open_ports": [80, 8080, 8443],
        "hostname": "unknown"
    },
    {
        "ip": "192.168.1.112",
        "mac": "30:9c:23:ff:ee:dd",
        "open_ports": [135, 139, 445],
        "hostname": "DESKTOP-WIN01"
    },
    {
        "ip": "192.168.1.200",
        "mac": "b8:27:eb:55:44:33",
        "open_ports": [22, 80, 9000],
        "hostname": "raspberrypi"
    }
]

if __name__ == "__main__":
    print("Scanning LAN... found {} devices.".format(len(SCAN_RESULTS)))
    print("")
    for device in SCAN_RESULTS:
        ports_str = ", ".join(str(p) for p in device["open_ports"])
        print("IP={ip}  MAC={mac}  PORTS=[{ports}]  HOST={hostname}".format(
            ip=device["ip"],
            mac=device["mac"],
            ports=ports_str,
            hostname=device["hostname"]
        ))
    print("")
    print("Scan complete.")
'''

(skill_dir / "scan.py").write_text(scan_py_content)
(skill_dir / "scan.py").chmod(0o755)

# Create a PowerShell stub
scan_ps1_content = '''# scan.ps1 - Windows stub
Write-Output "Use scan.py for full scan results."
'''
(skill_dir / "scan.ps1").write_text(scan_ps1_content)

# Create distractor files in the workspace to simulate a real project

# config files
config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "network.conf").write_text("""[network]
subnet=192.168.1.0/24
gateway=192.168.1.1
dns=8.8.8.8,8.8.4.4
scan_timeout=3
""")
(config_dir / "devices_legacy.json").write_text(json.dumps({
    "known_devices": [
        {"ip": "192.168.1.1", "label": "Router"},
        {"ip": "192.168.1.42", "label": "Server"}
    ]
}, indent=2))

# logs dir
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "scan_2024_01_15.log").write_text("""2024-01-15 09:00:01 INFO Starting scan
2024-01-15 09:00:03 INFO Found 3 devices
2024-01-15 09:00:03 INFO Scan finished
""")
(logs_dir / "scan_2024_01_16.log").write_text("""2024-01-16 09:01:11 INFO Starting scan
2024-01-16 09:01:14 INFO Found 4 devices
2024-01-16 09:01:14 INFO Scan finished
""")
(logs_dir / "error.log").write_text("2024-01-16 09:01:12 WARN arp table partially unavailable\n")

# old reports in a different format (distractor)
reports_dir = workspace / "reports" / "archive"
reports_dir.mkdir(parents=True, exist_ok=True)
(reports_dir / "Q4_2023_network_audit.txt").write_text("""Network Audit Q4 2023
=====================
Devices found: 6
Unreachable: 1
Flagged: 0
""")
(reports_dir / "Q3_2023_network_audit.txt").write_text("""Network Audit Q3 2023
=====================
Devices found: 5
Unreachable: 0
Flagged: 1
""")

# src dir with some helper scripts (distractors)
src_dir = workspace / "src"
src_dir.mkdir(exist_ok=True)
(src_dir / "parse_arp.py").write_text("""#!/usr/bin/env python3
# Helper: parse arp cache - NOT the main scanner
import subprocess
result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
print(result.stdout)
""")
(src_dir / "mac_lookup.py").write_text("""#!/usr/bin/env python3
# MAC prefix to vendor lookup (partial)
OUI = {
    "e4:68:a3": "Xiaomi",
    "94:e6:f7": "Unknown",
    "40:31:3c": "Xiaomi",
}
""")
(src_dir / "port_utils.py").write_text("""#!/usr/bin/env python3
# Generic port utilities
COMMON_PORTS = {22: 'SSH', 80: 'HTTP', 443: 'HTTPS', 445: 'SMB'}
""")

# data dir
data_dir = workspace / "data"
data_dir.mkdir(exist_ok=True)
(data_dir / "mac_prefixes.csv").write_text("""prefix,vendor,type
e4:68:a3,Xiaomi Communications,Router
40:31:3c,Xiaomi Communications,IoT
b8:27:eb,Raspberry Pi Foundation,SBC
94:e6:f7,SomeVendor,Unknown
""")
(data_dir / "port_services.csv").write_text("""port,service,protocol
21,FTP,TCP
22,SSH,TCP
23,Telnet,TCP
80,HTTP,TCP
135,MS-RPC,TCP
139,NetBIOS,TCP
443,HTTPS,TCP
445,SMB,TCP
8080,HTTP-Alt,TCP
8443,HTTPS-Alt,TCP
9000,Portainer,TCP
""")

# docs dir
docs_dir = workspace / "docs"
docs_dir.mkdir(exist_ok=True)
(docs_dir / "architecture.md").write_text("""# Network Scanner Architecture

## Components
- scan.py: Main scanner entry point
- parse_arp.py: ARP cache reader
- mac_lookup.py: Vendor identification

## Flow
1. Discover devices via ARP / ping sweep
2. Port scan discovered IPs
3. Identify device type
4. Output formatted report
""")
(docs_dir / "changelog.txt").write_text("""v1.2.0 - Added MAC prefix detection
v1.1.0 - Added port scanning
v1.0.0 - Initial release
""")

# tests dir
tests_dir = workspace / "tests"
tests_dir.mkdir(exist_ok=True)
(tests_dir / "test_scan.py").write_text("""import unittest
class TestScan(unittest.TestCase):
    def test_placeholder(self):
        pass
""")
(tests_dir / "fixtures" / "sample_arp.txt").parent.mkdir(exist_ok=True)
(tests_dir / "fixtures" / "sample_arp.txt").write_text("""? (192.168.1.1) at e4:68:a3:11:22:33 [ether] on eth0
? (192.168.1.42) at 94:e6:f7:aa:bb:cc [ether] on eth0
""")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")