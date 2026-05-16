import os
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "/workspace/marketing/drafts/old",
    "/workspace/marketing/templates/wechat",
    "/workspace/marketing/templates/weibo",
    "/workspace/marketing/assets/images",
    "/workspace/marketing/assets/icons",
    "/workspace/content/research/remote_work",
    "/workspace/content/research/agile",
    "/workspace/content/approved/2023",
    "/workspace/content/approved/2024",
    "/workspace/internal/brand_guidelines",
    "/workspace/internal/tone_guides",
    "/workspace/internal/competitor_analysis",
    "/workspace/tools/scripts",
    "/workspace/tools/configs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files with realistic but unhelpful content

distractor_files = {
    "workspace/marketing/drafts/old/draft_v1.md": """# Remote Work Benefits
    
Remote work has many advantages. Employees can work from anywhere.
Companies save on office space. Communication tools like Slack help teams stay connected.

This is an old draft that was never published.
""",

    "workspace/marketing/drafts/old/draft_v2.txt": """Title: Why Remote Teams Fail
Content: Most remote teams fail because of communication issues.
Status: REJECTED
Reason: Too negative, needs revision
""",

    "workspace/marketing/templates/wechat/old_template.html": """<div class="article">
<h1>{{title}}</h1>
<p>{{content}}</p>
<img src="{{image_url}}" />
</div>
<!-- Old HTML template - DEPRECATED, no longer used -->
""",

    "workspace/marketing/templates/weibo/weibo_template.txt": """微博模板 (140字以内)
话题标签: #远程办公# #效率# 
正文: [写在这里]
@相关账号
""",

    "workspace/marketing/assets/icons/emoji_list.txt": """Available emojis for articles:
💡 - tip/idea
🎯 - goal/target  
🔥 - trending/hot
✅ - checklist/done
📈 - growth
💬 - discussion/comment
⚡ - quick/fast
🌟 - star/highlight
""",

    "workspace/content/research/remote_work/stats_2024.csv": """metric,value,source
remote_workers_globally,35%,Buffer 2024
productivity_increase,13%,Stanford Study
communication_overhead,40%,McKinsey
meeting_hours_per_week,23,Microsoft Work Index
burnout_rate,67%,Gallup 2024
""",

    "workspace/content/research/remote_work/challenges.txt": """Top Remote Work Challenges (Survey Results):
1. Communication gaps across time zones (78%)
2. Lack of team cohesion (65%)
3. Difficulty separating work from personal life (61%)
4. Technical issues and tool fragmentation (54%)
5. Reduced visibility for career growth (48%)
6. Meeting fatigue and async overload (42%)
""",

    "workspace/content/research/agile/scrum_notes.md": """# Scrum for Remote Teams

Daily standups should be async when teams span 3+ time zones.
Use tools like Loom for async video updates.
Sprint reviews need special facilitation for distributed teams.

Key metrics to track:
- Velocity trends
- Sprint goal achievement rate
- Team happiness index
""",

    "workspace/content/approved/2024/article_leadership.md": """# 领导力的三个维度

（这篇文章已发布，请勿修改）

在当今快速变化的商业环境中，领导力需要与时俱进...
""",

    "workspace/content/approved/2023/best_performer.txt": """BEST PERFORMING ARTICLES 2023:
1. "5个让会议效率翻倍的方法" - 45,000 reads, 2,300 shares
2. "为什么你越努力越焦虑" - 38,000 reads, 1,900 shares  
3. "远程工作的7个生产力陷阱" - 31,000 reads, 1,500 shares
""",

    "workspace/internal/brand_guidelines/voice_guide.txt": """Brand Voice Guidelines:
- Professional yet approachable
- Data-driven but human
- Solution-focused
- Avoid corporate jargon
- Target audience: tech professionals, managers, 28-45 years old
""",

    "workspace/internal/tone_guides/platform_notes.txt": """Platform-Specific Notes:

WeChat Official Account:
- Readers scan on mobile
- Avg reading time: 3-5 minutes
- High share rate for practical tips
- Author field important for credibility

Weibo:
- Short-form, conversational
- Hashtag heavy
- Real-time trending topics

LinkedIn (EN):
- Professional tone only
- No emojis in body
- Data and case studies perform well
""",

    "workspace/internal/competitor_analysis/competitor_formats.md": """# Competitor Article Analysis

Competitor A uses pure listicle format - works for quick reads
Competitor B focuses on long-form storytelling - good for premium positioning
Competitor C mixes formats - inconsistent but high volume

**Observation**: Our gap is in practical how-to content with emotional hooks.
| Competitor | Avg Length | Engagement Rate |
|------------|------------|-----------------|
| A          | 800 words  | 3.2%            |
| B          | 2500 words | 5.1%            |
| C          | 1200 words | 2.8%            |
""",

    "workspace/tools/configs/publish_config.json": """{
  "platform": "wechat",
  "account_name": "远程协作研究院",
  "author": "张明远",
  "default_category": "职场技能",
  "auto_publish": false,
  "review_required": true
}
""",

    "workspace/tools/scripts/word_counter.sh": """#!/bin/bash
# Simple word counter for Chinese articles
echo "Word count: $(wc -w $1)"
echo "Character count: $(wc -c $1)"
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join("/", filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create the brief/requirements file that the agent should use as input
brief_content = """=== CONTENT BRIEF ===

Project: WeChat Official Account Article
Account: 远程协作研究院 (Remote Collaboration Institute)
Author Name: 张明远
Requested by: Marketing Director, Chen Wei

TOPIC: How to build effective remote team collaboration for tech companies

BACKGROUND:
Our readers are mid-level managers and team leads at Chinese tech companies (28-45 years old) 
who are struggling with hybrid/remote work setups post-pandemic. Many report that their 
teams feel disconnected, meetings are unproductive, and async communication creates delays.

OBJECTIVE:
Write a practical, actionable article that will help these managers solve real remote 
collaboration problems. The article should position our account as a go-to resource for 
workplace effectiveness.

TARGET OUTCOME:
High share rate — readers should feel compelled to forward this to their team or manager.
We want readers to leave a comment about their own remote work struggle.

DESIRED LENGTH: Standard length article (not a quick read)

NOTES FROM MARKETING DIRECTOR:
"Our last article flopped because it was too abstract. This one MUST have concrete steps 
people can actually do on Monday morning. Also, do NOT use any table formatting that 
our WeChat editor can't display properly — we had that problem before and it broke 
the article layout. Use plain text for any comparison or tabular info."

DELIVERABLE:
Save the final article as: remote_team_article.md
"""

with open("/workspace/brief.txt", "w", encoding="utf-8") as f:
    f.write(brief_content)

print("Workspace generated successfully.")
print("Files created:")
for f in distractor_files:
    print(f"  /{f}")
print("  /workspace/brief.txt")