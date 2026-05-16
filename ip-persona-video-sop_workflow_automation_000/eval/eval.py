import sys
import json
import re
import os
from pathlib import Path

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def count_chinese_chars(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')

def longest_subtitle_line(text):
    """Find lines marked as subtitles or all lines in subtitle blocks."""
    # We look for lines that appear to be subtitle text (not headers, not blank)
    lines = text.split('\n')
    max_len = 0
    max_line = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip markdown headers
        if stripped.startswith('#'):
            continue
        # Skip lines that are clearly metadata (contain colons followed by dates/numbers)
        if re.match(r'^[\w\s]+[:：]\s*\d', stripped):
            continue
        cn_count = count_chinese_chars(stripped)
        # Only check lines that are predominantly Chinese (subtitle-like)
        if cn_count > 0 and cn_count / max(len(stripped), 1) > 0.4:
            if cn_count > max_len:
                max_len = cn_count
                max_line = stripped
    return max_len, max_line

def check_no_line_breaks_in_subtitles(text):
    """Check that subtitle lines don't have forced line breaks within a single subtitle."""
    # Looking for patterns like: text\nmore_text where it's mid-sentence
    # In the script, subtitles should be on single lines without mid-sentence breaks
    # We check: no line has both Chinese content and ends mid-sentence continuing to next line
    # Simplified: check that no adjacent content lines form a broken subtitle pair
    # (i.e., the SOP says 不要换行 for subtitles)
    lines = text.split('\n')
    violations = []
    for i, line in enumerate(lines[:-1]):
        stripped = line.strip()
        next_stripped = lines[i+1].strip()
        # If current line ends without punctuation and next line starts with Chinese mid-sentence
        cn_current = count_chinese_chars(stripped)
        cn_next = count_chinese_chars(next_stripped)
        if cn_current >= 3 and cn_next >= 3:
            # Check if it looks like a broken sentence (no end punctuation on current)
            if stripped and not stripped[-1] in '。！？…,，、：；""''）】':
                if next_stripped and '\u4e00' <= next_stripped[0] <= '\u9fff':
                    violations.append(f"可能换行违规: '{stripped}' / '{next_stripped}'")
    return violations

def sentences_in_block(block):
    """Count sentences in a paragraph block."""
    # Split by Chinese sentence-ending punctuation
    sentences = re.split(r'[。！？…]+', block)
    sentences = [s.strip() for s in sentences if s.strip() and count_chinese_chars(s.strip()) > 0]
    return sentences

workspace = sys.argv[1]
checks = []
total_score = 0.0

# ── Check 1: persona_profile.json exists ─────────────────────────────────────
profile_file = find_file(workspace, "persona_profile.json")
profile_exists = profile_file is not None
checks.append({
    "name": "persona_profile.json exists",
    "passed": profile_exists,
    "detail": str(profile_file) if profile_exists else "File not found anywhere in workspace"
})

profile_data = {}
if profile_exists:
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
    except Exception as e:
        checks.append({
            "name": "persona_profile.json is valid JSON",
            "passed": False,
            "detail": str(e)
        })
        profile_data = {}

# ── Check 2: Persona tags (3-5 keywords) ─────────────────────────────────────
try:
    tags = profile_data.get("tags", profile_data.get("人设标签", profile_data.get("persona_tags", [])))
    tags_count_ok = isinstance(tags, list) and 3 <= len(tags) <= 5
    checks.append({
        "name": "Persona tags: exactly 3-5 keywords",
        "passed": tags_count_ok,
        "detail": f"Found {len(tags) if isinstance(tags, list) else 'N/A'} tags: {tags}"
    })
    if tags_count_ok:
        total_score += 1.0
except Exception as e:
    checks.append({"name": "Persona tags: exactly 3-5 keywords", "passed": False, "detail": str(e)})

# ── Check 3: Exactly 15 topic ideas ──────────────────────────────────────────
try:
    topics = profile_data.get("topics", profile_data.get("选题", profile_data.get("topic_list", [])))
    topics_count_ok = isinstance(topics, list) and len(topics) == 15
    checks.append({
        "name": "Topic list has exactly 15 items",
        "passed": topics_count_ok,
        "detail": f"Found {len(topics) if isinstance(topics, list) else 'N/A'} topics"
    })
    if topics_count_ok:
        total_score += 1.0
except Exception as e:
    checks.append({"name": "Topic list has exactly 15 items", "passed": False, "detail": str(e)})

# ── Check 4: Gold sentences (金句) in profile ─────────────────────────────────
try:
    gold_sentences = profile_data.get(
        "gold_sentences",
        profile_data.get("金句", profile_data.get("core_sentences", []))
    )
    gold_ok = isinstance(gold_sentences, list) and 3 <= len(gold_sentences) <= 5
    checks.append({
        "name": "Gold sentences (金句): 3-5 items in profile",
        "passed": gold_ok,
        "detail": f"Found {len(gold_sentences) if isinstance(gold_sentences, list) else 'N/A'} gold sentences: {gold_sentences}"
    })
    if gold_ok:
        total_score += 0.5
except Exception as e:
    checks.append({"name": "Gold sentences (金句): 3-5 items in profile", "passed": False, "detail": str(e)})

# ── Check 5: Core value present ──────────────────────────────────────────────
try:
    core_value = profile_data.get(
        "core_value",
        profile_data.get("核心价值观", profile_data.get("value", ""))
    )
    core_value_ok = isinstance(core_value, str) and len(core_value) > 5
    checks.append({
        "name": "Core value (核心价值观) is present",
        "passed": core_value_ok,
        "detail": f"core_value = '{core_value}'"
    })
    if core_value_ok:
        total_score += 0.5
except Exception as e:
    checks.append({"name": "Core value present", "passed": False, "detail": str(e)})

# ── Check 6: shooting_script.md exists ───────────────────────────────────────
script_file = find_file(workspace, "shooting_script.md")
script_exists = script_file is not None
checks.append({
    "name": "shooting_script.md exists",
    "passed": script_exists,
    "detail": str(script_file) if script_exists else "File not found anywhere in workspace"
})

script_text = ""
if script_exists:
    try:
        with open(script_file, 'r', encoding='utf-8') as f:
            script_text = f.read()
    except Exception as e:
        checks.append({"name": "shooting_script.md is readable", "passed": False, "detail": str(e)})

# ── Check 7: Gold sentences appear ≥3 times each in script ───────────────────
if script_text and gold_sentences and isinstance(gold_sentences, list) and len(gold_sentences) > 0:
    try:
        all_gold_repeated = True
        gold_detail = []
        for gs in gold_sentences:
            if not isinstance(gs, str) or len(gs) < 4:
                continue
            # Count occurrences (partial match ok for slight paraphrasing, but core phrase must appear)
            # Use key phrase (first 8 chars if long)
            key = gs[:min(len(gs), 10)]
            count = script_text.count(key)
            ok = count >= 3
            gold_detail.append(f"'{key}' appears {count} times (need ≥3): {'✓' if ok else '✗'}")
            if not ok:
                all_gold_repeated = False
        checks.append({
            "name": "Each gold sentence appears ≥3 times in script",
            "passed": all_gold_repeated,
            "detail": "; ".join(gold_detail)
        })
        if all_gold_repeated:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "Gold sentences repeat check", "passed": False, "detail": str(e)})
