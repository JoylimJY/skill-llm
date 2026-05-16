import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Distractor files (irrelevant noise) ──────────────────────────────────────
distractors = {
    "wifi_channels.txt": "Channel 1: congested\nChannel 6: moderate\nChannel 11: clear\nRecommend: 11",
    "router_models.csv": "model,firmware,band\nASUS RT-AX88U,3.0.0.4.386,dual\nNetgear R7000,1.0.11.116,dual\nTP-Link Archer AX73,1.2.1,tri",
    "vpn_config_notes.txt": "OpenVPN port 1194\nWireGuard port 51820\nDo not mix with ISP diagnostics",
    "mesh_setup_log.txt": "Node 1 paired at 10:32\nNode 2 failed pairing — retry at 10:45\nNode 2 success",
    "wifi_security_audit.json": json.dumps({"wpa2": True, "wps_enabled": False, "hidden_ssid": False}),
    "network_infra_notes.md": "# Infrastructure\nSwitch: Cisco SG350\nPatch panel: 24-port\nCabling: Cat6",
    "dns_benchmark_old.txt": "8.8.8.8: 12ms\n1.1.1.1: 9ms\n9.9.9.9: 15ms\nNote: this data is 18 months old",
    "qos_wishlist.txt": "Want QoS for gaming on Unit 4B\nRouter model unknown — need to check first",
    "tethering_policy.txt": "Residents may tether up to 5 devices\nNo BitTorrent permitted\nThrottle after 50GB",
    "esim_compatibility_matrix.csv": "device,esim_support\niPhone 14,yes\nSamsung S21,yes\nMoto G7,no\nPixel 6,yes",
    "internal_tickets/ticket_001.txt": "Reported by: Unit 3A\nDate: 2024-01-15\nIssue: slow streaming",
    "internal_tickets/ticket_002.txt": "Reported by: Unit 7C\nDate: 2024-02-20\nIssue: intermittent drops",
    "internal_tickets/ticket_003.txt": "Reported by: Unit 2B\nDate: 2024-03-10\nIssue: no connection after router reset",
    "archive/old_provider_deal_2021.txt": "ClearLink promo 2021: $29.99/mo for 6mo then $64.99 — EXPIRED",
    "archive/speedtest_archive_2022.csv": "date,down_mbps,up_mbps\n2022-01-10,45.2,8.1\n2022-03-22,38.9,7.4",
}

for rel_path, content in distractors.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ── PRIMARY INPUT 1: Provider quotes (messy, raw notes format) ────────────────
# Deliberately messy — includes promo rates, buried post-promo rates, ETF buried in text
provider_quotes_raw = """\
=== PROVIDER QUOTES RECEIVED 2024-04-01 ===

Provider: FiberNow
Tier: 500 Mbps / 500 Mbps (symmetric fiber)
Promo rate: $39.99/month for first 12 months
After promo: $74.99/month
Contract length: 24 months
Early termination fee: $180 flat
Notes: Includes modem/router combo rental ($0 during promo, $9.99/mo after promo ends)

---

Provider: CableZone
Tier: 600 Mbps down / 25 Mbps up (cable DOCSIS 3.1)
Promo rate: $49.99/month for first 6 months
After promo: $89.99/month
Contract length: 24 months
Early termination fee: $15 per remaining month in contract
Notes: Equipment rental $12/month throughout. No symmetric upload.

---

Provider: DSL-Direct
Tier: 100 Mbps down / 20 Mbps up (DSL bonded pair)
Rate: $34.99/month (no promo — this is standard rate)
Contract length: 12 months then month-to-month
Early termination fee: $50 flat
Notes: Equipment included. Speed varies by line quality — may be lower at property address.

---

Provider: FiberNow Premium
Tier: 1000 Mbps / 1000 Mbps (symmetric fiber)
Promo rate: $59.99/month for first 12 months  
After promo: $99.99/month
Contract length: 24 months
Early termination fee: $240 flat
Notes: Equipment included. Business-grade SLA. Includes static IP.
"""

(workspace / "provider_quotes_raw.txt").write_text(provider_quotes_raw)

# ── PRIMARY INPUT 2: Speedtest logs (raw, mixed format, some missing fields) ──
speedtest_logs_raw = """\
# Speedtest logs for Unit 5 — contracted plan: 500 Mbps down / 500 Mbps up with FiberNow
# Format varies because different staff members recorded these

2024-03-01 09:14 | down: 487.3 Mbps | up: 491.2 Mbps | ping: 8ms | packet_loss: 0% | note: normal morning
2024-03-05 14:30 | down: 102.4 Mbps | up: 98.1 Mbps | ping: 45ms | packet_loss: 3.2% | note: resident complained slow
2024-03-05 14:55 | down: 98.7 Mbps | up: 95.3 Mbps | ping: 48ms | packet_loss: 4.1% | note: second test same issue
2024-03-07 10:00 | down: 450.1 Mbps | up: 445.8 Mbps | ping: 9ms | packet_loss: 0% | note: seems back to normal
2024-03-12 19:45 | down: 312.5 Mbps | up: 298.0 Mbps | ping: 22ms | packet_loss: 0.8% | note: evening slowdown
2024-03-18 08:00 | down: 55.2 Mbps | up: 51.8 Mbps | ping: 120ms | packet_loss: 11.5% | note: complete degradation reported by unit 5A and 5B
2024-03-18 08:30 | down: 48.9 Mbps | up: 44.2 Mbps | ping: 135ms | packet_loss: 13.2% | note: called ISP hold 42min no resolution
2024-03-18 11:00 | down: 51.1 Mbps | up: 49.0 Mbps | ping: 128ms | packet_loss: 12.8% | note: ISP claims no outage in area
2024-03-18 15:30 | down: 489.2 Mbps | up: 478.1 Mbps | ping: 8ms | packet_loss: 0% | note: service restored no explanation given
2024-03-22 21:00 | down: 188.4 Mbps | up: 180.2 Mbps | ping: 31ms | packet_loss: 0.2% | note: moderate evening slowdown
2024-03-25 07:30 | down: 501.3 Mbps | up: 498.7 Mbps | ping: 7ms | packet_loss: 0% | note: normal
2024-04-02 13:15 | down: 340.2 Mbps | up: 330.1 Mbps | ping: 18ms | packet_loss: 0.1% | note: slight dip unremarkable
"""

