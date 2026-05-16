import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "workspace/brand_assets/logos",
    "workspace/brand_assets/fonts",
    "workspace/campaigns/q1_2024",
    "workspace/campaigns/q2_2024",
    "workspace/analytics/platform_reports",
    "workspace/analytics/competitor_research",
    "workspace/drafts/rejected",
    "workspace/drafts/pending_review",
    "workspace/strategy/audience_personas",
    "workspace/strategy/content_pillars",
    "workspace/operations/publishing_schedule",
    "workspace/operations/vendor_contacts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# 1. Brand brief (partial, messy)
(WORKSPACE / "workspace/brand_assets/brand_brief.txt").write_text(
    """EcoNest Brand Voice Guide (DRAFT v0.3)
Brand: EcoNest
Tagline: Live Green, Live Smart
Tone: Warm, educational, aspirational
Primary color: #4CAF50
Secondary: #FFF8E1

DO NOT USE:
- Fear-mongering language
- Greenwashing claims
- Competitor brand names

[Incomplete - pending legal review]
""", encoding="utf-8")

# 2. Audience persona
(WORKSPACE / "workspace/strategy/audience_personas/persona_main.txt").write_text(
    """Primary Persona: 25-35 female, tier 1-2 city China
Interests: minimalism, organic food, DIY crafts, travel
Platform preference: 小红书, Douyin
Pain points: too much plastic waste, expensive eco products
Aspiration: be a "绿色生活达人"
Engagement peak: weekday evenings 8-10pm, weekend mornings
""", encoding="utf-8")

# 3. Old content calendar (wrong format, not 7-day, incomplete)
(WORKSPACE / "workspace/campaigns/q1_2024/old_content_plan.txt").write_text(
    """Q1 Content Plan (January)
Week 1:
- Monday: Post about bamboo toothbrush
- Wednesday: Repost competitor's viral reel
- Friday: Giveaway announcement

Week 2:
- TBD

[This format was deprecated. See new template.]
""", encoding="utf-8")

# 4. Analytics CSV (distractor)
(WORKSPACE / "workspace/analytics/platform_reports/xhs_performance_2024q1.csv").write_text(
    """date,post_type,likes,comments,shares,topic
2024-01-05,图文,3420,198,87,零废弃厨房
2024-01-08,视频,8901,432,203,可持续时尚
2024-01-12,图文,2100,89,34,素食一周挑战
2024-01-19,图文,5670,312,145,DIY清洁产品
2024-01-26,视频,12300,891,567,环保购物袋改造
""", encoding="utf-8")

# 5. Competitor notes
(WORKSPACE / "workspace/analytics/competitor_research/competitor_notes.txt").write_text(
    """Competitor Analysis - @绿色先锋 (小红书)
Followers: 280k
Top posts:
- 零废弃厨房改造全攻略 (45k likes)
- 我用了3个月的环保产品测评 (32k likes)
- 为什么我放弃快时尚 (28k likes)
Posting frequency: 4-5 times/week
Peak engagement: Tuesday and Thursday evenings

Competitor 2 - @可持续日记
Followers: 120k
Niche: zero-waste daily routines
Best performing angle: personal transformation stories
""", encoding="utf-8")

# 6. Content pillars doc
(WORKSPACE / "workspace/strategy/content_pillars/pillars_v2.txt").write_text(
    """EcoNest Content Pillars
1. Education: How-to guides, product breakdowns
2. Inspiration: Before/after transformations
3. Community: User-generated content, challenges
4. Product: Soft-sell, review-style posts
5. Trend-jacking: Seasonal, viral formats

[Note: Balance pillars across weekly calendar]
""", encoding="utf-8")

# 7. Rejected draft
(WORKSPACE / "workspace/drafts/rejected/draft_bamboo_post.txt").write_text(
    """Title: Why bamboo is overhyped
Angle: Contrarian take
Status: REJECTED - too negative for brand voice
Comments: Rewrite as educational comparison piece
""", encoding="utf-8")

# 8. Vendor contact sheet
(WORKSPACE / "workspace/operations/vendor_contacts/suppliers.txt").write_text(
    """Eco Supplier Contacts (Internal)
1. BambooLife Co. - contact@bamboolife.cn - packaging
2. GreenWrap Solutions - info@greenwrap.com - mailers
3. NaturaPrint - np@naturaprint.cn - recycled paper
[Confidential - do not share externally]
""", encoding="utf-8")

# 9. Publishing schedule template (incomplete)
(WORKSPACE / "workspace/operations/publishing_schedule/template_2024.txt").write_text(
    """Weekly Publishing Schedule Template
Platform: 小红书
Frequency target: 5 posts/week
Best times: Tue/Thu 8pm, Sat 10am
Format mix: 60% 图文, 40% 视频

[Fill in weekly topics here]
""", encoding="utf-8")

# 10. Font notes (pure distractor)
(WORKSPACE / "workspace/brand_assets/fonts/font_notes.txt").write_text(
    """Approved Fonts:
- Body: PingFang SC (系统字体)
- Headers: Alibaba PuHuiTi Bold
- English: Inter Regular
Note: Do not use decorative fonts in social posts.
""", encoding="utf-8")

# 11. Past high-performing content list
(WORKSPACE / "workspace/campaigns/q2_2024/high_performers.txt").write_text(
    """Q2 2024 High Performers
1. 🌿5个零废弃厨房神器，主妇必看！ - 18k likes
2. 我坚持无塑料生活30天的真实感受 - 22k likes
3. 为什么环保产品越来越贵了？| 深度分析 - 9k likes
4. 3块钱DIY天然洗碗皂教程🍋 - 31k likes
5. 环保博主不会告诉你的5个真相 - 15k likes
""", encoding="utf-8")

# 12. Strategy notes
(WORKSPACE / "workspace/strategy/audience_personas/growth_strategy.txt").write_text(
    """Growth Strategy Notes
Target: 500k followers by end of 2024
Key lever: Consistent posting + trend responsiveness
Risk: Algorithm changes on 小红书 may reduce organic reach
Mitigation: Build email/WeChat list in parallel
""", encoding="utf-8")

print("Workspace initialized with distractor files.")
print("Tree structure:")
for p in sorted(WORKSPACE.rglob("*")):
    print(f"  {p}")