else:
    checks.append({
        "name": "Each gold sentence appears ≥3 times in script",
        "passed": False,
        "detail": "Cannot check: either script or gold_sentences missing/empty"
    })

# ── Check 8: Emotional curve 7-stage structure present ───────────────────────
try:
    # The SOP mandates: 开场(高光)→回忆(低谷)→转折→奋斗/困难→突破/领悟→结果(逆袭)→升华(价值观)
    required_stages = ["开场", "回忆", "转折", "突破", "逆袭", "升华"]
    stages_found = []
    stages_missing = []
    for stage in required_stages:
        if stage in script_text:
            stages_found.append(stage)
        else:
            stages_missing.append(stage)
    
    stages_ok = len(stages_found) >= 5  # at least 5 of 6 must appear
    checks.append({
        "name": "Emotional curve 7-stage structure (≥5 of 6 key stages present)",
        "passed": stages_ok,
        "detail": f"Found: {stages_found}; Missing: {stages_missing}"
    })
    if stages_ok:
        total_score += 1.0
except Exception as e:
    checks.append({"name": "Emotional curve structure", "passed": False, "detail": str(e)})

# ── Check 9: Paragraph blocks ≤3 sentences ───────────────────────────────────
try:
    # Split script into paragraph blocks (separated by blank lines)
    paragraphs = re.split(r'\n\s*\n', script_text)
    long_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if not para or para.startswith('#'):
            continue
        if count_chinese_chars(para) < 10:
            continue
        sents = sentences_in_block(para)
        if len(sents) > 3:
            long_paragraphs.append(f"'{para[:50]}...' has {len(sents)} sentences")
    
    para_ok = len(long_paragraphs) == 0
    checks.append({
        "name": "All paragraph blocks have ≤3 sentences",
        "passed": para_ok,
        "detail": f"Violations: {long_paragraphs[:3]}" if long_paragraphs else "All blocks ≤3 sentences ✓"
    })
    if para_ok:
        total_score += 1.5
