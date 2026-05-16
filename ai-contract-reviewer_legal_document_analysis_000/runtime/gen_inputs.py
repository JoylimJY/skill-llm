import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/contracts/archive/2022",
    "workspace/contracts/archive/2023",
    "workspace/contracts/pending",
    "workspace/contracts/signed",
    "workspace/legal/templates/nda",
    "workspace/legal/templates/employment",
    "workspace/legal/notes",
    "workspace/admin/hr/onboarding",
    "workspace/admin/finance",
    "workspace/projects/client_a",
    "workspace/projects/client_b/docs",
    "workspace/tools/scripts",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "workspace/contracts/archive/2022/old_nda_template.txt": "NON-DISCLOSURE AGREEMENT TEMPLATE v1.0 - ARCHIVED - DO NOT USE",
    "workspace/contracts/archive/2023/vendor_agreement_draft.txt": "VENDOR AGREEMENT DRAFT - INCOMPLETE - pending legal review",
    "workspace/contracts/signed/client_a_2023_signed.txt": "SERVICE AGREEMENT - SIGNED - Client A - 2023 - [FULLY EXECUTED]",
    "workspace/contracts/pending/README_do_not_use.txt": "This folder contains pending contracts awaiting signature. Do not modify.",
    "workspace/legal/templates/nda/standard_nda_en.txt": "STANDARD NDA TEMPLATE - English Version - For reference only",
    "workspace/legal/templates/employment/emp_contract_template.txt": "EMPLOYMENT CONTRACT TEMPLATE - HR USE ONLY",
    "workspace/legal/notes/review_checklist.txt": "General review checklist (not for AI use): 1. Check dates 2. Check signatures 3. File correctly",
    "workspace/admin/hr/onboarding/welcome_packet.txt": "Welcome to the team! Please review your benefits package.",
    "workspace/admin/finance/invoice_template.txt": "INVOICE TEMPLATE #001 - Amount: ¥XXXX - Date: XXXX",
    "workspace/projects/client_a/project_spec.txt": "Project Alpha Specification - Confidential - Internal Use",
    "workspace/projects/client_b/docs/meeting_notes.txt": "Meeting notes 2024-01-15: Discussed scope changes, timeline adjustments.",
    "workspace/tools/scripts/convert_pdf.py": "# PDF conversion utility - placeholder\nprint('PDF converter not implemented')",
}

for path, content in distractors.items():
    (workspace / path).write_text(content, encoding="utf-8")

# Create a config file that looks like it might be relevant but is a distractor
config_data = {
    "version": "1.2.0",
    "review_settings": {
        "language": "auto",
        "output_format": "text",
        "risk_threshold": "medium"
    },
    "paths": {
        "input": "./contracts/pending",
        "output": "./reports"
    }
}
(workspace / "workspace/config.json").write_text(json.dumps(config_data, indent=2), encoding="utf-8")

# THE MAIN CONTRACT: A Chinese-language service agreement with multiple deliberate red flags
# This is the contract that needs to be reviewed
contract_text = """技术服务合同

合同编号：TSC-2024-0892

甲方（委托方）：北京创新科技有限公司
地址：北京市朝阳区建国路88号
法定代表人：张伟

乙方（服务方）：[自由职业者姓名]
身份证号：[XXXXXXXXXXXXXXXX]
联系方式：[电话/邮箱]

签订日期：2024年3月1日
合同期限：自2024年3月1日起至2025年2月28日止

第一条 服务内容

乙方应按照甲方要求提供以下技术服务：
1.1 为甲方开发和维护移动应用程序（iOS及Android平台）；
1.2 根据甲方需求进行系统架构设计与实施；
1.3 提供7×24小时技术支持，响应时间不超过1小时；
1.4 完成甲方随时提出的任何技术任务，无论是否在本合同约定范围内。

第二条 服务费用

2.1 甲方应向乙方支付服务费用，月费为人民币18,000元整。
2.2 付款方式：每月最后一个工作日完成当月服务后支付。
2.3 若乙方未能完全满足甲方对服务质量的主观判断，甲方有权扣减或拒绝支付当月全部费用，无需说明理由。
2.4 本合同到期后，若双方未提前30日书面通知对方，本合同将自动续期一年，且续期条款以届时甲方单方面确定的条款为准。

第三条 知识产权

3.1 乙方在合同期间完成的所有工作成果，包括但不限于代码、设计、文档、创意及改进方案，其全部知识产权归甲方独家所有。
3.2 乙方不得以任何形式主张对上述成果的任何权利。
3.3 乙方在合同期间产生的任何创意或发明，无论是否与本合同服务直接相关，均归甲方所有。

第四条 保密义务

4.1 乙方应对甲方的所有商业信息、技术信息、客户信息严格保密。
4.2 保密义务在合同终止后永久有效，没有时间限制。
4.3 若因乙方原因导致信息泄露，乙方须向甲方赔偿因此产生的一切损失，包括但不限于直接损失、间接损失、预期利润损失及商誉损失，赔偿金额不设上限。

第五条 竞业禁止

5.1 合同期间及合同终止后五年内，乙方不得以任何形式（包括但不限于受雇、合作、投资、咨询）在以下范围内为甲方竞争对手提供服务：
（一）中华人民共和国境内所有地区；
（二）亚太地区（包括但不限于日本、韩国、东南亚各国、澳大利亚）；
（三）甲方未来可能进入的任何业务领域。
5.2 竞争对手的认定由甲方单方面判断，乙方不得异议。
5.3 违反竞业禁止条款的，乙方须向甲方一次性支付违约金人民币500,000元，并赔偿甲方全部损失。

第六条 违约责任

6.1 乙方违约时，须向甲方赔偿由此产生的全部损失，赔偿金额无上限，包括甲方的间接损失、商誉损失及律师费用。
6.2 甲方违约时，仅需赔偿乙方当月已完成工作对应服务费用的30%。

第七条 合同变更

7.1 甲方有权在提前3日通知乙方的情况下，单方面修改本合同的任何条款，包括服务范围、费用标准及本条款本身，修改后的条款即时生效。
7.2 乙方如不接受变更，可在变更生效后30日内书面通知甲方终止合同，但须赔偿甲方因此产生的损失。

第八条 合同终止

8.1 甲方可提前3日通知乙方终止本合同，无需说明原因，无需支付违约金。
8.2 乙方如需提前终止合同，须提前90日书面通知甲方，并赔偿甲方相当于剩余合同期服务费用50%的违约金。

附件：无

（合同未尽事宜，以中国相关法律法规为准。）

甲方签章：_______________        乙方签字：_______________
日期：_______________            日期：_______________
"""

# Save the contract to the pending folder
contract_path = workspace / "workspace/contracts/pending/TSC-2024-0892_service_agreement.txt"
contract_path.write_text(contract_text, encoding="utf-8")

# Also create a misleading "previous report" file to confuse the agent
old_report = """DRAFT RISK SUMMARY (INCOMPLETE - DO NOT USE)
Contract: TSC-2024-0892
Date: Preliminary scan only
Risk: Unknown - full analysis pending
Status: INCOMPLETE
"""
(workspace / "workspace/legal/notes/TSC-2024-0892_draft_notes.txt").write_text(old_report, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Contract file: workspace/contracts/pending/TSC-2024-0892_service_agreement.txt")