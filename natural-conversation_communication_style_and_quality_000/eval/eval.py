import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # --- Locate the output file ---
    output_candidates = list(Path(workspace_dir).rglob("natural_replies.json"))
    if not output_candidates:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "natural_replies.json not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = output_candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_path}"})

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "output_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_parseable", "passed": True, "detail": "JSON parsed successfully."})

    # Ensure it's a list with at least 6 entries
    if not isinstance(data, list) or len(data) < 6:
        checks.append({"name": "output_structure", "passed": False, "detail": f"Expected list of >=6 entries, got {type(data).__name__} with length {len(data) if isinstance(data, list) else 'N/A'}."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_structure", "passed": True, "detail": f"List with {len(data)} entries found."})

    # Build a dict by id
    reply_map = {}
    for entry in data:
        if isinstance(entry, dict) and "id" in entry:
            key = entry["id"]
            # Accept natural_reply or rewritten_reply field
            text = entry.get("natural_reply") or entry.get("rewritten_reply") or entry.get("reply") or ""
            reply_map[key] = (text, entry)

    # -----------------------------------------------------------------------
    # BANNED JAPANESE PHRASES (from SKILL.md)
    # -----------------------------------------------------------------------
    banned_jp_patterns = [
        r"させていただきます",
        r"以下の通りです",
        r"以下の通りご",
        r"ご不明な点がございましたら",
        r"お気軽にお申し付けください",
        r"〜と存じます",
        r"かと思われます",
        r"誠に申し訳ございません",
        r"ご確認ください",        # banned exact form per table
        r"ご連絡いただきまして",
        r"お問い合わせいただきまして",
        r"以下のポイントをご確認",
        r"以下の通り対応させていただきます",
        r"まず、.*次に、.*最後に、",  # mechanical structure
        r"ご回答申し上げます",
        r"ご報告申し上げます",
        r"誠にありがとうございます",  # overly formal
        r"お気軽にお問い合わせください",
    ]

    # BANNED ENGLISH PHRASES (from SKILL.md)
    banned_en_patterns = [
        r"I would like to express my",
        r"Please find below",
        r"do not hesitate to contact",
        r"do not hesitate to reach out",
        r"should you have any further questions",
        r"at the earliest convenience",
        r"as per your instructions",
        r"I am pleased to inform you",
        r"sincere gratitude",
    ]

    # -----------------------------------------------------------------------
    # CHECK 1: Forbidden Japanese phrases removed (IDs 1,2,4,5)
    # -----------------------------------------------------------------------
    jp_ids = [1, 2, 4, 5]
    jp_banned_found = []
    max_score += 25.0
    for rid in jp_ids:
        if rid not in reply_map:
            jp_banned_found.append(f"ID {rid}: missing")
            continue
        text, _ = reply_map[rid]
        for pat in banned_jp_patterns:
            if re.search(pat, text):
                jp_banned_found.append(f"ID {rid}: matched forbidden pattern '{pat}'")

    if not jp_banned_found:
        checks.append({"name": "jp_forbidden_phrases_removed", "passed": True, "detail": "No banned Japanese phrases found in JP replies."})
        total_score += 25.0
    else:
        checks.append({"name": "jp_forbidden_phrases_removed", "passed": False, "detail": "; ".join(jp_banned_found[:5])})

    # -----------------------------------------------------------------------
    # CHECK 2: Forbidden English phrases removed (IDs 3,6)
    # -----------------------------------------------------------------------
    en_ids = [3, 6]
    en_banned_found = []
    max_score += 20.0
    for rid in en_ids:
        if rid not in reply_map:
            en_banned_found.append(f"ID {rid}: missing")
            continue
        text, _ = reply_map[rid]
        for pat in banned_en_patterns:
            if re.search(pat, text, re.IGNORECASE):
                en_banned_found.append(f"ID {rid}: matched forbidden pattern '{pat}'")

    if not en_banned_found:
        checks.append({"name": "en_forbidden_phrases_removed", "passed": True, "detail": "No banned English phrases found in EN replies."})
        total_score += 20.0
    else:
        checks.append({"name": "en_forbidden_phrases_removed", "passed": False, "detail": "; ".join(en_banned_found[:5])})

    # -----------------------------------------------------------------------
    # CHECK 3: Tone matching - short customer messages must have short replies
    # IDs 2,5 have very short messages ("このデザインどう思う？" / "修正お願い！")
    # Replies must be SHORT (not multi-paragraph lectures)
    # Per SKILL.md: short input → short output, never longer than input message
    # -----------------------------------------------------------------------
    max_score += 20.0
    short_tone_issues = []
    short_ids = {
        2: "このデザインどう思う？",
        5: "修正お願い！",
    }
    for rid, customer_msg in short_ids.items():
        if rid not in reply_map:
            short_tone_issues.append(f"ID {rid}: missing")
            continue
        text, _ = reply_map[rid]
        customer_len = len(customer_msg)
        reply_len = len(text)
        # Strict rule: reply should be no longer than the original draft's customer message
        # Also check: no bullet list overuse (more than 2 bullets is suspicious for a short casual reply)
        bullet_count = len(re.findall(r"[・•\-\*]\s", text))
        numbered_lines = len(re.findall(r"^\d+\.", text, re.MULTILINE))
        if reply_len > 120:
            short_tone_issues.append(f"ID {rid}: reply too long ({reply_len} chars) for short customer message ({customer_len} chars). Expected ≤120 chars.")
        if bullet_count > 2 or numbered_lines > 2:
            short_tone_issues.append(f"ID {rid}: too many bullet/numbered items ({bullet_count} bullets, {numbered_lines} numbered) for a casual short reply.")

    if not short_tone_issues:
        checks.append({"name": "short_message_short_reply", "passed": True, "detail": "Short customer messages received appropriately short replies."})
        total_score += 20.0
    else:
        checks.append({"name": "short_message_short_reply", "passed": False, "detail": "; ".join(short_tone_issues)})

    # -----------------------------------------------------------------------
    # CHECK 4: Platform-specific natural language indicators
    # Coconala: polite but natural, should contain warm connectors
    # X/Threads: casual, should contain casual expressions
    # Fiverr: friendly professional English
    # -----------------------------------------------------------------------
    max_score += 20.0
    platform_issues = []

    # Coconala (IDs 1, 4): must NOT have over-formal markers, MUST have some naturalness
    # Check: no 「〜でしょうか？」overuse, no 「〜申し上げます」
    for rid in [1, 4]:
        if rid not in reply_map:
            platform_issues.append(f"ID {rid}: missing")
            continue
        text, _ = reply_map[rid]
        if re.search(r"申し上げます", text):
            platform_issues.append(f"ID {rid} (coconala): still uses 'お申し上げます' - too formal.")
        if re.search(r"いただけますでしょうか", text):
            platform_issues.append(f"ID {rid} (coconala): uses 'いただけますでしょうか' - overly formal question form.")
        # Must have at least some reply text
        if len(text.strip()) < 10:
            platform_issues.append(f"ID {rid} (coconala): reply is too short/empty.")

    # X/Threads (IDs 2, 5): must be casual, no stiff business Japanese
    for rid in [2, 5]:
        if rid not in reply_map:
            platform_issues.append(f"ID {rid}: missing")
            continue
        text, _ = reply_map[rid]
        if re.search(r"申し上げます|いたします|ございます|誠に|拝察", text):
            platform_issues.append(f"ID {rid} (x_threads): still uses stiff formal Japanese unsuitable for casual platform.")

    # Fiverr (IDs 3, 6): should be friendly English, must not be cold/robotic
    for rid in [3, 6]:
        if rid not in reply_map:
            platform_issues.append(f"ID {rid}: missing")
            continue
        text, _ = reply_map[rid]
        # Should not use overly corporate stiff English
        if re.search(r"I would like to|Please find below|do not hesitate", text, re.IGNORECASE):
            platform_issues.append(f"ID {rid} (fiverr): still uses robotic English phrases.")
        # Must have some friendly marker
        friendly_markers = re.search(r"(Thanks|Happy to|Sure|Great|Sounds good|Let me|Got it|Love|Awesome)", text, re.IGNORECASE)
        if not friendly_markers:
            platform_issues.append(f"ID {rid} (fiverr): missing friendly/warm English tone markers (e.g., 'Thanks', 'Happy to', 'Sure', 'Got it').")

    if not platform_issues:
        checks.append({"name": "platform_specific_tone", "passed": True, "detail": "All replies match their platform's expected tone."})
        total_score += 20.0
    else:
        checks.append({"name": "platform_specific_tone", "passed": False, "detail": "; ".join(platform_issues[:6])})

    # -----------------------------------------------------------------------
    # CHECK 5: Substitution table compliance
    # 「させていただきます」→「しますね」type replacements must be present where needed
    # More precisely: banned forms should be replaced with natural equivalents
    # Check that ID 4 (apology scenario) does NOT use 「誠に申し訳ございません」
    # and ID 4 should have something like 「すみません」or「ごめんなさい」or similar natural apology
    # Also check that ID 1's coconala reply uses natural question forms (not 「いただけますでしょうか」)
    # -----------------------------------------------------------------------
    max_score += 15.0
    subst_issues = []

    # ID 4: apology must be natural
    if 4 in reply_map:
        text, _ = reply_map[4]
        has_natural_apology = bool(re.search(r"ごめん|すみません|申し訳ない(?!ございません)", text))
        still_formal_apology = bool(re.search(r"誠に申し訳ございません|申し訳ございません", text))
        if still_formal_apology:
            subst_issues.append("ID 4: still uses '誠に申し訳ございません' - must use natural alternative like 'ごめんなさい' or 'すみません'.")
        elif not has_natural_apology:
            subst_issues.append("ID 4: No natural apology expression found. Expected 'ごめん', 'すみません', or similar per substitution table.")

    # ID 1: natural question forms (should use casual question like 「どんな感じ」or「どのくらい」)
    if 1 in reply_map:
        text, _ = reply_map[1]
        overly_formal_q = re.search(r"お聞かせいただけますでしょうか|お教えいただけますでしょうか", text)
        if overly_formal_q:
            subst_issues.append("ID 1: uses overly formal question form - should use simpler phrasing like '〜ってどんな感じ？' or '〜はどのくらい？'.")

    if not subst_issues:
        checks.append({"name": "substitution_table_compliance", "passed": True, "detail": "Banned formal expressions replaced with natural alternatives."})
        total_score += 15.0
    else:
        checks.append({"name": "substitution_table_compliance", "passed": False, "detail": "; ".join(subst_issues)})

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed_count = sum(1 for c in checks if c["passed"])
    critical_checks = ["jp_forbidden_phrases_removed", "en_forbidden_phrases_removed", "platform_specific_tone"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = (final_score >= 0.70) and critical_passed

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))