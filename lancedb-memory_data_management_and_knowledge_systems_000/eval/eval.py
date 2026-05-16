#!/usr/bin/env python3
"""
Evaluation script for the LanceDB memory management task.
Usage: python eval_script.py /workspace
"""

import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── 1. Locate memory_report.json ────────────────────────────────────────
    report_path = None
    candidates = list(workspace.rglob("memory_report.json"))
    if candidates:
        report_path = candidates[0]

    if report_path is None:
        add_check("memory_report.json exists", False, "File not found anywhere in workspace")
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    add_check("memory_report.json exists", True, str(report_path.relative_to(workspace)))

    # ── 2. Parse report ──────────────────────────────────────────────────────
    try:
        report = json.loads(report_path.read_text())
    except Exception as e:
        add_check("memory_report.json is valid JSON", False, str(e))
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    add_check("memory_report.json is valid JSON", True, "")

    # ── 3. Report has required top-level keys ────────────────────────────────
    required_keys = {"stats", "deleted_ids"}
    missing_keys = required_keys - set(report.keys())
    add_check(
        "report has required keys (stats, deleted_ids)",
        len(missing_keys) == 0,
        f"Missing: {missing_keys}" if missing_keys else "All present"
    )

    # ── 4. Stats sub-structure ───────────────────────────────────────────────
    stats = report.get("stats", {})
    stats_keys = {"total_memories", "categories", "by_category", "date_range"}
    missing_stats = stats_keys - set(stats.keys())
    add_check(
        "stats has correct sub-keys from get_memory_stats()",
        len(missing_stats) == 0,
        f"Missing: {missing_stats}" if missing_stats else "All present"
    )

    # ── 5. Total memories correct ────────────────────────────────────────────
    # 15 original notes ingested.
    # Corrections don't change count.
    # Pruning: delete importance < 4.
    # After corrections:
    #   N004: importance=3  -> DELETE
    #   N007: importance=2  -> DELETE
    #   N010: importance=1  -> DELETE
    #   N013: importance=1  -> DELETE
    # N002 corrected from 7->6 (stays, >=4)
    # Expected remaining: 15 - 4 = 11
    expected_total = 11
    actual_total = stats.get("total_memories", -1)
    add_check(
        f"total_memories == {expected_total} after pruning",
        actual_total == expected_total,
        f"Got {actual_total}, expected {expected_total}"
    )

    # ── 6. Deleted IDs correct ───────────────────────────────────────────────
    # The 4 deleted entries are N004, N007, N010, N013.
    # Their DB IDs should be 4, 7, 10, 13 (since add_memory assigns sequential IDs
    # starting at 1, in order of insertion).
    expected_deleted_ids = {4, 7, 10, 13}
    try:
        actual_deleted = set(int(x) for x in report.get("deleted_ids", []))
    except Exception as e:
        actual_deleted = set()
        add_check("deleted_ids are parseable integers", False, str(e))
    else:
        add_check("deleted_ids are parseable integers", True, "")

    add_check(
        f"deleted_ids == {sorted(expected_deleted_ids)}",
        actual_deleted == expected_deleted_ids,
        f"Got {sorted(actual_deleted)}, expected {sorted(expected_deleted_ids)}"
    )

    # ── 7. Verify LanceDB was actually used ──────────────────────────────────
    db_path = workspace / "lab_memory" / "lancedb"
    db_exists = db_path.exists() and any(db_path.iterdir()) if db_path.exists() else False
    add_check(
        "LanceDB database created at /workspace/lab_memory/lancedb",
        db_exists,
        f"Path: {db_path}, exists: {db_path.exists()}"
    )

    # ── 8. Verify category correction for N009 ───────────────────────────────
    # N009 should have category='literature_review' after correction
    # We verify via the by_category counts: literature_review should appear
    by_cat = stats.get("by_category", {})
    add_check(
        "category 'literature_review' appears in by_category (N009 correction applied)",
        "literature_review" in by_cat,
        f"by_category keys: {list(by_cat.keys())}"
    )

    # Original category was 'literature' - should no longer appear
    # (N009 was the only 'literature' entry; after correction it becomes 'literature_review')
    add_check(
        "category 'literature' no longer in by_category (replaced by literature_review)",
        "literature" not in by_cat,
        f"by_category keys: {list(by_cat.keys())}"
    )

    # ── 9. Verify correct category counts ────────────────────────────────────
    # After ingestion + corrections + pruning, expected by_category:
    # architecture: N001, N015 = 2
    # training: N002, N005, N008, N012 = 4
    # research_direction: N003, N011 = 2
    # publication: N006, N014 = 2
    # literature_review: N009 = 1  (corrected from 'literature')
    # Deleted: N004(infrastructure), N007(infrastructure), N010(admin), N013(admin)
    expected_by_cat = {
        "architecture": 2,
        "training": 4,
        "research_direction": 2,
        "publication": 2,
        "literature_review": 1,
    }
    cat_correct = all(by_cat.get(k, 0) == v for k, v in expected_by_cat.items())
    add_check(
        "by_category counts correct after all operations",
        cat_correct,
        f"Expected {expected_by_cat}, got {dict(by_cat)}"
    )

    # ── 10. Number of unique categories ─────────────────────────────────────
    expected_cat_count = 5  # architecture, training, research_direction, publication, literature_review
    actual_cat_count = stats.get("categories", -1)
    add_check(
        f"categories count == {expected_cat_count}",
        actual_cat_count == expected_cat_count,
        f"Got {actual_cat_count}"
    )

    # ── 11. Verify metadata correction for N011 ───────────────────────────────
    # We check the actual LanceDB if accessible, else rely on stats
    # Try to load via lancedb directly
    try:
        sys.path.insert(0, str(workspace))
        import lancedb as ldb
        import json as _json

        conn = ldb.connect(str(db_path))
        if "memory" in conn.table_names():
            tbl = conn.open_table("memory")
            df = tbl.to_pandas()

            # N011 should have id=11 and metadata with verified=true
            n011_rows = df[df["id"] == 11]
            if len(n011_rows) > 0:
                meta_raw = n011_rows.iloc[0]["metadata"]
                try:
                    meta = _json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
                    verified_correct = meta.get("verified") is True
                    contact_correct = "priya.nair@lab.org" in str(meta.get("data_team_contact", ""))
                    add_check(
                        "N011 metadata updated correctly (verified=true, contact present)",
                        verified_correct and contact_correct,
                        f"metadata={meta}"
                    )
                except Exception as e:
                    add_check("N011 metadata updated correctly", False, f"Parse error: {e}")
            else:
                add_check("N011 exists in DB with id=11", False, "Row not found")

            # N015 tags should include 'distillation_benchmark'
            n015_rows = df[df["id"] == 15]
            if len(n015_rows) > 0:
                tags = list(n015_rows.iloc[0]["tags"] or [])
                add_check(
                    "N015 tags updated (distillation_benchmark included)",
                    "distillation_benchmark" in tags,
                    f"tags={tags}"
                )
            else:
                add_check("N015 exists in DB with id=15", False, "Row not found")

            # N006 importance should be 10
            n006_rows = df[df["id"] == 6]
            if len(n006_rows) > 0:
                imp = int(n006_rows.iloc[0]["importance"])
                add_check(
                    "N006 importance == 10 after correction",
                    imp == 10,
                    f"Got importance={imp}"
                )
            else:
                add_check("N006 exists in DB", False, "Row not found")

            # N002 importance should be 6
            n002_rows = df[df["id"] == 2]
            if len(n002_rows) > 0:
                imp2 = int(n002_rows.iloc[0]["importance"])
                add_check(
                    "N002 importance == 6 after correction",
                    imp2 == 6,
                    f"Got importance={imp2}"
                )
            else:
                add_check("N002 exists in DB", False, "Row not found")

        else:
            add_check("memory table exists in LanceDB", False, "Table 'memory' not found")

    except Exception as e:
        add_check("LanceDB direct verification", False, f"Error: {e}")

    # ── Score ────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round(passed_count / total_count, 4) if total_count > 0 else 0.0
    overall_passed = score >= 0.80  # must pass at least 80% of checks

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(ws)