import sys
import json
import os
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []
passed_all = True
score = 0.0

def add_check(name, passed, detail):
    global passed_all, score
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Helper: run the lsp-service check on a file ──────────────────────────────
def lsp_check(filepath):
    try:
        r = subprocess.run(
            ["python3", os.path.join(workspace, "scripts", "lsp-service.py"), "check", filepath],
            capture_output=True, text=True, timeout=30
        )
        return r.stdout + r.stderr
    except Exception as e:
        return f"ERROR: {e}"

def pyflakes_check(filepath):
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pyflakes", filepath],
            capture_output=True, text=True, timeout=15
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"ERROR: {e}"

def pycodestyle_check(filepath):
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pycodestyle", "--max-line-length=79", filepath],
            capture_output=True, text=True, timeout=15
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"ERROR: {e}"

# ── CHECK 1: quality_report.json exists ──────────────────────────────────────
report_files = list(Path(workspace).rglob("quality_report.json"))
if not report_files:
    add_check("quality_report.json exists", False, "File 'quality_report.json' not found anywhere in workspace.")
    # Short-circuit remaining checks that depend on this file
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = report_files[0]
add_check("quality_report.json exists", True, f"Found at {report_path}")
score += 0.1

# ── CHECK 2: quality_report.json is valid JSON ────────────────────────────────
try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    add_check("quality_report.json is valid JSON", True, "Parsed successfully.")
    score += 0.1
