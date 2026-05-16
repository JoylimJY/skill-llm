import sys
import os
import json
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    workspace = Path(workspace)

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Check 1: leak was invoked (result log exists) ─────────────────────────
    result_log = workspace / "tmp" / "leak_result.log"
    invocation_log = workspace / "tmp" / "leak_invocation.log"

    try:
        result_text = result_log.read_text()
        add("leak_was_invoked", True, "leak_result.log found and readable")
    except Exception as e:
        add("leak_was_invoked", False, f"leak_result.log missing or unreadable: {e}")
        return finalize(checks)

    # ── Check 2: leak completed successfully ──────────────────────────────────
    if "SUCCESS" in result_text:
        add("leak_succeeded", True, "Result log contains SUCCESS")
    else:
        add("leak_succeeded", False, f"Result log does not contain SUCCESS: {result_text!r}")
        return finalize(checks)

    # ── Parse result log fields ───────────────────────────────────────────────
    result_fields = {}
    for line in result_text.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            result_fields[k.strip()] = v.strip()

    # ── Check 3: URL was a /download URL ──────────────────────────────────────
    url_used = result_fields.get("URL", "")
    is_download_url = result_fields.get("IS_DOWNLOAD_URL", "0")
    if is_download_url == "1" or "/download" in url_used:
        add("correct_url_type_download", True, f"URL used: {url_used}")
    else:
        add("correct_url_type_download", False, f"URL was not a /download URL: {url_used!r}")

    # ── Check 4: Download code was provided ───────────────────────────────────
    code_used = result_fields.get("DOWNLOAD_CODE", "")
    if code_used == "beats-lab-vip":
        add("correct_download_code", True, f"Download code matched: {code_used!r}")
    else:
        add("correct_download_code", False, f"Download code incorrect or missing: {code_used!r} (expected 'beats-lab-vip')")

    # ── Check 5: Buyer key file used is NOT a symlink ─────────────────────────
    key_file_used = result_fields.get("BUYER_KEY_FILE", "")
    if not key_file_used:
        add("buyer_key_file_not_symlink", False, "No BUYER_KEY_FILE recorded in result log")
    else:
        key_path = Path(key_file_used)
        if key_path.is_symlink():
            add("buyer_key_file_not_symlink", False, f"Key file used is a symlink: {key_file_used}")
        elif key_path.is_file():
            add("buyer_key_file_not_symlink", True, f"Key file is a regular (non-symlink) file: {key_file_used}")
        else:
            add("buyer_key_file_not_symlink", False, f"Key file path not a regular file: {key_file_used}")

    # ── Check 6: Key path has no whitespace ───────────────────────────────────
    if key_file_used and " " not in key_file_used and "\t" not in key_file_used:
        add("key_path_no_whitespace", True, f"Key path has no whitespace: {key_file_used!r}")
    else:
        add("key_path_no_whitespace", False, f"Key path has whitespace or is empty: {key_file_used!r}")

    # ── Check 7: Output file exists ───────────────────────────────────────────
    dest_used = result_fields.get("DEST", "")
    # Primary: check the exact file the task specifies
    expected_output = workspace / "downloads" / "sample_pack.bin"
    
    # Also accept any file in downloads/ that the agent saved to
    dest_path = Path(dest_used) if dest_used else None

    if expected_output.exists():
        add("output_file_exists_at_expected_path", True, f"Found at {expected_output}")
        final_dest = expected_output
    elif dest_path and dest_path.exists():
        add("output_file_exists_at_expected_path", False,
            f"File saved at {dest_path} instead of {expected_output}. Partial credit: file exists but wrong name/path.")
        final_dest = dest_path
    else:
        # Search broadly
        found = list((workspace / "downloads").rglob("*.bin")) if (workspace / "downloads").exists() else []
        if found:
            add("output_file_exists_at_expected_path", False,
                f"File(s) found in downloads/ but not named sample_pack.bin: {[str(f) for f in found]}")
            final_dest = found[0]
        else:
            add("output_file_exists_at_expected_path", False, "No output file found in downloads/")
            return finalize(checks)

    # ── Check 8: Output file has non-zero content (was actually written) ──────
    try:
        size = final_dest.stat().st_size
        if size > 0:
            add("output_file_nonempty", True, f"Output file size: {size} bytes")
        else:
            add("output_file_nonempty", False, "Output file is empty")
    except Exception as e:
        add("output_file_nonempty", False, f"Could not stat output file: {e}")

    # ── Check 9: buy.sh was used (not direct leak call bypassing wrapper) ─────
    try:
        inv_text = invocation_log.read_text()
        # The wrapper calls: exec leak buy "$@"
        # The invocation log records args passed to leak (via buy.sh exec)
        # We check that "buy" appears as the first recorded arg
        if "buy" in inv_text:
            add("used_buy_subcommand", True, "buy subcommand detected in invocation log")
        else:
            add("used_buy_subcommand", False, f"buy subcommand not detected: {inv_text!r}")
    except Exception as e:
        add("used_buy_subcommand", False, f"Could not read invocation log: {e}")

    # ── Check 10: --buyer-private-key-file flag was used (not raw key mode) ──
    try:
        inv_text = invocation_log.read_text()
        if "--buyer-private-key-file" in inv_text:
            add("used_buyer_private_key_file_flag", True, "--buyer-private-key-file flag detected in invocation log")
        else:
            add("used_buyer_private_key_file_flag", False,
                "--buyer-private-key-file not found in invocation; agent may have used forbidden raw key mode")
    except Exception as e:
        add("used_buyer_private_key_file_flag", False, f"Could not read invocation log: {e}")

    return finalize(checks)


def finalize(checks):
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)
    return {"passed": all_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))