import sys
import os
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    
    # ── Locate firewall_setup.sh anywhere in the workspace ──────────────────
    candidates = list(Path(workspace).rglob("firewall_setup.sh"))
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "firewall_setup.sh not found anywhere in workspace"}]
        }
    
    target = candidates[0]
    try:
        content = target.read_text()
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read firewall_setup.sh: {e}"}]
        }

    lines = content.splitlines()
    # Normalize: strip comments and blank lines for ordered checks
    effective_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]

    # ── CHECK 1: File is a bash script ───────────────────────────────────────
    has_shebang = content.startswith("#!/bin/bash") or content.startswith("#!/usr/bin/env bash")
    checks.append({
        "name": "is_bash_script",
        "passed": has_shebang,
        "detail": "File starts with #!/bin/bash or #!/usr/bin/env bash" if has_shebang else "Missing bash shebang"
    })

    # ── CHECK 2: Idempotent flush block (patterns: -F, -X, -Z + nat + mangle) 
    has_flush_F = bool(re.search(r'iptables\s+-F\b', content))
    has_flush_X = bool(re.search(r'iptables\s+-X\b', content))
    has_flush_Z = bool(re.search(r'iptables\s+-Z\b', content))
    has_nat_flush = bool(re.search(r'iptables\s+-t\s+nat\s+-F', content))
    has_mangle_flush = bool(re.search(r'iptables\s+-t\s+mangle\s+-F', content))
    idempotent_flush = has_flush_F and has_flush_X and has_flush_Z and has_nat_flush and has_mangle_flush
    checks.append({
        "name": "idempotent_flush_block",
        "passed": idempotent_flush,
        "detail": f"Flush block: -F={has_flush_F}, -X={has_flush_X}, -Z={has_flush_Z}, nat-F={has_nat_flush}, mangle-F={has_mangle_flush}. All required per patterns/cheatsheet."
    })

    # ── CHECK 3: Default policies DROP for INPUT and FORWARD, ACCEPT for OUTPUT
    has_input_drop = bool(re.search(r'iptables\s+-P\s+INPUT\s+DROP', content))
    has_fwd_drop   = bool(re.search(r'iptables\s+-P\s+FORWARD\s+DROP', content))
    has_out_accept = bool(re.search(r'iptables\s+-P\s+OUTPUT\s+ACCEPT', content))
    default_policies = has_input_drop and has_fwd_drop and has_out_accept
    checks.append({
        "name": "default_policies",
        "passed": default_policies,
        "detail": f"INPUT DROP={has_input_drop}, FORWARD DROP={has_fwd_drop}, OUTPUT ACCEPT={has_out_accept}"
    })

    # ── CHECK 4: Loopback rule present and is FIRST effective INPUT rule ─────
    loopback_pattern = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+-i\s+lo\s+-j\s+ACCEPT')
    loopback_match = loopback_pattern.search(content)
    has_loopback = bool(loopback_match)
    
    # Find position: loopback must be first INPUT -A/-I rule in effective lines
    loopback_first = False
    if has_loopback:
        # Find all INPUT append/insert lines
        input_rule_pattern = re.compile(r'iptables\s+(-A|-I)\s+INPUT\b')
        first_input_line = None
        for line in effective_lines:
            if input_rule_pattern.search(line):
                first_input_line = line
                break
        if first_input_line and loopback_pattern.search(first_input_line):
            loopback_first = True
    checks.append({
        "name": "loopback_rule_first",
        "passed": has_loopback and loopback_first,
        "detail": f"Loopback present={has_loopback}, is first INPUT rule={loopback_first}. Required by security/patterns ordering."
    })

    # ── CHECK 5: Anti-spoof rule (SEC-3 from security) ────────────────────────
    # iptables -A INPUT ! -i lo -s 127.0.0.0/8 -j DROP
    antispoof_pattern = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*!\s*-i\s+lo\s+.*-s\s+127\.0\.0\.0/8\s+.*-j\s+DROP')
    antispoof_alt     = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-s\s+127\.0\.0\.0/8\s+.*!\s*-i\s+lo\s+.*-j\s+DROP')
    has_antispoof = bool(antispoof_pattern.search(content)) or bool(antispoof_alt.search(content))
    checks.append({
        "name": "anti_spoof_rule",
        "passed": has_antispoof,
        "detail": "Anti-spoof rule (SEC-3): drop loopback-sourced packets on non-lo interfaces. Required by security section."
    })

    # ── CHECK 6: Conntrack ESTABLISHED,RELATED rule (second in order after loopback/antispoof)
    conntrack_est = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-m\s+conntrack\s+--ctstate\s+ESTABLISHED,RELATED\s+.*-j\s+ACCEPT')
    has_conntrack_est = bool(conntrack_est.search(content))
    checks.append({
        "name": "conntrack_established_related",
        "passed": has_conntrack_est,
        "detail": f"ESTABLISHED,RELATED conntrack rule present={has_conntrack_est}. Required by patterns/cheatsheet (must use -m conntrack --ctstate)."
    })

    # ── CHECK 7: INVALID packet drop rule ────────────────────────────────────
    invalid_pattern = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-m\s+conntrack\s+--ctstate\s+INVALID\s+.*-j\s+DROP')
    has_invalid_drop = bool(invalid_pattern.search(content))
    checks.append({
        "name": "invalid_packet_drop",
        "passed": has_invalid_drop,
        "detail": f"INVALID conntrack drop rule present={has_invalid_drop}. Required by SEC-2 and patterns."
    })

    # ── CHECK 8: SSH restricted to management subnet 10.10.0.0/24 with conntrack NEW
    ssh_restricted = re.compile(
        r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*-s\s+10\.10\.0\.0/24\s+.*--dport\s+22\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT'
    )
    ssh_restricted_alt = re.compile(
        r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*--dport\s+22\s+.*-s\s+10\.10\.0\.0/24\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT'
    )
    has_ssh_restricted = bool(ssh_restricted.search(content)) or bool(ssh_restricted_alt.search(content))
    checks.append({
        "name": "ssh_restricted_to_mgmt_subnet",
        "passed": has_ssh_restricted,
        "detail": f"SSH (port 22) restricted to 10.10.0.0/24 with --ctstate NEW: {has_ssh_restricted}. Required by business requirements + SEC-6."
    })

    # ── CHECK 9: HTTP/HTTPS open with conntrack NEW (multiport or separate rules)
    http_rule  = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*--dport\s+80\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT')
    https_rule = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*--dport\s+443\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT')
    multi_web  = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*-m\s+multiport\s+--dports\s+80,443\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT')
    multi_web2 = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-m\s+multiport\s+--dports\s+80,443\s+.*-j\s+ACCEPT')
    has_http  = bool(http_rule.search(content))
    has_https = bool(https_rule.search(content))
    has_multi = bool(multi_web.search(content)) or bool(multi_web2.search(content))
    has_web_rules = (has_http and has_https) or has_multi
    checks.append({
        "name": "http_https_allowed_with_conntrack",
        "passed": has_web_rules,
        "detail": f"HTTP={has_http}, HTTPS={has_https}, multiport={has_multi}. Must use -m conntrack --ctstate NEW per SEC-6/patterns."
    })

    # ── CHECK 10: MySQL restricted to app subnet 10.20.0.0/24 with conntrack NEW
    mysql_restricted = re.compile(
        r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*-s\s+10\.20\.0\.0/24\s+.*--dport\s+3306\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT'
    )
    mysql_restricted_alt = re.compile(
        r'iptables\s+(-A|-I)\s+INPUT\s+.*-p\s+tcp\s+.*--dport\s+3306\s+.*-s\s+10\.20\.0\.0/24\s+.*-m\s+conntrack\s+--ctstate\s+NEW\s+.*-j\s+ACCEPT'
    )
    has_mysql_restricted = bool(mysql_restricted.search(content)) or bool(mysql_restricted_alt.search(content))
    checks.append({
        "name": "mysql_restricted_to_app_subnet",
        "passed": has_mysql_restricted,
        "detail": f"MySQL (port 3306) restricted to 10.20.0.0/24 with --ctstate NEW: {has_mysql_restricted}. Required by business requirements + SEC-6."
    })

    # ── CHECK 11: LOG rule with exact prefix "IPT_DROP: " and --log-level 4 ──
    # From security/cheatsheet: --log-prefix "IPT_DROP: " --log-level 4
    log_pattern = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*-j\s+LOG\s+.*--log-prefix\s+["\']?IPT_DROP:\s*["\']?.*--log-level\s+4')
    log_pattern_alt = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*--log-level\s+4\s+.*-j\s+LOG\s+.*--log-prefix\s+["\']?IPT_DROP:\s*["\']?')
    # Also check prefix before -j LOG
    log_pattern2 = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+.*--log-prefix\s+"IPT_DROP:\s*".*--log-level\s+4.*-j\s+LOG')
    has_log_rule = (bool(log_pattern.search(content)) or 
                    bool(log_pattern_alt.search(content)) or
                    bool(log_pattern2.search(content)))
    # More flexible check for log prefix
    has_log_prefix = bool(re.search(r'--log-prefix\s+["\']?IPT_DROP:', content))
    has_log_level4 = bool(re.search(r'--log-level\s+4', content))
    has_log_on_input = bool(re.search(r'iptables.*INPUT.*-j\s+LOG', content)) or bool(re.search(r'iptables.*-j\s+LOG.*INPUT', content))
    has_log_rule_combined = has_log_prefix and has_log_level4 and has_log_on_input
    checks.append({
        "name": "log_rule_with_correct_prefix_and_level",
        "passed": has_log_rule_combined,
        "detail": f"LOG rule: prefix='IPT_DROP:'={has_log_prefix}, --log-level 4={has_log_level4}, applied to INPUT={has_log_on_input}. Required by security SEC-4 and cheatsheet."
    })

    # ── CHECK 12: Explicit final DROP rule on INPUT (LOG must come before it) ─
    explicit_drop = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+-j\s+DROP\s*$', re.MULTILINE)
    has_explicit_drop = bool(explicit_drop.search(content))
    
    # Check order: LOG before DROP at end of chain
    log_drop_order_ok = False
    if has_log_prefix and has_explicit_drop:
        log_pos   = content.rfind("IPT_DROP:")
        drop_pos  = content.rfind("INPUT -j DROP")
        if drop_pos == -1:
            # Try alternate form
            for m in explicit_drop.finditer(content):
                drop_pos = m.start()
        log_drop_order_ok = log_pos < drop_pos if (log_pos >= 0 and drop_pos >= 0) else False
    checks.append({
        "name": "log_before_explicit_drop_at_chain_end",
        "passed": has_explicit_drop and log_drop_order_ok,
        "detail": f"Explicit INPUT DROP={has_explicit_drop}, LOG comes before DROP={log_drop_order_ok}. Required by security SEC-4 and patterns PATTERN 7."
    })

    # ── CHECK 13: No broad unrestricted SSH (without subnet) ─────────────────
    # Should NOT have: iptables -A INPUT -p tcp --dport 22 -j ACCEPT (without -s)
    bad_ssh = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+-p\s+tcp\s+--dport\s+22\s+-j\s+ACCEPT')
    bad_ssh2 = re.compile(r'iptables\s+(-A|-I)\s+INPUT\s+-p\s+tcp\s+--dport\s+22\s+(?!.*-s\s+10\.10).*-j\s+ACCEPT')
    # Simpler: does a line have --dport 22 and ACCEPT but no subnet restriction?
    no_unrestricted_ssh = True
    for line in effective_lines:
        if '--dport 22' in line and '-j ACCEPT' in line:
            if '-s 10.10.0.0/24' not in line and '-s 10.10.' not in line:
                no_unrestricted_ssh = False
                break
    checks.append({
        "name": "no_unrestricted_ssh_access",
        "passed": no_unrestricted_ssh,
        "detail": f"SSH not left open to all IPs: {no_unrestricted_ssh}. The partial script had this bug; agent must fix it per business requirements."
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    weights = {
        "is_bash_script": 1,
        "idempotent_flush_block": 2,
        "default_policies": 2,
        "loopback_rule_first": 2,
        "anti_spoof_rule": 2,
        "conntrack_established_related": 2,
        "invalid_packet_drop": 1,
        "ssh_restricted_to_mgmt_subnet": 2,
        "http_https_allowed_with_conntrack": 2,
        "mysql_restricted_to_app_subnet": 2,
        "log_rule_with_correct_prefix_and_level": 2,
        "log_before_explicit_drop_at_chain_end": 2,
        "no_unrestricted_ssh_access": 2,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)
    passed = score >= 0.85

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))