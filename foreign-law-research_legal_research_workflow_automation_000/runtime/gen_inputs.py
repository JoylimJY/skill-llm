import os
import random
from pathlib import Path

random.seed(42)

# Base workspace for the researcher user
workspace = Path("/home/researcher")

# Create a realistic legal research workspace with distractors
# Distractor: old completed research on a different topic
old_research = workspace / "Downloads" / "research" / "Kazakhstan_investment"
old_research.mkdir(parents=True, exist_ok=True)

(old_research / "00_问题拆解.md").write_text("""# 哈萨克斯坦投资法律问题拆解

## 东道国：哈萨克斯坦
## 法律领域：外商直接投资
## 时间节点：2023年Q3
## 适用主体：中资国有企业

问题1：哈萨克斯坦是否允许外资控股矿业公司？
问题2：外资审批流程及主管部门？
""", encoding='utf-8')

(old_research / "01_资料来源.md").write_text("""# 资料来源

| 资源 | URL | 发布日期 | 时效性 |
|------|-----|---------|--------|
| ICLG Mining Laws | https://iclg.com/practice-areas/mining-laws-and-regulations/kazakhstan | 2023-03 | 🟡中等 |
| Lex Mundi | https://www.lexmundi.com/guide/kazakhstan | 2022-11 | 🔴低（超6个月）|
""", encoding='utf-8')

(old_research / "02_事实卡片.md").write_text("""# 事实卡片

🟢 **官方规定**：根据哈萨克斯坦《矿产资源法》第XX条，外资持股比例上限为...
🟡 **机构解读**：ICLG 2023年报告指出...
🔴 **推测分析**（待核实）：预计新规将于2024年实施...
""", encoding='utf-8')

(old_research / "FINAL_调研报告.md").write_text("""# 哈萨克斯坦投资法调研报告（旧版示例）
""", encoding='utf-8')

# Distractor: incomplete research on DRC (no final report)
drc_research = workspace / "Downloads" / "research" / "DRC_mining"
drc_research.mkdir(parents=True, exist_ok=True)

(drc_research / "00_问题拆解.md").write_text("""# 刚果（金）矿业法律问题拆解（草稿）
## 状态：未完成
""", encoding='utf-8')

(drc_research / "notes_draft.txt").write_text("""随手笔记：DRC 2018年修订矿业法，提高了国家股份要求到10%，royalty也上调了。
来源不明，需要核实。
""", encoding='utf-8')

# Distractor: general legal templates
templates_dir = workspace / "Downloads" / "legal_templates"
templates_dir.mkdir(parents=True, exist_ok=True)

(templates_dir / "NDA_template_EN.md").write_text("""# Non-Disclosure Agreement Template
[Party A] agrees not to disclose...
""", encoding='utf-8')

(templates_dir / "JV_agreement_outline.md").write_text("""# Joint Venture Agreement Outline
1. Parties
2. Purpose
3. Capital Contribution
""", encoding='utf-8')

(templates_dir / "due_diligence_checklist.txt").write_text("""Due Diligence Checklist for Mining M&A:
- [ ] Mining licenses verified
- [ ] Environmental permits
- [ ] Local content compliance
- [ ] Tax clearance certificates
""", encoding='utf-8')

# Distractor: old reference materials with outdated info
refs_dir = workspace / "Downloads" / "references"
refs_dir.mkdir(parents=True, exist_ok=True)

(refs_dir / "Zimbabwe_investment_2018.txt").write_text("""OUTDATED REFERENCE (2018):
Zimbabwe Investment Authority (ZIA) - superseded by Zimbabwe Investment and Development Agency (ZIDA) in 2020.
Old indigenisation rules required 51% local ownership - REPEALED in 2018.
Note: This document is from 2018 and should NOT be used as primary source.
""", encoding='utf-8')

(refs_dir / "africa_mining_overview_2021.txt").write_text("""Africa Mining Overview (2021 - potentially outdated):
Zimbabwe: Platinum, gold, chrome major minerals.
ZELA (Zimbabwe Environmental Law Association) monitors compliance.
Royalty rates as of 2021: Gold 5%, Platinum 2.5% (subject to change).
""", encoding='utf-8')

(refs_dir / "forex_regulations_summary.txt").write_text("""Foreign Exchange Regulations Summary (multiple jurisdictions):
Zimbabwe: RBZ (Reserve Bank of Zimbabwe) governs forex.
Surrender requirements may apply to mining export proceeds.
""", encoding='utf-8')

# Distractor: internal memos
memos_dir = workspace / "Downloads" / "internal_memos"
memos_dir.mkdir(parents=True, exist_ok=True)

(memos_dir / "project_longbow_memo.txt").write_text("""CONFIDENTIAL - Project Longbow
Target: Zimbabwe platinum asset
Status: Pre-LOI stage
Legal team to complete regulatory review by end of Q2.
Key concerns: Local content, forex repatriation, environmental permits.
Contact: BD team
""", encoding='utf-8')

(memos_dir / "board_presentation_outline.pptx.txt").write_text("""[Board Presentation - Placeholder]
Slide 1: Executive Summary
Slide 2: Target Overview
Slide 3: Legal & Regulatory Risk
Slide 4: Financial Projections
""", encoding='utf-8')

# Distractor: competitor analysis
(workspace / "Downloads" / "competitor_analysis.txt").write_text("""Competitor Activity in Zimbabwe Mining Sector:
- Company A (Chinese SOE): Entered 2019, platinum JV
- Company B (Australian): Divested 2022 citing regulatory uncertainty
- Company C (South African): Active in chrome sector
""", encoding='utf-8')

# The actual task brief - a messy internal briefing note (NOT a perfect spec)
task_brief = workspace / "Downloads" / "TASK_BRIEF_Zimbabwe_mining.txt"
task_brief.write_text("""FROM: Business Development Team
TO: Legal Research Support
DATE: 2024-06-10
RE: URGENT - Zimbabwe Mining Regulatory Research

We are evaluating the acquisition of a platinum mining concession in Zimbabwe (Project Longbow).
Before we proceed to LOI stage, we need a thorough legal research report on Zimbabwe's mining
regulations for foreign investors.

Key questions the deal team needs answered:
1. Can a Chinese-owned company (WFOE/JV structure) hold a platinum mining license in Zimbabwe?
2. What are the local content / indigenisation requirements post-2018 reform?
3. What are the key licensing steps and which government bodies are involved?
4. What are the main legal risks (forex, environmental, political risk)?
5. Are there any special rules for "special grants" or large-scale platinum operations?

Please produce a research report that the deal team can rely on for the board presentation.
The report should be thorough, clearly distinguish between confirmed legal provisions and 
interpretive analysis, and flag anything that needs local counsel verification.

Output needed: FINAL_调研报告.md (and all supporting research files per our standard process)

Country: Zimbabwe
Topic: mining (platinum sector, foreign investment)
""", encoding='utf-8')

print("Workspace setup complete.")
print(f"Task brief: {task_brief}")
print(f"Distractor files created: {len(list(workspace.rglob('*')))} total items")