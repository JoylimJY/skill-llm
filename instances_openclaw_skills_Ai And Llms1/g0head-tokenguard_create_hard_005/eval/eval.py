from pathlib import Path
import json
import re
import sys

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def find_file_by_pattern(base_path, pattern, extensions=None):
    """Find files matching pattern in workspace and subdirectories"""
    pattern = re.compile(pattern, re.IGNORECASE)
    candidates = []
    for ext in extensions or ['']:
        for path in base_path.rglob(f'*{ext}'):
            if pattern.search(path.name):
                candidates.append(path)
    return candidates


def safe_read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None


def flatten_dict(data, parent_key='', sep='.'):
    """Flatten nested dict into dot-notation keys"""
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    return dict(items)


def find_value_by_key_pattern(data, pattern, case_sensitive=False):
    """Find values in nested dict by matching key pattern"""
    if not isinstance(data, dict):
        return None
    
    flat = flatten_dict(data)
    pattern_re = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
    
    for key, value in flat.items():
        if pattern_re.search(key):
            return value
    return None


def find_all_values_by_key_pattern(data, pattern, case_sensitive=False):
    """Find all values in nested dict by matching key pattern"""
    if not isinstance(data, dict):
        return []
    
    flat = flatten_dict(data)
    pattern_re = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
    
    results = []
    for key, value in flat.items():
        if pattern_re.search(key):
            results.append(value)
    return results


def normalize_marker(marker):
    """Normalize marker for case-insensitive comparison"""
    if marker is None:
        return ""
    return str(marker).lower().replace("-", "").replace("_", "")


# Expected outputs - search for files with relevant names
report_txt_candidates = find_file_by_pattern(workspace, r'tokenguard.*report', ['.txt'])
report_json_candidates = find_file_by_pattern(workspace, r'tokenguard.*report', ['.json'])
summary_md_candidates = find_file_by_pattern(workspace, r'tokenguard.*summary', ['.md'])
input_json = workspace / "session_input.json"

# Load input marker for reference
input_marker = None
if input_json.exists():
    try:
        inp_data = json.loads(safe_read_text(input_json))
        input_marker = inp_data.get("marker", "")
    except:
        pass

# Check 1: report text exists and contains marker + key fields
try:
    if report_txt_candidates:
        # Prefer exact match, otherwise use first candidate
        report_txt = next((p for p in report_txt_candidates if p.name == "tokenguard_report.txt"), report_txt_candidates[0])
        txt = safe_read_text(report_txt)
        if txt:
            norm = re.sub(r"\s+", " ", txt.lower())
            # Case-insensitive marker check
            marker_ok = input_marker and normalize_marker(input_marker) in normalize_marker(norm)
            limit_ok = any(k in norm for k in ["limit", "current limit"])
            spent_ok = any(k in norm for k in ["spent", "current spent"])
            add_check("text_report", marker_ok and limit_ok and spent_ok, f"file={report_txt.name}, marker={marker_ok}, limit={limit_ok}, spent={spent_ok}")
        else:
            add_check("text_report", False, f"could not read {report_txt.name}")
    else:
        add_check("text_report", False, "tokenguard_report.txt is missing")
except Exception as e:
    add_check("text_report", False, f"error while checking text report: {e}")

# Check 2: JSON report exists and has fuzzy-valid structure
try:
    if report_json_candidates:
        # Prefer exact match, otherwise use first candidate
        report_json = next((p for p in report_json_candidates if p.name == "tokenguard_report.json"), report_json_candidates[0])
        try:
            data = json.loads(safe_read_text(report_json))
            
            # Check for marker - search for any key containing "marker"
            marker_values = find_all_values_by_key_pattern(data, r"marker")
            has_marker = False
            if input_marker and marker_values:
                for mv in marker_values:
                    if normalize_marker(input_marker) in normalize_marker(str(mv)):
                        has_marker = True
                        break
            
            # Check for required fields with fuzzy matching (anywhere in structure)
            limit_val = find_value_by_key_pattern(data, r"limit")
            spent_val = find_value_by_key_pattern(data, r"spent")
            remaining_val = find_value_by_key_pattern(data, r"remaining")
            entry_count_val = find_value_by_key_pattern(data, r"entry|count|num_entries|entries")
            
            has_fields = all(v is not None for v in [limit_val, spent_val, remaining_val, entry_count_val])
            
            # Check for warning field with fuzzy matching
            warning_val = find_value_by_key_pattern(data, r"warning")
            warning_ok = warning_val is not None and isinstance(warning_val, (bool, str, type(None)))
            
            add_check("json_report", has_marker and has_fields and warning_ok, f"file={report_json.name}, marker={has_marker}, fields={has_fields}, warning_type_ok={warning_ok}")
        except Exception as e:
            add_check("json_report", False, f"invalid JSON or parse error: {e}")
    else:
        add_check("json_report", False, "tokenguard_report.json is missing")
except Exception as e:
    add_check("json_report", False, f"error while checking json report: {e}")

# Check 3: markdown summary exists and references sample input marker
try:
    if summary_md_candidates:
        # Prefer exact match, otherwise use first candidate
        summary_md = next((p for p in summary_md_candidates if p.name == "tokenguard_summary.md"), summary_md_candidates[0])
        md = safe_read_text(summary_md)
        if md:
            md_norm = re.sub(r"\s+", " ", md.lower())
            # Case-insensitive marker check
            marker_present = input_marker and normalize_marker(input_marker) in normalize_marker(md_norm)
            ok = "tokenguard" in md_norm and "marker" in md_norm and marker_present
            add_check("markdown_summary", ok, f"file={summary_md.name}, contains_required_terms={ok}")
        else:
            add_check("markdown_summary", False, f"could not read {summary_md.name}")
    else:
        add_check("markdown_summary", False, "tokenguard_summary.md is missing")
except Exception as e:
    add_check("markdown_summary", False, f"error while checking markdown summary: {e}")

# Check 4: input file exists and contains deterministic marker content
try:
    if input_json.exists():
        try:
            inp = json.loads(safe_read_text(input_json))
            marker = str(inp.get("marker", ""))
            marker_ok = "tokenguard_marker_7f3a9c" in marker.lower()
            entries_ok = isinstance(inp.get("entries"), list) and len(inp.get("entries", [])) >= 2
            add_check("input_fixture", marker_ok and entries_ok, f"marker={marker_ok}, entries={entries_ok}")
        except Exception as e:
            add_check("input_fixture", False, f"invalid JSON or parse error: {e}")
    else:
        add_check("input_fixture", False, "session_input.json is missing")
except Exception as e:
    add_check("input_fixture", False, f"error while checking input fixture: {e}")

# Compute score
passed_count = sum(1 for c in checks if c["passed"])
total_count = len(checks)
score = (passed_count / total_count) if total_count else 0.0
passed = passed_count == total_count

result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))