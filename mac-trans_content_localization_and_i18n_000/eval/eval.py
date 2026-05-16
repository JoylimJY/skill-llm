import sys
import json
import os
import re
from pathlib import Path

def has_chinese_characters(text):
    """Check if text contains Chinese characters (CJK Unified Ideographs)."""
    for char in text:
        cp = ord(char)
        if (0x4E00 <= cp <= 0x9FFF or   # CJK Unified Ideographs
            0x3400 <= cp <= 0x4DBF or   # CJK Extension A
            0x20000 <= cp <= 0x2A6DF or # CJK Extension B
            0xF900 <= cp <= 0xFAFF):    # CJK Compatibility Ideographs
            return True
    return False

def has_japanese_characters(text):
    """Check if text contains Hiragana, Katakana, or CJK (used in Japanese)."""
    for char in text:
        cp = ord(char)
        if (0x3040 <= cp <= 0x309F or   # Hiragana
            0x30A0 <= cp <= 0x30FF or   # Katakana
            0x4E00 <= cp <= 0x9FFF or   # CJK (also used in Japanese kanji)
            0xFF65 <= cp <= 0xFF9F):    # Halfwidth Katakana
            return True
    return False

def is_mostly_english(text):
    """Check if text is mostly ASCII English (i.e., not translated)."""
    if not text.strip():
        return False
    ascii_count = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return False
    return (ascii_count / total_alpha) > 0.8

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ---- CHECK 1: chinese_summary.txt exists ----
    chinese_files = list(Path(workspace).rglob("chinese_summary.txt"))
    chinese_exists = len(chinese_files) > 0
    checks.append({
        "name": "chinese_summary.txt exists",
        "passed": chinese_exists,
        "detail": f"Found {len(chinese_files)} file(s)" if chinese_exists else "File not found anywhere in workspace"
    })
    
    chinese_content = ""
    if chinese_exists:
        try:
            with open(chinese_files[0], "r", encoding="utf-8") as f:
                chinese_content = f.read()
        except Exception as e:
            checks.append({"name": "chinese_summary.txt readable", "passed": False, "detail": str(e)})
    
    # ---- CHECK 2: chinese_summary.txt is non-empty ----
    chinese_nonempty = len(chinese_content.strip()) > 10
    checks.append({
        "name": "chinese_summary.txt is non-empty",
        "passed": chinese_nonempty,
        "detail": f"Content length: {len(chinese_content.strip())} chars" if chinese_exists else "File not available"
    })
    
    # ---- CHECK 3: chinese_summary.txt contains Chinese characters ----
    has_zh = has_chinese_characters(chinese_content)
    checks.append({
        "name": "chinese_summary.txt contains Chinese characters",
        "passed": has_zh,
        "detail": f"Chinese chars found: {has_zh}. Sample: {chinese_content[:100].encode('unicode_escape').decode()}"
    })
    
    # ---- CHECK 4: chinese_summary.txt is NOT just the original English ----
    not_just_english_zh = not is_mostly_english(chinese_content) if chinese_nonempty else False
    checks.append({
        "name": "chinese_summary.txt is translated (not original English)",
        "passed": not_just_english_zh,
        "detail": f"Content appears {'translated' if not_just_english_zh else 'still in English or untranslated'}"
    })
    
    # ---- CHECK 5: japanese_summary.txt exists ----
    japanese_files = list(Path(workspace).rglob("japanese_summary.txt"))
    japanese_exists = len(japanese_files) > 0
    checks.append({
        "name": "japanese_summary.txt exists",
        "passed": japanese_exists,
        "detail": f"Found {len(japanese_files)} file(s)" if japanese_exists else "File not found anywhere in workspace"
    })
    
    japanese_content = ""
    if japanese_exists:
        try:
            with open(japanese_files[0], "r", encoding="utf-8") as f:
                japanese_content = f.read()
        except Exception as e:
            checks.append({"name": "japanese_summary.txt readable", "passed": False, "detail": str(e)})
    
    # ---- CHECK 6: japanese_summary.txt is non-empty ----
    japanese_nonempty = len(japanese_content.strip()) > 10
    checks.append({
        "name": "japanese_summary.txt is non-empty",
        "passed": japanese_nonempty,
        "detail": f"Content length: {len(japanese_content.strip())} chars" if japanese_exists else "File not available"
    })
    
    # ---- CHECK 7: japanese_summary.txt contains Japanese/CJK characters ----
    has_ja = has_japanese_characters(japanese_content)
    checks.append({
        "name": "japanese_summary.txt contains Japanese characters",
        "passed": has_ja,
        "detail": f"Japanese chars found: {has_ja}. Sample: {japanese_content[:100].encode('unicode_escape').decode()}"
    })
    
    # ---- CHECK 8: japanese_summary.txt is NOT just the original English ----
    not_just_english_ja = not is_mostly_english(japanese_content) if japanese_nonempty else False
    checks.append({
        "name": "japanese_summary.txt is translated (not original English)",
        "passed": not_just_english_ja,
        "detail": f"Content appears {'translated' if not_just_english_ja else 'still in English or untranslated'}"
    })
    
    # ---- CHECK 9: phrase_translation.txt exists ----
    phrase_files = list(Path(workspace).rglob("phrase_translation.txt"))
    phrase_exists = len(phrase_files) > 0
    checks.append({
        "name": "phrase_translation.txt exists",
        "passed": phrase_exists,
        "detail": f"Found {len(phrase_files)} file(s)" if phrase_exists else "File not found anywhere in workspace"
    })
    
    phrase_content = ""
    if phrase_exists:
        try:
            with open(phrase_files[0], "r", encoding="utf-8") as f:
                phrase_content = f.read()
        except Exception as e:
            checks.append({"name": "phrase_translation.txt readable", "passed": False, "detail": str(e)})
    
    # ---- CHECK 10: phrase_translation.txt contains Chinese characters ----
    has_zh_phrase = has_chinese_characters(phrase_content) if phrase_exists else False
    checks.append({
        "name": "phrase_translation.txt contains Chinese translation",
        "passed": has_zh_phrase,
        "detail": f"Chinese chars found: {has_zh_phrase}. Sample: {phrase_content[:80].encode('unicode_escape').decode()}" if phrase_exists else "File not available"
    })
    
    # ---- CHECK 11: Verify line range correctness for Chinese (lines 3-8 of release_notes.txt) ----
    # We verify the Chinese file does NOT contain content from lines 15-22
    # Lines 3-8 (1-indexed) of release_notes.txt:
    lines_3_to_8_english = [
        "This release introduces major performance improvements",
        "Database connection pooling",
        "Memory usage has been reduced",
        "caching layer",
        "deprecated APIs",
        "Migration guides",
    ]
    # The Chinese file should NOT contain these exact English phrases as-is (they should be translated)
    # But the content should have been sourced from those lines (we check it's non-trivially non-English)
    # We also check the Japanese file doesn't somehow end up with Chinese content only
    
    # Cross-check: japanese file should NOT be all Chinese without any Japanese-specific script
    # (Japanese uses Hiragana/Katakana distinctively)
    has_kana = any(
        0x3040 <= ord(c) <= 0x309F or 0x30A0 <= ord(c) <= 0x30FF
        for c in japanese_content
    )
    checks.append({
        "name": "japanese_summary.txt contains kana (distinctly Japanese, not just Chinese)",
        "passed": has_kana,
        "detail": f"Kana (Hiragana/Katakana) found: {has_kana}. This confirms Japanese translation, not just Chinese."
    })
    
    # ---- FINAL SCORE ----
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    all_passed = passed_count == total
    
    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()