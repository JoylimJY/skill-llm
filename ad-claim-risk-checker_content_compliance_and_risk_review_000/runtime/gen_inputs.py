import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "brand_assets/copy_drafts",
    "brand_assets/approved_assets",
    "brand_assets/legal_clearance",
    "campaigns/q3_launch/tiktok",
    "campaigns/q3_launch/meta",
    "campaigns/q3_launch/landing_pages",
    "campaigns/q3_launch/creator_briefs",
    "campaigns/q2_archive",
    "compliance/internal_notes",
    "compliance/platform_policies",
    "product/formulation_notes",
    "product/clinical_references",
    "analytics/past_performance",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "brand_assets/approved_assets/logo_usage_guide.txt": (
        "Logo must appear on white or dark backgrounds only. Minimum size: 32px."
    ),
    "brand_assets/legal_clearance/q2_clearance_memo.txt": (
        "Q2 campaigns were reviewed by outside counsel on 2024-04-10. No action required."
    ),
    "campaigns/q2_archive/summer_drop_results.csv": (
        "campaign,impressions,clicks,conversions\n"
        "meta_story_a,140000,3200,88\n"
        "tiktok_spark_b,290000,7100,201\n"
    ),
    "campaigns/q3_launch/meta/audience_segments.json": (
        '{"segments": ["women_25_44", "fitness_interest", "supplement_buyers"], '
        '"exclude": ["under_18"]}'
    ),
    "compliance/platform_policies/meta_health_policy_summary.txt": (
        "Meta restricts before/after imagery and claims implying guaranteed weight loss. "
        "Substantiation required for quantified performance claims."
    ),
    "compliance/platform_policies/tiktok_ad_policy_excerpt.txt": (
        "TikTok prohibits absolute health outcome claims (e.g., 'cures', 'eliminates fat'). "
        "Testimonials must reflect typical results."
    ),
    "compliance/internal_notes/ftc_reminder.txt": (
        "FTC Endorsement Guides updated 2023: disclose material connections, "
        "testimonials must reflect typical results, no unsubstantiated efficacy claims."
    ),
    "product/formulation_notes/ingredient_list.txt": (
        "Active ingredients: Green Tea Extract 400mg, Glucomannan 1g, Chromium 200mcg.\n"
        "Manufactured in GMP-certified facility. Not evaluated by FDA."
    ),
    "product/clinical_references/study_summary.txt": (
        "Internal pilot: n=24, 8-week trial. Average weight change: -3.1 lbs vs -1.2 lbs placebo. "
        "Not peer-reviewed. Funded by brand."
    ),
    "analytics/past_performance/hook_test_results.txt": (
        "Hook A ('Lose weight fast'): CTR 4.2%, high disapproval rate, ad rejected on Meta.\n"
        "Hook B ('Support your goals'): CTR 3.1%, approved on all platforms.\n"
    ),
    "brand_assets/copy_drafts/old_homepage_hero.txt": (
        "Transform your body in 30 days or your money back! "
        "Our #1 formula melts fat like nothing else on the market."
    ),
}
for rel_path, content in distractors.items():
    (WORKSPACE / rel_path).write_text(content, encoding="utf-8")

# ── MAIN TASK INPUT: messy multi-channel ad copy to review ───────────────────
# This is the file the agent must find, analyze, and produce output from.

tiktok_script = """\
[TIKTOK UGC SCRIPT — UNREVIEWED DRAFT v0.3]
Hook (0–3s): "This is the ONLY supplement that actually melts belly fat — I lost 14 pounds in 3 weeks."
Body (3–18s): "Every single person who tries BurnCore sees results. It's clinically proven to eliminate fat fast — 
no diet changes needed, no gym required. My metabolism is fixed now and the weight stays off forever."
CTA (18–22s): "Order today — guaranteed to work or you get your money back, every time, no questions asked."
"""

meta_carousel = """\
[META CAROUSEL — COPY DECK, UNREVIEWED]
Slide 1 headline: "Scientifically proven to melt fat 3x faster than diet alone"
Slide 1 body: "BurnCore is the #1 fat burner trusted by millions worldwide. Guaranteed results."
Slide 2 headline: "No gym. No diet. Just results."
Slide 2 body: "Take 2 capsules daily and watch the fat disappear. Works for everyone, every body type."
Slide 3 headline: "14 lbs in 21 days — real customers, real results."
Slide 3 body: "Our formula is so powerful, doctors are calling it a breakthrough. 100% guaranteed weight loss."
CTA: "Shop now — risk-free, results guaranteed or full refund."
"""

creator_brief = """\
[CREATOR BRIEF — TALKING POINTS, NOT YET COMPLIANCE-CHECKED]
- Tell your audience BurnCore is THE solution to stubborn belly fat — nothing else compares.
- Say you've never felt this kind of energy before and that BurnCore cured your slow metabolism.
- Mention that clinical studies prove it eliminates fat from problem areas (spot reduction).
- Promise viewers that if they follow the same routine as you, they WILL lose at least 10 lbs in the first month.
- Call it doctor-approved and the safest fat burner ever made.
- Use the phrase: "This works 100% of the time for anyone who tries it."
"""

landing_page_hero = """\
[LANDING PAGE HERO SECTION — PRE-LAUNCH DRAFT]
Headline: "The Last Weight Loss Supplement You'll Ever Need"
Subheadline: "BurnCore's patented formula is clinically proven to eliminate fat permanently — 
no matter your age, metabolism, or lifestyle."
Bullet 1: "Guaranteed: Lose 10–15 lbs in your first 30 days or we'll refund every penny."
Bullet 2: "3x faster fat burn than any other supplement on the market — lab verified."
Bullet 3: "Works for 100% of users — zero exceptions."
Bullet 4: "Your metabolism will be permanently reset after just one bottle."
Trust badge copy: "Endorsed by leading doctors and approved by the FDA."
"""

combined_copy = f"""
PRODUCT: BurnCore Fat Loss Capsules
CATEGORY: Dietary supplement / nutraceutical
CHANNEL MIX: TikTok UGC, Meta Carousel, Creator Brief, Landing Page
EVIDENCE LEVEL: Internal pilot study (n=24, non-peer-reviewed, brand-funded), customer testimonials
MARKET: United States
DESIRED TONE: Aggressive (current draft) — needs to become: balanced

==================== COPY ASSETS FOR REVIEW ====================

{tiktok_script}

{meta_carousel}

{creator_brief}

{landing_page_hero}
"""

input_file = WORKSPACE / "campaigns/q3_launch/burncore_copy_for_review.txt"
input_file.write_text(combined_copy.strip(), encoding="utf-8")

print("Workspace generated successfully.")
print(f"Main input file: {input_file}")
print(f"Total files created: {1 + len(distractors)}")