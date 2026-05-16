import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "project_alpha/docs/legal",
    "project_alpha/docs/technical",
    "project_alpha/team/profiles",
    "project_alpha/financials/q1",
    "project_alpha/financials/q2",
    "market_research/competitors",
    "market_research/surveys",
    "prototypes/v1/hardware",
    "prototypes/v1/software",
    "prototypes/v2",
    "admin/hr",
    "admin/compliance",
    "patents/filed",
    "patents/pending",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "project_alpha/docs/legal/nda_template.txt": "保密协议模板 v2.3\n甲方：____\n乙方：____\n保密期限：3年\n",
    "project_alpha/docs/legal/ip_agreement_draft.txt": "知识产权归属协议草稿\n本协议规定技术成果归属...",
    "project_alpha/docs/technical/architecture_overview.md": "# 系统架构\n## 模块1: 数据采集\n## 模块2: AI推断引擎\n",
    "project_alpha/docs/technical/api_specs.json": json.dumps({"version": "1.0", "endpoints": ["/diagnose", "/report"]}),
    "project_alpha/team/profiles/teacher_profile.txt": "姓名：张教授\n专业：医学影像AI\n职称：教授\n发表论文：48篇\n专利：7项",
    "project_alpha/team/profiles/student_lead.txt": "姓名：李明\n角色：CEO候选\n背景：计算机博士在读\n创业经验：1次",
    "project_alpha/team/profiles/tech_lead.txt": "姓名：王芳\n角色：CTO候选\n背景：AI工程师5年经验",
    "project_alpha/financials/q1/expenses_raw.csv": "月份,研发费用,人员费用,运营费用\n1月,80000,120000,30000\n2月,90000,120000,35000\n3月,85000,125000,32000\n",
    "project_alpha/financials/q2/projection_notes.txt": "Q2预测：研发投入增加15%，招募2名工程师",
    "market_research/competitors/competitor_list.txt": "竞争对手1: 某医疗AI公司，融资2亿\n竞争对手2: 外资企业，市占率12%",
    "market_research/surveys/survey_results_raw.txt": "调研样本数：127\n愿意付费比例：63%\n平均期望价格：月付2800元",
    "prototypes/v1/hardware/sensor_specs.txt": "传感器规格：分辨率4096x4096，帧率30fps",
    "prototypes/v1/software/test_log.txt": "2024-03-01 测试通过率: 94.2%\n2024-03-15 测试通过率: 96.1%",
    "prototypes/v2/progress_notes.txt": "V2原型预计2个月完成，增加实时处理功能",
    "admin/hr/hiring_plan.txt": "Q2招募：高级算法工程师×2，产品经理×1，市场专员×1",
    "admin/compliance/medical_device_notes.txt": "医疗器械注册：预计需要18个月，费用约80万",
    "patents/filed/patent_001.txt": "专利号：CN202310045678\n名称：基于深度学习的肺结节检测方法\n状态：已授权",
    "patents/pending/patent_002.txt": "申请号：CN202410098765\n名称：多模态医学影像融合算法\n状态：实质审查中",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM INPUT ---
# Raw, messy project data that the agent must process using the SKILL.md framework
project_data = {
    "project_name": "MedVision AI 辅助诊断系统",
    "description": "基于深度学习的肺部CT影像智能诊断平台，准确率达97.3%（业内平均91%），已申请3项发明专利",
    "technology_scores_raw": {
        # Raw scores 1-10 for each dimension - NOT yet weighted
        # Agent must know the exact weights from SKILL.md
        "技术创新性": 9,
        "市场需求度": 8,
        "技术成熟度": 7,
        "竞争优势": 8,
        "团队匹配度": 6,
        "资源可获得性": 5
    },
    "funding_scenario": {
        # Agent must use the exact formula: burn_rate × months_to_milestone × 1.5
        "monthly_burn_rate_yuan": 230000,
        "months_to_next_milestone": 8,
        "description": "下一里程碑：完成产品原型并获得首批10家医院试用合同"
    },
    "market_validation_metrics": {
        # Agent must compare against EXACT health standards from SKILL.md
        "CAC_yuan": 15000,
        "LTV_yuan": 52000,
        "MAU_growth_rate_percent": 23.5,
        "b2b_retention_rate_percent": 38,
        "NPS_score": 34
    },
    "team_structure_draft": {
        "首席科学家": {"person": "张教授", "time_commitment_percent": 30, "proposed_equity_percent": 18},
        "CEO": {"person": "李明", "time_commitment_percent": 100, "proposed_equity_percent": 35},
        "CTO": {"person": "王芳", "time_commitment_percent": 100, "proposed_equity_percent": 17},
        "option_pool_percent": 12
    }
}

with open(os.path.join(workspace, "project_data.json"), "w", encoding="utf-8") as f:
    json.dump(project_data, f, ensure_ascii=False, indent=2)

# A deliberately misleading/wrong pre-analysis file to confuse naive agents
wrong_analysis = {
    "note": "初步分析（未经验证，勿用）",
    "naive_score_calculation": "简单平均分 = (9+8+7+8+6+5)/6 = 7.17 × 10 = 71.7分",
    "naive_funding": "230000 × 8 = 1840000元",
    "wrong_retention_comment": "留存率38%，行业标准通常>80%",
    "warning": "以上计算方式可能不正确，请以正式评估框架为准"
}

with open(os.path.join(workspace, "project_alpha/financials/preliminary_rough_notes.json"), "w", encoding="utf-8") as f:
    json.dump(wrong_analysis, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 2} files")