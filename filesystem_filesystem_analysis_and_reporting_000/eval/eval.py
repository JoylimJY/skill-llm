import sys
import os
import json
import re
from pathlib import Path

def main(workspace):
    checks = []
    total_score = 0.0

    base = os.path.join(workspace, "data_landing_zone")

    # ---- Find the audit_report.json anywhere in workspace ----
    report_files = list(Path(workspace).rglob("audit_report.json"))

    if not report_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "audit_report.json exists", "passed": False, "detail": "File audit_report.json not found anywhere in workspace."}]
        }))
        return

    report_path = report_files[0]

    checks.append({"name": "audit_report.json exists", "passed": True, "detail": str(report_path)})
    total_score += 0.05

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.05,
            "checks": checks + [{"name": "audit_report.json is valid JSON", "passed": False, "detail": str(e)}]
        }))
        return

    checks.append({"name": "audit_report.json is valid JSON", "passed": True, "detail": "Parsed successfully"})
    total_score += 0.05

    # ---- Ground truth computation ----
    import subprocess

    # Get all files
    result = subprocess.run(["find", base, "-type", "f"], capture_output=True, text=True)
    all_files = [f for f in result.stdout.strip().split("\n") if f]

    # 1. File counts per extension
    expected_ext_counts = {}
    for f in all_files:
        if "." in os.path.basename(f):
            ext = f.rsplit(".", 1)[-1].lower()
        else:
            ext = "no_ext"
        expected_ext_counts[ext] = expected_ext_counts.get(ext, 0) + 1

    # 2. Total size of .log files in bytes
    expected_log_size = sum(os.path.getsize(f) for f in all_files if f.endswith(".log"))

    # 3. Top 3 largest .csv files (just their basenames and sizes)
    csv_sizes = [(f, os.path.getsize(f)) for f in all_files if f.endswith(".csv")]
    csv_sizes.sort(key=lambda x: x[1], reverse=True)
    top3_csv = csv_sizes[:3]
    top3_csv_basenames = [os.path.basename(p) for p, _ in top3_csv]

    # 4. Count lines matching [ERROR] in .txt files
    expected_error_lines = 0
    for f in all_files:
        if f.endswith(".txt"):
            try:
                with open(f) as fh:
                    for line in fh:
                        if re.search(r'\[ERROR\]', line):
                            expected_error_lines += 1
            except Exception:
                pass

    # ---- CHECK 1: file_type_counts ----
    try:
        reported_counts = report.get("file_type_counts", report.get("extension_counts", report.get("counts_by_extension", {})))
        assert isinstance(reported_counts, dict), "file_type_counts must be a dict"

        # Normalize keys to lowercase
        reported_counts_norm = {k.lstrip(".").lower(): v for k, v in reported_counts.items()}
        expected_norm = {k.lower(): v for k, v in expected_ext_counts.items()}

        # Check each expected extension
        wrong = []
        for ext, expected_count in expected_norm.items():
            reported = reported_counts_norm.get(ext, reported_counts_norm.get("."+ext, None))
            if reported != expected_count:
                wrong.append(f"{ext}: expected {expected_count}, got {reported}")

        if not wrong:
            checks.append({"name": "file_type_counts correct", "passed": True, "detail": f"All extension counts match: {expected_norm}"})
            total_score += 0.20
        else:
            checks.append({"name": "file_type_counts correct", "passed": False, "detail": f"Mismatches: {wrong[:5]}"})
    except Exception as e:
        checks.append({"name": "file_type_counts correct", "passed": False, "detail": str(e)})

    # ---- CHECK 2: total_log_file_size_bytes ----
    try:
        # Accept various key names
        log_size_val = None
        for key in ["total_log_file_size_bytes", "log_files_total_size_bytes", "total_log_size_bytes", "log_total_size", "total_log_size"]:
            if key in report:
                log_size_val = report[key]
                break
        if log_size_val is None:
            # Try nested
            for k, v in report.items():
                if "log" in k.lower() and "size" in k.lower():
                    log_size_val = v
                    break

        assert log_size_val is not None, "Could not find total log size field in report"
        log_size_int = int(log_size_val)

        # Allow 1% tolerance for text file size variance
        tolerance = max(1024, int(expected_log_size * 0.01))
        diff = abs(log_size_int - expected_log_size)
        if diff <= tolerance:
            checks.append({"name": "total_log_file_size_bytes correct", "passed": True,
                           "detail": f"Reported: {log_size_int}, Expected: {expected_log_size}, diff: {diff}"})
            total_score += 0.20
        else:
            checks.append({"name": "total_log_file_size_bytes correct", "passed": False,
                           "detail": f"Reported: {log_size_int}, Expected: {expected_log_size}, diff: {diff}, tolerance: {tolerance}"})
    except Exception as e:
        checks.append({"name": "total_log_file_size_bytes correct", "passed": False, "detail": str(e)})

    # ---- CHECK 3: top_3_largest_csv_files ----
    try:
        top3_val = None
        for key in ["top_3_largest_csv_files", "top3_largest_csv", "largest_csv_files", "top_3_csv_files"]:
            if key in report:
                top3_val = report[key]
                break
        if top3_val is None:
            for k, v in report.items():
                if "csv" in k.lower() and ("top" in k.lower() or "large" in k.lower()):
                    top3_val = v
                    break

        assert top3_val is not None, "Could not find top_3_largest_csv_files field in report"
        assert isinstance(top3_val, list), "top_3_largest_csv_files must be a list"
        assert len(top3_val) >= 3, f"Expected at least 3 entries, got {len(top3_val)}"

        # Extract filenames from the entries (could be dicts or strings)
        reported_basenames = []
        for entry in top3_val[:3]:
            if isinstance(entry, dict):
                path_str = entry.get("file", entry.get("path", entry.get("name", entry.get("filename", ""))))
                reported_basenames.append(os.path.basename(str(path_str)))
            else:
                reported_basenames.append(os.path.basename(str(entry)))

        # Check all 3 correct basenames present (order matters for top-N)
        all_correct = all(rb == eb for rb, eb in zip(reported_basenames, top3_csv_basenames))

        if all_correct:
            checks.append({"name": "top_3_largest_csv_files correct", "passed": True,
                           "detail": f"Correct top 3: {top3_csv_basenames}"})
            total_score += 0.25
        else:
            # Partial: check if at least the correct set is present (unordered)
            set_match = set(reported_basenames) == set(top3_csv_basenames)
            if set_match:
                checks.append({"name": "top_3_largest_csv_files correct", "passed": True,
                               "detail": f"Correct files but order may differ. Expected order: {top3_csv_basenames}, Got: {reported_basenames}"})
                total_score += 0.15
            else:
                checks.append({"name": "top_3_largest_csv_files correct", "passed": False,
                               "detail": f"Expected: {top3_csv_basenames}, Got: {reported_basenames}"})
    except Exception as e:
        checks.append({"name": "top_3_largest_csv_files correct", "passed": False, "detail": str(e)})

    # ---- CHECK 4: error_lines_in_txt_files ----
    try:
        error_count_val = None
        for key in ["error_lines_in_txt_files", "total_error_lines_txt", "txt_error_line_count",
                    "error_line_count_in_txt", "total_error_lines", "error_lines_txt"]:
            if key in report:
                error_count_val = report[key]
                break
        if error_count_val is None:
            for k, v in report.items():
                if "error" in k.lower() and "txt" in k.lower():
                    error_count_val = v
                    break
            if error_count_val is None:
                for k, v in report.items():
                    if "error" in k.lower() and ("line" in k.lower() or "count" in k.lower()):
                        error_count_val = v
                        break

        assert error_count_val is not None, "Could not find error_lines_in_txt_files field in report"
        reported_errors = int(error_count_val)

        if reported_errors == expected_error_lines:
            checks.append({"name": "error_lines_in_txt_files correct", "passed": True,
                           "detail": f"Correct: {expected_error_lines} [ERROR] lines in .txt files"})
            total_score += 0.25
        else:
            checks.append({"name": "error_lines_in_txt_files correct", "passed": False,
                           "detail": f"Reported: {reported_errors}, Expected: {expected_error_lines}"})
    except Exception as e:
        checks.append({"name": "error_lines_in_txt_files correct", "passed": False, "detail": str(e)})

    passed = total_score >= 0.60

    print(json.dumps({
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)