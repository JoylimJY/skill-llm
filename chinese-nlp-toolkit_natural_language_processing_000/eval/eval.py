import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Find the analysis report file anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("review_analysis_report.json"))
    if not candidates:
        return None, "File 'review_analysis_report.json' not found anywhere in workspace."
    return candidates[0], None

def check_output_format(data):
    """Each review entry must have the required Chinese-labeled fields."""
    required_fields_patterns = [
        (r"原文", "原文"),
        (r"分词", "分词"),
        (r"关键词", "关键词"),
        (r"情感", "情感"),
        (r"摘要", "摘要"),
        (r"可读性", "可读性"),
    ]
    checks = []
    
    if not isinstance(data, list):
        return [{"name": "output_is_list", "passed": False, "detail": "Root element must be a JSON list of review analyses."}]
    
    checks.append({"name": "output_is_list", "passed": True, "detail": f"Found list with {len(data)} entries."})
    
    if len(data) < 5:
        checks.append({"name": "all_five_reviews_present", "passed": False, "detail": f"Expected 5 reviews, found {len(data)}."})
    else:
        checks.append({"name": "all_five_reviews_present", "passed": True, "detail": "All 5 reviews present."})
    
    # Check first entry has the required Chinese field labels
    if data:
        entry = data[0]
        entry_str = json.dumps(entry, ensure_ascii=False)
        missing = []
        for pattern, label in required_fields_patterns:
            if not re.search(pattern, entry_str):
                missing.append(label)
        if missing:
            checks.append({"name": "chinese_field_labels", "passed": False, "detail": f"Missing required Chinese field labels: {missing}. Fields must be labeled: 原文, 分词, 关键词, 情感, 摘要, 可读性"})
        else:
            checks.append({"name": "chinese_field_labels", "passed": True, "detail": "All required Chinese field labels present."})
    
    return checks

def check_r001_sarcasm(data):
    """R001: 厉害了 + 🙄🙄🙄 + 也是醉了 → must be NEGATIVE sentiment, not positive."""
    checks = []
    r001 = None
    for entry in data:
        entry_str = json.dumps(entry, ensure_ascii=False)
        if "R001" in entry_str or "厉害了" in entry_str:
            r001 = entry
            break
    
    if r001 is None:
        checks.append({"name": "r001_found", "passed": False, "detail": "Could not locate R001 analysis in output."})
        return checks
    
    checks.append({"name": "r001_found", "passed": True, "detail": "R001 analysis located."})
    
    entry_str = json.dumps(r001, ensure_ascii=False).lower()
    
    # Must detect negative sentiment (not positive)
    negative_indicators = ["负面", "negative", "强烈负面", "偏负面", "负向"]
    positive_indicators = ["正面", "positive", "偏正面", "强烈正面", "满意"]
    
    has_negative = any(ind in entry_str for ind in negative_indicators)
    has_positive_only = any(ind in entry_str for ind in positive_indicators) and not has_negative
    
    if has_negative:
        checks.append({"name": "r001_sarcasm_detected_negative", "passed": True, "detail": "R001 correctly classified as negative despite surface-level positive words (sarcasm detected via 厉害了/也是醉了/🙄🙄🙄)."})
    elif has_positive_only:
        checks.append({"name": "r001_sarcasm_detected_negative", "passed": False, "detail": "R001 incorrectly classified as positive — agent failed to detect sarcasm markers (厉害了, 也是醉了, 🙄🙄🙄 triple repetition = disdain)."})
    else:
        checks.append({"name": "r001_sarcasm_detected_negative", "passed": False, "detail": f"R001 sentiment classification unclear or missing. Entry: {entry_str[:300]}"})
    
    # Check that sarcasm signals are identified
    sarcasm_signals = ["厉害了", "也是醉了", "🙄", "讽刺", "sarcas", "反讽"]
    has_signal_mention = any(sig in json.dumps(r001, ensure_ascii=False) for sig in sarcasm_signals)
    if has_signal_mention:
        checks.append({"name": "r001_sarcasm_signals_reported", "passed": True, "detail": "Sarcasm signals mentioned in analysis."})
    else:
        checks.append({"name": "r001_sarcasm_signals_reported", "passed": False, "detail": "Sarcasm signals (厉害了, 也是醉了, 🙄🙄🙄) not mentioned in the analysis signal field."})
    
    return checks

