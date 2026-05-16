#!/usr/bin/env python3
"""
Evaluation script for the json-formatter-pro task.

Expected agent behavior:
1. Validate all 6 config files → identify 3 valid, 3 invalid.
2. Format the 3 valid configs using 4-space indent + --sort-keys → save to new files.
3. Produce an invalid_configs.json report listing the 3 bad filenames.

Grading:
- Check A: invalid_configs.json exists and lists exactly the 3 invalid filenames (any order).
- Check B: trading_config_A_normalized.json (or similar) is formatted with 4-space indent and sorted keys.
- Check C: trading_config_B_normalized.json is formatted with 4-space indent and sorted keys.
- Check D: risk_config_A_normalized.json is formatted with 4-space indent and sorted keys.
- Check E: The 3 invalid files were NOT processed into normalized outputs (no corrupt normalized files).
"""

import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, 'r') as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def read_raw_safe(path):
    try:
        with open(path, 'r') as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)

def check_4space_indent(raw_text):
    """Check that the JSON uses 4-space indentation."""
    lines = raw_text.splitlines()
    indented_lines = [l for l in lines if l.startswith(' ')]
    if not indented_lines:
        return False, "No indented lines found"
    for line in indented_lines:
        stripped = line.lstrip(' ')
        n_spaces = len(line) - len(stripped)
        if n_spaces % 4 != 0:
            return False, f"Line with {n_spaces} spaces (not multiple of 4): {repr(line[:40])}"
    # At least some lines must have exactly 4 spaces (first level)
    first_level = [l for l in indented_lines if len(l) - len(l.lstrip(' ')) == 4]
    if not first_level:
        return False, "No lines with exactly 4-space first-level indent found"
    return True, "OK"

