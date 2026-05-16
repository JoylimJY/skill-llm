import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ------------------------------------------------------------------ #
    # 1. Find the audit report JSON
    # ------------------------------------------------------------------ #
    report_files = list(Path(workspace).rglob("contract_audit_report.json"))
    report_path = report_files[0] if report_files else None

    if report_path is None:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "contract_audit_report.json not found anywhere in workspace"})
        checks.append({"name": "report_valid_json", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "vectorization_results_present", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "all_three_files_vectorized", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "chunks_added_positive", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "search_results_present", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "search_top_k_5_results", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "similarity_scores_valid_range", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "collection_stats_present", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "total_documents_matches_chunks", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "metadata_attached_to_vectorization", "passed": False, "detail": "skipped - file missing"})
        checks.append({"name": "persistence_files_exist", "passed": False, "detail": "skipped - file missing"})
        return {"passed": False, "score": 0.0, "checks": checks}

    total_score += add_check("report_file_exists", True, f"Found at {report_path}")

    # ------------------------------------------------------------------ #
    # 2. Parse JSON
    # ------------------------------------------------------------------ #
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        total_score += add_check("report_valid_json", True, "JSON parsed successfully")
    except Exception as e:
        total_score += add_check("report_valid_json", False, f"JSON parse error: {e}")
        for name in ["vectorization_results_present", "all_three_files_vectorized",
                     "chunks_added_positive", "search_results_present",
                     "search_top_k_5_results", "similarity_scores_valid_range",
                     "collection_stats_present", "total_documents_matches_chunks",
                     "metadata_attached_to_vectorization", "persistence_files_exist"]:
            checks.append({"name": name, "passed": False, "detail": "skipped - JSON invalid"})
        return {"passed": False, "score": total_score / 12.0, "checks": checks}

    # ------------------------------------------------------------------ #
    # 3. Check vectorization_results section
    # ------------------------------------------------------------------ #
    vec_results = report.get("vectorization_results") or report.get("vectorization") or report.get("documents_vectorized")
    has_vec = isinstance(vec_results, list) and len(vec_results) > 0
    total_score += add_check("vectorization_results_present", has_vec,
                             f"vectorization_results is {'present with ' + str(len(vec_results)) + ' entries' if has_vec else 'missing or empty'}")

    if has_vec:
        # Check all three contract files appear
        expected_files = ["software_service_agreement.txt", "data_processing_agreement.md", "ip_license_agreement.docx"]
        found_files = []
        chunks_by_file = {}
        metadata_has_contract_type = False

        for item in vec_results:
            if not isinstance(item, dict):
                continue
            # Look for file reference (source, file_path, filename, file)
            source = (item.get("source") or item.get("file_path") or 
                      item.get("filename") or item.get("file") or "")
            # Check chunks_added
            chunks = item.get("chunks_added") or item.get("chunks") or item.get("num_chunks") or 0
            status = item.get("status", "")
            meta = item.get("metadata") or {}
            if isinstance(meta, dict) and meta:
                metadata_has_contract_type = True

            for ef in expected_files:
                if ef in str(source):
                    found_files.append(ef)
                    chunks_by_file[ef] = chunks

        found_all = all(ef in found_files for ef in expected_files)
        total_score += add_check("all_three_files_vectorized", found_all,
                                 f"Found files: {found_files}, expected: {expected_files}")

        all_chunks_positive = all(chunks_by_file.get(ef, 0) > 0 for ef in expected_files if ef in found_files)
        chunk_detail = str(chunks_by_file)
        total_score += add_check("chunks_added_positive", all_chunks_positive,
                                 f"Chunks per file: {chunk_detail}")

        total_score += add_check("metadata_attached_to_vectorization", metadata_has_contract_type,
                                 "At least one vectorization entry has non-empty metadata dict" if metadata_has_contract_type else "No metadata found in vectorization entries")
    else:
        for name in ["all_three_files_vectorized", "chunks_added_positive", "metadata_attached_to_vectorization"]:
            checks.append({"name": name, "passed": False, "detail": "skipped - no vectorization results"})

    # ------------------------------------------------------------------ #
    # 4. Check search_results section
    # ------------------------------------------------------------------ #
    search_key = None
    for k in ["search_results", "query_results", "search", "retrieval_results"]:
        if k in report:
            search_key = k
            break

    search_data = report.get(search_key) if search_key else None
    has_search = search_data is not None

    total_score += add_check("search_results_present", has_search,
                             f"search_results section {'found under key: ' + search_key if has_search else 'not found'}")

    if has_search:
        # Could be a list of results directly or a dict with queries
        result_list = []
        if isinstance(search_data, list):
            result_list = search_data
        elif isinstance(search_data, dict):
            # might be {query: [results]} structure
            for v in search_data.values():
                if isinstance(v, list):
                    result_list.extend(v)

        # Check top_k=5 respected: at most 5 results per query
        top_k_ok = False
        if isinstance(search_data, list):
            top_k_ok = len(search_data) <= 5
        elif isinstance(search_data, dict):
            # Each query should have at most 5 results
            all_within = all(
                isinstance(v, list) and len(v) <= 5
                for v in search_data.values()
                if isinstance(v, list)
            )
            top_k_ok = all_within and len(search_data) > 0
        
        total_score += add_check("search_top_k_5_results", top_k_ok,
                                 f"top_k constraint check: {'passed' if top_k_ok else 'failed - more than 5 results found or empty'}")

        # Check similarity scores in 0-1 range
        sim_scores = []
        for item in result_list:
            if isinstance(item, dict):
                sim = item.get("similarity") or item.get("score") or item.get("similarity_score")
                if sim is not None:
                    try:
                        sim_scores.append(float(sim))
                    except (TypeError, ValueError):
                        pass

        if sim_scores:
            all_valid = all(0.0 <= s <= 1.0 for s in sim_scores)
            total_score += add_check("similarity_scores_valid_range", all_valid,
                                     f"Similarity scores: {sim_scores[:5]}{'...' if len(sim_scores)>5 else ''} - all in [0,1]: {all_valid}")
        else:
            total_score += add_check("similarity_scores_valid_range", False,
                                     "No similarity scores found in search results")
    else:
        for name in ["search_top_k_5_results", "similarity_scores_valid_range"]:
            checks.append({"name": name, "passed": False, "detail": "skipped - no search results"})

    # ------------------------------------------------------------------ #
    # 5. Check collection_stats section
    # ------------------------------------------------------------------ #
    stats_key = None
    for k in ["collection_stats", "stats", "collection_statistics", "database_stats"]:
        if k in report:
            stats_key = k
            break

    stats_data = report.get(stats_key) if stats_key else None
    has_stats = isinstance(stats_data, dict) and "total_documents" in stats_data
    total_score += add_check("collection_stats_present", has_stats,
                             f"collection_stats {'found: ' + str(stats_data) if has_stats else 'not found or missing total_documents'}")

    if has_stats and has_vec and vec_results:
        # total_documents in stats should match sum of chunks_added from vectorization
        total_chunks = sum(
            (item.get("chunks_added") or item.get("chunks") or item.get("num_chunks") or 0)
            for item in vec_results if isinstance(item, dict)
        )
        reported_total = stats_data.get("total_documents", -1)
        # Allow exact match
        match = (reported_total == total_chunks) and total_chunks > 0
        total_score += add_check("total_documents_matches_chunks", match,
                                 f"stats.total_documents={reported_total}, sum of chunks_added={total_chunks}, match={match}")
    else:
        checks.append({"name": "total_documents_matches_chunks", "passed": False,
                       "detail": "skipped - missing stats or vectorization data"})

    # ------------------------------------------------------------------ #
    # 6. Check persistence files exist
    # ------------------------------------------------------------------ #
    pkl_path = Path(workspace) / "chroma_data" / "documents_data.pkl"
    idx_path = Path(workspace) / "chroma_data" / "documents_index.json"
    persist_ok = pkl_path.exists() and idx_path.exists()
    total_score += add_check("persistence_files_exist", persist_ok,
                             f"chroma_data/documents_data.pkl exists: {pkl_path.exists()}, "
                             f"chroma_data/documents_index.json exists: {idx_path.exists()}")

    # ------------------------------------------------------------------ #
    # Final scoring
    # ------------------------------------------------------------------ #
    num_checks = len(checks)
    final_score = total_score / num_checks if num_checks > 0 else 0.0
    passed_all = all(c["passed"] for c in checks)

    return {
        "passed": passed_all,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))