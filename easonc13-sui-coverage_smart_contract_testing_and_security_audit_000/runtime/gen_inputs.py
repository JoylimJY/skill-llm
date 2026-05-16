#!/usr/bin/env python3
"""
Generate the sandbox workspace for the sui-coverage task.
Creates a Sui Move package with intentional coverage gaps,
the skill's Python tools, and a mock `sui` binary.
"""
import os
import stat
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── 1. Directory structure ────────────────────────────────────────────────────
dirs = [
    "vault_package/sources",
    "vault_package/tests",
    "skills/sui-coverage",
    "skills/sui-coverage/lib",
    "docs",
    "scripts",
    "archive/old_tests",
    "archive/old_sources",
    "deployment/configs",
    "deployment/scripts",
    "audit_reports",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Move.toml ──────────────────────────────────────────────────────────────
(WORKSPACE / "vault_package/Move.toml").write_text(textwrap.dedent("""\
    [package]
    name = "vault"
    version = "1.0.0"
    edition = "2024.beta"

    [dependencies]
    Sui = { git = "https://github.com/MystenLabs/sui.git", subdir = "crates/sui-framework/packages/sui-framework", rev = "framework-testnet" }

    [addresses]
    vault = "0x0"
"""))

# ── 3. Main vault module ───────────────────────────────────────────────────────
# This module has THREE intentional coverage gaps:
#   A) `emergency_pause()` is never called in any test
#   B) `withdraw()` assert failure path (EInsufficientFunds) not tested
#   C) `classify_deposit()` else-branch (amount >= 1000) not tested
vault_source = textwrap.dedent("""\
    module vault::vault {
        use sui::object::{Self, UID};
        use sui::tx_context::{Self, TxContext};
        use sui::transfer;

        // ── Error codes ──────────────────────────────────────────────────────
        const EInsufficientFunds: u64 = 1;
        const EVaultPaused: u64 = 2;
        const EUnauthorized: u64 = 3;

        // ── Structs ──────────────────────────────────────────────────────────
        struct Vault has key, store {
            id: UID,
            balance: u64,
            owner: address,
            paused: bool,
        }

        struct AdminCap has key, store {
            id: UID,
        }

        // ── Constructor ──────────────────────────────────────────────────────
        public fun create_vault(ctx: &mut TxContext): Vault {
            Vault {
                id: object::new(ctx),
                balance: 0,
                owner: tx_context::sender(ctx),
                paused: false,
            }
        }

        // ── Deposit ──────────────────────────────────────────────────────────
        public fun deposit(vault: &mut Vault, amount: u64) {
            assert!(!vault.paused, EVaultPaused);
            vault.balance = vault.balance + amount;
        }

        // ── Withdraw ─────────────────────────────────────────────────────────
        public fun withdraw(vault: &mut Vault, amount: u64, ctx: &TxContext) {
            assert!(!vault.paused, EVaultPaused);
            assert!(vault.owner == tx_context::sender(ctx), EUnauthorized);
            assert!(vault.balance >= amount, EInsufficientFunds);
            vault.balance = vault.balance - amount;
        }

        // ── Emergency pause (GAP A: never tested) ───────────────────────────
        public fun emergency_pause(vault: &mut Vault, ctx: &TxContext) {
            assert!(vault.owner == tx_context::sender(ctx), EUnauthorized);
            vault.paused = true;
        }

        // ── Classify deposit amount (GAP C: large-amount branch not tested) ─
        public fun classify_deposit(amount: u64): u8 {
            if (amount == 0) {
                0  // zero deposit
            } else if (amount < 1000) {
                1  // small deposit
            } else {
                2  // large deposit  ← this branch never executed
            }
        }

        // ── Getters ──────────────────────────────────────────────────────────
        public fun get_balance(vault: &Vault): u64 {
            vault.balance
        }

        public fun is_paused(vault: &Vault): bool {
            vault.paused
        }

        public fun destroy_vault(vault: Vault) {
            let Vault { id, balance: _, owner: _, paused: _ } = vault;
            object::delete(id);
        }
    }
""")

(WORKSPACE / "vault_package/sources/vault.move").write_text(vault_source)

# ── 4. Existing partial test file (intentionally incomplete) ──────────────────
existing_tests = textwrap.dedent("""\
    #[test_only]
    module vault::vault_tests {
        use vault::vault;
        use sui::tx_context;

        // Tests deposit happy path
        #[test]
        fun test_deposit_basic() {
            let mut ctx = tx_context::dummy();
            let mut v = vault::create_vault(&mut ctx);
            vault::deposit(&mut v, 500);
            assert!(vault::get_balance(&v) == 500, 0);
            vault::destroy_vault(v);
        }

        // Tests withdraw happy path
        #[test]
        fun test_withdraw_basic() {
            let mut ctx = tx_context::dummy();
            let mut v = vault::create_vault(&mut ctx);
            vault::deposit(&mut v, 200);
            vault::withdraw(&mut v, 100, &ctx);
            assert!(vault::get_balance(&v) == 100, 0);
            vault::destroy_vault(v);
        }

        // Tests classify_deposit for zero
        #[test]
        fun test_classify_zero() {
            assert!(vault::classify_deposit(0) == 0, 0);
        }

        // Tests classify_deposit for small amount
        #[test]
        fun test_classify_small() {
            assert!(vault::classify_deposit(50) == 1, 0);
        }
    }
""")

(WORKSPACE / "vault_package/tests/vault_tests.move").write_text(existing_tests)

# ── 5. Mock `sui` CLI binary ──────────────────────────────────────────────────
# This mock interprets common sui commands and produces realistic output.
# It also writes trace/coverage files that analyze_source.py will read.
mock_sui = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Mock sui CLI for coverage testing.\"\"\"
    import sys
    import os
    import json
    from pathlib import Path

    args = sys.argv[1:]

    # Determine package path (cwd)
    cwd = Path(os.getcwd())

    def find_package_root():
        \"\"\"Walk up to find Move.toml\"\"\"
        p = cwd
        for _ in range(5):
            if (p / "Move.toml").exists():
                return p
            p = p.parent
        return cwd

    pkg = find_package_root()

    if args[:2] == ["move", "test"] or args[:3] == ["move", "test", "--coverage"]:
        coverage = "--coverage" in args
        trace = "--trace" in args

        # Read source to determine which functions exist
        src = pkg / "sources" / "vault.move"
        test_src = pkg / "tests" / "vault_tests.move"

        # Simulate test output
        print("BUILDING")
        print("   Compiling vault v1.0.0")
        print("RUNNING TESTS")
        print("   [ PASS    ] vault::vault_tests::test_deposit_basic")
        print("   [ PASS    ] vault::vault_tests::test_withdraw_basic")
        print("   [ PASS    ] vault::vault_tests::test_classify_zero")
        print("   [ PASS    ] vault::vault_tests::test_classify_small")

        # Check if new tests exist in the test file
        if test_src.exists():
            content = test_src.read_text()
            extra_tests = []
            if "emergency_pause" in content and "#[test]" in content:
                extra_tests.append("test_emergency_pause")
                print("   [ PASS    ] vault::vault_tests::test_emergency_pause")
            if "EInsufficientFunds" in content or "insufficient" in content.lower():
                extra_tests.append("test_withdraw_insufficient")
                print("   [ PASS    ] vault::vault_tests::test_withdraw_insufficient_funds")
            if "classify_deposit" in content and ("1000" in content or "large" in content.lower()):
                extra_tests.append("test_classify_large")
                print("   [ PASS    ] vault::vault_tests::test_classify_large_deposit")

        print("")
        print(f"Test result: ok. Tests passed")

        if coverage or trace:
            # Write a .trace file that analyze_source.py will read
            trace_data = {
                "module": "vault",
                "package": str(pkg),
                "covered_functions": [
                    "create_vault",
                    "deposit",
                    "withdraw",
                    "classify_deposit",
                    "get_balance",
                    "destroy_vault",
                    "is_paused"
                ],
                "uncovered_functions": ["emergency_pause"],
                "covered_lines": list(range(1, 45)) + list(range(48, 60)) + list(range(62, 70)),
                "covered_assertions": [
                    {"line": 34, "desc": "assert!(!vault.paused, EVaultPaused) in deposit - pass path"},
                    {"line": 40, "desc": "assert!(!vault.paused, EVaultPaused) in withdraw - pass path"},
                    {"line": 41, "desc": "assert!(vault.owner == sender, EUnauthorized) in withdraw - pass path"},
                    {"line": 42, "desc": "assert!(vault.balance >= amount, EInsufficientFunds) in withdraw - pass path"},
                ],
                "uncovered_assertions": [
                    {"line": 42, "desc": "assert!(vault.balance >= amount, EInsufficientFunds) - FAILURE path not tested"},
                ],
                "covered_branches": [
                    {"line": 52, "branch": "if amount == 0 => true"},
                    {"line": 54, "branch": "if amount < 1000 => true"},
                ],
                "uncovered_branches": [
                    {"line": 56, "branch": "else (amount >= 1000) in classify_deposit - never executed"},
                ],
                "total_lines": 75,
                "covered_lines_count": 58,
            }
            trace_file = pkg / ".coverage_trace.json"
            trace_file.write_text(json.dumps(trace_data, indent=2))

            # Also write lcov.info style file
            lcov = pkg / "lcov.info"
            lcov.write_text(
                "SF:sources/vault.move\\n"
                "FN:10,create_vault\\n"
                "FN:18,deposit\\n"
                "FN:24,withdraw\\n"
                "FN:32,emergency_pause\\n"
                "FN:38,classify_deposit\\n"
                "FN:48,get_balance\\n"
                "FN:52,is_paused\\n"
                "FN:56,destroy_vault\\n"
                "FNDA:1,create_vault\\n"
                "FNDA:1,deposit\\n"
                "FNDA:1,withdraw\\n"
                "FNDA:0,emergency_pause\\n"
                "FNDA:1,classify_deposit\\n"
                "FNDA:1,get_balance\\n"
                "FNDA:1,is_paused\\n"
                "FNDA:1,destroy_vault\\n"
                "FNF:8\\n"
                "FNH:7\\n"
                "DA:10,1\\nDA:18,1\\nDA:24,1\\nDA:32,0\\nDA:38,1\\n"
                "BRDA:38,0,0,1\\nBRDA:40,0,0,1\\nBRDA:42,0,0,0\\n"
                "BRF:3\\nBRH:2\\n"
                "end_of_record\\n"
            )

    elif args[:3] == ["move", "coverage", "lcov"]:
        pkg_lcov = pkg / "lcov.info"
        if pkg_lcov.exists():
            print(pkg_lcov.read_text())
        else:
            print("No coverage data. Run `sui move test --coverage` first.")
            sys.exit(1)

    elif args[:3] == ["move", "coverage", "bytecode"]:
        mod = None
        for i, a in enumerate(args):
            if a == "--module" and i+1 < len(args):
                mod = args[i+1]
        print(f"Bytecode coverage for module: {mod or 'unknown'}")
        print("Function: create_vault -> covered: yes")
        print("Function: emergency_pause -> covered: NO")
        print("Function: classify_deposit branch 2 -> covered: NO")

    elif args[:1] == ["--version"]:
        print("sui 1.22.0-homebrew")

    else:
        print(f"sui: unknown command {' '.join(args)}")
        sys.exit(1)
""")

sui_bin = WORKSPACE / "bin" / "sui"
(WORKSPACE / "bin").mkdir(exist_ok=True)
sui_bin.write_text(mock_sui)
sui_bin.chmod(sui_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 6. analyze_source.py skill tool ───────────────────────────────────────────
analyze_source = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    analyze_source.py - Primary coverage analysis tool for Sui Move modules.
    Reads source files + .coverage_trace.json to produce a coverage report.
    \"\"\"
    import argparse
    import json
    import sys
    import os
    import re
    from pathlib import Path

    def find_package_root(start: Path) -> Path:
        p = start
        for _ in range(6):
            if (p / "Move.toml").exists():
                return p
            p = p.parent
        return start

    def parse_source(src_file: Path):
        \"\"\"Parse Move source to extract functions and assertions.\"\"\"
        text = src_file.read_text()
        functions = []
        # Match function definitions
        for m in re.finditer(r'(public\\s+)?fun\\s+(\\w+)\\s*\\(', text):
            functions.append(m.group(2))
        assertions = []
        for i, line in enumerate(text.splitlines(), 1):
            if 'assert!' in line:
                assertions.append({"line": i, "text": line.strip()})
        branches = []
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r'\\bif\\s*\\(', line):
                branches.append({"line": i, "text": line.strip()})
        return functions, assertions, branches

    def load_trace(pkg_root: Path):
        trace_file = pkg_root / ".coverage_trace.json"
        if trace_file.exists():
            return json.loads(trace_file.read_text())
        return None

    def generate_report(module: str, pkg_root: Path, trace, src_file: Path) -> str:
        functions, assertions, branches = parse_source(src_file)
        lines = []
        lines.append(f"# Coverage Report: {module}\\n")

        if trace is None:
            lines.append("⚠️  No coverage trace found. Run `sui move test --coverage --trace` first.\\n")
            return "\\n".join(lines)

        pct = round(trace['covered_lines_count'] / trace['total_lines'] * 100, 1)
        lines.append(f"## Summary")
        lines.append(f"- **Coverage:** {pct}% ({trace['covered_lines_count']}/{trace['total_lines']} lines)")
        lines.append(f"- **Covered functions:** {len(trace['covered_functions'])}/{len(functions)}")
        lines.append("")

        # Uncalled functions
        uncalled = trace.get("uncovered_functions", [])
        lines.append("## 🔴 Uncalled Functions")
        if uncalled:
            for fn in uncalled:
                lines.append(f"- `{fn}()` — never executed in any test")
        else:
            lines.append("- ✅ All functions called")
        lines.append("")

        # Uncovered assertions
        unc_assert = trace.get("uncovered_assertions", [])
        lines.append("## 🔴 Uncovered Assertions (Failure Paths)")
        if unc_assert:
            for a in unc_assert:
                lines.append(f"- Line {a['line']}: {a['desc']}")
        else:
            lines.append("- ✅ All assertion paths tested")
        lines.append("")

        # Uncovered branches
        unc_branch = trace.get("uncovered_branches", [])
        lines.append("## 🔴 Uncovered Branches")
        if unc_branch:
            for b in unc_branch:
                lines.append(f"- Line {b['line']}: {b['branch']}")
        else:
            lines.append("- ✅ All branches covered")
        lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        if uncalled:
            lines.append(f"1. Write tests for uncalled functions: {', '.join(uncalled)}")
        if unc_assert:
            lines.append(f"2. Write #[expected_failure] tests for assertion failure paths")
        if unc_branch:
            lines.append(f"3. Write branch-coverage tests for uncovered if/else paths")
        lines.append("")
        lines.append("## Error Constants in vault module")
        lines.append("- `EInsufficientFunds: u64 = 1`")
        lines.append("- `EVaultPaused: u64 = 2`")
        lines.append("- `EUnauthorized: u64 = 3`")
        lines.append("")

        return "\\n".join(lines)

    def main():
        parser = argparse.ArgumentParser(description="Analyze Sui Move coverage")
        parser.add_argument("-m", "--module", required=True, help="Module name")
        parser.add_argument("-p", "--path", default=".", help="Package path")
        parser.add_argument("-o", "--output", help="Output file")
        parser.add_argument("--json", action="store_true", help="JSON output")
        parser.add_argument("--markdown", action="store_true", help="Markdown to stdout")
        args = parser.parse_args()

        pkg_root = find_package_root(Path(args.path).resolve())
        src_file = pkg_root / "sources" / f"{args.module}.move"

        if not src_file.exists():
            print(f"Error: source file not found: {src_file}", file=sys.stderr)
            sys.exit(1)

        trace = load_trace(pkg_root)
        report = generate_report(args.module, pkg_root, trace, src_file)

        if args.output:
            out = Path(args.output)
            out.write_text(report)
            print(f"Coverage report written to {out}")
        else:
            print(report)

        if args.json:
            if trace:
                print(json.dumps(trace, indent=2))

    if __name__ == "__main__":
        main()
""")

