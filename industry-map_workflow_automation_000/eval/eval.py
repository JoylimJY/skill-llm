import sys
import json
import csv
import re
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
score = 0.0
total_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, total_weight
    total_weight += weight
    if passed:
        score += weight

# ===================== FIND FILES =====================
csv_files = list(Path(workspace).rglob("半导体产业图谱_full.csv"))
md_files = list(Path(workspace).rglob("半导体产业图谱生成过程记录.md"))

csv_path = csv_files[0] if csv_files else None
md_path = md_files[0] if md_files else None

# ===================== CHECK 1: CSV FILE EXISTS =====================
add_check(
    "CSV文件存在",
    csv_path is not None,
    f"找到文件: {csv_path}" if csv_path else "未找到半导体产业图谱_full.csv",
    weight=2.0
)

# ===================== CHECK 2: MD FILE EXISTS =====================
add_check(
    "MD文件存在",
    md_path is not None,
    f"找到文件: {md_path}" if md_path else "未找到半导体产业图谱生成过程记录.md",
    weight=1.0
)

rows = []
headers = []

if csv_path:
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
    except Exception as e:
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)
        except Exception as e2:
            add_check("CSV可读性", False, f"无法读取CSV: {e2}", weight=2.0)

    # ===================== CHECK 3: CORRECT 8 COLUMNS =====================
    required_cols = {"id", "name", "level", "parent_id", "parent_name", "path", "classification", "decision_basis"}
    actual_cols = set(h.strip().lower() for h in headers) if headers else set()
    # Also handle exact case match
    actual_cols_exact = set(h.strip() for h in headers) if headers else set()
    cols_ok = required_cols.issubset(actual_cols_exact) or required_cols.issubset(actual_cols)
    add_check(
        "CSV包含8个必需列",
        cols_ok,
        f"实际列: {list(actual_cols_exact)}, 需要: {list(required_cols)}",
        weight=2.0
    )

    # ===================== CHECK 4: ROW COUNT 400-1200 =====================
    row_count = len(rows)
    count_ok = 400 <= row_count <= 1200
    add_check(
        "CSV行数在400-1200范围内",
        count_ok,
        f"实际行数: {row_count}",
        weight=2.0
    )

    # ===================== CHECK 5: ID FORMAT (hierarchical with dashes) =====================
    id_pattern = re.compile(r'^\d+(-\d+)*$')
    bad_ids = []
    id_set = set()
    for i, row in enumerate(rows[:20]):  # check first 20 for speed
        row_id = row.get("id", "").strip()
        if row_id and not id_pattern.match(row_id):
            bad_ids.append(row_id)
        if row_id:
            id_set.add(row_id)
    
    # Also check all IDs
    all_ids = set()
    for row in rows:
        rid = row.get("id", "").strip()
        if rid:
            all_ids.add(rid)
    
    id_format_ok = len(bad_ids) == 0 and len(all_ids) > 0
    add_check(
        "ID格式正确(层级递进格式如1-1-1)",
        id_format_ok,
        f"错误格式ID样例: {bad_ids[:5]}" if bad_ids else f"共{len(all_ids)}个唯一ID，格式正确",
        weight=2.0
    )

    # ===================== CHECK 6: LEVEL DEPTH 5-7 EXISTS =====================
    level_counts = {}
    for row in rows:
        try:
            lv = int(row.get("level", "0").strip())
            level_counts[lv] = level_counts.get(lv, 0) + 1
        except:
            pass
    
    max_level = max(level_counts.keys()) if level_counts else 0
    has_deep = max_level >= 5
    add_check(
        "存在5层及以上深度节点",
        has_deep,
        f"最大层级: {max_level}, 各层分布: {level_counts}",
        weight=2.0
    )

    # ===================== CHECK 7: PARENT_ID REFERENCES VALID IDS =====================
    if all_ids:
        orphan_count = 0
        checked = 0
        for row in rows:
            pid = row.get("parent_id", "").strip()
            rid = row.get("id", "").strip()
            if pid and pid not in all_ids:  # parent should exist
                orphan_count += 1
            if rid and rid != "1":  # non-root should have parent
                checked += 1
        
        orphan_ok = orphan_count == 0
        add_check(
            "parent_id引用有效(无孤立节点)",
            orphan_ok,
            f"孤立节点数量: {orphan_count}",
            weight=1.5
        )

    # ===================== CHECK 8: PATH COLUMN USES / SEPARATOR =====================
    bad_paths = []
    for row in rows[:50]:
        path_val = row.get("path", "").strip()
        if path_val and "/" not in path_val and len(path_val) > 5:
            # Only flag if it's not a level-1 node (which might not have /)
            try:
                lv = int(row.get("level", "1").strip())
                if lv > 1:
                    bad_paths.append(path_val)
            except:
                pass
    
    path_ok = len(bad_paths) == 0
    add_check(
        "path列使用/分隔符",
        path_ok,
        f"错误路径样例: {bad_paths[:3]}" if bad_paths else "路径格式正确",
        weight=1.0
    )

    # ===================== CHECK 9: NO COMPANY/BRAND NAMES IN node names =====================
    forbidden_companies = [
        "华为", "中兴", "小米", "TSMC", "台积电", "三星", "英特尔", "英伟达", "AMD",
        "高通", "联发科", "紫光", "中芯国际", "长江存储", "长鑫", "应用材料", "阿斯麦", "ASML",
        "东京电子", "泛林", "科磊", "博通", "德州仪器", "恩智浦", "意法半导体"
    ]
    company_violations = []
    for row in rows:
        name_val = row.get("name", "").strip()
        for company in forbidden_companies:
            if company in name_val:
                company_violations.append(f"'{name_val}' 含 '{company}'")
                break
    
    no_company_ok = len(company_violations) == 0
    add_check(
        "节点名称不含企业/品牌名称",
        no_company_ok,
        f"违规节点: {company_violations[:5]}" if company_violations else "无企业名称违规",
        weight=2.0
    )

    # ===================== CHECK 10: NO PUNCTUATION IN NODE NAMES =====================
    punct_pattern = re.compile(r'[，,；;、。.！!？?（）()【】\[\]{}《》<>""\'\'：:@#$%^&*+=|\\]')
    punct_violations = []
    for row in rows:
        name_val = row.get("name", "").strip()
        if name_val and punct_pattern.search(name_val):
            punct_violations.append(name_val)
    
    no_punct_ok = len(punct_violations) == 0
    add_check(
        "节点名称不含标点符号",
        no_punct_ok,
        f"含标点节点: {punct_violations[:5]}" if punct_violations else "无标点违规",
        weight=1.5
    )

    # ===================== CHECK 11: NO PARAMETER SPECS IN NAMES =====================
    spec_pattern = re.compile(r'\d+\s*(nm|mm|um|μm|GHz|MHz|V|kV|W|kW|MW|GB|TB|%)')
    spec_violations = []
    for row in rows:
        name_val = row.get("name", "").strip()
        if name_val and spec_pattern.search(name_val):
            spec_violations.append(name_val)
    
    no_spec_ok = len(spec_violations) == 0
    add_check(
        "节点名称不含具体参数规格",
        no_spec_ok,
        f"含参数节点: {spec_violations[:5]}" if spec_violations else "无参数规格违规",
        weight=1.5
    )

    # ===================== CHECK 12: DECISION_BASIS FOR LEVEL 5+ NODES =====================
    deep_nodes = [row for row in rows if row.get("level", "").strip() in ("5", "6", "7")]
    deep_with_basis = [row for row in deep_nodes if row.get("decision_basis", "").strip()]
    
    if deep_nodes:
        basis_ratio = len(deep_with_basis) / len(deep_nodes)
        basis_ok = basis_ratio >= 0.5  # At least 50% of deep nodes should have decision_basis
        add_check(
            "5-7层节点有decision_basis说明(覆盖率≥50%)",
            basis_ok,
            f"深层节点总数: {len(deep_nodes)}, 有decision_basis: {len(deep_with_basis)}, 覆盖率: {basis_ratio:.1%}",
            weight=2.0
        )
    else:
        add_check(
            "5-7层节点有decision_basis说明",
            False,
            "未找到5层以上节点，无法评估decision_basis",
            weight=2.0
        )

    # ===================== CHECK 13: HEAD NODE IS 半导体 =====================
    head_nodes = [row for row in rows if row.get("level", "").strip() == "1"]
    head_ok = any(row.get("name", "").strip() == "半导体" for row in head_nodes)
    add_check(
        "头节点为半导体",
        head_ok,
        f"一级节点: {[row.get('name','') for row in head_nodes]}",
        weight=1.0
    )

    # ===================== CHECK 14: MULTIPLE FIRST-LEVEL CATEGORIES (Level 2) =====================
    level2_nodes = [row for row in rows if row.get("level", "").strip() == "2"]
    l2_count = len(level2_nodes)
    l2_ok = l2_count >= 4  # At least 4 first-level categories
    add_check(
        "至少有4个一级分类(level=2节点)",
        l2_ok,
        f"发现{l2_count}个一级分类: {[row.get('name','') for row in level2_nodes[:8]]}",
        weight=1.5
    )

    # ===================== CHECK 15: NO MARKETING ADJECTIVES =====================
    marketing_words = ["高效", "领先", "核心", "先进", "新型", "智能化", "最新", "顶尖", "卓越"]
    marketing_violations = []
    for row in rows:
        name_val = row.get("name", "").strip()
        for word in marketing_words:
            if name_val.startswith(word) or f"{word}" == name_val[:len(word)]:
                # Only flag if it's a pure marketing adjective prefix
                if word in name_val and len(name_val) <= len(word) + 6:
                    marketing_violations.append(name_val)
                    break
    
    no_marketing_ok = len(marketing_violations) <= 2  # Allow small tolerance
    add_check(
        "节点名称无营销性描述",
        no_marketing_ok,
        f"营销词汇节点: {marketing_violations[:5]}" if marketing_violations else "无营销词汇",
        weight=1.0
    )

# ===================== CHECK MD FILE =====================
if md_path:
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        required_sections = [
            "初始需求理解",
            "第一版设计方案",
            "问题识别",
            "关键节点划分依据",
            "参考来源"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in md_content:
                missing_sections.append(section)
        
        md_sections_ok = len(missing_sections) == 0
        add_check(
            "MD文件包含所有必需章节",
            md_sections_ok,
            f"缺少章节: {missing_sections}" if missing_sections else "所有章节存在",
            weight=1.5
        )
        
        # Check MD mentions 半导体
        md_topic_ok = "半导体" in md_content
        add_check(
            "MD文件涉及半导体主题",
            md_topic_ok,
            "MD文件包含半导体内容" if md_topic_ok else "MD文件未提及半导体",
            weight=0.5
        )

    except Exception as e:
        add_check("MD文件可读性", False, f"无法读取MD文件: {e}", weight=1.5)

# ===================== FINAL SCORE =====================
final_score = score / total_weight if total_weight > 0 else 0.0
passed = final_score >= 0.70

result = {
    "passed": passed,
    "score": round(final_score, 4),
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))