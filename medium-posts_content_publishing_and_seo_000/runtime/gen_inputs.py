import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ── helpers ──────────────────────────────────────────────────────────────────
def mkdirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

# ── directory skeleton ────────────────────────────────────────────────────────
mkdirs(
    f"{WORKSPACE}/.claude",
    f"{WORKSPACE}/blog/posts",
    f"{WORKSPACE}/blog/drafts",
    f"{WORKSPACE}/marketing/campaigns",
    f"{WORKSPACE}/marketing/social",
    f"{WORKSPACE}/seo/reports",
    f"{WORKSPACE}/seo/competitor-analysis",
    f"{WORKSPACE}/content/old-articles",
    f"{WORKSPACE}/content/repurpose-queue",
    f"{WORKSPACE}/ops/config",
)

# ── .claude/project-context.md  (THE KEY FILE the agent must read) ────────────
# Sections are deliberately out of numerical order, mixed with noise,
# and keywords are buried in Section 6, content strategy in Section 11.
write(f"{WORKSPACE}/.claude/project-context.md", """
    # Project Context — GreenNest Home

    ## Section 1: Company Overview
    GreenNest Home is a direct-to-consumer e-commerce brand selling
    sustainable, non-toxic home goods since 2019. HQ: Austin, TX.
    Website: https://www.greennesthouse.com

    ## Section 2: Target Audience
    Eco-conscious homeowners aged 28-45, primarily female, household
    income $75k+. Values: sustainability, minimalism, health.

    ## Section 3: Brand Voice
    Warm, knowledgeable, never preachy. Use "you" and "we". Avoid
    greenwashing language.

    ## Section 4: Product Lines
    - BioCleanse (all-purpose cleaners)
    - WoolNest (organic wool bedding)
    - ClayGlow (natural skincare)
    - BareBamboo (kitchenware)

    ## Section 5: Pricing & Margins
    AOV: $87. Margins: 62% blended. Free shipping above $65.

    ## Section 6: Keywords
    Primary keywords (high priority — use in titles and H2s):
      - non-toxic cleaning products
      - sustainable home essentials
      - eco-friendly household cleaners
      - zero-waste kitchen products
      - organic wool bedding benefits

    Secondary / long-tail:
      - how to switch to non-toxic cleaners
      - best zero-waste products for home
      - natural alternatives to bleach
      - organic bedding for better sleep
      - compostable kitchen supplies

    Branded terms: GreenNest, BioCleanse, WoolNest, BareBamboo

    ## Section 7: Tone Dos and Don'ts
    DO: cite studies, use numbered lists, end with clear CTA.
    DON'T: use superlatives ("best ever"), make unverified health claims.

    ## Section 8: Competitor Intel
    Main competitors: Branch Basics, Grove Collaborative, Blueland.
    Differentiator: fully compostable packaging across all lines.

    ## Section 9: Conversion Goals
    Primary: Add-to-cart on BioCleanse Starter Kit ($29).
    Secondary: Email list signup (10% discount popup).

    ## Section 10: Technical SEO Notes
    Site uses Shopify. Blog is /blogs/journal/. Canonical tags
    implemented via theme.liquid. Sitemap: /sitemap.xml.

    ## Section 11: Content Strategy
    Pillar pages around "non-toxic home" and "sustainable living".
    Cluster topics:
      - Room-by-room non-toxic guides (kitchen, bathroom, bedroom)
      - Ingredient deep-dives (what is sodium lauryl sulfate, etc.)
      - Lifestyle/how-to (switching to zero-waste routine)
    Distribution: publish original on GreenNest blog first, then
    syndicate to Medium with canonical pointing back to original.
    Repurpose top performers into Pinterest infographics and email.
    LinkedIn used for B2B gifting angle; Instagram for lifestyle UGC.

    ## Section 12: Email & CRM
    Platform: Klaviyo. Segments: Prospects, One-time buyers, VIPs.
    Welcome flow discount: 10%. VIP threshold: 3+ orders or $250 LTV.

    ## Section 13: Paid Media
    Meta: Retargeting + lookalike on BioCleanse. Google: Shopping +
    branded search. Monthly budget: $8,400.
""")

# ── The original blog post that needs to be republished on Medium ─────────────
write(f"{WORKSPACE}/blog/posts/switch-to-non-toxic-cleaners-guide.md", """
    ---
    title: How to Switch to Non-Toxic Cleaners (Without the Overwhelm)
    slug: how-to-switch-to-non-toxic-cleaners
    published_date: 2024-09-14
    author: Maya Torres
    canonical_url: https://www.greennesthouse.com/blogs/journal/how-to-switch-to-non-toxic-cleaners
    tags: [non-toxic cleaning products, eco-friendly household cleaners, how to switch to non-toxic cleaners]
    ---

    # How to Switch to Non-Toxic Cleaners (Without the Overwhelm)

    Making the switch from conventional to non-toxic cleaners sounds
    simple—until you're standing in the cleaning aisle staring at a
    wall of "natural" labels that may mean nothing at all.

    ## Why Conventional Cleaners Are a Problem

    Most household cleaners contain volatile organic compounds (VOCs),
    synthetic fragrances, and surfactants like sodium lauryl sulfate
    that irritate airways and contaminate waterways. A 2019 study in
    the American Journal of Respiratory and Critical Care Medicine
    found that weekly use of spray cleaners caused lung damage
    comparable to smoking 20 cigarettes a day.

    ## A Room-by-Room Switching Plan

    ### Kitchen First
    Start with your kitchen. Swap your all-purpose spray for a
    plant-based concentrate. The BioCleanse All-Purpose Concentrate
    (https://www.greennesthouse.com/products/biocleanse-starter-kit)
    makes 6 spray bottles from one small bottle—less plastic, less cost.

    ### Bathroom Second
    Toilets, sinks, and tile need something slightly stronger. Look for
    oxygen-based bleach alternatives (hydrogen peroxide + citric acid)
    instead of chlorine bleach.

    ### Bedroom Last
    Bedrooms are lower priority for cleaning products but high priority
    for air quality. Consider swapping synthetic-fragrance sprays for
    beeswax candles or diffusers with pure essential oils.

    ## Reading Labels Like a Pro

    Ignore "natural" and "green" — they are unregulated. Instead look for:
    - EPA Safer Choice certification
    - EWG Verified mark
    - Full ingredient disclosure

    ## The GreenNest Starter Kit

    Our BioCleanse Starter Kit includes everything you need for a
    complete kitchen and bathroom switchover. Free shipping on orders
    over $65.
    (https://www.greennesthouse.com/products/biocleanse-starter-kit)

    ## Final Thoughts

    Switching to non-toxic cleaners does not have to be expensive or
    stressful. Start with one room, read labels, and choose certified
    products. Your lungs, your family, and the planet will thank you.
""")

