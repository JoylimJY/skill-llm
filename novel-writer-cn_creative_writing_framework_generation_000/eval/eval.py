import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output file ---
    target_files = list(workspace.rglob("novel_framework_007.md"))
    
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "novel_framework_007.md not found anywhere in workspace"}]
        }
    
    target_file = target_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_file}"})

    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    # --- CHECK 1: Top-level title contains 创作框架 ---
    has_main_title = bool(re.search(r'^#\s+.+创作框架', content, re.MULTILINE))
    checks.append({
        "name": "main_title_with_框架",
        "passed": has_main_title,
        "detail": "Top-level H1 heading must contain '创作框架'"
    })

    # --- CHECK 2: Section 一 - 作品概述 present ---
    has_section1 = bool(re.search(r'##\s+一[、.．,，]\s*作品概述', content))
    checks.append({
        "name": "section_1_作品概述",
        "passed": has_section1,
        "detail": "Must have '## 一、作品概述' (or similar numbering) section"
    })

    # --- CHECK 3: Section 二 - 人物设定 with subsections 2.1 主角, 2.2 核心配角, 2.3 反派 ---
    has_section2 = bool(re.search(r'##\s+二[、.．,，]\s*人物设定', content))
    has_sub21 = bool(re.search(r'###\s+2[\s.．]*[.．]\s*1\s*.*主角', content))
    has_sub22 = bool(re.search(r'###\s+2[\s.．]*[.．]\s*2\s*.*配角', content))
    has_sub23 = bool(re.search(r'###\s+2[\s.．]*[.．]\s*3\s*.*反派', content))

    checks.append({
        "name": "section_2_人物设定",
        "passed": has_section2,
        "detail": "Must have '## 二、人物设定' section"
    })
    checks.append({
        "name": "subsection_2.1_主角",
        "passed": has_sub21,
        "detail": "Must have '### 2.1 主角' subsection"
    })
    checks.append({
        "name": "subsection_2.2_核心配角",
        "passed": has_sub22,
        "detail": "Must have '### 2.2 核心配角' subsection"
    })
    checks.append({
        "name": "subsection_2.3_反派",
        "passed": has_sub23,
        "detail": "Must have '### 2.3 反派/对立角色' subsection"
    })

    # --- CHECK 4: Section 三 - 人物关系图 with proper 4-column table ---
    has_section3 = bool(re.search(r'##\s+三[、.．,，]\s*人物关系', content))
    checks.append({
        "name": "section_3_人物关系图",
        "passed": has_section3,
        "detail": "Must have '## 三、人物关系图' section"
    })

    # Check for 4-column markdown table with correct Chinese headers
    # Expected: | 角色A | 关系类型 | 角色B | 关系描述 |
    has_table_header = bool(re.search(
        r'\|\s*角色A?\s*\|\s*关系类型\s*\|\s*角色B?\s*\|\s*关系描述\s*\|',
        content
    ))
    checks.append({
        "name": "relationship_table_4col_headers",
        "passed": has_table_header,
        "detail": "Relationship table must have 4 columns: 角色A | 关系类型 | 角色B | 关系描述"
    })

    # Check table has at least 2 data rows (beyond header and separator)
    table_rows = re.findall(r'^\|[^|\n]+\|[^|\n]+\|[^|\n]+\|[^|\n]+\|', content, re.MULTILINE)
    # Filter out separator rows (---) and header rows
    data_rows = [r for r in table_rows if not re.search(r'[-:]{3,}', r) and '角色' not in r]
    has_sufficient_table_data = len(data_rows) >= 2
    checks.append({
        "name": "relationship_table_has_data_rows",
        "passed": has_sufficient_table_data,
        "detail": f"Relationship table must have at least 2 data rows. Found: {len(data_rows)}"
    })

    # --- CHECK 5: Section 四 - 剧情发展 with 3 acts ---
    has_section4 = bool(re.search(r'##\s+四[、.．,，]\s*剧情发展', content))
    has_act1 = bool(re.search(r'###\s+4[\s.．]*[.．]\s*1\s*.*[铺垫|第一幕]', content))
    has_act2 = bool(re.search(r'###\s+4[\s.．]*[.．]\s*2\s*.*[对抗|第二幕]', content))
    has_act3 = bool(re.search(r'###\s+4[\s.．]*[.．]\s*3\s*.*[解决|第三幕]', content))

    checks.append({
        "name": "section_4_剧情发展",
        "passed": has_section4,
        "detail": "Must have '## 四、剧情发展' section"
    })
    checks.append({
        "name": "three_act_structure_4.1_4.2_4.3",
        "passed": has_act1 and has_act2 and has_act3,
        "detail": f"Must have subsections 4.1 (铺垫), 4.2 (对抗), 4.3 (解决). Found: 4.1={has_act1}, 4.2={has_act2}, 4.3={has_act3}"
    })

    # --- CHECK 6: Section 五 - 多版本结局 with ALL FOUR endings ---
    has_section5 = bool(re.search(r'##\s+五[、.．,，]\s*多版本结局', content))
    checks.append({
        "name": "section_5_多版本结局",
        "passed": has_section5,
        "detail": "Must have '## 五、多版本结局' section"
    })

    # All 4 endings must be present
    has_ending_a = bool(re.search(r'###\s+结局\s*A[：:\s]', content))
    has_ending_b = bool(re.search(r'###\s+结局\s*B[：:\s]', content))
    has_ending_c = bool(re.search(r'###\s+结局\s*C[：:\s]', content))
    has_ending_d = bool(re.search(r'###\s+结局\s*D[：:\s]', content))

    checks.append({
        "name": "all_four_endings_A_B_C_D",
        "passed": has_ending_a and has_ending_b and has_ending_c and has_ending_d,
        "detail": f"Must have all 4 endings (A, B, C, D). Found: A={has_ending_a}, B={has_ending_b}, C={has_ending_c}, D={has_ending_d}"
    })

    # Endings must be named/typed (圆满/悲剧/开放/反转 somewhere in section 5)
    ending_types_present = sum([
        bool(re.search(r'圆满', content)),
        bool(re.search(r'悲剧', content)),
        bool(re.search(r'开放', content)),
        bool(re.search(r'反转', content)),
    ])
    checks.append({
        "name": "ending_types_named_圆满悲剧开放反转",
        "passed": ending_types_present >= 4,
        "detail": f"All 4 ending types (圆满, 悲剧, 开放, 反转) must appear. Found {ending_types_present}/4"
    })

    # --- CHECK 7: Section 六 - 创作建议 ---
    has_section6 = bool(re.search(r'##\s+六[、.．,，]\s*创作建议', content))
    checks.append({
        "name": "section_6_创作建议",
        "passed": has_section6,
        "detail": "Must have '## 六、创作建议' section"
    })

    # --- CHECK 8: Content relevance - mentions 悬疑 or 侦探 (correct genre) ---
    is_correct_genre = bool(re.search(r'悬疑|侦探|推理', content))
    checks.append({
        "name": "content_matches_genre_悬疑推理",
        "passed": is_correct_genre,
        "detail": "Content must be about 悬疑推理/侦探 genre as specified in the brief"
    })

    # --- CHECK 9: Dual protagonist (双主角) ---
    # Brief specifies 双主角 setting
    has_dual_protagonist = bool(re.search(r'双主角|两.*主角|主角.*两|第二.*主角', content)) or \
                           (len(re.findall(r'###\s+2\.1', content)) >= 1 and 
                            len(re.findall(r'主角[一二两1-2]?[：:、]|[一二两]号主角', content)) >= 1)
    # More lenient: check if section 2.1 has substantial content suggesting two protagonists
    protagonist_section_match = re.search(r'###\s+2[\s.]*[.．]\s*1.*?(?=###|\Z)', content, re.DOTALL)
    if protagonist_section_match:
        protagonist_content = protagonist_section_match.group(0)
        # If it has two distinct character names, consider dual protagonist addressed
        has_dual_content = bool(re.search(r'双主角|两.*主角|主角.*[二两]|第[一二]主角', content))
        has_dual_protagonist = has_dual_content or bool(re.search(r'双主角', content))
    
    checks.append({
        "name": "dual_protagonist_mentioned",
        "passed": has_dual_protagonist or bool(re.search(r'双主角', content)),
        "detail": "Brief specifies 双主角 (dual protagonist) - should be reflected in character design"
    })

    # --- SCORING ---
    critical_checks = [
        "file_exists",
        "section_2_人物设定",
        "subsection_2.1_主角",
        "section_3_人物关系图",
        "relationship_table_4col_headers",
        "section_4_剧情发展",
        "three_act_structure_4.1_4.2_4.3",
        "section_5_多版本结局",
        "all_four_endings_A_B_C_D",
        "ending_types_named_圆满悲剧开放反转",
        "section_6_创作建议",
    ]

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    score = round(passed_count / total, 3)
    overall_passed = critical_passed and (passed_count / total >= 0.8)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))