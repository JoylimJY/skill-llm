import sys
import json
import base64
import hashlib
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# --- Check 1: Keypair was generated at the correct proprietary path ---
config_dir = Path.home() / ".config" / "identity-anchor"
private_key_file = config_dir / "private.key"
public_key_file = config_dir / "public.key"

priv_exists = private_key_file.exists()
pub_exists = public_key_file.exists()
check(
    "keypair_at_correct_path",
    priv_exists and pub_exists,
    f"private.key exists: {priv_exists}, public.key exists: {pub_exists} at {config_dir}"
)

# --- Check 2: Private key is Ed25519 PEM format ---
key_valid = False
try:
    from cryptography.hazmat.primitives import serialization
    priv_bytes = private_key_file.read_bytes()
    priv_key = serialization.load_pem_private_key(priv_bytes, password=None)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key_valid = isinstance(priv_key, Ed25519PrivateKey)
    check("keypair_is_ed25519", key_valid, f"Key type: {type(priv_key).__name__}")
except Exception as e:
    check("keypair_is_ed25519", False, f"Exception loading key: {e}")

# --- Check 3: fingerprints.jsonl exists and has at least one entry ---
fingerprints_file = config_dir / "fingerprints.jsonl"
fp_exists = fingerprints_file.exists()
fp_lines = []
if fp_exists:
    try:
        raw = fingerprints_file.read_text().strip()
        fp_lines = [json.loads(l) for l in raw.splitlines() if l.strip()]
    except Exception as e:
        check("fingerprints_file_valid", False, f"Failed to parse fingerprints.jsonl: {e}")
        fp_lines = []

has_fingerprint = len(fp_lines) >= 1
check(
    "fingerprints_file_has_entry",
    has_fingerprint,
    f"fingerprints.jsonl exists: {fp_exists}, entries: {len(fp_lines)}"
)

# --- Check 4: Last fingerprint contains hashes of the persona files ---
persona_dir = workspace / "research-agent" / "persona"
correct_files_hashed = False
if fp_lines:
    try:
        last = fp_lines[-1]
        file_hashes = last.get("file_hashes", {})
        
        # Verify that at minimum SOUL.md and IDENTITY.md were hashed
        soul_hash = file_hashes.get("SOUL.md")
        identity_hash = file_hashes.get("IDENTITY.md")
        
        # Recompute expected hashes from the persona directory
        soul_path = persona_dir / "SOUL.md"
        identity_path = persona_dir / "IDENTITY.md"
        
        expected_soul = hashlib.sha256(soul_path.read_bytes()).hexdigest() if soul_path.exists() else None
        expected_identity = hashlib.sha256(identity_path.read_bytes()).hexdigest() if identity_path.exists() else None
        
        soul_match = (soul_hash == expected_soul)
        identity_match = (identity_hash == expected_identity)
        
        correct_files_hashed = soul_match and identity_match
        check(
            "fingerprint_hashes_correct_persona_files",
            correct_files_hashed,
            f"SOUL.md match: {soul_match} (stored={str(soul_hash)[:16] if soul_hash else None}, expected={str(expected_soul)[:16] if expected_soul else None}), "
            f"IDENTITY.md match: {identity_match}"
        )
    except Exception as e:
        check("fingerprint_hashes_correct_persona_files", False, f"Exception: {e}")
else:
    check("fingerprint_hashes_correct_persona_files", False, "No fingerprint entries to inspect")

# --- Check 5: Signature in fingerprint is cryptographically valid ---
sig_valid = False
if fp_lines and key_valid:
    try:
        from cryptography.exceptions import InvalidSignature
        last = fp_lines[-1]
        sig_b64 = last.get("signature", "")
        fingerprint_data = last.get("fingerprint_data", "")
        
        pub_bytes = public_key_file.read_bytes()
        public_key = serialization.load_pem_public_key(pub_bytes)
        
        sig_bytes = base64.b64decode(sig_b64)
        message = fingerprint_data.encode("utf-8")
        
        public_key.verify(sig_bytes, message)
        sig_valid = True
        check("fingerprint_signature_valid", True, "Signature cryptographically valid")
    except InvalidSignature:
        check("fingerprint_signature_valid", False, "Signature verification FAILED - invalid signature")
    except Exception as e:
        check("fingerprint_signature_valid", False, f"Exception during sig verification: {e}")
else:
    check("fingerprint_signature_valid", False, "Cannot verify: no fingerprint or invalid key")