def check_r002_positive_classical(data):
    """R002: Classical Chinese elements + positive emoji → strongly positive, higher readability."""
    checks = []
    r002 = None
    for entry in data:
        entry_str = json.dumps(entry, ensure_ascii=False)
        if "R002" in entry_str or "此物件" in entry_str or "做工精良" in entry_str:
            r002 = entry
            break
    
    if r002 is None:
        checks.append({"name": "r002_found", "passed": False, "detail": "Could not locate R002 analysis."})
        return checks
    checks.append({"name": "r002_found", "passed": True, "detail": "R002 analysis located."})
    
    entry_str = json.dumps(r002, ensure_ascii=False)
    
    # Sentiment must be positive
    positive_indicators = ["正面", "positive", "偏正面", "强烈正面"]
    has_positive = any(ind in entry_str for ind in positive_indicators)
    checks.append({"name": "r002_positive_sentiment", "passed": has_positive,
                   "detail": "R002 correctly identified as positive." if has_positive else "R002 sentiment not identified as positive."})
    
    # Readability should be >= 4 (classical Chinese elements increase difficulty)
    readability_match = re.search(r'[4-9](?:\s*[/／]\s*10|\s*分)', entry_str)
    # Also check for numeric scores as standalone
    score_match = re.search(r'\b([4-9])\b', entry_str)
    has_high_readability = readability_match is not None or score_match is not None
    
    # Try extracting actual score more carefully
    score_numbers = re.findall(r'\b(\d+)\b', entry_str)
    score_in_range = any(4 <= int(n) <= 10 for n in score_numbers if n.isdigit())
    
    checks.append({"name": "r002_readability_moderate_or_higher", "passed": score_in_range,
                   "detail": "R002 readability score >= 4 (classical Chinese elements elevate difficulty)." if score_in_range else f"R002 readability score expected >= 4 due to classical Chinese style. Scores found: {score_numbers[:5]}"})
    
    return checks

def check_r003_slang_expansion(data):
    """R003: 'yyds' must be recognized as internet slang and expanded, mixed language handled."""
    checks = []
    r003 = None
    for entry in data:
        entry_str = json.dumps(entry, ensure_ascii=False)
        if "R003" in entry_str or "yyds" in entry_str.lower() or "永远的神" in entry_str:
            r003 = entry
            break
    
    if r003 is None:
        checks.append({"name": "r003_found", "passed": False, "detail": "Could not locate R003 analysis (yyds review)."})
        return checks
    checks.append({"name": "r003_found", "passed": True, "detail": "R003 analysis located."})
    
    entry_str = json.dumps(r003, ensure_ascii=False)
    
    # yyds should be expanded to 永远的神 or at least recognized
    slang_expansion = "永远的神" in entry_str or "yyds" in entry_str.lower()
    checks.append({"name": "r003_yyds_recognized", "passed": slang_expansion,
                   "detail": "yyds recognized as internet slang (永远的神)." if slang_expansion else "yyds not recognized or expanded — agent missed internet slang handling requirement."})
    
    # Mixed language should be noted
    mixed_lang_indicators = ["混合", "中英", "mixed", "english", "英文", "code-switching", "代码切换", "bug", "nice", "feature"]
    has_mixed = any(ind in entry_str.lower() for ind in mixed_lang_indicators)
    checks.append({"name": "r003_mixed_language_handled", "passed": has_mixed,
                   "detail": "Mixed-language text (中英混合) handled appropriately." if has_mixed else "Mixed-language text not noted — 'bug', 'nice', 'feature' are English words that should not be force-segmented as Chinese."})
    
    return checks

def check_r004_rhetorical_sarcasm(data):
    """R004: Rhetorical questions + 呵呵 + 你开心就好 + negative emoji → negative sentiment."""
    checks = []
    r004 = None
    for entry in data:
        entry_str = json.dumps(entry, ensure_ascii=False)
        if "R004" in entry_str or "呵呵" in entry_str or "你开心就好" in entry_str:
            r004 = entry
            break
    
    if r004 is None:
        checks.append({"name": "r004_found", "passed": False, "detail": "Could not locate R004 analysis."})
        return checks
    checks.append({"name": "r004_found", "passed": True, "detail": "R004 analysis located."})
    
    entry_str = json.dumps(r004, ensure_ascii=False)
    
    negative_indicators = ["负面", "negative", "强烈负面", "偏负面"]
    has_negative = any(ind in entry_str for ind in negative_indicators)
    checks.append({"name": "r004_negative_sentiment", "passed": has_negative,
                   "detail": "R004 correctly classified as negative (rhetorical questions + 呵呵 + negative emoji)." if has_negative else "R004 not classified as negative — agent missed rhetorical question sarcasm and 呵呵/你开心就好 signals."})
    
    # Negative emoji should be mentioned
    emoji_indicators = ["😤", "👎", "负面", "emoji", "表情"]
    has_emoji_mention = any(ind in entry_str for ind in emoji_indicators)
    checks.append({"name": "r004_negative_emoji_noted", "passed": has_emoji_mention,
                   "detail": "Negative emoji (😤👎) noted as sentiment amplifier." if has_emoji_mention else "Negative emoji (😤👎) not noted — SKILL.md requires emoji contribution tracking."})
    
    return checks

