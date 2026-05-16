import os
import random
import json

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "hr_system/payroll/2025",
    "hr_system/payroll/2024",
    "hr_system/benefits/social_insurance",
    "hr_system/benefits/housing_fund",
    "hr_system/reports/monthly",
    "hr_system/reports/annual",
    "finance/tax/filings",
    "finance/tax/receipts",
    "finance/budgets",
    "legal/contracts",
    "admin/templates",
    "admin/forms",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "hr_system/payroll/2024/salary_template_OLD.csv": "name,base,bonus\nPlaceholder,0,0\n",
    "hr_system/payroll/2024/tax_rates_2018.json": json.dumps({
        "note": "OUTDATED 2018 rates, do not use",
        "brackets": [3500, 10000, 30000, 70000, 110000, 160000]
    }, ensure_ascii=False, indent=2),
    "hr_system/benefits/social_insurance/rules_draft.txt": (
        "Draft rules - NOT FINAL\n"
        "Beijing: pension 8%, medical 2%, unemployment 0.3%\n"
        "WARNING: These numbers are WRONG, verify with official sources\n"
    ),
    "hr_system/benefits/housing_fund/shenzhen_2023.txt": (
        "Shenzhen Housing Fund 2023 (EXPIRED)\n"
        "Employee contribution: 7% (CHANGED - verify current rate)\n"
    ),
    "hr_system/reports/monthly/oct_2025_draft.csv": (
        "id,name,gross\n001,张三,28000\n002,李四,22000\n"
    ),
    "hr_system/reports/annual/2024_summary.txt": (
        "2024 Annual Tax Summary\nTotal employees: 127\nAverage tax rate: 12.3%\n"
        "NOTE: Calculated under old rules, do not use for 2025\n"
    ),
    "finance/tax/filings/q3_2025.txt": (
        "Q3 2025 Corporate Tax Filing\nIIT withheld: CNY 4,567,890\nStatus: Filed\n"
    ),
    "finance/tax/receipts/bonus_2024.txt": (
        "2024 Year-end Bonus Tax Receipts\nTotal bonus pool: CNY 8,200,000\n"
        "Note: Several employees triggered bonus traps, review needed\n"
    ),
    "finance/budgets/2025_q4_plan.csv": (
        "department,headcount,bonus_budget\nEngineering,45,2000000\nProduct,20,800000\nHR,10,350000\n"
    ),
    "legal/contracts/template_v3.txt": (
        "Employment Contract Template v3\n[EMPLOYEE NAME]\nBase Salary: [AMOUNT]\n"
        "Bonus: Discretionary, subject to performance\n"
    ),
    "admin/templates/offer_letter_template.txt": (
        "Dear [NAME],\nWe are pleased to offer you...\nGross Monthly Salary: [AMOUNT] CNY\n"
        "Note: Individual income tax will be withheld per applicable regulations.\n"
    ),
    "admin/forms/deduction_claim_form_2024.txt": (
        "Special Additional Deduction Claim Form 2024\nEmployee: ___\n"
        "Children Education: ___ yuan/month\nHousing Loan Interest: ___ yuan/month\n"
        "WARNING: 2024 form, amounts may have changed for 2025\n"
        "Old 2024 child deduction: 1000 yuan/child/month (OUTDATED)\n"
    ),
}

for fpath, content in distractor_files.items():
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

# === THE MAIN PROBLEM FILE ===
# Messy, inconsistent employee CSV with deliberate issues:
# - Bonuses in trap zones (36001, 144500, 300500)
# - Mixed formatting (spaces, different decimal styles)
# - Family situations described in natural language (not template names)
# - City names with inconsistency

employee_csv = """员工ID,姓名,城市,月薪(税前),月度五险一金(个人缴纳),年终奖(拟定),家庭情况
E001,陈晓明,北京,35000,7000,36001,"已婚，一个孩子在上小学，有首套房贷，需赡养父母（独生子女）"
E002,王芳,上海,22000,4400,144500,"单身，租房住，无房贷"
E003,刘建国,深圳,48000,5760,300500,"已婚，两个孩子（一个3岁一个7岁），有首套房贷"
E004,赵丽,广州,18000,2700,60000,"已婚，无孩，有首套房贷"
E005,孙伟,杭州,55000,11000,200000,"已婚，一个孩子在读初中，有首套房贷，需赡养父母（独生子女）"
E006,周明,成都,28000,4200,96000,"在读在职研究生，单身，租房"
"""

with open("hr_system/payroll/2025/employees_yearend_2025.csv", "w", encoding="utf-8") as f:
    f.write(employee_csv)

# Also create a notes file with some red-herring information
notes_content = """年终奖发放注意事项 - 2025年度（草稿，未经审核）

一、关于年终奖个税计算
方案A：合并计税 - 将年终奖并入当年综合所得计算
方案B：单独计税 - 年终奖单独适用月度税率表（除以12）

注意：根据旧政策（2021年），某些金额节点可能导致税负激增。
具体节点详见税务局官网（链接已失效）。

二、社保缴纳基数
各城市不同，请联系当地社保局核实。
（注意：此文件中的比例仅供参考，实际以当地规定为准）
北京养老：个人8%？存疑
上海公积金：个人7%？存疑

三、专项附加扣除（2025年度）
子女教育：每月每孩1000元（注：此为旧标准，请核实2025年新标准）
住房贷款利息：每月1000元（待核实）
赡养老人：独生子女每月2000元（注：此数字可能有误）

此文件仅供内部讨论，请勿作为正式依据。
"""

with open("hr_system/payroll/2025/bonus_notes_DRAFT.txt", "w", encoding="utf-8") as f:
    f.write(notes_content)

print("Workspace generated successfully.")
print("Main input file: hr_system/payroll/2025/employees_yearend_2025.csv")