import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a deeply nested directory structure with distractor files
dirs = [
    "hr_system/candidates/2024",
    "hr_system/candidates/2025/pending",
    "hr_system/candidates/2025/reviewed",
    "hr_system/templates/email",
    "hr_system/templates/resume",
    "hr_system/internal/meeting_notes",
    "hr_system/internal/policies",
    "hr_system/outbox/sent",
    "hr_system/outbox/drafts",
    "hr_system/reports/q1",
    "hr_system/reports/q2",
    "archive/2023/candidates",
    "archive/2023/emails",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files — realistic but irrelevant
distractor_files = {
    "hr_system/internal/policies/leave_policy.txt": "年假政策：员工入职满一年可享受年假5天，每增加一年增加1天，最多15天。",
    "hr_system/internal/policies/onboarding.txt": "新员工入职流程：1. 签署劳动合同 2. 配置办公设备 3. 参加入职培训 4. 与导师对接",
    "hr_system/internal/meeting_notes/2025_01_15.txt": "会议纪要：讨论Q1招聘计划，目标岗位：产品经理2名，研发工程师5名，运营专员1名。",
    "hr_system/internal/meeting_notes/2025_02_20.txt": "会议纪要：审核2024年度绩效，确定晋升名单，讨论薪资调整方案。",
    "hr_system/templates/email/interview_invite_template.txt": "尊敬的[姓名]：感谢您投递[职位]岗位，我们诚邀您参加面试，请于[时间]前往[地点]。",
    "hr_system/templates/resume/standard_format.txt": "标准简历格式：个人信息、教育背景、工作经历、项目经验、技能证书",
    "hr_system/candidates/2024/zhang_wei_reviewed.txt": "张伟 - 已通过初筛 - 产品经理岗位 - 5年经验",
    "hr_system/candidates/2024/li_na_rejected.txt": "李娜 - 未通过 - 经验不足",
    "hr_system/reports/q1/recruitment_summary.txt": "Q1招聘报告：共收到简历156份，初筛通过32份，面试18人，录用6人。",
    "hr_system/reports/q2/pipeline_status.txt": "Q2招聘进度：产品经理岗位已关闭，研发工程师还有3个HC，运营专员面试中。",
    "archive/2023/candidates/batch_processed.txt": "2023年批量处理记录：共润色简历87份，邮件32份",
    "archive/2023/emails/outreach_log.txt": "2023外联邮件记录：发送猎头邮件120封，校招邮件340封",
    "hr_system/outbox/sent/weekly_report.txt": "本周发送邮件统计：面试邀请12封，拒信8封，offer3封",
}

for path, content in distractor_files.items():
    (workspace / path).write_text(content, encoding="utf-8")

# =====================================================================
# THE ACTUAL PROBLEM FILES - messy, unpolished Chinese writing samples
# =====================================================================

# Sample 1: A badly written resume (简历) - needs verb-first, quantification, and cleanup
resume_draft = """姓名：陈思远
应聘岗位：市场营销经理

工作经历：

某互联网公司（2021年-2024年）
- 我在那里主要是负责了公司的一些社交媒体账号的运营工作，包括微博啊微信什么的，然后粉丝方面也有一定的增长。
- 然后我还有参与过一个比较大的营销活动的策划，那个活动还是比较成功的，销售额也提升了不少。
- 平时也会写一些文章什么的，发布在公众号上面，用户们都挺喜欢看的，阅读量还可以。

某广告公司（2019年-2021年）
- 主要是做一些广告方案的，帮助客户做品牌推广方面的工作。
- 和客户沟通方面做的也不错，续签合同的客户挺多的。
- 团队里面有几个人是我在管的，配合还可以。

教育背景：
北京某大学市场营销专业本科毕业，成绩还行，获得过一些奖学金。

技能：
会用一些办公软件，英语也还可以，有驾照。
"""

# Sample 2: A badly written business email (邮件)
email_draft = """你好，

我是ABC公司的王明，我想给你们发这封邮件是因为我们公司有一个合作的想法想要跟你们谈谈，我觉得这个对双方来说都是有好处的。

我们公司是做软件开发的，已经做了挺长时间了，在这个行业还是有一定的经验和实力的。然后我之前有了解过你们公司，感觉你们在人工智能这块做的挺好的，所以就想到了是不是可以合作一下。

具体的合作方式的话，我们可以找时间坐下来好好谈谈，我这边时间比较灵活，你们方便的话可以定个时间见面聊聊，如果方便的话也可以先发个资料给我看看，反正随你们。

王明
"""

# Sample 3: A badly written formal article/essay (文章)
article_draft = """关于企业数字化转型的一些想法

现在这个时代，数字化这个词非常非常的热门，很多企业都在说要进行数字化转型，但是真正做好的企业其实没有多少，大部分的企业在数字化转型的过程当中都遇到了各种各样的问题和困难，这些问题有的是技术层面的，有的是管理层面的，也有的是观念层面的。

首先我们来说说技术层面的问题。很多企业的IT基础设施比较落后，老旧的系统跟新的数字化系统之间的兼容性很差，这就导致了数据没有办法很好的流通，形成了一个个的信息孤岛，这个问题其实是很严重的，因为数据如果没有办法流通的话，那数字化也就没有什么意义了。

然后是管理层面，企业里面的各个部门都有自己的利益考量，在推进数字化的过程中经常会出现各部门之间互相不配合，互相推诿的情况，这就导致项目推进非常的缓慢甚至是失败。

最后是观念层面的问题，很多企业的领导层对数字化的认识不够深刻，只是觉得数字化是一个非常时髦的东西，跟风去做，但是并没有真正的想清楚自己的企业到底需要什么样的数字化，这样的话数字化转型就很难成功。

总的来说，企业数字化转型是一个很复杂的系统性工程，需要从技术、管理、观念等多个层面同时发力，才能真正的取得成功。
"""

# Write the problem files to the pending directory
(workspace / "hr_system/candidates/2025/pending/resume_draft_chensiyuan.txt").write_text(
    resume_draft, encoding="utf-8"
)
(workspace / "hr_system/outbox/drafts/cooperation_email_draft.txt").write_text(
    email_draft, encoding="utf-8"
)
(workspace / "hr_system/internal/meeting_notes/digital_transformation_article_draft.txt").write_text(
    article_draft, encoding="utf-8"
)

# Create a task manifest file telling the agent what to process
task_manifest = """待处理文件清单
====================

以下三份文件需要进行专业润色处理，请逐一处理并将结果保存到指定输出文件。

1. 简历文件：hr_system/candidates/2025/pending/resume_draft_chensiyuan.txt
   - 输出文件名：polished_resume_chensiyuan.txt

2. 邮件草稿：hr_system/outbox/drafts/cooperation_email_draft.txt
   - 输出文件名：polished_email_cooperation.txt

3. 文章草稿：hr_system/internal/meeting_notes/digital_transformation_article_draft.txt
   - 输出文件名：polished_article_digital_transformation.txt

所有输出文件请统一放在：hr_system/candidates/2025/reviewed/ 目录下。
"""

(workspace / "hr_system/task_manifest.txt").write_text(task_manifest, encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*.txt")):
    print(f"  {f.relative_to(workspace)}")