import sys
import json
import os
import stat
import subprocess
import re
from pathlib import Path

def find_file(workspace, filename):
    """Search for a file recursively in workspace."""
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace = Path(workspace)
    checks = []

    # ── CHECK 1: Managed wallet file exists at correct path with correct permissions ──
    def check_managed_wallet():
        home = Path.home()
        wallet_dir = home / ".openclaw" / "wallets"
        wallet_files = list(wallet_dir.glob("*.json")) if wallet_dir.exists() else []
        
        if not wallet_files:
            return False, f"No wallet JSON files found in {wallet_dir}. Expected ~/.openclaw/wallets/<name>.json"
        
        # Check permissions on each wallet file
        for wf in wallet_files:
            file_stat = os.stat(wf)
            mode = stat.S_IMODE(file_stat.st_mode)
            if mode != 0o600:
                return False, f"Wallet file {wf.name} has permissions {oct(mode)}, expected 0o600 (chmod 600)"
        
        # Try to parse the wallet file
        wf = wallet_files[0]
        try:
            data = json.loads(wf.read_text())
        except json.JSONDecodeError as e:
            return False, f"Wallet file is not valid JSON: {e}"
        
        if "address" not in data:
            return False, f"Wallet JSON missing 'address' field. Keys found: {list(data.keys())}"
        if "privateKey" not in data:
            return False, f"Wallet JSON missing 'privateKey' field. Keys found: {list(data.keys())}"
        
        addr = data["address"]
        if not re.match(r'^0x[0-9a-fA-F]{40}$', addr):
            return False, f"Wallet address '{addr}' is not a valid Ethereum address"
        
        pk = data["privateKey"]
        if not re.match(r'^0x[0-9a-fA-F]{64}$', pk):
            return False, f"Private key format invalid (should be 0x + 64 hex chars)"
        
        return True, f"Managed wallet file found at {wf} with correct 0o600 permissions. Address: {addr}"

    checks.append(run_check("managed_wallet_file_correct_path_and_permissions", check_managed_wallet))

    # ── CHECK 2: agent_identity.json output file exists with valid structure ──
    def check_identity_file():
        # Look for the output file named agent_identity.json
        found = find_file(workspace, "agent_identity.json")
        if not found:
            return False, "agent_identity.json not found anywhere in workspace"
        
        try:
            data = json.loads(found.read_text())
        except json.JSONDecodeError as e:
            return False, f"agent_identity.json is not valid JSON: {e}"
        
        required_keys = ["wallet_address", "siwe_message", "siwe_signature"]
        missing = [k for k in required_keys if k not in data]
        if missing:
            return False, f"agent_identity.json missing required keys: {missing}. Found: {list(data.keys())}"
        
        addr = data["wallet_address"]
        if not re.match(r'^0x[0-9a-fA-F]{40}$', addr):
            return False, f"wallet_address '{addr}' is not a valid Ethereum address"
        
        sig = data["siwe_signature"]
        if not re.match(r'^0x[0-9a-fA-F]{130}$', sig):
            return False, f"siwe_signature '{sig[:20]}...' is not a valid 65-byte Ethereum signature (0x + 130 hex chars)"
        
        return True, f"agent_identity.json found at {found} with all required fields. Address: {addr}"

    checks.append(run_check("agent_identity_file_structure", check_identity_file))

    # ── CHECK 3: SIWE message uses correct Base chain ID (8453) ──
    def check_siwe_chain_id():
        found = find_file(workspace, "agent_identity.json")
        if not found:
            return False, "agent_identity.json not found"
        
        try:
            data = json.loads(found.read_text())
        except Exception as e:
            return False, f"Cannot parse agent_identity.json: {e}"
        
        siwe_msg = data.get("siwe_message", "")
        
        # Check for Base chain ID: 8453
        if "Chain ID: 8453" not in siwe_msg:
            # Also check for chainId or chain_id variants
            chain_match = re.search(r'[Cc]hain\s*[Ii][Dd][\s:]+(\d+)', siwe_msg)
            if chain_match:
                found_id = chain_match.group(1)
                return False, f"SIWE message uses Chain ID {found_id} instead of required 8453 (Base Mainnet)"
            return False, f"SIWE message does not contain 'Chain ID: 8453'. Message preview: {siwe_msg[:200]}"
        
        return True, "SIWE message correctly uses Chain ID: 8453 (Base Mainnet)"

    checks.append(run_check("siwe_message_uses_base_chain_id_8453", check_siwe_chain_id))

    # ── CHECK 4: SIWE message has all required EIP-4361 fields ──
    def check_siwe_message_format():
        found = find_file(workspace, "agent_identity.json")
        if not found:
            return False, "agent_identity.json not found"
        
        try:
            data = json.loads(found.read_text())
        except Exception as e:
            return False, f"Cannot parse agent_identity.json: {e}"
        
        siwe_msg = data.get("siwe_message", "")
        wallet_addr = data.get("wallet_address", "")
        
        missing_fields = []
        
        # URI field required
        if "URI:" not in siwe_msg:
            missing_fields.append("URI")
        
        # Version field required  
        if "Version:" not in siwe_msg:
            missing_fields.append("Version")
        
        # Nonce field required
        if "Nonce:" not in siwe_msg:
            missing_fields.append("Nonce")
        
        # Issued At field required
        if "Issued At:" not in siwe_msg:
            missing_fields.append("Issued At")
        
        # Wallet address must appear in message
        if wallet_addr and wallet_addr.lower() not in siwe_msg.lower():
            missing_fields.append(f"wallet address ({wallet_addr})")
        
        if missing_fields:
            return False, f"SIWE message missing required EIP-4361 fields: {missing_fields}. Message: {siwe_msg[:300]}"
        
        return True, f"SIWE message contains all required EIP-4361 fields (URI, Version, Chain ID, Nonce, Issued At, wallet address)"

    checks.append(run_check("siwe_message_has_required_eip4361_fields", check_siwe_message_format))

    # ── CHECK 5: Signature is cryptographically valid (matches address) ──
    def check_signature_validity():
        found = find_file(workspace, "agent_identity.json")
        if not found:
            return False, "agent_identity.json not found"
        
        try:
            data = json.loads(found.read_text())
        except Exception as e:
            return False, f"Cannot parse agent_identity.json: {e}"
        
        siwe_msg = data.get("siwe_message", "")
        sig = data.get("siwe_signature", "")
        wallet_addr = data.get("wallet_address", "")
        
        if not siwe_msg or not sig or not wallet_addr:
            return False, "Missing siwe_message, siwe_signature, or wallet_address in agent_identity.json"
        
        # Use eth_account to recover the signer
        try:
            from eth_account import Account
            from eth_account.messages import encode_defunct
            
            msg_obj = encode_defunct(text=siwe_msg)
            recovered = Account.recover_message(msg_obj, signature=sig)
            
            if recovered.lower() != wallet_addr.lower():
                return False, f"Signature does not match wallet address. Recovered: {recovered}, Expected: {wallet_addr}"
            
            return True, f"Cryptographic signature is valid. Recovered address {recovered} matches wallet {wallet_addr}"
        except Exception as e:
            return False, f"Error verifying signature: {e}"

    checks.append(run_check("siwe_signature_cryptographically_valid", check_signature_validity))

    # ── CHECK 6: Wallet address consistency (managed file == identity JSON) ──
    def check_address_consistency():
        home = Path.home()
        wallet_dir = home / ".openclaw" / "wallets"
        wallet_files = list(wallet_dir.glob("*.json")) if wallet_dir.exists() else []
        
        identity_file = find_file(workspace, "agent_identity.json")
        
        if not wallet_files:
            return False, "No managed wallet file found to compare"
        if not identity_file:
            return False, "agent_identity.json not found to compare"
        
        try:
            managed_data = json.loads(wallet_files[0].read_text())
            identity_data = json.loads(identity_file.read_text())
        except Exception as e:
            return False, f"Error reading files: {e}"
        
        managed_addr = managed_data.get("address", "").lower()
        identity_addr = identity_data.get("wallet_address", "").lower()
        
        if not managed_addr or not identity_addr:
            return False, f"Missing address in one of the files. Managed: '{managed_addr}', Identity: '{identity_addr}'"
        
        if managed_addr != identity_addr:
            return False, f"Address mismatch: managed wallet has {managed_addr}, identity JSON has {identity_addr}. Must be the same wallet."
        
        return True, f"Wallet addresses are consistent across both files: {managed_addr}"

    checks.append(run_check("wallet_address_consistency_across_files", check_address_consistency))

    # ── CHECK 7: .gitignore contains openclaw pattern ──
    def check_gitignore():
        gitignore_path = workspace / ".gitignore"
        if not gitignore_path.exists():
            return False, ".gitignore not found in workspace root"
        
        content = gitignore_path.read_text()
        
        # Check for .openclaw/ pattern (exact requirement from SKILL.md)
        if ".openclaw/" not in content:
            # Check if any openclaw-related pattern exists
            if "openclaw" in content.lower():
                return True, f".gitignore contains openclaw pattern (non-standard form): {[l for l in content.splitlines() if 'openclaw' in l.lower()]}"
            return False, f".gitignore does not contain '.openclaw/' entry. Current content:\n{content}"
        
        return True, ".gitignore correctly includes '.openclaw/' to prevent committing wallet files"

    checks.append(run_check("gitignore_contains_openclaw_pattern", check_gitignore))

    # ── Compute final score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()