(workspace / "speedtest_logs_unit5.txt").write_text(speedtest_logs_raw)

# ── PRIMARY INPUT 3: Outage incident notes (totally unstructured) ─────────────
outage_notes_raw = """\
march 5th afternoon – a resident in unit 5 called saying everything was sluggish. we ran tests around 2:30pm and got about 100 meg down, way below normal. tried rebooting the ONT box, no change. issue lasted from roughly 2pm to about 5pm per the resident. ticket opened with ISP, no callback received.

march 18 morning – woke up to 3 complaints from unit 5A and 5B both saying no connection. measured at 8am, only getting 50 megs, huge packet loss over 11%. called ISP spent 42 minutes on hold and they said no outage detected. ran three more tests — all terrible. then at 3:30pm it just came back. ISP never explained. total outage duration approx 7.5 hours. we logged all the speed readings.

april 2 midday – small dip noticed around 1:15pm, download was 340 megs, not alarming but logged it. ping was 18ms, no packet loss. back to normal within 30 minutes. probably not ISP fault — maybe local congestion.
"""

(workspace / "outage_notes_raw.txt").write_text(outage_notes_raw)

# ── Skill documentation directory (SKILL.md content) ─────────────────────────
skills_dir = workspace / "skills" / "internet"
skills_dir.mkdir(parents=True, exist_ok=True)

skill_md = """\
---
name: Internet
slug: internet
version: 1.0.0
description: Manage internet connectivity, compare providers, diagnose issues, optimize performance, and handle mobile data when away from home.
metadata: {"clawdbot":{"emoji":"🌐","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

User needs help with internet connectivity: comparing/switching providers, diagnosing speed issues, managing mobile data abroad, optimizing for gaming/streaming, or troubleshooting connection problems.

## Quick Reference

| Topic | File |
|-------|------|
| Provider comparison | `providers.md` |
| Diagnostics | `diagnostics.md` |
| Mobile connectivity | `mobile.md` |
| Performance optimization | `performance.md` |

## Core Rules

### 1. Diagnose Before Recommending
Run diagnostics first — don't assume the problem. Check:
- Speedtest vs contracted speed (flag if <70%)
- Packet loss and jitter
- DNS resolution time
- Whether issue is local, ISP, or destination

### 2. Provider Comparison Must Include Hidden Costs
When comparing providers:
- Show price AFTER promotional period ends
- Include early termination penalties
- Calculate total 24-month cost, not monthly
- Check coverage at user's exact address first

### 3. Mobile Data: Verify Before Activating
Before recommending eSIM/roaming:
- Confirm device eSIM compatibility
- Check destination country coverage
- Compare local SIM vs international eSIM vs roaming
- Alert user to data caps and throttling thresholds

### 4. Performance Claims Need Verification
For gaming/streaming optimization:
- Measure actual latency to game servers, not generic ping
- QoS changes require router admin access
- Bufferbloat is real — test with loaded connection
- "Faster DNS" rarely matters for speed, only for reliability

### 5. Keep History for ISP Disputes
Log incidents with timestamps:
- Date, time, duration of outages
- Speedtest results during issues
- Steps already attempted
- This evidence helps when escalating to ISP

## Common Traps

- Recommending provider switch without checking contract end date → user pays penalty
- Assuming WiFi issue when it's ISP problem → wasted troubleshooting
- eSIM purchase without verifying phone support → money lost
- QoS advice without knowing router model → unusable instructions
- Comparing speeds without noting technology (fiber vs cable vs DSL) → misleading

## Scope

This skill handles:
- ISP selection, comparison, and contract analysis
- Connection diagnostics and troubleshooting
- Mobile data management (eSIM, roaming, tethering)
- Performance optimization for specific use cases

This skill does NOT handle:
- WiFi-specific issues (channel optimization, security) → use `wifi` skill
- Network infrastructure setup (routers, mesh systems)
- VPN configuration or privacy tools
"""

(skills_dir / "SKILL.md").write_text(skill_md)

# ── Additional distractor skills dirs ─────────────────────────────────────────
for skill_name in ["wifi", "vpn", "mesh"]:
    d = workspace / "skills" / skill_name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"# {skill_name.upper()} Skill\nThis is a stub for the {skill_name} skill.")

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")