import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested directory structure with distractor files ---

dirs = [
    "gis_platform/raw_data/rivers",
    "gis_platform/raw_data/lakes",
    "gis_platform/raw_data/basins",
    "gis_platform/processed/exports",
    "gis_platform/processed/logs",
    "gis_platform/schemas",
    "gis_platform/archive/2022",
    "gis_platform/archive/2023",
    "reference_docs/geography",
    "reference_docs/hydrology",
    "reference_docs/climate",
    "temp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor file 1: An old, incomplete river data file with WRONG values
old_data = {
    "rivers": [
        {"name": "长江", "length_km": 6300, "note": "needs update"},
        {"name": "黄河", "length_km": 5400, "ocean": "黄海"},  # WRONG ocean
        {"name": "珠江", "length_km": 2400},  # WRONG length
    ]
}
with open(os.path.join(workspace, "gis_platform/raw_data/rivers/legacy_river_data.json"), "w", encoding="utf-8") as f:
    json.dump(old_data, f, ensure_ascii=False, indent=2)

# Distractor file 2: A partial systems list with errors
partial_systems = [
    {"id": 1, "name": "松花江水系", "area": "55.68"},
    {"id": 2, "name": "辽河水系", "area": "22.9"},
    {"id": 3, "name": "海河水系"},  # missing area
    {"id": 5, "name": "淮河水系", "area": "27"},
    # Note: system 4 (黄河水系) and 6 (长江水系) and 7 (珠江水系) are MISSING
]
with open(os.path.join(workspace, "gis_platform/raw_data/rivers/partial_systems.json"), "w", encoding="utf-8") as f:
    json.dump(partial_systems, f, ensure_ascii=False, indent=2)

# Distractor file 3: Lake data (irrelevant)
lake_data = {
    "lakes": [
        {"name": "鄱阳湖", "region": "东部平原", "type": "淡水湖"},
        {"name": "青海湖", "region": "青藏高原", "type": "咸水湖"},
        {"name": "太湖", "region": "东部平原", "type": "淡水湖"},
    ]
}
with open(os.path.join(workspace, "gis_platform/raw_data/lakes/major_lakes.json"), "w", encoding="utf-8") as f:
    json.dump(lake_data, f, ensure_ascii=False, indent=2)

# Distractor file 4: Basin coverage estimates (wrong percentages)
basin_stats = {"external": "60%", "internal": "40%", "source": "estimated_2019"}
with open(os.path.join(workspace, "gis_platform/raw_data/basins/basin_coverage_draft.json"), "w", encoding="utf-8") as f:
    json.dump(basin_stats, f, ensure_ascii=False, indent=2)

# Distractor file 5: A processing log
with open(os.path.join(workspace, "gis_platform/processed/logs/import_2023.log"), "w", encoding="utf-8") as f:
    f.write("2023-11-01 08:00:00 INFO Import started\n")
    f.write("2023-11-01 08:01:22 WARN Missing basin area for 海河水系\n")
    f.write("2023-11-01 08:02:45 ERROR Ocean field missing for 黄河\n")
    f.write("2023-11-01 08:03:10 INFO Partial import completed: 5/7 systems\n")

# Distractor file 6: JSON schema stub (incomplete)
schema_stub = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "seven_systems": {"type": "array"},
        "major_rivers_detail": {"type": "object"}
    },
    "required": ["seven_systems"],
    "note": "DRAFT - incomplete schema, do not use for validation"
}
with open(os.path.join(workspace, "gis_platform/schemas/river_report_schema_draft.json"), "w", encoding="utf-8") as f:
    json.dump(schema_stub, f, ensure_ascii=False, indent=2)

# Distractor file 7: A climate reference file
with open(os.path.join(workspace, "reference_docs/climate/monsoon_regions.txt"), "w", encoding="utf-8") as f:
    f.write("季风区：东部地区，年降水量600mm以上\n")
    f.write("内陆干旱区：西北地区，年降水量200mm以下\n")
    f.write("青藏高原区：特殊气候，高寒\n")

# Distractor file 8: Hydrology notes with misleading info
with open(os.path.join(workspace, "reference_docs/hydrology/river_notes_draft.txt"), "w", encoding="utf-8") as f:
    f.write("注意：部分数据待核实\n")
    f.write("黄河流入：渤海？黄海？待确认\n")  # deliberately ambiguous
    f.write("长江流域面积：约180万平方公里（待精确）\n")
    f.write("额尔齐斯河：流入北冰洋（仅中国境内段）\n")
    f.write("七大水系排序：待确认南北顺序\n")

# Distractor file 9: Archive data with old format
with open(os.path.join(workspace, "gis_platform/archive/2022/systems_v1.csv"), "w", encoding="utf-8") as f:
    f.write("系统名,面积\n")
    f.write("松花江水系,55.68\n")
    f.write("长江水系,180\n")
    f.write("黄河水系,75.2\n")
    # Incomplete - only 3 rows

# Distractor file 10: A requirements document (vague)
with open(os.path.join(workspace, "gis_platform/archive/2023/requirements_v2.txt"), "w", encoding="utf-8") as f:
    f.write("GIS数据库导入需求 v2\n")
    f.write("================\n")
    f.write("1. 需要完整的七大水系数据\n")
    f.write("2. 需要主要河流详细信息\n")
    f.write("3. 需要流域统计数据\n")
    f.write("4. 输出格式: JSON\n")
    f.write("5. 文件名: china_rivers_report.json\n")
    f.write("注：具体字段规范见技术文档\n")

# Distractor file 11: A scratch notes file with partially correct info
with open(os.path.join(workspace, "temp/scratch/notes.txt"), "w", encoding="utf-8") as f:
    f.write("七大水系（从北到南）：\n")
    f.write("1. 松花江\n")
    f.write("2. 辽河\n")
    f.write("3. 海河\n")
    f.write("4. 黄河\n")
    f.write("5. 淮河\n")
    f.write("6. 长江\n")
    f.write("7. 珠江\n")
    f.write("注：以上顺序可能有误，需核实\n")

# Distractor file 12: Geography reference
with open(os.path.join(workspace, "reference_docs/geography/china_regions.txt"), "w", encoding="utf-8") as f:
    f.write("中国地理分区：\n")
    f.write("东北：黑龙江、吉林、辽宁\n")
    f.write("华北：北京、天津、河北、山西、内蒙古\n")
    f.write("西北：陕西、甘肃、青海、宁夏、新疆\n")
    f.write("西南：重庆、四川、贵州、云南、西藏\n")
    f.write("华南：广东、广西、海南\n")
    f.write("华东：上海、江苏、浙江、安徽、福建、江西、山东\n")

print("Workspace initialized with distractor files.")
print(f"Files created in: {workspace}")