def check_keys_sorted(data, path="root"):
    """Recursively check that all dict keys are sorted."""
    if isinstance(data, dict):
        keys = list(data.keys())
        if keys != sorted(keys):
            return False, f"Keys not sorted at {path}: {keys}"
        for k, v in data.items():
            ok, msg = check_keys_sorted(v, f"{path}.{k}")
            if not ok:
                return False, msg
    elif isinstance(data, list):
        for i, item in enumerate(data):
            ok, msg = check_keys_sorted(item, f"{path}[{i}]")
            if not ok:
                return False, msg
    return True, "OK"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        return

    workspace = sys.argv[1]
    ws = Path(workspace)
    checks = []

    INVALID_FILENAMES = {
        "trading_config_BAD1.json",
        "risk_config_BAD1.json",
        "risk_config_BAD2.json"
    }
    VALID_SOURCE_BASENAMES = {
        "trading_config_A.json",
        "trading_config_B.json",
        "risk_config_A.json"
    }

    # ----------------------------------------------------------------
    # CHECK A: invalid_configs.json must exist and list the 3 bad files
    # ----------------------------------------------------------------
    invalid_report_files = list(ws.rglob("invalid_configs.json"))
    if not invalid_report_files:
        checks.append({
            "name": "invalid_configs_report_exists",
            "passed": False,
            "detail": "No file named 'invalid_configs.json' found anywhere in workspace."
        })
        check_a_passed = False
    else:
        report_path = invalid_report_files[0]
        report_data, err = load_json_safe(report_path)
        if err:
            checks.append({
                "name": "invalid_configs_report_parseable",
                "passed": False,
                "detail": f"invalid_configs.json is not valid JSON: {err}"
            })
            check_a_passed = False
        else:
            # Accept either a list of filenames or a dict with a key containing a list
            reported_names = set()
            if isinstance(report_data, list):
                for item in report_data:
                    if isinstance(item, str):
                        reported_names.add(os.path.basename(item))
                    elif isinstance(item, dict):
                        # might have a "file" or "filename" key
                        for k in ("file", "filename", "name", "path"):
                            if k in item:
                                reported_names.add(os.path.basename(item[k]))
                                break
            elif isinstance(report_data, dict):
                for k in ("invalid", "invalid_files", "files", "errors"):
                    if k in report_data and isinstance(report_data[k], list):
                        for item in report_data[k]:
                            if isinstance(item, str):
                                reported_names.add(os.path.basename(item))
                            elif isinstance(item, dict):
                                for kk in ("file", "filename", "name", "path"):
                                    if kk in item:
                                        reported_names.add(os.path.basename(item[kk]))
                                        break
                        break

            missing = INVALID_FILENAMES - reported_names
            extra = reported_names - INVALID_FILENAMES - VALID_SOURCE_BASENAMES
            if not missing and not extra:
                checks.append({
                    "name": "invalid_configs_report_correct",
                    "passed": True,
                    "detail": f"Correctly identifies all 3 invalid configs: {sorted(INVALID_FILENAMES)}"
                })
                check_a_passed = True
            else:
                detail = ""
                if missing:
                    detail += f"Missing from report: {sorted(missing)}. "
                if extra:
                    detail += f"Unexpected entries in report: {sorted(extra)}. "
                checks.append({
                    "name": "invalid_configs_report_correct",
                    "passed": False,
                    "detail": detail.strip()
                })
                check_a_passed = False

    # ----------------------------------------------------------------
    # CHECKs B, C, D: Find normalized outputs for each valid config
    # ----------------------------------------------------------------
    # We look for any JSON file whose parsed content matches the valid source,
    # and verify 4-space indent + sorted keys. Also accept exact name patterns.

    def find_normalized_for(source_basename, expected_data):
        """Search workspace for a JSON file with matching content."""
        candidates = []
        for jf in ws.rglob("*.json"):
            # Skip source files and the invalid report
            if jf.name in INVALID_FILENAMES:
                continue
            if jf.name == "invalid_configs.json":
                continue
            raw, err = read_raw_safe(jf)
            if err or not raw:
                continue
            data, perr = load_json_safe(jf)
            if perr or data is None:
                continue
            if data == expected_data:
                candidates.append((jf, raw))
        return candidates

    # Load expected data from source files
    sources = {
        "trading_config_A.json": ws / "legacy_exports/trading/configs/trading_config_A.json",
        "trading_config_B.json": ws / "legacy_exports/trading/configs/trading_config_B.json",
        "risk_config_A.json": ws / "legacy_exports/risk/configs/risk_config_A.json",
    }

    check_labels = {
        "trading_config_A.json": "Check_B_trading_config_A_normalized",
        "trading_config_B.json": "Check_C_trading_config_B_normalized",
        "risk_config_A.json": "Check_D_risk_config_A_normalized",
    }

    normalized_passed = 0
    for src_name, src_path in sources.items():
        label = check_labels[src_name]
        expected_data, load_err = load_json_safe(src_path)
        if load_err:
            checks.append({
                "name": label,
                "passed": False,
                "detail": f"Could not load source file {src_path}: {load_err}"
            })
            continue

        candidates = find_normalized_for(src_name, expected_data)
        if not candidates:
            checks.append({
                "name": label,
                "passed": False,
                "detail": f"No normalized output found for {src_name} (no JSON file with matching content)."
            })
            continue

        # Check all candidates — pass if at least one satisfies both constraints
        passed_any = False
        best_detail = ""
        for (fpath, raw) in candidates:
            indent_ok, indent_msg = check_4space_indent(raw)
            sort_ok, sort_msg = check_keys_sorted(expected_data)

            # For sort check, we need to parse the OUTPUT file's key order
            # json.load doesn't preserve order by default in older Python, but Python 3.7+ dicts are ordered
            # Re-check sort on the actual output text by parsing with object_pairs_hook
            try:
                import collections
                def ordered_load(s):
                    return json.loads(s, object_pairs_hook=collections.OrderedDict)
                out_ordered = ordered_load(raw)
                keys_sorted_ok, keys_sorted_msg = check_keys_sorted(out_ordered)
            except Exception as e:
                keys_sorted_ok, keys_sorted_msg = False, str(e)

            if indent_ok and keys_sorted_ok:
                passed_any = True
                best_detail = f"Found at {fpath}: 4-space indent ✓, keys sorted ✓"
                break
            else:
                msgs = []
                if not indent_ok:
                    msgs.append(f"indent: {indent_msg}")
                if not keys_sorted_ok:
                    msgs.append(f"sort: {keys_sorted_msg}")
                best_detail = f"Candidate {fpath}: " + "; ".join(msgs)

        checks.append({
            "name": label,
            "passed": passed_any,
            "detail": best_detail
        })
        if passed_any:
            normalized_passed += 1

    # ----------------------------------------------------------------
    # CHECK E: No normalized output was created for invalid configs
    # ----------------------------------------------------------------
    spurious = []
    for bad_name in INVALID_FILENAMES:
        bad_src = None
        # Try to read the bad source to see if any output matches it (it shouldn't parse)
        # Since invalid JSON can't be parsed, any normalized file can't have matching content
        # Just check if any file is named similarly to suggest attempted processing
        stem = Path(bad_name).stem
        for jf in ws.rglob("*.json"):
            if jf.name == bad_name:
                continue
            if stem.lower() in jf.name.lower() and jf.name not in INVALID_FILENAMES:
                # Found a file with similar name — check if it is valid JSON
                data, err = load_json_safe(jf)
                if data is not None:
                    spurious.append(str(jf))

    checks.append({
        "name": "Check_E_no_normalized_output_for_invalid",
        "passed": len(spurious) == 0,
        "detail": f"Spurious normalized outputs for invalid configs: {spurious}" if spurious else "No spurious outputs found ✓"
    })

    # ----------------------------------------------------------------
    # Scoring
    # ----------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = (score == 1.0)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()