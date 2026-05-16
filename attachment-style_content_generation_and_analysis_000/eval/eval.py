import sys
import json
import re
from pathlib import Path

def load_report(reports_dir, user_id):
    filename = f"{user_id}_report.txt"
    # Search in reports/final/ first, then broadly
    target = reports_dir / filename
    if not target.exists():
        # Try rglob as fallback
        matches = list(Path(sys.argv[1]).rglob(filename))
        if matches:
            return matches[0].read_text(encoding="utf-8")
        return None
    return target.read_text(encoding="utf-8")

def check_format_sections(text, lang="en"):
    """Check the 5 required emoji-prefixed sections exist."""
    required = [
        ("🔗", "Attachment Style emoji section"),
        ("🔍", "Evidence emoji section"),
        ("💡", "Your Pattern emoji section / 你的模式"),
        ("🎯", "Strategy emoji section"),
        ("📖", "Deeper emoji section"),
    ]
    results = []
    for emoji, name in required:
        found = emoji in text
        results.append((name, found, f"{'Found' if found else 'MISSING'}: {emoji}"))
    return results

def check_style_identification(text, expected_style_keywords, user_id):
    """Check that the correct attachment style is identified."""
    text_lower = text.lower()
    found = any(kw.lower() in text_lower for kw in expected_style_keywords)
    return found, f"Expected one of {expected_style_keywords} for {user_id}"

def check_confidence_level(text):
    """Check that a confidence level is mentioned in the style line."""
    # Look for confidence indicators near the style line
    confidence_patterns = [
        r"(?i)(high|medium|low|strong|moderate|very\s+likely|likely|confident|确信|高|中|低|较高|较低)",
        r"(?i)\d{1,3}%",
        r"(?i)(clear|clearly|strongly suggest|strongly indicate)",
    ]
    for pat in confidence_patterns:
        if re.search(pat, text):
            return True, "Confidence level indicator found"
    return False, "No confidence level found near style identification"

def check_pairing_dynamic(text, user_id):
    """For U-2041 (Anxious+Avoidant pair), check for pursue-withdraw terminology."""
    keywords = [
        "pursue-withdraw", "pursue withdraw", "pursues", "withdraw",
        "death spiral", "anxious.*avoidant", "avoidant.*anxious",
        "追.*回避", "回避.*焦虑", "追逐.*回避",
    ]
    found = any(re.search(kw, text, re.IGNORECASE) for kw in keywords)
    return found, f"Pairing dynamic analysis for {user_id}"

def check_strategies_count(text):
    """Check that at least 2 actionable strategies are present after 🎯."""
    strat_idx = text.find("🎯")
    if strat_idx == -1:
        return False, "🎯 section not found"
    strat_section = text[strat_idx:]
    # Find next section
    next_section = strat_section.find("📖")
    if next_section != -1:
        strat_section = strat_section[:next_section]
    # Count bullet points or numbered items or line breaks with content
    lines = [l.strip() for l in strat_section.split("\n") if l.strip() and l.strip() not in ["🎯", "🎯 Strategy:", "🎯 Strategy"]]
    # Remove header line
    lines = [l for l in lines if not l.startswith("🎯")]
    strategy_lines = [l for l in lines if len(l) > 15]
    count = len(strategy_lines)
    return count >= 2, f"Found {count} strategy lines (need >= 2)"

def check_language(text, expected_lang):
    """Rough check: Chinese report should contain Chinese characters."""
    if expected_lang == "zh":
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return chinese_chars > 50, f"Chinese char count: {chinese_chars} (need > 50)"
    else:
        # English report should not be predominantly Chinese
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_alpha = len(re.findall(r'[a-zA-Z]', text))
        return total_alpha > 100, f"English char count: {total_alpha} (need > 100)"

def check_no_excuse_behavior(text):
    """Safety: should not say things like 'I can't help it' as an excuse."""
    bad_patterns = [
        r"(?i)can't help (it|myself)",
        r"(?i)not (my|their) fault because.*avoidant",
        r"(?i)avoidant.*excuse",
    ]
    for pat in bad_patterns:
        if re.search(pat, text):
            return False, f"Report excuses bad behavior with attachment label: matched '{pat}'"
    return True, "No excuse-behavior language detected"

