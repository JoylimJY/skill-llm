import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "brand/guidelines/drafts",
    "brand/guidelines/approved",
    "brand/assets/logos",
    "brand/assets/fonts",
    "social/instagram/q1",
    "social/weibo/campaigns",
    "social/tiktok/scripts",
    "seo/keywords/research",
    "seo/blog/drafts",
    "growth/experiments/archive",
    "growth/metrics/q3",
    "internal/briefs/2024",
    "internal/meeting_notes",
    "competitors/analysis/raw",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (messy, realistic) ---
distractor_files = {
    "brand/guidelines/drafts/brand_voice_v1.txt": """\
DRAFT - NOT FINAL
Brand voice: eco-conscious, youthful, empowering
Tone: casual but credible
Colors: earth tones, forest green, off-white
--- needs CMO approval ---
""",
    "brand/guidelines/approved/color_palette.json": json.dumps({
        "primary": "#3D7A4E",
        "secondary": "#F5ECD7",
        "accent": "#E8A838",
        "note": "Pantone approved 2024"
    }, indent=2),
    "brand/assets/logos/logo_usage.txt": "Logo must have 20px clearance on all sides. Never stretch. Never rotate.",
    "social/instagram/q1/post_ideas.txt": """\
Post 1: Behind the scenes factory tour
Post 2: Customer testimonials
Post 3: Sustainability stats infographic
(Not approved yet)
""",
    "social/weibo/campaigns/spring_campaign_brief.txt": """\
Campaign: 绿色春天
Target: 25-35 urban females
Budget: ¥50,000
Status: PAUSED
""",
    "social/tiktok/scripts/unboxing_script.txt": """\
[Scene 1] Open box dramatically
[Scene 2] Show fabric texture close up
[Scene 3] Try on outfit, smile at camera
Music: trending lo-fi
""",
    "seo/keywords/research/keyword_list_raw.csv": """\
keyword,volume,difficulty
sustainable fashion,12000,78
eco friendly clothes,8500,65
环保服装,45000,55
可持续时尚,32000,48
小红书穿搭,95000,80
""",
    "seo/blog/drafts/why_fast_fashion_fails.md": """\
# Why Fast Fashion is Failing Gen Z
(DRAFT - incomplete)

Gen Z consumers are increasingly aware of...
[TODO: add statistics]
[TODO: add brand examples]
""",
    "growth/experiments/archive/experiment_log_q2.json": json.dumps([
        {"id": "EXP-001", "type": "A/B test", "channel": "WeChat", "result": "inconclusive", "lift": 0.02},
        {"id": "EXP-002", "type": "referral", "channel": "Xiaohongshu", "result": "positive", "lift": 0.18},
        {"id": "EXP-003", "type": "influencer", "channel": "Douyin", "result": "negative", "lift": -0.05},
    ], indent=2, ensure_ascii=False),
    "growth/metrics/q3/kpi_tracker_stub.txt": """\
Q3 KPIs (STUB - needs data)
MAU target: 50,000
CAC target: < ¥35
Conversion rate target: > 3.5%
NPS target: > 40
""",
    "internal/briefs/2024/product_brief.txt": """\
Product: EcoThread App
Category: Sustainable fashion marketplace
Target demographic: Gen Z, 18-28, urban China
Key features:
  - Second-hand clothing exchange
  - Carbon footprint tracker per item
  - Community styling challenges
  - Brand transparency scores
USP: Every purchase plants a tree
Launch market: Tier 1 cities (Beijing, Shanghai, Shenzhen, Chengdu)
App stores: iOS + Android
Referral code system: built-in
""",
    "internal/meeting_notes/kick_off_2024_09_12.txt": """\
Attendees: Marketing Lead, Growth Lead, Content Lead, CEO
Discussed: Launch strategy for EcoThread
Key decision: Prioritize Xiaohongshu for Gen Z reach
Action items:
  - Content team: produce launch content package
  - Growth team: define first 90-day experiment plan
  - Brand team: finalize tone of voice
Next meeting: TBD
""",
    "competitors/analysis/raw/competitor_snapshot.txt": """\
Competitor A: XiuXiu (已下线)
Competitor B: 好物严选 - strong WeChat presence, weak XHS
Competitor C: 环保衣橱 - niche, high engagement but low MAU
Gap identified: No competitor owns the "fun + sustainable" positioning on XHS
""",
    "internal/briefs/2024/content_request.txt": """\
REQUEST FROM MARKETING DIRECTOR - URGENT

We are launching EcoThread (可持续时尚交换平台) next month.
We need a complete content package targeting Gen Z users on Xiaohongshu.

Deliverable required: content_package.md

The package should cover:
1. A publish-ready Xiaohongshu post promoting the EcoThread app
2. A creatively enhanced / more fun version of that post
3. A growth hacking strategy for user acquisition in the first 90 days

All three sections should be written by the appropriate content expert persona.
Each section must be clearly labeled with which expert is handling it.
The content must be realistic, complete, and immediately usable — not placeholder templates.
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace initialized with distractor files.")
print(f"Agent should read internal/briefs/2024/content_request.txt for the task.")