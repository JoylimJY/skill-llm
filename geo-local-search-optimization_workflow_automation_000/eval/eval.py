import sys
import json
import os
from pathlib import Path

def find_output_file(workspace):
    """Search for optimization_plan.json anywhere under workspace."""
    candidates = list(Path(workspace).rglob("optimization_plan.json"))
    return candidates[0] if candidates else None

def count_words(text):
    """Simple word counter — splits on whitespace."""
    return len(text.split())

def eval_main(workspace):
    checks = []
    total_score = 0.0

    # ─── Locate output file ───────────────────────────────────────────────────
    output_path = find_output_file(workspace)
    file_found = output_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found at {output_path}" if file_found else "optimization_plan.json not found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ─── Parse JSON ───────────────────────────────────────────────────────────
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ─── CHECK 1: Correct legal business name used (from license, NOT brief alias) ──
    # Must contain the official registered name (either Chinese or English trade name)
    legal_name_cn = "成都松果餐饮管理有限公司锦江分店"
    legal_name_en = "Chengdu Songguo Hotpot Restaurant"
    legal_name_en_alt = "Chengdu Songguo Catering"
    alias_wrong = "Pinecone Hotpot"

    plan_str = json.dumps(plan, ensure_ascii=False)
    has_legal_name = (legal_name_cn in plan_str or
                      legal_name_en in plan_str or
                      legal_name_en_alt in plan_str)
    uses_wrong_alias = alias_wrong in plan_str

    checks.append({
        "name": "uses_legal_business_name",
        "passed": has_legal_name,
        "detail": f"Legal name present: {has_legal_name}. Wrong alias used: {uses_wrong_alias}."
    })
    if has_legal_name:
        total_score += 0.15

    checks.append({
        "name": "avoids_wrong_alias",
        "passed": not uses_wrong_alias,
        "detail": f"'Pinecone Hotpot' (informal alias) {'was NOT found — correct' if not uses_wrong_alias else 'WAS found — wrong name used'}"
    })
    if not uses_wrong_alias:
        total_score += 0.05

    # ─── CHECK 2: 7 daily articles present ───────────────────────────────────
    try:
        articles = plan.get("articles", [])
        has_7_articles = len(articles) == 7
        checks.append({
            "name": "seven_articles_present",
            "passed": has_7_articles,
            "detail": f"Found {len(articles)} article(s); expected exactly 7"
        })
        if has_7_articles:
            total_score += 0.10
    except Exception as e:
        articles = []
        checks.append({"name": "seven_articles_present", "passed": False,
                        "detail": f"Error reading articles: {e}"})

    # ─── CHECK 3: Each article has 500+ words ─────────────────────────────────
    if articles:
        articles_500_plus = 0
        article_details = []
        for i, art in enumerate(articles):
            title = art.get("title", "")
            content = art.get("content", "")
            combined = title + " " + content
            wc = count_words(combined)
            passed = wc >= 500
            if passed:
                articles_500_plus += 1
            article_details.append(f"Article {i+1}: {wc} words ({'OK' if passed else 'FAIL'})")

        all_500_plus = articles_500_plus == len(articles)
        checks.append({
            "name": "all_articles_500_plus_words",
            "passed": all_500_plus,
            "detail": "; ".join(article_details)
        })
        if all_500_plus:
            total_score += 0.15
        elif articles_500_plus > 0:
            total_score += 0.05 * (articles_500_plus / len(articles))

    # ─── CHECK 4: Each article contains business address and phone ────────────
    if articles:
        addr_keywords = ["Shaocheng", "少城路", "Jinjiang", "锦江", "No. 88", "88号"]
        phone = "028-85551234"
        articles_with_contact = 0
        contact_details = []
        for i, art in enumerate(articles):
            content_str = json.dumps(art, ensure_ascii=False)
            has_addr = any(kw in content_str for kw in addr_keywords)
            has_phone = phone in content_str
            passed = has_addr and has_phone
            if passed:
                articles_with_contact += 1
            contact_details.append(
                f"Article {i+1}: addr={'Y' if has_addr else 'N'}, phone={'Y' if has_phone else 'N'}"
            )
        all_have_contact = articles_with_contact == len(articles)
        checks.append({
            "name": "all_articles_contain_address_and_phone",
            "passed": all_have_contact,
            "detail": "; ".join(contact_details)
        })
        if all_have_contact:
            total_score += 0.10
        elif articles_with_contact > 0:
            total_score += 0.04 * (articles_with_contact / len(articles))

    # ─── CHECK 5: 5 keywords present ──────────────────────────────────────────
    expected_keywords = [
        "成都火锅推荐", "锦江区麻辣火锅", "成都聚餐好去处", "正宗四川火锅", "成都网红火锅店"
    ]
    found_keywords = [kw for kw in expected_keywords if kw in plan_str]
    all_keywords = len(found_keywords) == 5
    checks.append({
        "name": "five_keywords_present",
        "passed": all_keywords,
        "detail": f"Found {len(found_keywords)}/5 keywords: {found_keywords}"
    })
    if all_keywords:
        total_score += 0.05

    # ─── CHECK 6: Media selection — correct tiers present ────────────────────
    try:
        selected_media = plan.get("selected_media", [])
        selected_ids = [m.get("id") for m in selected_media] if isinstance(selected_media, list) else []
        selected_ids_str = json.dumps(selected_media, ensure_ascii=False)

        # All three geographic tiers must be represented
        provincial_valid = {"M01", "M02"}
        municipal_valid = {"M05", "M06"}
        local_valid = {"M09", "M10", "M11"}

        # Check tiers covered
        has_provincial = any(mid in selected_ids for mid in provincial_valid)
        has_municipal = any(mid in selected_ids for mid in municipal_valid)
        has_local = any(mid in selected_ids for mid in local_valid)

        tiers_covered = has_provincial and has_municipal and has_local
        checks.append({
            "name": "all_geographic_tiers_covered",
            "passed": tiers_covered,
            "detail": f"Selected IDs: {selected_ids}. Provincial: {has_provincial}, Municipal: {has_municipal}, Local: {has_local}"
        })
        if tiers_covered:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "all_geographic_tiers_covered", "passed": False,
                        "detail": f"Error reading selected_media: {e}"})

    # ─── CHECK 7: No cross-industry media selected ────────────────────────────
    try:
        invalid_ids = {"M03", "M04", "M07", "M08", "M12"}  # automotive/education/beauty/fitness
        selected_invalid = [mid for mid in selected_ids if mid in invalid_ids]
        no_cross_industry = len(selected_invalid) == 0
        checks.append({
            "name": "no_cross_industry_media",
            "passed": no_cross_industry,
            "detail": f"Invalid (cross-industry) channels selected: {selected_invalid if selected_invalid else 'None — correct'}"
        })
        if no_cross_industry:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "no_cross_industry_media", "passed": False,
                        "detail": f"Error checking cross-industry: {e}"})

    # ─── CHECK 8: Cost-efficiency — lowest-priced within each valid tier ──────
    # Provincial valid options: M01(800), M02(650) → cheapest = M02
    # Municipal valid options: M05(500), M06(420) → cheapest = M06
    # Local valid options:     M09(200), M10(180), M11(150) → cheapest = M11
    try:
        # For each tier, if the agent selected media, the cheapest valid one must be chosen
        # (it's OK to select MORE than one, but the cheapest must be included; or only cheapest selected)
        cheapest_per_tier = {
            "provincial": "M02",  # 650 vs 800
            "municipal": "M06",   # 420 vs 500
            "local": "M11",       # 150 vs 180 vs 200
        }
        cost_details = []
        cost_score_parts = 0
        for tier, cheapest_id in cheapest_per_tier.items():
            is_cheapest_selected = cheapest_id in selected_ids
            cost_details.append(f"{tier}: cheapest={cheapest_id}, selected={is_cheapest_selected}")
            if is_cheapest_selected:
                cost_score_parts += 1

        all_cheapest = cost_score_parts == 3
        checks.append({
            "name": "cost_efficiency_cheapest_per_tier",
            "passed": all_cheapest,
            "detail": "; ".join(cost_details)
        })
        if all_cheapest:
            total_score += 0.15
        elif cost_score_parts > 0:
            total_score += 0.04 * cost_score_parts
    except Exception as e:
        checks.append({"name": "cost_efficiency_cheapest_per_tier", "passed": False,
                        "detail": f"Error checking cost efficiency: {e}"})

    # ─── Final result ─────────────────────────────────────────────────────────
    total_score = min(round(total_score, 3), 1.0)
    passed = total_score >= 0.75

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = eval_main(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))