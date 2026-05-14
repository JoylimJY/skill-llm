#!/usr/bin/env python3
"""
Evaluation script for the node-transfer file streaming task.

Checks:
1. Received file exists at expected destination path.
2. Received file has correct byte size (matches source).
3. Received file MD5 matches source file MD5 (integrity).
4. transfer_manifest.json exists somewhere in workspace.
5. transfer_manifest.json is valid JSON.
6. manifest.success == true.
7. manifest.bytesReceived == source file size.
8. manifest.totalBytes == source file size.
9. manifest.speedMBps is a positive number.
10. manifest.outputPath resolves to the received file location.
"""

import sys
import json
import hashlib
import os
from pathlib import Path

def compute_md5(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "workspace path not provided"}
        ]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks = []

    # Load ground truth
    gt_path = os.path.join(workspace, ".eval_ground_truth.json")
    try:
        with open(gt_path) as f:
            gt = json.load(f)
        source_size = gt["source_size"]
        source_md5 = gt["source_md5"]
        expected_dest = gt["expected_dest"]
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "ground_truth_load", "passed": False, "detail": f"Cannot load ground truth: {e}"}
        ]}))
        sys.exit(1)

    # ── Check 1: Received file exists ────────────────────────────────────────
    dest_exists = os.path.isfile(expected_dest)
    checks.append({
        "name": "received_file_exists",
        "passed": dest_exists,
        "detail": f"Expected file at {expected_dest}: {'found' if dest_exists else 'NOT FOUND'}"
    })

    # ── Check 2: Received file byte size ─────────────────────────────────────
    if dest_exists:
        dest_size = os.path.getsize(expected_dest)
        size_ok = (dest_size == source_size)
        checks.append({
            "name": "received_file_size_correct",
            "passed": size_ok,
            "detail": f"Expected {source_size} bytes, got {dest_size} bytes"
        })
    else:
        checks.append({
            "name": "received_file_size_correct",
            "passed": False,
            "detail": "Skipped: received file does not exist"
        })
        size_ok = False

    # ── Check 3: Received file MD5 integrity ─────────────────────────────────
    if dest_exists and size_ok:
        try:
            dest_md5 = compute_md5(expected_dest)
            integrity_ok = (dest_md5 == source_md5)
            checks.append({
                "name": "received_file_integrity",
                "passed": integrity_ok,
                "detail": f"Source MD5: {source_md5}, Dest MD5: {dest_md5}"
            })
        except Exception as e:
            checks.append({
                "name": "received_file_integrity",
                "passed": False,
                "detail": f"Error computing MD5: {e}"
            })
            integrity_ok = False
    else:
        checks.append({
            "name": "received_file_integrity",
            "passed": False,
            "detail": "Skipped: received file missing or wrong size"
        })
        integrity_ok = False

    # ── Check 4: transfer_manifest.json exists ───────────────────────────────
    manifest_path = None
    try:
        candidates = list(Path(workspace).rglob("transfer_manifest.json"))
        # Exclude any inside .eval* hidden files
        candidates = [p for p in candidates if ".eval" not in str(p)]
        if candidates:
            manifest_path = str(candidates[0])
            manifest_found = True
        else:
            manifest_found = False
    except Exception as e:
        manifest_found = False

    checks.append({
        "name": "transfer_manifest_exists",
        "passed": manifest_found,
        "detail": f"transfer_manifest.json {'found at ' + manifest_path if manifest_found else 'NOT FOUND in workspace'}"
    })

    # ── Check 5: manifest is valid JSON ──────────────────────────────────────
    manifest = None
    if manifest_found:
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            json_valid = True
        except Exception as e:
            json_valid = False
            checks.append({
                "name": "manifest_valid_json",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
    else:
        json_valid = False

    if manifest_found and json_valid:
        checks.append({
            "name": "manifest_valid_json",
            "passed": True,
            "detail": "transfer_manifest.json is valid JSON"
        })

    # ── Check 6: manifest.success == true ────────────────────────────────────
    if manifest is not None:
        success_val = manifest.get("success")
        success_ok = (success_val is True)
        checks.append({
            "name": "manifest_success_true",
            "passed": success_ok,
            "detail": f"manifest.success = {repr(success_val)}"
        })
    else:
        checks.append({
            "name": "manifest_success_true",
            "passed": False,
            "detail": "Skipped: manifest not loaded"
        })
        success_ok = False

    # ── Check 7: manifest.bytesReceived == source_size ───────────────────────
    if manifest is not None:
        bytes_recv = manifest.get("bytesReceived")
        bytes_ok = (bytes_recv == source_size)
        checks.append({
            "name": "manifest_bytes_received_correct",
            "passed": bytes_ok,
            "detail": f"manifest.bytesReceived={bytes_recv}, expected={source_size}"
        })
    else:
        checks.append({
            "name": "manifest_bytes_received_correct",
            "passed": False,
            "detail": "Skipped: manifest not loaded"
        })
        bytes_ok = False

    # ── Check 8: manifest.totalBytes == source_size ──────────────────────────
    if manifest is not None:
        total_bytes = manifest.get("totalBytes")
        total_ok = (total_bytes == source_size)
        checks.append({
            "name": "manifest_total_bytes_correct",
            "passed": total_ok,
            "detail": f"manifest.totalBytes={total_bytes}, expected={source_size}"
        })
    else:
        checks.append({
            "name": "manifest_total_bytes_correct",
            "passed": False,
            "detail": "Skipped: manifest not loaded"
        })
        total_ok = False

    # ── Check 9: manifest.speedMBps is positive number ───────────────────────
    if manifest is not None:
        speed = manifest.get("speedMBps")
        try:
            speed_ok = isinstance(speed, (int, float)) and float(speed) > 0
        except Exception:
            speed_ok = False
        checks.append({
            "name": "manifest_speed_positive",
            "passed": speed_ok,
            "detail": f"manifest.speedMBps={repr(speed)}, must be a positive number"
        })
    else:
        checks.append({
            "name": "manifest_speed_positive",
            "passed": False,
            "detail": "Skipped: manifest not loaded"
        })
        speed_ok = False

    # ── Check 10: manifest.outputPath points to received file ────────────────
    if manifest is not None:
        out_path = manifest.get("outputPath", "")
        try:
            # Normalize both paths for comparison
            manifest_dest = os.path.realpath(os.path.abspath(str(out_path)))
            expected_dest_real = os.path.realpath(os.path.abspath(expected_dest))
            path_ok = (manifest_dest == expected_dest_real) or os.path.isfile(manifest_dest)
        except Exception as e:
            path_ok = False
        checks.append({
            "name": "manifest_output_path_valid",
            "passed": path_ok,
            "detail": f"manifest.outputPath={repr(out_path)}, expected destination={expected_dest}"
        })
    else:
        checks.append({
            "name": "manifest_output_path_valid",
            "passed": False,
            "detail": "Skipped: manifest not loaded"
        })
        path_ok = False

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    weights = {
        "received_file_exists": 2.0,
        "received_file_size_correct": 1.5,
        "received_file_integrity": 2.0,
        "transfer_manifest_exists": 1.0,
        "manifest_valid_json": 0.5,
        "manifest_success_true": 1.0,
        "manifest_bytes_received_correct": 1.5,
        "manifest_total_bytes_correct": 1.0,
        "manifest_speed_positive": 0.5,
        "manifest_output_path_valid": 0.5,
    }

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)

    # Must pass critical checks to be considered overall passed
    critical_checks = {"received_file_exists", "received_file_integrity",
                       "transfer_manifest_exists", "manifest_bytes_received_correct"}
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()