def check_fearful_avoidant(text, user_id="U-2043"):
    """U-2043 should be identified as Fearful-Avoidant."""
    keywords = [
        "fearful-avoidant", "fearful avoidant", "FA", "恐惧型", "恐惧回避",
        "hot-cold", "hot cold", "push-pull", "push pull",
        "idealization", "idealiz", "冷热", "推拉",
    ]
    found = any(kw.lower() in text.lower() for kw in keywords)
    return found, f"Fearful-Avoidant identification for {user_id}"

def main():
    workspace = Path(sys.argv[1])
    reports_dir = workspace / "reports" / "final"

    checks = []
    total_score = 0.0
    max_score = 0.0

    # ---- U-2041: Priya — Anxious user with Avoidant partner ----
    report_2041 = load_report(reports_dir, "U-2041")

    checks.append({
        "name": "U-2041: Report file exists",
        "passed": report_2041 is not None,
        "detail": "File U-2041_report.txt found" if report_2041 else "File U-2041_report.txt NOT found"
    })
    max_score += 1.0
    if report_2041:
        total_score += 1.0

    if report_2041:
        # Format sections
        for name, passed, detail in check_format_sections(report_2041, "en"):
            checks.append({"name": f"U-2041 Format: {name}", "passed": passed, "detail": detail})
            max_score += 0.5
            if passed:
                total_score += 0.5

        # Style: Anxious
        style_ok, style_detail = check_style_identification(
            report_2041,
            ["anxious", "焦虑型", "anxious attachment"],
            "U-2041"
        )
        checks.append({"name": "U-2041: Correct style = Anxious", "passed": style_ok, "detail": style_detail})
        max_score += 2.0
        if style_ok:
            total_score += 2.0

        # Confidence level
        conf_ok, conf_detail = check_confidence_level(report_2041)
        checks.append({"name": "U-2041: Confidence level present", "passed": conf_ok, "detail": conf_detail})
        max_score += 1.0
        if conf_ok:
            total_score += 1.0

        # Pairing dynamic (Anxious + Avoidant)
        pair_ok, pair_detail = check_pairing_dynamic(report_2041, "U-2041")
        checks.append({"name": "U-2041: Pairing dynamic analysis (Anxious+Avoidant)", "passed": pair_ok, "detail": pair_detail})
        max_score += 2.0
        if pair_ok:
            total_score += 2.0

        # Strategies >= 2
        strat_ok, strat_detail = check_strategies_count(report_2041)
        checks.append({"name": "U-2041: At least 2 strategies", "passed": strat_ok, "detail": strat_detail})
        max_score += 1.0
        if strat_ok:
            total_score += 1.0

        # Language: English
        lang_ok, lang_detail = check_language(report_2041, "en")
        checks.append({"name": "U-2041: Report in English", "passed": lang_ok, "detail": lang_detail})
        max_score += 0.5
        if lang_ok:
            total_score += 0.5

        # Safety check
        safe_ok, safe_detail = check_no_excuse_behavior(report_2041)
        checks.append({"name": "U-2041: Safety — no excuse behavior", "passed": safe_ok, "detail": safe_detail})
        max_score += 0.5
        if safe_ok:
            total_score += 0.5

    # ---- U-2042: Marcus — Avoidant ----
    report_2042 = load_report(reports_dir, "U-2042")

    checks.append({
        "name": "U-2042: Report file exists",
        "passed": report_2042 is not None,
        "detail": "File U-2042_report.txt found" if report_2042 else "File U-2042_report.txt NOT found"
    })
    max_score += 1.0
    if report_2042:
        total_score += 1.0

    if report_2042:
        for name, passed, detail in check_format_sections(report_2042, "en"):
            checks.append({"name": f"U-2042 Format: {name}", "passed": passed, "detail": detail})
            max_score += 0.5
            if passed:
                total_score += 0.5

        style_ok, style_detail = check_style_identification(
            report_2042,
            ["avoidant", "回避型", "dismissive"],
            "U-2042"
        )
        checks.append({"name": "U-2042: Correct style = Avoidant", "passed": style_ok, "detail": style_detail})
        max_score += 2.0
        if style_ok:
            total_score += 2.0

        conf_ok, conf_detail = check_confidence_level(report_2042)
        checks.append({"name": "U-2042: Confidence level present", "passed": conf_ok, "detail": conf_detail})
        max_score += 1.0
        if conf_ok:
            total_score += 1.0

        strat_ok, strat_detail = check_strategies_count(report_2042)
        checks.append({"name": "U-2042: At least 2 strategies", "passed": strat_ok, "detail": strat_detail})
        max_score += 1.0
        if strat_ok:
            total_score += 1.0

        lang_ok, lang_detail = check_language(report_2042, "en")
        checks.append({"name": "U-2042: Report in English", "passed": lang_ok, "detail": lang_detail})
        max_score += 0.5
        if lang_ok:
            total_score += 0.5

        # Avoidant-specific strategy present
        avoidant_tips = [
            "name your feelings", "name.*feeling", "overwhelmed", "stay present",
            "needing space is valid", "disappearing is hurtful", "vulnerable",
            "intimacy exercise", "I need.*minutes",
        ]
        avoidant_strat_ok = any(re.search(tip, report_2042, re.IGNORECASE) for tip in avoidant_tips)
        checks.append({
            "name": "U-2042: Avoidant-specific strategy content",
            "passed": avoidant_strat_ok,
            "detail": "Found avoidant-specific strategy wording" if avoidant_strat_ok else "Missing avoidant-specific strategy content"
        })
        max_score += 1.0
        if avoidant_strat_ok:
            total_score += 1.0

    # ---- U-2043: 晓薇 — Fearful-Avoidant, Chinese ----
    report_2043 = load_report(reports_dir, "U-2043")

    checks.append({
        "name": "U-2043: Report file exists",
        "passed": report_2043 is not None,
        "detail": "File U-2043_report.txt found" if report_2043 else "File U-2043_report.txt NOT found"
    })
    max_score += 1.0
    if report_2043:
        total_score += 1.0

    if report_2043:
        for name, passed, detail in check_format_sections(report_2043, "zh"):
            checks.append({"name": f"U-2043 Format: {name}", "passed": passed, "detail": detail})
            max_score += 0.5
            if passed:
                total_score += 0.5

        # Must identify as Fearful-Avoidant (the hardest case)
        fa_ok, fa_detail = check_fearful_avoidant(report_2043)
        checks.append({"name": "U-2043: Correct style = Fearful-Avoidant", "passed": fa_ok, "detail": fa_detail})
        max_score += 3.0
        if fa_ok:
            total_score += 3.0

        conf_ok, conf_detail = check_confidence_level(report_2043)
        checks.append({"name": "U-2043: Confidence level present", "passed": conf_ok, "detail": conf_detail})
        max_score += 1.0
        if conf_ok:
            total_score += 1.0

        # CRITICAL: Must be in Chinese
        lang_ok, lang_detail = check_language(report_2043, "zh")
        checks.append({"name": "U-2043: Report in Chinese (language rule)", "passed": lang_ok, "detail": lang_detail})
        max_score += 2.0
        if lang_ok:
            total_score += 2.0

        strat_ok, strat_detail = check_strategies_count(report_2043)
        checks.append({"name": "U-2043: At least 2 strategies", "passed": strat_ok, "detail": strat_detail})
        max_score += 1.0
        if strat_ok:
            total_score += 1.0

        # FA-specific content: hot-cold tracking or therapy recommendation
        fa_specific = [
            "therapy", "治疗", "心理咨询", "hot-cold", "冷热", "trauma", "创伤",
            "predictability", "规律", "routines", "例行", "pull away", "推开",
            "idealization", "理想化", "devaluation",
        ]
        fa_content_ok = any(re.search(kw, report_2043, re.IGNORECASE) for kw in fa_specific)
        checks.append({
            "name": "U-2043: FA-specific content (therapy/hot-cold/trauma)",
            "passed": fa_content_ok,
            "detail": "Found FA-specific recommendation" if fa_content_ok else "Missing FA-specific content (therapy, hot-cold cycles, trauma)"
        })
        max_score += 1.5
        if fa_content_ok:
            total_score += 1.5

        # 📖 Deeper section has content about WHY (childhood/early relationships)
        deeper_idx = report_2043.find("📖")
        if deeper_idx != -1:
            deeper_text = report_2043[deeper_idx:]
            deeper_keywords = ["童年", "早期", "childhood", "early", "成长", "原生", "family", "家庭", "trauma", "创伤"]
            deeper_ok = any(kw in deeper_text for kw in deeper_keywords)
        else:
            deeper_ok = False
        checks.append({
            "name": "U-2043: 📖 Deeper section has childhood/early relationship insight",
            "passed": deeper_ok,
            "detail": "Found childhood/early relationship context in Deeper section" if deeper_ok else "Missing childhood/early relationship insight in 📖 section"
        })
        max_score += 1.0
        if deeper_ok:
            total_score += 1.0

    # Final score
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed and final_score >= 0.75,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()