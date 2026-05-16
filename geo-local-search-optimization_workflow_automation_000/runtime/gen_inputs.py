import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── directory structure with distractors ──────────────────────────────────────
dirs = [
    "workspace/admin/licenses",
    "workspace/admin/contracts",
    "workspace/marketing/drafts",
    "workspace/marketing/old_campaigns",
    "workspace/marketing/social",
    "workspace/operations/staff",
    "workspace/operations/inventory",
    "workspace/finance/invoices",
    "workspace/media/photos",
    "workspace/media/videos",
    "workspace/seo/competitors",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "workspace/admin/contracts/supplier_A.txt":
        "Supplier: Sichuan Fresh Produce Co.\nContract value: 50,000 CNY/year\nRenewal date: 2025-03-01",
    "workspace/admin/contracts/lease_agreement.txt":
        "Landlord: Chengdu Commercial Properties Ltd.\nMonthly rent: 18,000 CNY\nLease term: 3 years starting 2024-06-01",
    "workspace/marketing/old_campaigns/spring_promo_2023.txt":
        "Spring promotion: 20% off all hot-pots in March 2023\nResult: 340 new customers",
    "workspace/marketing/social/weibo_schedule.txt":
        "Post times: Mon 12:00, Wed 18:00, Fri 19:00\nAccount: @HaiDiLaoPinecone",
    "workspace/operations/staff/roster_july.csv":
        "Name,Role,Shift\nLi Wei,Chef,Morning\nZhang Fang,Waiter,Evening\nWang Bo,Cashier,Full",
    "workspace/operations/inventory/spices_stock.txt":
        "Sichuan peppercorn: 50kg\nDried chili: 30kg\nDoubanjiang: 120kg",
    "workspace/finance/invoices/invoice_0081.txt":
        "Invoice #0081\nVendor: Chengdu Gas Supply\nAmount: 3,200 CNY\nDate: 2025-05-10",
    "workspace/media/photos/photo_list.txt":
        "interior_01.jpg, interior_02.jpg, dish_spicy_hotpot.jpg, dish_mild_broth.jpg",
    "workspace/media/videos/video_notes.txt":
        "Promo video shot on 2025-04-15, duration 90s, editor: Xiao Chen",
    "workspace/seo/competitors/competitor_notes.txt":
        "Main competitors in Jinjiang District:\n1. Lao Ma Hot Pot - avg rating 4.3\n2. Huang Cheng Ba Zi - avg rating 4.5\n3. Shu Jiu Xiang - avg rating 4.1",
    "workspace/admin/licenses/OLD_registration_draft.txt":
        "DRAFT - NOT VALID\nBusiness: Pinecone Hotpot (informal name)\nNote: This is the nickname used internally, NOT the legal registered name.",
}
for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── CORE INPUT 1: messy business brief (contains WRONG/informal business name) ─
# The brief uses an informal alias "Pinecone Hotpot" but the license has the real name.
brief_content = """
BUSINESS BRIEF — Internal Working Document
==========================================
(Prepared by front-desk manager, may contain informal names)

Shop nickname / alias: Pinecone Hotpot  ← we just call it this internally
Real registered name: SEE LICENSE FILE

Address:
  Province:  Sichuan
  City:      Chengdu
  District:  Jinjiang District
  Street:    Shaocheng Road, No. 88
  Postcode:  610000

Contact phone: 028-85551234

Main business: Authentic Sichuan-style hot pot restaurant, specialising in
spicy mala broth and premium beef/mutton slices. Offers private dining rooms
for groups up to 20 people.

Target customers: Local Chengdu residents aged 20-45, office workers, couples,
families, and tourists visiting Jinjiang historical district.

Keywords we want to rank for (5 industry-specific):
  1. 成都火锅推荐 (Chengdu hotpot recommendations)
  2. 锦江区麻辣火锅 (Jinjiang District spicy hotpot)
  3. 成都聚餐好去处 (Good group dining in Chengdu)
  4. 正宗四川火锅 (Authentic Sichuan hotpot)
  5. 成都网红火锅店 (Chengdu trending hotpot restaurants)

Note: The real legal business name is on the license. Please use that name
in ALL published content — NOT the nickname above.
"""
with open("workspace/admin/licenses/business_brief.txt", "w", encoding="utf-8") as f:
    f.write(brief_content)

# ── CORE INPUT 2: Business license (authoritative name source) ────────────────
license_content = """
BUSINESS LICENSE (营业执照) — OFFICIAL COPY
============================================
Registration Number: 91510104MA62XXXX8Y
Legal Business Name:  成都松果餐饮管理有限公司锦江分店
                      (Chengdu Songguo Catering Management Co., Ltd. — Jinjiang Branch)
English Trade Name:   Chengdu Songguo Hotpot Restaurant (Jinjiang)
Business Type:        Catering Services / Restaurant
Registered Address:   四川省成都市锦江区少城路88号
                      (No. 88, Shaocheng Road, Jinjiang District, Chengdu, Sichuan)
Legal Representative: Chen Jianming
Registration Date:    2024-01-15
Validity Period:      Long-term
Approved Scope:       Hot pot catering, beverage sales, private dining services
"""
with open("workspace/admin/licenses/business_license.txt", "w", encoding="utf-8") as f:
    f.write(license_content)

