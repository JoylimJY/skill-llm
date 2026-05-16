import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "references",
    "network/logs",
    "network/configs",
    "tickets/open",
    "tickets/closed",
    "assets/icons",
    "assets/screenshots",
    "tools/scripts",
    "tools/templates",
    "docs/onboarding",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "network/logs/vpn_events_2024.log": (
        "2024-03-01 09:12 INFO  Peer connected: win-workstation-01\n"
        "2024-03-01 09:13 INFO  Peer connected: mac-designer-02\n"
        "2024-03-02 14:45 WARN  Peer unreachable: mac-designer-02\n"
        "2024-03-02 14:46 INFO  Retrying handshake…\n"
    ),
    "network/configs/firewall_rules_old.txt": (
        "# Legacy firewall rules — DO NOT USE\n"
        "allow tcp from 192.168.1.0/24 to any port 22\n"
        "allow tcp from 192.168.1.0/24 to any port 5900\n"
        "deny all\n"
    ),
    "network/configs/network_topology.md": (
        "# Network Topology\n\n"
        "- HQ Windows desktops: 10.0.0.0/24\n"
        "- Remote Mac fleet: Tailscale IPs 100.x.x.x\n"
        "- Jump host: not available\n"
    ),
    "tickets/open/INC-2041.txt": (
        "INCIDENT: mac-designer-04 unreachable\n"
        "Reporter: alice@agency.com\n"
        "Date: 2024-06-10\n"
        "Status: OPEN\n"
        "Description: Designer cannot be reached via remote desktop since yesterday.\n"
    ),
    "tickets/open/INC-2042.txt": (
        "INCIDENT: mac-designer-07 SSH works but screen share fails\n"
        "Reporter: bob@agency.com\n"
        "Date: 2024-06-11\n"
        "Status: OPEN\n"
        "Description: IT confirmed SSH on port 22 succeeds. VNC on port 5900 times out.\n"
    ),
    "tickets/closed/INC-1998.txt": (
        "INCIDENT: Windows workstation cannot ping Mac fleet\n"
        "Resolution: Tailscale ACL was missing accept rule for ICMP.\n"
        "Closed: 2024-05-01\n"
    ),
    "tools/scripts/health_check.sh": (
        "#!/bin/bash\n"
        "# Placeholder health-check script\n"
        "echo 'Checking reachability…'\n"
        "ping -c 1 $1 && echo 'Host reachable' || echo 'Host unreachable'\n"
    ),
    "tools/templates/incident_template.md": (
        "# Incident Report Template\n\n"
        "**ID:**\n**Date:**\n**Severity:**\n**Summary:**\n**Root Cause:**\n**Resolution:**\n"
    ),
    "docs/onboarding/new_hire_mac_setup.md": (
        "# New Hire Mac Setup\n\n"
        "1. Install Tailscale from tailscale.com\n"
        "2. Authenticate with company Google account\n"
        "3. Contact IT to join the tailnet\n"
    ),
    "assets/icons/.gitkeep": "",
    "assets/screenshots/.gitkeep": "",
}
for rel, content in distractors.items():
    (WORKSPACE / rel).write_text(content)

# ── skill reference files (exist in workspace per SKILL.md) ──────────────────

(WORKSPACE / "references" / "acl-template.md").write_text(
    """# Minimal Tailscale ACL Template

Use this as a starting point for troubleshooting. This is the minimal working
example that allows Windows clients to reach Mac hosts over the tailnet.

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:windows-client"],
      "dst": ["tag:mac-host:22", "tag:mac-host:5900"]
    }
  ],
  "tagOwners": {
    "tag:windows-client": ["autogroup:admin"],
    "tag:mac-host": ["autogroup:admin"]
  }
}
```

**Notes:**
- Always include port 22 alongside any GUI port so SSH fallback is preserved.
- Use tags rather than raw IP CIDRs in production ACLs.
- Apply the minimal ACL first, verify connectivity, then layer on restrictions.
"""
)

