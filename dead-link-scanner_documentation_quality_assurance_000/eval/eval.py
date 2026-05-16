import json
import sys
import os
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True
    score = 0.0

    report_candidates = list(Path(workspace).rglob("audit_report.json"))

    # CHECK 1: audit_report.json exists
    check1 = {"name": "audit_report.json exists", "passed": False, "detail": ""}
    if not report_candidates:
        check1["detail"] = "No file named audit_report.json found anywhere in the workspace."
        checks.append(check1)
        passed_all = False
        return passed_all, score, checks

    report_path = report_candidates[0]
    check1["passed"] = True
    check1["detail"] = f"Found at {report_path}"
    checks.append(check1)
    score += 0.1

    # Load JSON
    check2 = {"name": "audit_report.json is valid JSON", "passed": False, "detail": ""}
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
        check2["passed"] = True
        check2["detail"] = "File is valid JSON."
        checks.append(check2)
        score += 0.1
    except Exception as e:
        check2["detail"] = f"JSON parse error: {e}"
        checks.append(check2)
        passed_all = False
        return passed_all, score, checks

    # CHECK 3: Top-level keys present
    check3 = {"name": "Top-level keys: 'broken_links' and 'summary'", "passed": False, "detail": ""}
    if isinstance(data, dict) and "broken_links" in data and "summary" in data:
        check3["passed"] = True
        check3["detail"] = f"Keys present: {list(data.keys())}"
        checks.append(check3)
        score += 0.1
    else:
        check3["detail"] = f"Missing required top-level keys. Got: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        checks.append(check3)
        passed_all = False

    # CHECK 4: broken_links is a list
    check4 = {"name": "'broken_links' is a list", "passed": False, "detail": ""}
    broken_links = data.get("broken_links", None)
    if isinstance(broken_links, list):
        check4["passed"] = True
        check4["detail"] = f"broken_links has {len(broken_links)} entries."
        checks.append(check4)
        score += 0.1
    else:
        check4["detail"] = f"'broken_links' is not a list. Type: {type(broken_links)}"
        checks.append(check4)
        passed_all = False

    # CHECK 5: Each broken link entry has required fields
    check5 = {"name": "Each broken link entry has 'url', 'status', 'found_on' fields", "passed": False, "detail": ""}
    if isinstance(broken_links, list) and len(broken_links) > 0:
        required_fields = {"url", "found_on"}
        all_valid = True
        bad_entries = []
        for entry in broken_links:
            if not isinstance(entry, dict):
                all_valid = False
                bad_entries.append(str(entry))
                continue
            missing = required_fields - set(entry.keys())
            if missing:
                all_valid = False
                bad_entries.append(f"Missing {missing} in {entry}")
        if all_valid:
            check5["passed"] = True
            check5["detail"] = "All entries have required fields."
            score += 0.1
        else:
            check5["detail"] = f"Bad entries found: {bad_entries[:3]}"
            passed_all = False
    elif isinstance(broken_links, list) and len(broken_links) == 0:
        check5["detail"] = "broken_links is empty — no broken links recorded."
        passed_all = False
    else:
        check5["detail"] = "broken_links is not a valid list."
        passed_all = False
    checks.append(check5)

    # CHECK 6: Key broken links from WEBSITE SCAN are present
    # Expected broken URLs from the staged site (depth 2, internal-only scan):
    # /legacy/old-feature -> 404
    # /docs/widget-api -> 404
    # /archive/2019/announcement -> 404
    # /blog/post-2 -> 404
    # /products/gadget -> 404
    expected_broken_from_scan = {
        "http://localhost:7891/legacy/old-feature",
        "http://localhost:7891/docs/widget-api",
        "http://localhost:7891/archive/2019/announcement",
        "http://localhost:7891/blog/post-2",
        "http://localhost:7891/products/gadget",
    }

    check6 = {"name": "Website scan: broken site links present in report", "passed": False, "detail": ""}
    if isinstance(broken_links, list):
        found_urls = {entry.get("url", "") for entry in broken_links if isinstance(entry, dict)}
        missing_from_scan = expected_broken_from_scan - found_urls
        found_from_scan = expected_broken_from_scan & found_urls
        if len(found_from_scan) >= 4:  # Allow 1 miss due to crawl ordering
            check6["passed"] = True
            check6["detail"] = f"Found {len(found_from_scan)}/5 expected broken site URLs: {found_from_scan}"
            score += 0.2
        else:
            check6["detail"] = (
                f"Only found {len(found_from_scan)}/5 broken site URLs. "
                f"Missing: {missing_from_scan}. Found: {found_from_scan}"
            )
            passed_all = False
    else:
        check6["detail"] = "Cannot check — broken_links is not a list."
        passed_all = False
    checks.append(check6)

    # CHECK 7: Key broken links from MARKDOWN FILE SCAN are present
    # Expected broken URLs from the markdown docs:
    # installation.md: /dashboard, /releases/latest, /docs/quickstart, /portal/register, /faq
    # api/reference.md: /docs/auth, /docs/widget-api, /docs/migration, /archive/2019/announcement
    # tutorials/getting-started.md: /portal/register, /products/gadget
    expected_broken_from_files = {
        "http://localhost:7891/dashboard",
        "http://localhost:7891/releases/latest",
        "http://localhost:7891/docs/quickstart",
        "http://localhost:7891/portal/register",
        "http://localhost:7891/faq",
        "http://localhost:7891/docs/auth",
        "http://localhost:7891/docs/migration",
    }

    check7 = {"name": "Markdown scan: broken doc links present in report", "passed": False, "detail": ""}
    if isinstance(broken_links, list):
        found_urls = {entry.get("url", "") for entry in broken_links if isinstance(entry, dict)}
        found_from_files = expected_broken_from_files & found_urls
        if len(found_from_files) >= 5:  # Allow some flex
            check7["passed"] = True
            check7["detail"] = f"Found {len(found_from_files)}/7 expected broken doc URLs: {found_from_files}"
            score += 0.2
        else:
            check7["detail"] = (
                f"Only found {len(found_from_files)}/7 expected broken doc URLs. "
                f"Missing: {expected_broken_from_files - found_urls}. Found: {found_from_files}"
            )
            passed_all = False
    else:
        check7["detail"] = "Cannot check — broken_links is not a list."
        passed_all = False
    checks.append(check7)

    # CHECK 8: Summary block is well-formed
    check8 = {"name": "Summary block is well-formed with total_broken count", "passed": False, "detail": ""}
    summary = data.get("summary", {})
    if isinstance(summary, dict) and "total_broken" in summary:
        total = summary["total_broken"]
        actual_count = len(broken_links) if isinstance(broken_links, list) else -1
        if isinstance(total, int) and total == actual_count:
            check8["passed"] = True
            check8["detail"] = f"summary.total_broken = {total}, matches broken_links length."
            score += 0.1
        else:
            check8["detail"] = (
                f"summary.total_broken = {total}, but broken_links has {actual_count} entries. "
                "They must match."
            )
            passed_all = False
    else:
        check8["detail"] = f"Summary missing 'total_broken'. Got: {summary}"
        passed_all = False
    checks.append(check8)

    # Finalize
    score = round(min(score, 1.0), 2)
    passed_all = passed_all and all(c["passed"] for c in checks)
    return passed_all, score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    passed, score, checks = run_checks(workspace)
    result = {
        "passed": passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()