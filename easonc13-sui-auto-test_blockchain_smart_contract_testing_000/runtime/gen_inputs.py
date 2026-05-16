#!/usr/bin/env python3
"""
Generate the sandbox workspace for the sui-coverage task.
Creates a realistic Sui Move DeFi vault package with partial test coverage.
"""

import os
import random
import stat
from pathlib import Path

# Fixed seed for determinism
random.seed(42)

WORKSPACE = Path("/workspace")

# ============================================================
# 1. Create the Sui Move package structure
# ============================================================
pkg_dir = WORKSPACE / "defi_vault"
sources_dir = pkg_dir / "sources"
tests_dir = pkg_dir / "tests"
build_dir = pkg_dir / "build"

for d in [sources_dir, tests_dir, build_dir / "defi_vault" / "sources"]:
    d.mkdir(parents=True, exist_ok=True)

# Move.toml
(pkg_dir / "Move.toml").write_text("""\
[package]
name = "defi_vault"
version = "0.0.1"
edition = "2024.beta"

[dependencies]
Sui = { git = "https://github.com/MystenLabs/sui.git", subdir = "crates/sui-framework/packages/sui-framework", rev = "framework-testnet" }

[addresses]
defi_vault = "0x0"
""")

# Main vault module - the primary subject of coverage analysis
vault_move = """\
module defi_vault::vault {
    use sui::tx_context::{Self, TxContext};
    use sui::object::{Self, UID};
    use sui::transfer;

    // === Error Codes ===
    const EInsufficientBalance: u64 = 1;
    const ENotOwner: u64 = 2;
    const EDepositTooSmall: u64 = 3;
    const EVaultFrozen: u64 = 4;
    const EInvalidRiskTier: u64 = 5;

    // === Structs ===
    struct Vault has key, store {
        id: UID,
        owner: address,
        balance: u64,
        is_frozen: bool,
        total_deposited: u64,
        total_withdrawn: u64,
    }

    struct AdminCap has key {
        id: UID,
    }

    // === Constants ===
    const MIN_DEPOSIT: u64 = 100;
    const MAX_BALANCE: u64 = 1_000_000_000;

    // === Public Functions ===

    public fun create_vault(ctx: &mut TxContext): Vault {
        Vault {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
            balance: 0,
            is_frozen: false,
            total_deposited: 0,
            total_withdrawn: 0,
        }
    }

    public fun deposit(vault: &mut Vault, amount: u64, ctx: &TxContext) {
        assert!(!vault.is_frozen, EVaultFrozen);
        assert!(amount >= MIN_DEPOSIT, EDepositTooSmall);
        assert!(vault.balance + amount <= MAX_BALANCE, EInsufficientBalance);

        vault.balance = vault.balance + amount;
        vault.total_deposited = vault.total_deposited + amount;
    }

    public fun withdraw(vault: &mut Vault, amount: u64, ctx: &TxContext) {
        assert!(!vault.is_frozen, EVaultFrozen);
        assert!(tx_context::sender(ctx) == vault.owner, ENotOwner);
        assert!(vault.balance >= amount, EInsufficientBalance);

        vault.balance = vault.balance - amount;
        vault.total_withdrawn = vault.total_withdrawn + amount;
    }

    public fun classify_risk(balance: u64): u8 {
        if (balance == 0) {
            0
        } else if (balance < 10_000) {
            1
        } else if (balance < 100_000) {
            2
        } else {
            3
        }
    }

    public fun emergency_pause(vault: &mut Vault, _cap: &AdminCap) {
        vault.is_frozen = true;
    }

    public fun emergency_resume(vault: &mut Vault, _cap: &AdminCap) {
        vault.is_frozen = false;
    }

    public fun get_balance(vault: &Vault): u64 {
        vault.balance
    }

    public fun get_owner(vault: &Vault): address {
        vault.owner
    }

    public fun is_frozen(vault: &Vault): bool {
        vault.is_frozen
    }

    public fun get_total_deposited(vault: &Vault): u64 {
        vault.total_deposited
    }

    public fun get_total_withdrawn(vault: &Vault): u64 {
        vault.total_withdrawn
    }

    public fun compute_net_flow(vault: &Vault): u64 {
        if (vault.total_deposited >= vault.total_withdrawn) {
            vault.total_deposited - vault.total_withdrawn
        } else {
            0
        }
    }

    public fun destroy_empty_vault(vault: Vault) {
        let Vault { id, owner: _, balance, is_frozen: _, total_deposited: _, total_withdrawn: _ } = vault;
        assert!(balance == 0, EInsufficientBalance);
        object::delete(id);
    }

    // === Test-only helpers ===
    #[test_only]
    public fun create_admin_cap(ctx: &mut TxContext): AdminCap {
        AdminCap { id: object::new(ctx) }
    }

    #[test_only]
    public fun destroy_admin_cap(cap: AdminCap) {
        let AdminCap { id } = cap;
        object::delete(id);
    }

    #[test_only]
    public fun destroy_vault_for_testing(vault: Vault) {
        let Vault { id, owner: _, balance: _, is_frozen: _, total_deposited: _, total_withdrawn: _ } = vault;
        object::delete(id);
    }
}
"""
(sources_dir / "vault.move").write_text(vault_move)