(WORKSPACE / "references" / "checklist.md").write_text(
    """# Remote Access Baseline Checklist

## Mac side
- [ ] Tailscale is running and authenticated (`tailscale status`)
- [ ] Tailscale IPv4 obtained (`tailscale ip -4`)
- [ ] Remote Login (SSH) enabled (`sudo systemsetup -getremotelogin`)
- [ ] Screen Sharing service listening on 5900
      (`sudo /usr/sbin/netstat -anv -p tcp | grep '\.5900 .*LISTEN'`)

## Windows side
- [ ] Test-NetConnection <Mac-IP> -Port 22   → TcpTestSucceeded : True
- [ ] Test-NetConnection <Mac-IP> -Port 5900 → TcpTestSucceeded : True

## ACL
- [ ] Tailscale ACL explicitly allows src tag → dst tag:22 and tag:5900
- [ ] Tags assigned correctly to both endpoint types

## Recovery paths
- [ ] SSH access confirmed working
- [ ] AnyDesk installed and unattended-access password set (primary GUI fallback)
- [ ] VNC client tested as secondary GUI fallback
"""
)

(WORKSPACE / "references" / "sop.md").write_text(
    """# End-to-End Remote Access SOP

## Objective
Establish and verify remote access from a Windows workstation to a Mac over Tailscale.

## Step 1 — Mac-side verification
Run all Mac-side checks listed in the checklist.
Confirm `tailscale status` shows the Mac as an active peer.

## Step 2 — TCP reachability test from Windows
Use Test-NetConnection (PowerShell) for ports 22 and 5900.
Do NOT rely on ping; ICMP may be blocked by ACL.

## Step 3 — ACL review
If both ports fail  → fix ACL first (see acl-template.md).
If port 22 passes and port 5900 fails → skip ACL; go to Step 4.
If both ports pass  → move to client-side auth / compatibility.

## Step 4 — Screen Sharing recovery on Mac
If TCP 5900 is closed despite Screen Sharing appearing enabled:
  sudo launchctl kickstart -k system/com.apple.screensharing

## Step 5 — Layered access stack
Maintain three layers in priority order:
  1. SSH (command-line fallback — MUST be preserved at all times)
  2. AnyDesk (primary GUI fallback)
  3. VNC / Screen Sharing (secondary GUI fallback)

Never remove SSH access when troubleshooting GUI tools.
"""
)

(WORKSPACE / "references" / "anydesk-rustdesk.md").write_text(
    """# GUI Fallback: AnyDesk & RustDesk

## AnyDesk (Recommended primary GUI fallback)

### Installation (Mac)
Download from https://anydesk.com/en/downloads/mac-os
Grant Accessibility and Screen Recording permissions in System Settings.

### Unattended access
Set a password under Settings → Security → Unattended Access.
Note the 9-digit AnyDesk ID; share it with IT.

### Troubleshooting
- If the AnyDesk window is blank: revoke and re-grant Screen Recording permission.
- Service restart: `launchctl kickstart -k gui/$(id -u)/com.anydesk.anydesk`

## RustDesk (Open-source alternative)

### Installation
brew install --cask rustdesk

### Self-hosted relay
Point both client and host to your relay server in Settings → Network.

## VNC / Screen Sharing (secondary fallback)

Built-in macOS Screen Sharing is acceptable as a secondary option.
Prefer AnyDesk over VNC because VNC requires port 5900 to be reachable through
the Tailscale ACL, whereas AnyDesk uses an outbound relay and is more
firewall-friendly.

When all else fails, re-enable Screen Sharing via:
  sudo launchctl kickstart -k system/com.apple.screensharing
"""
)

# ── the messy problem input ───────────────────────────────────────────────────
# A raw, ambiguous incident brief that the agent must interpret
(WORKSPACE / "incident_brief.txt").write_text(
    """INCIDENT BRIEF — INC-2042 escalation
Submitted by: Bob (IT Support Lead)
Date: 2024-06-11

The remote designer's Mac (Tailscale IP: 100.101.102.103) appears healthy in
the network overlay dashboard — it shows as "Connected". From the Windows
support workstation we CAN open a terminal session successfully. However every
attempt to launch a graphical remote-desktop session to the same machine on the
standard display port fails with a connection timeout. This has been happening
since a macOS update last night.

We need:
 A. A structured runbook (recovery_runbook.md) that:
    - States the exact diagnosis (what the port test results mean per our
      standard interpretation table).
    - Lists every Mac-side command to run, in order.
    - Includes the single specific service-restart command for the stuck
      graphical-access daemon.
    - Documents the correct priority-ordered layered access stack we should
      maintain going forward.
 B. A Tailscale ACL policy file (tailscale_acl.json) that represents the
    minimal working configuration for this environment, using the correct
    tag-based structure.

Please produce both artifacts so we can close this ticket and update our SOP.
"""
)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")