(WORKSPACE / "skills/sui-coverage/analyze_source.py").write_text(analyze_source)
(WORKSPACE / "skills/sui-coverage/analyze_source.py").chmod(
    (WORKSPACE / "skills/sui-coverage/analyze_source.py").stat().st_mode | stat.S_IEXEC
)

# ── 7. analyze.py (LCOV statistics tool) ──────────────────────────────────────
analyze_py = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"analyze.py - LCOV statistics for Sui Move coverage.\"\"\"
    import argparse
    import sys
    import json
    from pathlib import Path

    def parse_lcov(lcov_text: str, filter_str: str = None, source_dir: str = None, issues_only: bool = False):
        records = []
        current = {}
        for line in lcov_text.splitlines():
            line = line.strip()
            if line.startswith("SF:"):
                current = {"file": line[3:], "functions": {}, "lines": {}, "branches": {}}
            elif line.startswith("FNDA:"):
                parts = line[5:].split(",", 1)
                if len(parts) == 2:
                    current["functions"][parts[1]] = int(parts[0])
            elif line.startswith("DA:"):
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    current["lines"][parts[0]] = int(parts[1])
            elif line == "end_of_record":
                if current:
                    records.append(current)
                current = {}

        results = []
        for rec in records:
            if filter_str and filter_str not in rec["file"]:
                continue
            total_fn = len(rec["functions"])
            covered_fn = sum(1 for v in rec["functions"].values() if v > 0)
            total_lines = len(rec["lines"])
            covered_lines = sum(1 for v in rec["lines"].values() if v > 0)
            uncovered_fns = [k for k, v in rec["functions"].items() if v == 0]
            has_issues = bool(uncovered_fns) or covered_lines < total_lines
            if issues_only and not has_issues:
                continue
            results.append({
                "file": rec["file"],
                "function_coverage": f"{covered_fn}/{total_fn}",
                "line_coverage": f"{covered_lines}/{total_lines}",
                "uncovered_functions": uncovered_fns,
                "has_issues": has_issues,
            })
        return results

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("lcov_file")
        parser.add_argument("-f", "--filter", default=None)
        parser.add_argument("-s", "--source-dir", default=None)
        parser.add_argument("-i", "--issues-only", action="store_true")
        parser.add_argument("-j", "--json", action="store_true")
        args = parser.parse_args()

        lcov_path = Path(args.lcov_file)
        if not lcov_path.exists():
            print(f"Error: {lcov_path} not found", file=sys.stderr)
            sys.exit(1)

        results = parse_lcov(lcov_path.read_text(), args.filter, args.source_dir, args.issues_only)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"File: {r['file']}")
                print(f"  Functions: {r['function_coverage']}")
                print(f"  Lines: {r['line_coverage']}")
                if r['uncovered_functions']:
                    print(f"  Uncovered functions: {', '.join(r['uncovered_functions'])}")
                print()

    if __name__ == "__main__":
        main()
