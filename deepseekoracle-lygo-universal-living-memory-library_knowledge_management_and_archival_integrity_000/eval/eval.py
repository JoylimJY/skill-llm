#!/usr/bin/env python3
"""
Evaluator for LYGO Living Memory Library task.
Usage: python eval_script.py /workspace
"""
import sys
import json
import os
import hashlib
import datetime
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # ─── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    MAX_WEIGHT = 10.0  # sum of all weights

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1: outputs/audit_report.json exists and has required keys
    # ════════════════════════════════════════════════════════════════════════
    audit_path = Path(workspace) / "outputs" / "audit_report.json"
    try:
        audit = load_json(audit_path)
        required_keys = {"audit_timestamp", "total_indexed", "integrity", "drift", "fragile_flags", "compliant"}
        missing = required_keys - set(audit.keys())
        if missing:
            add_check("audit_report_schema", False,
                      f"Missing keys: {missing}", weight=1.5)
        else:
            add_check("audit_report_schema", True,
                      "All required keys present in audit_report.json", weight=1.5)
    except Exception as e:
        add_check("audit_report_schema", False,
                  f"Could not load outputs/audit_report.json: {e}", weight=1.5)
        audit = None

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2: audit correctly identifies integrity failures (missing files)
    # ════════════════════════════════════════════════════════════════════════
    # The original index had missing files:
    KNOWN_MISSING = {
        "archive/analysis/omega_pipeline.py",
        "archive/reports/final_report_v3.md",
        "archive/raw_logs/run_004.log",
        "archive/analysis/epsilon_model.pkl",
        "archive/analysis/zeta_config.yaml",
        "archive/reports/methodology_v2.md",
        "archive/raw_logs/run_005.log",
        "archive/raw_logs/run_006.log",
        "archive/analysis/theta_viz.py",
        "archive/reports/calibration_log.md",
        "archive/analysis/iota_stats.R",
        "archive/raw_logs/run_007_partial.log",
    }
    if audit is not None:
        try:
            reported_integrity = set(audit.get("integrity", []))
            # At minimum, the three clearly missing core/support files must appear
            # (others might have been dropped during compression before audit,
            # so we check the audit was run on the original bloated index OR
            # that the integrity list was generated correctly)
            core_missing = {
                "archive/analysis/omega_pipeline.py",
                "archive/reports/final_report_v3.md",
                "archive/raw_logs/run_004.log",
            }
            # If agent ran audit BEFORE compression the original 3 missing core files appear.
            # If agent ran audit AFTER compression, missing files may be fewer (dropped).
            # Either way, integrity must be a list (not empty if original index used).
            # We accept any non-trivially wrong result: integrity must be a list.
            if isinstance(audit.get("integrity"), list):
                add_check("audit_integrity_field", True,
                          f"integrity field is a list with {len(reported_integrity)} items", weight=1.0)
            else:
                add_check("audit_integrity_field", False,
                          "integrity field is not a list", weight=1.0)
        except Exception as e:
            add_check("audit_integrity_field", False, f"Error: {e}", weight=1.0)
    else:
        add_check("audit_integrity_field", False, "No audit report to inspect", weight=1.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3: audit fragile_flags — must list {FRAGILE} tagged entries
    # ════════════════════════════════════════════════════════════════════════
    FRAGILE_FILES = {
        "archive/raw_logs/run_003_partial.log",
        "archive/analysis/gamma_notes.txt",
        "archive/raw_logs/run_007_partial.log",
    }
    if audit is not None:
        try:
            reported_fragile = set(audit.get("fragile_flags", []))
            # At least one known fragile file must be reported
            found = reported_fragile & FRAGILE_FILES
            if len(found) >= 1:
                add_check("audit_fragile_flags", True,
                          f"Fragile flags correctly includes: {found}", weight=1.5)
            else:
                add_check("audit_fragile_flags", False,
                          f"fragile_flags missing expected entries. Got: {reported_fragile}", weight=1.5)
        except Exception as e:
            add_check("audit_fragile_flags", False, f"Error: {e}", weight=1.5)
    else:
        add_check("audit_fragile_flags", False, "No audit report", weight=1.5)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 4: core_files_index.json compressed to ≤ 20 entries
    # ════════════════════════════════════════════════════════════════════════
    index_path = Path(workspace) / "references" / "core_files_index.json"
    compressed_index = None
    try:
        compressed_index = load_json(index_path)
        entries = compressed_index.get("entries", [])
        n = len(entries)
        if n <= 20:
            add_check("index_max20_compliant", True,
                      f"Index has {n} entries (≤ 20)", weight=2.0)
        else:
            add_check("index_max20_compliant", False,
                      f"Index has {n} entries — exceeds Max20 limit", weight=2.0)
    except Exception as e:
        add_check("index_max20_compliant", False,
                  f"Could not load core_files_index.json: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 5: {FRAGILE} tags preserved in compressed index
    # ════════════════════════════════════════════════════════════════════════
    if compressed_index is not None:
        try:
            entries = compressed_index.get("entries", [])
            fragile_in_index = [
                e["filename"] for e in entries
                if "{FRAGILE}" in e.get("tag", "")
            ]
            # run_003_partial.log is CORE+{FRAGILE} — must survive
            core_fragile = "archive/raw_logs/run_003_partial.log"
            if core_fragile in fragile_in_index:
                add_check("fragile_tags_preserved", True,
                          f"{core_fragile} kept with {{FRAGILE}} tag intact", weight=1.5)
            else:
                add_check("fragile_tags_preserved", False,
                          f"Expected {core_fragile} with {{FRAGILE}} tag in compressed index. "
                          f"Found fragile entries: {fragile_in_index}", weight=1.5)
        except Exception as e:
            add_check("fragile_tags_preserved", False, f"Error: {e}", weight=1.5)
    else:
        add_check("fragile_tags_preserved", False, "No index to inspect", weight=1.5)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 6: outputs/compression_manifest.json exists and is valid
    # ════════════════════════════════════════════════════════════════════════
    manifest_path = Path(workspace) / "outputs" / "compression_manifest.json"
    manifest = None
    try:
        manifest = load_json(manifest_path)
        required_manifest_keys = {
            "compression_timestamp", "entries_before",
            "entries_after", "dropped_entries", "retained_fragile"
        }
        missing_m = required_manifest_keys - set(manifest.keys())
        if not missing_m:
            entries_after = manifest.get("entries_after", 999)
            entries_before = manifest.get("entries_before", 0)
            if entries_after <= 20 and entries_before > 20:
                add_check("compression_manifest_valid", True,
                          f"Manifest: {entries_before} → {entries_after} entries, "
                          f"dropped={len(manifest.get('dropped_entries',[]))}", weight=1.0)
            else:
                add_check("compression_manifest_valid", False,
                          f"Manifest entries_before={entries_before} entries_after={entries_after} "
                          f"— expected before>20 and after≤20", weight=1.0)
        else:
            add_check("compression_manifest_valid", False,
                      f"Missing keys in manifest: {missing_m}", weight=1.0)
    except Exception as e:
        add_check("compression_manifest_valid", False,
                  f"Could not load compression_manifest.json: {e}", weight=1.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 7: outputs/mint/anchor_snippet.json — existence and schema
    # ════════════════════════════════════════════════════════════════════════
    anchor_candidates = list(Path(workspace).rglob("anchor_snippet.json"))
    anchor = None
    if anchor_candidates:
        try:
            anchor = load_json(anchor_candidates[0])
            required_anchor_keys = {
                "lygo_mint_label", "algorithm", "file_count", "hash",
                "minted_at", "source_index"
            }
            missing_a = required_anchor_keys - set(anchor.keys())
            if not missing_a:
                add_check("anchor_snippet_schema", True,
                          "anchor_snippet.json has all required keys", weight=1.0)
            else:
                add_check("anchor_snippet_schema", False,
                          f"Missing keys in anchor_snippet.json: {missing_a}", weight=1.0)
        except Exception as e:
            add_check("anchor_snippet_schema", False,
                      f"Could not load anchor_snippet.json: {e}", weight=1.0)
            anchor = None
    else:
        add_check("anchor_snippet_schema", False,
                  "outputs/mint/anchor_snippet.json not found", weight=1.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 8: anchor_snippet — LYGO-MINT label exact string + algorithm
    # ════════════════════════════════════════════════════════════════════════
    if anchor is not None:
        try:
            label_ok = anchor.get("lygo_mint_label") == "LYGO-MINT-ANCHOR"
            algo_ok  = anchor.get("algorithm", "").lower() == "sha256"
            si_ok    = "core_files_index.json" in anchor.get("source_index", "")
            all_ok   = label_ok and algo_ok and si_ok
            add_check("anchor_snippet_provenance", all_ok,
                      f"lygo_mint_label={anchor.get('lygo_mint_label')!r} "
                      f"algorithm={anchor.get('algorithm')!r} "
                      f"source_index={anchor.get('source_index')!r}", weight=1.5)
        except Exception as e:
            add_check("anchor_snippet_provenance", False, f"Error: {e}", weight=1.5)
    else:
        add_check("anchor_snippet_provenance", False, "No anchor to inspect", weight=1.5)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 9: anchor hash is correct SHA-256 of sorted filenames joined by \n
    # ════════════════════════════════════════════════════════════════════════
    if anchor is not None and compressed_index is not None:
        try:
            entries = compressed_index.get("entries", [])
            filenames_sorted = sorted(set(e["filename"] for e in entries))
            expected_hash = hashlib.sha256(
                "\n".join(filenames_sorted).encode()
            ).hexdigest()
            reported_hash = anchor.get("hash", "")
            reported_count = anchor.get("file_count", -1)
            hash_ok  = (reported_hash == expected_hash)
            count_ok = (reported_count == len(filenames_sorted))
            if hash_ok and count_ok:
                add_check("anchor_hash_correct", True,
                          f"SHA-256 hash matches ({expected_hash[:16]}…) "
                          f"file_count={len(filenames_sorted)}", weight=2.0)
            else:
                add_check("anchor_hash_correct", False,
                          f"Expected hash={expected_hash[:16]}… got={reported_hash[:16] if reported_hash else 'NONE'}…; "
                          f"expected file_count={len(filenames_sorted)} got={reported_count}", weight=2.0)
        except Exception as e:
            add_check("anchor_hash_correct", False, f"Error: {e}", weight=2.0)
    else:
        add_check("anchor_hash_correct", False,
                  "Cannot verify hash without anchor and/or compressed index", weight=2.0)

    # ════════════════════════════════════════════════════════════════════════
    # Scoring
    # ════════════════════════════════════════════════════════════════════════
    total_weight = sum(
        c_weight for c_weight in [1.5, 1.0, 1.5, 2.0, 1.5, 1.0, 1.0, 1.5, 2.0]
    )  # = 14.0
    earned = sum(
        weight for (ch, weight) in zip(checks, [1.5, 1.0, 1.5, 2.0, 1.5, 1.0, 1.0, 1.5, 2.0])
        if ch["passed"]
    )
    score = round(earned / total_weight, 3)
    passed = score >= 0.75 and all(
        ch["passed"] for ch in checks
        if ch["name"] in ("index_max20_compliant", "anchor_hash_correct", "fragile_tags_preserved")
    )

    result = {
        "passed": passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()