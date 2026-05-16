import sys
import os
import json
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1]
checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

# ─── 1. Spec stubs: correct docstring format ─────────────────────────────────
# The agent MUST produce 4 stubs (4 criteria) with the exact format from SKILL.md
# Required: `/// Spec: specs/tracking-id.spec.md — Criterion #N`  (em-dash U+2014)
# and function names: tracking_id_criterion_N_<slug>

tracking_id_src = Path(workspace) / "crates" / "tracking-utils" / "src" / "tracking_id.rs"

try:
    src = tracking_id_src.read_text()
except Exception as e:
    check("tracking_id.rs exists", False, str(e))
    # emit remaining checks as failed
    for n in ["spec_docstring_format", "four_criteria_stubs", "cfg_test_module",
              "stubs_use_todo_macro", "function_naming_convention",
              "implementation_present", "cargo_test_passes",
              "ralph_emit_called", "ralph_emit_coverage_evidence"]:
        check(n, False, "Source file missing")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

check("tracking_id.rs exists", True)

# ─── 2. Docstring format — must contain the em-dash (—) not a hyphen ─────────
spec_doc_pattern = re.compile(
    r'///\s+Spec:\s+.*tracking-id\.spec\.md\s+\u2014\s+Criterion\s+#\d'
)
spec_doc_matches = spec_doc_pattern.findall(src)
check(
    "spec_docstring_format",
    len(spec_doc_matches) >= 1,
    f"Found {len(spec_doc_matches)} correctly-formatted '/// Spec:' docstrings (need em-dash \u2014, not hyphen)"
)

# ─── 3. Exactly 4 criterion stubs or test functions generated ─────────────────
criterion_fn_pattern = re.compile(
    r'fn\s+tracking_id_criterion_\d+_\w+'
)
criterion_fns = criterion_fn_pattern.findall(src)
check(
    "four_criteria_stubs",
    len(criterion_fns) >= 4,
    f"Found {len(criterion_fns)} criterion test functions (need >= 4 for 4 spec criteria)"
)

# ─── 4. Tests are inside #[cfg(test)] (inline, not separate test file) ────────
# Single module => inline tests per SKILL.md
cfg_test_present = "#[cfg(test)]" in src
check(
    "cfg_test_module",
    cfg_test_present,
    "Must use inline #[cfg(test)] module (spec maps to single module)"
)

# ─── 5. todo!() macro appears at least once (stubs before implementation) ─────
# After implementation the todo!() calls should be replaced, but the agent
# workflow requires them at stub stage; we check implementation exists instead
todo_or_impl = "todo!" in src or "TrackingId" in src
check(
    "stubs_use_todo_macro_or_implementation",
    todo_or_impl,
    "Either todo!() stubs or full implementation must be present"
)

# ─── 6. Implementation: TrackingId struct or type is defined ─────────────────
impl_present = bool(re.search(r'(pub\s+struct\s+TrackingId|pub\s+fn\s+parse|fn\s+parse)', src))
check(
    "implementation_present",
    impl_present,
    "TrackingId struct or parse function must be implemented (GREEN phase)"
)

# ─── 7. cargo test passes for the tracking-utils crate ───────────────────────
try:
    result = subprocess.run(
        ["cargo", "test", "-p", "tracking-utils", "--", "--test-output=immediate"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180
    )
    cargo_passed = result.returncode == 0
    detail = result.stdout[-2000:] + result.stderr[-1000:] if not cargo_passed else "All tests passed"
    check("cargo_test_passes", cargo_passed, detail)
except Exception as e:
    check("cargo_test_passes", False, str(e))

# ─── 8. ralph emit was called ────────────────────────────────────────────────
ralph_log = Path(workspace) / ".ralph_events.log"
try:
    ralph_content = ralph_log.read_text()
    ralph_called = "build.done" in ralph_content
    check("ralph_emit_called", ralph_called,
          f"ralph_events.log content: {ralph_content[:500]}" if ralph_content else "Log empty")
except Exception as e:
    check("ralph_emit_called", False, str(e))

# ─── 9. ralph emit contains coverage evidence in correct format ───────────────
try:
    ralph_content = ralph_log.read_text()
    # Must contain the exact keys: "tests: pass" and "coverage: pass"
    has_tests_pass = "tests: pass" in ralph_content
    has_coverage = "coverage: pass" in ralph_content or "coverage: " in ralph_content
    # Must follow: "tests: pass, lint: pass, typecheck: pass, audit: pass, coverage: pass (XX%)"
    coverage_format = re.search(
        r'tests: pass.*coverage: (pass|[0-9]+%)',
        ralph_content
    )
    check(
        "ralph_emit_coverage_evidence",
        has_tests_pass and has_coverage,
        f"ralph log snippet: {ralph_content[:600]}"
    )
except Exception as e:
    check("ralph_emit_coverage_evidence", False, str(e))

# ─── Score ────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
overall = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": overall,
    "score": score,
    "checks": checks
}, indent=2))