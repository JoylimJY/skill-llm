#!/usr/bin/env python3
"""
Evaluation script for arh-pr-workflow task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

def load_log(path: Path) -> list[str]:
    try:
        return [line.strip() for line in path.read_text().splitlines() if line.strip()]
    except Exception as e:
        return []

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    arh_log_path     = workspace / "arh_invocations.log"
    gitbzl_log_path  = workspace / "git_bzl_invocations.log"

    arh_lines    = load_log(arh_log_path)
    gitbzl_lines = load_log(gitbzl_log_path)

    arh_text    = " ||| ".join(arh_lines)
    gitbzl_text = " ||| ".join(gitbzl_lines)

    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def any_line_matches(lines, pattern):
        """Return the first line matching pattern, or None."""
        rx = re.compile(pattern)
        for ln in lines:
            if rx.search(ln):
                return ln
        return None

    def lines_in_order(lines, patterns):
        """Check that all patterns appear in lines in the given order."""
        idx = 0
        matched = []
        for ln in lines:
            if idx < len(patterns) and re.search(patterns[idx], ln):
                matched.append(ln)
                idx += 1
        return idx == len(patterns), matched

    # ── CHECK 1: `arh feature payment-gateway` (base feature from main) ───────
    m = any_line_matches(arh_lines, r'^arh feature payment-gateway$')
    checks.append(check(
        "create_base_feature_payment_gateway",
        m is not None,
        f"Expected 'arh feature payment-gateway' (no 'next'). Found: {m!r}"
    ))

    # ── CHECK 2: `arh feature next payment-logging` (stacked on top) ──────────
    m = any_line_matches(arh_lines, r'^arh feature next payment-logging$')
    checks.append(check(
        "create_stacked_feature_payment_logging",
        m is not None,
        f"Expected 'arh feature next payment-logging'. Found: {m!r}"
    ))

    # ── CHECK 3: payment-gateway must be created BEFORE payment-logging ────────
    ok, matched = lines_in_order(arh_lines, [
        r'arh feature payment-gateway',
        r'arh feature next payment-logging',
    ])
    checks.append(check(
        "feature_creation_order",
        ok,
        f"payment-gateway must be created before payment-logging. Matched sequence: {matched}"
    ))

    # ── CHECK 4: publish --full-stack with --changes-planned (draft WIP) ───────
    # Must have both flags; --no-interactive is also required
    m = any_line_matches(arh_lines,
        r'^arh publish(?=.*--full-stack)(?=.*--changes-planned)(?=.*--no-interactive).*$')
    checks.append(check(
        "publish_full_stack_draft_no_interactive",
        m is not None,
        (
            "Expected 'arh publish' with ALL THREE flags: --full-stack, --changes-planned, --no-interactive "
            f"(in any order). Found matching line: {m!r}. "
            f"All arh publish lines: {[l for l in arh_lines if 'publish' in l]}"
        )
    ))

    # ── CHECK 5: `arh pull -r` to pull from main and rebase ───────────────────
    m = any_line_matches(arh_lines, r'^arh pull\s+-r')
    checks.append(check(
        "pull_with_rebase_flag",
        m is not None,
        f"Expected 'arh pull -r'. Found: {m!r}. All arh lines with pull: {[l for l in arh_lines if 'pull' in l]}"
    ))

    # ── CHECK 6: `git-bzl refresh` called after pull ──────────────────────────
    m = any_line_matches(gitbzl_lines, r'^git-bzl refresh$')
    checks.append(check(
        "git_bzl_refresh_after_pull",
        m is not None,
        f"Expected 'git-bzl refresh' to be called. git-bzl log: {gitbzl_lines!r}"
    ))

    # ── CHECK 7: pull must happen BEFORE git-bzl refresh ──────────────────────
    pull_idx    = next((i for i, l in enumerate(arh_lines) if re.search(r'^arh pull\s+-r', l)), None)
    refresh_idx = next((i for i, l in enumerate(gitbzl_lines) if re.search(r'^git-bzl refresh$', l)), None)
    # We can't compare cross-log indices directly, but we verify both exist.
    # As a proxy: git-bzl log must be non-empty only if arh pull was also called.
    pull_before_refresh = (pull_idx is not None) and (refresh_idx is not None)
    checks.append(check(
        "pull_before_git_bzl_refresh",
        pull_before_refresh,
        f"Both 'arh pull -r' (index {pull_idx}) and 'git-bzl refresh' (index {refresh_idx}) must be present."
    ))

    # ── CHECK 8: `arh rebase` with stack-wide scope (--all or --base) ─────────
    m = any_line_matches(arh_lines, r'^arh rebase\s+(--all|--base\s+\S+)')
    checks.append(check(
        "rebase_entire_stack",
        m is not None,
        (
            "Expected 'arh rebase --all' or 'arh rebase --base <branch>' to rebase the entire stack. "
            f"Found: {m!r}. All rebase lines: {[l for l in arh_lines if 'rebase' in l]}"
        )
    ))

    # ── CHECK 9: rebase happens AFTER pull ────────────────────────────────────
    rebase_idx = next((i for i, l in enumerate(arh_lines) if re.search(r'^arh rebase', l)), None)
    ok = (pull_idx is not None) and (rebase_idx is not None) and (rebase_idx > pull_idx)
    checks.append(check(
        "rebase_after_pull",
        ok,
        f"Rebase (index {rebase_idx}) must come after pull (index {pull_idx}) in arh log."
    ))

    # ── CHECK 10: re-publish with --no-coverage (proprietary flag) ─────────────
    # The agent must use arh publish ... --no-coverage
    # According to SKILL.md this is handled by arh() shell wrapper in ~/.aliases
    # but the flag must appear in the invocation.
    m = any_line_matches(arh_lines, r'^arh publish(?=.*--no-coverage).*$')
    checks.append(check(
        "republish_with_no_coverage_flag",
        m is not None,
        (
            "Expected a second 'arh publish --no-coverage' call (to skip coverage gate). "
            f"Found: {m!r}. All publish lines: {[l for l in arh_lines if 'publish' in l]}"
        )
    ))

    # ── CHECK 11: second publish also uses --full-stack ────────────────────────
    # After rebase, the whole stack should be republished
    m = any_line_matches(arh_lines,
        r'^arh publish(?=.*--no-coverage)(?=.*--full-stack).*$')
    checks.append(check(
        "republish_with_no_coverage_and_full_stack",
        m is not None,
        (
            "The republish after rebase should also include --full-stack. "
            f"Found: {m!r}. All publish lines: {[l for l in arh_lines if 'publish' in l]}"
        )
    ))

    # ── CHECK 12: `arh tidy --no-interactive` for automated cleanup ───────────
    m = any_line_matches(arh_lines, r'^arh tidy\s+--no-interactive')
    checks.append(check(
        "tidy_no_interactive",
        m is not None,
        f"Expected 'arh tidy --no-interactive'. Found: {m!r}. All tidy lines: {[l for l in arh_lines if 'tidy' in l]}"
    ))

    # ── CHECK 13: tidy must come AFTER publish operations ─────────────────────
    tidy_idx = next((i for i, l in enumerate(arh_lines) if re.search(r'^arh tidy', l)), None)
    first_publish_idx = next((i for i, l in enumerate(arh_lines) if re.search(r'^arh publish', l)), None)
    ok = (tidy_idx is not None) and (first_publish_idx is not None) and (tidy_idx > first_publish_idx)
    checks.append(check(
        "tidy_after_publish",
        ok,
        f"Tidy (index {tidy_idx}) must come after first publish (index {first_publish_idx})."
    ))

    # ── CHECK 14: no `arh auth` invoked (already authenticated env) ───────────
    m = any_line_matches(arh_lines, r'^arh auth')
    checks.append(check(
        "no_arh_auth_called",
        m is None,
        f"'arh auth' should NOT be called in an already-configured CI environment. Found: {m!r}"
    ))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total  = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score  = round(passed_count / total, 4)
    passed = passed_count == total

    result = {
        "passed": passed,
        "score":  score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()