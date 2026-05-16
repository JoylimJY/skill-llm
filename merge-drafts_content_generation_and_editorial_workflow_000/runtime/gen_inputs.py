import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── directory structure with distractors ──────────────────────────────────────
dirs = [
    "drafts",
    "drafts/archive",
    "research",
    "research/market_data",
    "research/interviews",
    "editorial/notes",
    "editorial/previous_issues",
    "assets",
    "assets/images_meta",
    "internal/logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "research/market_data/raw_numbers_2022.txt": (
        "2022 AI tools market: $8.2B global. Source: IDC annual report.\n"
        "Growth rate: 34% YoY. Key players: GitHub, JetBrains, TabNine.\n"
    ),
    "research/market_data/analyst_notes.txt": (
        "Note from analyst team: figures from Gartner and Forrester diverge significantly.\n"
        "Do not use 2022 data in 2025 publication without updating.\n"
    ),
    "research/interviews/dev_survey_raw.csv": (
        "respondent_id,years_exp,uses_ai_tools,satisfaction\n"
        "001,5,yes,4\n002,12,no,N/A\n003,3,yes,5\n004,8,yes,3\n005,1,yes,4\n"
    ),
    "research/interviews/cto_quotes.txt": (
        "CTO of FinTechCorp: 'We reduced code review time by 40% after adopting AI assistants.'\n"
        "VP Engineering at LogisticsPro: 'Onboarding time dropped from 3 months to 6 weeks.'\n"
        "CISO at SecureBank: 'We paused rollout pending security audit — code suggestions leaked internal variable names.'\n"
    ),
    "editorial/notes/style_guide_reminder.txt": (
        "Reminder: All published articles must use AP Style.\n"
        "Avoid passive voice. Max sentence length: 25 words.\n"
        "Tech jargon must be explained on first use.\n"
    ),
    "editorial/notes/editor_feedback_draft_round1.txt": (
        "Editor Li: The intro is too long. Cut the first two paragraphs.\n"
        "Editor Wang: Missing the 'enterprise adoption challenges' angle entirely.\n"
        "Both editors agree: need more concrete case studies.\n"
    ),
    "editorial/previous_issues/ai_tools_2023_published.md": (
        "# AI Tools in Development: 2023 Retrospective\n\n"
        "Published: December 2023\n\n"
        "Last year's landscape was dominated by GitHub Copilot and early ChatGPT integrations...\n"
        "Market was estimated at $12B globally (Forrester, 2023).\n"
    ),
    "assets/images_meta/hero_image_metadata.txt": (
        "File: hero_coding_ai.jpg\nDimensions: 1920x1080\nAlt text: Developer using AI coding assistant\nCredit: Unsplash/JohnDoe\n"
    ),
    "internal/logs/submission_log.txt": (
        "2025-01-10 09:00 - Reporter Zhang submitted draft_a.md\n"
        "2025-01-11 14:30 - Reporter Li submitted draft_b.md\n"
        "2025-01-12 17:45 - Intern Wang submitted draft_c.md\n"
        "2025-01-13 10:00 - Editor requested merge\n"
    ),
    "drafts/archive/old_draft_2024_abandoned.md": (
        "# AI in Dev: Abandoned Draft (2024)\n\n"
        "This draft was abandoned due to outdated statistics.\n"
        "DO NOT USE — superseded by 2025 drafts.\n"
    ),
    "internal/logs/conflict_tracker.txt": (
        "Known conflicts to resolve:\n"
        "- Market size figures differ between sources\n"
        "- Adoption rate percentages inconsistent\n"
        "- Timeline for mainstream adoption varies by 2 years\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── DRAFT A: High quality (should score ~85, basis for base draft) ─────────────
draft_a = """\
# 企业级AI编程助手：重塑软件开发的沉默革命

## 引言

2025年，AI编程助手已从新奇工具演变为企业软件开发的基础设施。从自动补全到完整功能模块生成，这类工具正在系统性地改变开发者的工作方式——不仅提升效率，也在重新定义"程序员"这一职业的技能边界。

本文聚焦企业场景，梳理AI编程助手在大规模生产环境中的落地路径、真实收益与潜在风险。

## 技术能力全景

当前主流AI编程助手（包括GitHub Copilot、Cursor、Tabnine、Amazon CodeWhisperer）均基于大型语言模型（LLM），核心能力分为三层：

- **代码补全层**：基于上下文的实时补全，准确率在经验测试中达到65%–78%
- **功能生成层**：根据自然语言描述生成完整函数或模块
- **重构辅助层**：识别代码异味，提供重构建议并自动应用

值得注意的是，不同编程语言的表现差距显著——Python、JavaScript支持最优，而COBOL、Fortran等老旧语言几乎无效。

## 企业落地现状

根据Stack Overflow 2025年开发者调查（样本量：82,000人），企业开发者中AI工具使用率已达67%，较2023年的34%翻倍。

**典型落地案例：**

- **FinTechCorp**（金融科技）：引入GitHub Copilot Business后，代码审查时间降低40%，新员工上手周期从3个月压缩至6周。数据来源：企业内部效能报告（2024Q4）。
- **LogisticsPro**（物流平台）：将Cursor集成入CI/CD流水线，自动生成单元测试，测试覆盖率从52%提升至81%。
- **HealthDataSys**（医疗数据）：因合规要求，仅部署私有化模型，功能受限但满足HIPAA要求。

## 市场规模与增长预测

据Gartner 2025年报告，企业AI编程工具市场规模预计于2027年达到**450亿美元**，复合增长率38%。中国市场在同期预计占比约18%，以智谱AI、通义灵码为代表的本土产品加速渗透。

## 核心挑战

### 安全与合规风险

SecureBank的案例值得关注：其AI助手曾在代码建议中泄露内部变量命名规范，暴露了系统架构信息。主要安全风险包括：

1. **代码泄露**：模型训练或API传输中可能涉及专有代码
2. **供应链污染**：AI生成代码可能引入已知漏洞（CVE数据库中有记录的模式）
3. **过度依赖**：开发者审查能力退化，"橡皮图章"现象出现

### 技术债务问题

AI生成代码质量参差不齐，在部分压力测试中，生成代码引入技术债务的概率约为23%（来源：McKinsey, 2024）。

## 未来展望

AI编程助手正向"智能协作者"演进：从被动响应转向主动提议架构决策、识别潜在缺陷。预计2026年将出现首批"AI-first"开发团队——即AI承担60%以上编码工作、人类专注架构与审查的新型组织模式。

## 结语

企业采纳AI编程助手不再是"是否"的问题，而是"如何"的问题。技术能力已就绪，挑战在于治理框架、培训体系与文化转型的同步配套。
"""

# ── DRAFT B: Medium quality (should score ~72, has unique data but weaker structure) ──
draft_b = """\
# AI编程工具在企业中的应用与挑战

AI编程助手这两年在企业里越来越普及了。很多公司都开始用，但效果参差不齐。这篇文章想聊聊这个话题，说说好的地方，也说说问题在哪。

## 市场情况

现在市场上做AI编程工具的公司很多。GitHub有Copilot，亚马逊有CodeWhisperer，还有Cursor这种新秀。根据一份行业报告（来源不详），2028年这个市场会到620亿美元，增速很快。

另外我自己访谈了一些开发者，有人说挺好用的，有人说不好用，感觉差异很大。

## 好的地方

- 写代码快了
- 不用记那么多API文档
- 新手上手快一些
- 能帮忙写注释

有个公司（不方便透明具体名字）用了之后说效率提升了大概30%左右，但具体怎么测的不太清楚。

## 问题和挑战

AI工具带来的安全问题很严重，这是公认的。

首先是代码质量问题。AI生成的代码有时候看着能跑，但有很多隐患。在大型项目里这个问题更明显。

其次是对开发者的影响。有人担心程序员的基础能力会退化，特别是刚入行的新人，可能就不会从头写代码了。

还有版权问题。AI是用很多开源代码训练的，生成的代码到底有没有版权问题，现在还不清楚，各国法律也不一样。

最后是数据安全。把自己公司的代码发给第三方AI服务，存在泄露风险，特别是金融、医疗这类对数据敏感的行业。

## 一个独特视角：认知负荷转移

值得关注的一个现象是，AI工具不是减少了开发者的认知负荷，而是**转移**了认知负荷——从"怎么写"转向"写得对不对"。这要求开发者具备更强的代码审查能力和系统性思维，而不是更少的技能。

部分研究者认为，未来5年内，"AI代码审查员"将成为一个新兴岗位，专门负责验证AI生成代码的正确性与安全性。

## 小结

AI编程助手是个好工具，但不是银弹。企业在采纳时需要仔细考虑自己的情况，不能一刀切。
"""

# ── DRAFT C: Very low quality, fragmented (should score <30, triggers edge case) ──
draft_c = """\
# AI编程

AI很厉害。

编程助手能帮忙写代码这是大家都知道的事情了。

有用。

企业在用。

未来会更多企业用。

有问题要注意。

安全问题。

质量问题。

就这样吧总结一下就是AI编程助手是趋势。
"""

with open(os.path.join(workspace, "drafts/draft_a.md"), "w", encoding="utf-8") as f:
    f.write(draft_a)

with open(os.path.join(workspace, "drafts/draft_b.md"), "w", encoding="utf-8") as f:
    f.write(draft_b)

with open(os.path.join(workspace, "drafts/draft_c.md"), "w", encoding="utf-8") as f:
    f.write(draft_c)

print("Workspace generated successfully.")
print(f"Draft A: {len(draft_a)} chars")
print(f"Draft B: {len(draft_b)} chars")
print(f"Draft C: {len(draft_c)} chars")