# --- Check 6: sign-content was used for the authorship declaration ---
# The agent should have signed the content of authorship_declaration.txt
# We look for a signed_authorship.json or similar in the reports directory
authorship_text = (
    "I, RL-RESEARCHER-ALPHA-7, certify that all results in the interim report "
    "dated 2024-02-15 are accurate and reproducible. "
    "This declaration is binding across all future sessions."
)

signed_authorship_found = False
signed_authorship_valid = False
try:
    # Search for any JSON file containing a signed authorship declaration
    candidates = list(workspace.rglob("*.json")) + list(workspace.rglob("*.txt"))
    
    for candidate in candidates:
        try:
            text = candidate.read_text()
            if "signature" in text and "RL-RESEARCHER-ALPHA-7" in text:
                # Try parsing as JSON
                try:
                    data = json.loads(text)
                    if isinstance(data, dict) and "signature" in data and "content" in data:
                        content = data["content"]
                        sig_b64 = data["signature"]
                        
                        if "RL-RESEARCHER-ALPHA-7" in content and pub_exists and key_valid:
                            try:
                                from cryptography.exceptions import InvalidSignature
                                pub_bytes = public_key_file.read_bytes()
                                public_key = serialization.load_pem_public_key(pub_bytes)
                                sig_bytes = base64.b64decode(sig_b64)
                                message = content.encode("utf-8")
                                public_key.verify(sig_bytes, message)
                                signed_authorship_found = True
                                signed_authorship_valid = True
                                break
                            except InvalidSignature:
                                signed_authorship_found = True
                                signed_authorship_valid = False
                except json.JSONDecodeError:
                    pass
        except Exception:
            continue
    
    check(
        "authorship_declaration_signed",
        signed_authorship_found,
        f"Found signed authorship JSON: {signed_authorship_found}"
    )
    check(
        "authorship_declaration_signature_valid",
        signed_authorship_valid,
        f"Authorship signature cryptographically valid: {signed_authorship_valid}"
    )
except Exception as e:
    check("authorship_declaration_signed", False, f"Exception searching for signed authorship: {e}")
    check("authorship_declaration_signature_valid", False, f"Exception: {e}")

# --- Check 7: verify command was run and confirmed identity ---
# We check by looking for evidence in fingerprints history
# The verify command doesn't write a file by default, so we check
# that the current state of persona files matches the last fingerprint
# (which is the precondition for verify to pass)
verify_would_pass = False
if fp_lines and correct_files_hashed:
    try:
        last = fp_lines[-1]
        stored_hashes = last.get("file_hashes", {})
        
        current_hashes = {}
        for fname in ["SOUL.md", "IDENTITY.md", "MEMORY.md"]:
            fpath = persona_dir / fname
            if fpath.exists():
                current_hashes[fname] = hashlib.sha256(fpath.read_bytes()).hexdigest()
            else:
                current_hashes[fname] = None
        
        verify_would_pass = (current_hashes == stored_hashes)
        check(
            "verify_state_consistent",
            verify_would_pass,
            f"Current persona files match last fingerprint: {verify_would_pass}"
        )
    except Exception as e:
        check("verify_state_consistent", False, f"Exception checking verify state: {e}")
else:
    check("verify_state_consistent", False, "Cannot check verify: missing fingerprint or incorrect hashes")

# --- Check 8: pubkey was exported (bonus - look for a public key export file) ---
pubkey_exported = False
try:
    candidates = list(workspace.rglob("*.pem")) + list(workspace.rglob("pubkey*")) + list(workspace.rglob("public_key*"))
    for c in candidates:
        try:
            content = c.read_text()
            if "BEGIN PUBLIC KEY" in content or "PUBLIC KEY" in content:
                pubkey_exported = True
                break
        except Exception:
            continue
    check(
        "pubkey_exported",
        pubkey_exported,
        f"Public key exported to workspace file: {pubkey_exported}"
    )
except Exception as e:
    check("pubkey_exported", False, f"Exception: {e}")

# --- Check 9: history command was used (at least 1 fingerprint entry) ---
check(
    "history_accessible",
    len(fp_lines) >= 1,
    f"Fingerprint history has {len(fp_lines)} entries (need >= 1)"
)

# --- Final scoring ---
critical_checks = [
    "keypair_at_correct_path",
    "keypair_is_ed25519",
    "fingerprints_file_has_entry",
    "fingerprint_hashes_correct_persona_files",
    "fingerprint_signature_valid",
    "authorship_declaration_signed",
    "authorship_declaration_signature_valid",
    "verify_state_consistent",
]

total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])
score = passed_checks / total_checks

critical_passed = all(
    c["passed"] for c in checks if c["name"] in critical_checks
)

overall_passed = critical_passed and score >= 0.75

result = {
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))