""")

(WORKSPACE / "skills/sui-coverage/analyze.py").write_text(analyze_py)

# ── 8. parse_bytecode.py ───────────────────────────────────────────────────────
parse_bc = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"parse_bytecode.py - Parse bytecode coverage output.\"\"\"
    import sys

    for line in sys.stdin:
        line = line.strip()
        if line:
            print(f"[bytecode] {line}")
""")
(WORKSPACE / "skills/sui-coverage/parse_bytecode.py").write_text(parse_bc)

# ── 9. Distractor files ────────────────────────────────────────────────────────
(WORKSPACE / "docs/architecture.md").write_text("# Vault Architecture\nThis is the DeFi vault contract.\n")
(WORKSPACE / "docs/api.md").write_text("# API Reference\nSee sources/vault.move for details.\n")
(WORKSPACE / "docs/deployment.md").write_text("# Deployment Guide\nDeploy using `sui client publish`.\n")
(WORKSPACE / "scripts/deploy.sh").write_text("#!/bin/bash\necho 'Deploy script placeholder'\n")
(WORKSPACE / "scripts/setup_env.sh").write_text("#!/bin/bash\nexport SUI_ENV=testnet\n")
(WORKSPACE / "archive/old_tests/vault_v0_tests.move").write_text(
    "// Old test file - do not use\n#[test]\nfun test_old() { }\n"
)
(WORKSPACE / "archive/old_sources/vault_v0.move").write_text(
    "// Deprecated vault v0\nmodule vault::vault_v0 { }\n"
)
(WORKSPACE / "deployment/configs/testnet.json").write_text(
    json.dumps({"network": "testnet", "gas_budget": 10000000}, indent=2)
)
(WORKSPACE / "deployment/configs/mainnet.json").write_text(
    json.dumps({"network": "mainnet", "gas_budget": 50000000}, indent=2)
)
(WORKSPACE / "audit_reports/.gitkeep").write_text("")
(WORKSPACE / "skills/sui-coverage/lib/__init__.py").write_text("# sui-coverage library\n")
(WORKSPACE / "skills/sui-coverage/README.md").write_text(
    "# sui-coverage\nSee SKILL.md for documentation.\n"
)

# ── 10. Workspace-level README placeholder (no hints) ─────────────────────────
(WORKSPACE / "PROJECT.md").write_text(textwrap.dedent("""\
    # DeFi Vault Project
    A Sui Move smart contract for secure token vaulting.

    ## Status
    - Contract: Complete
    - Tests: Partial (needs improvement before mainnet launch)
    - Audit: Pending
"""))

print("Workspace generated successfully.")
print(f"Package: {WORKSPACE / 'vault_package'}")
print(f"Skills: {WORKSPACE / 'skills/sui-coverage'}")
print(f"Mock sui: {WORKSPACE / 'bin/sui'}")