# Partial test file - covers only basic happy paths, MISSING many cases
vault_tests_partial = """\
#[test_only]
module defi_vault::vault_tests {
    use defi_vault::vault::{Self, Vault};
    use sui::tx_context;

    // Tests create_vault and basic deposit - happy path only
    #[test]
    fun test_create_and_deposit() {
        let mut ctx = tx_context::dummy();
        let mut vault = vault::create_vault(&mut ctx);
        
        vault::deposit(&mut vault, 500, &ctx);
        assert!(vault::get_balance(&vault) == 500, 0);
        assert!(vault::get_total_deposited(&vault) == 500, 0);
        
        vault::destroy_vault_for_testing(vault);
    }

    // Tests withdraw happy path
    #[test]
    fun test_withdraw_success() {
        let mut ctx = tx_context::dummy();
        let mut vault = vault::create_vault(&mut ctx);
        
        vault::deposit(&mut vault, 1000, &ctx);
        vault::withdraw(&mut vault, 400, &ctx);
        
        assert!(vault::get_balance(&vault) == 600, 0);
        assert!(vault::get_total_withdrawn(&vault) == 400, 0);
        
        vault::destroy_vault_for_testing(vault);
    }

    // Tests classify_risk for low-tier only
    #[test]
    fun test_classify_risk_low() {
        assert!(vault::classify_risk(5000) == 1, 0);
    }
}
"""
(tests_dir / "vault_tests.move").write_text(vault_tests_partial)

# ============================================================
# 2. Distractor files to test contextual awareness
# ============================================================

# Old/stale coverage report (outdated, misleading)
(pkg_dir / "coverage_old.md").write_text("""\
# Coverage Report (STALE - DO NOT USE)
Generated: 2023-01-01

## vault
- create_vault: ✅ covered
- deposit: ✅ covered
- withdraw: ✅ covered
- classify_risk: ✅ covered
- emergency_pause: ✅ covered

Coverage: 100%

NOTE: This file is from a previous analysis run and is no longer valid.
""")

# Fake security notes file
(pkg_dir / "NOTES.txt").write_text("""\
Dev notes:
- Need to add more tests for edge cases
- Check if emergency_pause is tested
- TODO: Test frozen vault behavior
- Ask team about overflow scenarios
""")

# Build artifacts (distractors)
(build_dir / "defi_vault" / "sources" / "vault.mv").write_bytes(bytes(range(256)) * 4)

# Random config file
(pkg_dir / ".sui" / "config").write_text("""\
[network]
rpc_url = "https://fullnode.testnet.sui.io"
""") if (pkg_dir / ".sui").mkdir(exist_ok=True) or True else None

# Additional distractor modules (not to be tested)
(sources_dir / "events.move").write_text("""\
module defi_vault::events {
    struct DepositEvent has copy, drop {
        amount: u64,
        vault_id: address,
    }
    struct WithdrawEvent has copy, drop {
        amount: u64,
        vault_id: address,
    }
}
""")

(sources_dir / "math_utils.move").write_text("""\
module defi_vault::math_utils {
    public fun safe_add(a: u64, b: u64): u64 {
        a + b
    }
    public fun safe_sub(a: u64, b: u64): u64 {
        if (a >= b) { a - b } else { 0 }
    }
    public fun percent(value: u64, bps: u64): u64 {
        value * bps / 10000
    }
}
""")

# Leftover temp files
(pkg_dir / "tmp_analysis.txt").write_text("Temp file from previous session - ignore\n")
(pkg_dir / "scratch.py").write_text("# scratch work\nprint('hello')\n")

# Git-like structure
git_dir = pkg_dir / ".git"
git_dir.mkdir(exist_ok=True)
(git_dir / "HEAD").write_text("ref: refs/heads/main\n")
(git_dir / "config").write_text("""\
[core]
    repositoryformatversion = 0
    filemode = true
""")

