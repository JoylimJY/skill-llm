import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
distractor_dirs = [
    "workspace/docs/internal/hr",
    "workspace/docs/internal/finance",
    "workspace/docs/technical/patents",
    "workspace/docs/technical/protocols",
    "workspace/projects/pharma_delivery/v1",
    "workspace/projects/pharma_delivery/v2_prototype",
    "workspace/projects/pharma_delivery/market_research",
    "workspace/admin/registrations",
    "workspace/admin/legal",
    "workspace/team/bios",
    "workspace/team/tasks",
    "workspace/external/investors",
    "workspace/external/partners",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d.replace("workspace/", "")), exist_ok=True)

# Distractor files
distractor_files = {
    "docs/internal/hr/team_roster.txt": "张明 - PhD candidate, Biomedical Engineering\n李雪 - MSc, Chemistry\n王浩 - MBA\n陈芳 - Undergrad, Biology",
    "docs/internal/finance/budget_draft.txt": "Q1 budget: 50,000 RMB\nLab consumables: 20,000\nSalaries: 0 (all students)\nTravel: 5,000",
    "docs/technical/patents/patent_notes.txt": "PCT application pending for nanoparticle formulation\nFiling date: 2023-11\nInventors: Prof. Liu Wei, Zhang Ming",
    "docs/technical/protocols/delivery_protocol_v3.txt": "Step 1: Synthesize lipid shell\nStep 2: Load active compound\nStep 3: Characterize particle size (target: 100-200nm)",
    "projects/pharma_delivery/v1/old_pitch.txt": "Draft pitch deck notes - OUTDATED\nMarket size: ??? billion\nCompetitors: unknown",
    "projects/pharma_delivery/v2_prototype/prototype_notes.txt": "Prototype achieved 85% encapsulation efficiency\nIn vitro results promising\nNeed animal testing facility access",
    "projects/pharma_delivery/market_research/competitor_list.txt": "Competitor A: Nanoform\nCompetitor B: Selecta Biosciences\nCompetitor C: Alnylam",
    "admin/registrations/company_name_ideas.txt": "NanoCure Tech\nBioDeliver Inc\nSmartDrug Solutions",
    "admin/legal/nda_template.txt": "NON-DISCLOSURE AGREEMENT TEMPLATE\n[Party A] and [Party B] agree to...",
    "team/bios/zhang_ming.txt": "Zhang Ming: PhD Year 3, focuses on lipid nanoparticles, 2 publications",
    "team/tasks/weekly_tasks.txt": "TODO:\n- Apply for lab time\n- Contact Prof Chen about animal facility\n- Prepare presentation",
    "external/investors/vc_list.txt": "Sequoia China, Matrix Partners, IDG Capital (general list - not targeted)",
    "external/partners/pharma_companies.txt": "Pfizer China, Novartis, Zhejiang Beta Pharma",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN INPUT: Messy team meeting notes (raw, unstructured, incomplete)
meeting_notes = """
团队会议记录 - 2024年3月15日
项目名称：纳米药物递送系统商业化
参会人员：张明（博士生，技术负责人）、李雪（硕士生）、王浩（MBA在读）、陈芳（本科生）

会议讨论内容（杂乱记录）：

== 我们现在有什么 ==
- 实验室：刘伟教授课题组，已经在用，但不确定是否可以更多时间
- 技术：已有专利申请（PCT），核心配方
- 团队：4人，来自生物医学工程系和MBA
- 已经参加过一次校内路演，拿了个三等奖
- 王浩之前在一家生物科技公司实习过，有点行业人脉

== 我们缺什么 / 需要找的资源 ==
- 缺钱！！需要至少50万来做动物实验和后续研究
- 需要动物实验设施 - 校内有没有可以用？
- 需要有人告诉我们怎么做商业模式，感觉我们都是技术背景
- 想找投资人，但不知道怎么接触
- 需要了解学校对老师和学生创业有什么政策，刘教授有点担心职称的事情
- 有家药企（浙江贝塔医药）说对我们技术感兴趣，但不知道怎么合作
- 想知道有没有什么政府补贴可以申请
- 王浩说听说清华x-lab有个什么驻校企业家项目，可以咨询

== 其他讨论 ==
- 陈芳问能不能用创业实践来换学分
- 张明问专利和成果转化怎么算，收益怎么分
- 刘教授说他愿意支持但需要了解保留教职的政策
- 大家觉得需要一个正式的资源规划，但不知道怎么写
- 下次会议定在4月1日

问题和疑虑：
1. 如果和浙江贝塔医药合作，核心技术知识产权怎么保护？
2. 政府补贴申请时间窗口是什么时候？
3. 找投资人之前是否需要先做什么准备？
"""

with open(os.path.join(workspace, "team_meeting_notes.txt"), "w", encoding="utf-8") as f:
    f.write(meeting_notes)

# Additional messy input: partial resource inventory (inconsistent format)
resource_inventory = """
Current Resource Inventory (incomplete draft)
=============================================
DATE: March 2024
STATUS: DRAFT - needs cleanup

资源类型 | 名称 | 状态 | 备注
---------|------|------|----
实验室空间 | 刘伟教授课题组实验室 | 部分可用 | 需要正式协议
专利 | PCT专利申请 | 进行中 | 2023年11月提交
校内路演奖项 | 校内创业大赛三等奖 | 已有 | x-lab组织的
行业人脉 | 王浩的行业联系 | 零散 | 来自实习

MISSING INFO:
- Don't know what government funds we qualify for
- Don't know x-lab services in detail
- Not sure about IP policy at our university
- Pharma partner terms unknown
"""

with open(os.path.join(workspace, "resource_inventory_draft.txt"), "w", encoding="utf-8") as f:
    f.write(resource_inventory)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")