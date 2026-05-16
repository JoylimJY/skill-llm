import os
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic law firm directory structure with distractor files
dirs = [
    "cases/2024/civil",
    "cases/2024/criminal",
    "cases/2023/archived",
    "templates/contracts",
    "templates/pleadings",
    "research/judicial_interpretations",
    "research/academic_papers",
    "tools/analysis_frameworks",
    "client_files/pending",
    "client_files/closed",
    "admin/billing",
    "admin/correspondence",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# 1. An unrelated contract template
with open(os.path.join(workspace, "templates/contracts/purchase_agreement_template.md"), "w", encoding="utf-8") as f:
    f.write("# 买卖合同模板\n\n甲方：______\n乙方：______\n\n## 第一条 标的物\n\n## 第二条 价款\n\n## 第三条 交付\n")

# 2. An unrelated pleading template
with open(os.path.join(workspace, "templates/pleadings/civil_complaint_template.md"), "w", encoding="utf-8") as f:
    f.write("# 民事起诉状模板\n\n原告：\n被告：\n\n诉讼请求：\n1.\n2.\n\n事实与理由：\n")

# 3. Old case notes (distractor)
with open(os.path.join(workspace, "cases/2023/archived/case_2023_0451_notes.txt"), "w", encoding="utf-8") as f:
    f.write("案件编号：2023-民初-0451\n当事人：张某 vs 某公司\n争议焦点：劳动合同解除\n结案时间：2023-11-15\n结果：调解结案\n")

# 4. A judicial interpretation document (distractor, different article)
with open(os.path.join(workspace, "research/judicial_interpretations/spc_2021_contract_law.txt"), "w", encoding="utf-8") as f:
    f.write("《最高人民法院关于适用〈中华人民共和国民法典〉合同编通则若干问题的解释》\n\n第一条 合同的订立...\n第二条 格式条款的认定...\n注意：此文件仅供参考，请以官方文本为准。\n")

# 5. Academic paper snippet (distractor)
with open(os.path.join(workspace, "research/academic_papers/format_clauses_analysis_2022.txt"), "w", encoding="utf-8") as f:
    f.write("格式条款的司法规制研究\n\n摘要：本文从比较法角度分析格式条款的效力认定问题...\n关键词：格式条款、不公平条款、消费者保护\n\n一、引言\n格式条款（又称标准条款）在现代商业活动中广泛存在...\n")

# 6. Analysis framework (distractor - generic, NOT the proprietary 7-step)
with open(os.path.join(workspace, "tools/analysis_frameworks/generic_legal_analysis.txt"), "w", encoding="utf-8") as f:
    f.write("通用法律分析框架（旧版）\n\n步骤一：识别法律问题\n步骤二：查找适用法律\n步骤三：分析案件事实\n步骤四：得出结论\n\n注：此框架已被新版七步法工作流替代，请勿使用。\n")

# 7. Client correspondence (distractor)
with open(os.path.join(workspace, "client_files/pending/client_wang_inquiry.txt"), "w", encoding="utf-8") as f:
    f.write("客户：王某某\n咨询时间：2024-03-10\n咨询内容：购买二手房时，中介合同中有一条款声称中介费不予退还，即使房屋交易未成功。客户询问该条款是否有效。\n负责律师：待分配\n")

# 8. Billing records (distractor)
with open(os.path.join(workspace, "admin/billing/2024_q1_invoices.txt"), "w", encoding="utf-8") as f:
    f.write("2024年第一季度账单记录\n\n客户A：服务费 15,000元，已付\n客户B：服务费 28,000元，待付\n客户C：服务费 9,500元，已付\n")

# 9. Correspondence (distractor)
with open(os.path.join(workspace, "admin/correspondence/court_notice_2024_0312.txt"), "w", encoding="utf-8") as f:
    f.write("北京市朝阳区人民法院\n\n传票\n\n案件编号：（2024）京0105民初×××号\n\n请于2024年4月15日上午9:00准时出庭。\n")

# 10. Another pending case (distractor)
with open(os.path.join(workspace, "cases/2024/civil/case_2024_0089_brief.txt"), "w", encoding="utf-8") as f:
    f.write("案件编号：2024-民初-0089\n当事人：李某 vs 某电商平台\n争议焦点：产品质量责任\n关联法条：民法典第1203条\n案件状态：一审\n")

# 11. A criminal case note (distractor)
with open(os.path.join(workspace, "cases/2024/criminal/case_2024_cr_012.txt"), "w", encoding="utf-8") as f:
    f.write("刑事案件记录\n编号：2024-刑-012\n罪名：合同诈骗罪\n刑法条文：第224条\n辩护要点：主观故意的认定\n")

# --- MAIN TASK INPUT: The case brief with the messy, realistic inputs ---

case_brief_content = """律所内部案件分析任务单
===============================
编号：2024-格式条款-007
负责律师：（待分配）
接案日期：2024年6月3日
优先级：高
===============================

【案件背景】
委托人：陈某（消费者）
对方当事人：某网络金融科技有限公司（以下简称"金融公司"）

【纠纷概述】
陈某于2023年9月通过金融公司App申请了一笔消费贷款。签约时，App界面要求陈某勾选同意《用户服务协议》，协议共计68页，字体极小。其中第47条第3款规定："用户一旦发生逾期，公司有权将用户个人信息（包括但不限于姓名、工作单位、紧急联系人信息）提供给第三方催收机构，用户不得以任何理由要求公司承担任何责任。"陈某当时并未实际阅读该条款。

2024年2月，陈某因收入减少，出现3天逾期（后已还款）。金融公司随即将其信息提供给催收机构，催收人员多次联系陈某家人及工作单位，造成陈某严重困扰，并被单位辞退。

陈某主张该条款系格式条款，金融公司未尽提示说明义务，该条款无效。金融公司反驳称陈某已勾选同意，条款有效。

【核心争议法条】
请重点分析以下法条：

《中华人民共和国民法典》第四百九十六条

原文：
"格式条款是当事人为了重复使用而预先拟定，并在订立合同时未与对方协商的条款。
采用格式条款订立合同的，提供格式条款的一方应当遵循公平原则确定当事人之间的权利和义务，并采取合理的方式提示对方注意免除或者限制其责任的条款，按照对方的要求，对该条款予以说明。提供格式条款的一方未履行提示或者说明义务，致使对方没有注意或者理解与其有重大利害关系的条款，对方可以主张该条款不成为合同的内容。"

【额外背景信息（可能有用，也可能无关）】
- 《个人信息保护法》第十三条：处理个人信息应当取得个人同意，但"格式同意"是否构成真实同意存在争议。
- 相关司法解释：最高人民法院于2023年12月发布《关于适用〈中华人民共和国民法典〉合同编通则若干问题的解释》，其中第9条至第11条对格式条款的提示说明义务有进一步规定（注意：此解释为新规，AI训练数据可能未涵盖）。
- 参考案例（未经核验）：北京互联网法院（2023）京0491民初12345号——某平台格式条款纠纷案，法院认定平台未尽提示义务，条款无效。（注意：此案例真实性未经核验）

【任务要求】
请对上述法条运用本律所标准分析协议，生成完整的法条分析报告，文件命名为 legal_analysis_report.md，存放于 cases/2024/civil/ 目录下。

报告必须涵盖从结构拆解到决策固化的全流程分析，并明确标注各步骤的质量检验点。

律所合伙人特别提示：上方参考案例的真实性尚未核验，报告中必须体现对此的专业处理。
"""

with open(os.path.join(workspace, "cases/2024/civil/case_2024_007_brief.txt"), "w", encoding="utf-8") as f:
    f.write(case_brief_content)

print("Workspace setup complete.")
print("Directory structure:")
for root, dirs_list, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')