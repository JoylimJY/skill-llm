import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/project/drafts/v1",
    "workspace/project/drafts/v2",
    "workspace/project/references",
    "workspace/project/references/downloaded",
    "workspace/project/figures",
    "workspace/project/submission/journal_a",
    "workspace/project/submission/journal_b",
    "workspace/project/notes",
    "workspace/project/tools/scripts",
    "workspace/project/tools/templates",
    "workspace/project/backup",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/project/drafts/v1/outline.txt": """第一章 绪论
1.1 研究背景
1.2 研究意义
1.3 研究方法
第二章 文献综述
第三章 实验设计
第四章 结果与讨论
第五章 结论
""",
    "workspace/project/drafts/v1/abstract_draft.txt": """本文研究了机器学习在自然语言处理领域的应用，
通过大量实验验证了所提方法的有效性。实验结果表明，
该方法在多个基准数据集上取得了显著的性能提升。""",
    "workspace/project/drafts/v2/chapter2_v2.txt": """第二章 相关研究综述
近年来，深度学习技术取得了长足进步，众多学者投入到这一领域的研究中。
Vaswani等人于2017年提出的Transformer架构彻底改变了自然语言处理的研究范式。""",
    "workspace/project/references/reading_list.txt": """待阅读文献：
1. BERT: Pre-training of Deep Bidirectional Transformers
2. Attention Is All You Need
3. GPT-3: Language Models are Few-Shot Learners
4. 中文信息处理若干问题研究（待下载）""",
    "workspace/project/references/downloaded/notes_bert.txt": """BERT论文笔记：
- 双向Transformer编码器
- 预训练任务：MLM + NSP
- 在11项NLP任务上SOTA""",
    "workspace/project/references/downloaded/notes_transformer.txt": """Transformer论文笔记：
- Self-attention mechanism
- Multi-head attention
- Position encoding""",
    "workspace/project/figures/figure_captions.txt": """图1：实验框架示意图
图2：不同模型在测试集上的性能对比
图3：训练损失曲线
图4：注意力权重可视化""",
    "workspace/project/submission/journal_a/cover_letter.txt": """尊敬的编辑：
兹投稿《基于深度学习的文本分类方法研究》一文，
请惠予审稿。""",
    "workspace/project/submission/journal_b/submission_checklist.txt": """投稿检查清单：
□ 标题页（含作者信息）
□ 摘要（300字以内）
□ 关键词（5-8个）
□ 正文
□ 参考文献（GB/T 7714格式）""",
    "workspace/project/notes/meeting_notes_20240315.txt": """会议纪要 2024-03-15
参与人：导师、课题组成员
议题：
1. 论文进度汇报
2. 实验方案讨论
3. 下一步计划""",
    "workspace/project/notes/revision_comments.txt": """审稿意见（第一轮）：
1. 文献综述需要补充近期相关工作
2. 实验部分描述不够详细
3. 结论部分过于简短，需要扩充""",
    "workspace/project/tools/templates/reference_template_gbt.txt": """GB/T 7714参考文献格式示例：
专著：作者.书名[M].出版地:出版社,年份.
期刊：作者.文章标题[J].期刊名,年份,卷(期):起止页码.
学位论文：作者.论文标题[D].学位授予城市:学位授予单位,年份.
会议论文：作者.文章标题[C]//会议论文集名.出版地:出版社,年份:起止页码.""",
    "workspace/project/tools/scripts/word_count.py": """# 字数统计脚本
import sys
def count_chinese_chars(text):
    return sum(1 for c in text if '\\u4e00' <= c <= '\\u9fff')
if __name__ == '__main__':
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    print(f'中文字符数: {count_chinese_chars(text)}')
    print(f'总字符数: {len(text)}')
""",
    "workspace/project/backup/chapter3_backup_20240301.txt": """第三章 实验设计与实现（备份版本2024-03-01）
3.1 数据集描述
本研究使用了三个公开数据集进行实验验证，分别为THUCNews、LCQMC和CMRC2018。
数据预处理步骤包括分词、去停用词和词向量化。""",
    "workspace/project/tools/templates/ai_writing_patterns.txt": """常见AI写作痕迹模式（用于识别）：
1. 过度使用"值得注意的是"、"综上所述"
2. 段落结构高度一致（总-分-总）
3. 缺乏个人观点和批判性分析
4. 句式过于规整，缺少变化
5. 引用过少或引用不自然""",
}

for filepath, content in distractor_files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# THE MAIN INPUT: AI-generated academic paragraph that needs humanization
# This is a realistic AI-generated Chinese academic text with obvious AI characteristics
ai_generated_content = """以下是一段AI生成的学术论文内容，请按照规范进行人类化处理。

---原文开始---

随着人工智能技术的迅猛发展，自然语言处理领域取得了显著的研究成果。值得注意的是，深度学习模型在文本分类任务中展现出了卓越的性能，这一发现具有重要的学术价值和实践意义。首先，基于Transformer架构的预训练语言模型已经成为该领域的主流方法。其次，这些模型通过大规模语料库的预训练，能够有效捕捉语言的深层语义特征。最后，经过微调的模型在下游任务中表现出色。此外，近年来的研究表明，模型的规模与性能之间存在显著的正相关关系，非常重要的一点是，计算资源的投入对最终结果有很大提高的作用。综上所述，大型语言模型代表了当前自然语言处理研究的最前沿方向，值得学术界和工业界共同关注与深入探索。这一研究方向的重要性不言而喻，未来的发展前景十分广阔。

---原文结束---

目标检测系统：知网学术不端检测系统
"""

with open("workspace/project/drafts/v2/ai_generated_paragraph.txt", 'w', encoding='utf-8') as f:
    f.write(ai_generated_content)

# Create the output directory where the agent should write results
os.makedirs("workspace/project/submission/final_output", exist_ok=True)

print("Workspace generated successfully.")
print("Directory structure:")
for root, dirs_list, files in os.walk("workspace"):
    level = root.replace("workspace", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")