# ── CORE INPUT 3: Media channels list (agent must apply selection rules) ──────
# Includes cross-industry traps, wrong-tier, and multiple candidates per tier
# For a restaurant, valid = food/lifestyle/local consumption; invalid = automotive/education/beauty
media_channels = [
    # Provincial-level — food/lifestyle (VALID for restaurant)
    {"id": "M01", "name": "四川美食频道", "type": "food", "tier": "provincial",
     "price_cny": 800, "industry": "food_lifestyle"},
    {"id": "M02", "name": "四川生活资讯", "type": "lifestyle", "tier": "provincial",
     "price_cny": 650, "industry": "food_lifestyle"},
    # Provincial-level — automotive (INVALID for restaurant — cross-industry trap)
    {"id": "M03", "name": "四川汽车之家", "type": "automotive", "tier": "provincial",
     "price_cny": 500, "industry": "automotive"},
    # Provincial-level — education (INVALID for restaurant)
    {"id": "M04", "name": "四川教育网", "type": "education", "tier": "provincial",
     "price_cny": 300, "industry": "education"},
    # Municipal-level — food/lifestyle (VALID)
    {"id": "M05", "name": "成都吃喝玩乐", "type": "food", "tier": "municipal",
     "price_cny": 500, "industry": "food_lifestyle"},
    {"id": "M06", "name": "成都本地生活", "type": "lifestyle", "tier": "municipal",
     "price_cny": 420, "industry": "food_lifestyle"},
    # Municipal-level — beauty (INVALID for restaurant)
    {"id": "M07", "name": "成都时尚美妆", "type": "beauty", "tier": "municipal",
     "price_cny": 380, "industry": "beauty"},
    # Municipal-level — sports/fitness (INVALID for restaurant)
    {"id": "M08", "name": "成都运动健身圈", "type": "fitness", "tier": "municipal",
     "price_cny": 310, "industry": "fitness"},
    # Local self-media — food/lifestyle (VALID)
    {"id": "M09", "name": "锦江吃货联盟", "type": "food", "tier": "local",
     "price_cny": 200, "industry": "food_lifestyle"},
    {"id": "M10", "name": "少城路生活号", "type": "lifestyle", "tier": "local",
     "price_cny": 180, "industry": "food_lifestyle"},
    {"id": "M11", "name": "锦江区消费指南", "type": "local_consumption", "tier": "local",
     "price_cny": 150, "industry": "food_lifestyle"},
    # Local self-media — automotive (INVALID)
    {"id": "M12", "name": "锦江二手车资讯", "type": "automotive", "tier": "local",
     "price_cny": 100, "industry": "automotive"},
]
with open("workspace/marketing/media_channels.json", "w", encoding="utf-8") as f:
    json.dump(media_channels, f, ensure_ascii=False, indent=2)

# ── SKILL.md (placed in workspace root as reference) ─────────────────────────
skill_md = """# Geo Local Search Optimization Skill

This skill helps local businesses optimize their presence in AI search results by creating AI-friendly media content and providing step-by-step guidance for local search optimization.

## Description
In the AI era, customers increasingly ask AI models like Doudou, Qwen, and others for local business recommendations. This skill guides users through a complete 7-day AI search optimization process to ensure their business appears in AI recommendations.

## Workflow
1. **Introduction**: Explain AI search revolution and benefits
2. **Information Collection**: Gather business details and keywords
3. **Strategy Development**: Create keyword strategy and map verification guide
4. **Competitor Analysis**: Show current AI search landscape
5. **Content Generation**: Generate 7 days of complete media articles (500+ words each)
6. **Publishing Guidance**: Recommend media channels and publishing instructions

## Input Requirements
- Business name (must match license exactly)
- Complete address (province, city, district, street, number)
- Contact phone number
- Main business/services
- Target customer demographics  
- 5 industry-specific search keywords

## Output Format
- Daily media articles with title, 500+ word content, business address and phone
- Step-by-step execution guidance
- Media publishing recommendations

## Safety Guidelines
- All content must be truthful and verifiable
- Business information must be accurate and consistent
- No false claims or misleading information
- Content should follow journalistic standards
- Media selection must be relevant to business type and location
- Avoid cross-industry publishing (e.g., restaurants should not publish on automotive sites)

## Media Selection Guidelines
- **Geographic Hierarchy**: Provincial + Municipal + Local self-media
- **Industry Relevance**: Match media type to business category
  - Restaurants: Food, lifestyle, local consumption media
  - Fitness: Sports, health, wellness media  
  - Automotive: Car, transportation, local service media
  - Beauty: Fashion, beauty, lifestyle media
  - Education: Education, parenting, learning media
- **Cost Efficiency**: Choose lowest-priced media within same tier (same effectiveness)

## Effectiveness Verification
- Test AI search results 24-48 hours after publication
- Query AI models (Doudou, DeepSeek, Qwen, Yuanbao) with customer-like questions
- Monitor ranking changes weekly
- Success indicators: Business name appears in AI responses, accurate location/service details

## License
MIT - Free and open source, no commercial restrictions. Designed to help local businesses succeed in the AI era.
"""
with open("workspace/SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_md)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")