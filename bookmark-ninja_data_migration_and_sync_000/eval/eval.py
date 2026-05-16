#!/usr/bin/env python3
"""
Evaluation script for Bookmark Ninja legal research task.
Checks:
1. legal-sources.json exists and is valid JSON
2. legal-sources.csv exists and is valid CSV
3. Merge was performed: original 12 Q1 entries are all present
4. New Q2 entries (Discovery category) are present (2 new bookmarks)
5. Conflicts were resolved with --keep-new:
   - CourtListener has updated title "CourtListener — Free Legal Research (Updated)"
   - Casetext has updated description containing "CoCounsel"
6. Category hierarchy is preserved as breadcrumb strings (e.g., "Legal > Case Law > Federal")
7. Total entry count is correct (14 = 12 original + 2 new Discovery entries)
"""

import sys
import json
import csv
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── Helper ────────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. Find legal-sources.json ────────────────────────────────────────────
    json_files = list(workspace.rglob("legal-sources.json"))
    if not json_files:
        check("legal-sources.json exists", False, "File not found anywhere in workspace")
        # Cannot continue without the file
        score = 0.0
        passed = False
        return {"passed": passed, "score": score, "checks": checks}

    json_path = json_files[0]
    check("legal-sources.json exists", True, str(json_path.relative_to(workspace)))

    # ── 2. Parse JSON ─────────────────────────────────────────────────────────
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        check("legal-sources.json is valid JSON", True, f"{len(data)} entries loaded")
    except Exception as e:
        check("legal-sources.json is valid JSON", False, str(e))
        score = 0.1
        passed = False
        return {"passed": passed, "score": score, "checks": checks}

    # ── 3. Find legal-sources.csv ─────────────────────────────────────────────
    csv_files = list(workspace.rglob("legal-sources.csv"))
    if not csv_files:
        check("legal-sources.csv exists", False, "File not found anywhere in workspace")
        csv_data = []
    else:
        csv_path = csv_files[0]
        check("legal-sources.csv exists", True, str(csv_path.relative_to(workspace)))
        try:
            with open(csv_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)
            check("legal-sources.csv is valid CSV with headers", True,
                  f"Columns: {list(csv_data[0].keys()) if csv_data else '(empty)'}")
        except Exception as e:
            check("legal-sources.csv is valid CSV with headers", False, str(e))
            csv_data = []

    # ── 4. Total entry count (should be 14) ───────────────────────────────────
    # Q1: 12 unique URLs, Q2 adds 2 new (Relativity + Logikcull), 2 conflict updates
    urls = [b.get("url", "") for b in data]
    total = len(data)
    target_total = 14
    check(
        f"Total entry count is {target_total}",
        total == target_total,
        f"Found {total} entries (expected {target_total})"
    )

    # ── 5. All Q1 URLs present ────────────────────────────────────────────────
    q1_urls = [
        "https://www.courtlistener.com/",
        "https://www.law.cornell.edu/supremecourt/text/home",
        "https://cases.justia.com/",
        "https://casetext.com/",
        "https://www.leagle.com/",
        "https://uscode.house.gov/",
        "https://www.govinfo.gov/app/collection/cfr",
        "https://www.citationmachine.net/",
        "https://guides.lib.uchicago.edu/bluebook",
        "https://pacer.uscourts.gov/",
        "https://pcl.uscourts.gov/",
    ]
    missing = [u for u in q1_urls if u not in urls]
    check(
        "All original Q1 URLs are present after merge",
        len(missing) == 0,
        f"Missing URLs: {missing}" if missing else "All 11 base URLs found"
    )

    # ── 6. New Q2 Discovery entries present ───────────────────────────────────
    q2_new_urls = [
        "https://www.relativity.com/",
        "https://logikcull.com/",
    ]
    missing_new = [u for u in q2_new_urls if u not in urls]
    check(
        "New Q2 Discovery bookmarks are merged in",
        len(missing_new) == 0,
        f"Missing new URLs: {missing_new}" if missing_new else "Relativity + Logikcull found"
    )

    # ── 7. Conflict resolution: CourtListener title updated (--keep-new) ──────
    url_map = {b["url"]: b for b in data}
    cl_entry = url_map.get("https://www.courtlistener.com/", {})
    cl_title = cl_entry.get("title", "")
    cl_title_updated = "Updated" in cl_title or "Updated" in cl_title
    check(
        "CourtListener conflict resolved with keep-new (updated title)",
        "Updated" in cl_title,
        f"Title found: '{cl_title}'"
    )

    # ── 8. Conflict resolution: Casetext description updated (--keep-new) ─────
    ct_entry = url_map.get("https://casetext.com/", {})
    ct_desc = ct_entry.get("description", "")
    check(
        "Casetext conflict resolved with keep-new (updated description with CoCounsel)",
        "CoCounsel" in ct_desc,
        f"Description found: '{ct_desc}'"
    )

    # ── 9. Category hierarchy preserved as breadcrumb ─────────────────────────
    categories = [b.get("category", "") for b in data]

    # Federal case law entries should have "Legal > Case Law > Federal"
    federal_cat = "Legal > Case Law > Federal"
    federal_entries = [b for b in data if b.get("category", "") == federal_cat]
    check(
        f"Category hierarchy '{federal_cat}' preserved",
        len(federal_entries) >= 3,
        f"Found {len(federal_entries)} entries in '{federal_cat}'"
    )

    # Discovery entries should have "Legal > Discovery"
    discovery_cat = "Legal > Discovery"
    discovery_entries = [b for b in data if b.get("category", "") == discovery_cat]
    check(
        f"Category hierarchy '{discovery_cat}' preserved for new Q2 entries",
        len(discovery_entries) >= 2,
        f"Found {len(discovery_entries)} entries in '{discovery_cat}'"
    )

    # ── 10. CSV entry count matches JSON ──────────────────────────────────────
    if csv_data:
        csv_count = len(csv_data)
        check(
            "CSV entry count matches JSON entry count",
            csv_count == total,
            f"CSV has {csv_count} rows, JSON has {total} entries"
        )
        # Check CSV has required columns
        required_cols = {"url", "title", "category", "description", "date_added"}
        actual_cols = set(csv_data[0].keys()) if csv_data else set()
        check(
            "CSV has required columns (url, title, category, description, date_added)",
            required_cols.issubset(actual_cols),
            f"Columns present: {sorted(actual_cols)}"
        )

    # ── Scoring ───────────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 3) if total_checks else 0.0
    passed = score >= 0.85  # 85% threshold

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))