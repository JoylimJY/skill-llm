import os
import random

random.seed(42)

# Create the workspace directory structure
base = "/workspace"
os.makedirs(base, exist_ok=True)

# Create distractor directories and files
distractor_dirs = [
    "archive/2022/q1",
    "archive/2022/q2",
    "archive/2023/q3",
    "templates/standard",
    "templates/urgent",
    "internal/memos",
    "internal/reports",
    "drafts/pending",
    "drafts/reviewed",
    "assets/images_refs",
    "assets/data_tables",
    "style_guides",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "archive/2022/q1/newsletter_jan.txt": "元月通讯已归档。包含春节特别报道和社区活动信息。",
    "archive/2022/q2/newsletter_apr.txt": "四月通讯已归档。包含清明节活动和城市绿化报告。",
    "archive/2022/q2/newsletter_jun.txt": "六月通讯。城市更新项目进展报告。",
    "archive/2023/q3/newsletter_sep.txt": "九月通讯。秋季城市规划展览回顾。",
    "templates/standard/cover_letter.txt": "标准封面信模板。适用于一般城市项目公告。",
    "templates/standard/press_release.txt": "新闻稿模板。适用于重大项目启动通告。",
    "templates/urgent/emergency_notice.txt": "紧急通知模板。适用于突发城市事件。",
    "internal/memos/style_policy_2023.txt": "编辑风格政策备忘录。所有对外发布文件须经总编审核。",
    "internal/memos/submission_deadlines.txt": "投稿截止时间表。每月25日为截止日期。",
    "internal/reports/readership_survey_2023.txt": "读者调查报告2023。调查显示读者更偏好简洁、直接的表达方式。",
    "drafts/reviewed/march_feature_approved.txt": "三月特刊已审核通过，待排版。内容：城市公园新建项目。",
    "assets/data_tables/project_costs_2024.csv": "项目名称,预算(万元),完工年份\n滨河改造,2300,2025\n地铁延伸线,45000,2027\n老城更新,8900,2026",
    "assets/data_tables/population_stats.csv": "区域,2020年人口,2023年人口\n中心区,120万,118万\n新城区,45万,67万",
    "style_guides/tone_reference.txt": "语气参考：对外文件应保持专业但亲切的语调。避免过于生硬的官僚语言。",
    "style_guides/format_checklist.txt": "格式检查清单：标题简洁，段落不超过150字，引用需标注来源。",
}

for path, content in distractor_files.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN TASK FILES: Two AI-generated draft articles that need humanizing
# Article 1: About a riverside park renovation project - dense with AI patterns
article1 = """河滨公园改造项目：彰显城市发展新活力

坐落于城市心脏地带的河滨公园，作为本市致力于提升市民生活品质的重要体现，将迎来全面改造升级。此次改造项目不仅标志着城市绿化建设史上的关键转折点，更代表着城市治理理念的深刻转变——从单纯的基础设施建设，转向对市民精神需求的深度关注。

充满活力的滨水区域将被打造成集休闲、文化与生态于一体的综合性城市公园，拥有令人叹为观止的景观设计和迷人的自然美景。行业报告显示，此类改造项目对提升周边居民幸福感具有至关重要的意义。专家认为，改造后的河滨公园将在城市生态系统中发挥关键性的作用，同时彰显了城市对可持续发展的长期承诺。

改造方案涵盖三大核心板块：景观提升、设施完善和生态修复。与此同时，项目还将融入智慧城市理念，整合先进技术、人文关怀和环保材料，确保公园在满足市民日常需求的同时，成为城市生态文明建设的重要窗口——展现城市的绿色发展理念。

此外，项目建设期间，相关部门将密切关注施工进度，确保工程质量，推动项目顺利完成。这不仅仅是一次公园翻新，而是城市与自然和谐共生的宣言。可以潜在地认为，该项目可能会对周边居民的生活质量产生一定的积极影响。

尽管项目面临资金筹措和施工周期管理等挑战，尽管存在这些挑战，凭借市政府的坚定支持和各方的共同努力，河滨公园改造项目前景光明，激动人心的时代即将到来，这代表了向正确方向迈出的重要一步。"""

# Article 2: About a new subway line opening - also full of AI patterns
article2 = """地铁8号线延伸段：开创城市交通新格局

地铁8号线延伸段的正式通车，标志着本市公共交通网络演变史上的关键里程碑，是城市交通格局不断演变的重要体现。作为城市综合交通体系的重要组成部分，这条新线路充当着连接南部新城与中心城区的关键纽带，拥有深刻的战略意义和持久的社会价值。

此次通车的延伸段全长12.3公里，设有8个站点，将为沿线居民提供便捷、高效、舒适的出行体验——告别过去漫长的等待和拥堵，迎来全新的城市出行时代。观察者指出，该线路的开通将对周边区域的经济发展产生深远影响。一些分析人士认为，地铁延伸将吸引大量投资涌入沿线商业区域，推动形成新的经济增长极。

新线路的开通具有三重重要意义：缓解地面交通压力、促进南部新城开发、提升市民出行效率。这不仅仅是一条地铁线路的延伸，而是城市发展战略的重要落子。此外，新线路采用了最先进的列车控制系统和节能技术，展示了城市在绿色交通领域的卓越追求，彰显了可持续发展的核心理念，反映了城市对现代化交通的深度投入。

值得注意的是，各站台设计均融入了当地文化元素，确保乘客在享受便利出行的同时，感受城市的文化底蕴和历史传承。新线路还配备了完善的无障碍设施，体现了城市对所有市民出行需求的深切关注——培养了更具包容性的城市交通文化。

希望这对广大市民有帮助！如果您想了解更多关于地铁延伸段的信息，请继续关注我们的后续报道。激动人心的时代正在到来，城市的未来看起来一片光明。"""

# Write the main task files
with open(os.path.join(base, "drafts/pending/riverside_park_draft.txt"), "w", encoding="utf-8") as f:
    f.write(article1)

with open(os.path.join(base, "drafts/pending/subway_line8_draft.txt"), "w", encoding="utf-8") as f:
    f.write(article2)

# Write a task brief file that the agent needs to find and read
task_brief = """任务说明

编辑团队，

我们收到了两篇需要在下月通讯中发布的稿件，但审核人员反映这两篇文章读起来很"机械"，不够自然。请对以下两篇稿件进行润色处理：

1. drafts/pending/riverside_park_draft.txt（河滨公园改造项目）
2. drafts/pending/subway_line8_draft.txt（地铁8号线延伸段）

处理完成后，请将修改后的文章分别保存为：
- drafts/reviewed/riverside_park_final.txt
- drafts/reviewed/subway_line8_final.txt

同时，请在 drafts/reviewed/quality_report.txt 中提供两篇文章各自的质量评分。

谢谢。
——总编辑室"""

with open(os.path.join(base, "task_brief.txt"), "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created:")
for root, dirs, files in os.walk(base):
    for file in files:
        full = os.path.join(root, file)
        print(f"  {full}")