import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Directory structure with distractor files ---
dirs = [
    "data", "references", "logs", "archive",
    "reports/draft", "reports/final",
    "config", "tmp", "scripts/utils", "scripts/legacy"
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "logs/access.log": "2024-01-15 10:23:01 GET /api/recommend 200\n2024-01-15 10:23:45 GET /api/compare 200\n",
    "logs/error.log": "2024-01-14 09:00:00 ERROR: timeout connecting to upstream\n",
    "archive/old_platforms.json": json.dumps({"deprecated": True, "version": "0.1", "note": "Do not use - outdated"}),
    "archive/backup_categories.csv": "id,name,parent\n1,electronics,root\n2,clothing,root\n3,books,root\n",
    "config/app.conf": "[server]\nhost=localhost\nport=8080\n\n[cache]\nttl=3600\n",
    "config/logging.yaml": "level: INFO\nformat: '%(asctime)s %(levelname)s %(message)s'\n",
    "tmp/scratch.txt": "random scratch notes: check amazon fees, ebay listing\n",
    "scripts/utils/helpers.py": "# utility helpers - not for direct use\ndef sanitize(s): return s.strip()\n",
    "scripts/legacy/old_recommend.py": "# DEPRECATED - use online-shopping.py instead\nprint('deprecated')\n",
    "reports/draft/preliminary_notes.txt": "Draft notes: need to finalize platform comparison\nTODO: check which platform is best for electronics\n",
}

for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# --- Core data files ---
platforms_data = {
    "platforms": {
        "amazon": {
            "name": "Amazon",
            "full_name": "Amazon Global",
            "regions": ["US", "EU", "JP", "AU"],
            "strengths": ["electronics", "books", "prime_delivery", "brand_authenticity"],
            "fee_structure": {"seller_fee": "8-15%", "subscription": "optional"},
            "delivery_speed": "fast",
            "buyer_protection": "excellent",
            "rating": 4.7,
            "notes": "Best for brand-name electronics and fast delivery. Prime membership unlocks free shipping."
        },
        "ebay": {
            "name": "eBay",
            "full_name": "eBay International",
            "regions": ["US", "EU", "AU", "CA"],
            "strengths": ["collectibles", "used_goods", "auctions", "vintage"],
            "fee_structure": {"seller_fee": "10-12%", "subscription": "optional"},
            "delivery_speed": "variable",
            "buyer_protection": "good",
            "rating": 4.2,
            "notes": "Best for second-hand, collectibles, and auction-style purchases."
        },
        "aliexpress": {
            "name": "AliExpress",
            "full_name": "AliExpress Global",
            "regions": ["Global", "CN", "EU", "LatAm"],
            "strengths": ["low_price", "electronics_accessories", "fashion", "bulk_orders"],
            "fee_structure": {"seller_fee": "5-8%", "subscription": "none"},
            "delivery_speed": "slow",
            "buyer_protection": "moderate",
            "rating": 3.9,
            "notes": "Best for budget purchases. Delivery can take 2-6 weeks. Good buyer protection via dispute system."
        },
        "temu": {
            "name": "Temu",
            "full_name": "Temu Global Shopping",
            "regions": ["US", "EU", "CA", "AU"],
            "strengths": ["ultra_low_price", "fashion", "home_goods", "daily_necessities"],
            "fee_structure": {"seller_fee": "0%", "subscription": "none"},
            "delivery_speed": "moderate",
            "buyer_protection": "moderate",
            "rating": 3.7,
            "notes": "Ultra-low pricing model. Quality varies significantly. Best for non-critical everyday items."
        },
        "shopee": {
            "name": "Shopee",
            "full_name": "Shopee Southeast Asia",
            "regions": ["SEA", "TW", "BR"],
            "strengths": ["southeast_asia", "local_brands", "fashion", "food_products"],
            "fee_structure": {"seller_fee": "2-6%", "subscription": "none"},
            "delivery_speed": "fast_in_region",
            "buyer_protection": "good",
            "rating": 4.3,
            "notes": "Dominant in Southeast Asia. Best for SEA regional products and local brands."
        }
    },
    "last_updated": "2024-01-01",
    "version": "2.1"
}

