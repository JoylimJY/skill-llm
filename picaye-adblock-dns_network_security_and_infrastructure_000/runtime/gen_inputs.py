import os
import json
import random

random.seed(42)

# Create the main skill directory structure
base = "/workspace"

# Simulate a realistic skills/adblock directory tree
dirs = [
    "skills/adblock/scripts",
    "skills/adblock/data",
    "skills/adblock/logs",
    "skills/adblock/tests",
    "skills/network-monitor/data",
    "skills/network-monitor/scripts",
    "skills/vpn-manager/config",
    "skills/vpn-manager/scripts",
    "skills/firewall/rules",
    "ops/deployments",
    "ops/audits/2024",
    "ops/audits/2023",
    "docs/runbooks",
    "docs/architecture",
    "tmp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ---- CORE SKILL FILES ----

# The real config.json with DEFAULT values (agent must change upstream to 8.8.8.8 and apiPort to 9053)
config = {
    "upstream": "1.1.1.1",
    "port": 53,
    "apiPort": 8053
}
with open(os.path.join(base, "skills/adblock/data/config.json"), "w") as f:
    json.dump(config, f, indent=2)

# Existing whitelist with a couple of domains already in it
with open(os.path.join(base, "skills/adblock/data/whitelist.txt"), "w") as f:
    f.write("internal.corp.local\n")
    f.write("erp.acmecorp.com\n")

# Existing custom-blacklist with one domain
with open(os.path.join(base, "skills/adblock/data/custom-blacklist.txt"), "w") as f:
    f.write("malware-hub.net\n")

# stats.json with realistic but stale data
stats = {
    "totalQueries": 48201,
    "blockedQueries": 9344,
    "blockPercentage": 19.38,
    "topBlockedDomains": [
        {"domain": "doubleclick.net", "count": 1203},
        {"domain": "ads.google.com", "count": 987},
        {"domain": "tracking.amazon.com", "count": 654},
        {"domain": "px.ads.linkedin.com", "count": 432},
        {"domain": "bat.bing.com", "count": 299}
    ]
}
with open(os.path.join(base, "skills/adblock/data/stats.json"), "w") as f:
    json.dump(stats, f, indent=2)

# Minimal blocklist stub
with open(os.path.join(base, "skills/adblock/data/blocklist.txt"), "w") as f:
    f.write("doubleclick.net\n")
    f.write("ads.google.com\n")
    f.write("tracking.amazon.com\n")
    f.write("px.ads.linkedin.com\n")
    f.write("bat.bing.com\n")
    f.write("criteo.com\n")
    f.write("rubiconproject.com\n")
    f.write("adnxs.com\n")
    f.write("scorecardresearch.com\n")
    f.write("googlesyndication.com\n")

# ---- DISTRACTOR FILES ----

# A fake old config from 2023 audit
with open(os.path.join(base, "ops/audits/2023/dns_config_backup.json"), "w") as f:
    json.dump({"upstream": "8.8.4.4", "port": 53, "apiPort": 7053}, f, indent=2)

# A network monitor config
with open(os.path.join(base, "skills/network-monitor/data/config.json"), "w") as f:
    json.dump({"listenPort": 9090, "logLevel": "info"}, f, indent=2)

# VPN manager config
with open(os.path.join(base, "skills/vpn-manager/config/vpn.conf"), "w") as f:
    f.write("[Interface]\nListenPort = 51820\nPrivateKey = PLACEHOLDER\n")

# Firewall rules
with open(os.path.join(base, "skills/firewall/rules/inbound.rules"), "w") as f:
    f.write("ALLOW tcp 22\nALLOW tcp 443\nALLOW tcp 80\nDENY ALL\n")

# Old deployment notes
with open(os.path.join(base, "ops/deployments/deployment_notes.txt"), "w") as f:
    f.write("2024-01-15: Deployed adblock DNS v1.2. Default config. Upstream 1.1.1.1\n")
    f.write("2024-03-20: Added 5 custom blacklist entries\n")
    f.write("Note: API runs on 8053 by default. Do NOT expose to internet.\n")

# Runbook (generic, no hints)
with open(os.path.join(base, "docs/runbooks/network_ops.md"), "w") as f:
    f.write("# Network Operations Runbook\n\n")
    f.write("## DNS\nEnsure DNS servers are reachable before troubleshooting.\n")
    f.write("## VPN\nVerify tunnels are up with ping tests.\n")

# Architecture doc
with open(os.path.join(base, "docs/architecture/overview.md"), "w") as f:
    f.write("# Architecture Overview\n\nThree-tier: edge, app, data.\n")

# Scratch files
with open(os.path.join(base, "tmp/scratch/notes.txt"), "w") as f:
    f.write("TODO: update all upstream DNS to Google 8.8.8.8 for new office deployment\n")
    f.write("TODO: whitelist payroll.acmecorp.com\n")
    f.write("TODO: block telemetry.spyware-vendor.com and ads.badnetwork.io\n")
    f.write("TODO: run audit and produce report\n")

# Fake stats from network monitor (distractor)
with open(os.path.join(base, "skills/network-monitor/data/stats.json"), "w") as f:
    json.dump({"packets": 10000, "dropped": 12}, f)

# A second fake config.json at wrong path (distractor)
with open(os.path.join(base, "skills/adblock/scripts/old_config.json"), "w") as f:
    json.dump({"upstream": "9.9.9.9", "port": 53, "apiPort": 8053}, f, indent=2)

# Adblock test script stub (distractor, not real)
with open(os.path.join(base, "skills/adblock/tests/test_dns.sh"), "w") as f:
    f.write("#!/bin/bash\n# Placeholder test script\necho 'DNS tests not implemented'\n")

# Log files
with open(os.path.join(base, "skills/adblock/logs/adblock.log"), "w") as f:
    f.write("[2024-06-01 08:00:01] DNS server started on port 53\n")
    f.write("[2024-06-01 08:00:02] Stats API started on port 8053\n")
    f.write("[2024-06-01 09:15:33] BLOCKED ads.google.com\n")
    f.write("[2024-06-01 09:15:44] ALLOWED google.com\n")
    f.write("[2024-06-01 10:02:11] BLOCKED doubleclick.net\n")

print("Workspace generated successfully.")
print("Key files:")
print("  - skills/adblock/data/config.json (needs upstream->8.8.8.8, apiPort->9053)")
print("  - skills/adblock/data/whitelist.txt (needs payroll.acmecorp.com added)")
print("  - skills/adblock/data/custom-blacklist.txt (needs new domains added)")
print("  - Agent must produce: dns_audit_report.json")