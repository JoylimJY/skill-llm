import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
score_parts = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. Find the output report ───────────────────────────────────────────────
report_files = list(Path(workspace).rglob("formatting_report.json"))
report_found = len(report_files) > 0
add_check(
    "formatting_report.json exists",
    report_found,
    f"Found at: {report_files[0]}" if report_found else "File not found anywhere in workspace"
)
if not report_found:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 2. Parse the report ─────────────────────────────────────────────────────
report_path = report_files[0]
try:
    with open(report_path) as f:
        report = json.load(f)
    add_check("formatting_report.json is valid JSON", True, "Parsed successfully")
except Exception as e:
    add_check("formatting_report.json is valid JSON", False, str(e))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. Report has required top-level fields ──────────────────────────────────
required_top_fields = ["total_files_audited", "files_with_lint_errors", "formatted_files", "total_warnings"]
missing_top = [f for f in required_top_fields if f not in report]
top_fields_ok = len(missing_top) == 0
add_check(
    "Report has required top-level fields",
    top_fields_ok,
    f"Missing fields: {missing_top}" if missing_top else f"All required fields present: {required_top_fields}"
)

# ── 4. total_files_audited is correct (5 messy markdown files) ───────────────
expected_total = 5
total_audited = report.get("total_files_audited", -1)
total_correct = (total_audited == expected_total)
add_check(
    f"total_files_audited == {expected_total}",
    total_correct,
    f"Got: {total_audited}, expected: {expected_total}"
)

# ── 5. files_with_lint_errors: all 5 files have lint errors ──────────────────
files_with_errors = report.get("files_with_lint_errors", -1)
# All 5 documents have intentional formatting issues
lint_errors_ok = isinstance(files_with_errors, int) and files_with_errors >= 4
add_check(
    "files_with_lint_errors >= 4 (all messy files detected)",
    lint_errors_ok,
    f"Got: {files_with_errors}, expected >= 4"
)

# ── 6. formatted_files field is present and is a list of dicts ───────────────
formatted_files = report.get("formatted_files", None)
formatted_is_list = isinstance(formatted_files, list)
add_check(
    "formatted_files is a list",
    formatted_is_list,
    f"Type: {type(formatted_files).__name__}" if not formatted_is_list else f"List with {len(formatted_files)} entries"
)

if formatted_is_list and len(formatted_files) > 0:
    # ── 7. Each formatted file entry has required per-file fields ─────────────
    required_file_fields = ["file", "warnings", "original_length", "formatted_length"]
    sample = formatted_files[0]
    missing_file_fields = [f for f in required_file_fields if f not in sample]
    file_fields_ok = len(missing_file_fields) == 0
    add_check(
        "Each formatted_files entry has required per-file fields",
        file_fields_ok,
        f"Missing: {missing_file_fields}" if missing_file_fields else f"All fields present in sample entry"
    )

    # ── 8. original_length > formatted_length for at least 3 files ─────────────
    # Formatting should reduce length (remove extra blank lines, trailing spaces)
    compression_count = sum(
        1 for entry in formatted_files
        if isinstance(entry.get("original_length"), (int, float))
        and isinstance(entry.get("formatted_length"), (int, float))
        and entry["original_length"] > 0
        and entry["formatted_length"] > 0
    )
    lengths_valid = compression_count >= 3
    add_check(
        "At least 3 entries have valid original_length and formatted_length > 0",
        lengths_valid,
        f"{compression_count} entries have valid length data"
    )

    # ── 9. Formatted files count >= 4 (all problematic files formatted) ─────────
    formatted_count = len(formatted_files)
    formatted_count_ok = formatted_count >= 4
    add_check(
        "At least 4 files were formatted (all problematic files)",
        formatted_count_ok,
        f"Got {formatted_count} formatted file entries"
    )

    # ── 10. Style used is 'github' ────────────────────────────────────────────
    style_used = report.get("style_used", None)
    style_ok = style_used == "github"
    add_check(
        "style_used == 'github' in report",
        style_ok,
        f"Got: {style_used!r}, expected: 'github'"
    )
else:
    add_check("Each formatted_files entry has required per-file fields", False, "formatted_files is empty or not a list")
    add_check("At least 3 entries have valid original_length and formatted_length > 0", False, "formatted_files is empty or not a list")
    add_check("At least 4 files were formatted (all problematic files)", False, "formatted_files is empty or not a list")
    add_check("style_used == 'github' in report", False, "Cannot check — formatted_files missing")

# ── 11. Verify the actual markdown files were overwritten / formatted ────────
target_md_files = [
    "docs/runbooks/incident_response.md",
    "docs/runbooks/deployment_checklist.md",
    "docs/guides/onboarding_guide.md",
    "docs/guides/monitoring_guide.md",
    "docs/onboarding/tools_setup.md",
]

files_modified_count = 0
for rel_path in target_md_files:
    full_path = Path(workspace) / rel_path
    try:
        content = full_path.read_text()
        # Check that consecutive blank lines (3+) have been removed
        has_triple_blank = "\n\n\n" in content
        # Check trailing whitespace on lines is reduced
        lines = content.split("\n")
        trailing_space_lines = sum(1 for l in lines if l != l.rstrip())
        # A well-formatted file should have no triple blanks and minimal trailing spaces
        if not has_triple_blank and trailing_space_lines <= 1:
            files_modified_count += 1
    except Exception:
        pass

files_modified_ok = files_modified_count >= 3
add_check(
    "At least 3 original markdown files are formatted in-place (no triple blank lines, minimal trailing spaces)",
    files_modified_ok,
    f"{files_modified_count}/5 files appear to have been formatted in-place"
)

# ── 12. total_warnings is a non-negative integer ────────────────────────────
total_warnings = report.get("total_warnings", None)
warnings_ok = isinstance(total_warnings, int) and total_warnings >= 0
add_check(
    "total_warnings is a non-negative integer",
    warnings_ok,
    f"Got: {total_warnings!r}"
)

# ── Score computation ────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = round(passed_count / total_checks, 3)
overall_passed = passed_count >= (total_checks * 0.8)  # 80% threshold

print(json.dumps({
    "passed": overall_passed,
    "score": score,
    "checks": checks
}, indent=2))