categories_data = {
    "categories": {
        "electronics": {
            "id": "CAT001",
            "label": "Electronics & Gadgets",
            "subcategories": ["smartphones", "laptops", "tablets", "cameras", "audio"],
            "top_platforms": ["amazon", "aliexpress", "ebay"],
            "price_sensitivity": "high",
            "authenticity_risk": "high",
            "notes": "Verify seller ratings carefully. Brand authenticity is a major concern."
        },
        "fashion": {
            "id": "CAT002",
            "label": "Fashion & Apparel",
            "subcategories": ["clothing", "shoes", "accessories", "bags"],
            "top_platforms": ["temu", "aliexpress", "shopee"],
            "price_sensitivity": "medium",
            "authenticity_risk": "medium",
            "notes": "Sizing charts vary by region. Check return policies before purchasing."
        },
        "books": {
            "id": "CAT003",
            "label": "Books & Media",
            "subcategories": ["textbooks", "novels", "ebooks", "magazines"],
            "top_platforms": ["amazon", "ebay"],
            "price_sensitivity": "low",
            "authenticity_risk": "low",
            "notes": "Amazon dominates for new books. eBay is better for rare or used copies."
        },
        "collectibles": {
            "id": "CAT004",
            "label": "Collectibles & Antiques",
            "subcategories": ["coins", "stamps", "vintage_toys", "sports_cards"],
            "top_platforms": ["ebay"],
            "price_sensitivity": "low",
            "authenticity_risk": "very_high",
            "notes": "eBay is the definitive platform. Always request authentication certificates."
        },
        "home_goods": {
            "id": "CAT005",
            "label": "Home & Living",
            "subcategories": ["furniture", "kitchen", "bedding", "decor"],
            "top_platforms": ["temu", "aliexpress", "amazon"],
            "price_sensitivity": "high",
            "authenticity_risk": "low",
            "notes": "Temu and AliExpress offer very competitive pricing for basic home goods."
        }
    },
    "version": "1.8"
}

regions_data = {
    "regions": {
        "north_america": {
            "countries": ["US", "CA", "MX"],
            "recommended_platforms": ["amazon", "ebay", "temu"],
            "customs_complexity": "low",
            "primary_currency": "USD"
        },
        "europe": {
            "countries": ["DE", "FR", "UK", "IT", "ES"],
            "recommended_platforms": ["amazon", "ebay", "aliexpress"],
            "customs_complexity": "medium",
            "primary_currency": "EUR"
        },
        "southeast_asia": {
            "countries": ["SG", "MY", "TH", "PH", "ID", "VN"],
            "recommended_platforms": ["shopee", "aliexpress", "temu"],
            "customs_complexity": "low",
            "primary_currency": "varies"
        },
        "east_asia": {
            "countries": ["CN", "JP", "KR", "TW"],
            "recommended_platforms": ["aliexpress", "amazon", "ebay"],
            "customs_complexity": "medium",
            "primary_currency": "varies"
        }
    },
    "version": "1.3"
}

with open(os.path.join(workspace, "data/platforms.json"), "w", encoding="utf-8") as f:
    json.dump(platforms_data, f, indent=2, ensure_ascii=False)

with open(os.path.join(workspace, "data/categories.json"), "w", encoding="utf-8") as f:
    json.dump(categories_data, f, indent=2, ensure_ascii=False)

with open(os.path.join(workspace, "data/regions.json"), "w", encoding="utf-8") as f:
    json.dump(regions_data, f, indent=2, ensure_ascii=False)