# Another partial test file for a different module (distractor)
(tests_dir / "math_utils_tests.move").write_text("""\
#[test_only]
module defi_vault::math_utils_tests {
    use defi_vault::math_utils;

    #[test]
    fun test_safe_add() {
        assert!(math_utils::safe_add(3, 4) == 7, 0);
    }

    #[test]
    fun test_safe_sub() {
        assert!(math_utils::safe_sub(10, 3) == 7, 0);
        assert!(math_utils::safe_sub(3, 10) == 0, 0);
    }

    #[test]
    fun test_percent() {
        assert!(math_utils::percent(10000, 500) == 500, 0);
    }
}
""")

# Previous failed attempt at tests (wrong syntax, commented out)
(tests_dir / "vault_tests_draft.move.bak").write_text("""\
// DRAFT - BROKEN - DO NOT USE
// #[test]
// fun test_emergency_pause_broken() {
//     let cap = AdminCap { id: 999 }; // wrong, can't construct directly
//     vault.emergency_pause(&cap);
// }
""")

# ============================================================
# 3. Skill directory - create the actual tools
# ============================================================
skill_dir = Path("/root/clawd/skills/sui-coverage")
skill_dir.mkdir(parents=True, exist_ok=True)

# analyze_source.py - Smart mock that parses Move source
analyze_source_py = r'''#!/usr/bin/env python3
"""
analyze_source.py - Sui Move Coverage Analyzer
Parses Move source and test files to identify coverage gaps.
"""

import argparse
import re
import sys
import os
import json
from pathlib import Path

def find_package_root(start_path):
    """Find Move.toml to identify package root."""
    p = Path(start_path).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "Move.toml").exists():
            return parent
    return p

def parse_functions(source: str):
    """Extract public/entry function names from Move source."""
    # Match public fun, public entry fun, entry fun (not test_only)
    pattern = r'(?<!#\[test_only\]\s{0,200})(?:public\s+(?:entry\s+)?|entry\s+)fun\s+(\w+)\s*[(<]'
    fns = re.findall(pattern, source)
    return [f for f in fns if not f.startswith('_')]

def parse_all_functions(source: str):
    """Extract ALL function names including private ones."""
    pattern = r'^\s*(?:public\s+(?:entry\s+)?|entry\s+|)fun\s+(\w+)\s*[(<]'
    fns = re.findall(pattern, source, re.MULTILINE)
    return [f for f in fns if not f.startswith('_') and f != 'test']

def parse_assert_patterns(source: str):
    """Find assert! calls and their error codes."""
    pattern = r'assert!\s*\(([^,]+),\s*(\w+)\s*\)'
    return re.findall(pattern, source)

def parse_branches(source: str, fn_name: str):
    """Find if/else branches in a function."""
    # Find function body
    fn_pattern = rf'fun\s+{re.escape(fn_name)}\s*[(<][^{{]*\{{(.*?)(?=\n\s*(?:public|entry|#|\}})\s*(?:fun|struct|const)|\Z)'
    match = re.search(fn_pattern, source, re.DOTALL)
    if not match:
        return 0
    body = match.group(1)
    # Count if statements
    ifs = len(re.findall(r'\bif\s*\(', body))
    return ifs

def parse_test_calls(test_source: str):
    """Extract which functions are called in tests."""
    # Find test function bodies
    test_pattern = r'#\[test[^\]]*\]\s*(?:#\[expected_failure[^\]]*\]\s*)?fun\s+\w+\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
    calls = set()
    for test_body in re.findall(test_pattern, test_source, re.DOTALL):
        # Find vault:: calls
        fn_calls = re.findall(r'vault::(\w+)\s*\(', test_body)
        calls.update(fn_calls)
    return calls

def parse_expected_failures(test_source: str):
    """Extract error codes covered by expected_failure tests."""
    pattern = r'#\[expected_failure\s*\(\s*abort_code\s*=\s*(\w+(?:::\w+)?)\s*\)\]'
    return set(re.findall(pattern, test_source))

def load_sources(package_path, module_name):
    """Load main module source and test sources."""
    pkg = Path(package_path)
    
    # Find main source
    main_source = None
    for src_file in (pkg / "sources").glob("*.move"):
        content = src_file.read_text()
        if f"module {module_name.replace('::', ' ')}".replace(' ', '::') in content or \
           re.search(rf'module\s+[\w:]*{re.escape(module_name.split("::")[-1])}\s*\{{', content):
            main_source = content
            break
    
    if main_source is None:
        # Try by filename
        candidate = pkg / "sources" / f"{module_name}.move"
        if candidate.exists():
            main_source = candidate.read_text()
    
    # Load test sources
    test_sources = []
    for test_file in (pkg / "tests").glob("*.move"):
        test_sources.append(test_file.read_text())
    # Also check sources for #[test] blocks
    for src_file in (pkg / "sources").glob("*.move"):
        content = src_file.read_text()
        if '#[test' in content:
            test_sources.append(content)
    
    return main_source, "\n".join(test_sources)

def analyze(package_path, module_name):
    """Main analysis function."""
    main_source, test_source = load_sources(package_path, module_name)
    
    if not main_source:
        print(f"ERROR: Could not find source for module '{module_name}'", file=sys.stderr)
        sys.exit(1)
    
    # Parse source elements
    all_fns = parse_all_functions(main_source)
    # Filter out test_only helpers
    test_only_section = re.search(r'#\[test_only\](.*)', main_source, re.DOTALL)
    test_only_fns = set()
    if test_only_section:
        test_only_fns = set(re.findall(r'fun\s+(\w+)\s*[(<]', test_only_section.group(1)))
    
    public_fns = [f for f in all_fns if f not in test_only_fns]
    assert_patterns = parse_assert_patterns(main_source)
    
    # Parse test elements  
    test_calls = parse_test_calls(test_source)
    expected_failures = parse_expected_failures(test_source)
    
    # Determine uncovered items
    uncalled_fns = [f for f in public_fns if f not in test_calls]
    
    # Error constants defined in module
    error_consts = dict(re.findall(r'const\s+(E\w+)\s*:\s*u64\s*=\s*(\d+)', main_source))
    
    # Check which assertion errors are covered
    uncovered_assertions = []
    for cond, err_code in assert_patterns:
        # err_code is the constant name
        err_name = err_code.strip()
        # Check if this error is covered by expected_failure
        covered = False
        for ef in expected_failures:
            ef_short = ef.split("::")[-1]
            if ef_short == err_name or ef == err_name:
                covered = True
                break
        if not covered:
            uncovered_assertions.append((cond.strip(), err_name))
    
    # Check branches for key functions with branches
    uncovered_branches = []
    branch_fns = ['classify_risk', 'compute_net_flow', 'deposit', 'withdraw']
    for fn in branch_fns:
        if fn in public_fns:
            num_branches = parse_branches(main_source, fn)
            if num_branches > 1:
                # Check how many test variants exist
                test_variants = len(re.findall(rf'vault::{re.escape(fn)}\s*\(', test_source))
                if test_variants < num_branches:
                    uncovered_branches.append((fn, num_branches, test_variants))
    
    return {
        "module": module_name,
        "public_functions": public_fns,
        "test_calls": list(test_calls),
        "uncalled_functions": uncalled_fns,
        "assert_patterns": assert_patterns,
        "error_constants": error_consts,
        "uncovered_assertions": uncovered_assertions,
        "uncovered_branches": uncovered_branches,
        "expected_failures_covered": list(expected_failures),
    }

def format_markdown(data):
    """Format analysis as markdown report."""
    lines = [
        f"# Coverage Analysis: {data['module']}",
        "",
        "## Summary",
        f"- Total public functions: {len(data['public_functions'])}",
        f"- Functions called in tests: {len(data['test_calls'])}",
        f"- **Uncalled functions: {len(data['uncalled_functions'])}**",
        f"- **Uncovered assertion paths: {len(data['uncovered_assertions'])}**",
        f"- **Uncovered branch groups: {len(data['uncovered_branches'])}**",
        "",
        "## Function Coverage",
        "",
    ]
    
    for fn in data['public_functions']:
        if fn in data['test_calls']:
            lines.append(f"- ✅ `{fn}()`")
        else:
            lines.append(f"- 🔴 **`{fn}()`** - UNCALLED: No test exercises this function")
    
    lines += ["", "## Assertion Failure Paths", ""]
    
    if data['uncovered_assertions']:
        for cond, err in data['uncovered_assertions']:
            lines.append(f"- 🔴 **`assert!({cond}, {err})`** - Failure path not tested")
    else:
        lines.append("- ✅ All assertion failure paths covered")
    
    lines += ["", "## Branch Coverage", ""]
    
    if data['uncovered_branches']:
        for fn, total, tested in data['uncovered_branches']:
            lines.append(f"- 🔴 **`{fn}()`** - {tested}/{total} branches tested")
    else:
        lines.append("- ✅ All branches covered")
    
    lines += ["", "## Error Constants", ""]
    for name, val in data['error_constants'].items():
        covered = any(
            name in ef or ef.endswith(name)
            for ef in data['expected_failures_covered']
        )
        status = "✅" if covered else "🔴"
        lines.append(f"- {status} `{name} = {val}`")
    
    lines += [
        "",
        "## Coverage Assessment",
        "",
    ]
    
    total_issues = len(data['uncalled_functions']) + len(data['uncovered_assertions']) + len(data['uncovered_branches'])
    if total_issues == 0:
        lines.append("✅ **FULL COVERAGE ACHIEVED** - All functions, branches, and assertion paths are tested.")
    else:
        lines.append(f"🔴 **{total_issues} coverage gaps found** - Add tests for the items marked 🔴 above.")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Sui Move Coverage Analyzer")
    parser.add_argument("-m", "--module", required=True, help="Module name")
    parser.add_argument("-p", "--path", default=".", help="Package path")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--markdown", action="store_true", help="Markdown to stdout")
    
    args = parser.parse_args()
    
    data = analyze(args.path, args.module)
    
    if args.json:
        output = json.dumps(data, indent=2)
    else:
        output = format_markdown(data)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Coverage report written to: {args.output}")
        # Also print summary to stdout
        total_issues = len(data['uncalled_functions']) + len(data['uncovered_assertions']) + len(data['uncovered_branches'])
        if total_issues > 0:
            print(f"⚠️  {total_issues} coverage gaps found.")
            print("Uncalled:", data['uncalled_functions'])
            print("Uncovered assertions:", data['uncovered_assertions'])
            print("Uncovered branches:", data['uncovered_branches'])
        else:
            print("✅ Full coverage achieved!")
    else:
        print(output)

if __name__ == "__main__":
    main()
'''

