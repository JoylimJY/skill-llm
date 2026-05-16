import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create a realistic, messy directory structure with distractor files ---

dirs = [
    "workspace/brand_assets",
    "workspace/brand_assets/logos",
    "workspace/brand_assets/fonts",
    "workspace/competitor_research",
    "workspace/competitor_research/q1_2024",
    "workspace/customer_data",
    "workspace/customer_data/surveys",
    "workspace/product_docs",
    "workspace/product_docs/ingredients",
    "workspace/product_docs/certifications",
    "workspace/old_campaigns",
    "workspace/old_campaigns/2023",
    "workspace/analytics",
    "workspace/analytics/monthly_reports",
    "workspace/team_notes",
]

for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# Distractor files

distractors = {
    "/workspace/brand_assets/brand_guidelines_draft.txt": """
PAWFECT ORIGINS - BRAND GUIDELINES (DRAFT v0.3)
Primary Color: Forest Green (#2D5A27)
Secondary Color: Warm Oat (#F5E6C8)
Font: Nunito (headings), Lato (body)
Tone: Warm, science-backed, eco-conscious
DO NOT USE: cartoon animals, neon colors, aggressive sales language
""",
    "/workspace/brand_assets/logos/logo_usage_notes.txt": "Use SVG where possible. Min size 32px. Do not distort aspect ratio.",
    "/workspace/brand_assets/fonts/font_list.txt": "Nunito Bold, Nunito Regular, Lato Regular, Lato Italic",

    "/workspace/competitor_research/q1_2024/competitor_analysis.csv": """Competitor,Product,Price/lb,Key Claim,Weakness
NutriPaws,Grain-Free Kibble,12.50,Vet recommended,No sustainability angle
EcoTails,Raw Frozen,18.00,100% organic,Hard to store
PureBowl,Dehydrated,22.00,Human-grade,Too expensive
FreshFur,Subscription Box,15.00,Personalized,High churn
""",
    "/workspace/competitor_research/q1_2024/notes.txt": "NutriPaws dominates SEO for 'grain-free dog food'. EcoTails has poor retention. Opportunity in 'sustainable + affordable' positioning.",

    "/workspace/customer_data/surveys/q4_2023_survey_results.json": json.dumps({
        "respondents": 412,
        "top_pain_points": [
            "Not knowing if ingredients are truly sustainable",
            "Price premium feels unjustified",
            "Lack of transparency about sourcing"
        ],
        "what_they_love": [
            "Knowing their pet's food is ethical",
            "Visible ingredient origins",
            "Community of like-minded pet owners"
        ],
        "nps_score": 47,
        "verbatims": [
            "I wish I could see exactly where the chicken comes from",
            "The price is high but I believe in the mission",
            "My vet was skeptical but my dog's coat improved"
        ]
    }, indent=2),
    "/workspace/customer_data/surveys/methodology.txt": "Online survey via Typeform, distributed to email list of 2,800 subscribers. Response rate: 14.7%.",

    "/workspace/product_docs/ingredients/sourcing_map.txt": """
INGREDIENT SOURCES - PAWFECT ORIGINS
- Chicken: Free-range farms, certified humane, Pacific Northwest
- Sweet Potato: Organic co-ops, California Central Valley
- Kelp: Wild-harvested, Icelandic waters
- Turmeric: Fair-trade certified, Kerala, India
- Probiotics: Proprietary blend, manufactured in-house, Oregon
""",
    "/workspace/product_docs/certifications/cert_list.txt": "Certified B Corp (pending), USDA Organic (partial line), Non-GMO Project Verified, Leaping Bunny (cruelty-free)",
    "/workspace/product_docs/new_product_brief.txt": """
PRODUCT LAUNCH: PawfectOrigins Kibble Starter Kit
Launch date: Q2 2024
SKU: PO-SK-001
Description: 30-day supply of our new grain-free, sustainably sourced kibble, bundled with a feeding guide and impact report showing carbon offset per bag.
Target: Health-conscious millennial pet owners, urban households, eco-aware families
Price: $49.99 (introductory) / $59.99 (regular)
USP: First kibble brand to show real-time sourcing transparency via QR code on packaging.
""",

    "/workspace/old_campaigns/2023/summer_promo_notes.txt": "Summer 'Eat Clean, Play Green' campaign underperformed. CTR 0.8%. Lesson: too generic, no hook.",
    "/workspace/old_campaigns/2023/influencer_list.csv": """Handle,Platform,Followers,Niche,Status
@sustainablepetmom,Instagram,82000,eco pets,contacted
@dogdietdoc,YouTube,150000,vet nutrition,no response
@wildhikedogs,TikTok,310000,outdoor dogs,agreed
""",
    "/workspace/old_campaigns/2023/retro_notes.txt": "Key lesson: stories of real transformations outperform product feature posts 3:1. Need more UGC.",

    "/workspace/analytics/monthly_reports/march_2024.txt": """
Sessions: 42,311
Bounce Rate: 68%
Top Landing Page: /shop/kibble-starter-kit
Email Open Rate: 24.3%
Conversion Rate: 1.8%
Top Traffic Source: Organic Search (38%), Instagram (27%), Direct (19%)
""",
    "/workspace/analytics/monthly_reports/feb_2024.txt": "Sessions: 38,104 | Conversion: 1.4% | Email: 22.1%",

    "/workspace/team_notes/slack_export_fragment.txt": """
[sarah.k]: We really need something that goes viral. Generic 'sustainable pet food' content just isn't cutting through.
[mike.t]: Agreed. What if we challenged people to do something with their pets for 30 days?
[sarah.k]: Or we expose something uncomfortable about the industry. Like, do people even know what 'byproduct meal' actually is?
[mike.t]: That could be controversial but effective. Let's get something drafted for the campaign planning meeting.
[priya.n]: Also - our customers LOVE showing off their dogs' health improvements. We should use that more.
""",
    "/workspace/team_notes/budget_q2.txt": "Q2 Campaign Budget: $35,000 total. Breakdown TBD pending campaign strategy sign-off.",
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content.strip())

print("Workspace generated successfully.")
print(f"Created {len(distractors)} distractor files across {len(dirs)} directories.")