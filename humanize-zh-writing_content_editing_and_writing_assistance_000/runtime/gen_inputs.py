import os
import random

random.seed(42)

workspace = "/workspace"

# Create distractor directory structure
dirs = [
    "archive/2023/drafts",
    "archive/2023/published",
    "archive/2024/drafts",
    "archive/2024/published",
    "editorial/guidelines",
    "editorial/templates",
    "submissions/pending",
    "submissions/rejected",
    "resources/style_guides",
    "resources/references",
    "tools/scripts",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("archive/2023/published/tech_review_q1.txt", "【已发布】关于芯片短缺的深度报道，本稿已通过终审。"),
    ("archive/2023/drafts/ai_overview_draft.txt", "草稿：AI 概览，待修改。作者：张伟。"),
    ("archive/2024/published/semiconductor_analysis.txt", "半导体行业分析报告（2024年第一季度）\n\n市场数据显示，全球半导体出货量同比增长12%。"),
    ("archive/2024/drafts/cloud_computing_draft.txt", "云计算专题草稿。这一段需要补充数据。"),
    ("editorial/guidelines/writing_standards.txt", "写作规范：\n1. 字数控制在1500-3000字\n2. 引用需注明来源\n3. 避免使用绝对化表述"),
    ("editorial/templates/news_template.txt", "新闻稿模板\n\n标题：\n导语：\n正文：\n结尾："),
    ("submissions/pending/reader_submission_001.txt", "投稿人：李明\n主题：智能驾驶安全问题\n\n近年来，智能驾驶事故频发……"),
    ("submissions/rejected/rejected_draft_042.txt", "退稿原因：论点不清晰，数据来源不明。"),
    ("resources/style_guides/punctuation_guide.txt", "标点符号使用指南：破折号、省略号的正确用法……"),
    ("resources/references/llm_terminology.txt", "大语言模型术语表\nLLM: Large Language Model\nRAG: Retrieval-Augmented Generation"),
    ("tools/scripts/word_count.py", "# 字数统计工具\ndef count_words(text):\n    return len(text)"),
    ("archive/2024/drafts/notes.txt", "编辑备注：这批稿件需要在周五前完成审核。"),
]

for path, content in distractors:
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN TASK FILE: an AI-flavored Chinese tech commentary article
# This article is about large language models in the enterprise context
# It is deliberately packed with ALL the AI writing tells:
# - "不可否认", "综合来看", "值得注意的是", "总体而言"
# - "一方面...另一方面...综合来看" structure
# - Perfectly balanced paragraphs
# - Smooth transitions everywhere
# - Stable emotion, no real stance
# - Perfect concluding summary

ai_article = """大模型进企业：一场被高估的革命？

近年来，以GPT-4、文心一言为代表的大语言模型迅速进入企业市场，引发了广泛的关注与讨论。不可否认，这一技术浪潮正在深刻改变各行各业的工作方式，其影响不容小觑。

一方面，大模型在内容生成、代码辅助、客服自动化等领域展现出了令人瞩目的潜力。多项行业调研数据显示，引入大模型的企业在特定任务上的效率提升幅度达到了20%至40%。值得注意的是，这一数字在不同行业之间存在较大差异，制造业与金融业的表现尤为突出。另一方面，大模型的落地应用也面临诸多现实挑战。数据安全、模型幻觉、私有化部署成本居高不下，都构成了企业大规模应用的掣肘因素。不少企业在引入大模型后，发现实际效果与宣传存在明显落差，投入产出比并不理想。

综合来看，大模型进企业这一趋势是真实的，但泡沫同样存在。总体而言，我们需要以更加理性、审慎的态度来看待这场技术变革，既不应盲目跟风，也不应因噎废食。

值得注意的是，在具体落地路径上，行业内逐渐形成了几种主流模式：一是通过API调用公有云大模型，降低前期投入；二是基于开源模型进行私有化微调，保障数据安全；三是与大模型服务商签订战略合作协议，定制专属解决方案。这三种模式各有利弊，企业需要根据自身规模、数据敏感程度和技术能力做出综合判断。

不可否认，技术本身并无好坏之分，关键在于应用场景的精准匹配与落地策略的持续优化。令人深思的是，那些率先取得成效的企业，往往并非技术实力最强的头部企业，而是在某一垂直场景深耕多年、对业务流程理解最为透彻的中型企业。这一现象值得行业从业者深入思考与借鉴。

总体而言，面对大模型这一新兴技术，企业决策者应保持开放而不失冷静的心态，在跟进技术趋势的同时，牢牢把握自身核心竞争力，方能在这场技术浪潮中立于不败之地。综合来看，未来属于那些既能拥抱变化、又能保持定力的企业。"""

task_file_path = os.path.join(workspace, "submissions/pending/llm_enterprise_commentary.txt")
with open(task_file_path, "w", encoding="utf-8") as f:
    f.write(ai_article)

# Also create an instruction file from the "editor"
instruction_file = os.path.join(workspace, "editorial_task.txt")
with open(instruction_file, "w", encoding="utf-8") as f:
    f.write("""编辑任务说明
=============

待处理稿件：submissions/pending/llm_enterprise_commentary.txt

任务：这篇稿子读起来太像 AI 写的了，帮我去掉 AI 味，改得像真人写的。
改写完的版本请保存为：rewritten_article.txt（放在工作目录根目录下）
""")

print("Workspace initialized successfully.")
print(f"Main task file: {task_file_path}")
print(f"Instruction file: {instruction_file}")