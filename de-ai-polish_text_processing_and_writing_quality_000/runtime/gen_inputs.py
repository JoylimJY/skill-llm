import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "legal_media/drafts/civil_law",
    "legal_media/drafts/criminal_law",
    "legal_media/drafts/archive",
    "legal_media/published/2024",
    "legal_media/published/2023",
    "legal_media/templates",
    "legal_media/research/notes",
    "legal_media/research/citations",
    "editorial/style_guides",
    "editorial/submissions",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files (do NOT hint at the solution) ──────────────────────────
distractors = {
    "legal_media/drafts/civil_law/contract_basics.md": "合同法的基本原则包括自愿原则、公平原则和诚实信用原则。当事人依法享有自愿订立合同的权利。",
    "legal_media/drafts/criminal_law/sentencing_reform.md": "量刑改革近年来受到广泛关注，法院在实践中积累了丰富经验。",
    "legal_media/drafts/archive/old_editorial_001.md": "本文探讨了民事诉讼程序中的若干问题，供读者参考。",
    "legal_media/published/2024/jan_feature.md": "2024年1月，最高人民法院发布了新的司法解释，对相关问题作出明确规定。",
    "legal_media/published/2023/year_review.md": "2023年度法治建设综述，回顾了全年重要立法与司法动态。",
    "legal_media/templates/article_template.md": "【标题】\n\n【导言】\n\n【正文】\n\n【结语】",
    "legal_media/research/notes/judicial_independence.txt": "司法独立是现代法治国家的基本原则，相关文献综述见附件。",
    "legal_media/research/citations/references.bib": "@article{li2023, author={Li Wei}, title={Judicial Reform}, year={2023}}",
    "editorial/style_guides/house_style.txt": "本刊要求文章逻辑清晰、语言简练，避免冗余表达。",
    "editorial/submissions/pending_review.md": "作者投稿，待审核。内容涉及知识产权保护的最新进展。",
    "editorial/style_guides/submission_guidelines.md": "投稿须知：字数3000-5000字，附参考文献，格式规范。",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# ── THE PROBLEM FILE: article riddled with AI-pattern violations ─────────────
# This article about judicial reform contains ALL violation categories:
#   1. 对比句式 (contrast patterns)
#   2. 程式化连接词 (formulaic connectors)
#   3. 结尾姿态句 (closing platitudes)
#   4. 口语化表述 (colloquial absolute terms)
#   5. 绝对化与戏剧化 (absolutist/dramatic language)
#   6. AI过渡语 (AI transition phrases)
#   7. 自我陈述 (self-referential statements)
#   8. 过多无序列表 (>3 bullet lists)
#   9. 过度引号 (excessive quotation marks)

article_content = """# 司法体制改革的深层逻辑

我更愿意从一个具体案例出发来讨论这个问题。近年来，司法体制改革成为法律界热议的话题。

不是所有人都理解改革的意义，而是只有深入实践的从业者才能感受到其重要性。表面上看似平静，实则暗流涌动。

原因很简单：司法公正是法治社会的基石。

不妨把这个问题拆成几个维度来看：首先，制度层面的改革；其次，人员素质的提升；此外，社会监督机制的完善。

## 制度层面

本质上，司法改革的核心矛盾在于权力与责任的匹配问题。从根本上说，必须建立权责对等的制度框架。

制度层面涉及以下几个方面：

- 立案登记制改革
- 员额制法官制度
- 司法责任制
- 巡回法庭建设
- 跨行政区划法院设置

这些改革措施无疑将对司法实践产生深远影响。

## 人员素质

其次，我想强调的是，法官职业化建设是改革的关键所在。

人员素质方面需要关注：

- 法官遴选机制
- 职业晋升通道
- 薪酬保障制度
- 培训体系建设

真正的职业化，绝对不是简单的考试选拔，肯定需要系统性的制度设计。

## 社会监督

然而，仅靠内部机制是不够的。因此，外部监督的引入变得尤为重要。

社会监督的主要渠道包括：

- 人大监督
- 检察监督
- 社会舆论监督
- 当事人权利保障

我越来越觉得，"监督"与"独立"之间的张力是永恒的命题。

先把几个核心争议摆出来：一是司法独立与民主问责如何平衡；二是职业化与大众化如何协调；三是改革速度与社会承受能力如何匹配。

## 改革成效

看起来改革推进顺利，其实面临重重阻力。并非外部压力造成了困难，而是内部惰性才是真正的障碍。

一个直接的原因是：改革触动了既有利益格局。

从根本上说，任何改革都必然遭遇阻力。关键的问题在于能否形成合力，核心的挑战是利益协调。

## 结语

综上所述，司法体制改革是一项系统工程，搞定其中任何一个环节都需要付出巨大努力。

方向已经明确，未来可期。尽管面临挑战，机遇与挑战并存，我们应当拭目以待改革的最终成果。

总而言之，靠谱的改革路径需要稳扎稳打，这一点肯定没问题。
"""

article_path = os.path.join(workspace, "legal_media/drafts/judicial_reform_draft.md")
with open(article_path, "w", encoding="utf-8") as f:
    f.write(article_content)

print("Workspace generated successfully.")
print(f"Problem file: {article_path}")
print(f"Total distractor files: {len(distractors)}")