(skill_dir / "analyze_source.py").write_text(analyze_source_py)
os.chmod(skill_dir / "analyze_source.py", 0o755)

# analyze.py - LCOV statistics tool
analyze_py = r'''#!/usr/bin/env python3
"""analyze.py - LCOV Statistics Analyzer for Sui Move"""
import argparse, sys, re, json
from pathlib import Path

def parse_lcov(lcov_file, filter_pat=None, source_dir=None):
    results = {}
    current_file = None
    lines_found = lines_hit = 0
    try:
        with open(lcov_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("SF:"):
                    current_file = line[3:]
                    lines_found = lines_hit = 0
                elif line.startswith("LF:"):
                    lines_found = int(line[3:])
                elif line.startswith("LH:"):
                    lines_hit = int(line[3:])
                elif line == "end_of_record":
                    if current_file and (not filter_pat or filter_pat in current_file):
                        pct = (lines_hit / lines_found * 100) if lines_found else 0
                        results[current_file] = {"lines_found": lines_found, "lines_hit": lines_hit, "pct": pct}
    except FileNotFoundError:
        print(f"Error: {lcov_file} not found. Run 'sui move coverage lcov' first.", file=sys.stderr)
        sys.exit(1)
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lcov_file")
    parser.add_argument("-f", "--filter", default=None)
    parser.add_argument("-s", "--source-dir", default=None)
    parser.add_argument("-i", "--issues-only", action="store_true")
    parser.add_argument("-j", "--json", action="store_true")
    args = parser.parse_args()
    
    results = parse_lcov(args.lcov_file, args.filter, args.source_dir)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for fname, data in results.items():
            if args.issues_only and data["pct"] >= 100:
                continue
            print(f"{fname}: {data['lines_hit']}/{data['lines_found']} lines ({data['pct']:.1f}%)")

if __name__ == "__main__":
    main()
'''
(skill_dir / "analyze.py").write_text(analyze_py)
os.chmod(skill_dir / "analyze.py", 0o755)

# parse_bytecode.py
parse_bytecode_py = r'''#!/usr/bin/env python3
"""parse_bytecode.py - Low-level bytecode coverage parser"""
import sys
for line in sys.stdin:
    line = line.strip()
    if line and not line.startswith('#'):
        print(f"  BYTECODE: {line}")
'''
(skill_dir / "parse_bytecode.py").write_text(parse_bytecode_py)
os.chmod(skill_dir / "parse_bytecode.py", 0o755)

print("Workspace generated successfully.")
print(f"Package: {pkg_dir}")
print(f"Skill tools: {skill_dir}")
print("\nUncovered items the agent must fix:")
print("  1. emergency_pause() - uncalled function")
print("  2. emergency_resume() - uncalled function")
print("  3. destroy_empty_vault() - uncalled function")
print("  4. compute_net_flow() - uncalled function")
print("  5. classify_risk() - only 1 of 4 branches tested (missing 0, >=10000, >=100000)")
print("  6. EVaultFrozen assertion failure path - not tested")
print("  7. ENotOwner assertion failure path - not tested")
print("  8. EDepositTooSmall assertion failure path - not tested")
print("  9. EInsufficientBalance from deposit (overflow) - not tested")