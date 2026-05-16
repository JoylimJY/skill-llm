import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
distractor_dirs = [
    "workspace/admin/archive/2024",
    "workspace/admin/templates",
    "workspace/team/members/profiles",
    "workspace/team/meetings/notes",
    "workspace/research/market/reports",
    "workspace/research/tech/patents",
    "workspace/finance/budget/q1",
    "workspace/finance/projections",
    "workspace/assets/images",
    "workspace/assets/videos",
    "workspace/references/gov_docs",
    "workspace/references/past_entries",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/admin/archive/2024/old_submission.txt": "2024年参赛项目存档，已过期。赛道：创业组。得分：78分。",
    "workspace/admin/templates/cover_letter.txt": "尊敬的评审老师，您好。附件为我团队参赛材料，请审阅。",
    "workspace/team/members/profiles/member1.txt": "姓名：张伟\n学历：本科在读\n专业：计算机科学\n角色：技术负责人",
    "workspace/team/members/profiles/member2.txt": "姓名：李梅\n学历：本科在读\n专业：工商管理\n角色：市场负责人",
    "workspace/team/meetings/notes/kickoff.txt": "会议时间：2025-01-10\n议题：项目立项讨论\n结论：确定赛道，分工明确",
    "workspace/research/market/reports/market_size_2024.txt": "中国农村电商市场规模2024年达8000亿元，年增长率约15%。",
    "workspace/research/tech/patents/pending_patent.txt": "专利申请编号：CN202510XXXXXX\n名称：一种智能农业监测系统\n状态：实质审查中",
    "workspace/finance/budget/q1/q1_expenses.csv": "类别,金额(元)\n人力成本,5000\n设备采购,8000\n市场推广,3000",
    "workspace/finance/projections/revenue_forecast.txt": "预计第一年营收：50万元\n第二年营收：200万元\n第三年营收：800万元",
    "workspace/assets/images/placeholder.txt": "[图片占位符：请替换为实际项目图片]",
    "workspace/references/gov_docs/education_ministry_notice.txt": "教育部办公厅关于举办中国国际大学生创新大赛（2025）的通知（摘要）\n各省级教育行政部门...",
    "workspace/references/past_entries/2023_winner_summary.txt": "2023年金奖项目概况：清洁能源领域，产业赛道，团队5人，营收300万。",
    "workspace/admin/templates/scoring_notes_WRONG.txt": "【注意：此文件为旧版评分标准，已作废，请勿参考】\n创意组：创新60分，团队40分\n创业组：营收50分，创新50分",
    "workspace/research/market/reports/competitor_analysis.txt": "竞争对手分析：\n1. 公司A：估值5亿，主营B2B农业SaaS\n2. 公司B：月活10万，主营C端农产品电商",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Project A: Matches 高教主赛道-创业组 ---
# Already has a company, undergraduate + graduate students, tech innovation
project_a = """项目名称：智农云——面向中小农场的智能化管理SaaS平台

项目简介：
智农云是一款为中小型农场主提供精准农业管理服务的SaaS软件平台，整合了物联网传感器数据采集、AI病虫害识别、天气预警和市场价格预测功能。平台已于2024年3月完成工商注册，公司名称为"智农云科技有限公司"，注册资本50万元。

团队构成：
- 队长：陈明（农业大学农学院大三本科生）
- 技术负责人：黄杰（计算机学院大四本科生）
- 产品经理：王芳（管理学院研究生一年级）
- 市场负责人：刘涛（工商管理大三本科生）
- 顾问：李教授（农学院副教授，指导老师）

项目阶段：
公司成立后已完成MVP版本开发，签约3家农场试用客户，累计合同金额12万元，获得一项软件著作权。

行业背景：
中国农业数字化转型市场庞大，但中小农场主缺乏低成本智能化管理工具。现有解决方案价格昂贵且操作复杂，不适合中小规模农场。

核心创新：
1. 自研边缘计算模型，适配低成本IoT设备，降低农场接入门槛
2. 基于历史农业数据训练的病虫害早期预警AI模型（准确率92%）
3. 订阅制SaaS模式，月费仅为市场同类产品的30%

参赛诉求：
请帮助分析我们应参加哪个赛道和组别，并提供该赛道的完整评分标准及专业参赛建议，以及适合该赛道的PPT章节结构列表。请将全部分析结果输出到 competition_guidance.json 文件中。
"""

# --- Project B: Matches 青年红色筑梦之旅赛道-公益组 ---
# Non-profit, rural revitalization, not-for-profit social innovation
project_b = """项目名称：红心助农——山区留守老人农产品助销公益平台

项目简介：
红心助农是一个专注于帮助偏远山区留守老人销售自产农副产品的公益平台。项目由大学生志愿者团队发起，通过直播带货、社区团购和爱心义购等方式，帮助山区老人对接城市消费者，改善其生活状况。项目不以盈利为目的，所有收益扣除运营成本后全部返还给农户。团队目前无公司主体，以大学志愿者协会形式运作。

团队构成：
- 负责人：赵婷（师范大学中文系大二本科生）
- 运营：孙磊（新闻传播学院大二本科生）
- 技术：周强（计算机学院大三本科生）
- 社工：吴丽（社会工作学院大三本科生）

项目背景：
项目在湖南省某山区县开展，深入挖掘当地红色文化资源（该县是革命老区），将红色精神融入公益品牌建设。已累计帮助47户留守老人家庭，销售农产品总值达28万元，带动直接受益人口约120人。

社会影响：
- 多次在当地主流媒体报道
- 入选省级大学生志愿服务优秀案例
- 与当地乡村振兴局建立合作关系

参赛诉求：
请帮助分析我们应参加哪个赛道和组别，并提供该赛道的完整评分标准及专业参赛建议，以及适合该赛道的PPT章节结构列表。请将全部分析结果输出到 competition_guidance.json 文件中。
"""

# Write project files
project_a_path = os.path.join(workspace, "project_alpha_description.txt")
project_b_path = os.path.join(workspace, "project_beta_description.txt")

with open(project_a_path, "w", encoding="utf-8") as f:
    f.write(project_a)

with open(project_b_path, "w", encoding="utf-8") as f:
    f.write(project_b)

# Write a task manifest that describes what needs to be done
task_manifest = """任务说明
========

我们有两个待参赛项目，分别描述在以下文件中：
- project_alpha_description.txt （智农云项目）
- project_beta_description.txt （红心助农项目）

请对两个项目进行赛道分析，并将完整的参赛指导信息整合输出到单个文件：competition_guidance.json

该文件应包含两个项目各自的参赛赛道、评分标准和PPT结构等信息。
"""

with open(os.path.join(workspace, "TASK_MANIFEST.txt"), "w", encoding="utf-8") as f:
    f.write(task_manifest)

print("Workspace generation complete.")
print(f"Created project files: project_alpha_description.txt, project_beta_description.txt")
print(f"Created {len(distractors)} distractor files in nested directories")