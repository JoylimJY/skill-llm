import os
import random
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create realistic project directory structure with distractors
dirs = [
    "assets",
    "docs/航空航天",
    "docs/新能源",
    "docs/人工智能",
    "research/raw_data",
    "research/processed",
    "templates",
    "output/draft",
    "scripts",
    "config",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Create the default template CSV (assets/default_template.csv) ---
# This is the航空航天 example template referenced in the SKILL.md
template_rows = [
    ["id", "name", "level", "parent_id", "parent_name", "path", "classification", "decision_basis"],
    ["1", "航空航天", "1", "", "", "航空航天", "头节点", ""],
    ["1-1", "航空装备", "2", "1", "航空航天", "航空航天/航空装备", "产业链环节", ""],
    ["1-2", "航天装备", "2", "1", "航空航天", "航空航天/航天装备", "产业链环节", ""],
    ["1-3", "通用航空", "2", "1", "航空航天", "航空航天/通用航空", "产业链环节", ""],
    ["1-4", "航空航天材料", "2", "1", "航空航天", "航空航天/航空航天材料", "产业链环节", ""],
    ["1-5", "航空航天电子", "2", "1", "航空航天", "航空航天/航空航天电子", "产业链环节", ""],
    ["1-1-1", "民用飞机", "3", "1-1", "航空装备", "航空航天/航空装备/民用飞机", "产品大类", ""],
    ["1-1-2", "军用飞机", "3", "1-1", "航空装备", "航空航天/航空装备/军用飞机", "产品大类", ""],
    ["1-1-3", "无人机", "3", "1-1", "航空装备", "航空航天/航空装备/无人机", "产品大类", ""],
    ["1-2-1", "运载火箭", "3", "1-2", "航天装备", "航空航天/航天装备/运载火箭", "产品大类", ""],
    ["1-2-2", "卫星", "3", "1-2", "航天装备", "航空航天/航天装备/卫星", "产品大类", ""],
    ["1-2-3", "空间站", "3", "1-2", "航天装备", "航空航天/航天装备/空间站", "产品大类", ""],
    ["1-1-1-1", "干线飞机", "4", "1-1-1", "民用飞机", "航空航天/航空装备/民用飞机/干线飞机", "产品细分", ""],
    ["1-1-1-2", "支线飞机", "4", "1-1-1", "民用飞机", "航空航天/航空装备/民用飞机/支线飞机", "产品细分", ""],
    ["1-1-1-3", "宽体飞机", "4", "1-1-1", "民用飞机", "航空航天/航空装备/民用飞机/宽体飞机", "产品细分", ""],
    ["1-1-2-1", "战斗机", "4", "1-1-2", "军用飞机", "航空航天/航空装备/军用飞机/战斗机", "产品细分", ""],
    ["1-1-2-2", "轰炸机", "4", "1-1-2", "军用飞机", "航空航天/航空装备/军用飞机/轰炸机", "产品细分", ""],
    ["1-2-1-1", "液体运载火箭", "4", "1-2-1", "运载火箭", "航空航天/航天装备/运载火箭/液体运载火箭", "产品细分", ""],
    ["1-2-1-2", "固体运载火箭", "4", "1-2-1", "运载火箭", "航空航天/航天装备/运载火箭/固体运载火箭", "产品细分", ""],
    ["1-1-1-1-1", "涡扇发动机", "5", "1-1-1-1", "干线飞机", "航空航天/航空装备/民用飞机/干线飞机/涡扇发动机", "核心零部件", "民用航空主流动力形式，推力大、燃油经济性好"],
    ["1-1-1-1-2", "机体结构", "5", "1-1-1-1", "干线飞机", "航空航天/航空装备/民用飞机/干线飞机/机体结构", "核心零部件", "承力结构，包含机身框架和蒙皮"],
    ["1-1-1-1-3", "航电系统", "5", "1-1-1-1", "干线飞机", "航空航天/航空装备/民用飞机/干线飞机/航电系统", "核心子系统", "飞行控制与导航集成系统"],
    ["1-2-1-1-1", "液氧煤油发动机", "5", "1-2-1-1", "液体运载火箭", "航空航天/航天装备/运载火箭/液体运载火箭/液氧煤油发动机", "推进系统", "高比冲、环保，主流选择"],
    ["1-2-1-1-2", "液氢液氧发动机", "5", "1-2-1-1", "液体运载火箭", "航空航天/航天装备/运载火箭/液体运载火箭/液氢液氧发动机", "推进系统", "比冲高，用于上面级"],
    ["1-2-1-1-1-1", "涡轮泵", "6", "1-2-1-1-1", "液氧煤油发动机", "航空航天/航天装备/运载火箭/液体运载火箭/液氧煤油发动机/涡轮泵", "关键零件", "驱动推进剂高压输送的核心部件"],
    ["1-2-1-1-1-2", "燃烧室", "6", "1-2-1-1-1", "液氧煤油发动机", "航空航天/航天装备/运载火箭/液体运载火箭/液氧煤油发动机/燃烧室", "关键零件", "推进剂混合燃烧区域，承受极端高温高压"],
    ["1-2-1-1-1-3", "喷管", "6", "1-2-1-1-1", "液氧煤油发动机", "航空航天/航天装备/运载火箭/液体运载火箭/液氧煤油发动机/喷管", "关键零件", "推力矢量控制与气体膨胀加速"],
    ["1-2-1-1-1-1-1", "离心式涡轮泵", "7", "1-2-1-1-1-1", "涡轮泵", "航空航天/航天装备/运载火箭/液体运载火箭/液氧煤油发动机/涡轮泵/离心式涡轮泵", "工艺类型", "结构紧凑，适用于高流量推进系统"],
]

with open(os.path.join(workspace, "assets/default_template.csv"), "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(template_rows)

# --- Create the user-provided template for 半导体 (the --template file) ---
# This is a PARTIAL/STUB template (only level 1-2) that the agent should USE AS REFERENCE
semi_template_rows = [
    ["id", "name", "level", "parent_id", "parent_name", "path", "classification", "decision_basis"],
    ["1", "半导体", "1", "", "", "半导体", "头节点", ""],
    ["1-1", "半导体材料", "2", "1", "半导体", "半导体/半导体材料", "产业链环节", "按材料类型分类"],
    ["1-2", "半导体设备", "2", "1", "半导体", "半导体/半导体设备", "产业链环节", ""],
    ["1-3", "集成电路设计", "2", "1", "半导体", "半导体/集成电路设计", "产业链环节", ""],
    ["1-4", "晶圆制造", "2", "1", "半导体", "半导体/晶圆制造", "产业链环节", ""],
    ["1-5", "封装测试", "2", "1", "半导体", "半导体/封装测试", "产业链环节", ""],
]

with open(os.path.join(workspace, "assets/半导体产业图谱_template.csv"), "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(semi_template_rows)

# --- Create distractor files ---

# Existing 新能源 industry map (distractor, shows the depth expected)
xny_rows = [
    ["id", "name", "level", "parent_id", "parent_name", "path", "classification", "decision_basis"],
    ["1", "新能源", "1", "", "", "新能源", "头节点", ""],
    ["1-1", "太阳能光伏", "2", "1", "新能源", "新能源/太阳能光伏", "产业链环节", ""],
    ["1-2", "风能发电", "2", "1", "新能源", "新能源/风能发电", "产业链环节", ""],
    ["1-1-1", "光伏材料", "3", "1-1", "太阳能光伏", "新能源/太阳能光伏/光伏材料", "产品大类", ""],
    ["1-1-2", "光伏电池", "3", "1-1", "太阳能光伏", "新能源/太阳能光伏/光伏电池", "产品大类", ""],
    ["1-1-1-1", "硅材料", "4", "1-1-1", "光伏材料", "新能源/太阳能光伏/光伏材料/硅材料", "材料类型", ""],
    ["1-1-1-2", "薄膜材料", "4", "1-1-1", "光伏材料", "新能源/太阳能光伏/光伏材料/薄膜材料", "材料类型", ""],
    ["1-1-1-1-1", "多晶硅", "5", "1-1-1-1", "硅材料", "新能源/太阳能光伏/光伏材料/硅材料/多晶硅", "具体材料", "改良西门子法生产，纯度99.9999%以上"],
    ["1-1-1-1-2", "单晶硅棒", "5", "1-1-1-1", "硅材料", "新能源/太阳能光伏/光伏材料/硅材料/单晶硅棒", "具体材料", "直拉法生长，用于高效单晶电池"],
]
with open(os.path.join(workspace, "docs/新能源/新能源产业图谱_full.csv"), "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(xny_rows)

# Distractor: old/wrong format CSV that should NOT be used as output
with open(os.path.join(workspace, "research/raw_data/semiconductor_raw.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows([
        ["节点", "父节点", "层级"],
        ["半导体", "", "1"],
        ["集成电路", "半导体", "2"],
        ["分立器件", "半导体", "2"],
    ])

# Distractor: a fake "completed" but incorrect semiconductor map (wrong columns, wrong format)
with open(os.path.join(workspace, "output/draft/semiconductor_draft.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows([
        ["ID", "Name", "Level", "Parent"],
        ["1", "半导体", "1", ""],
        ["2", "集成电路", "2", "1"],
        ["3", "华为海思芯片", "3", "2"],  # Intentionally wrong: company name
        ["4", "7nm工艺芯片", "3", "2"],   # Intentionally wrong: specific parameter
    ])

# Distractor: research notes
with open(os.path.join(workspace, "research/processed/semi_notes.txt"), "w", encoding="utf-8") as f:
    f.write("半导体产业链调研笔记\n")
    f.write("主要分类：材料、设备、设计、制造、封测\n")
    f.write("参考来源：GB/T 4754-2017\n")
    f.write("注意：需要细分到工艺层面\n")

# Distractor: config file
with open(os.path.join(workspace, "config/map_config.json"), "w", encoding="utf-8") as f:
    f.write('{\n  "default_depth": 5,\n  "output_format": "csv",\n  "language": "zh-CN"\n}\n')

# Distractor: scripts
with open(os.path.join(workspace, "scripts/validate_csv.py"), "w", encoding="utf-8") as f:
    f.write("# CSV validation script\n# Usage: python validate_csv.py <file>\nimport sys\nprint('Validation script placeholder')\n")

# Distractor: existing AI map (different industry)
ai_rows = [
    ["id", "name", "level", "parent_id", "parent_name", "path", "classification", "decision_basis"],
    ["1", "人工智能", "1", "", "", "人工智能", "头节点", ""],
    ["1-1", "机器学习", "2", "1", "人工智能", "人工智能/机器学习", "技术领域", ""],
    ["1-2", "计算机视觉", "2", "1", "人工智能", "人工智能/计算机视觉", "技术领域", ""],
    ["1-1-1", "深度学习", "3", "1-1", "机器学习", "人工智能/机器学习/深度学习", "技术分支", ""],
]
with open(os.path.join(workspace, "docs/人工智能/人工智能产业图谱_full.csv"), "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(ai_rows)

# Distractor: template for a different industry
with open(os.path.join(workspace, "templates/量子科技_template.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows([
        ["id", "name", "level", "parent_id", "parent_name", "path", "classification", "decision_basis"],
        ["1", "量子科技", "1", "", "", "量子科技", "头节点", ""],
    ])

# Distractor: README for existing project
with open(os.path.join(workspace, "research/raw_data/SOURCES.txt"), "w", encoding="utf-8") as f:
    f.write("Data sources for semiconductor research:\n")
    f.write("- SEMI (Semiconductor Equipment and Materials International)\n")
    f.write("- CSIA (China Semiconductor Industry Association)\n")
    f.write("- MIIT semiconductor industry reports\n")

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")