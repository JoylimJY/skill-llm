import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/investment_research/company_profiles",
    "workspace/investment_research/market_data",
    "workspace/investment_research/archived_reports/2022",
    "workspace/investment_research/archived_reports/2023",
    "workspace/tools/templates",
    "workspace/tools/scripts",
    "workspace/clients/portfolio_A",
    "workspace/clients/portfolio_B",
    "workspace/admin/config",
    "workspace/admin/logs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---

# 1. A generic company profile (distractor)
with open("workspace/investment_research/company_profiles/generic_profile_template.md", "w", encoding="utf-8") as f:
    f.write("""# Company Profile Template
Company Name: [TBD]
Industry: [TBD]
Founded: [TBD]
Revenue: [TBD]

## Business Overview
[Fill in business description here]

## Key Financials
- Revenue Growth: [X]%
- Net Margin: [Y]%
- Dividend Yield: [Z]%
""")

# 2. An old scoring rubric (distractor - uses different scoring system to confuse)
with open("workspace/investment_research/archived_reports/2022/old_scoring_rubric.txt", "w", encoding="utf-8") as f:
    f.write("""LEGACY SCORING SYSTEM (DEPRECATED - DO NOT USE)
====================================================
Score A (80-100): Excellent understanding
Score B (60-79): Good understanding
Score C (40-59): Partial understanding
Score D (0-39): Poor understanding

NOTE: This rubric was replaced in Q1 2023. Please refer to the current framework.
""")

# 3. A sample old report (distractor - wrong format)
with open("workspace/investment_research/archived_reports/2023/sample_report_OLD_FORMAT.md", "w", encoding="utf-8") as f:
    f.write("""# Investment Report - Acme Corp
Date: 2023-03-15

Summary: The investor demonstrates moderate understanding.

Scores:
- Business Model: 7/10
- Competitive Moat: 6/10
- Growth: 5/10
- Shareholder Return: 8/10

Recommendation: Further research needed.
""")

# 4. Market data CSV (distractor)
with open("workspace/investment_research/market_data/sector_pe_ratios.csv", "w", encoding="utf-8") as f:
    f.write("""sector,avg_pe,median_pe,date
Consumer Staples,28.5,26.3,2024-01-15
Technology,35.2,31.1,2024-01-15
Healthcare,22.7,20.4,2024-01-15
Financials,12.3,11.8,2024-01-15
Energy,14.5,13.2,2024-01-15
""")

# 5. A confusing "four-question" template (distractor - different questions)
with open("workspace/tools/templates/interview_questions_v1.txt", "w", encoding="utf-8") as f:
    f.write("""Interview Questions Template v1 (DRAFT)
========================================
Question 1: What industry is the company in?
Question 2: Who are the main competitors?
Question 3: What is the stock price target?
Question 4: What is your entry price?

Note: This template is for basic screening only.
""")

# 6. Config file (distractor)
with open("workspace/admin/config/report_settings.json", "w", encoding="utf-8") as f:
    f.write("""{
  "output_format": "pdf",
  "language": "zh-CN",
  "report_version": "2.1",
  "auto_email": false,
  "template_dir": "/workspace/tools/templates"
}
""")

# 7. Log file (distractor)
with open("workspace/admin/logs/system.log", "w", encoding="utf-8") as f:
    f.write("""2024-01-15 09:12:33 INFO  System started
2024-01-15 09:13:01 INFO  Interview session started: investor_ID_7821
2024-01-15 10:45:22 INFO  Session completed
2024-01-15 10:45:23 INFO  Transcript saved
2024-01-15 11:00:00 INFO  Report generation queued
""")

# 8. Portfolio file (distractor)
with open("workspace/clients/portfolio_A/holdings.csv", "w", encoding="utf-8") as f:
    f.write("""ticker,company,shares,avg_cost,current_price
HLJ001,鸿利佳食品,5000,38.50,42.30
HLJ001,鸿利佳食品,3000,41.20,42.30
""")

# 9. Another portfolio (distractor)
with open("workspace/clients/portfolio_B/notes.txt", "w", encoding="utf-8") as f:
    f.write("""Portfolio B - Client Notes
Client requested cognitive assessment for HLJ001 (鸿利佳食品股份有限公司)
Interview conducted: 2024-01-15
Interviewer: Research Team
Status: PENDING REPORT GENERATION
""")

# 10. A script file (distractor)
with open("workspace/tools/scripts/data_fetch.py", "w", encoding="utf-8") as f:
    f.write("""#!/usr/bin/env python3
# Data fetching utility - DO NOT MODIFY
import requests

def fetch_company_data(ticker):
    # Placeholder - connects to internal data API
    pass

def fetch_dividend_history(ticker, years=5):
    # Placeholder
    pass
""")

