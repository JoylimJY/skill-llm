import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "content/drafts",
    "content/published",
    "content/archive",
    "content/images",
    "marketing/campaigns",
    "marketing/briefs",
    "seo/keywords",
    "seo/reports",
    "analytics/traffic",
    "analytics/conversions",
    "brand/guidelines",
    "brand/assets",
    "legal/disclaimers",
    "ops/logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "content/published/email_marketing_101.md": "# Email Marketing 101\nEmail is a great way to reach customers.\n",
    "content/published/seo_basics.md": "# SEO Basics\nSearch engine optimization helps you rank higher in Google.\n",
    "content/archive/old_protein_article_v1.md": "# Protein Supplements\nProtein is good for muscles. Many athletes use protein powder.\n",
    "marketing/campaigns/q3_campaign_brief.txt": "Q3 Campaign: Focus on plant-based audience. Budget: $50k. KPIs: CTR 2%, ROAS 3x.\n",
    "marketing/briefs/influencer_brief.txt": "Influencer targets: fitness, nutrition, wellness verticals. Deliverables: 2 reels, 1 static post.\n",
    "seo/keywords/target_keywords.csv": "keyword,volume,difficulty\nplant based protein,12000,65\nprotein supplement review,8000,70\nbest vegan protein powder,15000,72\n",
    "seo/reports/monthly_ranking_report.txt": "Site: nutritionhq.com\nTop keyword: protein powder review (pos 14)\nOrganic sessions: 4200/month\n",
    "analytics/traffic/june_traffic.json": '{"sessions": 4200, "bounce_rate": 0.61, "avg_time_on_page": "1m 23s"}\n',
    "analytics/conversions/conversion_funnel.txt": "Landing Page -> Product Page -> Add to Cart -> Checkout\nConversion rate: 1.8%\n",
    "brand/guidelines/tone_of_voice.md": "# Tone of Voice\nFriendly, science-backed, approachable. Avoid jargon. Use second-person where possible.\n",
    "brand/assets/logo_specs.txt": "Logo: SVG preferred. Min size: 40px. Colors: #2ECC71, #1A252F.\n",
    "legal/disclaimers/supplement_disclaimer.txt": "These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease.\n",
    "ops/logs/content_pipeline.log": "2024-06-01 09:00 - Draft uploaded: plant_protein_draft.md\n2024-06-01 10:30 - Review pending\n2024-06-02 08:15 - Revision requested\n",
    "content/drafts/blog_outline_ideas.txt": "Ideas:\n1. Top 5 plant protein sources\n2. Whey vs plant protein comparison\n3. How to hit daily protein goals on a vegan diet\n",
}

for filepath, content in distractors.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM FILE: A deliberately weak, low-GEO article draft ---
# Designed to score poorly across all 8 GEO dimensions
weak_article = """\
# Plant-Based Protein Supplements: What You Need to Know

Plant-based protein supplements have become really popular lately. Lots of people are
switching to vegan diets and they need protein. These supplements are a good option for
people who don't want to eat meat.

There are different kinds of plant proteins out there. Pea protein is one type. Soy protein
is another popular choice. Rice protein is also available. Many companies now make these
products.

## Why People Use Them

People use plant-based protein for many reasons. Some want to build muscle. Others want
to lose weight. Some people just want to be healthier. Athletes are starting to use them
more too. It's becoming a trend in the fitness world.

## Are They Effective?

Studies suggest that plant proteins can work well. Some research shows they might be
as good as whey protein in some cases. Results may vary though. It depends on the person
and how they use the supplement.

## Taste and Mixability

One issue people mention is that plant proteins can taste different from whey. Some find
the texture chalky. Companies have been working on making them taste better though.
New formulations are improving things.

## Cost Considerations

Plant-based proteins can cost more than traditional whey protein. Prices vary widely.
Some brands are more affordable than others. It's worth shopping around. Quality matters.

## Conclusion

Plant-based protein supplements are a growing category. If you're considering making
a switch, it might be worth trying one. They have benefits and some drawbacks. Do your
own research before buying.
"""

with open(os.path.join(workspace, "content/drafts/plant_protein_draft.md"), "w") as f:
    f.write(weak_article)

print("Workspace generated successfully.")
print(f"Main problem file: {workspace}/content/drafts/plant_protein_draft.md")