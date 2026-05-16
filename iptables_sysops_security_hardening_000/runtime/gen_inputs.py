import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── 1. Create a realistic directory structure with distractor files ──────────

dirs = [
    "scripts",
    "configs/nginx",
    "configs/ssh",
    "configs/firewall",
    "logs/audit",
    "logs/syslog",
    "docs/runbooks",
    "docs/architecture",
    "deploy/staging",
    "deploy/production",
    "monitoring/alerts",
    "monitoring/dashboards",
    "backups/weekly",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "configs/nginx/nginx.conf": """\
worker_processes auto;
events { worker_connections 1024; }
http {
    server {
        listen 80;
        server_name example.com;
        root /var/www/html;
    }
}
""",
    "configs/ssh/sshd_config": """\
Port 22
PermitRootLogin no
PasswordAuthentication yes
""",
    "configs/firewall/old_rules.v4": """\
# Old iptables backup - DO NOT USE
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
COMMIT
""",
    "logs/audit/audit.log": """\
type=SYSCALL msg=audit(1700000001.123:456): arch=c000003e syscall=2
type=SYSCALL msg=audit(1700000002.456:457): arch=c000003e syscall=59
""",
    "logs/syslog/syslog.log": """\
Jan 15 10:00:01 webserver kernel: [12345.678] NET: Registered PF_INET6 protocol family
Jan 15 10:01:02 webserver sshd[1234]: Accepted publickey for admin from 192.168.1.10
""",
    "docs/runbooks/incident_response.md": """\
# Incident Response Runbook
1. Identify affected systems
2. Isolate the system
3. Collect evidence
4. Remediate
""",
    "docs/architecture/network_diagram.txt": """\
[Internet] --- [Firewall/Router] --- [DMZ: 10.0.1.0/24] --- [Internal: 10.0.2.0/24]
                                         |
                                    [Web Server: 10.0.1.10]
""",
    "deploy/staging/deploy.sh": """\
#!/bin/bash
echo "Deploying to staging..."
rsync -avz ./app/ staging-server:/opt/app/
""",
    "deploy/production/deploy.sh": """\
#!/bin/bash
echo "Deploying to production..."
rsync -avz ./app/ prod-server:/opt/app/
""",
    "monitoring/alerts/alert_rules.yml": """\
alerts:
  - name: high_cpu
    condition: cpu_usage > 90
    action: notify_slack
  - name: disk_full
    condition: disk_usage > 85
    action: notify_email
""",
    "monitoring/dashboards/overview.json": """\
{
  "title": "Server Overview",
  "panels": ["cpu", "memory", "network", "disk"]
}
""",
    "backups/weekly/backup_manifest.txt": """\
2024-01-08: /etc /var/www /home
2024-01-15: /etc /var/www /home
""",
    "docs/runbooks/firewall_requirements.txt": """\
# Web Server Firewall Requirements (Business Requirements Only)
# ----------------------------------------------------------------
# The production web server must:
#  - Accept inbound HTTP (port 80) and HTTPS (port 443) from the internet
#  - Accept inbound SSH (port 22) ONLY from the management subnet 10.10.0.0/24
#  - Accept inbound MySQL (port 3306) ONLY from the app subnet 10.20.0.0/24
#  - Block all other inbound traffic
#  - Allow all established/related traffic (stateful inspection)
#  - Allow all outbound traffic
#  - The script must be idempotent (safe to run multiple times)
#  - Must log dropped packets
#  - The script file should be named: firewall_setup.sh
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── 2. Create the SKILL script infrastructure ────────────────────────────────
# The scripts/script.sh is the reference tool the agent MUST invoke.
# We write a realistic, opinionated script that outputs specific best practices.

skill_script = r"""#!/bin/bash
# BytesAgain iptables reference tool v1.0.0

CMD="${1:-help}"

case "$CMD" in
  intro)
    cat <<'EOF'
=== IPTABLES OVERVIEW ===

Iptables is a user-space utility to configure Linux kernel firewall rules
via Netfilter. It operates on TABLES containing CHAINS of RULES.

Tables:
  filter  - Default table (INPUT, FORWARD, OUTPUT)
  nat     - Network address translation (PREROUTING, POSTROUTING, OUTPUT)
  mangle  - Packet alteration
  raw     - Connection tracking bypass

Chains:
  INPUT    - Packets destined for the local system
  OUTPUT   - Packets originating from the local system
  FORWARD  - Packets routed through the system

Rule Anatomy:
  iptables [-t table] -A CHAIN [matches] -j TARGET

Common Targets:
  ACCEPT   - Allow the packet
  DROP     - Silently discard
  REJECT   - Discard and send error reply
  LOG      - Log to kernel log
  RETURN   - Return to calling chain
EOF
    ;;

  quickstart)
    cat <<'EOF'
