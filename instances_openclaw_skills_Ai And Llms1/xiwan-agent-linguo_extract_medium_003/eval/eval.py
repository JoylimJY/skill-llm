import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    out = workspace / "output.txt"
    if not out.exists():
        add_check("output_exists", False, "output.txt is missing")
        text = ""
    else:
        text = out.read_text(encoding="utf-8", errors="replace")
        add_check("output_exists", True, "output.txt found")
except Exception as e:
    text = ""
    add_check("output_exists", False, f"could not read output.txt: {e}")

lower = text.lower()
normalized = re.sub(r"[^a-z0-9]+", " ", lower)

def fuzzy_contains(*needles):
    try:
        for needle in needles:
            n = re.sub(r"[^a-z0-9]+", " ", needle.lower()).strip()
            if n and n not in normalized:
                return False
        return True
    except Exception:
        return False

# Check 1: mentions protocol and version
try:
    passed = fuzzy_contains("agent lingua", "0.4.0") or fuzzy_contains("agent lingua", "0.4")
    add_check("protocol_version", passed, "expects Agent Lingua and version 0.4.x")
except Exception as e:
    add_check("protocol_version", False, f"error: {e}")

# Check 2: mentions handshake/source/signature details
try:
    passed = fuzzy_contains("handshake", "agent lingua") or fuzzy_contains("signature", "agent lingua")
    add_check("handshake_or_signature", passed, "expects handshake or signature reference")
except Exception as e:
    add_check("handshake_or_signature", False, f"error: {e}")

# Check 3: mentions security and crypto in some form
try:
    sec_ok = fuzzy_contains("security", "p b e") or fuzzy_contains("security", "base64") or fuzzy_contains("security", "encrypted")
    crypto_ok = fuzzy_contains("x25519", "aes gcm") or fuzzy_contains("psk", "aes gcm") or fuzzy_contains("crypto")
    add_check("security_crypto", sec_ok and crypto_ok, "expects security plus crypto details")
except Exception as e:
    add_check("security_crypto", False, f"error: {e}")

# Check 4: mentions deterministic marker or marker-derived content
try:
    marker_ok = fuzzy_contains("deterministic marker", "alpha 42") or fuzzy_contains("deterministic marker", "alpha42")
    add_check("marker_content", marker_ok, "expects deterministic marker-derived content")
except Exception as e:
    add_check("marker_content", False, f"error: {e}")

# Check 5: if session is mentioned, it should be plausible
try:
    if "session" in normalized:
        sess_ok = fuzzy_contains("s123456") or fuzzy_contains("session", "s123")
        add_check("session_if_present", sess_ok, "session mention should look like s123456")
    else:
        add_check("session_if_present", False, "session not mentioned")
except Exception as e:
    add_check("session_if_present", False, f"error: {e}")

passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
