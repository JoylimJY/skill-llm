import os
import sys
import json
import re
from pathlib import Path

def count_sentences(text):
    # 鲁棒的句子计数：匹配以 .!? 结尾的片段，或至少包含一段文字
    text = text.strip()
    if not text:
        return 0
    # 匹配结尾标点符号加上空格或字符串结尾
    sentences = re.findall(r'[^.!?]+[.!?]?(?=\s|$)', text)
    return max(len(sentences), 1 if text else 0)

def has_metrics(text):
    # 检查数字、百分比、时间（10 minutes）、日期等硬指标
    # 排除标题中的年份日期，只看内容段落
    metrics_patterns = [
        r'\d+%',             # 15%
        r'\d+\s?min',        # 8 minutes
        r'\d+\s?sec',
        r'\d+-\d+',          # 10-8
        r'(increased|reduced|cut|improved) by \d+',
        r'\$\d+',            # 金额
        r'\b\d{1,3}(\.\d+)?\b' # 独立的数字
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in metrics_patterns)

def main(workspace_path):
    checks = []
    workspace = Path(workspace_path)
    file_path = workspace / 'platform_engineering_3p_update.md'
    
    if not file_path.exists():
        return {"passed": False, "score": 0.0, "detail": "File not found"}

    lines = [l.strip() for l in file_path.read_text().splitlines() if l.strip()]
    
    # Check 1: Content length
    checks.append({"name": "content_length", "passed": len(lines) >= 4})

    # Check 2: Title and Emoji
    title = lines[0] if lines else ""
    has_emoji = any(ord(c) > 127 for c in title[:2]) # 简单判断起始是否有非ASCII字符(Emoji)
    checks.append({"name": "emoji_at_start", "passed": has_emoji})
    checks.append({"name": "title_team_and_date", "passed": "Platform Engineering" in title and "2024-05" in title})

    # 提取各部分内容
    content_map = {}
    current_key = None
    for line in lines:
        if line.startswith("Progress:"): content_map["Progress"] = line.replace("Progress:", "").strip()
        elif line.startswith("Plans:"): content_map["Plans"] = line.replace("Plans:", "").strip()
        elif line.startswith("Problems:"): content_map["Problems"] = line.replace("Problems:", "").strip()

    sections = ["Progress", "Plans", "Problems"]
    for section in sections:
        text = content_map.get(section, "")
        
        # 句子数量检查 (要求 1-3 句)
        s_count = count_sentences(text)
        passed_count = 1 <= s_count <= 3
        checks.append({"name": f"{section.lower()}_sentence_count", "passed": passed_count, "detail": f"{section} has {s_count} sentences"})

        # 指标检查 (Progress 和 Plans 通常需要数据驱动)
        if section in ["Progress", "Plans"]:
            passed_metrics = has_metrics(text)
            checks.append({"name": f"{section.lower()}_has_metrics", "passed": passed_metrics, "detail": f"{section} metrics check"})
        else:
            # Problems 只要有内容即可
            checks.append({"name": f"section_{section.lower()}_exists", "passed": len(text) > 5})

    score = sum(1 for c in checks if c['passed']) / len(checks)
    return {"passed": score >= 0.9, "score": round(score, 2), "checks": checks}

if __name__ == '__main__':
    # 语法检查: python3 -m py_compile eval.py
    result = main(sys.argv[1])
    print(json.dumps(result))