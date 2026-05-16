import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(workspace.rglob("pausable_erc20.cairo"))
    if not candidates:
        # also accept PausableERC20.cairo or pausable_token.cairo as reasonable
        candidates = list(workspace.rglob("PausableERC20.cairo")) + list(workspace.rglob("pausable_token.cairo"))

    if not candidates:
        checks.append(check("file_exists", False, "No pausable_erc20.cairo (or PausableERC20.cairo/pausable_token.cairo) found in workspace."))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    filepath = candidates[0]
    checks.append(check("file_exists", True, f"Found contract file at: {filepath}"))

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_readable", True, "File is readable."))

    # ── CHECK 1: Uses #[starknet::contract] module declaration ────────────────
    has_contract_attr = bool(re.search(r'#\[starknet::contract\]', content))
    checks.append(check(
        "starknet_contract_attribute",
        has_contract_attr,
        "#[starknet::contract] attribute found." if has_contract_attr else "Missing #[starknet::contract] attribute — required by Cairo 2 / StarkNet."
    ))

    # ── CHECK 2: Storage struct has #[storage] and includes required fields ───
    has_storage_attr = bool(re.search(r'#\[storage\]', content))
    checks.append(check(
        "storage_attribute",
        has_storage_attr,
        "#[storage] attribute found." if has_storage_attr else "Missing #[storage] attribute on Storage struct."
    ))

    # owner field in storage
    has_owner_storage = bool(re.search(r'owner\s*:\s*ContractAddress', content))
    checks.append(check(
        "storage_owner_field",
        has_owner_storage,
        "owner: ContractAddress found in Storage." if has_owner_storage else "Missing 'owner: ContractAddress' in Storage struct."
    ))

    # paused field in storage (bool type)
    has_paused_storage = bool(re.search(r'paused\s*:\s*bool', content))
    checks.append(check(
        "storage_paused_field",
        has_paused_storage,
        "paused: bool found in Storage." if has_paused_storage else "Missing 'paused: bool' in Storage struct — required for pause functionality."
    ))

    # balances LegacyMap
    has_balances = bool(re.search(r'balances\s*:\s*LegacyMap\s*<\s*ContractAddress\s*,\s*u256\s*>', content))
    checks.append(check(
        "storage_balances_legacymap",
        has_balances,
        "balances: LegacyMap<ContractAddress, u256> found." if has_balances else "Missing 'balances: LegacyMap<ContractAddress, u256>' in Storage."
    ))

    # ── CHECK 3: Event enum with #[event] and #[derive(Drop, starknet::Event)] ─
    has_event_attr = bool(re.search(r'#\[event\]', content))
    checks.append(check(
        "event_attribute",
        has_event_attr,
        "#[event] attribute found." if has_event_attr else "Missing #[event] attribute on Event enum."
    ))

    has_event_derive = bool(re.search(r'#\[derive\([^)]*starknet::Event[^)]*\)\]', content))
    checks.append(check(
        "event_derive_starknet",
        has_event_derive,
        "#[derive(..., starknet::Event)] found." if has_event_derive else "Missing #[derive(Drop, starknet::Event)] on Event enum or structs."
    ))

    # ── CHECK 4: Paused and Unpaused event variants in the Event enum ─────────
    has_paused_variant = bool(re.search(r'Paused\s*:\s*Paused', content))
    checks.append(check(
        "event_paused_variant",
        has_paused_variant,
        "Paused: Paused event variant found in Event enum." if has_paused_variant else "Missing 'Paused: Paused' variant in Event enum."
    ))

    has_unpaused_variant = bool(re.search(r'Unpaused\s*:\s*Unpaused', content))
    checks.append(check(
        "event_unpaused_variant",
        has_unpaused_variant,
        "Unpaused: Unpaused event variant found in Event enum." if has_unpaused_variant else "Missing 'Unpaused: Unpaused' variant in Event enum."
    ))

    # ── CHECK 5: Paused/Unpaused event structs with #[key] indexed field ──────
    has_paused_struct = bool(re.search(
        r'struct\s+Paused\s*\{[^}]*#\[key\][^}]*account\s*:\s*ContractAddress[^}]*\}',
        content, re.DOTALL
    ))
    checks.append(check(
        "paused_event_struct",
        has_paused_struct,
        "Paused event struct with #[key] account: ContractAddress found." if has_paused_struct
        else "Missing Paused event struct with '#[key] account: ContractAddress'."
    ))

    # ── CHECK 6: Transfer and Approval events preserved from ERC20 template ───
    has_transfer_variant = bool(re.search(r'Transfer\s*:\s*Transfer', content))
    checks.append(check(
        "event_transfer_variant",
        has_transfer_variant,
        "Transfer: Transfer event variant preserved." if has_transfer_variant else "Missing Transfer: Transfer in Event enum."
    ))

    has_approval_variant = bool(re.search(r'Approval\s*:\s*Approval', content))
    checks.append(check(
        "event_approval_variant",
        has_approval_variant,
        "Approval: Approval event variant preserved." if has_approval_variant else "Missing Approval: Approval in Event enum."
    ))

    # ── CHECK 7: pause() function emits Paused event and writes to storage ────
    has_pause_fn = bool(re.search(r'fn\s+pause\s*\(', content))
    checks.append(check(
        "pause_function_exists",
        has_pause_fn,
        "pause() function found." if has_pause_fn else "Missing pause() function."
    ))

    has_pause_write = bool(re.search(r'self\.paused\.write\s*\(\s*true\s*\)', content))
    checks.append(check(
        "pause_writes_storage",
        has_pause_write,
        "self.paused.write(true) found in pause logic." if has_pause_write else "Missing self.paused.write(true) call."
    ))

    has_pause_emit = bool(re.search(r'self\.emit\s*\(\s*Paused\s*\{', content))
    checks.append(check(
        "pause_emits_event",
        has_pause_emit,
        "self.emit(Paused { ... }) found." if has_pause_emit else "Missing self.emit(Paused { ... }) in pause function."
    ))

    # ── CHECK 8: unpause() function emits Unpaused event ─────────────────────
    has_unpause_fn = bool(re.search(r'fn\s+unpause\s*\(', content))
    checks.append(check(
        "unpause_function_exists",
        has_unpause_fn,
        "unpause() function found." if has_unpause_fn else "Missing unpause() function."
    ))

    has_unpause_write = bool(re.search(r'self\.paused\.write\s*\(\s*false\s*\)', content))
    checks.append(check(
        "unpause_writes_storage",
        has_unpause_write,
        "self.paused.write(false) found." if has_unpause_write else "Missing self.paused.write(false) call."
    ))

    has_unpause_emit = bool(re.search(r'self\.emit\s*\(\s*Unpaused\s*\{', content))
    checks.append(check(
        "unpause_emits_event",
        has_unpause_emit,
        "self.emit(Unpaused { ... }) found." if has_unpause_emit else "Missing self.emit(Unpaused { ... }) in unpause function."
    ))

    # ── CHECK 9: transfer() function guards against paused state ──────────────
    # Must check paused state before allowing transfer
    has_transfer_pause_guard = bool(re.search(
        r'fn\s+transfer\b[^}]+paused\.read\(\)',
        content, re.DOTALL
    ))
    if not has_transfer_pause_guard:
        # More lenient: check that assert appears with !paused or paused == false near transfer
        has_transfer_pause_guard = bool(re.search(
            r'fn\s+transfer\b[^}]+assert[^}]+paused',
            content, re.DOTALL
        ))
    checks.append(check(
        "transfer_pause_guard",
        has_transfer_pause_guard,
        "transfer() checks paused state." if has_transfer_pause_guard else "transfer() does not guard against paused state."
    ))

    # ── CHECK 10: Does NOT use Cairo v0 syntax ────────────────────────────────
    uses_old_syntax = bool(re.search(r'%lang starknet|@storage_var|@external|@view', content))
    checks.append(check(
        "no_cairo_v0_syntax",
        not uses_old_syntax,
        "No Cairo v0 syntax detected." if not uses_old_syntax else "File uses Cairo v0 syntax (%lang, @storage_var, etc.) — must use Cairo 2."
    ))

    # ── CHECK 11: Uses get_caller_address for owner checks ────────────────────
    has_caller = bool(re.search(r'get_caller_address', content))
    checks.append(check(
        "uses_get_caller_address",
        has_caller,
        "get_caller_address() usage found." if has_caller else "Missing get_caller_address() — needed for owner/access control."
    ))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Must pass critical checks to be considered passing overall
    critical = [
        "starknet_contract_attribute",
        "storage_attribute",
        "storage_paused_field",
        "event_attribute",
        "event_derive_starknet",
        "paused_event_struct",
        "pause_function_exists",
        "pause_writes_storage",
        "pause_emits_event",
        "unpause_function_exists",
        "unpause_emits_event",
        "no_cairo_v0_syntax",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))