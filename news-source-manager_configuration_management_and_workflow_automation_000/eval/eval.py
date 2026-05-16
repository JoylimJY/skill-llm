#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
from datetime import datetime

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate(workspace: str):
    checks = []
    score = 0.0

    workspace = Path(workspace)
    news_sources_path = workspace / ".openclaw" / "workspace" / "memory" / "news-sources.json"
    export_path = workspace / ".openclaw" / "workspace" / "exports" / "active-news-config.json"

    # ─── CHECK 1: news-sources.json exists at exact correct path ───
    if not news_sources_path.exists():
        # Also search for it anywhere in workspace as partial credit diagnostic
        found_elsewhere = list(workspace.rglob("news-sources.json"))
        detail = f"File not found at required path: {news_sources_path}"
        if found_elsewhere:
            detail += f". Found at wrong location(s): {[str(p) for p in found_elsewhere]}"
        checks.append({"name": "news-sources.json exists at correct path", "passed": False, "detail": detail})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    checks.append({"name": "news-sources.json exists at correct path", "passed": True, "detail": str(news_sources_path)})
    score += 0.05

    # ─── Load news-sources.json ───
    try:
        config = load_json(news_sources_path)
    except Exception as e:
        checks.append({"name": "news-sources.json is valid JSON", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return
    checks.append({"name": "news-sources.json is valid JSON", "passed": True, "detail": "Parsed successfully"})
    score += 0.05

    # ─── CHECK 2: Top-level structure ───
    has_categories = isinstance(config.get("categories"), list)
    has_last_updated = bool(config.get("last_updated"))
    has_user_confirmed = config.get("user_confirmed") is True

    checks.append({
        "name": "Has 'categories' array",
        "passed": has_categories,
        "detail": f"categories type: {type(config.get('categories')).__name__}"
    })
    if has_categories:
        score += 0.05

    checks.append({
        "name": "Has 'last_updated' timestamp",
        "passed": has_last_updated,
        "detail": f"last_updated: {config.get('last_updated')}"
    })
    if has_last_updated:
        score += 0.03

    checks.append({
        "name": "Has 'user_confirmed: true'",
        "passed": has_user_confirmed,
        "detail": f"user_confirmed: {config.get('user_confirmed')}"
    })
    if has_user_confirmed:
        score += 0.03

    if not has_categories:
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return

    categories = config["categories"]
    cat_names = [c.get("name", "") for c in categories]

    # ─── CHECK 3: Finance/Crypto category is present and INACTIVE ───
    finance_cats = [c for c in categories if "Finance" in c.get("name", "") or "Crypto" in c.get("name", "")]
    if finance_cats:
        fc = finance_cats[0]
        fc_inactive = fc.get("active") is False
        checks.append({
            "name": "Finance/Crypto category exists",
            "passed": True,
            "detail": f"Found: {fc.get('name')}, active={fc.get('active')}"
        })
        score += 0.05
        checks.append({
            "name": "Finance/Crypto is inactive (active: false)",
            "passed": fc_inactive,
            "detail": f"active field: {fc.get('active')}"
        })
        if fc_inactive:
            score += 0.05
    else:
        checks.append({"name": "Finance/Crypto category exists", "passed": False, "detail": f"Not found. Categories: {cat_names}"})
        checks.append({"name": "Finance/Crypto is inactive (active: false)", "passed": False, "detail": "Category not present"})

    # ─── CHECK 4: AI/Tech category with correct structure ───
    ai_cats = [c for c in categories if "AI" in c.get("name", "") or "Tech" in c.get("name", "")]
    if ai_cats:
        ac = ai_cats[0]
        # Must have keywords covering multiple sub-domains
        ac_keywords = ac.get("keywords", [])
        ac_sources = ac.get("sources", [])
        ac_active = ac.get("active") is True
        ac_has_search_params = isinstance(ac.get("search_params"), dict)

        checks.append({
            "name": "AI/Tech category exists and is active",
            "passed": ac_active,
            "detail": f"name={ac.get('name')}, active={ac.get('active')}"
        })
        if ac_active:
            score += 0.05

        has_sufficient_keywords = len(ac_keywords) >= 4
        checks.append({
            "name": "AI/Tech has >=4 keywords (coverage sub-domains)",
            "passed": has_sufficient_keywords,
            "detail": f"keywords ({len(ac_keywords)}): {ac_keywords}"
        })
        if has_sufficient_keywords:
            score += 0.05

        # Sources must have priority field
        sources_have_priority = all(isinstance(s.get("priority"), int) for s in ac_sources) if ac_sources else False
        checks.append({
            "name": "AI/Tech sources have priority field",
            "passed": sources_have_priority,
            "detail": f"sources: {ac_sources}"
        })
        if sources_have_priority:
            score += 0.05

        checks.append({
            "name": "AI/Tech has search_params",
            "passed": ac_has_search_params,
            "detail": f"search_params: {ac.get('search_params')}"
        })
        if ac_has_search_params:
            score += 0.03

        # Check The Verge is present (replacing Ars Technica or similar modification)
        source_names = [s.get("name", "").lower() for s in ac_sources]
        has_verge = any("verge" in n for n in source_names)
        checks.append({
            "name": "AI/Tech includes The Verge as a source",
            "passed": has_verge,
            "detail": f"source names: {[s.get('name') for s in ac_sources]}"
        })
        if has_verge:
            score += 0.05

        # Ars Technica should be removed (the low-quality source to replace)
        has_ars = any("ars" in n or "technica" in n for n in source_names)
        checks.append({
            "name": "Ars Technica removed from AI/Tech sources",
            "passed": not has_ars,
            "detail": f"source names: {[s.get('name') for s in ac_sources]}"
        })
        if not has_ars:
            score += 0.05

    else:
        for check_name in ["AI/Tech category exists and is active", "AI/Tech has >=4 keywords (coverage sub-domains)",
                           "AI/Tech sources have priority field", "AI/Tech has search_params",
                           "AI/Tech includes The Verge as a source", "Ars Technica removed from AI/Tech sources"]:
            checks.append({"name": check_name, "passed": False, "detail": f"AI/Tech not found. Categories: {cat_names}"})

    # ─── CHECK 5: Custom "Quantum Computing" category (or similarly named niche category) ───
    # The task asks for a custom category not in templates
    custom_cats = [c for c in categories if not any(
        template_name.lower() in c.get("name", "").lower()
        for template_name in ["AI/Tech", "Business Strategy", "Finance/Crypto", "Health/Bio",
                               "Energy/Climate", "Policy/Regulation", "Product Design",
                               "AI", "Tech", "Business", "Finance", "Crypto", "Health", "Bio",
                               "Energy", "Climate", "Policy", "Regulation", "Product", "Design"]
    )]

    # More targeted: look for Quantum or Space or Quantum Computing
    quantum_cats = [c for c in categories if any(
        kw in c.get("name", "").lower() 
        for kw in ["quantum", "space", "aerospace", "defense", "supply chain", "logistics", "material"]
    )]

    # Actually let's just check if there's any category that doesn't match standard templates
    standard_names_lower = ["ai/tech", "ai", "tech", "business strategy", "business", "finance/crypto",
                            "finance", "crypto", "health/bio", "health", "bio", "energy/climate",
                            "energy", "climate", "policy/regulation", "policy", "regulation",
                            "product design", "product", "design"]

    truly_custom = [c for c in categories if not any(
        c.get("name", "").lower().strip() == sn or
        c.get("name", "").lower().strip().startswith(sn)
        for sn in standard_names_lower
    )]

    has_custom_category = len(truly_custom) > 0
    checks.append({
        "name": "Custom non-template category added",
        "passed": has_custom_category,
        "detail": f"Custom categories found: {[c.get('name') for c in truly_custom]}" if truly_custom else f"No custom category. All: {cat_names}"
    })
    if has_custom_category:
        score += 0.08

    # Custom category must have keywords (at least 3 for sub-domain coverage)
    if truly_custom:
        cc = truly_custom[0]
        cc_keywords = cc.get("keywords", [])
        cc_has_enough_keywords = len(cc_keywords) >= 3
        checks.append({
            "name": "Custom category has >=3 keywords for sub-domain coverage",
            "passed": cc_has_enough_keywords,
            "detail": f"keywords ({len(cc_keywords)}): {cc_keywords}"
        })
        if cc_has_enough_keywords:
            score += 0.07

        cc_sources = cc.get("sources", [])
        cc_has_sources = len(cc_sources) >= 1
        checks.append({
            "name": "Custom category has at least 1 source with priority",
            "passed": cc_has_sources and all(isinstance(s.get("priority"), int) for s in cc_sources),
            "detail": f"sources: {cc_sources}"
        })
        if cc_has_sources and all(isinstance(s.get("priority"), int) for s in cc_sources):
            score += 0.05

        cc_has_search_params = isinstance(cc.get("search_params"), dict)
        checks.append({
            "name": "Custom category has search_params",
            "passed": cc_has_search_params,
            "detail": f"search_params: {cc.get('search_params')}"
        })
        if cc_has_search_params:
            score += 0.04
    else:
        for cn in ["Custom category has >=3 keywords for sub-domain coverage",
                   "Custom category has at least 1 source with priority",
                   "Custom category has search_params"]:
            checks.append({"name": cn, "passed": False, "detail": "No custom category found"})

    # ─── CHECK 6: At least 3 active categories ───
    active_cats = [c for c in categories if c.get("active") is True]
    has_enough_active = len(active_cats) >= 3
    checks.append({
        "name": "At least 3 active categories configured",
        "passed": has_enough_active,
        "detail": f"Active categories ({len(active_cats)}): {[c.get('name') for c in active_cats]}"
    })
    if has_enough_active:
        score += 0.05

    # ─── CHECK 7: Export file with correct structure ───
    if export_path.exists():
        try:
            export_data = load_json(export_path)
            has_active_categories_key = isinstance(export_data.get("active_categories"), list)
            checks.append({
                "name": "Export file has 'active_categories' array",
                "passed": has_active_categories_key,
                "detail": f"Keys: {list(export_data.keys())}"
            })
            if has_active_categories_key:
                score += 0.05

            if has_active_categories_key:
                exp_cats = export_data["active_categories"]

                # All exported categories must be active in main config
                exported_names = {c.get("name") for c in exp_cats}
                inactive_names = {c.get("name") for c in categories if c.get("active") is False}
                no_inactive_exported = not (exported_names & inactive_names)
                checks.append({
                    "name": "Export only contains active categories (no inactive ones)",
                    "passed": no_inactive_exported,
                    "detail": f"Exported: {exported_names}, Inactive in config: {inactive_names}"
                })
                if no_inactive_exported:
                    score += 0.07

                # Each exported category should have: name, keywords, sources (as strings), search_params
                if exp_cats:
                    sample = exp_cats[0]
                    sources_are_strings = (
                        isinstance(sample.get("sources"), list) and
                        len(sample.get("sources", [])) > 0 and
                        isinstance(sample["sources"][0], str)
                    )
                    checks.append({
                        "name": "Export sources are strings (not objects) per export format spec",
                        "passed": sources_are_strings,
                        "detail": f"Sample sources field: {sample.get('sources', [])[:3]}"
                    })
                    if sources_are_strings:
                        score += 0.07

                    has_keywords_in_export = isinstance(sample.get("keywords"), list) and len(sample.get("keywords", [])) > 0
                    checks.append({
                        "name": "Export categories have keywords array",
                        "passed": has_keywords_in_export,
                        "detail": f"Sample keywords: {sample.get('keywords', [])[:3]}"
                    })
                    if has_keywords_in_export:
                        score += 0.04

                    has_search_params_in_export = isinstance(sample.get("search_params"), dict)
                    checks.append({
                        "name": "Export categories have search_params",
                        "passed": has_search_params_in_export,
                        "detail": f"Sample search_params: {sample.get('search_params')}"
                    })
                    if has_search_params_in_export:
                        score += 0.04
        except Exception as e:
            checks.append({"name": "Export file is valid JSON", "passed": False, "detail": str(e)})
    else:
        checks.append({
            "name": "Export file generated at exports/active-news-config.json",
            "passed": False,
            "detail": f"Not found at {export_path}"
        })

    # ─── Final scoring ───
    score = min(round(score, 3), 1.0)
    total_passed = sum(1 for c in checks if c["passed"])
    all_passed = total_passed >= int(len(checks) * 0.75)  # 75% threshold to pass

    print(json.dumps({
        "passed": all_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)