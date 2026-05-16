import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create realistic distractor directory structure
dirs = [
    "campaigns/q1_2024",
    "campaigns/q2_2024",
    "campaigns/drafts",
    "brand_assets/logos",
    "brand_assets/fonts",
    "analytics/weekly_reports",
    "analytics/monthly_reports",
    "competitors/analysis",
    "templates/email",
    "templates/social",
    "archive/2023",
    "archive/2022",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "campaigns/q1_2024/brief.txt": "Q1 Campaign: Focus on brand awareness. Target: 18-35. Budget: $5000.",
    "campaigns/q1_2024/results.csv": "platform,impressions,clicks,conversions\nTwitter,12000,340,22\nInstagram,45000,1200,89\nLinkedIn,8000,120,15",
    "campaigns/q2_2024/brief.txt": "Q2 Campaign: Product launch. Theme: sustainability. KPIs: reach and engagement.",
    "campaigns/drafts/post_ideas.txt": "- Post about new protein powder\n- Behind the scenes at the gym\n- Recipe of the week\n- Collaboration with local athletes",
    "brand_assets/logos/brand_guide.txt": "Primary color: #2ECC71 (green)\nSecondary: #27AE60\nFont: Montserrat Bold for headers, Open Sans for body",
    "brand_assets/fonts/typography.txt": "Heading: 36px bold\nSubheading: 24px semibold\nBody: 16px regular",
    "analytics/weekly_reports/week_12.csv": "week,total_posts,avg_engagement_rate,top_platform\n12,21,4.2%,Instagram",
    "analytics/weekly_reports/week_11.csv": "week,total_posts,avg_engagement_rate,top_platform\n11,18,3.8%,Twitter",
    "analytics/monthly_reports/march_2024.txt": "Total impressions: 280,000. Best performing: Instagram Stories. Worst: LinkedIn polls.",
    "competitors/analysis/competitor_a.txt": "CompetitorA posts 3x/day on Instagram. Heavy use of Reels. Hashtag strategy: 8-12 per post.",
    "competitors/analysis/competitor_b.txt": "CompetitorB focuses on LinkedIn thought leadership. Posts long-form 2x/week.",
    "templates/email/newsletter_template.txt": "Subject: [TOPIC] — Weekly Digest\nPreheader: This week in [NICHE]\n\nHi [NAME],\nHere's what's happening in [TOPIC] this week...",
    "templates/social/old_twitter_template.txt": "OLD FORMAT (deprecated):\n[HOOK] + [CONTENT] + [CTA] + [HASHTAGS]\nMax: 140 chars (OLD LIMIT - DO NOT USE)",
    "archive/2023/content_calendar_v1.md": "# Old Content Calendar 2023\n## Week 1\n- Monday: Generic post about fitness\n- Tuesday: Product spotlight\n(This format is outdated)",
    "archive/2022/strategy_doc.txt": "2022 Strategy: Post 5x/week. Focus on Twitter. Ignore LinkedIn.\n(ARCHIVED - superseded by 2024 multi-platform strategy)",
    "analytics/monthly_reports/april_2024.txt": "April summary: Vegan content performed 34% better. Plant-based recipes got highest saves on Instagram.",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create the generate.sh script as it "already exists in the workspace"
# This script generates a real content-calendar.md following the SKILL.md spec
generate_sh = r'''#!/usr/bin/env bash
# Social Media Scheduler - Content Calendar Generator
# Usage: ./generate.sh "topic" ["target audience"]

TOPIC="${1:-general topic}"
AUDIENCE="${2:-general audience}"
OUTPUT="content-calendar.md"

cat > "$OUTPUT" << CALENDAR
# 📅 Weekly Content Calendar
**Topic:** ${TOPIC}
**Target Audience:** ${AUDIENCE}
**Generated:** $(date +%Y-%m-%d)

---

## Monday — Motivational / Week opener

### 🐦 Twitter/X
Start your week with the power of ${TOPIC}! 🚀 Small steps today lead to big wins by Friday. What's your #1 goal this week? Drop it below 👇 #${TOPIC// /} #MondayMotivation

**Best time:** 8:00 AM – 9:00 AM
**Hashtags:** #${TOPIC// /} #MondayMotivation #WeeklyGoals

---

### 💼 LinkedIn
Monday Mindset: The best time to start with ${TOPIC} was yesterday. The second best time is right now.

This week, I'm focused on helping ${AUDIENCE} unlock new possibilities through ${TOPIC}. Whether you're just starting out or looking to level up, the journey begins with a single intentional step.

What does success look like for you this week? Share in the comments — I read every reply.

**Best time:** 7:30 AM – 8:30 AM
**Hashtags:** #${TOPIC// /} #MondayMotivation #ProfessionalGrowth #Leadership #WeeklyGoals

---

### 📸 Instagram
New week, new opportunities ✨

This week we're diving deep into ${TOPIC} — crafted especially for ${AUDIENCE} who are ready to level up 💪

Whether you're a beginner or a seasoned pro, there's something here for you. Save this post and come back throughout the week as we drop daily value bombs 💣

Double tap if you're ready to make this week count! 👇

🔗 Full resources in bio link

**Best time:** 6:00 AM – 8:00 AM
**Hashtags:** #${TOPIC// /} #MondayMotivation #NewWeek #Goals #Inspired #LevelUp #Community #Growth #${AUDIENCE// /} #WeeklyVibes

---

## Tuesday — Educational / How-to

### 🐦 Twitter/X
Here's how ${AUDIENCE} can master ${TOPIC} in 3 steps: 1️⃣ Learn the fundamentals 2️⃣ Practice consistently 3️⃣ Track your progress 🎯 Which step trips you up most? #${TOPIC// /} #HowTo #Tips

**Best time:** 9:00 AM – 10:00 AM
**Hashtags:** #${TOPIC// /} #HowTo #Tips

---

### 💼 LinkedIn
How-To Guide: Getting Started with ${TOPIC}

I've spent years helping ${AUDIENCE} navigate ${TOPIC}, and the #1 mistake I see? Skipping the fundamentals.

Here's the framework that actually works:

▶ Step 1: Understand the core principles — don't skip this.
▶ Step 2: Apply them in low-stakes situations first.
▶ Step 3: Iterate based on real feedback, not assumptions.

The difference between those who struggle and those who thrive with ${TOPIC} almost always comes down to consistency in these three areas.

What would you add to this list? I'd love to hear from fellow ${AUDIENCE}.

**Best time:** 10:00 AM – 11:00 AM
**Hashtags:** #${TOPIC// /} #HowTo #Education #ProfessionalDevelopment #Tips

---

### 📸 Instagram
TUTORIAL TIME 📚✨

Everything ${AUDIENCE} need to know about ${TOPIC} — broken down step by step 👆 Swipe through for the full guide!

The secret? It's simpler than you think once you know the roadmap 🗺️

Save this post for reference and tag someone who needs to see this 👇

🔗 Free guide in bio!

**Best time:** 11:00 AM – 1:00 PM
**Hashtags:** #${TOPIC// /} #HowTo #Tutorial #LearnSomethingNew #Education #TipsAndTricks #Guide #${AUDIENCE// /} #Knowledge #Helpful

---

## Wednesday — Engagement / Question

### 🐦 Twitter/X
Hot take: ${TOPIC} is more important than ever for ${AUDIENCE}. Agree or disagree? Tell me why 👇 #${TOPIC// /} #DebateThis #Community

**Best time:** 12:00 PM – 1:00 PM
**Hashtags:** #${TOPIC// /} #DebateThis #Community

---

### 💼 LinkedIn
I want to hear from you — the ${AUDIENCE} community.

When it comes to ${TOPIC}, what's the ONE question you wish someone had answered for you sooner?

I'm compiling the top questions for a dedicated post next week. Drop yours in the comments. Every response gets read, and the most common themes will shape our content for the next month.

No question is too basic. The "obvious" questions are often the most important ones.

**Best time:** 12:00 PM – 2:00 PM
**Hashtags:** #${TOPIC// /} #Community #Question #Engagement #Discussion

---

### 📸 Instagram
Let's settle this once and for all 🙋‍♀️

When it comes to ${TOPIC}... what camp are you in? Comment below with your answer!

We love hearing from our ${AUDIENCE} community — your perspectives shape everything we create 💬

Tag your friend who has the OPPOSITE opinion 😂

**Best time:** 6:00 PM – 8:00 PM
**Hashtags:** #${TOPIC// /} #ThisOrThat #CommunityQuestion #Engage #LetsTalk #Poll #${AUDIENCE// /} #Discussion #Opinion #ShareYourThoughts

---

## Thursday — Behind-the-scenes / Story

### 🐦 Twitter/X
Real talk: building content around ${TOPIC} for ${AUDIENCE} isn't always glamorous. Here's what a real workday looks like 🧵 (thread) #${TOPIC// /} #BehindTheScenes #Authentic

**Best time:** 8:00 AM – 10:00 AM
**Hashtags:** #${TOPIC// /} #BehindTheScenes #Authentic

---

### 💼 LinkedIn
The Story Behind Our ${TOPIC} Journey

Not many people talk about the messy middle — the part between "I have an idea" and "this actually works."

When we first started creating content for ${AUDIENCE} around ${TOPIC}, we made every mistake in the book. We posted at the wrong times. We used jargon nobody understood. We solved problems people didn't actually have.

The turning point? We started listening more than talking.

Three things that changed everything:
1. Customer conversations became our content calendar.
2. We stopped chasing trends and started setting them.
3. We measured outcomes, not just outputs.

If you're in the messy middle right now — keep going. The clarity comes.

**Best time:** 9:00 AM – 10:00 AM
**Hashtags:** #${TOPIC// /} #BehindTheScenes #Storytelling #Entrepreneurship #Authentic

---

### 📸 Instagram
Behind the scenes of creating this space for ${AUDIENCE} 👀✨

Not everything is perfectly curated — and honestly? That's the point 💯

${TOPIC} has taught us that authenticity always wins over perfection. Here's a peek into our real process, real challenges, and real wins 🙌

What do you want to see more BTS content about? Tell us in the comments 👇

**Best time:** 3:00 PM – 5:00 PM
**Hashtags:** #${TOPIC// /} #BehindTheScenes #Authentic #RealTalk #Process #${AUDIENCE// /} #Transparency #ContentCreation #BTS #Community

---

## Friday — Tip / Quick win

### 🐦 Twitter/X
Friday tip for ${AUDIENCE}: The fastest way to improve your ${TOPIC} results? Do one thing differently this weekend. Just one. 🎯 Save this tweet. Thank me Monday. #${TOPIC// /} #FridayTip #QuickWin

**Best time:** 9:00 AM – 11:00 AM
**Hashtags:** #${TOPIC// /} #FridayTip #QuickWin

---

### 💼 LinkedIn
Friday Quick Win: The 5-Minute ${TOPIC} Audit

Before you close your laptop today, spend 5 minutes on this:

✅ Identify your biggest win this week related to ${TOPIC}
✅ Name one thing you'd do differently
✅ Write down one specific action for next week

That's it. Five minutes. This simple habit has helped countless ${AUDIENCE} achieve more consistent results with ${TOPIC} than any complex system I've seen.

Happy Friday — you earned the weekend.

**Best time:** 9:00 AM – 10:00 AM
**Hashtags:** #${TOPIC// /} #FridayTip #QuickWin #Productivity #WeeklyReview

---

### 📸 Instagram
FRIDAY TIP 🙌🎉

One quick win for ${AUDIENCE} to end the week strong with ${TOPIC} 💥

Screenshot this. Put it somewhere you'll see it. Make it happen this weekend 📲

Drop a 🙌 if you're implementing this TODAY!

🔗 More tips like this in the link in bio

**Best time:** 11:00 AM – 1:00 PM
**Hashtags:** #${TOPIC// /} #FridayTip #QuickWin #TGIF #WeekendVibes #${AUDIENCE// /} #ProTip #LifeHack #TipOfTheDay #FridayFeeling

---

## Saturday — Curated / Industry news

### 🐦 Twitter/X
Roundup: The top ${TOPIC} stories you might have missed this week 📰 Curated for ${AUDIENCE} who want to stay ahead of the curve 👇 #${TOPIC// /} #WeeklyRoundup #IndustryNews

**Best time:** 10:00 AM – 12:00 PM
**Hashtags:** #${TOPIC// /} #WeeklyRoundup #IndustryNews

---

### 💼 LinkedIn
This Week in ${TOPIC}: What ${AUDIENCE} Need to Know

The landscape around ${TOPIC} is evolving fast. Here's my curated take on what mattered most this week:

🔍 Emerging trends worth watching
📊 Data points that challenge conventional wisdom  
💡 Insights from leading voices in the space

Staying informed isn't just good practice — for ${AUDIENCE}, it's a competitive advantage. The people who act on early signals are the ones who lead.

What caught your attention in ${TOPIC} this week? Add your links and takes below.

**Best time:** 10:00 AM – 12:00 PM
**Hashtags:** #${TOPIC// /} #IndustryNews #Trends #Curated #WeeklyRoundup

---

### 📸 Instagram
WEEKLY ROUNDUP 📰🔍

The ${TOPIC} news ${AUDIENCE} are talking about this week 👆

Stay ahead of the curve by knowing what's happening in your space. Knowledge is power 💪

Save this for reference and share with someone in the ${TOPIC} space 🔁

**Best time:** 10:00 AM – 12:00 PM
**Hashtags:** #${TOPIC// /} #WeeklyRoundup #IndustryNews #StayInformed #${AUDIENCE// /} #Curated #Trending #NewsYouCanUse #SaturdayReads #KnowledgeIsPower

---

## Sunday — Reflection / Community

### 🐦 Twitter/X
Sundays are for reflection 🌿 What did ${TOPIC} teach you this week? Share your biggest insight — your words might inspire another ${AUDIENCE} member 💬 #${TOPIC// /} #SundayReflection #Community

**Best time:** 5:00 PM – 7:00 PM
**Hashtags:** #${TOPIC// /} #SundayReflection #Community

---

### 💼 LinkedIn
Sunday Reflection: What ${TOPIC} Taught Me This Week

Growth rarely looks the way we expect it to.

This week, working within the ${TOPIC} space and engaging with our ${AUDIENCE} community reminded me of something fundamental: progress is always happening, even when it's invisible.

Take a moment today to reflect on:
- What worked for you this week in relation to ${TOPIC}?
- What will you approach differently next week?
- Who in your community deserves a shout-out?

Gratitude and reflection aren't soft skills — they're strategic ones. See you Monday with fresh energy.

**Best time:** 6:00 PM – 8:00 PM
**Hashtags:** #${TOPIC// /} #SundayReflection #Community #Gratitude #WeeklyReview

---

### 📸 Instagram
Sunday reset 🌿✨

Taking a moment to reflect on this week's ${TOPIC} journey with our incredible ${AUDIENCE} community 💛

Every week we grow a little more. Every post, every comment, every share — it builds something real 🏗️

Drop a gratitude below 👇 What are you thankful for this week?

See you Monday for another week of value 🚀

**Best time:** 6:00 PM – 8:00 PM
**Hashtags:** #${TOPIC// /} #SundayReflection #Community #Gratitude #${AUDIENCE// /} #WeeklyWrapUp #Mindfulness #SundayVibes #Reflect #CommunityLove

---

*Generated by Social Media Scheduler 📅 | Customize each post before publishing!*
CALENDAR

echo "✅ Content calendar generated: $OUTPUT"
echo "📊 21 posts ready (7 days × 3 platforms)"
echo "🎯 Topic: ${TOPIC} | Audience: ${AUDIENCE}"
'''

generate_sh_path = os.path.join(workspace, "generate.sh")
with open(generate_sh_path, "w") as f:
    f.write(generate_sh)

os.chmod(generate_sh_path, os.stat(generate_sh_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Create a misleading/outdated content calendar to tempt the agent into editing it
old_calendar = """# Content Calendar (OUTDATED)
## Topic: generic content
## Week of: 2023-01-01

Monday: Post something motivational
Tuesday: Share a tip
...
(This file is from an old campaign and is no longer valid)
"""

with open(os.path.join(workspace, "archive", "2023", "old_content_calendar.md"), "w") as f:
    f.write(old_calendar)

# Add a confusing partial template
partial_template = """# Partial Social Media Draft
Topic: plant-based nutrition
NOTE: This is incomplete and was never finished. Do not use.

Monday Twitter: [DRAFT] Something about plants... (INCOMPLETE)
"""

with open(os.path.join(workspace, "campaigns", "drafts", "partial_draft.md"), "w") as f:
    f.write(partial_template)

# Add a brand voice document that mentions the audience
brand_voice = """# Brand Voice Document
Target Persona: Health-conscious Gen Z individuals (ages 18-26)
Niche: Plant-based nutrition and vegan fitness
Tone: Energetic, evidence-based, inclusive
Platform priority: Instagram > Twitter > LinkedIn
Note: Our audience responds best to authentic, science-backed content.
"""

with open(os.path.join(workspace, "brand_assets", "brand_voice.txt"), "w") as f:
    f.write(brand_voice)

# Add a social media policy doc
policy_doc = """# Social Media Policy
All posts must:
- Be factually accurate
- Include appropriate hashtags per platform
- Be reviewed before posting
- Never make unsubstantiated health claims
- Always include a call to action
"""

with open(os.path.join(workspace, "templates", "social", "social_media_policy.txt"), "w") as f:
    f.write(policy_doc)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")