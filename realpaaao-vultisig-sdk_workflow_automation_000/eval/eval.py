import sys
import json
import re
import os
from pathlib import Path

def find_script(workspace):
    """Find treasury_automation.ts - check exact path first, then search."""
    exact = Path(workspace) / "treasury" / "scripts" / "treasury_automation.ts"
    if exact.exists():
        return exact
    results = list(Path(workspace).rglob("treasury_automation.ts"))
    if results:
        return results[0]
    return None

def run_checks(workspace):
    checks = []
    
    script_path = find_script(workspace)
    
    # CHECK 0: File exists
    file_exists = script_path is not None and script_path.exists()
    checks.append({
        "name": "treasury_automation.ts exists",
        "passed": file_exists,
        "detail": str(script_path) if file_exists else "File treasury_automation.ts not found anywhere in workspace"
    })
    
    if not file_exists:
        # All remaining checks fail
        for name in [
            "SDK import uses MemoryStorage (not FileStorage or other)",
            "Uses Vultisig class with MemoryStorage storage init",
            "sdk.initialize() is called",
            "createFastVault is used (not createSecureVault)",
            "verifyVault is called to complete vault creation",
            "vault.address('Ethereum') called for address retrieval",
            "addAddressBookEntry used with both BTC and ETH contacts",
            "vault.balance('Ethereum') called for native ETH balance",
            "vault.balance('Ethereum', '0xA0b86991...') called for USDC token balance",
            "prepareSendTx uses BigInt for USDC amount (50000000)",
            "USDC send includes 'id' field with contract address",
            "3-step send flow: prepareSendTx → sign → broadcastTx",
            "getSwapQuote amount is number 0.5 (not bigint)",
            "prepareSwapTx is called after getSwapQuote",
            "approvalPayload check and conditional sign+broadcast before swap",
            "4-step swap: getSwapQuote → prepareSwapTx → sign → broadcastTx",
            "Chain identifiers use PascalCase (Ethereum, Bitcoin, etc.)",
            "Vultisig.getTxExplorerUrl called for swap tx hash",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File not found"})
        return checks
    
    try:
        content = script_path.read_text(encoding='utf-8')
    except Exception as e:
        checks.append({"name": "Can read file", "passed": False, "detail": str(e)})
        return checks

    # CHECK 1: SDK import with MemoryStorage
    has_memory_storage_import = bool(re.search(r'import\s*\{[^}]*MemoryStorage[^}]*\}\s*from\s*[\'"]@vultisig/sdk[\'"]', content))
    checks.append({
        "name": "SDK import uses MemoryStorage (not FileStorage or other)",
        "passed": has_memory_storage_import,
        "detail": "Found MemoryStorage import from @vultisig/sdk" if has_memory_storage_import else "Missing: import { ..., MemoryStorage, ... } from '@vultisig/sdk'"
    })

    # CHECK 2: Vultisig + MemoryStorage init pattern
    has_sdk_init = bool(re.search(r'new\s+Vultisig\s*\(\s*\{[^}]*storage\s*:\s*new\s+MemoryStorage\s*\(\s*\)', content))
    checks.append({
        "name": "Uses Vultisig class with MemoryStorage storage init",
        "passed": has_sdk_init,
        "detail": "Found: new Vultisig({ storage: new MemoryStorage() })" if has_sdk_init else "Missing: new Vultisig({ storage: new MemoryStorage() })"
    })

    # CHECK 3: sdk.initialize()
    has_initialize = bool(re.search(r'sdk\.initialize\s*\(\s*\)', content))
    checks.append({
        "name": "sdk.initialize() is called",
        "passed": has_initialize,
        "detail": "Found sdk.initialize()" if has_initialize else "Missing: await sdk.initialize()"
    })

    # CHECK 4: createFastVault (NOT createSecureVault)
    has_fast_vault = bool(re.search(r'createFastVault\s*\(', content))
    has_secure_vault = bool(re.search(r'createSecureVault\s*\(', content))
    fast_vault_correct = has_fast_vault and not has_secure_vault
    checks.append({
        "name": "createFastVault is used (not createSecureVault)",
        "passed": fast_vault_correct,
        "detail": (
            "Correctly uses createFastVault" if fast_vault_correct
            else (
                "Found createSecureVault instead of createFastVault (wrong for autonomous agents)"
                if has_secure_vault else "Missing createFastVault call"
            )
        )
    })

    # CHECK 5: verifyVault
    has_verify = bool(re.search(r'verifyVault\s*\(', content))
    checks.append({
        "name": "verifyVault is called to complete vault creation",
        "passed": has_verify,
        "detail": "Found verifyVault()" if has_verify else "Missing: sdk.verifyVault(vaultId, code) — required 2-step vault creation"
    })

    # CHECK 6: vault.address('Ethereum')
    has_eth_address = bool(re.search(r"vault\.address\s*\(\s*['\"]Ethereum['\"]\s*\)", content))
    checks.append({
        "name": "vault.address('Ethereum') called for address retrieval",
        "passed": has_eth_address,
        "detail": "Found vault.address('Ethereum')" if has_eth_address else "Missing: vault.address('Ethereum')"
    })

    # CHECK 7: addAddressBookEntry with both BTC and ETH contacts
    has_address_book = bool(re.search(r'addAddressBookEntry\s*\(', content))
    has_btc_contact = bool(re.search(r'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', content))
    has_eth_contact = bool(re.search(r'0x742d35Cc6634C0532925a3b844Bc454e4438f44e', content, re.IGNORECASE))
    has_bitcoin_chain = bool(re.search(r"['\"]Bitcoin['\"]", content))
    address_book_ok = has_address_book and has_btc_contact and has_eth_contact
    checks.append({
        "name": "addAddressBookEntry used with both BTC and ETH contacts",
        "passed": address_book_ok,
        "detail": (
            f"addAddressBookEntry: {has_address_book}, BTC addr: {has_btc_contact}, ETH addr: {has_eth_contact}"
        )
    })

    # CHECK 8: vault.balance('Ethereum') for native ETH
    has_eth_balance = bool(re.search(r"vault\.balance\s*\(\s*['\"]Ethereum['\"]\s*\)", content))
    checks.append({
        "name": "vault.balance('Ethereum') called for native ETH balance",
        "passed": has_eth_balance,
        "detail": "Found vault.balance('Ethereum')" if has_eth_balance else "Missing: vault.balance('Ethereum')"
    })

    # CHECK 9: vault.balance('Ethereum', '<USDC contract>') for token balance
    usdc_contract = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    has_usdc_balance = bool(re.search(
        r"vault\.balance\s*\(\s*['\"]Ethereum['\"]\s*,\s*['\"]" + re.escape(usdc_contract) + r"['\"]",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "vault.balance('Ethereum', '0xA0b86991...') called for USDC token balance",
        "passed": has_usdc_balance,
        "detail": (
            f"Found token balance query with USDC contract address"
            if has_usdc_balance
            else f"Missing: vault.balance('Ethereum', '{usdc_contract}') — token balance requires contract address as 2nd arg"
        )
    })

    # CHECK 10: prepareSendTx uses BigInt for USDC amount (50000000)
    # Must be BigInt('50000000') or BigInt(50000000) or 50000000n
    has_bigint_amount = bool(re.search(
        r"BigInt\s*\(\s*['\"]?50000000['\"]?\s*\)|50000000n",
        content
    ))
    checks.append({
        "name": "prepareSendTx uses BigInt for USDC amount (50000000)",
        "passed": has_bigint_amount,
        "detail": "Found BigInt(50000000) or 50000000n" if has_bigint_amount else "Missing: amount must be bigint for prepareSendTx, e.g., BigInt('50000000') for 50 USDC"
    })

    # CHECK 11: USDC send coin has 'id' field with contract address
    # Check that in prepareSendTx context there is an 'id' field with the USDC contract
    has_id_field = bool(re.search(
        r"id\s*:\s*['\"]" + re.escape(usdc_contract) + r"['\"]",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "USDC send includes 'id' field with contract address",
        "passed": has_id_field,
        "detail": "Found id: '<USDC contract>' in coin object" if has_id_field else f"Missing: id: '{usdc_contract}' in coin object for USDC send"
    })

    # CHECK 12: 3-step send flow (prepareSendTx -> sign -> broadcastTx)
    has_prepare_send = bool(re.search(r'prepareSendTx\s*\(', content))
    has_sign = bool(re.search(r'vault\.sign\s*\(', content))
    has_broadcast = bool(re.search(r'broadcastTx\s*\(', content))
    three_step_ok = has_prepare_send and has_sign and has_broadcast
    checks.append({
        "name": "3-step send flow: prepareSendTx → sign → broadcastTx",
        "passed": three_step_ok,
        "detail": f"prepareSendTx: {has_prepare_send}, sign: {has_sign}, broadcastTx: {has_broadcast}"
    })

    # CHECK 13: getSwapQuote amount is number 0.5 (not bigint)
    # Should see: amount: 0.5 in getSwapQuote context
    # Check that swap amount 0.5 appears as a number literal (not bigint)
    has_swap_amount_number = bool(re.search(r'getSwapQuote', content)) and bool(re.search(r'amount\s*:\s*0\.5(?!\s*n)', content))
    # Also verify it's not BigInt(0.5) or similar
    has_swap_bigint = bool(re.search(r'amount\s*:\s*BigInt.*0\.5|0\.5n', content))
    swap_amount_ok = has_swap_amount_number and not has_swap_bigint
    checks.append({
        "name": "getSwapQuote amount is number 0.5 (not bigint)",
        "passed": swap_amount_ok,
        "detail": "Found amount: 0.5 as number for getSwapQuote" if swap_amount_ok else "Missing or wrong: getSwapQuote requires amount as plain number (0.5), not bigint"
    })

    # CHECK 14: prepareSwapTx is called
    has_prepare_swap = bool(re.search(r'prepareSwapTx\s*\(', content))
    checks.append({
        "name": "prepareSwapTx is called after getSwapQuote",
        "passed": has_prepare_swap,
        "detail": "Found prepareSwapTx()" if has_prepare_swap else "Missing: vault.prepareSwapTx() — required step between getSwapQuote and signing"
    })

    # CHECK 15: approvalPayload check before swap
    has_approval_check = bool(re.search(r'approvalPayload', content))
    checks.append({
        "name": "approvalPayload check and conditional sign+broadcast before swap",
        "passed": has_approval_check,
        "detail": "Found approvalPayload handling" if has_approval_check else "Missing: must check swapResult.approvalPayload and handle token approval before swap execution"
    })

    # CHECK 16: 4-step swap flow (getSwapQuote -> prepareSwapTx -> sign -> broadcastTx)
    has_get_quote = bool(re.search(r'getSwapQuote\s*\(', content))
    four_step_ok = has_get_quote and has_prepare_swap and has_sign and has_broadcast
    checks.append({
        "name": "4-step swap: getSwapQuote → prepareSwapTx → sign → broadcastTx",
        "passed": four_step_ok,
        "detail": f"getSwapQuote: {has_get_quote}, prepareSwapTx: {has_prepare_swap}, sign: {has_sign}, broadcastTx: {has_broadcast}"
    })

    # CHECK 17: PascalCase chain identifiers
    # Must NOT use lowercase chain names
    has_lowercase_ethereum = bool(re.search(r"['\"]ethereum['\"]", content))
    has_lowercase_bitcoin = bool(re.search(r"['\"]bitcoin['\"]", content))
    has_lowercase_solana = bool(re.search(r"['\"]solana['\"]", content))
    has_pascal_ethereum = bool(re.search(r"['\"]Ethereum['\"]", content))
    pascal_case_ok = has_pascal_ethereum and not has_lowercase_ethereum and not has_lowercase_bitcoin
    checks.append({
        "name": "Chain identifiers use PascalCase (Ethereum, Bitcoin, etc.)",
        "passed": pascal_case_ok,
        "detail": (
            "Correct PascalCase chain identifiers" if pascal_case_ok
            else f"lowercase 'ethereum': {has_lowercase_ethereum}, lowercase 'bitcoin': {has_lowercase_bitcoin}, PascalCase 'Ethereum': {has_pascal_ethereum}"
        )
    })

    # CHECK 18: getTxExplorerUrl called
    has_explorer_url = bool(re.search(r'getTxExplorerUrl\s*\(', content))
    checks.append({
        "name": "Vultisig.getTxExplorerUrl called for swap tx hash",
        "passed": has_explorer_url,
        "detail": "Found Vultisig.getTxExplorerUrl()" if has_explorer_url else "Missing: Vultisig.getTxExplorerUrl('Ethereum', txHash)"
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "evaluation_error", "passed": False, "detail": str(e)}]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()