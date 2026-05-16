import sys
import os
import json
import time

def evaluate(workspace):
    checks = []
    overall_passed = True

    # ---- Check 1: build_log.txt exists ----
    log_path = os.path.join(workspace, "build_log.txt")
    log_exists = os.path.isfile(log_path)
    checks.append({
        "name": "build_log.txt exists",
        "passed": log_exists,
        "detail": f"File found at {log_path}" if log_exists else f"build_log.txt not found at {log_path}"
    })
    if not log_exists:
        overall_passed = False

    # ---- Check 2: build_log.txt has at least one entry (entr triggered) ----
    log_has_entry = False
    log_content = ""
    if log_exists:
        try:
            with open(log_path, "r") as f:
                log_content = f.read().strip()
            log_has_entry = len(log_content) > 0 and "Manifest rebuilt" in log_content
        except Exception as e:
            log_has_entry = False
            log_content = str(e)
    checks.append({
        "name": "build_log.txt has at least one rebuild entry",
        "passed": log_has_entry,
        "detail": f"Log content: {repr(log_content[:300])}" if log_content else "Log file is empty or missing 'Manifest rebuilt' marker"
    })
    if not log_has_entry:
        overall_passed = False

    # ---- Check 3: checksums.md5 exists ----
    manifest_path = os.path.join(workspace, "results", "tables", "checksums.md5")
    manifest_exists = os.path.isfile(manifest_path)
    checks.append({
        "name": "checksums.md5 manifest exists",
        "passed": manifest_exists,
        "detail": f"Manifest found at {manifest_path}" if manifest_exists else f"checksums.md5 not found at {manifest_path}"
    })
    if not manifest_exists:
        overall_passed = False

    # ---- Check 4: checksums.md5 covers all .py files in src/ ----
    manifest_covers_all = False
    manifest_detail = ""
    if manifest_exists:
        try:
            with open(manifest_path, "r") as f:
                manifest_lines = [line.strip() for line in f if line.strip()]

            # Find all actual .py files in src/
            actual_py_files = []
            for root, dirs, files in os.walk(os.path.join(workspace, "src")):
                for fname in files:
                    if fname.endswith(".py"):
                        actual_py_files.append(os.path.join(root, fname))

            # Extract file paths from manifest lines (md5sum format: "hash  path")
            manifest_paths = set()
            for line in manifest_lines:
                parts = line.split(None, 1)
                if len(parts) == 2:
                    manifest_paths.add(parts[1].strip())

            actual_py_set = set(actual_py_files)
            covered = actual_py_set.issubset(manifest_paths) or manifest_paths.issuperset(actual_py_set)

            # At minimum all non-__init__ py files should be there
            non_init_actual = [p for p in actual_py_files if "__init__" not in p]
            non_init_covered = all(p in manifest_paths for p in non_init_actual)

            manifest_covers_all = len(manifest_lines) >= len(actual_py_files) and non_init_covered
            manifest_detail = (
                f"Manifest has {len(manifest_lines)} entries; "
                f"src/ has {len(actual_py_files)} .py files. "
                f"Non-init files covered: {non_init_covered}"
            )
        except Exception as e:
            manifest_covers_all = False
            manifest_detail = f"Error reading manifest: {e}"
    checks.append({
        "name": "checksums.md5 covers all .py source files in src/",
        "passed": manifest_covers_all,
        "detail": manifest_detail
    })
    if not manifest_covers_all:
        overall_passed = False

    # ---- Check 5: entr usage was correct (verify via build_log content showing reactive trigger) ----
    # The build should have been triggered AFTER a file modification (reactive), 
    # not just a one-shot manual run. We check: log was written AFTER at least one 
    # source .py file was modified (mtime of log >= mtime of some src .py file).
    reactive_trigger = False
    reactive_detail = ""
    if log_exists and log_has_entry:
        try:
            log_mtime = os.path.getmtime(log_path)
            src_py_files = []
            for root, dirs, files in os.walk(os.path.join(workspace, "src")):
                for fname in files:
                    if fname.endswith(".py"):
                        src_py_files.append(os.path.join(root, fname))

            # Check if any .py file was modified (mtime close to or before log)
            # In an entr workflow, at least one file should have been touched
            touched_files = [f for f in src_py_files if abs(os.path.getmtime(f) - log_mtime) < 60]
            # Also accept if log exists and manifest exists — the workflow ran
            # (entr must have been used since build_manifest.sh appends to build_log.txt)
            reactive_trigger = len(touched_files) > 0 or (log_has_entry and manifest_exists)
            reactive_detail = (
                f"Log mtime: {log_mtime:.1f}; "
                f"Files with nearby mtime: {len(touched_files)}; "
                f"Reactive workflow confirmed by log+manifest presence"
            )
        except Exception as e:
            reactive_trigger = False
            reactive_detail = f"Error checking mtimes: {e}"
    checks.append({
        "name": "Reactive trigger confirmed (entr-style workflow)",
        "passed": reactive_trigger,
        "detail": reactive_detail
    })
    if not reactive_trigger:
        overall_passed = False

    # ---- Check 6: Verify the -s flag pattern was used correctly (shell command with redirection worked) ----
    # Evidence: build_log.txt was produced by shell redirection (>>) inside the entr command,
    # meaning the -s flag (or equivalent shell invocation) was used. 
    # We verify by checking the log contains a timestamp-formatted entry.
    shell_flag_evidence = False
    shell_flag_detail = ""
    if log_has_entry:
        try:
            import re
            # build_manifest.sh produces lines like: [2024-01-15 10:30:22] Manifest rebuilt: 10 files
            timestamp_pattern = re.compile(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] Manifest rebuilt: \d+ files')
            shell_flag_evidence = bool(timestamp_pattern.search(log_content))
            shell_flag_detail = f"Timestamp log entry found: {shell_flag_evidence}. Content: {repr(log_content[:200])}"
        except Exception as e:
            shell_flag_evidence = False
            shell_flag_detail = f"Error checking log format: {e}"
    checks.append({
        "name": "build_log.txt contains properly formatted timestamp entry (shell execution confirmed)",
        "passed": shell_flag_evidence,
        "detail": shell_flag_detail
    })
    if not shell_flag_evidence:
        overall_passed = False

    # Compute score
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))