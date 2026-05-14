import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "campaigns/q1_2024",
    "campaigns/q2_2024/drafts",
    "campaigns/q2_2024/approved",
    "analytics/social",
    "analytics/email",
    "brand/assets/logos",
    "brand/guidelines",
    "team/onboarding",
    "archive/2023/posts",
    "archive/2023/metrics",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# distractor files
distractors = {
    "campaigns/q1_2024/brief.txt": "Q1 campaign focused on brand awareness.\nBudget: $50,000\nChannels: Twitter, LinkedIn",
    "campaigns/q1_2024/performance.csv": "platform,impressions,clicks,ctr\nTwitter,120000,3400,2.83\nLinkedIn,45000,1200,2.67\nInstagram,89000,4100,4.61",
    "campaigns/q2_2024/drafts/ideas.txt": "- Thought leadership series\n- Customer spotlight posts\n- Product demo clips",
    "campaigns/q2_2024/approved/post_001.txt": "Check out our latest health tips! Stay well. #health",
    "campaigns/q2_2024/approved/post_002.txt": "Monday motivation: Small steps lead to big changes. #wellness",
    "analytics/social/summary_march.csv": "week,engagement_rate,follower_growth\nWk1,4.2,320\nWk2,3.8,290\nWk3,5.1,410",
    "analytics/email/open_rates.txt": "Average open rate: 24.3%\nBest day: Tuesday\nWorst day: Sunday",
    "brand/guidelines/tone_of_voice.txt": "Our brand voice is: warm, professional, evidence-based.\nAvoid: jargon, fear-mongering, unsubstantiated claims.",
    "brand/assets/logos/logo_notes.txt": "Primary logo: navy blue (#0A2463)\nSecondary: teal (#3E92CC)",
    "team/onboarding/social_media_checklist.txt": "1. Review brand guidelines\n2. Join scheduling tool\n3. Shadow senior editor for 2 weeks",
    "archive/2023/posts/top_performers.txt": "Top post 2023: 'Five ways to beat burnout' - 12k impressions",
    "archive/2023/metrics/yearly_summary.txt": "Total impressions: 2.4M\nTop platform: Instagram\nLowest: LinkedIn (but highest quality leads)",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── generate.sh — the proprietary script ────────────────────────────────────
# This script generates a FULL content calendar with strict platform rules
generate_sh = r"""#!/usr/bin/env bash
# Social Media Scheduler - generate.sh
# Usage: ./generate.sh <topic> [target_audience]

TOPIC="${1:-general}"
AUDIENCE="${2:-general audience}"
OUTPUT="content-calendar.md"

cat > "$OUTPUT" << CALENDAR
# Content Calendar: ${TOPIC}
**Target Audience:** ${AUDIENCE}
**Generated:** $(date +%Y-%m-%d)

---

## Monday — Motivational / Week Opener

### Twitter/X
Start your week strong! Mastering ${TOPIC} begins with one small step today. What's your Monday goal? Drop it below 👇 #${TOPIC// /} #MondayMotivation #Goals

**Best time:** 8:00 AM
**Hashtags:** #${TOPIC// /} #MondayMotivation #Goals

### LinkedIn
Every expert in ${TOPIC} started exactly where you are now — at the beginning.

This week, I challenge you and your team to pick one area of ${TOPIC} to improve. The compounding effect of consistent, small actions targeted at ${AUDIENCE} is what separates good professionals from great ones.

What's one thing about ${TOPIC} you've been putting off? Share it in the comments — accountability starts here.

**Best time:** 7:30 AM
**Hashtags:** #${TOPIC// /} #ProfessionalDevelopment #MondayMotivation #Leadership #Growth

### Instagram
✨ New week, new possibilities with ${TOPIC}! ✨

Whether you're just starting your journey or you're a seasoned pro, every Monday is a chance to reset and refocus on what matters most.

This week we're diving deep into ${TOPIC} — specifically for ${AUDIENCE}. Are you ready?

Save this post for your weekly reminder 📌
Link in bio for our full ${TOPIC} guide!

**Best time:** 9:00 AM
**Hashtags:** #${TOPIC// /} #MondayMotivation #NewWeek #Goals #Wellness #Growth #Community #Inspiration #WeeklyGoals #SaveThis

---

## Tuesday — Educational / How-to

### Twitter/X
3 things about ${TOPIC} they don't teach you: 1) Consistency > intensity 2) Community accelerates growth 3) Rest is part of the process. Thread coming Thursday 🧵 #${TOPIC// /} #LearnSomethingNew #Tips

**Best time:** 9:00 AM
**Hashtags:** #${TOPIC// /} #LearnSomethingNew #Tips

### LinkedIn
**How ${AUDIENCE} can master ${TOPIC} in 30 days:**

Most people approach ${TOPIC} the wrong way. They focus on the outcome rather than the system. Here's a framework I've seen work consistently:

**Week 1:** Audit your current baseline
**Week 2:** Identify the 20% of actions that drive 80% of results
**Week 3:** Build a sustainable daily habit
**Week 4:** Review, adjust, and share your learnings

The professionals who succeed in ${TOPIC} aren't the most talented — they're the most consistent. Which week would you start with?

**Best time:** 12:00 PM
**Hashtags:** #${TOPIC// /} #HowTo #Education #ProfessionalGrowth #LearningAndDevelopment

### Instagram
📚 SWIPE to learn the 3-step framework for ${TOPIC} that every ${AUDIENCE} needs to know!

Step 1: Start with WHY — your purpose fuels your persistence
Step 2: Build your environment for success
Step 3: Track what actually matters (hint: it's not what you think)

Tag someone who needs to see this! 👇
More tips daily — follow along and tap the link in bio!

**Best time:** 6:00 PM
**Hashtags:** #${TOPIC// /} #Education #HowTo #LearnEveryDay #Tips #Tutorial #Knowledge #Growth #SwipeLeft #TagAFriend

---

## Wednesday — Engagement / Question

### Twitter/X
Honest question for ${AUDIENCE}: What's the #1 thing holding you back from ${TOPIC}? I read every reply. 👇 #${TOPIC// /} #CommunityQuestion #AskYourAudience

**Best time:** 12:00 PM
**Hashtags:** #${TOPIC// /} #CommunityQuestion #AskYourAudience

### LinkedIn
I'd love your perspective on something.

After speaking with dozens of professionals about ${TOPIC}, I keep hearing the same themes. But I want to hear from you directly: **What is the single biggest challenge you face with ${TOPIC}?**

A) Finding reliable information
B) Consistency and accountability
C) Time and resources
D) Something else entirely

Drop your answer in the comments — I'll compile the results and share insights next week. Your experience shapes better content for our entire ${AUDIENCE} community.

**Best time:** 10:00 AM
**Hashtags:** #${TOPIC// /} #Poll #CommunityEngagement #LinkedIn #Discussion

### Instagram
💬 THIS OR THAT: ${TOPIC} edition!

Which approach do you prefer? Comment A or B below!

A) Learn everything first, then take action
B) Take action immediately, learn as you go

There's no wrong answer — we're all different! But this tells us a LOT about how to best serve our ${AUDIENCE} community.

Share this to your stories and tag us in your answer! 🔁

**Best time:** 7:00 PM
**Hashtags:** #${TOPIC// /} #ThisOrThat #Poll #Engagement #Community #Question #InteractWithUs #AskMe #YourThoughts #ShareThis

---

## Thursday — Behind-the-scenes / Story

### Twitter/X
Real talk: when I started with ${TOPIC}, I failed 7 times before anything worked. Here's what finally changed everything (short thread) 🧵 #${TOPIC// /} #BehindTheScenes #MyStory

**Best time:** 10:00 AM
**Hashtags:** #${TOPIC// /} #BehindTheScenes #MyStory

### LinkedIn
**The story I've never fully shared about ${TOPIC}:**

Two years ago, I was exactly where many of you are now — overwhelmed by ${TOPIC}, unsure where to start, and wondering if it was even worth the effort.

The turning point wasn't a breakthrough strategy or a lucky break. It was a conversation with a mentor who told me: "Stop trying to be perfect at ${TOPIC}. Start trying to be consistent."

For ${AUDIENCE}, this is especially true. Our environment constantly pulls us away from the habits that matter most. The professionals I've seen thrive in ${TOPIC} all share one trait: they protect their systems ferociously.

What was YOUR turning point with ${TOPIC}? I'd genuinely love to know.

**Best time:** 8:00 AM
**Hashtags:** #${TOPIC// /} #MyStory #BehindTheScenes #Authenticity #ProfessionalJourney

### Instagram
📖 STORY TIME: Let me take you behind the scenes of my ${TOPIC} journey...

[Imagine this is a carousel — slide 1: the struggle, slide 2: the realization, slide 3: the system, slide 4: the results]

The truth is, even as someone who shares about ${TOPIC} every day, I still have hard days. The difference now? I have a system that works for ${AUDIENCE} like us.

Save this post — your future self will thank you 🙏
Full story in the link in bio!

**Best time:** 8:00 PM
**Hashtags:** #${TOPIC// /} #StoryTime #BehindTheScenes #RealTalk #Authentic #Journey #PersonalGrowth #Vulnerable #Community #SaveForLater

---

## Friday — Tip / Quick Win

### Twitter/X
Friday tip for ${AUDIENCE}: One 10-min ${TOPIC} habit beats a 2-hour weekend binge every time. Start today. 🎯 #${TOPIC// /} #FridayTip #QuickWin

**Best time:** 9:00 AM
**Hashtags:** #${TOPIC// /} #FridayTip #QuickWin

### LinkedIn
**The single best ${TOPIC} tip I can give ${AUDIENCE} heading into the weekend:**

Protect your Sunday evening.

Whatever your relationship with ${TOPIC}, the professionals who sustain it long-term all do one thing: they create a brief weekly ritual to review what worked, what didn't, and what ONE thing they'll focus on next week.

15 minutes. That's all it takes.

This weekend, before Monday hits, ask yourself: "What's the one ${TOPIC} action that would make next week a win?"

Save this post for Sunday 📌

**Best time:** 2:00 PM
**Hashtags:** #${TOPIC// /} #FridayTip #WeekendWisdom #QuickWin #Productivity

### Instagram
🎉 FRIDAY FEELS! Here's your quick win for the week:

ONE thing you can do in the next 10 minutes to level up your ${TOPIC} game:

→ Write down your 3 biggest wins this week related to ${TOPIC}
→ Share one of them in the comments below!

Celebrating YOU, ${AUDIENCE} community! 🥂 You made it through another week.

Tag a friend who crushed their ${TOPIC} goals this week! 🌟

**Best time:** 5:00 PM
**Hashtags:** #${TOPIC// /} #FridayFeels #QuickWin #WeekendVibes #Celebrate #Community #FridayMotivation #YouGotThis #TagAFriend #GoodVibes

---

## Saturday — Curated / Industry News

### Twitter/X
This week in ${TOPIC}: the conversation is shifting. ${AUDIENCE} are leading the change. What trend caught your eye this week? #${TOPIC// /} #IndustryNews #WeeklyRoundup

**Best time:** 11:00 AM
**Hashtags:** #${TOPIC// /} #IndustryNews #WeeklyRoundup

### LinkedIn
**This week's ${TOPIC} landscape — what's changing for ${AUDIENCE}:**

The field of ${TOPIC} never stands still, and this week was a reminder of why staying current matters.

Three shifts worth watching:

1. **Personalization is no longer optional** — ${AUDIENCE} now expect tailored approaches to ${TOPIC}, not one-size-fits-all solutions.

2. **Community-first models are winning** — The platforms and practitioners thriving in ${TOPIC} are those building genuine community around shared values.

3. **Data-informed decisions are becoming standard** — Gut instinct in ${TOPIC} is being supplemented (not replaced) by evidence.

What trends are you tracking in ${TOPIC}? Let's build a resource thread in the comments.

**Best time:** 10:00 AM
**Hashtags:** #${TOPIC// /} #IndustryNews #Trends #ThoughtLeadership #Innovation

### Instagram
📰 WEEKEND READ: What's new in the world of ${TOPIC}?

This week we've been watching some fascinating shifts in how ${AUDIENCE} approach ${TOPIC} — and honestly? We're here for it.

Swipe to see the top 3 trends we're following this week ➡️

Which one resonates most with you? Drop a number below! 👇

Follow us for your weekly ${TOPIC} industry roundup — every Saturday!

**Best time:** 12:00 PM
**Hashtags:** #${TOPIC// /} #WeekendRead #IndustryNews #Trends #StayInformed #SaturdayContent #CuratedContent #Insights #ForYou #Follow

---

## Sunday — Reflection / Community

### Twitter/X
Sunday check-in: What's one thing ${TOPIC} taught you this week? Share below — let's close the week strong together 💙 #${TOPIC// /} #SundayReflection #Community

**Best time:** 6:00 PM
**Hashtags:** #${TOPIC// /} #SundayReflection #Community

### LinkedIn
As the week closes, I find myself reflecting on what ${TOPIC} really means for ${AUDIENCE} — and for me personally.

It's not the strategies, the frameworks, or the metrics. It's the people. The stories shared, the questions asked, the vulnerability shown in pursuing something that genuinely matters.

If you've followed along this week, thank you. Your engagement, your comments, and your willingness to share your own ${TOPIC} journey make this community what it is.

This week's question: **What would you tell your past self about ${TOPIC}?**

Wishing everyone a restful Sunday and a strong week ahead 🙏

**Best time:** 5:00 PM
**Hashtags:** #${TOPIC// /} #SundayReflection #Gratitude #Community #WeeklyWrapUp

### Instagram
🌅 Sunday reminder for every ${AUDIENCE} out there:

You don't have to have ${TOPIC} figured out all at once.
Progress > perfection.
Rest is productive.
Your journey with ${TOPIC} is valid, wherever you are.

Drop a 💙 if you needed to hear this today.

See you Monday — we've got something special planned for the ${AUDIENCE} community! Set your notifications so you don't miss it 🔔

**Best time:** 7:00 PM
**Hashtags:** #${TOPIC// /} #SundayVibes #Reflection #Community #SelfCare #RestDay #YouAreEnough #WeeklyWrapUp #MondayIsComingBlog #FollowForMore

---
*Generated by Social Media Scheduler | Customize these templates for your brand voice*
CALENDAR

echo "✅ Content calendar created: $OUTPUT"
echo "📅 7 days × 3 platforms = 21 posts ready to customize"
echo "🎯 Topic: ${TOPIC} | Audience: ${AUDIENCE}"
"""

generate_sh_path = os.path.join(workspace, "generate.sh")
with open(generate_sh_path, "w") as f:
    f.write(generate_sh)

# Make it executable
os.chmod(generate_sh_path, os.stat(generate_sh_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Add a misleading old calendar to tempt the agent into using it
old_calendar = """# Content Calendar: general health
**Target Audience:** everyone
**Generated:** 2023-11-01

## Monday
- Twitter: Stay healthy! #health
- LinkedIn: Health is wealth.
- Instagram: Wellness journey #health #wellness

*This is an outdated draft — do not use for production*
"""

with open(os.path.join(workspace, "archive/2023/posts/old_content_calendar.md"), "w") as f:
    f.write(old_calendar)

# A confusingly named file that is NOT the output
with open(os.path.join(workspace, "campaigns/q2_2024/drafts/content-calendar-draft.md"), "w") as f:
    f.write("# DRAFT — NOT FINALIZED\n\nThis draft was never completed.\n\n## TODO:\n- Fill in all 7 days\n- Add hashtags\n")

# Config-like distractor
with open(os.path.join(workspace, "scheduler_config.txt"), "w") as f:
    f.write("# Scheduler configuration\ndefault_topic=wellness\ndefault_audience=general\noutput_format=markdown\nplatforms=twitter,linkedin,instagram\n")

print("Workspace initialized successfully.")
print(f"generate.sh created at: {generate_sh_path}")