import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/projects/mindwave_app",
    "workspace/projects/mindwave_app/research",
    "workspace/projects/mindwave_app/research/competitors",
    "workspace/projects/mindwave_app/research/raw_data",
    "workspace/projects/mindwave_app/marketing",
    "workspace/projects/mindwave_app/marketing/drafts",
    "workspace/projects/mindwave_app/product",
    "workspace/projects/mindwave_app/product/roadmap",
    "workspace/projects/mindwave_app/notes",
    "workspace/archive",
    "workspace/archive/2023",
    "workspace/archive/2023/reports",
    "workspace/templates",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/projects/mindwave_app/research/competitors/headspace_notes.txt": """Headspace:
- Founded 2010, US-based
- 70M+ downloads globally
- Subscription: $12.99/mo
- Focus: guided meditation, sleep
- Weakness: English-first, not localized for China
- No social features
""",
    "workspace/projects/mindwave_app/research/competitors/calm_analysis.txt": """Calm:
- Valuation $2B (2020)
- Celebrity narrators
- Heavy on sleep stories
- Corporate wellness B2B growing
- Weak on habit-tracking
""",
    "workspace/projects/mindwave_app/research/raw_data/survey_responses_q3.csv": """respondent_id,age,city,frequency,pain_point
001,28,Beijing,daily,"too busy to meditate"
002,34,Shanghai,weekly,"can't quiet my mind"
003,26,Shenzhen,monthly,"don't know where to start"
004,31,Hangzhou,daily,"work stress overwhelming"
005,29,Guangzhou,weekly,"sleep quality poor"
006,33,Beijing,daily,"anxiety about career"
007,27,Shanghai,monthly,"relationship stress"
008,35,Chengdu,weekly,"need work-life balance"
""",
    "workspace/projects/mindwave_app/research/raw_data/app_store_reviews_sample.txt": """Review 1 (★★★★★): "在地铁上15分钟就能做完一次练习，太适合我这种忙人了"
Review 2 (★★★☆☆): "界面太简陋了，感觉不够高级"
Review 3 (★★★★★): "帮我戒掉了失眠，真的救了我"
Review 4 (★★☆☆☆): "内容太少，一周就刷完了"
Review 5 (★★★★☆): "同事都在用，跟着一起用感觉更有动力坚然"
Review 6 (★★★★★): "下班后冥想15分钟，感觉整个人都重启了"
""",
    "workspace/projects/mindwave_app/marketing/drafts/tagline_ideas.txt": """Possible taglines:
- "每天15分钟，重新找回自己"
- "都市疲惫者的精神充电站"  
- "不是逃避，是充电"
- "让焦虑休息一会儿"
- "忙碌时代的内心慢行"
""",
    "workspace/projects/mindwave_app/marketing/drafts/channel_strategy_rough.txt": """Channels to consider:
- WeChat ecosystem (articles + mini-program)
- Douyin short video (meditation clips)
- Xiaohongshu (lifestyle positioning)
- Corporate HR partnerships
- KOL: wellness influencers

Budget estimate: 500K CNY for Q1 pilot
""",
    "workspace/projects/mindwave_app/product/roadmap/v1_features.txt": """MVP Feature List (debate ongoing):
[ ] 5-min guided breathing
[ ] 10-min body scan meditation  
[ ] Sleep stories (Mandarin)
[ ] Daily mood check-in
[ ] Progress streaks
[ ] Social sharing (controversial - team split)
[ ] Corporate team features
[ ] Offline mode
""",
    "workspace/projects/mindwave_app/product/roadmap/tech_stack_notes.txt": """Backend: Go microservices
CDN: Alibaba Cloud CDN
Audio streaming: HLS
DB: PostgreSQL + Redis
Analytics: Mixpanel (considering switching to domestic alternative)
Payment: WeChat Pay + Alipay
""",
    "workspace/projects/mindwave_app/notes/founder_braindump.txt": """Random thoughts 2024-03:
- The real competitor isn't other meditation apps — it's scrolling Douyin at midnight
- People don't want to meditate, they want to feel less shitty
- Corporate angle might be easier sales but kills the brand
- What makes someone become a DAILY user vs monthly?
- The "streak" mechanic is both our best retention tool and our biggest churn cause
- Need to figure out who is CORE user - can't serve everyone
- 焦虑 is the hook, 成就感 is the retention
""",
    "workspace/projects/mindwave_app/notes/investor_questions.txt": """Questions from Series A investors:
1. What is your DAU/MAU ratio?
2. Who is the core user and why will they pay?
3. What's stopping WeChat from building this?
4. How do you differentiate from free YouTube meditation content?
5. What is the LTV of a corporate vs consumer user?
""",
    "workspace/archive/2023/reports/market_size_estimate.txt": """China digital mental wellness market:
- 2022: RMB 8.3B
- 2025E: RMB 28B (CAGR ~50%)
- Penetration rate: <3% of population
- Key driver: COVID aftereffects, Gen-Z workplace stress
- Avg spend per active user: RMB 300-800/year
Source: iResearch 2022 (unverified)
""",
    "workspace/archive/2023/reports/failed_pivot_notes.txt": """Why the B2B-only pivot failed (Q2 2023):
- Corporate HR decision cycles: 6-9 months
- ROI hard to prove for wellness
- Employees don't use tools mandated by employer
- Killed product-user intimacy
- Returning to B2C with optional B2B layer
""",
    "workspace/templates/generic_market_report_template.txt": """# Market Analysis Template

## Executive Summary
[...]

## Market Size
[...]

## Target Segments  
[...]

## Competitive Landscape
[...]

## Recommendations
[...]
""",
}

for filepath, content in distractor_files.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# The core brief that the agent will use as input
brief_content = """# 产品简介：MindWave 正念冥想订阅App

## 产品描述
MindWave 是一款面向中国都市白领的正念冥想订阅App。
核心功能：5-20分钟引导冥想、呼吸练习、睡前故事、情绪打卡。
订阅价格：月费49元 / 年费298元。
当前阶段：产品已上市，但月活留存率偏低（Day30留存仅12%），
团队急需明确核心用户群，优化产品方向。

## 分析需求
需要完整的用户洞察分析（全流程），
最终输出一份可以直接给产品和营销团队使用的报告。
"""

with open("workspace/projects/mindwave_app/product_brief.md", "w", encoding="utf-8") as f:
    f.write(brief_content)

print("Workspace generated successfully.")
print("Files created:")
for filepath in list(distractor_files.keys()) + ["workspace/projects/mindwave_app/product_brief.md"]:
    print(f"  {filepath}")