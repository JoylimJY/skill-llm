import os
import json
import random
import pathlib

random.seed(42)

base = pathlib.Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "advisory_platform/config",
    "advisory_platform/templates",
    "advisory_platform/logs",
    "advisory_platform/outputs",
    "advisory_platform/clients/midea_group",
    "advisory_platform/clients/haier_group",
    "advisory_platform/clients/byd_corp",
    "advisory_platform/perspectives/legacy_v1",
    "advisory_platform/perspectives/archived",
    "advisory_platform/tests",
    "advisory_platform/docs",
    "advisory_platform/scripts",
]
for d in dirs:
    (base / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# Outdated v1 perspective file (WRONG - only 6 models, 5 tests - legacy)
legacy_perspective = {
    "version": "1.0",
    "name": "方洪波思维视角",
    "mental_models": [
        "职业经理人典范", "战略定力", "组织重构",
        "数字化先锋", "全球视野", "危机意识"
    ],
    "validation_tests": 5,
    "note": "DEPRECATED - use v2.0"
}
with open(base / "advisory_platform/perspectives/legacy_v1/fang_hongbo_v1.json", "w", encoding="utf-8") as f:
    json.dump(legacy_perspective, f, ensure_ascii=False, indent=2)

# Distractor: wrong trigger words file
with open(base / "advisory_platform/perspectives/legacy_v1/triggers_old.txt", "w", encoding="utf-8") as f:
    f.write("老版触发词:\n")
    f.write("方洪波分析\n")
    f.write("fang style\n")
    f.write("美的视角\n")
    f.write("# NOTE: These triggers are deprecated and no longer valid\n")

# Distractor: haier client scenarios (irrelevant)
haier_scenarios = [
    {"id": "H001", "scenario": "海尔冰箱海外市场销量下滑", "advisor": "zhang_ruimin"},
    {"id": "H002", "scenario": "智家平台用户增长放缓", "advisor": "zhang_ruimin"},
]
with open(base / "advisory_platform/clients/haier_group/scenarios.json", "w", encoding="utf-8") as f:
    json.dump(haier_scenarios, f, ensure_ascii=False, indent=2)

# Distractor: BYD scenarios
byd_scenarios = [
    {"id": "B001", "scenario": "新能源汽车补贴退坡影响", "advisor": "wang_chuanfu"},
]
with open(base / "advisory_platform/clients/byd_corp/scenarios.json", "w", encoding="utf-8") as f:
    json.dump(byd_scenarios, f, ensure_ascii=False, indent=2)

# Distractor: platform config with wrong output format spec
platform_config = {
    "platform": "Strategic Advisory System",
    "version": "3.2.1",
    "default_output_format": "xml",  # WRONG - agent must use correct format per SKILL.md
    "language": "zh-CN",
    "max_response_length": 500,
    "perspectives_loaded": ["zhang_ruimin", "ren_zhengfei"]  # NOTE: fang_hongbo NOT listed (trap)
}
with open(base / "advisory_platform/config/platform_config.json", "w", encoding="utf-8") as f:
    json.dump(platform_config, f, ensure_ascii=False, indent=2)

# Distractor: log file with misleading old outputs
with open(base / "advisory_platform/logs/old_advisory_runs.log", "w", encoding="utf-8") as f:
    f.write("2025-01-10 10:23:11 [INFO] Processed scenario M001 using fang_hongbo_v1 perspective\n")
    f.write("2025-01-10 10:23:12 [INFO] Output: 作为美的管理者，我认为需要稳步推进\n")
    f.write("2025-01-10 10:23:13 [WARN] v1 perspective deprecated, upgrade to v2.0\n")
    f.write("2025-01-10 10:23:14 [INFO] Processed scenario M002 using fang_hongbo_v1 perspective\n")
    f.write("2025-01-10 10:23:15 [INFO] Output format: XML (deprecated)\n")

# Distractor: archived wrong-format output example
archived_output = {
    "scenario_id": "M000",
    "perspective": "fang_hongbo_v1",
    "response_format": "xml",
    "content": "<response><stance>谨慎观察</stance><recommendation>等等看</recommendation></response>",
    "note": "ARCHIVED - wrong format, wrong stance"
}
with open(base / "advisory_platform/perspectives/archived/sample_output_v1.json", "w", encoding="utf-8") as f:
    json.dump(archived_output, f, ensure_ascii=False, indent=2)

# Distractor: a misleading template
with open(base / "advisory_platform/templates/generic_advisor_template.txt", "w", encoding="utf-8") as f:
    f.write("作为一名顾问，我建议您考虑以下几点：\n")
    f.write("1. 分析市场环境\n")
    f.write("2. 评估风险\n")
    f.write("3. 制定计划\n")
    f.write("# Generic template - does NOT apply Fang Hongbo perspective rules\n")

# Distractor: docs about a different advisor
with open(base / "advisory_platform/docs/ren_zhengfei_perspective.md", "w", encoding="utf-8") as f:
    f.write("# 任正非思维视角\n\n")
    f.write("核心：客户第一、奋斗者文化、技术立国\n\n")
    f.write("触发词：任正非模式、华为思维\n")

# Distractor: test scripts that test the WRONG perspective
with open(base / "advisory_platform/tests/test_zhang_ruimin.py", "w", encoding="utf-8") as f:
    f.write("# Test suite for Zhang Ruimin perspective\n")
    f.write("# Not relevant to Fang Hongbo\n")
    f.write("def test_zhang_ruimin_digital():\n    pass\n")

# Distractor: scripts folder with unrelated script
with open(base / "advisory_platform/scripts/batch_xml_exporter.py", "w", encoding="utf-8") as f:
    f.write("# Exports advisory results to XML format\n")
    f.write("# DEPRECATED - platform moved away from XML\n")

# Distractor: empty outputs folder marker
with open(base / "advisory_platform/outputs/.gitkeep", "w") as f:
    f.write("")

# --- THE ACTUAL TASK INPUT ---
# Midea Group client: batch of strategic scenarios requiring Fang Hongbo perspective
# These are deliberately crafted to test the counter-intuitive stances from SKILL.md validation tests

midea_scenarios = [
    {
        "id": "M001",
        "title": "新业务资源困境",
        "context": "美的集团某事业部被分配到一个新兴业务方向，但总部给予的预算和人员编制相当有限，团队士气低落，部分管理层建议放弃该方向。",
        "question": "作为事业部负责人，面对资源严重不足的新业务，应该采取什么立场？"
    },
    {
        "id": "M002",
        "title": "战略执行一年未见成效",
        "context": "美的某战略方向已执行整整一年，市场反馈平淡，竞争对手仍领先，董事会部分成员提议调整或放弃该战略。",
        "question": "面对战略执行一年未见效的压力，应该如何回应？"
    },
    {
        "id": "M003",
        "title": "公司业绩创历史新高",
        "context": "美的集团刚刚发布了历史最佳季度财报，营收和利润双双创纪录，媒体和投资者一片叫好，团队士气高涨。",
        "question": "在业绩最好的时候，作为领导层应该持什么态度？"
    },
    {
        "id": "M004",
        "title": "数字化转型投入争议",
        "context": "董事会讨论数字化转型投入计划，该计划投资周期长达5年，短期ROI不明确，财务总监提出强烈反对意见，认为风险过大。",
        "question": "面对数字化投入周期长、短期ROI不确定的质疑，应持什么立场？"
    },
    {
        "id": "M005",
        "title": "海外并购整合挑战",
        "context": "美的拟收购一家欧洲工业机器人公司，整合难度被评估为极高，包括文化差异、监管障碍和技术融合风险，部分顾问建议放弃。",
        "question": "面对海外并购整合难度极大的情况，应如何决策？"
    }
]

with open(base / "advisory_platform/clients/midea_group/scenarios_batch_2026.json", "w", encoding="utf-8") as f:
    json.dump(midea_scenarios, f, ensure_ascii=False, indent=2)

# Also create a confusing "instructions" file with WRONG output format guidance
with open(base / "advisory_platform/clients/midea_group/client_brief.txt", "w", encoding="utf-8") as f:
    f.write("Midea Group Strategic Advisory Brief\n")
    f.write("=====================================\n")
    f.write("Client request: Generate strategic advisory responses for attached scenarios.\n")
    f.write("Requested advisor persona: 方洪波 (Fang Hongbo)\n")
    f.write("Preferred output: XML format (per IT department legacy system requirement)\n")
    f.write("NOTE: IT department XML requirement may be overridden by advisor persona spec.\n")
    f.write("Scenario file: scenarios_batch_2026.json\n")
    f.write("Output file requested: advisory_report_2026.json\n")

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(pathlib.Path("/workspace").rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to('/workspace')}")