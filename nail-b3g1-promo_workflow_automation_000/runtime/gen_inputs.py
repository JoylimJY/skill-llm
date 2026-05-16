import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Brand & Product Context Files ---
os.makedirs(f"{workspace}/brand", exist_ok=True)
os.makedirs(f"{workspace}/brand/collections", exist_ok=True)
os.makedirs(f"{workspace}/brand/pricing", exist_ok=True)
os.makedirs(f"{workspace}/brand/campaigns/past", exist_ok=True)
os.makedirs(f"{workspace}/brand/campaigns/drafts", exist_ok=True)
os.makedirs(f"{workspace}/ops/reporting", exist_ok=True)
os.makedirs(f"{workspace}/ops/platform", exist_ok=True)
os.makedirs(f"{workspace}/marketing/copy_bank", exist_ok=True)
os.makedirs(f"{workspace}/marketing/social", exist_ok=True)

# brand/collections/product_catalog.csv — distractor
with open(f"{workspace}/brand/collections/product_catalog.csv", "w") as f:
    f.write("sku,name,collection,price,margin_pct,launched_weeks_ago\n")
    f.write("CE-001,Magnetic Cat-Eye Noir,cat-eye,14.99,62,12\n")
    f.write("CE-002,Magnetic Cat-Eye Aurora,cat-eye,14.99,60,8\n")
    f.write("CE-003,Magnetic Cat-Eye Crimson,cat-eye,14.99,61,5\n")
    f.write("MT-001,Matte Velvet Black,matte,12.99,58,20\n")
    f.write("MT-002,Matte Clay Rose,matte,12.99,57,18\n")
    f.write("GE-001,Gel-Effect Coral Pop,gel-effect,13.99,59,15\n")
    f.write("GE-002,Gel-Effect Berry Bliss,gel-effect,13.99,58,10\n")
    f.write("SS-001,Seasonal Starfall Glitter,seasonal,16.99,48,1\n")
    f.write("SS-002,Seasonal Frosted Petal,seasonal,15.99,47,0\n")
    f.write("GS-001,Gift Set Trio Classic,gift-set,39.99,30,24\n")

# brand/pricing/margin_notes.txt — distractor
with open(f"{workspace}/brand/pricing/margin_notes.txt", "w") as f:
    f.write("Minimum acceptable blended margin floor: 45%\n")
    f.write("Gift sets run at lower margin due to packaging — exclude from free-item eligibility.\n")
    f.write("Seasonal SKUs launched within first 2 weeks should be excluded from 'free' eligibility.\n")
    f.write("Cat-eye, matte, gel-effect: core lines, eligible for promos.\n")

# brand/campaigns/past/summer_flash_2023.txt — distractor
with open(f"{workspace}/brand/campaigns/past/summer_flash_2023.txt", "w") as f:
    f.write("Campaign: Summer Flash 2023\n")
    f.write("Mechanic: 15% off site-wide, code SUMMER15\n")
    f.write("Result: AOV dropped slightly, many single-item orders. Not ideal.\n")
    f.write("Recommendation: Consider multi-buy mechanic next time.\n")

# brand/campaigns/drafts/ideas_q4.txt — distractor
with open(f"{workspace}/brand/campaigns/drafts/ideas_q4.txt", "w") as f:
    f.write("Q4 promo ideas (DRAFT - not approved):\n")
    f.write("- Flash 20% off weekend (rejected by margin team)\n")
    f.write("- Bundle 3 polishes together at fixed price\n")
    f.write("- Buy 3 get 1 free — preferred by CEO, needs proper campaign doc\n")
    f.write("- Holiday gift set push\n")

# ops/platform/shopify_config_notes.txt — distractor
with open(f"{workspace}/ops/platform/shopify_config_notes.txt", "w") as f:
    f.write("Platform: Shopify (lacquerlux.myshopify.com)\n")
    f.write("Current apps: Email pop-up, review widget, basic discount codes\n")
    f.write("No loyalty or advanced promo app currently installed.\n")
    f.write("Team is open to installing a third-party app for cart automation.\n")
    f.write("Cart: default Shopify cart, no custom checkout.\n")

# ops/reporting/kpi_baseline.csv — distractor
with open(f"{workspace}/ops/reporting/kpi_baseline.csv", "w") as f:
    f.write("metric,value,period\n")
    f.write("avg_order_value,18.50,last_90_days\n")
    f.write("avg_units_per_order,1.4,last_90_days\n")
    f.write("repeat_purchase_rate_pct,22,last_90_days\n")
    f.write("top_collection,cat-eye,last_90_days\n")

# marketing/copy_bank/generic_taglines.txt — distractor
with open(f"{workspace}/marketing/copy_bank/generic_taglines.txt", "w") as f:
    f.write("Existing brand taglines (general use):\n")
    f.write("- 'Your nails, your rules.'\n")
    f.write("- 'Cat-eye magic, everyday.'\n")
    f.write("- 'Matte is the new glam.'\n")

# marketing/social/instagram_schedule.txt — distractor
with open(f"{workspace}/marketing/social/instagram_schedule.txt", "w") as f:
    f.write("Instagram posting schedule (Q4):\n")
    f.write("Mon/Wed/Fri: Product shots\n")
    f.write("Tue/Thu: UGC reposts\n")
    f.write("Sat: Promo announcement (pending campaign finalization)\n")

# The KEY task brief — gives context but NOT the required output structure
with open(f"{workspace}/campaign_brief.txt", "w") as f:
    f.write("=== LacquerLux Campaign Brief — Internal ===\n\n")
    f.write("Brand: LacquerLux (DTC nail polish, Shopify store)\n")
    f.write("Lines: cat-eye, matte, gel-effect nail polish; seasonal line just launched this week\n")
    f.write("Request: We want to run a 'buy 3 get 1 free' promotion.\n\n")
    f.write("Key constraints from the business team:\n")
    f.write("- No manual discount codes — must work automatically when customer adds items\n")
    f.write("- Our minimum margin floor is 45% blended\n")
    f.write("- Gift sets should NOT be eligible for the free item\n")
    f.write("- The new seasonal collection launched this week — handle carefully on margin\n")
    f.write("- We are on Shopify; open to installing an app if needed\n")
    f.write("- Brand tone: playful but clear. Customers sometimes don't get multi-buy rules.\n\n")
    f.write("Deliverable needed: A complete campaign design document our team and platform vendor can act on.\n")
    f.write("Save the final document as: lacquerlux_b3g1_campaign.md\n")