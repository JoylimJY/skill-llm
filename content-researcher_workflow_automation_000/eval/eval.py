import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── 1. Find the output file ──────────────────────────────────────────────
    target_filename = "edtech_competitive_research.json"
    found_files = list(workspace.rglob(target_filename))
    
    file_exists = len(found_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found {target_filename} at: {found_files[0]}" if file_exists else f"File '{target_filename}' not found anywhere in workspace."
    })
    
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    output_path = found_files[0]
    
    # ── 2. Parse JSON ────────────────────────────────────────────────────────
    try:
        raw = output_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        json_valid = True
        checks.append({
            "name": "output_is_valid_json",
            "passed": True,
            "detail": "File parsed as valid JSON."
        })
    except Exception as e:
        checks.append({
            "name": "output_is_valid_json",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # ── 3. Check required top-level keys ─────────────────────────────────────
    required_keys = {"generated_at", "keywords", "total_results", "results"}
    present_keys = set(data.keys())
    has_structure = required_keys.issubset(present_keys)
    checks.append({
        "name": "json_has_required_top_level_keys",
        "passed": has_structure,
        "detail": f"Present keys: {present_keys}. Required: {required_keys}. Missing: {required_keys - present_keys}"
    })
    
    # ── 4. Verify exactly 3 keywords: online learning platforms, e-learning trends, EdTech startups ──
    expected_keywords = {"online learning platforms", "e-learning trends", "EdTech startups"}
    try:
        actual_keywords = set(kw.strip() for kw in data.get("keywords", []))
        keywords_correct = actual_keywords == expected_keywords
        checks.append({
            "name": "correct_keywords_used",
            "passed": keywords_correct,
            "detail": f"Expected keywords: {expected_keywords}. Got: {actual_keywords}"
        })
    except Exception as e:
        checks.append({
            "name": "correct_keywords_used",
            "passed": False,
            "detail": f"Error checking keywords: {e}"
        })
        keywords_correct = False
    
    # ── 5. Verify max-results constraint: ≤12 results ────────────────────────
    try:
        results = data.get("results", [])
        total_reported = data.get("total_results", -1)
        actual_count = len(results)
        # max-results must be 12, so actual results should be <= 12
        results_within_limit = actual_count <= 12
        total_matches = total_reported == actual_count
        checks.append({
            "name": "max_results_at_most_12",
            "passed": results_within_limit,
            "detail": f"Actual result count: {actual_count}. Must be ≤ 12 (--max-results 12)."
        })
        checks.append({
            "name": "total_results_field_matches_actual",
            "passed": total_matches,
            "detail": f"total_results field: {total_reported}, actual list length: {actual_count}."
        })
    except Exception as e:
        checks.append({
            "name": "max_results_at_most_12",
            "passed": False,
            "detail": f"Error checking results count: {e}"
        })
        results_within_limit = False
        total_matches = False
    
    # ── 6. Verify per-keyword = 5 (results come from 3 keywords × 5 each = 15 raw, capped at 12) ──
    # With 3 keywords at 5 each = 15 raw, deduped and capped at 12.
    # We verify that results appear to come from all 3 expected keywords
    try:
        keyword_sources = set()
        for r in results:
            kw = r.get("keyword", "").strip()
            if kw:
                keyword_sources.add(kw)
        all_three_keywords_present = expected_keywords.issubset(keyword_sources) or len(keyword_sources) >= 3
        checks.append({
            "name": "results_from_all_3_keywords",
            "passed": all_three_keywords_present,
            "detail": f"Keywords found in results: {keyword_sources}"
        })
    except Exception as e:
        checks.append({
            "name": "results_from_all_3_keywords",
            "passed": False,
            "detail": f"Error checking keyword sources in results: {e}"
        })
        all_three_keywords_present = False
    
    # ── 7. Verify AI summaries are present (--summarize was required) ─────────
    try:
        results_with_summary = [r for r in results if r.get("ai_summary") and r["ai_summary"] != "(summary unavailable)"]
        summaries_present = len(results_with_summary) > 0
        fraction = len(results_with_summary) / max(len(results), 1)
        checks.append({
            "name": "ai_summaries_present",
            "passed": summaries_present and fraction >= 0.5,
            "detail": f"{len(results_with_summary)}/{len(results)} results have ai_summary. Fraction: {fraction:.2f}"
        })
    except Exception as e:
        checks.append({
            "name": "ai_summaries_present",
            "passed": False,
            "detail": f"Error checking summaries: {e}"
        })
        summaries_present = False
    
    # ── 8. Verify the correct non-default model was used in summaries ─────────
    # The model must be "anthropic/claude-3-haiku" (non-default)
    # Summaries generated by mock contain "[Summary-XXXXXX via MODEL_NAME]"
    try:
        correct_model = "anthropic/claude-3-haiku"
        default_model = "google/gemini-3-flash-preview"
        model_found = False
        default_model_found = False
        
        for r in results:
            summary = r.get("ai_summary", "")
            if correct_model in summary:
                model_found = True
            if default_model in summary:
                default_model_found = True
        
        correct_model_used = model_found and not default_model_found
        checks.append({
            "name": "correct_non_default_model_used",
            "passed": correct_model_used,
            "detail": (
                f"Expected model '{correct_model}' found in summaries: {model_found}. "
                f"Default model '{default_model}' found (should NOT be): {default_model_found}."
            )
        })
    except Exception as e:
        checks.append({
            "name": "correct_non_default_model_used",
            "passed": False,
            "detail": f"Error checking model in summaries: {e}"
        })
        correct_model_used = False
    
    # ── 9. URL deduplication occurred (all URLs unique) ───────────────────────
    try:
        urls = [r.get("url", "") for r in results]
        unique_urls = set(urls)
        no_duplicate_urls = len(urls) == len(unique_urls)
        checks.append({
            "name": "url_deduplication_applied",
            "passed": no_duplicate_urls,
            "detail": f"Total URLs: {len(urls)}, Unique URLs: {len(unique_urls)}"
        })
    except Exception as e:
        checks.append({
            "name": "url_deduplication_applied",
            "passed": False,
            "detail": f"Error checking URL deduplication: {e}"
        })
        no_duplicate_urls = False
    
    # ── 10. Compute score ────────────────────────────────────────────────────
    # Weight each check
    weighted = [
        ("output_file_exists", 1.0),
        ("output_is_valid_json", 1.0),
        ("json_has_required_top_level_keys", 1.0),
        ("correct_keywords_used", 2.0),
        ("max_results_at_most_12", 2.0),
        ("total_results_field_matches_actual", 0.5),
        ("results_from_all_3_keywords", 1.5),
        ("ai_summaries_present", 1.5),
        ("correct_non_default_model_used", 2.5),
        ("url_deduplication_applied", 1.0),
    ]
    
    check_results = {c["name"]: c["passed"] for c in checks}
    total_weight = sum(w for _, w in weighted)
    earned_weight = sum(w for name, w in weighted if check_results.get(name, False))
    score = earned_weight / total_weight
    
    overall_passed = (
        check_results.get("output_file_exists", False) and
        check_results.get("output_is_valid_json", False) and
        check_results.get("correct_keywords_used", False) and
        check_results.get("max_results_at_most_12", False) and
        check_results.get("ai_summaries_present", False) and
        check_results.get("correct_non_default_model_used", False)
    )
    
    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))