# --- Reference files ---
platform_guide = """# Platform Guide

## Amazon
Amazon is the world's largest e-commerce platform. Known for reliability, fast shipping (especially with Prime), and strong buyer protection.
- **Best for**: Electronics, books, household goods
- **Shipping**: 1-5 days (Prime), 5-14 days (standard)
- **Trust score**: 9/10

## eBay
eBay pioneered online auctions. Excellent for collectibles, vintage items, and second-hand goods.
- **Best for**: Collectibles, used electronics, rare finds
- **Shipping**: Varies by seller
- **Trust score**: 8/10

## AliExpress
Alibaba's B2C platform connects global buyers with Chinese manufacturers directly.
- **Best for**: Budget electronics accessories, fashion, bulk orders
- **Shipping**: 14-45 days (standard), 7-14 days (premium)
- **Trust score**: 7/10

## Temu
New entrant with ultra-competitive pricing backed by PDD Holdings.
- **Best for**: Everyday household items, fast fashion, home goods
- **Shipping**: 7-20 days
- **Trust score**: 6.5/10

## Shopee
Southeast Asia's dominant platform with strong logistics network in the region.
- **Best for**: Southeast Asian buyers, local brands, food products
- **Shipping**: 1-7 days (within SEA)
- **Trust score**: 8/10
"""

shopping_tips = """# Shopping Tips & Red Flags

## General Tips
1. Always check seller ratings before purchasing
2. Read product reviews, especially negative ones
3. Understand the return policy before buying
4. Use platform-provided payment methods for buyer protection

## Platform-Specific Tips

### Amazon
- Use Amazon Warehouse for discounted open-box items
- Check price history using third-party tools
- Prime membership is worth it if you order frequently

### eBay
- Use "Best Offer" on fixed-price listings
- Auctions ending late at night typically go for less
- Always check seller feedback score > 98%

### AliExpress
- Use AliExpress Standard Shipping for balance of speed and cost
- Order well in advance for non-urgent items
- Use the dispute system if items don't match description

### Temu
- Prices fluctuate heavily — check multiple times
- Quality is inconsistent; read reviews carefully
- Their return policy is generous but process can be slow

## Red Flags
- Sellers with less than 100 feedback on high-value items
- Prices significantly below market (> 70% discount on electronics)
- No clear return policy stated
- Pressure tactics or countdown timers
"""

with open(os.path.join(workspace, "references/platform-guide.md"), "w", encoding="utf-8") as f:
    f.write(platform_guide)

with open(os.path.join(workspace, "references/shopping-tips.md"), "w", encoding="utf-8") as f:
    f.write(shopping_tips)

