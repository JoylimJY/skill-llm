import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ---- Load the saved Feishu document ----
doc_json_path = Path(workspace) / "feishu_output" / "latest_doc.json"
doc_md_path = Path(workspace) / "feishu_output" / "latest_doc.md"

raw_content = ""
title_field = ""

try:
    with open(doc_json_path, "r", encoding="utf-8") as f:
        doc_data = json.load(f)
    title_field = doc_data.get("title", "")
    raw_content = doc_data.get("content", "")
    checks.append(make_check(
        "feishu_doc_created",
        True,
        f"Feishu document JSON found at {doc_json_path}. Title: '{title_field}'"
    ))
except Exception as e:
    # Try markdown fallback
    try:
        with open(doc_md_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        checks.append(make_check(
            "feishu_doc_created",
            True,
            f"Feishu document MD found at {doc_md_path}"
        ))
    except Exception as e2:
        checks.append(make_check(
            "feishu_doc_created",
            False,
            f"Neither latest_doc.json nor latest_doc.md found in feishu_output/. Errors: {e}, {e2}"
        ))
        # Cannot continue meaningful checks
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

# Combine title and content for full-text search
full_text = title_field + "\n" + raw_content

# ---- CHECK 1: Top-level header with 🔪 emoji ----
has_breakdown_header = bool(re.search(r'🔪', full_text))
checks.append(make_check(
    "has_breakdown_emoji_header",
    has_breakdown_header,
    "Report must contain '🔪' in the main title (爆文拆解 header)" if not has_breakdown_header else "Found 🔪 header"
))

# ---- CHECK 2: Basic Info section with 📊 ----
has_basic_info = bool(re.search(r'📊', full_text))
checks.append(make_check(
    "has_basic_info_section",
    has_basic_info,
    "Report must contain '📊 基本信息' section" if not has_basic_info else "Found 📊 section"
))

# ---- CHECK 3: Structure Analysis section with 🏗️ ----
has_structure = bool(re.search(r'🏗', full_text))
checks.append(make_check(
    "has_structure_analysis_section",
    has_structure,
    "Report must contain '🏗️ 结构分析' section" if not has_structure else "Found 🏗️ section"
))

# ---- CHECK 4: Structure analysis has all 4 sub-fields ----
structure_fields = ["标题技巧", "开头手法", "段落逻辑", "结尾方式"]
missing_fields = [f for f in structure_fields if f not in full_text]
has_all_structure_fields = len(missing_fields) == 0
checks.append(make_check(
    "structure_has_all_four_fields",
    has_all_structure_fields,
    f"Missing structure sub-fields: {missing_fields}" if missing_fields else "All 4 structure fields present"
))

# ---- CHECK 5: Golden sentences section with ✍️ ----
has_golden = bool(re.search(r'✍', full_text))
checks.append(make_check(
    "has_golden_sentences_section",
    has_golden,
    "Report must contain '✍️ 金句' section" if not has_golden else "Found ✍️ section"
))

# ---- CHECK 6: At least 5 numbered golden sentences ----
# Look for numbered list items that are quotes (numbered 1. through 5+)
golden_lines = re.findall(r'^\s*[5-9][\.\、]|^\s*[1-9][0-9]*[\.\、]', full_text, re.MULTILINE)
# Alternative: count lines that match "数字. " pattern
all_numbered = re.findall(r'^\s*(\d+)[\.、\)]\s+[""「「].+', full_text, re.MULTILINE)
if not all_numbered:
    # Try without quotes marker  
    all_numbered = re.findall(r'^\s*(\d+)[\.、\)]\s+\S.{5,}', full_text, re.MULTILINE)

# Just check if we have at least 5 numbered items in the golden section
# Find the golden section
golden_section_match = re.search(r'[✍️金句].{0,30}([\s\S]*?)(?=##|$)', full_text)
if golden_section_match:
    golden_section = golden_section_match.group(1)
    numbered_in_golden = re.findall(r'^\s*\d+[\.、\)]\s+', golden_section, re.MULTILINE)
    has_min_5_golden = len(numbered_in_golden) >= 5
    golden_count = len(numbered_in_golden)
else:
    # Count all numbered items in full text
    all_num = re.findall(r'^\s*\d+[\.、\)]\s+', full_text, re.MULTILINE)
    has_min_5_golden = len(all_num) >= 5
    golden_count = len(all_num)

checks.append(make_check(
    "has_min_5_golden_sentences",
    has_min_5_golden,
    f"Found approximately {golden_count} numbered items (need ≥5 golden sentences)" if not has_min_5_golden else f"Found {golden_count} numbered items"
))

# ---- CHECK 7: Golden sentence TYPE annotations ----
type_keywords = ["比喻", "对比", "数据", "金句体", "反常识"]
found_types = [t for t in type_keywords if t in full_text]
has_type_annotations = len(found_types) >= 2
checks.append(make_check(
    "has_type_annotations_on_golden_sentences",
    has_type_annotations,
    f"Golden sentences must have type annotations (比喻/对比/数据/金句体/反常识). Found: {found_types}" if not has_type_annotations else f"Found type annotations: {found_types}"
))

# ---- CHECK 8: Topic Logic section with 🎯 ----
has_topic = bool(re.search(r'🎯', full_text))
checks.append(make_check(
    "has_topic_logic_section",
    has_topic,
    "Report must contain '🎯 选题逻辑' section" if not has_topic else "Found 🎯 section"
))

# ---- CHECK 9: Topic Logic has emotion curve (情绪曲线) ----
has_emotion_curve = "情绪曲线" in full_text
checks.append(make_check(
    "has_emotion_curve",
    has_emotion_curve,
    "Topic logic section must contain '情绪曲线' field" if not has_emotion_curve else "Found 情绪曲线"
))

# ---- CHECK 10: Replication Suggestions section with 💡 ----
has_replicate = bool(re.search(r'💡', full_text))
checks.append(make_check(
    "has_replication_suggestions_section",
    has_replicate,
    "Report must contain '💡 复刻建议' section" if not has_replicate else "Found 💡 section"
))

# ---- CHECK 11: Replication has required sub-fields ----
replicate_fields = ["标题复刻", "开头复刻", "结构复刻", "金句改编"]
missing_rep = [f for f in replicate_fields if f not in full_text]
has_all_replicate = len(missing_rep) == 0
checks.append(make_check(
    "replication_has_all_subfields",
    has_all_replicate,
    f"Missing replication sub-fields: {missing_rep}" if missing_rep else "All 4 replication sub-fields present"
))

# ---- CHECK 12: Article content actually used (key article phrases present) ----
article_references = [
    "月薪", "年薪", "逆袭", "职场", "产品"
]
found_refs = [r for r in article_references if r in full_text]
content_used = len(found_refs) >= 3
checks.append(make_check(
    "article_content_actually_analyzed",
    content_used,
    f"Report does not reference the actual article content. Found only: {found_refs}" if not content_used else f"Report references article content: {found_refs}"
))

# ---- CHECK 13: feishu_doc used with create subcommand (check if doc exists AND has meaningful content) ----
content_length = len(raw_content.strip())
meaningful_content = content_length > 500
checks.append(make_check(
    "feishu_doc_has_substantial_content",
    meaningful_content,
    f"Feishu doc content too short ({content_length} chars). Expected substantial analysis (>500 chars)" if not meaningful_content else f"Content length: {content_length} chars"
))

# ---- Compute score ----
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