=== QUICKSTART GUIDE ===

1. Check current rules:
   iptables -L -n -v --line-numbers

2. Set default policies (FIRST STEP in any hardened setup):
   iptables -P INPUT DROP
   iptables -P FORWARD DROP
   iptables -P OUTPUT ACCEPT

3. Allow loopback:
   iptables -A INPUT -i lo -j ACCEPT
   iptables -A OUTPUT -o lo -j ACCEPT

4. Allow established/related connections:
   iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

5. Allow specific service:
   iptables -A INPUT -p tcp --dport 22 -j ACCEPT

6. Save rules (Debian/Ubuntu):
   iptables-save > /etc/iptables/rules.v4
EOF
    ;;

  patterns)
    cat <<'EOF'
=== COMMON PATTERNS & BEST PRACTICES ===

PATTERN 1 — Flush and Reset (Idempotent Script Header):
  # Always start a firewall script with a full flush to ensure idempotency
  iptables -F
  iptables -X
  iptables -Z
  iptables -t nat -F
  iptables -t nat -X
  iptables -t mangle -F
  iptables -t mangle -X

PATTERN 2 — Default Deny with Explicit Allows:
  # Set default policies AFTER flushing
  iptables -P INPUT DROP
  iptables -P FORWARD DROP
  iptables -P OUTPUT ACCEPT

PATTERN 3 — Loopback (Always Required):
  iptables -A INPUT -i lo -j ACCEPT

PATTERN 4 — Stateful Conntrack (Must Come Before Port-Specific Rules):
  iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

PATTERN 5 — Invalid Packet Drop:
  iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

PATTERN 6 — Port-Specific Allow (with source restriction):
  iptables -A INPUT -p tcp -s <source_subnet> --dport <port> -m conntrack --ctstate NEW -j ACCEPT

PATTERN 7 — Logging Before DROP (log prefix convention):
  iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4
  iptables -A INPUT -j DROP

NOTE: The LOG rule MUST come immediately before the final DROP rule at end of INPUT chain.
NOTE: Port-specific rules MUST use -m conntrack --ctstate NEW for new connection tracking.
NOTE: Loopback rule MUST be the first rule in the INPUT chain.
NOTE: Conntrack ESTABLISHED,RELATED MUST be the second rule in the INPUT chain.
EOF
    ;;

  debugging)
    cat <<'EOF'
=== DEBUGGING & TROUBLESHOOTING ===

1. List rules with counters and line numbers:
   iptables -L INPUT -n -v --line-numbers

2. Watch live packet hits:
   watch -n1 "iptables -L -n -v"

3. Trace a packet (requires raw table):
   iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
   # View with: journalctl -k | grep TRACE

4. Test connectivity:
   nc -zv <host> <port>
   telnet <host> <port>

5. Check for rule conflicts:
   iptables -L -n --line-numbers | grep -E "(DROP|REJECT)"

6. Reset all rules (emergency):
   iptables -F && iptables -X && iptables -P INPUT ACCEPT

Common Issues:
  - Rules evaluated top-to-bottom; order matters critically
  - Missing ESTABLISHED,RELATED rule breaks return traffic
  - LOG target does NOT stop processing; always pair with DROP after
  - Default ACCEPT policy is dangerous; always set DROP after setup
EOF
    ;;

  performance)
    cat <<'EOF'
=== PERFORMANCE OPTIMIZATION ===

1. Use conntrack for stateful matching (faster than stateless):
   -m conntrack --ctstate ESTABLISHED,RELATED

2. Place high-frequency rules early in the chain.

3. Use ipset for large IP sets (avoids linear rule scan):
   ipset create BLOCKED_IPS hash:ip
   iptables -A INPUT -m set --match-set BLOCKED_IPS src -j DROP

4. Avoid excessive logging in high-traffic environments;
   use --limit to rate-limit LOG rules:
   iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4 -m limit --limit 5/min --limit-burst 10

5. Use -m multiport for multiple ports (reduces rule count):
   iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

6. Minimize use of -m string (CPU intensive).
EOF
    ;;

  security)
    cat <<'EOF'
=== SECURITY CONSIDERATIONS ===

CRITICAL RULES — Must appear in every hardened server firewall:

SEC-1: Default Deny — Never leave default policy as ACCEPT in production.
  iptables -P INPUT DROP
  iptables -P FORWARD DROP

SEC-2: Drop INVALID packets explicitly:
  iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

SEC-3: Anti-Spoofing — Drop packets claiming to come from loopback on external interfaces:
  iptables -A INPUT ! -i lo -s 127.0.0.0/8 -j DROP

SEC-4: Log and drop before default policy (use log-prefix "IPT_DROP: " --log-level 4):
  iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4
  iptables -A INPUT -j DROP

SEC-5: Restrict management ports (SSH) to known subnets only.

