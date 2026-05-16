import sys
import json
import os
from pathlib import Path

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def run_eval(workspace: str):
    checks = []
    
    # ----------------------------------------------------------------
    # Find curated_trends.json anywhere in workspace
    # ----------------------------------------------------------------
    candidates = list(Path(workspace).rglob("curated_trends.json"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "curated_trends.json not found anywhere in workspace"}]
        }
    
    # Pick the most recently modified if multiple
    output_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    try:
        data = load_json(output_path)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }

    checks.append({"name": "file_exists_and_parseable", "passed": True, "detail": str(output_path)})

    # ----------------------------------------------------------------
    # Expect top-level structure: {"tweets": [...], "summary": "..."}
    # ----------------------------------------------------------------
    has_tweets_key = isinstance(data, dict) and "tweets" in data
    if not has_tweets_key:
        # Also accept bare list
        if isinstance(data, list):
            tweets = data
            summary = ""
        else:
            checks.append({"name": "structure_valid", "passed": False, "detail": "Expected dict with 'tweets' key or a list"})
            return {"passed": False, "score": 0.1, "checks": checks}
    else:
        tweets = data["tweets"]
        summary = data.get("summary", "")

    checks.append({"name": "structure_valid", "passed": True, "detail": f"Found {len(tweets)} tweets"})

    # ----------------------------------------------------------------
    # CHECK 1: Total count 5-8
    # ----------------------------------------------------------------
    total_ok = 5 <= len(tweets) <= 8
    checks.append({
        "name": "total_count_5_to_8",
        "passed": total_ok,
        "detail": f"Total tweets: {len(tweets)} (expected 5-8)"
    })

    # ----------------------------------------------------------------
    # CHECK 2: Language balance (3-5 JP, 3-5 EN)
    # ----------------------------------------------------------------
    ja_tweets = [t for t in tweets if t.get("lang") == "ja"]
    en_tweets = [t for t in tweets if t.get("lang") == "en"]
    ja_balance = 3 <= len(ja_tweets) <= 5
    en_balance = 3 <= len(en_tweets) <= 5
    checks.append({
        "name": "language_balance_ja",
        "passed": ja_balance,
        "detail": f"Japanese tweets: {len(ja_tweets)} (expected 3-5)"
    })
    checks.append({
        "name": "language_balance_en",
        "passed": en_balance,
        "detail": f"English tweets: {len(en_tweets)} (expected 3-5)"
    })

    # ----------------------------------------------------------------
    # CHECK 3: No hype accounts included
    # HYPE accounts in our dataset: aiHYPE_daily, hype_jp_ai
    # ----------------------------------------------------------------
    hype_authors = {"aiHYPE_daily", "hype_jp_ai"}
    hype_included = [t for t in tweets if t.get("author") in hype_authors]
    no_hype = len(hype_included) == 0
    checks.append({
        "name": "no_hype_accounts",
        "passed": no_hype,
        "detail": f"Hype accounts included: {[t.get('author') for t in hype_included]}"
    })

    # ----------------------------------------------------------------
    # CHECK 4: No already-posted URL included
    # Posted URL: https://x.com/skirano/status/1745000000004
    # ----------------------------------------------------------------
    already_posted_urls = {
        "https://x.com/skirano/status/1745000000004",
        "https://x.com/old_user/status/1744000000001",
        "https://x.com/old_user/status/1744000000002",
    }
    duplicate_urls = [t for t in tweets if t.get("url") in already_posted_urls]
    no_duplicates = len(duplicate_urls) == 0
    checks.append({
        "name": "no_already_posted_urls",
        "passed": no_duplicates,
        "detail": f"Already-posted URLs included: {[t.get('url') for t in duplicate_urls]}"
    })

    # ----------------------------------------------------------------
    # CHECK 5: No below-threshold tweets
    # EN threshold: 500 likes; JA threshold: 100 likes
    # Below-threshold in dataset: randomdev (287 likes EN), newbie_ai (45 likes JA)
    # ----------------------------------------------------------------
    below_threshold_ids = {"1745000000007", "1745000000015"}
    below_threshold_included = [t for t in tweets if t.get("id") in below_threshold_ids]
    no_below_threshold = len(below_threshold_included) == 0
    checks.append({
        "name": "no_below_threshold_tweets",
        "passed": no_below_threshold,
        "detail": f"Below-threshold tweets included: {[t.get('id') for t in below_threshold_included]}"
    })

    # ----------------------------------------------------------------
    # CHECK 6: Each tweet has required fields: category, author_desc, quote_suggestion
    # ----------------------------------------------------------------
    required_fields = ["category", "author_desc", "quote_suggestion"]
    missing_fields_tweets = []
    for t in tweets:
        missing = [f for f in required_fields if not t.get(f)]
        if missing:
            missing_fields_tweets.append({"id": t.get("id", "?"), "missing": missing})
    
    all_have_required = len(missing_fields_tweets) == 0
    checks.append({
        "name": "all_tweets_have_required_fields",
        "passed": all_have_required,
        "detail": f"Tweets missing fields: {missing_fields_tweets}"
    })

    # ----------------------------------------------------------------
    # CHECK 7: English tweets have text_ja field
    # ----------------------------------------------------------------
    en_missing_text_ja = [t for t in en_tweets if not t.get("text_ja")]
    en_has_text_ja = len(en_missing_text_ja) == 0
    checks.append({
        "name": "english_tweets_have_text_ja",
        "passed": en_has_text_ja,
        "detail": f"English tweets missing text_ja: {[t.get('id') for t in en_missing_text_ja]}"
    })

    # ----------------------------------------------------------------
    # CHECK 8: quote_suggestion length 5-100 characters
    # ----------------------------------------------------------------
    bad_length_quotes = []
    for t in tweets:
        qs = t.get("quote_suggestion", "")
        if qs and not (5 <= len(qs) <= 100):
            bad_length_quotes.append({"id": t.get("id"), "len": len(qs), "quote": qs[:50]})
    
    quote_length_ok = len(bad_length_quotes) == 0
    checks.append({
        "name": "quote_suggestion_length_5_to_100",
        "passed": quote_length_ok,
        "detail": f"Quotes with wrong length: {bad_length_quotes}"
    })

    # ----------------------------------------------------------------
    # CHECK 9: quote_suggestion persona - first person 僕 usage
    # At least some quotes should use 僕 (not required on every single one,
    # but we check none use 私 or 俺 as primary persona contradiction)
    # ----------------------------------------------------------------
    wrong_persona_quotes = []
    for t in tweets:
        qs = t.get("quote_suggestion", "")
        # persona uses 僕; 私 or 俺 as I-pronoun would be wrong
        if "私は" in qs or "俺は" in qs or "私が" in qs or "俺が" in qs:
            wrong_persona_quotes.append({"id": t.get("id"), "quote": qs})
    
    persona_ok = len(wrong_persona_quotes) == 0
    checks.append({
        "name": "quote_persona_correct",
        "passed": persona_ok,
        "detail": f"Wrong persona quotes (使用禁止: 私/俺): {wrong_persona_quotes}"
    })

    # ----------------------------------------------------------------
    # CHECK 10: No thin/empty reactions in quotes
    # Banned: 最高！, 同意です, すごい, いいね
    # ----------------------------------------------------------------
    banned_reactions = ["最高！", "同意です", "すごいですね", "いいですね"]
    thin_reaction_tweets = []
    for t in tweets:
        qs = t.get("quote_suggestion", "")
        for banned in banned_reactions:
            if banned in qs:
                thin_reaction_tweets.append({"id": t.get("id"), "banned_phrase": banned, "quote": qs})
                break
    
    no_thin_reactions = len(thin_reaction_tweets) == 0
    checks.append({
        "name": "no_thin_reaction_quotes",
        "passed": no_thin_reactions,
        "detail": f"Thin reaction quotes found: {thin_reaction_tweets}"
    })

    # ----------------------------------------------------------------
    # CHECK 11: Category uses valid emoji-prefixed slug format
    # Valid: :rocket: new_release, :hammer_and_wrench: tools, 
    #        :microscope: research, :thought_balloon: opinions, :bulb: tips
    # ----------------------------------------------------------------
    valid_categories = {
        ":rocket: new_release",
        ":hammer_and_wrench: tools",
        ":microscope: research",
        ":thought_balloon: opinions",
        ":bulb: tips"
    }
    invalid_category_tweets = []
    for t in tweets:
        cat = t.get("category", "")
        if cat not in valid_categories:
            invalid_category_tweets.append({"id": t.get("id"), "category": cat})
    
    categories_valid = len(invalid_category_tweets) == 0
    checks.append({
        "name": "categories_use_valid_emoji_slug_format",
        "passed": categories_valid,
        "detail": f"Invalid categories: {invalid_category_tweets}. Valid options: {valid_categories}"
    })

    # ----------------------------------------------------------------
    # CHECK 12: quote_suggestion has a quote pattern label (A-H)
    # Either as field "quote_pattern" or embedded reference
    # ----------------------------------------------------------------
    valid_patterns = set("ABCDEFGH")
    missing_pattern_tweets = []
    for t in tweets:
        pattern = t.get("quote_pattern", "")
        if not pattern or pattern.upper() not in valid_patterns:
            missing_pattern_tweets.append({"id": t.get("id"), "pattern": pattern})
    
    patterns_present = len(missing_pattern_tweets) == 0
    checks.append({
        "name": "quote_pattern_A_to_H_labeled",
        "passed": patterns_present,
        "detail": f"Tweets missing valid quote pattern (A-H): {missing_pattern_tweets}"
    })

    # ----------------------------------------------------------------
    # CHECK 13: mark-posted was called - verify recently_posted.json updated
    # ----------------------------------------------------------------
    try:
        recent_data = load_json(os.path.join(workspace, "data/processed/recently_posted.json"))
        posted_urls_in_file = set(recent_data.get("posted_urls", []))
        curated_urls = {t.get("url") for t in tweets if t.get("url")}
        new_urls_marked = curated_urls.issubset(posted_urls_in_file)
        checks.append({
            "name": "curated_urls_marked_as_posted",
            "passed": new_urls_marked,
            "detail": f"Curated URLs not yet marked: {curated_urls - posted_urls_in_file}"
        })
    except Exception as e:
        checks.append({
            "name": "curated_urls_marked_as_posted",
            "passed": False,
            "detail": f"Could not verify mark-posted: {e}"
        })

    # ----------------------------------------------------------------
    # Score calculation
    # ----------------------------------------------------------------
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    
    # Weight critical checks more heavily
    critical_check_names = [
        "total_count_5_to_8",
        "no_hype_accounts",
        "no_already_posted_urls",
        "language_balance_ja",
        "language_balance_en",
        "categories_use_valid_emoji_slug_format",
        "quote_pattern_A_to_H_labeled",
        "english_tweets_have_text_ja",
    ]
    
    critical_passed = sum(1 for c in checks if c["name"] in critical_check_names and c["passed"])
    critical_total = len(critical_check_names)
    
    # Weighted score: 60% critical checks, 40% all checks
    score = 0.6 * (critical_passed / critical_total) + 0.4 * (passed_checks / total_checks)
    score = round(score, 3)
    
    # Must pass all critical checks + at least 80% overall to pass
    overall_passed = (critical_passed == critical_total) and (passed_checks / total_checks >= 0.8)
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))