except Exception as e:
    add_check("quality_report.json is valid JSON", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": score, "checks": checks}))
    sys.exit(0)

# ── CHECK 3: Report contains per-file entries ─────────────────────────────────
# The report must be either a dict keyed by filename or a list of dicts with a file field.
has_per_file = False
file_entries = {}

if isinstance(report, dict):
    # Could be {"files": [...]} or {"filename": {...}, ...}
    if "files" in report and isinstance(report["files"], list):
        for entry in report["files"]:
            if isinstance(entry, dict):
                fname = entry.get("file") or entry.get("filename") or entry.get("path") or ""
                file_entries[fname] = entry
        has_per_file = len(file_entries) > 0
    else:
        # Top-level keys are filenames
        for k, v in report.items():
            if isinstance(v, dict) and k.endswith(".py"):
                file_entries[k] = v
                has_per_file = True
elif isinstance(report, list):
    for entry in report:
        if isinstance(entry, dict):
            fname = entry.get("file") or entry.get("filename") or entry.get("path") or ""
            file_entries[fname] = entry
    has_per_file = len(file_entries) > 0

if not has_per_file:
    add_check("Report has per-file entries", False,
              f"Report structure does not contain recognizable per-file entries. Top-level type: {type(report).__name__}, keys/len: {list(report.keys()) if isinstance(report, dict) else len(report)}")
else:
    add_check("Report has per-file entries", True, f"Found {len(file_entries)} file entries.")
    score += 0.1

# ── CHECK 4: Report covers the 5 key source files ────────────────────────────
expected_files = [
    "fetch_trades.py",
    "normalize.py",
    "write_report.py",
    "validators.py",
    "old_loader.py",
]
covered = []
for ef in expected_files:
    found = any(ef in k for k in file_entries.keys())
    if found:
        covered.append(ef)

if len(covered) >= 4:
    add_check("Report covers key source files", True,
              f"Covered {len(covered)}/5 expected files: {covered}")
    score += 0.15
else:
    add_check("Report covers key source files", False,
              f"Only {len(covered)}/5 expected files covered: {covered}. Need at least 4.")

# ── CHECK 5: Report contains issue counts (before/after or total) ─────────────
# Must have numeric issue counts — not just file names
has_counts = False
for fname, entry in file_entries.items():
    if isinstance(entry, dict):
        vals = list(entry.values())
        if any(isinstance(v, int) for v in vals):
            has_counts = True
            break
        # Also accept nested
        for v in vals:
            if isinstance(v, dict) and any(isinstance(vv, int) for vv in v.values()):
                has_counts = True
                break

if not has_counts:
    # Try checking for "issues", "errors", "warnings", "count" keys
    for fname, entry in file_entries.items():
        if isinstance(entry, dict):
            for k in ["issues", "errors", "warnings", "count", "total", "before", "after",
                      "issue_count", "error_count", "warning_count"]:
                if k in entry:
                    has_counts = True
                    break

add_check("Report contains numeric issue counts", has_counts,
          "Found numeric counts in report entries." if has_counts
          else "No numeric issue counts found in per-file entries.")
if has_counts:
    score += 0.15

# ── CHECK 6: Auto-fix was applied — source files should be cleaner ───────────
# Run pyflakes + pycodestyle on the 5 key files; they should have fewer/no issues

key_files = {
    "fetch_trades.py": "fintech_etl/pipeline/ingestion/fetch_trades.py",
    "normalize.py": "fintech_etl/pipeline/transformation/normalize.py",
    "write_report.py": "fintech_etl/pipeline/output/write_report.py",
    "validators.py": "fintech_etl/utils/validators.py",
    "old_loader.py": "fintech_etl/legacy/old_loader.py",
}

clean_count = 0
clean_details = []
for name, rel_path in key_files.items():
    full_path = os.path.join(workspace, rel_path)
    if not os.path.isfile(full_path):
        clean_details.append(f"{name}: FILE MISSING")
        continue
    pf = pyflakes_check(full_path)
    pc = pycodestyle_check(full_path)
    combined = (pf + "\n" + pc).strip()
    remaining_lines = [l for l in combined.splitlines() if l.strip()]
    if len(remaining_lines) == 0:
        clean_count += 1
        clean_details.append(f"{name}: CLEAN")
    else:
        clean_details.append(f"{name}: {len(remaining_lines)} issues remain")

if clean_count >= 3:
    add_check("Auto-fix applied (files are cleaner)", True,
              f"{clean_count}/5 files are fully clean after fix. Details: {clean_details}")
    score += 0.2
else:
    add_check("Auto-fix applied (files are cleaner)", False,
              f"Only {clean_count}/5 files are clean. The auto-fix does not appear to have been run. "
              f"Details: {clean_details}")

# ── CHECK 7: Categorization by diagnostic source in report ────────────────────
# The report must distinguish pyflakes vs pycodestyle (or equivalent: errors vs warnings)
has_categorization = False
category_keys = ["pyflakes", "pycodestyle", "errors", "warnings", "style", "linting",
                 "error_count", "warning_count", "pyflakes_count", "pycodestyle_count"]

def deep_search_keys(obj, target_keys):
    if isinstance(obj, dict):
        for k in obj:
            if any(t in k.lower() for t in target_keys):
                return True
        for v in obj.values():
            if deep_search_keys(v, target_keys):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if deep_search_keys(item, target_keys):
                return True
    return False

has_categorization = deep_search_keys(report, ["pyflakes", "pycodestyle", "error", "warning", "style"])

add_check("Report categorizes issues by type/source", has_categorization,
          "Report contains category-differentiated counts (e.g., pyflakes vs pycodestyle)."
          if has_categorization
          else "No categorization found — report appears to lump all issues together without source/type labels.")
if has_categorization:
    score += 0.1

# ── CHECK 8: Summary statistics in report ────────────────────────────────────
has_summary = False
summary_keys = ["summary", "total", "total_issues", "total_files", "overall",
                "statistics", "stats", "aggregate"]
if isinstance(report, dict):
    for k in report:
        if any(t in k.lower() for t in summary_keys):
            has_summary = True
            break

add_check("Report includes summary/aggregate statistics", has_summary,
          "Found summary section in report." if has_summary
          else "No top-level summary section found (e.g., 'total_issues', 'summary', etc.).")
if has_summary:
    score += 0.1

# ── Final scoring ─────────────────────────────────────────────────────────────
score = round(min(score, 1.0), 3)
passed_all = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": passed_all,
    "score": score,
    "checks": checks
}))