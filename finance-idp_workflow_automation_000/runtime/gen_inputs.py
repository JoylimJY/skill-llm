import os
import random
import json

random.seed(42)

base = "/workspace"

# Create realistic distractor directory structure
dirs = [
    "hr/archive/2022",
    "hr/archive/2023",
    "hr/templates",
    "hr/idp_drafts",
    "finance/competency_model",
    "finance/budgets",
    "finance/reports/Q1",
    "finance/reports/Q2",
    "admin/policies",
    "admin/org_chart",
    "training/external",
    "training/internal",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ---- Distractor files ----
distractors = {
    "hr/archive/2022/idp_old_template.txt": "旧版IDP模板（2022年已废止）\n请使用新版模板进行员工发展计划编制。",
    "hr/archive/2023/competency_review_summary.txt": "2023年能力评估综述\n整体达标率：78%\n重点提升领域：融资筹划、资金管理",
    "hr/templates/smart_goal_guide.txt": "SMART目标制定指引\nS: Specific\nM: Measurable\nA: Achievable\nR: Relevant\nT: Time-bound",
    "hr/idp_drafts/draft_wang_fang.txt": "王芳 草稿\n当前职位：会计主管\n目标职位：财务经理\n（未完成）",
    "finance/competency_model/level_definitions.csv": "级别,说明\n1,初级\n2,基础\n3,胜任\n4,精通\n5,专家",
    "finance/competency_model/competency_framework_v3.json": json.dumps({
        "财务分析": ["初级", "基础", "胜任", "精通", "专家"],
        "预算管理": ["初级", "基础", "胜任", "精通", "专家"],
        "资金管理": ["初级", "基础", "胜任", "精通", "专家"],
        "融资筹划": ["初级", "基础", "胜任", "精通", "专家"],
        "税务管理": ["初级", "基础", "胜任", "精通", "专家"],
        "内部控制": ["初级", "基础", "胜任", "精通", "专家"],
    }, ensure_ascii=False, indent=2),
    "finance/budgets/2024_budget_plan.txt": "2024年预算计划\n总预算：12亿元\n海外业务预算：3.5亿元（同比增长120%）",
    "finance/reports/Q1/treasury_report_Q1.txt": "Q1资金报告\n平均资金余额：8.2亿\n融资成本：3.85%",
    "finance/reports/Q2/treasury_report_Q2.txt": "Q2资金报告\n平均资金余额：9.1亿\n融资成本：3.72%",
    "admin/policies/promotion_criteria.txt": "晋升标准\n能力评估总分须达到4.0以上\n须完成至少一个跨部门项目",
    "admin/org_chart/finance_dept_2024.txt": "财务部组织架构\n财务总监 - 李明\n  资金部经理 - 张华\n    资金主管 - 陈建国（空缺）\n  预算部经理（空缺）\n    预算主管 - 赵磊",
    "training/external/cfa_schedule_2024.txt": "CFA考试时间表\n2024年2月：报名截止\n2024年5月：Level I考试",
    "training/internal/q3_training_calendar.txt": "Q3内部培训计划\n7月：Excel高阶应用\n8月：IFRS新准则解读\n9月：并购估值基础",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ---- THE PROBLEM: Messy employee assessment file ----
# This is the raw, messy input the agent must process. It's a poorly formatted CSV
# with mixed delimiters, inconsistent spacing, extra commentary lines, and
# some scores written as fractions and some as plain integers.
messy_assessment = """\
# 员工能力自评数据导出 - 系统版本2.3.1 (导出时间: 2024-06-15 09:32:11)
# 注意: 部分数据由员工手工填写，格式可能不一致
# ==========================================
员工姓名,赵磊
工号,FIN-20190847
当前职位,预算主管
目标职位,预算经理
所属部门,财务部/预算中心
直属上级,财务总监 李明
评估周期,2024年H1

# --- 能力自评明细 (格式: 能力项 | 当前水平 | 目标水平) ---
能力项|当前|目标
资金管理 | 3 | 5
融资筹划   |2|5
预算管理|4 | 5
财务分析  | 3 | 4
税务管理 |  2 | 4
内部控制|3|4

# --- 业务背景备注 ---
集团战略方向: 未来两年将大力拓展海外业务，重点布局东南亚市场，需要具备跨境资金运营和境外融资能力的财务管理人才。
上级评语: 赵磊同志工作认真负责，预算管理能力突出，但在资金管理和融资方面需重点加强，建议尽快补齐短板以迎接海外业务扩张带来的挑战。

# 数据有效期至 2024-12-31
"""

with open(os.path.join(base, "employee_assessment_raw.csv"), "w", encoding="utf-8") as f:
    f.write(messy_assessment)

# Also create a partially filled, wrong-format old IDP attempt as a red herring
old_attempt = """\
赵磊个人发展计划（草稿 - 格式错误）
========================================
目标：成为预算经理
需要提升的技能：资金管理、融资
行动：参加培训
时间：2024年底
========================================
（此文件格式不符合公司IDP标准，请重新制作）
"""
with open(os.path.join(base, "hr/idp_drafts/draft_zhao_lei_WRONG.txt"), "w", encoding="utf-8") as f:
    f.write(old_attempt)

print("Workspace setup complete.")
print("Files created:")
for d_item in distractors:
    print(f"  {d_item}")
print("  employee_assessment_raw.csv (main problem input)")
print("  hr/idp_drafts/draft_zhao_lei_WRONG.txt (red herring)")