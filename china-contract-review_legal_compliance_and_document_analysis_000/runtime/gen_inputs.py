import os
import random
from pathlib import Path
from docx import Document

random.seed(42)

workspace = Path("/workspace")

# --- Create a realistic, nested directory structure with distractor files ---

dirs = [
    "hr_department/contracts/drafts",
    "hr_department/contracts/signed",
    "hr_department/templates",
    "hr_department/policies",
    "legal_team/archive/2023",
    "legal_team/archive/2024",
    "legal_team/references",
    "finance/payroll",
    "finance/reports",
    "admin/company_info",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

distractor_texts = {
    "hr_department/policies/leave_policy.txt": "年假政策：员工工作满1年享有5天年假，满3年10天，满10年15天。",
    "hr_department/policies/code_of_conduct.txt": "员工行为准则：遵守公司规章制度，保守公司商业秘密，维护公司形象。",
    "hr_department/templates/offer_letter_template.txt": "录用通知书模板：兹通知您已被本公司录用，担任XX职位，月薪XX元。",
    "hr_department/contracts/signed/contract_zhang_wei_2023.txt": "张伟劳动合同（已签署归档）- 合同编号: ZW-2023-001",
    "hr_department/contracts/signed/contract_li_fang_2024.txt": "李芳劳动合同（已签署归档）- 合同编号: LF-2024-008",
    "legal_team/archive/2023/case_notes_q3.txt": "2023年Q3法律事务记录：处理劳动纠纷3起，合同审查12份。",
    "legal_team/archive/2024/regulatory_updates.txt": "2024年劳动法规更新要点：最低工资标准调整，社保基数变更通知。",
    "legal_team/references/labor_law_excerpts.txt": "《中华人民共和国劳动合同法》部分条文摘录（仅供参考，不构成法律建议）",
    "finance/payroll/payroll_march_2025.csv": "员工姓名,工号,基本工资,社保扣除,实发工资\n王磊,EMP001,8000,800,7200\n陈静,EMP002,12000,1200,10800",
    "finance/reports/q1_2025_hr_cost.txt": "2025年Q1人力资源成本报告：总薪酬支出320万元，社保公积金支出68万元。",
    "admin/company_info/business_license.txt": "营业执照信息：公司名称：北京星辰科技有限公司，注册资本：1000万元人民币",
    "admin/company_info/org_chart.txt": "组织架构：CEO -> CTO/CFO/CHO -> 各部门总监 -> 员工",
}

for rel_path, content in distractor_texts.items():
    (workspace / rel_path).write_text(content, encoding="utf-8")

# --- CREATE THE PROBLEM: A labor contract draft with multiple legal issues ---
# Issues planted:
# 1. 试用期12个月（合同期3年）- 违反劳动合同法第19条（3年合同试用期最长6个月）
# 2. 违约金条款：提前离职赔偿20万元 - 违反劳动合同法第25条（劳动者违约金仅限培训服务期和竞业限制）
# 3. 未提及社会保险缴纳义务 - 违反劳动合同法第17条（必备条款）及社会保险法
# 4. 工作时间：每天10小时，每周6天 - 违反劳动法第36条（标准工时每日8小时，每周40小时）
# 5. 竞业限制期限3年 - 违反劳动合同法第24条（最长不超过2年）

doc = Document()

doc.add_heading('劳动合同', 0)

doc.add_paragraph('合同编号：BXKJ-2025-HR-009')
doc.add_paragraph('甲方（用人单位）：北京星辰科技有限公司')
doc.add_paragraph('乙方（劳动者）：赵明')
doc.add_paragraph('签订日期：2025年6月1日')

doc.add_heading('第一条 合同期限', level=1)
doc.add_paragraph(
    '本合同期限为固定期限合同，自2025年7月1日起至2028年6月30日止，合同期限共计3年。'
    '其中试用期为12个月，自2025年7月1日起至2026年6月30日止。'
    '试用期间甲方可随时解除劳动合同，无需支付任何补偿。'
)

doc.add_heading('第二条 工作内容与工作地点', level=1)
doc.add_paragraph(
    '乙方担任高级软件工程师职位，负责公司核心产品的研发工作。'
    '工作地点为北京市海淀区中关村科技园区，甲方有权根据业务需要调整乙方工作地点。'
)

doc.add_heading('第三条 工作时间', level=1)
doc.add_paragraph(
    '乙方实行综合计算工时工作制，每日工作时间为10小时，每周工作6天，每周工作时间共计60小时。'
    '加班不另行支付加班费，视为包含在月薪中。'
)

doc.add_heading('第四条 劳动报酬', level=1)
doc.add_paragraph(
    '试用期月薪为人民币15,000元整。'
    '转正后月薪为人民币20,000元整，含基本工资18,000元及岗位津贴2,000元。'
    '工资于每月15日以银行转账方式支付。'
)

doc.add_heading('第五条 违约责任', level=1)
doc.add_paragraph(
    '乙方在合同期内，如无正当理由提前解除劳动合同，须向甲方支付违约金人民币200,000元（二十万元整）。'
    '如因乙方过失导致甲方遭受损失超过违约金金额，乙方须赔偿实际损失。'
)

doc.add_heading('第六条 保密义务', level=1)
doc.add_paragraph(
    '乙方在职期间及离职后均有义务保守甲方商业秘密。'
    '乙方不得向任何第三方披露甲方的技术方案、客户信息、经营数据等保密信息。'
)

doc.add_heading('第七条 竞业限制', level=1)
doc.add_paragraph(
    '乙方离职后3年内，不得在与甲方存在竞争关系的企业任职，'
    '不得自行或协助他人从事与甲方相同或类似的业务。'
    '竞业限制期间甲方每月支付补偿金人民币3,000元。'
)

doc.add_heading('第八条 合同解除与终止', level=1)
doc.add_paragraph(
    '双方协商一致可解除本合同。甲方依法享有单方解除权。'
    '合同到期后，如双方未续签，合同自然终止。'
)

doc.add_heading('第九条 争议解决', level=1)
doc.add_paragraph(
    '因本合同引发的劳动争议，双方应协商解决；协商不成的，可向有管辖权的劳动仲裁委员会申请仲裁。'
)

doc.add_heading('第十条 其他', level=1)
doc.add_paragraph(
    '本合同未尽事宜，依照国家有关法律法规执行。'
    '本合同一式两份，甲乙双方各执一份，具有同等法律效力。'
)

doc.add_paragraph('\n甲方代表（签章）：___________    乙方（签字）：___________')
doc.add_paragraph('日期：___________              日期：___________')

contract_path = workspace / "hr_department/contracts/drafts/labor_contract_zhao_ming_draft.docx"
doc.save(str(contract_path))

print(f"Contract draft created at: {contract_path}")
print("Workspace setup complete.")
print("\nPlanted legal issues summary:")
print("1. 试用期12个月（3年合同最长6个月）- 违反劳动合同法第19条")
print("2. 违约金20万（劳动者仅在培训/竞业限制时可约定）- 违反劳动合同法第25条")
print("3. 未规定社会保险缴纳 - 违反劳动合同法第17条")
print("4. 每日10小时每周60小时 - 违反劳动法第36条")
print("5. 竞业限制3年 - 违反劳动合同法第24条（最长2年）")