# 11. Another archived file (distractor)
with open("workspace/investment_research/archived_reports/2022/notes_template.txt", "w", encoding="utf-8") as f:
    f.write("""Research Notes Template
======================
Company: ___________
Analyst: ___________
Date: ___________

Thesis: 
Risk Factors:
Conclusion:
""")

# --- THE MAIN TASK FILE: Interview Transcript ---
# This is a messy, realistic transcript of an investor's answers
# Q1 (Business Model): Reasonably good but surface-level (score ~65%)
# Q2 (Moat): Mediocre, identifies moat vaguely but can't articulate durability (score ~50%)
# Q3 (Growth): Weak, vague and speculative, no concrete second curve (score ~30%)
# Q4 (Shareholder Return): Decent, knows dividends but doesn't understand reinvestment quality (score ~60%)
# Expected overall: (65+50+30+60)/4 = ~51% -> 🟡 初步懂

transcript_content = """投资认知访谈记录
=====================================
公司：鸿利佳食品股份有限公司（股票代码：HLJ001）
投资者：匿名散户（ID: INV-7821）
访谈日期：2024-01-15
访谈员：研究团队

=====================================
【问题一】这家公司是靠什么赚钱的？
请用三句话向一个没有投资经验的人解释：这家公司的钱是从哪来的？

投资者回答：
"鸿利佳食品主要是做调味品的，就是酱油、醋、蚝油这些。他们在全国各地有经销商，然后超市里卖给普通消费者。另外他们最近也搞了一些餐饮渠道，就是卖给饭店和连锁餐厅这些。"

追问1：这三件事，哪个是最大收入来源？哪个增长最快？
投资者回答：
"最大收入来源应该是酱油吧，好像占了60%以上。增长最快的我觉得是餐饮渠道，因为现在消费升级嘛，餐厅用的调味品要求更高，他们的高端产品在那边卖得好。"

追问2：这三件事，5年后还会是主要收入来源吗？
投资者回答：
"应该还是酱油为主吧，这个不会变。人总要吃饭的嘛，调味品这个需求不会消失。不过可能比例会有点变化，餐饮渠道占比会更高一点。"

=====================================
【问题二】这家公司能否持续赚钱？
这家公司的护城河是什么？为什么竞争对手不能抢走它的利润？

投资者回答：
"护城河嘛……我觉得是品牌吧。鸿利佳这个品牌在华南市场很有名，消费者认牌子买。另外他们产品质量也不错，用的原料比较好。"

追问1：这个护城河5年后是变强了还是变弱了？
投资者回答：
"我觉得差不多吧，品牌应该会维持的。不过竞争也挺激烈的，海天、李锦记这些大牌子也在抢市场，所以护城河可能不会变强太多。"

追问2：什么会削弱这个护城河？最可能的颠覆性因素是什么？
投资者回答：
"价格战吧？如果大品牌打价格战，他们可能会有压力。还有就是如果有什么食品安全问题的话会很麻烦。我觉得这是主要风险。"

=====================================
【问题三】这家公司能否赚更多的钱？
它未来的增长来自哪里？有没有第二增长曲线？

投资者回答：
"增长的话……我觉得他们还有很大空间，因为华北市场还没有完全打开。另外他们在做一些新产品，好像有健康系列什么的。总的来说我觉得还是有增长潜力的。"

追问1：它现在的增长是存量市场的份额抢夺，还是增量市场的扩张？
投资者回答：
"这个……应该两个都有吧？一方面他们在抢海天的份额，另一方面也有新消费者。我说不太清楚具体比例。"

追问2：如果主业增长放缓，它靠什么实现下一阶段增长？
投资者回答：
"我也不是很清楚，可能搞多元化？或者做出口？这块我没有深入研究过，感觉管理层应该有规划的。"

=====================================
【问题四】这家公司赚了钱能否分给我？
它历史分红情况如何？利润是真现金还是纸面利润？

投资者回答：
"分红的话他们每年都有分，我记得最近几年分红率大概在40%左右。利润应该是真实的，他们的现金流看起来不错，经营性现金流比净利润还高一点点。"

追问1：如果它不分红，钱会用来做什么？再投资回报率高吗？
投资者回答：
"不分红的钱应该用来扩厂或者搞营销吧。再投资回报率……这个我没算过，应该还好的，调味品这个行业资本回报率一般都不错。"

追问2：它的分红政策稳定吗？跟同行比如何？
投资者回答：
"稳定的，这几年基本上都保持在这个比例。跟同行比嘛，我觉得差不多，反正有分就行。具体跟海天或者千禾比我没有专门比较过。"

=====================================
访谈结束
备注：本次访谈已完整记录，待生成正式诊断报告。
=====================================
"""

with open("workspace/interview_transcript.txt", "w", encoding="utf-8") as f:
    f.write(transcript_content)

print("Workspace generated successfully.")
print("Key file: workspace/interview_transcript.txt")
print("Distractor files created in nested directories.")