def check_r005_readability_high(data):
    """R005: Technical jargon + long sentences → readability score 7-10."""
    checks = []
    r005 = None
    for entry in data:
        entry_str = json.dumps(entry, ensure_ascii=False)
        if "R005" in entry_str or "纳米复合材料" in entry_str or "ISO9001" in entry_str:
            r005 = entry
            break
    
    if r005 is None:
        checks.append({"name": "r005_found", "passed": False, "detail": "Could not locate R005 analysis."})
        return checks
    checks.append({"name": "r005_found", "passed": True, "detail": "R005 analysis located."})
    
    entry_str = json.dumps(r005, ensure_ascii=False)
    
    # Readability should be 7-10 (domain experts / academic specialists)
    score_numbers = re.findall(r'\b(\d+)\b', entry_str)
    high_score = any(7 <= int(n) <= 10 for n in score_numbers if n.isdigit())
    checks.append({"name": "r005_high_readability_score", "passed": high_score,
                   "detail": "R005 readability score 7-10 (technical jargon + ISO/domain terminology)." if high_score else f"R005 readability expected 7-10 (highly technical text). Scores found: {score_numbers[:10]}"})
    
    # Keywords should include technical terms
    technical_terms = ["纳米", "ISO", "认证", "复合材料", "聚合物", "航空", "航天", "制造", "生物", "医疗"]
    entry_keywords_section = entry_str
    has_technical_keywords = sum(1 for t in technical_terms if t in entry_keywords_section) >= 3
    checks.append({"name": "r005_technical_keywords_extracted", "passed": has_technical_keywords,
                   "detail": f"Technical keywords correctly extracted from R005." if has_technical_keywords else f"Technical keywords from R005 not sufficiently represented. Expected terms like 纳米/ISO/认证/复合材料."})
    
    return checks

def check_segmentation_present(data):
    """All entries must have segmentation with / separators."""
    checks = []
    seg_present = 0
    total = len(data)
    
    for entry in data:
        entry_str = json.dumps(entry, ensure_ascii=False)
        # Look for 分词 field with slash separators
        if "分词" in entry_str and "/" in entry_str:
            seg_present += 1
    
    ratio = seg_present / total if total > 0 else 0
    passed = ratio >= 0.8
    checks.append({"name": "segmentation_with_slash_separators", "passed": passed,
                   "detail": f"{seg_present}/{total} entries have segmentation with '/' separators." })
    return checks

def check_summary_in_traditional_or_annotated(data):
    """At least one review's summary should show traditional Chinese conversion or pinyin annotation per the workflow requirement."""
    checks = []
    # Check if any entry contains Traditional Chinese characters (common ones)
    # Traditional markers: 體 (体), 產 (产), 電 (电), 質 (质), 發 (发), 這 (这), 為 (为)
    trad_chars = ["體", "產", "電", "質", "發", "這", "為", "說", "認", "數", "時", "會", "來", "國"]
    all_text = json.dumps(data, ensure_ascii=False)
    
    has_traditional = any(c in all_text for c in trad_chars)
    # Also check for pinyin annotation (tone marks)
    pinyin_pattern = re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', all_text)
    has_pinyin = pinyin_pattern is not None
    
    passed = has_traditional or has_pinyin
    checks.append({"name": "traditional_or_pinyin_in_output", "passed": passed,
                   "detail": "Traditional Chinese characters or pinyin annotation found in output (format conversion applied)." if passed else "No Traditional Chinese characters or pinyin annotation found — SKILL.md requires format conversion capability be exercised."})
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    overall_passed = True
    
    # Step 1: Find the report
    report_path, err = find_report(workspace)
    if err:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_found", "passed": False, "detail": err}]
        }
        print(json.dumps(result))
        return
    
    all_checks.append({"name": "report_file_found", "passed": True, "detail": f"Found at {report_path}"})
    
    # Step 2: Parse JSON
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks + [{"name": "report_json_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
        print(json.dumps(result))
        return
    
    all_checks.append({"name": "report_json_parseable", "passed": True, "detail": "Valid JSON."})
    
    # Step 3: Run all checks
    try:
        all_checks.extend(check_output_format(data))
    except Exception as e:
        all_checks.append({"name": "output_format_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_r001_sarcasm(data))
    except Exception as e:
        all_checks.append({"name": "r001_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_r002_positive_classical(data))
    except Exception as e:
        all_checks.append({"name": "r002_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_r003_slang_expansion(data))
    except Exception as e:
        all_checks.append({"name": "r003_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_r004_rhetorical_sarcasm(data))
    except Exception as e:
        all_checks.append({"name": "r004_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_r005_readability_high(data))
    except Exception as e:
        all_checks.append({"name": "r005_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_segmentation_present(data))
    except Exception as e:
        all_checks.append({"name": "segmentation_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_summary_in_traditional_or_annotated(data))
    except Exception as e:
        all_checks.append({"name": "traditional_check_error", "passed": False, "detail": str(e)})
    
    # Scoring
    passed_checks = [c for c in all_checks if c["passed"]]
    score = len(passed_checks) / len(all_checks) if all_checks else 0.0
    overall_passed = score >= 0.70
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()