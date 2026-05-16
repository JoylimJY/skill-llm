import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/thesis_project/chapter2",
    "workspace/thesis_project/chapter3",
    "workspace/thesis_project/references",
    "workspace/thesis_project/drafts/v1",
    "workspace/thesis_project/drafts/v2",
    "workspace/thesis_project/figures",
    "workspace/thesis_project/notes",
    "workspace/tools/templates",
    "workspace/tools/checklist",
    "workspace/submissions/journal_a",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/thesis_project/chapter2/literature_review.txt": "文献综述内容（第二章草稿，尚未修改）。",
    "workspace/thesis_project/chapter3/methodology.txt": "研究方法章节，待补充数据分析部分。",
    "workspace/thesis_project/references/bibliography.bib": "@article{Smith2020, author={Smith, J.}, title={AI in Education}, year={2020}}",
    "workspace/thesis_project/drafts/v1/abstract_v1.txt": "早期摘要草稿，内容过时，不作为最终版本。",
    "workspace/thesis_project/drafts/v2/abstract_v2.txt": "修订版摘要，语言尚需打磨。",
    "workspace/thesis_project/figures/fig1_description.txt": "图1：在线学习平台用户增长趋势（2018-2023）",
    "workspace/thesis_project/notes/meeting_notes_20240315.txt": "导师意见：第四章论证逻辑需加强，引用来源需核实。",
    "workspace/thesis_project/notes/revision_checklist.txt": "格式检查项：字体、行距、参考文献格式。",
    "workspace/tools/templates/cover_letter_template.txt": "投稿信模板，供提交期刊时使用。",
    "workspace/tools/checklist/submission_checklist.txt": "投稿前检查：摘要、关键词、正文、参考文献、作者信息。",
    "workspace/submissions/journal_a/submission_notes.txt": "期刊A要求：字数5000-8000，双盲评审，APA格式引用。",
}

for path, content in distractor_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN INPUT: AI-generated academic passage that needs humanization
# This passage is deliberately crafted to contain ALL the anti-patterns the skill targets:
# - 综上所述 (must be deleted or replaced)
# - 因此 (must be replaced)
# - 首先/其次/最后 (sequential markers to be restructured)
# - 此外 (to be replaced)
# - Perfect 总-分-总 structure with a concluding summary sentence
# - Uniform sentence length (all medium-length, very AI-like)
# - No hedging qualifiers
# - No parenthetical inserts
# - No logical gaps

ai_passage = """随着人工智能技术的快速发展，在线教育平台在教学模式上发生了深刻变革。首先，自适应学习系统能够根据学生的学习进度和知识掌握情况，动态调整教学内容与难度，从而实现个性化教学。其次，智能推荐算法通过分析学习者的行为数据，为其推送最为匹配的学习资源，提升了学习效率。最后，自然语言处理技术的应用使得智能辅导系统能够实时解答学生的问题，弥补了传统课堂中师生互动不足的缺陷。此外，人工智能技术还在教育评估领域展现出巨大潜力，自动评分系统和学习行为分析工具的引入，显著提高了教师的工作效率。因此，人工智能与在线教育的深度融合已成为当前教育技术领域研究的核心议题之一。综上所述，本文认为，在线教育平台对人工智能技术的广泛应用，不仅改变了传统的教与学方式，更为推动教育公平与质量提升提供了重要的技术支撑。"""

with open("workspace/thesis_project/chapter4_ai_section_raw.txt", "w", encoding="utf-8") as f:
    f.write(ai_passage)

print("Workspace generated successfully.")
print(f"Input passage character count: {len(ai_passage)}")
print(f"Input passage: {ai_passage}")