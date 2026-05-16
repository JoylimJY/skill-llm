import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find memory_audit_report.json ────────────────────────────────────
    report_path = None
    try:
        candidates = list(workspace.rglob("memory_audit_report.json"))
        if candidates:
            report_path = candidates[0]
    except Exception as e:
        pass

    if report_path is None:
        total_score += add_check(
            "output_file_exists",
            False,
            "memory_audit_report.json not found anywhere in workspace"
        )
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks
        }))
        return

    total_score += add_check(
        "output_file_exists",
        True,
        f"Found memory_audit_report.json at {report_path}"
    )

    # ── 2. Load and parse the JSON report ───────────────────────────────────
    report = None
    try:
        with open(report_path) as f:
            report = json.load(f)
        total_score += add_check("report_valid_json", True, "Report is valid JSON")
    except Exception as e:
        total_score += add_check("report_valid_json", False, f"Failed to parse JSON: {e}")
        print(json.dumps({"passed": False, "score": total_score / 10.0, "checks": checks}))
        return

    # ── 3. Check that memories were stored (ingestion evidence) ─────────────
    # The report should contain evidence of stored memory IDs or content references
    report_str = json.dumps(report).lower()

    stored_memories_evidence = any(k in report_str for k in [
        "f001", "f002", "f003", "f004", "f005", "f006", "f007", "f008",
        "stored", "memories", "ingested", "added", "memory_id", "memory_ids"
    ])
    total_score += add_check(
        "ingestion_evidence",
        stored_memories_evidence,
        "Report contains evidence of memory ingestion (fact IDs or storage confirmation)",
        weight=1.5
    )

    # ── 4. Check priority tag usage ─────────────────────────────────────────
    # The soul-memory system uses [C], [I], [N] tags — check that at least these appear
    priority_tags_used = any(tag in json.dumps(report) for tag in ["[C]", "[I]", "[N]"])
    total_score += add_check(
        "priority_tags_applied",
        priority_tags_used,
        "Report contains evidence of [C]/[I]/[N] priority tags as required by soul-memory Module A",
        weight=1.5
    )

    # ── 5. Check classification categories are present ──────────────────────
    # Expected soul-memory categories: User_Identity, Tech_Config, Project, Science, History, General
    expected_categories = ["user_identity", "tech_config", "project", "science", "general"]
    report_lower = json.dumps(report).lower()
    categories_found = [cat for cat in expected_categories if cat.replace("_", "") in report_lower.replace("_", "") or cat in report_lower]
    category_coverage = len(categories_found) >= 3  # at least 3 of 5 expected categories
    total_score += add_check(
        "classification_categories",
        category_coverage,
        f"Report references {len(categories_found)}/5 expected classification categories: {categories_found}",
        weight=1.5
    )

    # ── 6. Check search/retrieval results are present ───────────────────────
    # The task requires verifying retrieval — report should contain search results
    search_evidence = any(k in report_str for k in [
        "search", "query", "results", "retrieved", "retrieval", "top_k", "score", "hits"
    ])
    total_score += add_check(
        "search_results_present",
        search_evidence,
        "Report contains evidence of search/retrieval operations",
        weight=1.0
    )

    # ── 7. Check that CLI JSON format was used (pure JSON output evidence) ──
    # The soul-memory CLI outputs pure JSON with --format json flag
    # Look for evidence of CLI usage or JSON-formatted search results in the report
    cli_json_evidence = any(k in report_str for k in [
        "--format", "format_json", "cli", "json_output", "pure_json",
        "cluster", "slurm", "principal", "investigator", "quantum", "transport"
    ])
    total_score += add_check(
        "cli_search_results_content",
        cli_json_evidence,
        "Report shows content from CLI searches (memory content keywords present in results)",
        weight=1.0
    )

    # ── 8. Check that the 3 required search queries were executed ───────────
    query_keywords = [
        ("cluster", "slurm"),          # "cluster configuration SLURM"
        ("principal", "investigator"),   # "principal investigator preferences"
        ("quantum", "transport"),        # "quantum transport project deadline"
    ]
    queries_found = 0
    for kws in query_keywords:
        if any(kw in report_lower for kw in kws):
            queries_found += 1

    queries_complete = queries_found >= 2
    total_score += add_check(
        "required_queries_executed",
        queries_complete,
        f"Found evidence of {queries_found}/3 required search queries in report",
        weight=1.0
    )

    # ── 9. Check for v3.6.1 focus buckets (User/QST/Config/Recent/Project/General) ──
    v361_buckets = ["user", "qst", "config", "recent", "project", "general"]
    buckets_found = [b for b in v361_buckets if b in report_lower]
    bucket_present = len(buckets_found) >= 3
    total_score += add_check(
        "v361_focus_buckets",
        bucket_present,
        f"Report references v3.6.1 typed memory focus buckets ({len(buckets_found)}/6 found: {buckets_found})",
        weight=1.0
    )

    # ── 10. Check memory count is reasonable (8 facts → some stored) ────────
    # Try to find a count or list of stored memories
    count_evidence = False
    try:
        # Look for a list of stored IDs or a count
        def find_counts(obj, depth=0):
            if depth > 5:
                return 0
            if isinstance(obj, list) and len(obj) >= 4:
                return len(obj)
            if isinstance(obj, dict):
                for v in obj.values():
                    r = find_counts(v, depth + 1)
                    if r >= 4:
                        return r
            return 0

        found_count = find_counts(report)
        count_evidence = found_count >= 4
    except Exception:
        pass

    # Also check for numeric strings indicating 6+ facts stored
    import re
    number_matches = re.findall(r'\b([6-9]|[1-9]\d)\b', json.dumps(report))
    if number_matches:
        count_evidence = True

    total_score += add_check(
        "adequate_memory_count",
        count_evidence,
        "Report indicates at least 6+ memories were stored/processed",
        weight=0.5
    )

    # ── Final scoring ────────────────────────────────────────────────────────
    max_score = 1.0 + 1.5 + 1.5 + 1.5 + 1.0 + 1.0 + 1.0 + 1.0 + 0.5  # = 10.0
    normalized_score = round(total_score / max_score, 3)

    passed = normalized_score >= 0.6 and checks[0]["passed"] and checks[1]["passed"]

    print(json.dumps({
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(ws)