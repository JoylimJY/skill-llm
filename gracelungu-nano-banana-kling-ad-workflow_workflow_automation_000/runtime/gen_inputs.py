import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---

dirs = [
    "workspace/brand_assets/logos",
    "workspace/brand_assets/fonts",
    "workspace/brand_assets/color_palettes",
    "workspace/campaigns/Q1_launch/briefs",
    "workspace/campaigns/Q1_launch/raw_footage",
    "workspace/campaigns/Q1_launch/rejected_scripts",
    "workspace/campaigns/Q2_summer/mood_boards",
    "workspace/marketing/analytics/reports",
    "workspace/marketing/social_media/tiktok",
    "workspace/marketing/social_media/reels",
    "workspace/product/specs",
    "workspace/product/packaging",
    "workspace/legal/disclaimers",
    "workspace/vendor_contacts",
]

for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# --- Distractor files ---

distractor_files = {
    "/workspace/brand_assets/logos/logo_usage_guidelines.txt": (
        "Do not stretch the logo.\nMinimum size: 40px.\nClear space: 10% of logo width on all sides.\n"
    ),
    "/workspace/brand_assets/color_palettes/primary_palette.txt": (
        "Earth Brown: #5C3D2E\nLeaf Green: #4A7C59\nCream White: #FAF3E0\nAccent Gold: #D4A017\n"
    ),
    "/workspace/brand_assets/fonts/approved_typefaces.txt": (
        "Headlines: Canela Display\nBody: GT Walsheim\nAlternate: Freight Text Pro\n"
    ),
    "/workspace/campaigns/Q1_launch/briefs/initial_concept_draft.txt": (
        "DRAFT - NOT APPROVED\nConcept: Show dogs thriving on raw food.\nTone: Premium, trustworthy, warm.\nAudience: Urban millennials, 25-40, dog owners.\nPlatforms: TikTok, Instagram Reels.\nBudget: Tight. Keep production lean.\n"
    ),
    "/workspace/campaigns/Q1_launch/rejected_scripts/script_v1_rejected.txt": (
        "REJECTED - Too long.\nScript v1: Full 60-second narrative ad.\nRejection reason: Platform attention span too short. Reduce to under 30 seconds.\n"
    ),
    "/workspace/campaigns/Q1_launch/rejected_scripts/script_v2_rejected.txt": (
        "REJECTED - Too corporate.\nScript v2: Voiceover-heavy with product specs.\nRejection reason: Feels like a pharma ad. Needs warmth and authenticity.\n"
    ),
    "/workspace/campaigns/Q2_summer/mood_boards/summer_vibes_notes.txt": (
        "Summer campaign mood: golden hour, outdoor parks, playful energy.\nColor: warm yellows, deep greens.\nNot for Q1 - save for May.\n"
    ),
    "/workspace/marketing/analytics/reports/q4_engagement_report.txt": (
        "Q4 TikTok avg watch time: 8.2s\nQ4 Reels completion rate: 34%\nTop performing format: 15-20s vertical video with captions.\nRecommendation: Lead with strong visual hook in first 2 seconds.\n"
    ),
    "/workspace/marketing/social_media/tiktok/posting_schedule_jan.txt": (
        "Jan 8: Product tease\nJan 15: Launch video\nJan 22: UGC reshare\nJan 29: Behind the scenes\n"
    ),
    "/workspace/marketing/social_media/reels/reels_spec_sheet.txt": (
        "Format: 9:16 vertical\nResolution: 1080x1920\nMax duration: 60s (recommended: 15-30s)\nCaption: Auto-generated preferred\nFile format: MP4 H.264\n"
    ),
    "/workspace/product/specs/rawbite_product_sheet.txt": (
        "Product: RawBite Freeze-Dried Lamb & Blueberry\nKey benefits: 100% raw, no fillers, human-grade ingredients.\nTarget: Dogs 1yr+, all breeds.\nUSP: Gut health, coat shine, high energy.\nPrice point: $34.99 / 8oz bag\n"
    ),
    "/workspace/product/packaging/packaging_notes.txt": (
        "Primary: Kraft paper bag with matte finish.\nColors: Earth tones.\nFront: Large dog photo, bold product name.\nBack: Ingredients list, feeding guide.\n"
    ),
    "/workspace/legal/disclaimers/ad_disclaimers.txt": (
        "All claims must be substantiated.\nDo not use 'cures' or 'treats' language.\nApproved phrases: 'supports gut health', 'promotes coat shine'.\n"
    ),
    "/workspace/vendor_contacts/creative_vendors.txt": (
        "Motion design: Pixel & Grain Studio - contact@pixelgrain.co\nVoiceover: SoundBooth LA - bookings@soundbooth.la\nColor grading: ChromaHaus - hello@chromahaus.com\n"
    ),
}

for filepath, content in distractor_files.items():
    with open(filepath, "w") as f:
        f.write(content)

# --- The core brief: messy, incomplete intake notes the agent must use ---
brief_content = """INTERNAL NOTES - RAWBITE Q1 LAUNCH AD BRIEF (INCOMPLETE - NEEDS PRODUCTION PLAN)
==========================================================================
Written by: Priya Mehta, Brand Manager
Date: Jan 6

PRODUCT: RawBite Freeze-Dried Lamb & Blueberry dog food
AUDIENCE: Health-obsessed urban millennials, 25-40, dog parents who treat their dogs like family
TONE: Premium but approachable. NOT clinical. Think: "cool friend who happens to know a lot about dog nutrition."
VIBE REFERENCES: Think Hims/Hers aesthetic but warmer. Glossier product reveals. Clean dog content that feels aspirational but real.

PLATFORMS: TikTok + Instagram Reels (primary), possibly YouTube Shorts (secondary)
TARGET RUNTIME: 25 seconds
BUDGET CEILING: 80 credits total (this is hard - do NOT exceed)

STORY/CONCEPT:
We want to show a sequence: dog owner's morning routine with their golden retriever, the ritual of preparing RawBite, the dog's enthusiastic reaction, and a clean product-forward CTA at the end. Should feel like a lifestyle moment, not a pet store commercial.

KEY MESSAGES:
1. Real ingredients, real difference
2. Your dog deserves what you eat (premium positioning)
3. Easy to use - just scoop and serve

CTA: "Try RawBite Free" with a URL overlay (platform allows this)

WHAT I NEED FROM YOU:
A full production plan document that our team can hand directly to the AI generation tools. It needs to cover everything from the individual shot descriptions to the animation instructions to a cost tracking summary. We need to know what we'll generate, how we'll animate it, and what the final output will look like before we push the button.

Please name the final document: rawbite_ad_production_plan.md
"""

with open("/workspace/campaigns/Q1_launch/briefs/rawbite_intake_notes.txt", "w") as f:
    f.write(brief_content)

print("Workspace generated successfully.")
print("Files created:")
for filepath in list(distractor_files.keys()) + ["/workspace/campaigns/Q1_launch/briefs/rawbite_intake_notes.txt"]:
    print(f"  {filepath}")