# --- The main online-shopping.py script ---
online_shopping_script = '''#!/usr/bin/env python3
"""
Online Shopping Platform Recommendation Tool
Usage:
  python3 online-shopping.py recommend <category>
  python3 online-shopping.py categories
  python3 online-shopping.py compare <platform1> <platform2>
"""

import sys
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_categories():
    data = load_json("categories.json")
    print("=== Supported Product Categories ===")
    for key, cat in data["categories"].items():
        print(f"  [{cat[\'id\']}] {key}: {cat[\'label\']}")
        print(f"       Top platforms: {\', \'.join(cat[\'top_platforms\'])}")
        print(f"       Authenticity risk: {cat[\'authenticity_risk\']}")
    print(f"\\n[Data version: {data[\'version\']}]")


def cmd_recommend(category):
    cats = load_json("categories.json")
    platforms = load_json("platforms.json")
    
    cat_key = category.lower().strip()
    if cat_key not in cats["categories"]:
        print(f"ERROR: Category \'{category}\' not found.")
        print("Run \'python3 online-shopping.py categories\' to see supported categories.")
        sys.exit(1)
    
    cat = cats["categories"][cat_key]
    print(f"=== Platform Recommendations for: {cat[\'label\']} ===")
    print(f"Category ID: {cat[\'id\']}")
    print(f"Price sensitivity: {cat[\'price_sensitivity\']}")
    print(f"Authenticity risk: {cat[\'authenticity_risk\']}")
    print(f"Notes: {cat[\'notes\']}")
    print()
    
    print("Recommended Platforms (in order):")
    for i, pname in enumerate(cat["top_platforms"], 1):
        if pname in platforms["platforms"]:
            p = platforms["platforms"][pname]
            print(f"  {i}. {p[\'name\']} (rating: {p[\'rating\']})")
            print(f"     Delivery: {p[\'delivery_speed\']} | Buyer protection: {p[\'buyer_protection\']}")
            print(f"     Tip: {p[\'notes\']}")


def cmd_compare(p1_name, p2_name):
    platforms = load_json("platforms.json")
    
    p1_key = p1_name.lower().strip()
    p2_key = p2_name.lower().strip()
    
    errors = []
    if p1_key not in platforms["platforms"]:
        errors.append(f"Platform \'{p1_name}\' not found.")
    if p2_key not in platforms["platforms"]:
        errors.append(f"Platform \'{p2_name}\' not found.")
    
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print("Supported platforms: " + ", ".join(platforms["platforms"].keys()))
        sys.exit(1)
    
    p1 = platforms["platforms"][p1_key]
    p2 = platforms["platforms"][p2_key]
    
    print(f"=== Platform Comparison: {p1[\'name\']} vs {p2[\'name\']} ===")
    
    fields = [
        ("Full Name", "full_name"),
        ("Regions", "regions"),
        ("Delivery Speed", "delivery_speed"),
        ("Buyer Protection", "buyer_protection"),
        ("Rating", "rating"),
    ]
    
    for label, field in fields:
        v1 = p1[field]
        v2 = p2[field]
        if isinstance(v1, list):
            v1 = ", ".join(v1)
        if isinstance(v2, list):
            v2 = ", ".join(v2)
        print(f"  {label}:")
        print(f"    {p1[\'name\']}: {v1}")
        print(f"    {p2[\'name\']}: {v2}")
    
    print()
    print("  Strengths:")
    print(f"    {p1[\'name\']}: {\', \'.join(p1[\'strengths\'])}")
    print(f"    {p2[\'name\']}: {\', \'.join(p2[\'strengths\'])}")
    
    print()
    print("  Notes:")
    print(f"    {p1[\'name\']}: {p1[\'notes\']}")
    print(f"    {p2[\'name\']}: {p2[\'notes\']}")
    
    # Winner summary
    print()
    print("  Overall Ratings:")
    print(f"    {p1[\'name\']}: {p1[\'rating\']}/5.0")
    print(f"    {p2[\'name\']}: {p2[\'rating\']}/5.0")
    if p1["rating"] > p2["rating"]:
        print(f"  >> Overall winner by rating: {p1[\'name\']}")
    elif p2["rating"] > p1["rating"]:
        print(f"  >> Overall winner by rating: {p2[\'name\']}")
    else:
        print(f"  >> Ratings are equal.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "categories":
        cmd_categories()
    elif cmd == "recommend":
        if len(sys.argv) < 3:
            print("Usage: python3 online-shopping.py recommend <category>")
            sys.exit(1)
        cmd_recommend(sys.argv[2])
    elif cmd == "compare":
        if len(sys.argv) < 4:
            print("Usage: python3 online-shopping.py compare <platform1> <platform2>")
            sys.exit(1)
        cmd_compare(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "online-shopping.py"), "w", encoding="utf-8") as f:
    f.write(online_shopping_script)

# --- Distractor scripts that shouldn't be used ---
with open(os.path.join(workspace, "scripts/legacy/platform_compare_v1.py"), "w") as f:
    f.write("# Old comparison tool - DO NOT USE\n# Deprecated in favor of online-shopping.py\nprint('This tool is deprecated')\n")

with open(os.path.join(workspace, "scripts/utils/data_loader.py"), "w") as f:
    f.write("# Utility for loading platform data\nimport json\ndef load(fp):\n    with open(fp) as f:\n        return json.load(f)\n")

# An intentionally misleading report template in the wrong format
with open(os.path.join(workspace, "reports/draft/template_WRONG.json"), "w") as f:
    json.dump({
        "note": "This is an OLD template format - do not use",
        "platforms": [],
        "generated": "manually"
    }, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")