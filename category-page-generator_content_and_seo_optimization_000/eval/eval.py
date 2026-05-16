import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace = Path(workspace)

    # --- Locate the output file ---
    candidates = list(workspace.rglob("category_page_spec.json"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "category_page_spec.json not found anywhere in workspace"}]
        }

    spec_path = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": str(spec_path.relative_to(workspace))})

    try:
        with open(spec_path) as f:
            spec = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "output_file_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
    checks.append({"name": "output_file_parseable", "passed": True, "detail": "Valid JSON"})

    # ------------------------------------------------------------------ #
    # CHECK 1: Corrected URL — no /category/ prefix, lowercase, no stops  #
    # ------------------------------------------------------------------ #
    try:
        url = spec.get("url", "")
        no_category_prefix = "/category/" not in url
        is_lowercase = url == url.lower()
        # Should not contain uppercase or /category/ prefix
        # Should be like /pet-grooming/dog-grooming/dog-shampoo or similar hierarchy
        has_slug_segments = len([s for s in url.strip("/").split("/") if s]) >= 2
        # No stop words in slugs: "and", "the", "of", "for", "a", "an"
        stop_words_in_url = bool(re.search(r"/(and|the|of|for|an?)/", url))
        # No "shampoos-and-conditioners" allowed (contains stop word "and")
        # Acceptable: "dog-shampoo", "dog-shampoos", "grooming-shampoos" etc.
        url_ok = no_category_prefix and is_lowercase and has_slug_segments and not stop_words_in_url
        checks.append({
            "name": "corrected_url_structure",
            "passed": url_ok,
            "detail": (
                f"URL: '{url}' | no /category/ prefix: {no_category_prefix} | "
                f"lowercase: {is_lowercase} | min 2 segments: {has_slug_segments} | "
                f"no stop words: {not stop_words_in_url}"
            )
        })
    except Exception as e:
        checks.append({"name": "corrected_url_structure", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 2: H1 — exactly one, contains primary keyword                 #
    # ------------------------------------------------------------------ #
    try:
        h1 = spec.get("h1", "")
        h1_nonempty = bool(h1.strip())
        h1_has_keyword = "dog" in h1.lower() and ("shampoo" in h1.lower() or "grooming" in h1.lower())
        h1_ok = h1_nonempty and h1_has_keyword
        checks.append({
            "name": "h1_contains_primary_keyword",
            "passed": h1_ok,
            "detail": f"H1: '{h1}'"
        })
    except Exception as e:
        checks.append({"name": "h1_contains_primary_keyword", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 3: Title tag 50-60 characters                                 #
    # ------------------------------------------------------------------ #
    try:
        title = spec.get("title_tag", "")
        title_len = len(title.strip())
        title_ok = 50 <= title_len <= 60
        checks.append({
            "name": "title_tag_length_50_60_chars",
            "passed": title_ok,
            "detail": f"Title: '{title}' ({title_len} chars). Required: 50-60"
        })
    except Exception as e:
        checks.append({"name": "title_tag_length_50_60_chars", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 4: Meta description 150-160 characters                        #
    # ------------------------------------------------------------------ #
    try:
        meta = spec.get("meta_description", "")
        meta_len = len(meta.strip())
        meta_ok = 150 <= meta_len <= 160
        checks.append({
            "name": "meta_description_length_150_160_chars",
            "passed": meta_ok,
            "detail": f"Meta desc ({meta_len} chars): '{meta[:80]}...' Required: 150-160"
        })
    except Exception as e:
        checks.append({"name": "meta_description_length_150_160_chars", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 5: Intro copy word count 150-300                              #
    # ------------------------------------------------------------------ #
    try:
        intro = spec.get("intro_copy", "")
        word_count = len(intro.split())
        intro_ok = 150 <= word_count <= 300
        checks.append({
            "name": "intro_copy_word_count_150_300",
            "passed": intro_ok,
            "detail": f"Intro copy word count: {word_count}. Required: 150-300"
        })
    except Exception as e:
        checks.append({"name": "intro_copy_word_count_150_300", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 6: FAQ block — at least 3 Q&A pairs                          #
    # ------------------------------------------------------------------ #
    try:
        faq = spec.get("faq", [])
        faq_ok = isinstance(faq, list) and len(faq) >= 3
        has_qa_structure = faq_ok and all(
            isinstance(item, dict) and "question" in item and "answer" in item
            for item in faq
        )
        checks.append({
            "name": "faq_block_min_3_qa_pairs",
            "passed": has_qa_structure,
            "detail": f"FAQ entries: {len(faq) if isinstance(faq, list) else 'N/A'}. Needs >=3 with question+answer fields."
        })
    except Exception as e:
        checks.append({"name": "faq_block_min_3_qa_pairs", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 7: Facet strategy — canonical pointing to base category URL   #
    # ------------------------------------------------------------------ #
    try:
        facet = spec.get("facet_strategy", {})
        canonical = facet.get("canonical", "")
        strategy = facet.get("strategy", "")
        # Canonical must point to base (non-parameterized) category URL
        canonical_is_base = bool(canonical) and "?" not in canonical and "&" not in canonical
        strategy_mentions_canonical = "canonical" in strategy.lower() or "canonical" in str(facet).lower()
        facet_ok = canonical_is_base and strategy_mentions_canonical
        checks.append({
            "name": "facet_canonical_points_to_base_url",
            "passed": facet_ok,
            "detail": (
                f"Canonical: '{canonical}' | is base (no params): {canonical_is_base} | "
                f"strategy mentions canonical: {strategy_mentions_canonical}"
            )
        })
    except Exception as e:
        checks.append({"name": "facet_canonical_points_to_base_url", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 8: Schema — ItemList + FAQ JSON-LD present and valid          #
    # ------------------------------------------------------------------ #
    try:
        schema = spec.get("schema", {})
        schema_str = json.dumps(schema)
        has_item_list = "ItemList" in schema_str
        has_faq_schema = "FAQPage" in schema_str
        has_list_elements = "ListItem" in schema_str
        # Check for product entries in ItemList
        item_list_schema = schema.get("ItemList") or schema.get("item_list") or {}
        # Allow nested structures
        schema_ok = has_item_list and has_faq_schema and has_list_elements
        checks.append({
            "name": "schema_itemlist_and_faqpage_present",
            "passed": schema_ok,
            "detail": (
                f"ItemList: {has_item_list} | FAQPage: {has_faq_schema} | ListItem: {has_list_elements}"
            )
        })
    except Exception as e:
        checks.append({"name": "schema_itemlist_and_faqpage_present", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 9: Crawl depth fix — clicks_from_homepage <= 4               #
    # ------------------------------------------------------------------ #
    try:
        clicks = spec.get("clicks_from_homepage", None)
        depth_ok = clicks is not None and int(clicks) <= 4
        checks.append({
            "name": "crawl_depth_max_4_clicks",
            "passed": depth_ok,
            "detail": f"clicks_from_homepage: {clicks}. Original was 5, must be <=4."
        })
    except Exception as e:
        checks.append({"name": "crawl_depth_max_4_clicks", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # CHECK 10: Breadcrumb hierarchy present                              #
    # ------------------------------------------------------------------ #
    try:
        breadcrumb = spec.get("breadcrumb", [])
        breadcrumb_ok = isinstance(breadcrumb, list) and len(breadcrumb) >= 3
        # Should include Home > Pet Grooming (or similar) > Dog Grooming > current
        checks.append({
            "name": "breadcrumb_min_3_levels",
            "passed": breadcrumb_ok,
            "detail": f"Breadcrumb levels: {len(breadcrumb) if isinstance(breadcrumb, list) else 'N/A'}. Needs >=3."
        })
    except Exception as e:
        checks.append({"name": "breadcrumb_min_3_levels", "passed": False, "detail": f"Error: {e}"})

    # ------------------------------------------------------------------ #
    # Scoring                                                              #
    # ------------------------------------------------------------------ #
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 3)

    # Must pass all critical checks to overall pass
    critical = [
        "title_tag_length_50_60_chars",
        "meta_description_length_150_160_chars",
        "intro_copy_word_count_150_300",
        "facet_canonical_points_to_base_url",
        "corrected_url_structure",
        "schema_itemlist_and_faqpage_present",
    ]
    critical_passed = all(
        any(c["name"] == crit and c["passed"] for c in checks)
        for crit in critical
    )

    overall_passed = critical_passed and score >= 0.8

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))