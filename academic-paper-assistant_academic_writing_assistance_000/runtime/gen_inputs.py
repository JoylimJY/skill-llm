import os
import random

random.seed(42)

workspace = "/workspace"

# Create realistic directory structure with distractor files
dirs = [
    "paper_drafts",
    "paper_drafts/v1",
    "paper_drafts/v2",
    "paper_drafts/figures",
    "references",
    "notes",
    "notes/meeting_notes",
    "notes/ideas",
    "submission",
    "submission/journal_A",
    "tools",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

# 1. Old draft (v1) - irrelevant
with open(os.path.join(workspace, "paper_drafts/v1/draft_v1.txt"), "w", encoding="utf-8") as f:
    f.write("This is the old version of the paper. Please ignore.\n联邦学习是一种很有意思的技术，我们做了一些实验。结果还不错。\n")

# 2. Figures placeholder
with open(os.path.join(workspace, "paper_drafts/figures/fig_notes.txt"), "w", encoding="utf-8") as f:
    f.write("Figure 1: System architecture\nFigure 2: Accuracy comparison chart\nFigure 3: Privacy budget curve\n")

# 3. Meeting notes
with open(os.path.join(workspace, "notes/meeting_notes/20240315.txt"), "w", encoding="utf-8") as f:
    f.write("Meeting with supervisor:\n- Need to add more baselines\n- Fix the abstract, it sounds too casual\n- References are a mess, need GB/T 7714\n- Deadline: 2024-06-01\n")

with open(os.path.join(workspace, "notes/meeting_notes/20240320.txt"), "w", encoding="utf-8") as f:
    f.write("Follow-up: supervisor wants IMRAD structure strictly followed.\nWord budget: abstract ~250 words, intro ~600 words.\n")

# 4. Ideas file
with open(os.path.join(workspace, "notes/ideas/research_ideas.txt"), "w", encoding="utf-8") as f:
    f.write("Idea 1: differential privacy + federated learning\nIdea 2: secure aggregation protocol\nIdea 3: gradient compression\n")

# 5. Submission checklist
with open(os.path.join(workspace, "submission/journal_A/checklist.txt"), "w", encoding="utf-8") as f:
    f.write("[ ] Abstract: 200-300 words\n[ ] Keywords: 5-8 terms\n[ ] References: GB/T 7714-2015\n[ ] Figures: high resolution\n[ ] Cover letter\n")

# 6. Tools note
with open(os.path.join(workspace, "tools/latex_template.txt"), "w", encoding="utf-8") as f:
    f.write("LaTeX template for journal submission.\n\\documentclass{article}\n% ... template content ...\n")

# 7. Random data file
with open(os.path.join(workspace, "tools/experiment_log.csv"), "w", encoding="utf-8") as f:
    f.write("epoch,accuracy,loss,privacy_budget\n1,0.72,0.45,1.0\n2,0.78,0.38,1.0\n3,0.83,0.31,1.0\n10,0.91,0.19,1.0\n")

# 8. Another distractor
with open(os.path.join(workspace, "notes/ideas/related_work_notes.txt"), "w", encoding="utf-8") as f:
    f.write("Related work:\n- McMahan et al., 2017: FedAvg\n- Dwork, 2006: Differential Privacy\n- Bonawitz et al., 2017: Practical Secure Aggregation\n- Geyer et al., 2017: Differentially Private FL\n")

# 9. Distractor submission file
with open(os.path.join(workspace, "submission/journal_A/cover_letter_draft.txt"), "w", encoding="utf-8") as f:
    f.write("Dear Editor,\n\nWe submit our manuscript titled 'Privacy-Preserving Federated Learning...' for your consideration.\n\nSincerely,\nThe Authors\n")

# 10. Random .py distractor
with open(os.path.join(workspace, "tools/plot_results.py"), "w", encoding="utf-8") as f:
    f.write("import matplotlib.pyplot as plt\n# Script to plot experimental results\n# Not relevant to paper writing task\n")

# ── Core problem files ────────────────────────────────────────────────────────

# THE MESSY ABSTRACT (colloquial, needs polishing)
messy_abstract = """【待润色摘要】
随着机器学习越来越火，大家都想用数据训练模型，但是数据隐私是个大问题。
联邦学习这个方法挺好的，可以让好多机构一起训练模型但是不用共享数据，很厉害。
但是现在的联邦学习还是有点问题，比如说梯度泄露啊，还有成员推断攻击什么的，
所以我们就想了个新方法，把差分隐私和安全聚合结合起来，
我们叫它DP-SA框架。然后我们做了一堆实验，在好几个数据集上测试了，
结果发现我们的方法比其他方法好很多，隐私保护效果更强，准确率也没掉太多。
总的来说，这篇论文就是提出了DP-SA，解决了联邦学习里面的隐私问题，挺有意义的。
"""

with open(os.path.join(workspace, "paper_drafts/v2/abstract_draft.txt"), "w", encoding="utf-8") as f:
    f.write(messy_abstract)

# THE MESSY REFERENCES (unformatted, mixed styles, needs GB/T 7714-2015)
messy_references = """【待整理参考文献】

以下参考文献格式混乱，需要统一整理为GB/T 7714-2015格式：

[1] H. B. McMahan, E. Moore, D. Ramage, S. Hampson, B. A. y Arcas. Communication-Efficient Learning of Deep Networks from Decentralized Data. In Proceedings of the 20th International Conference on Artificial Intelligence and Statistics (AISTATS), 2017, pp. 1273-1282.

[2] Dwork, C., Roth, A. (2014). The Algorithmic Foundations of Differential Privacy. Foundations and Trends in Theoretical Computer Science, Vol 9, No 3-4, pages 211-407.

[3] Bonawitz K, Ivanov V, Kreuter B, et al. Practical Secure Aggregation for Privacy-Preserving Machine Learning[C]. ACM SIGSAC Conference on Computer and Communications Security, 2017, 1175-1191.

[4] Geyer R C, Klein T, Nabi M. Differentially Private Federated Learning: A Client Level Perspective. arXiv preprint arXiv:1712.07557, 2017.

[5] 李志远, 张华, 王建国. 面向联邦学习的隐私保护方法综述. 计算机学报, 2022, 45(9): 1953-1972.
"""

with open(os.path.join(workspace, "references/raw_references.txt"), "w", encoding="utf-8") as f:
    f.write(messy_references)

# THE RESEARCH TOPIC FILE (context for structure planning)
topic_context = """【论文信息】
论文题目：基于差分隐私与安全聚合的联邦学习隐私保护框架
英文题目：A Privacy-Preserving Federated Learning Framework Based on Differential Privacy and Secure Aggregation
论文类型：研究论文（Research Paper）
目标期刊：计算机学报
学科领域：计算机科学 / 信息安全
研究主题：在联邦学习场景下，结合差分隐私（Differential Privacy）和安全聚合（Secure Aggregation）
         机制，提出DP-SA框架，抵御梯度泄露和成员推断攻击，同时保持模型实用性。
关键词建议：联邦学习, 差分隐私, 安全聚合, 隐私保护, 梯度泄露
"""

with open(os.path.join(workspace, "paper_drafts/v2/topic_info.txt"), "w", encoding="utf-8") as f:
    f.write(topic_context)

print("Workspace generated successfully.")
print("\nDirectory structure:")
for root, dirs_list, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')