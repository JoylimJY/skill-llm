import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "workspace/media_team/archives/2023/q1",
    "workspace/media_team/archives/2023/q2",
    "workspace/media_team/archives/2024/drafts",
    "workspace/media_team/archives/2024/published",
    "workspace/media_team/templates_old",
    "workspace/media_team/brand_assets/logos",
    "workspace/media_team/brand_assets/fonts",
    "workspace/media_team/briefs/pending",
    "workspace/media_team/briefs/approved",
    "workspace/media_team/competitor_analysis",
    "workspace/media_team/seo_research",
    "workspace/media_team/social_calendar",
]

for d in dirs:
    os.makedirs(os.path.join("/", d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "workspace/media_team/archives/2023/q1/kimchi_post.txt": (
        "Kimchi making post - published Jan 2023\n"
        "Views: 45000\nLikes: 3200\nComments: 412\n"
        "Topics: fermentation, probiotics, Korean cuisine\n"
    ),
    "workspace/media_team/archives/2023/q2/pasta_review.txt": (
        "Pasta machine review - draft\n"
        "Product: Marcato Atlas 150\n"
        "Test duration: 2 weeks\n"
        "Rating: 4.5/5\n"
    ),
    "workspace/media_team/archives/2024/drafts/bread_ideas.txt": (
        "Bread baking ideas for Q3:\n"
        "- sourdough beginner guide\n"
        "- focaccia variations\n"
        "- quick no-knead loaf\n"
    ),
    "workspace/media_team/archives/2024/published/coffee_guide.json": json.dumps({
        "title": "Pour Over Coffee Complete Guide",
        "type": "tutorial",
        "published": "2024-03-15",
        "views": 89000
    }, ensure_ascii=False, indent=2),
    "workspace/media_team/templates_old/generic_outline_v1.txt": (
        "Old generic outline template v1 (DEPRECATED)\n"
        "1. Introduction\n2. Main Content\n3. Conclusion\n"
        "Note: Do not use this template anymore.\n"
    ),
    "workspace/media_team/templates_old/generic_outline_v2.txt": (
        "Old generic outline template v2 (DEPRECATED)\n"
        "Hook -> Problem -> Solution -> CTA\n"
        "This was replaced in 2024.\n"
    ),
    "workspace/media_team/brand_assets/logos/logo_specs.txt": (
        "Logo: 200x200px PNG\nColors: #FF5733, #FFFFFF\nFont: Noto Sans CJK\n"
    ),
    "workspace/media_team/brand_assets/fonts/font_list.txt": (
        "Approved fonts: Noto Sans, PingFang SC, Source Han Sans\n"
    ),
    "workspace/media_team/briefs/pending/sichuan_cooking.txt": (
        "BRIEF: Sichuan cooking series\n"
        "Status: PENDING APPROVAL\n"
        "Target audience: home cooks, age 25-40\n"
        "Platform: Xiaohongshu + WeChat\n"
    ),
    "workspace/media_team/briefs/approved/knife_skills_brief.txt": (
        "BRIEF: Knife skills for beginners\n"
        "Status: APPROVED\n"
        "Deadline: 2024-08-01\n"
        "Writer assigned: TBD\n"
    ),
    "workspace/media_team/competitor_analysis/competitor_notes.txt": (
        "Competitor A: Focuses on 5-ingredient recipes\n"
        "Competitor B: Strong on video tutorials\n"
        "Competitor C: SEO-optimized long-form articles\n"
        "Gap: Nobody covers wok technique for beginners systematically.\n"
    ),
    "workspace/media_team/seo_research/keywords_wok.txt": (
        "Target keywords:\n"
        "- 炒锅使用技巧 (monthly search: 12000)\n"
        "- 新手学炒菜 (monthly search: 8500)\n"
        "- 如何炒菜不粘锅 (monthly search: 6700)\n"
        "- 炒锅开锅方法 (monthly search: 9200)\n"
    ),
    "workspace/media_team/social_calendar/august_2024.txt": (
        "August 2024 Content Calendar:\n"
        "Week 1: Wok seasoning tutorial (ASSIGNED)\n"
        "Week 2: Knife sharpening guide\n"
        "Week 3: Stock-making masterclass\n"
        "Week 4: Monthly recipe roundup\n"
    ),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join("/", filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE MAIN PROBLEM FILE: Raw messy brainstorming notes ---
raw_notes_content = """
=== RAW BRAINSTORMING DUMP - WOK SEASONING ARTICLE ===
Created by: Chen Wei (Content Lead)
Date: 2024-07-22
Status: NEEDS STRUCTURE

--- MESSY NOTES BELOW ---

Ok so this article is about how to properly season (开锅) a new carbon steel wok.
Target: people who just bought a new wok and have no idea what to do with it.
Main pain: they try to cook and everything sticks, wok rusts, they give up.

Things I want to cover:
* what tools you need (heat source, paper towels, cooking oil, dish soap for initial wash, tongs, maybe an old rag)
* step 1 - wash the wok with soap ONCE to remove factory coating (most people skip this!!)
* step 2 - dry it completely on the stove (very important to prevent rust)
* step 3 - heat the wok until it smokes and changes color (blue/gray patina)
* step 4 - apply very thin layer of oil with paper towel (CRITICAL: NOT TOO MUCH OIL or it gets gummy)
* step 5 - repeat heating+oil process 3-4 times
* step 6 - cook something fatty first (bacon, lard, avoid veggies for first week)
* common mistake: using too much oil -> gummy seasoning -> have to start over
* common mistake: using wrong oil (butter, olive oil -> low smoke point -> problems)
* common mistake: not drying completely -> rust spots
* after care: never soak in water, dry immediately after washing, light oil coating for storage
* my own experience: ruined my first wok, had to redo from scratch, took me 3 attempts
* data point: a well-seasoned wok lasts 20+ years (my grandmother's wok is 30 years old)
* data point: proper seasoning takes about 45 minutes total
* who should read: anyone who just got a new carbon steel or cast iron wok
* CTA idea: ask readers to share photos of their wok after seasoning
* also mention: how to rescue a rusty wok (bonus tip)

Tone: practical, encouraging, not intimidating for beginners

--- END NOTES ---

The article needs a proper structured outline. Content team will use this to write the full draft.
The outline should follow our internal framework properly.
"""

notes_path = "/workspace/media_team/briefs/approved/wok_seasoning_raw_notes.txt"
with open(notes_path, "w", encoding="utf-8") as f:
    f.write(raw_notes_content)

print("Workspace generated successfully.")
print(f"Main problem file: {notes_path}")
print("Distractor files created:", len(distractor_files))