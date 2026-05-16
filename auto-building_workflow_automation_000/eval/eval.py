import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    project = Path(workspace) / "Auto_Building_new"

    # ─── CHECK 1: config/sources.json exists ───
    sources_path = project / "config" / "sources.json"
    try:
        with open(sources_path, encoding="utf-8") as f:
            sources = json.load(f)
        checks.append({"name": "sources.json is valid JSON", "passed": True, "detail": "File parsed successfully."})
    except Exception as e:
        checks.append({"name": "sources.json is valid JSON", "passed": False, "detail": str(e)})
        return finalize(checks)

    # ─── CHECK 2: primaryCategories contains "智能母体" (mandatory hidden entry) ───
    primary = sources.get("primaryCategories", [])
    has_zhimu = "智能母体" in primary
    checks.append({
        "name": "primaryCategories includes mandatory '智能母体'",
        "passed": has_zhimu,
        "detail": f"Found primaryCategories: {primary}"
    })

    # ─── CHECK 3: primaryCategories contains at least one medical/healthcare category ───
    medical_keywords = ["健康", "医疗", "医学", "药", "临床", "health", "medical", "医"]
    has_medical = any(
        any(kw in cat for kw in medical_keywords)
        for cat in primary
        if cat != "智能母体"
    )
    checks.append({
        "name": "primaryCategories includes a medical/healthcare category",
        "passed": has_medical,
        "detail": f"primaryCategories: {primary}"
    })

    # ─── CHECK 4: secondaryCategories is a dict keyed by primary category names ───
    sec_cats = sources.get("secondaryCategories", {})
    is_dict = isinstance(sec_cats, dict)
    checks.append({
        "name": "secondaryCategories is a dict (not a list)",
        "passed": is_dict,
        "detail": f"Type: {type(sec_cats).__name__}"
    })

    # ─── CHECK 5: secondaryCategories has a medical key with >=3 subcategories ───
    if is_dict:
        medical_key = None
        for k in sec_cats:
            if any(kw in k for kw in medical_keywords):
                medical_key = k
                break
        if medical_key:
            subcats = sec_cats[medical_key]
            has_subcats = isinstance(subcats, list) and len(subcats) >= 3
            checks.append({
                "name": f"secondaryCategories['{medical_key}'] has >=3 subcategories",
                "passed": has_subcats,
                "detail": f"Subcategories: {subcats}"
            })
        else:
            checks.append({
                "name": "secondaryCategories has a medical/healthcare key",
                "passed": False,
                "detail": f"Keys found: {list(sec_cats.keys())}"
            })
    else:
        checks.append({
            "name": "secondaryCategories medical key check",
            "passed": False,
            "detail": "secondaryCategories is not a dict, skipped."
        })

    # ─── CHECK 6: sources array exists with >=2 entries ───
    src_list = sources.get("sources", [])
    has_enough_sources = isinstance(src_list, list) and len(src_list) >= 2
    checks.append({
        "name": "sources array has >=2 entries",
        "passed": has_enough_sources,
        "detail": f"Found {len(src_list)} source(s)."
    })

    # ─── CHECK 7: all sources use valid type values (github|rss|directory|custom) ───
    valid_types = {"github", "rss", "directory", "custom"}
    invalid_type_sources = []
    for src in src_list:
        t = src.get("type", "")
        if t not in valid_types:
            invalid_type_sources.append({"name": src.get("name"), "type": t})
    has_valid_types = len(invalid_type_sources) == 0 and len(src_list) > 0
    checks.append({
        "name": "All sources use valid type (github|rss|directory|custom)",
        "passed": has_valid_types,
        "detail": f"Invalid: {invalid_type_sources}" if invalid_type_sources else "All valid."
    })

    # ─── CHECK 8: No source uses invalid type like 'web' or 'url' ───
    banned_types = {"web", "url", "http", "crawler", "scraper", "webpage"}
    banned_found = [s.get("type") for s in src_list if s.get("type", "").lower() in banned_types]
    checks.append({
        "name": "No source uses banned type (web/url/etc.)",
        "passed": len(banned_found) == 0,
        "detail": f"Banned types found: {banned_found}" if banned_found else "None found."
    })

    # ─── CHECK 9: All sources have 'enabled' field ───
    all_have_enabled = all("enabled" in s for s in src_list)
    checks.append({
        "name": "All sources have 'enabled' field",
        "passed": all_have_enabled and len(src_list) > 0,
        "detail": f"Sources: {[s.get('name') for s in src_list]}"
    })

    # ─── CHECK 10: resources.ts exists ───
    resources_path = project / "src" / "data" / "resources.ts"
    try:
        resources_content = resources_path.read_text(encoding="utf-8")
        checks.append({"name": "src/data/resources.ts exists", "passed": True, "detail": "File read successfully."})
    except Exception as e:
        checks.append({"name": "src/data/resources.ts exists", "passed": False, "detail": str(e)})
        return finalize(checks)

    # ─── CHECK 11: resources.ts has PRIMARY_CATEGORIES export ───
    has_primary_export = "PRIMARY_CATEGORIES" in resources_content and "export" in resources_content
    checks.append({
        "name": "resources.ts exports PRIMARY_CATEGORIES",
        "passed": has_primary_export,
        "detail": "Checked for 'export' and 'PRIMARY_CATEGORIES' in file."
    })

    # ─── CHECK 12: resources.ts PRIMARY_CATEGORIES includes '智能母体' ───
    has_zhimu_ts = "智能母体" in resources_content
    checks.append({
        "name": "resources.ts PRIMARY_CATEGORIES includes '智能母体'",
        "passed": has_zhimu_ts,
        "detail": "Checked for '智能母体' string in resources.ts"
    })

    # ─── CHECK 13: resources.ts has SECONDARY_CATEGORIES export ───
    has_secondary_export = "SECONDARY_CATEGORIES" in resources_content
    checks.append({
        "name": "resources.ts exports SECONDARY_CATEGORIES",
        "passed": has_secondary_export,
        "detail": "Checked for 'SECONDARY_CATEGORIES' in file."
    })

    # ─── CHECK 14: SECONDARY_CATEGORIES uses labelKey format 'type.<value>' ───
    # Must have at least one entry with labelKey: 'type.something'
    labelkey_pattern = re.compile(r"labelKey\s*:\s*['\"]type\.[a-zA-Z0-9_\u4e00-\u9fff]+['\"]")
    has_labelkey_format = bool(labelkey_pattern.search(resources_content))
    checks.append({
        "name": "SECONDARY_CATEGORIES uses proprietary labelKey 'type.<value>' format",
        "passed": has_labelkey_format,
        "detail": "Searched for pattern: labelKey: 'type.xxx' in resources.ts"
    })

    # ─── CHECK 15: resources.ts does NOT use plain 'label' key (old format replaced) ───
    # Check that the old bad format (label: 'xxx') in SECONDARY_CATEGORIES is removed
    # Allow 'label' only if 'labelKey' is also present (the old bad format had just 'label')
    bad_label_pattern = re.compile(r"\{\s*label\s*:\s*['\"][^'\"]+['\"]\s*,\s*value\s*:")
    has_bad_label = bool(bad_label_pattern.search(resources_content))
    checks.append({
        "name": "resources.ts SECONDARY_CATEGORIES does NOT use old plain 'label' format",
        "passed": not has_bad_label,
        "detail": "Checked that { label: '...', value: '...' } pattern is not present."
    })

    return finalize(checks)


def finalize(checks):
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total
    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))