import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep nested distractor files ---
dirs = [
    "drafts/old",
    "drafts/rejected",
    "research/sources",
    "research/stats",
    "assets/images",
    "assets/banners",
    "publications/tds",
    "publications/better_prog",
    "notes/interviews",
    "notes/outlines",
    "seo/keywords",
    "seo/competitors",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "drafts/old/draft_v1.txt": "Python is great. Use it for everything. THE END.",
    "drafts/old/draft_v2.txt": "Machine learning is transforming industries...\n\nBut nobody knows how to get started.",
    "drafts/rejected/too_short.txt": "AI is cool.\n5 reasons why.",
    "drafts/rejected/off_topic.txt": "Cooking pasta: A DevOps metaphor",
    "research/sources/arxiv_links.txt": "https://arxiv.org/abs/2301.00001\nhttps://arxiv.org/abs/2209.05433",
    "research/stats/salary_data.csv": "role,avg_salary\nML Engineer,145000\nData Scientist,130000\nAI Researcher,160000",
    "assets/images/placeholder.txt": "hero_image_url: https://unsplash.com/photos/python-code",
    "assets/banners/banner_specs.txt": "1200x628 px, JPG, under 1MB",
    "publications/tds/submission_notes.txt": "TDS accepts: Python, ML, Data Science. Min 6 min read. No promotional content.",
    "publications/better_prog/submission_notes.txt": "Better Programming: Clean code, architecture. No basic tutorials.",
    "notes/interviews/dev_interview_1.txt": "Dev said: switched to ML after 5 years in backend. Tripled salary.",
    "notes/interviews/dev_interview_2.txt": "She learned PyTorch in 30 days using project-based learning.",
    "notes/outlines/rough_outline.txt": "- Intro: why ML matters\n- Section: tools\n- Section: learning path\n- Conclusion",
    "seo/keywords/target_keywords.txt": "machine learning for developers\npython machine learning tutorial\nhow developers learn ML\n",
    "seo/competitors/top_articles.txt": "Top competitor article: 'Machine Learning for Beginners' — 200k views\nCompetitor 2: 'Python ML Guide' — 89k views",
}
for rel_path, content in distractors.items():
    with open(os.path.join(workspace, rel_path), "w", encoding="utf-8") as f:
        f.write(content)

# --- THE PROBLEM: Messy raw brief and research notes the agent must process ---

raw_brief = """\
CONTENT BRIEF — AI/ML Career Pivot Article
===========================================
Assigned Writer: TBD
Target Platform: Medium (Towards Data Science publication)
Primary Keyword: "machine learning for developers"
Target Audience: Software engineers / backend developers considering a switch into ML roles
Suggested Article Length: 7-8 minute read (~1600-1900 words)
Goal: Explain a concrete 5-step roadmap for software developers to transition into ML engineering

Suggested Angle (NOT final — writer has creative freedom):
  Something like "Here are N steps/ways/habits to go from dev to ML engineer"
  Should feel actionable and specific — not generic fluff

MUST HIT these sub-topics:
  1. Why developers have an unfair advantage entering ML (code, system design)
  2. Which math topics actually matter (linear algebra, stats — NOT all of calculus)
  3. Best first project ideas to build a portfolio
  4. How to frame your existing experience in ML job applications
  5. Realistic timeline expectations (most guides lie about this)

DO NOT write a generic "what is machine learning" piece.
CTA at the end should encourage readers to follow the author and clap.
Related content footer should be included.

Tone: Conversational, direct, slightly opinionated. Like a senior engineer talking to a peer.
"""

messy_research_notes = """\
RAW RESEARCH DUMP — Machine Learning for Developers
====================================================
(These are unorganized notes. Writer must structure these.)

STAT: According to LinkedIn 2023, ML Engineer job postings up 74% YoY.
STAT: Average ML Engineer salary: $145k USD (source: levels.fyi)
STAT: 68% of ML Engineers come from a software engineering background (O'Reilly survey)

DEVELOPER ADVANTAGE:
- Devs already know git, APIs, data structures — huge head start
- System design knowledge = deployment/scaling ML models is natural
- Writing clean, reproducible code >> notebook cowboys
- Most ML courses assume zero coding knowledge; devs skip 60% of that

MATH REALITY CHECK:
- Linear algebra: vectors, matrices, dot products — YES, essential
- Probability + statistics: distributions, Bayes — YES
- Full calculus: mostly NOT needed in practice (autodiff handles it)
- Discrete math: helpful but not blocking
- Quote from a hiring manager: "I've never asked a candidate to derive backprop by hand"

FIRST PROJECT IDEAS:
- Sentiment analysis on your own Slack/email data
- Build a recommender system for your reading list (Goodreads export)
- Fine-tune a small LLM on a niche dataset you care about
- Replicate a paper you read — forces you to actually understand it

TIMELINE REALITY:
- "Learn ML in 30 days" courses are marketing lies
- Realistic: 6-9 months of consistent part-time effort to land first ML role
- 3 months: solid foundations + first project
- 6 months: portfolio with 2-3 projects, contributions to OSS
- 9 months: first interviews, offers for some
- Some take 18 months — that's also normal

EXISTING EXPERIENCE FRAMING:
- Backend dev → "I've built data pipelines, I understand latency at scale"
- Frontend dev → "I understand user behavior modeling, AB testing"
- DevOps → "I own the MLOps stack"
- Reframe: every past project has a data story

PORTFOLIO TIPS:
- GitHub with clean READMEs is a must
- Write about what you built (Medium is perfect for this)
- Link projects together as a narrative
"""

with open(os.path.join(workspace, "content_brief.txt"), "w", encoding="utf-8") as f:
    f.write(raw_brief)

with open(os.path.join(workspace, "research_notes.txt"), "w", encoding="utf-8") as f:
    f.write(messy_research_notes)

# A broken/incomplete draft that is structurally wrong (no emoji markers, no proper sections, wrong headline)
broken_draft = """\
Title: How Developers Can Get Into Machine Learning

Machine learning is one of the hottest fields right now. Many developers want to switch but don't know how.

Why this matters:
Lots of people want to learn ML.

Step 1: Learn the basics
Step 2: Do some projects  
Step 3: Apply for jobs

In conclusion, machine learning is achievable for developers. Good luck!
"""
with open(os.path.join(workspace, "drafts/broken_draft.md"), "w", encoding="utf-8") as f:
    f.write(broken_draft)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in (os.path.join(r,f) for r,ds,fs in os.walk(workspace) for f in fs))}")