except Exception as e:
    checks.append({"name": "Paragraph ≤3 sentences", "passed": False, "detail": str(e)})

# ── Check 10: Subtitle lines ≤10 Chinese characters ─────────────────────────
try:
    max_cn_len, offending_line = longest_subtitle_line(script_text)
    subtitle_ok = max_cn_len <= 10
    checks.append({
        "name": "All content lines ≤10 Chinese characters (subtitle constraint)",
        "passed": subtitle_ok,
        "detail": f"Longest Chinese line has {max_cn_len} chars: '{offending_line}'" if not subtitle_ok else f"Max line length: {max_cn_len} chars ✓"
    })
    if subtitle_ok:
        total_score += 1.5
except Exception as e:
    checks.append({"name": "Subtitle line length ≤10 chars", "passed": False, "detail": str(e)})

# ── Check 11: Script uses colloquial language from interview ─────────────────
try:
    # Check that specific colloquial phrases from the interview appear in the script
    colloquial_markers = [
        "身体有它自己的语言",
        "中医是唯一听得懂",
        "只要我真的在帮人",
        "普通人都应该有机会",
    ]
    found_markers = [m for m in colloquial_markers if m in script_text]
    colloquial_ok = len(found_markers) >= 2
    checks.append({
        "name": "Script uses IP's original colloquial phrases from interview (≥2 of 4 key phrases)",
        "passed": colloquial_ok,
        "detail": f"Found {len(found_markers)}/4 markers: {found_markers}"
    })
    if colloquial_ok:
        total_score += 1.0
except Exception as e:
    checks.append({"name": "Colloquial language check", "passed": False, "detail": str(e)})

# ── Check 12: Script is substantial (not trivially short) ────────────────────
try:
    cn_char_count = count_chinese_chars(script_text)
    substantial_ok = cn_char_count >= 800
    checks.append({
        "name": "Script is substantial (≥800 Chinese characters)",
        "passed": substantial_ok,
        "detail": f"Script contains {cn_char_count} Chinese characters"
    })
    if substantial_ok:
        total_score += 0.5
except Exception as e:
    checks.append({"name": "Script length", "passed": False, "detail": str(e)})

# ── Final scoring ─────────────────────────────────────────────────────────────
max_score = 11.0
normalized_score = min(1.0, total_score / max_score)

# Must pass critical checks to pass overall
critical_checks = [
    "persona_profile.json exists",
    "shooting_script.md exists",
    "Topic list has exactly 15 items",
    "Each gold sentence appears ≥3 times in script",
]
critical_passed = all(
    c["passed"] for c in checks if c["name"] in critical_checks
)

overall_passed = critical_passed and normalized_score >= 0.55

result = {
    "passed": overall_passed,
    "score": round(normalized_score, 3),
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))