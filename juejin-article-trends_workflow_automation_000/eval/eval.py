import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir):
    checks = []
    total_score = 0.0

    # ---- Helper ----
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ---- Find the output file ----
    report_files = list(Path(workspace_dir).rglob("trends_report.json"))

    if not report_files:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "trends_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    total_score += add_check("output_file_exists", True, f"Found at {report_path}", weight=0.5)

    # ---- Load and parse the report ----
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        total_score += add_check("output_file_parseable", False, f"JSON parse error: {e}", weight=1.0)
        result_passed = total_score >= 3.0
        return {"passed": result_passed, "score": total_score, "checks": checks}

    total_score += add_check("output_file_parseable", True, "Valid JSON", weight=0.5)

    # ---- Expected categories ----
    EXPECTED_CATEGORIES = {
        "6809637769959178254": "前端",
        "6809637769959178255": "后端",
        "6809637769959178258": "人工智能",
    }

    # The report must be a list (array) of category objects, or a dict with a list
    # We accept both: {"categories": [...]} or directly [...]
    if isinstance(report, dict):
        category_list = report.get("categories", [])
    elif isinstance(report, list):
        category_list = report
    else:
        total_score += add_check("report_structure_valid", False, "Report must be a JSON array or object with 'categories' key", weight=2.0)
        result_passed = total_score >= 3.0
        return {"passed": result_passed, "score": total_score, "checks": checks}

    total_score += add_check("report_structure_valid", len(category_list) > 0, f"Category list has {len(category_list)} entries", weight=0.5)

    # ---- Check that all 3 required categories are present ----
    # We check by name (case-insensitive partial match) since agent may not use ID as key
    found_frontend = None
    found_backend = None
    found_ai = None

    for cat_entry in category_list:
        if not isinstance(cat_entry, dict):
            continue
        # Try to detect category by name field
        name = ""
        for key in ["name", "category_name", "categoryName", "category"]:
            if key in cat_entry:
                name = str(cat_entry[key])
                break
        # Also check by category_id
        cat_id = ""
        for key in ["id", "category_id", "categoryId"]:
            if key in cat_entry:
                cat_id = str(cat_entry[key])
                break

        if "前端" in name or cat_id == "6809637769959178254":
            found_frontend = cat_entry
        elif "后端" in name or cat_id == "6809637769959178255":
            found_backend = cat_entry
        elif "人工智能" in name or "AI" in name.upper() or cat_id == "6809637769959178258":
            found_ai = cat_entry

    has_frontend = found_frontend is not None
    has_backend = found_backend is not None
    has_ai = found_ai is not None

    total_score += add_check("has_frontend_category", has_frontend, "前端 category found in report" if has_frontend else "前端 category missing", weight=1.0)
    total_score += add_check("has_backend_category", has_backend, "后端 category found in report" if has_backend else "后端 category missing", weight=1.0)
    total_score += add_check("has_ai_category", has_ai, "人工智能 category found in report" if has_ai else "人工智能 category missing", weight=1.0)

    # ---- Check that correct category IDs were used (not from old/wrong sources) ----
    all_ids_in_report = set()
    for cat_entry in category_list:
        if isinstance(cat_entry, dict):
            for key in ["id", "category_id", "categoryId"]:
                if key in cat_entry:
                    all_ids_in_report.add(str(cat_entry[key]))

    wrong_ids = {"OUTDATED_001", "OUTDATED_002", "OUTDATED_003", "WRONG_ID_FRONTEND", "WRONG_ID_BACKEND", "fe_001", "be_002", "ai_003"}
    used_wrong_ids = all_ids_in_report & wrong_ids
    correct_ids_used = not used_wrong_ids
    total_score += add_check("correct_category_ids_used", correct_ids_used,
        "No outdated/wrong IDs used" if correct_ids_used else f"Wrong IDs found: {used_wrong_ids}",
        weight=1.5)

    # ---- Check articles per category ----
    def get_articles_from_cat(cat_entry):
        if cat_entry is None:
            return []
        for key in ["articles", "items", "posts", "data"]:
            if key in cat_entry and isinstance(cat_entry[key], list):
                return cat_entry[key]
        return []

    def check_category_articles(cat_entry, cat_name, expected_count=5):
        if cat_entry is None:
            return False, f"{cat_name}: category not found"
        articles = get_articles_from_cat(cat_entry)
        if len(articles) == 0:
            return False, f"{cat_name}: no articles found"
        if len(articles) != expected_count:
            return False, f"{cat_name}: expected {expected_count} articles, got {len(articles)}"
        return True, f"{cat_name}: has {len(articles)} articles"

    fe_ok, fe_detail = check_category_articles(found_frontend, "前端", 5)
    be_ok, be_detail = check_category_articles(found_backend, "后端", 5)
    ai_ok, ai_detail = check_category_articles(found_ai, "人工智能", 5)

    total_score += add_check("frontend_has_5_articles", fe_ok, fe_detail, weight=1.0)
    total_score += add_check("backend_has_5_articles", be_ok, be_detail, weight=1.0)
    total_score += add_check("ai_has_5_articles", ai_ok, ai_detail, weight=1.0)

    # ---- Check required fields in articles ----
    REQUIRED_FIELDS = ["title", "author", "viewCount", "likeCount", "collectCount"]

    def check_article_fields(cat_entry, cat_name):
        if cat_entry is None:
            return False, f"{cat_name}: category not found"
        articles = get_articles_from_cat(cat_entry)
        if not articles:
            return False, f"{cat_name}: no articles"
        missing_fields_report = []
        for i, art in enumerate(articles):
            if not isinstance(art, dict):
                missing_fields_report.append(f"article[{i}] is not a dict")
                continue
            for field in REQUIRED_FIELDS:
                if field not in art:
                    missing_fields_report.append(f"article[{i}] missing '{field}'")
        if missing_fields_report:
            return False, f"{cat_name} field issues: {'; '.join(missing_fields_report[:3])}"
        return True, f"{cat_name}: all articles have required fields"

    fe_fields_ok, fe_fields_detail = check_article_fields(found_frontend, "前端")
    be_fields_ok, be_fields_detail = check_article_fields(found_backend, "后端")
    ai_fields_ok, ai_fields_detail = check_article_fields(found_ai, "人工智能")

    total_score += add_check("frontend_articles_have_required_fields", fe_fields_ok, fe_fields_detail, weight=1.0)
    total_score += add_check("backend_articles_have_required_fields", be_fields_ok, be_fields_detail, weight=1.0)
    total_score += add_check("ai_articles_have_required_fields", ai_fields_ok, ai_fields_detail, weight=1.0)

    # ---- Check engagement_score field and sorting ----
    # engagement_score = viewCount + likeCount * 5 + collectCount * 3
    def compute_expected_score(art):
        try:
            return art["viewCount"] + art["likeCount"] * 5 + art["collectCount"] * 3
        except (KeyError, TypeError):
            return 0

    def check_engagement_sorting(cat_entry, cat_name):
        if cat_entry is None:
            return False, False, f"{cat_name}: not found"
        articles = get_articles_from_cat(cat_entry)
        if not articles or len(articles) < 2:
            return False, False, f"{cat_name}: too few articles to check sorting"

        # Check if engagement_score field exists
        has_score_field = all("engagement_score" in a for a in articles if isinstance(a, dict))

        # Check if engagement_score values match the formula
        score_values_correct = True
        for art in articles:
            if not isinstance(art, dict):
                continue
            if "engagement_score" in art:
                expected = compute_expected_score(art)
                actual = art.get("engagement_score", None)
                if actual is None or abs(float(actual) - expected) > 1:
                    score_values_correct = False
                    break

        # Check sorting by engagement_score descending
        scores = [compute_expected_score(a) for a in articles if isinstance(a, dict)]
        is_sorted_desc = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

        if has_score_field and score_values_correct:
            score_detail = f"{cat_name}: engagement_score field present and formula correct"
        elif has_score_field:
            score_detail = f"{cat_name}: engagement_score field present but formula may differ"
        else:
            score_detail = f"{cat_name}: engagement_score field missing"

        sort_detail = f"{cat_name}: articles sorted descending by engagement = {is_sorted_desc} (scores: {scores})"
        return has_score_field, is_sorted_desc, f"{score_detail}; {sort_detail}"

    fe_score_ok, fe_sorted, fe_sort_detail = check_engagement_sorting(found_frontend, "前端")
    be_score_ok, be_sorted, be_sort_detail = check_engagement_sorting(found_backend, "后端")
    ai_score_ok, ai_sorted, ai_sort_detail = check_engagement_sorting(found_ai, "人工智能")

    total_score += add_check("frontend_has_engagement_score", fe_score_ok, fe_sort_detail, weight=1.0)
    total_score += add_check("backend_has_engagement_score", be_score_ok, be_sort_detail, weight=1.0)
    total_score += add_check("ai_has_engagement_score", ai_score_ok, ai_sort_detail, weight=1.0)

    total_score += add_check("frontend_sorted_by_engagement", fe_sorted, f"前端 sort check: {fe_sorted}", weight=1.0)
    total_score += add_check("backend_sorted_by_engagement", be_sorted, f"后端 sort check: {be_sorted}", weight=1.0)
    total_score += add_check("ai_sorted_by_engagement", ai_sorted, f"人工智能 sort check: {ai_sorted}", weight=1.0)

    # ---- Check that 'hot' type was used (not 'new') ----
    # We can verify this by checking that the article data matches 'hot' order from the mock
    # The mock returns articles in template order for 'hot', reversed for 'new'
    # We check the first article of 前端: hot first = "深入理解Vue3响应式原理" (index 0) or similar
    # Actually let's check: for 前端 hot top article should be TypeScript one (viewCount 52100) after sorting by engagement
    # Let's verify frontend first article is NOT from reversed order
    # For 前端 'new' type, order would be reversed: last template item (CSS Grid) first
    # For 前端 'hot' type: TypeScript article has viewCount=52100, likeCount=2103, collectCount=1102
    # engagement = 52100 + 2103*5 + 1102*3 = 52100 + 10515 + 3306 = 65921 -> should be highest

    # Check that frontend articles include TypeScript article (only present in hot, not reversed-new top)
    if found_frontend:
        fe_articles = get_articles_from_cat(found_frontend)
        fe_titles = [a.get("title", "") for a in fe_articles if isinstance(a, dict)]
        has_ts_article = any("TypeScript" in t or "类型体操" in t for t in fe_titles)
        has_vue_article = any("Vue" in t or "响应式" in t for t in fe_titles)
        hot_indicators = has_ts_article or has_vue_article
        total_score += add_check("used_hot_type_for_frontend", hot_indicators,
            f"前端 hot-type articles detected (TS/Vue present: {fe_titles[:2]})" if hot_indicators else f"前端 hot-type articles not detected, titles: {fe_titles[:3]}",
            weight=1.0)
    else:
        total_score += add_check("used_hot_type_for_frontend", False, "前端 category not found", weight=1.0)

    # ---- Final verdict ----
    max_possible = 0.5 + 0.5 + 0.5 + 1.0 + 1.0 + 1.0 + 1.5 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0
    # Passing threshold: need at least 70% and must have core checks
    core_checks_passed = (
        has_frontend and has_backend and has_ai and
        fe_ok and be_ok and ai_ok and
        correct_ids_used
    )
    score_pct = total_score / max_possible if max_possible > 0 else 0
    passed = core_checks_passed and score_pct >= 0.65

    return {
        "passed": passed,
        "score": round(total_score, 2),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))