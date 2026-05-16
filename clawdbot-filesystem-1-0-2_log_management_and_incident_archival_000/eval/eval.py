#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
passed_all = True

def check(name, passed, detail):
    global passed_all
    if not passed:
        passed_all = False
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

# Ground truth: which .log files contain "CRITICAL"
log_base = os.path.join(workspace, "app_logs")
all_log_files = list(Path(log_base).rglob("*.log"))
critical_logs = set()
non_critical_logs = set()

for f in all_log_files:
    try:
        content = f.read_text(errors='replace')
        if "CRITICAL" in content:
            critical_logs.add(f.name)
        else:
            non_critical_logs.add(f.name)
    except Exception as e:
        pass

# Expected: access.log, pg_main.log, auth_service.log, payment.log
expected_archived = {"access.log", "pg_main.log", "auth_service.log", "payment.log"}
expected_not_archived = {"query.log", "debug.log"}

# CHECK 1: archive directory exists and is non-empty
archive_dir = Path(workspace) / "archive"
try:
    archive_exists = archive_dir.exists() and archive_dir.is_dir()
    archive_files = list(archive_dir.glob("*")) if archive_exists else []
    check(
        "archive_directory_exists_and_nonempty",
        archive_exists and len(archive_files) > 0,
        f"Archive dir exists: {archive_exists}, files found: {[f.name for f in archive_files]}"
    )
except Exception as e:
    check("archive_directory_exists_and_nonempty", False, f"Exception: {e}")

# CHECK 2: All CRITICAL-containing .log files are present in archive
try:
    archived_names = {f.name for f in archive_dir.rglob("*.log")} if archive_dir.exists() else set()
    missing = expected_archived - archived_names
    check(
        "all_critical_logs_archived",
        len(missing) == 0,
        f"Expected archived: {sorted(expected_archived)}, missing: {sorted(missing)}, found: {sorted(archived_names)}"
    )
except Exception as e:
    check("all_critical_logs_archived", False, f"Exception: {e}")

# CHECK 3: Non-CRITICAL .log files are NOT in archive
try:
    archived_names = {f.name for f in archive_dir.rglob("*.log")} if archive_dir.exists() else set()
    wrongly_archived = expected_not_archived & archived_names
    check(
        "non_critical_logs_not_archived",
        len(wrongly_archived) == 0,
        f"Non-critical logs that should NOT be archived but were: {sorted(wrongly_archived)}"
    )
except Exception as e:
    check("non_critical_logs_not_archived", False, f"Exception: {e}")

# CHECK 4: Non-.log files (distractor files) are NOT in archive
try:
    non_log_in_archive = [f for f in archive_dir.rglob("*") if f.is_file() and f.suffix != ".log"] if archive_dir.exists() else []
    check(
        "no_non_log_files_in_archive",
        len(non_log_in_archive) == 0,
        f"Non-.log files found in archive (should not be there): {[str(f) for f in non_log_in_archive]}"
    )
except Exception as e:
    check("no_non_log_files_in_archive", False, f"Exception: {e}")

# CHECK 5: archive_manifest.json exists somewhere in workspace
try:
    manifest_files = list(Path(workspace).rglob("archive_manifest.json"))
    check(
        "archive_manifest_json_exists",
        len(manifest_files) > 0,
        f"archive_manifest.json found at: {[str(f) for f in manifest_files]}"
    )
except Exception as e:
    check("archive_manifest_json_exists", False, f"Exception: {e}")

# CHECK 6: archive_manifest.json is valid JSON and is a list/array
try:
    manifest_files = list(Path(workspace).rglob("archive_manifest.json"))
    if not manifest_files:
        check("archive_manifest_is_valid_json_list", False, "archive_manifest.json not found")
    else:
        manifest_path = manifest_files[0]
        raw = manifest_path.read_text()
        data = json.loads(raw)
        is_list = isinstance(data, list)
        check(
            "archive_manifest_is_valid_json_list",
            is_list,
            f"Parsed type: {type(data).__name__}, length: {len(data) if is_list else 'N/A'}, raw[:200]: {raw[:200]}"
        )
except Exception as e:
    check("archive_manifest_is_valid_json_list", False, f"Exception: {e}")

# CHECK 7: archive_manifest.json entries reference the correct 4 archived log files
try:
    manifest_files = list(Path(workspace).rglob("archive_manifest.json"))
    if not manifest_files:
        check("archive_manifest_lists_correct_files", False, "archive_manifest.json not found")
    else:
        data = json.loads(manifest_files[0].read_text())
        if not isinstance(data, list):
            check("archive_manifest_lists_correct_files", False, f"Not a list: {type(data)}")
        else:
            # Extract names from the manifest entries (could be path or name fields)
            manifest_names = set()
            for entry in data:
                if isinstance(entry, dict):
                    # Try 'name' field first (filesystem list --format json uses 'name')
                    n = entry.get("name") or entry.get("path") or ""
                    manifest_names.add(os.path.basename(n))
                elif isinstance(entry, str):
                    manifest_names.add(os.path.basename(entry))
            found_expected = expected_archived & manifest_names
            missing_from_manifest = expected_archived - manifest_names
            check(
                "archive_manifest_lists_correct_files",
                len(missing_from_manifest) == 0 and len(manifest_names) == 4,
                f"Manifest file count: {len(manifest_names)}, found expected: {sorted(found_expected)}, "
                f"missing: {sorted(missing_from_manifest)}, extra: {sorted(manifest_names - expected_archived)}"
            )
except Exception as e:
    check("archive_manifest_lists_correct_files", False, f"Exception: {e}")

# CHECK 8: manifest entries have 'path' and 'size' fields (from filesystem list --format json)
try:
    manifest_files = list(Path(workspace).rglob("archive_manifest.json"))
    if not manifest_files:
        check("archive_manifest_has_required_fields", False, "archive_manifest.json not found")
    else:
        data = json.loads(manifest_files[0].read_text())
        if not isinstance(data, list) or len(data) == 0:
            check("archive_manifest_has_required_fields", False, "Manifest is empty or not a list")
        else:
            sample = data[0]
            has_path = "path" in sample if isinstance(sample, dict) else False
            has_size = "size" in sample if isinstance(sample, dict) else False
            check(
                "archive_manifest_has_required_fields",
                has_path and has_size,
                f"First entry keys: {list(sample.keys()) if isinstance(sample, dict) else type(sample)}, "
                f"has path: {has_path}, has size: {has_size}"
            )
except Exception as e:
    check("archive_manifest_has_required_fields", False, f"Exception: {e}")

score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0

result = {
    "passed": passed_all,
    "score": round(score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))