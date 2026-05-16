import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic deeply nested directory structure with distractor files ---

dirs = [
    "network_planning/office_deployments/london",
    "network_planning/office_deployments/berlin",
    "network_planning/datacenter/rack_a",
    "network_planning/datacenter/rack_b",
    "legacy_exports/2021_Q4",
    "legacy_exports/2022_Q1",
    "legacy_exports/2022_Q2",
    "tools/scripts",
    "tools/configs",
    "audit_reports/drafts",
    "audit_reports/final",
    "misc/temp",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "network_planning/office_deployments/london/vlan_config.txt": "VLAN 10: 192.168.10.0/24\nVLAN 20: 192.168.20.0/24\n",
    "network_planning/office_deployments/berlin/switch_inventory.csv": "hostname,ip,model\nbrl-sw-01,10.20.1.1,Cisco 2960\nbrl-sw-02,10.20.1.2,Cisco 2960\n",
    "network_planning/datacenter/rack_a/patch_panel.txt": "Port 1: Server A\nPort 2: Server B\nPort 3: Storage NAS\n",
    "network_planning/datacenter/rack_b/power_draw.log": "2024-01-10 12:00: 2.1kW\n2024-01-10 13:00: 2.3kW\n",
    "legacy_exports/2021_Q4/old_dhcp_leases.txt": "192.168.1.50 aa:bb:cc:dd:ee:ff hostname1\n10.0.0.5 11:22:33:44:55:66 hostname2\n",
    "legacy_exports/2022_Q1/firewall_rules_backup.cfg": "permit ip 10.0.0.0/8 any\ndeny ip 192.168.0.0/16 any\n",
    "legacy_exports/2022_Q2/nat_table.txt": "Inside: 10.0.0.10 <-> Outside: 203.0.113.5\n",
    "tools/scripts/ping_sweep.sh": "#!/bin/bash\nfor i in $(seq 1 254); do ping -c 1 192.168.1.$i; done\n",
    "tools/configs/dhcp.conf": "subnet 10.0.1.0 netmask 255.255.255.0 {\n  range 10.0.1.10 10.0.1.200;\n}\n",
    "misc/temp/scratch.txt": "TODO: check IP allocations for new office\n",
    "audit_reports/drafts/template.md": "# Network Audit Report\n## Date:\n## Prepared by:\n## Scope:\n",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.write_text(content)

# --- Create the main problem input: messy IP candidate list ---
# A CSV export from a legacy spreadsheet with mixed valid/invalid IPs
# Some IPs are invalid (bad octets, wrong format, extra spaces, etc.)
ip_candidates_content = """device_name,candidate_ip,notes
office-printer-01,10.0.1.5,floor 1 printer
office-printer-02,10.0.1.6,floor 2 printer
confroom-ap-01,10.0.1.300,bad octet
security-cam-01,10.0.1.15,lobby camera
security-cam-02,10.0.1.16,parking camera
ntp-server,999.1.1.1,external NTP candidate
voip-phone-01,10.0.1.20,reception desk
voip-phone-02,10.0.1.abc,corrupted entry
mgmt-switch,10.0.1.1,core switch mgmt
backup-nas,10.0.1.50,NAS appliance
guest-ap-01,10.0.1.55,guest wifi AP
firewall-inside,10.0.1.-1,corrupted
dev-laptop-01,10.0.1.88,developer workstation
dev-laptop-02,10.0.1.89,developer workstation
test-vm-01,10.0.1.100,QA test VM
"""

(workspace / "legacy_exports" / "2022_Q2" / "new_office_ip_candidates.csv").write_text(ip_candidates_content)

# --- Create the subnet planning brief ---
subnet_brief_content = """New Office Network Planning Brief
===================================
Site: London - New Building Wing B

Target Subnet Block: 10.0.1.0/24

Key Range of Interest:
  Start IP: 10.0.1.1
  End IP: 10.0.1.100

Action Items:
1. Validate all candidate IPs from the attached spreadsheet export.
2. Obtain full subnet details for the target block.
3. Enumerate all IPs in the key range of interest.
4. Consolidate findings into a report for the network team.

Note: The IP candidate list is from a legacy export and may contain 
corrupted or invalid entries that must be filtered out.
"""

(workspace / "network_planning" / "office_deployments" / "london" / "subnet_planning_brief.txt").write_text(subnet_brief_content)

print("Workspace setup complete.")
print("Problem files created:")
print("  - legacy_exports/2022_Q2/new_office_ip_candidates.csv")
print("  - network_planning/office_deployments/london/subnet_planning_brief.txt")