SEC-6: Use -m conntrack --ctstate NEW for all new inbound service rules.

SEC-7: Never use --jump ACCEPT on a broad rule without state restriction.

SECURE RULE ORDER FOR INPUT CHAIN:
  1. Loopback ACCEPT
  2. Anti-spoof DROP (loopback src on non-lo interface)
  3. ESTABLISHED,RELATED ACCEPT (conntrack)
  4. INVALID DROP (conntrack)
  5. [Service-specific NEW ACCEPT rules]
  6. LOG --log-prefix "IPT_DROP: " --log-level 4
  7. DROP (explicit final rule)
NOTE: Default policy DROP must also be set, but the explicit LOG+DROP at end of chain is required.
EOF
    ;;

  migration)
    cat <<'EOF'
=== MIGRATION & UPGRADE GUIDE ===

Migrating from iptables to nftables:
  iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
  iptables-restore-translate -f /etc/iptables/rules.v4

Save/Restore (iptables-persistent):
  # Save
  iptables-save > /etc/iptables/rules.v4
  ip6tables-save > /etc/iptables/rules.v6

  # Restore
  iptables-restore < /etc/iptables/rules.v4

Migrating between servers:
  iptables-save | ssh newserver "iptables-restore"

Legacy ipchains migration:
  - ipchains policies map to iptables default policies
  - ipchains -I INPUT = iptables -I INPUT
  - Masquerade = iptables -t nat -A POSTROUTING -j MASQUERADE
EOF
    ;;

  cheatsheet)
    cat <<'EOF'
=== IPTABLES QUICK REFERENCE CHEAT SHEET ===

--- VIEWING ---
iptables -L -n -v --line-numbers          # List all filter rules
iptables -t nat -L -n -v                   # List NAT rules
iptables -S                                # Show rules as commands

--- FLUSHING ---
iptables -F                                # Flush all filter rules
iptables -X                                # Delete user-defined chains
iptables -Z                                # Zero counters
iptables -t nat -F && iptables -t nat -X
iptables -t mangle -F && iptables -t mangle -X

--- POLICIES ---
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

--- LOOPBACK ---
iptables -A INPUT -i lo -j ACCEPT

--- CONNTRACK ---
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

--- ANTI-SPOOF ---
iptables -A INPUT ! -i lo -s 127.0.0.0/8 -j DROP

--- ALLOW SERVICE (subnet-restricted) ---
iptables -A INPUT -p tcp -s <SUBNET> --dport <PORT> -m conntrack --ctstate NEW -j ACCEPT

--- ALLOW SERVICE (open) ---
iptables -A INPUT -p tcp --dport <PORT> -m conntrack --ctstate NEW -j ACCEPT

--- MULTIPORT ---
iptables -A INPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate NEW -j ACCEPT

--- LOG & DROP ---
iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4
iptables -A INPUT -j DROP

--- SAVE / RESTORE ---
iptables-save > /etc/iptables/rules.v4
iptables-restore < /etc/iptables/rules.v4
EOF
    ;;

  help)
    cat <<'EOF'
BytesAgain iptables reference tool v1.0.0

Usage: scripts/script.sh <command>

Commands:
  intro        Overview and core concepts
  quickstart   Getting started guide
  patterns     Common patterns and best practices
  debugging    Debugging and troubleshooting
  performance  Performance optimization tips
  security     Security considerations
  migration    Migration and upgrade guide
  cheatsheet   Quick reference cheat sheet
  help         Show this help
  version      Show version info
EOF
    ;;

  version)
    echo "iptables-skill v1.0.0 by BytesAgain"
    ;;

  *)
    echo "Unknown command: $CMD"
    echo "Run 'scripts/script.sh help' for usage."
    exit 1
    ;;
esac
"""

script_path = os.path.join(workspace, "scripts", "script.sh")
with open(script_path, "w") as f:
    f.write(skill_script)
os.chmod(script_path, 0o755)

# ── 3. Create a deliberately incomplete/broken partial firewall script ────────
partial_firewall = """\
#!/bin/bash
# INCOMPLETE FIREWALL SCRIPT — DO NOT USE IN PRODUCTION
# Created by: junior-devops
# Date: 2024-01-10
# Status: DRAFT - missing many rules

# TODO: someone said we need to flush rules first?

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow web traffic
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow MySQL from app servers
iptables -A INPUT -p tcp --dport 3306 -j ACCEPT

# TODO: restrict SSH to management subnet only (10.10.0.0/24)
# TODO: restrict MySQL to app subnet only (10.20.0.0/24)
# TODO: block everything else?
# TODO: what about loopback?
# TODO: logging?
"""
partial_path = os.path.join(workspace, "configs", "firewall", "partial_firewall.sh")
with open(partial_path, "w") as f:
    f.write(partial_firewall)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")