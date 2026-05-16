import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "editorial/drafts/2024/q1",
    "editorial/drafts/2024/q2",
    "editorial/published/tech",
    "editorial/published/culture",
    "editorial/archive/2023",
    "editorial/templates/report_formats",
    "editorial/guidelines/style",
    "ops/logs/review_history",
    "ops/config",
    "media/images/covers",
    "media/assets/thumbnails",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("editorial/drafts/2024/q1/draft_template.txt", "这是一个标准稿件模板，供编辑参考使用。"),
    ("editorial/drafts/2024/q2/outline_notes.txt", "文章提纲：1. 引言 2. 正文 3. 结论"),
    ("editorial/published/tech/ai_article_final.txt", "人工智能正在改变世界，这是已发布的文章。"),
    ("editorial/published/culture/culture_review.txt", "文化类文章审核已通过，无需修改。"),
    ("editorial/archive/2023/old_draft_001.txt", "这是2023年的旧稿件，已归档。"),
    ("editorial/archive/2023/old_draft_002.txt", "旧稿件002，包含已修正的内容。"),
    ("editorial/templates/report_formats/standard_format.txt", "标准报告格式模板（旧版）。"),
    ("editorial/guidelines/style/writing_guide.txt", "写作风格指南：保持简洁、清晰、有力。"),
    ("ops/logs/review_history/review_log_2024.txt", "审核日志：2024年1月至6月审核记录。"),
    ("ops/config/editor_config.json", '{"version": "1.2", "language": "zh-CN", "auto_save": true}'),
    ("media/images/covers/placeholder.txt", "封面图片占位文件"),
    ("media/assets/thumbnails/thumb_info.txt", "缩略图资产说明"),
]
for path, content in distractors:
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN PROBLEM FILE: A messy Chinese draft article with deliberate errors
# The article is about "远程办公的利与弊" (Pros and cons of remote work)
# Planted errors:
# Typos:
#   - "以经" (should be "已经") - 同音字 - paragraph 1
#   - "在见" (should be "再见") - 同音字 - paragraph 3
#   - "我们们" (should be "我们") - 多字 - paragraph 2
#   - Missing punctuation: a sentence ending without 。
#   - "做" used where "坐" is needed (形近字 or 同义混淆)
# Expression issues:
#   - A sentence with broken subject-predicate agreement
#   - A logical non-sequitur paragraph

article_content = """远程办公的利与弊

随着互联网技术的迅猛发展，远程办公已经成为许多企业和员工的重要工作方式。根据最新调查，超过60%的知识工作者表示他们以经历过至少一段时间的远程工作经历，这一比例在过去五年中持续攀升。

远程办公的优势是显而易见的。我们们可以在任何地方工作，不再受地理位置的限制。员工可以节省通勤时间，将这些时间用于提升工作效率或照顾家庭。此外，企业也可以因此降低办公室租金等固定成本。研究表明，许多员工在家办公时的专注度反而高于在嘈杂的开放式办公室

然而，远程办公也存在明显的挑战。首先，团队协作变得更加困难，信息沟通的成本大幅上升。其次，长期在家工作的员工容易感到孤独和与团队隔离。尤其是对于需要频繁在见同事讨论方案的岗位，远程办公的效率损耗更为突出。值得注意的是，量子计算的发展也将对远程办公产生深远影响，虽然目前这一技术尚未普及。

从长远来看，混合办公模式或许是最优解。员工可以选择每周在办公室做两到三天，其余时间居家办公。这种灵活的安排既保留了面对面交流的温度，又给予员工充分的自主权。

总体而言，远程办公是一把双刃剑，关键在于企业如何建立配套的管理制度和文化氛围，才能真正发挥其潜力。"""

article_path = os.path.join(workspace, "editorial/drafts/2024/q2/remote_work_draft.txt")
with open(article_path, "w", encoding="utf-8") as f:
    f.write(article_content)

print(f"Workspace initialized at {workspace}")
print(f"Main article: {article_path}")
print("Distractor files created.")