# ── Distractor files ──────────────────────────────────────────────────────────

write(f"{WORKSPACE}/blog/drafts/wool-bedding-draft.md", """
    # DRAFT — Organic Wool Bedding: What No One Tells You
    [INCOMPLETE — DO NOT PUBLISH]
    Status: needs fact-check on fire-retardant claims.
    Target keyword: organic wool bedding benefits
""")

write(f"{WORKSPACE}/blog/drafts/zero-waste-kitchen-v2.md", """
    # Zero-Waste Kitchen: 12 Swaps You Can Make This Weekend
    Status: awaiting legal review (composting claims).
    Keyword target: zero-waste kitchen products
""")

write(f"{WORKSPACE}/marketing/campaigns/q4-2024-plan.md", """
    # Q4 2024 Campaign Plan
    Black Friday focus: BioCleanse Bundle (20% off).
    Cyber Monday: WoolNest Comforter + free pillowcase.
    Email cadence: 3 sends/week Nov 25–Dec 2.
""")

write(f"{WORKSPACE}/marketing/social/instagram-captions-oct.txt", """
    Oct 3: "Your kitchen deserves better than VOCs. 🌿 Swipe to see
    what we switched to. #nontoxichome #greenliving"
    Oct 7: "Laundry day just got a whole lot cleaner. #WoolNest"
    Oct 14: "Zero waste isn't a lifestyle. It's just Tuesday. ♻️"
""")

write(f"{WORKSPACE}/seo/reports/keyword-ranking-sep2024.csv", """
    keyword,position,url,volume
    non-toxic cleaning products,14,/blogs/journal/non-toxic-cleaning-guide,4400
    eco-friendly household cleaners,22,/blogs/journal/eco-cleaners-comparison,2900
    organic wool bedding benefits,31,/blogs/journal/wool-bedding-guide,1600
    zero-waste kitchen products,19,/blogs/journal/zero-waste-kitchen,3100
    how to switch to non-toxic cleaners,8,/blogs/journal/how-to-switch-to-non-toxic-cleaners,2200
""")

write(f"{WORKSPACE}/seo/competitor-analysis/branch-basics-gap.md", """
    # Branch Basics Content Gap Analysis
    They rank for: "non-toxic cleaning concentrate", "refillable cleaners"
    We should target: "compostable packaging cleaners", "plastic-free concentrate"
    Action: commission 2 articles by Nov 1.
""")

write(f"{WORKSPACE}/content/old-articles/2022-spring-cleaning-guide.md", """
    # Spring Cleaning Guide 2022
    [ARCHIVED — content outdated, links broken]
    Originally published: April 2022
    Reason archived: product line rebranded in 2023.
""")

write(f"{WORKSPACE}/content/repurpose-queue/repurpose-tracker.csv", """
    title,original_url,status,platform,notes
    How to Switch to Non-Toxic Cleaners,https://www.greennesthouse.com/blogs/journal/how-to-switch-to-non-toxic-cleaners,PENDING,Medium,Priority: high
    Wool Bedding Guide,https://www.greennesthouse.com/blogs/journal/wool-bedding-guide,PENDING,Medium,Wait for draft review
    Zero-Waste Kitchen,,BLOCKED,Pinterest,needs images
""")

write(f"{WORKSPACE}/ops/config/shopify-theme-vars.json", """\
    {
      "theme_id": "129847362910",
      "canonical_tag_template": "<link rel=\\"canonical\\" href=\\"{{ page.canonical_url }}\\">",
      "blog_handle": "journal",
      "sitemap_url": "/sitemap.xml"
    }
""")

write(f"{WORKSPACE}/ops/config/klaviyo-segments.yaml", """
    segments:
      - id: prospects
        trigger: signup_no_purchase
        welcome_discount: 10%
      - id: one_time
        trigger: single_order
        reactivation_window: 90_days
      - id: vip
        trigger: orders_gte_3_or_ltv_gte_250
        perks: [early_access, free_shipping_always]
""")

write(f"{WORKSPACE}/marketing/campaigns/medium-publishing-notes.txt", """
    Notes from team meeting Oct 2:
    - We need to get the non-toxic cleaners article onto Medium ASAP
    - It's been sitting in the repurpose-queue for weeks
    - Make sure it doesn't hurt our Shopify SEO — Sarah mentioned
      something about "canonical" settings but wasn't sure of details
    - The article already lives at our blog, we just want more reach
    - Use our standard keywords, they're somewhere in the project notes
""")

print("Workspace scaffold complete.")
print(f"Files written to {WORKSPACE}")