import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # ---- Locate the output file ----
    target_file = None
    candidates = list(Path(workspace_dir).rglob("platform_analysis_report.json"))
    if candidates:
        # Prefer one not inside 'archive' or 'tmp'
        for c in candidates:
            if 'archive' not in str(c) and 'tmp' not in str(c):
                target_file = c
                break
        if target_file is None:
            target_file = candidates[0]

    if not target_file:
        checks.append({"name": "file_exists", "passed": False, "detail": "platform_analysis_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_file}"})
    total_score += 0.1

    # ---- Parse JSON ----
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    total_score += 0.05

    # ---- Check top-level structure ----
    required_top_keys = {"categories_summary", "platform_comparison", "recommendations"}
    found_keys = set(report.keys()) if isinstance(report, dict) else set()
    missing_keys = required_top_keys - found_keys
    if missing_keys:
        checks.append({"name": "top_level_structure", "passed": False,
                        "detail": f"Missing top-level keys: {missing_keys}. Found: {found_keys}"})
    else:
        checks.append({"name": "top_level_structure", "passed": True,
                        "detail": f"All required top-level keys present: {required_top_keys}"})
        total_score += 0.1

    # ---- Check categories_summary ----
    EXPECTED_CATEGORIES = {"electronics", "fashion", "books", "collectibles", "home_goods"}
    try:
        cats_summary = report.get("categories_summary", {})
        if not isinstance(cats_summary, dict):
            raise ValueError("categories_summary must be a dict")
        found_cats = set(cats_summary.keys())
        overlap = found_cats & EXPECTED_CATEGORIES
        if len(overlap) >= 4:
            checks.append({"name": "categories_from_tool", "passed": True,
                            "detail": f"categories_summary contains {len(overlap)} valid categories: {sorted(overlap)}"})
            total_score += 0.15
        else:
            checks.append({"name": "categories_from_tool", "passed": False,
                            "detail": f"Expected at least 4 of {EXPECTED_CATEGORIES}, found only {overlap}"})
    except Exception as e:
        checks.append({"name": "categories_from_tool", "passed": False, "detail": f"Error: {e}"})

    # Check that each category entry has top_platforms derived from the tool
    KNOWN_PLATFORMS = {"amazon", "ebay", "aliexpress", "temu", "shopee"}
    try:
        cats_summary = report.get("categories_summary", {})
        all_valid = True
        issues = []
        for cat_key in EXPECTED_CATEGORIES:
            if cat_key in cats_summary:
                entry = cats_summary[cat_key]
                if not isinstance(entry, dict):
                    all_valid = False
                    issues.append(f"{cat_key}: entry is not a dict")
                    continue
                top_platforms = entry.get("top_platforms", [])
                if not isinstance(top_platforms, list) or len(top_platforms) == 0:
                    all_valid = False
                    issues.append(f"{cat_key}: missing or empty top_platforms list")
                else:
                    for p in top_platforms:
                        if p.lower() not in KNOWN_PLATFORMS:
                            all_valid = False
                            issues.append(f"{cat_key}: unknown platform '{p}'")
        if all_valid:
            checks.append({"name": "category_entries_valid", "passed": True,
                            "detail": "All category entries have valid top_platforms from tool output"})
            total_score += 0.1
        else:
            checks.append({"name": "category_entries_valid", "passed": False,
                            "detail": f"Issues: {issues}"})
    except Exception as e:
        checks.append({"name": "category_entries_valid", "passed": False, "detail": f"Error: {e}"})

    # ---- Check platform_comparison ----
    # Must contain a comparison between two specific platforms (e.g., amazon vs aliexpress or amazon vs temu)
    # The comparison must include rating data that only comes from the compare command
    try:
        comp = report.get("platform_comparison", {})
        if not isinstance(comp, dict):
            raise ValueError("platform_comparison must be a dict")

        # Must have at least one comparison entry
        if len(comp) == 0:
            checks.append({"name": "platform_comparison_present", "passed": False,
                            "detail": "platform_comparison is empty"})
        else:
            checks.append({"name": "platform_comparison_present", "passed": True,
                            "detail": f"platform_comparison has {len(comp)} entry/entries"})
            total_score += 0.1

        # Each comparison must include ratings (only obtainable from running compare command)
        found_ratings = False
        for comp_key, comp_val in comp.items():
            if isinstance(comp_val, dict):
                # Look for rating data
                for k, v in comp_val.items():
                    if "rating" in str(k).lower() or "rating" in str(v).lower():
                        found_ratings = True
                    if isinstance(v, dict):
                        for k2, v2 in v.items():
                            if "rating" in str(k2).lower():
                                found_ratings = True

        if found_ratings:
            checks.append({"name": "comparison_has_ratings", "passed": True,
                            "detail": "Comparison entries include rating data from tool"})
            total_score += 0.1
        else:
            checks.append({"name": "comparison_has_ratings", "passed": False,
                            "detail": "No rating data found in platform_comparison — likely not from compare command"})

        # Must reference real platform names from tool
        comp_text = json.dumps(comp).lower()
        real_platform_mentions = sum(1 for p in KNOWN_PLATFORMS if p in comp_text)
        if real_platform_mentions >= 2:
            checks.append({"name": "comparison_uses_real_platforms", "passed": True,
                            "detail": f"Found {real_platform_mentions} known platform names in comparison"})
            total_score += 0.1
        else:
            checks.append({"name": "comparison_uses_real_platforms", "passed": False,
                            "detail": f"Only {real_platform_mentions} known platforms found; need >= 2"})

    except Exception as e:
        checks.append({"name": "platform_comparison_check", "passed": False, "detail": f"Error: {e}"})

    # ---- Check recommendations ----
    # Must have recommendations per category with correct platform names
    try:
        recs = report.get("recommendations", {})
        if not isinstance(recs, dict) and not isinstance(recs, list):
            raise ValueError("recommendations must be a dict or list")

        recs_text = json.dumps(recs).lower()
        rec_platform_mentions = sum(1 for p in KNOWN_PLATFORMS if p in recs_text)

        if rec_platform_mentions >= 3:
            checks.append({"name": "recommendations_use_real_platforms", "passed": True,
                            "detail": f"Found {rec_platform_mentions} known platform references in recommendations"})
            total_score += 0.1
        else:
            checks.append({"name": "recommendations_use_real_platforms", "passed": False,
                            "detail": f"Only {rec_platform_mentions} known platforms in recommendations; expected >= 3"})

        # Recommendations must not be generic (must reference category-specific data)
        cat_refs = sum(1 for c in EXPECTED_CATEGORIES if c in recs_text)
        if cat_refs >= 3:
            checks.append({"name": "recommendations_category_specific", "passed": True,
                            "detail": f"Recommendations reference {cat_refs} specific categories"})
            total_score += 0.1
        else:
            checks.append({"name": "recommendations_category_specific", "passed": False,
                            "detail": f"Only {cat_refs} category references in recommendations; expected >= 3"})

    except Exception as e:
        checks.append({"name": "recommendations_check", "passed": False, "detail": f"Error: {e}"})

    # ---- Authenticity check: values must match actual data ----
    # Spot-check: amazon rating should be 4.7, collectibles top platform should be ebay
    try:
        authenticity_ok = True
        auth_issues = []

        # Check collectibles -> top platform must include ebay
        cats_summary = report.get("categories_summary", {})
        if "collectibles" in cats_summary:
            coll = cats_summary["collectibles"]
            top_plats = [p.lower() for p in coll.get("top_platforms", [])]
            if "ebay" not in top_plats:
                authenticity_ok = False
                auth_issues.append("collectibles.top_platforms should include 'ebay' (from categories command output)")

        # Check that electronics top platforms include amazon and aliexpress
        if "electronics" in cats_summary:
            elec = cats_summary["electronics"]
            top_plats = [p.lower() for p in elec.get("top_platforms", [])]
            if "amazon" not in top_plats and "aliexpress" not in top_plats:
                authenticity_ok = False
                auth_issues.append("electronics.top_platforms should include 'amazon' and/or 'aliexpress'")

        # Check platform_comparison for a rating value that matches real data
        comp = report.get("platform_comparison", {})
        comp_text = json.dumps(comp)
        # Amazon is rated 4.7, eBay 4.2, AliExpress 3.9, Temu 3.7, Shopee 4.3
        known_ratings = ["4.7", "4.2", "3.9", "3.7", "4.3"]
        rating_found = any(r in comp_text for r in known_ratings)
        if not rating_found:
            authenticity_ok = False
            auth_issues.append("No real platform ratings found in comparison (expected one of: 4.7, 4.2, 3.9, 3.7, 4.3)")

        if authenticity_ok:
            checks.append({"name": "data_authenticity", "passed": True,
                            "detail": "Data values match actual tool outputs"})
            total_score += 0.1
        else:
            checks.append({"name": "data_authenticity", "passed": False,
                            "detail": f"Data doesn't match tool output: {auth_issues}"})

    except Exception as e:
        checks.append({"name": "data_authenticity", "passed": False, "detail": f"Error: {e}"})

    # ---- Final verdict ----
    passed_checks = [c for c in checks if c["passed"]]
    final_passed = total_score >= 0.65

    return {
        "passed": final_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))