import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "site/category/grooming",
    "site/category/grooming/dog-grooming",
    "site/category/grooming/cat-grooming",
    "site/category/grooming/tools-and-accessories",
    "site/products",
    "site/products/shampoos",
    "site/products/brushes",
    "site/assets/images",
    "site/assets/css",
    "analytics/reports",
    "analytics/crawl-data",
    "content/drafts",
    "content/published",
    "seo/audits",
    "seo/schema",
    "config",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "site/assets/css/main.css": "body { font-family: Arial; } .product-grid { display: grid; }",
    "site/assets/images/.gitkeep": "",
    "logs/crawl_errors_2024-01.log": "\n".join([
        "404 /category/grooming/dog/large-breeds",
        "404 /category/grooming/cat/persian",
        "301 /category/grooming/shampoo -> /category/grooming/shampoos",
        "500 /category/grooming/tools-and-accessories?sort=price_asc&color=blue&brand=furminator",
    ]),
    "analytics/reports/traffic_q1_2024.json": json.dumps({
        "top_pages": ["/category/grooming", "/category/grooming/dog-grooming"],
        "bounce_rate": 0.62,
        "avg_session_duration": 142
    }, indent=2),
    "analytics/crawl-data/coverage_report.csv": (
        "URL,Status,Indexed\n"
        "/category/grooming,200,yes\n"
        "/category/grooming/dog-grooming?size=large&coat=double,200,yes\n"
        "/category/grooming/dog-grooming?size=small,200,yes\n"
        "/category/grooming/cat-grooming?brand=furminator,200,yes\n"
        "/category/grooming/tools-and-accessories,200,yes\n"
        "/category/grooming/tools-and-accessories?price=0-20,200,yes\n"
    ),
    "content/drafts/grooming_copy_v1.txt": (
        "Welcome to our grooming section! Here you will find a wide variety of grooming products "
        "for your beloved pets. We stock shampoos, conditioners, brushes, combs, nail clippers, "
        "and much more. Our products are sourced from top manufacturers worldwide and are suitable "
        "for dogs, cats, and small animals. Browse our selection and find the perfect grooming "
        "solution for your furry friend today.\n\n"
        "[NOTE: Marketing team says this is too short and generic. Also uses manufacturer copy from FurBrand Inc.]"
    ),
    "content/published/homepage_copy.txt": "Welcome to PawPerfect — your one-stop shop for all things pet.",
    "config/site_config.yaml": (
        "site_name: PawPerfect Pet Supplies\n"
        "base_url: https://www.pawperfect.com\n"
        "platform: custom_php\n"
        "robots_txt_managed: manual\n"
        "canonical_handled_by: meta_tag\n"
    ),
    "seo/audits/2023_audit_notes.txt": (
        "Issues found:\n"
        "- Category URLs include /category/ prefix — bad for SEO\n"
        "- Faceted filter URLs are being indexed (crawl waste)\n"
        "- No schema markup on category pages\n"
        "- Title tags on category pages average 72 characters (too long)\n"
        "- Meta descriptions missing on 60% of pages\n"
        "- Category intro copy is <50 words on most pages\n"
        "- /category/grooming/tools-and-accessories is 5 clicks from homepage\n"
    ),
    "seo/schema/.gitkeep": "",
    "site/products/shampoos/product_list.json": json.dumps([
        {"id": "sh001", "name": "FurGlow Oatmeal Shampoo", "price": 12.99, "rating": 4.6, "reviews": 312},
        {"id": "sh002", "name": "HydraCoat Conditioning Shampoo", "price": 15.49, "rating": 4.4, "reviews": 187},
        {"id": "sh003", "name": "PupFresh Whitening Shampoo", "price": 9.99, "rating": 4.7, "reviews": 523},
    ], indent=2),
    "site/products/brushes/product_list.json": json.dumps([
        {"id": "br001", "name": "ShedLess Slicker Brush", "price": 18.99, "rating": 4.8, "reviews": 891},
        {"id": "br002", "name": "DualCoat Dematting Comb", "price": 22.50, "rating": 4.5, "reviews": 445},
        {"id": "br003", "name": "SoftGlide Pin Brush", "price": 14.75, "rating": 4.3, "reviews": 267},
    ], indent=2),
    "site/category/grooming/dog-grooming/index.html": (
        "<!DOCTYPE html><html><head><title>Dog Grooming Products | Category | PawPerfect</title>"
        "<meta name='description' content='Shop dog grooming products.'></head>"
        "<body><h1>Dog Grooming</h1><p>Browse our dog grooming range.</p></body></html>"
    ),
    "site/category/grooming/cat-grooming/index.html": (
        "<!DOCTYPE html><html><head><title>Cat Grooming - PawPerfect Pet Supplies Online Store</title>"
        "<meta name='description' content='Cat grooming products for all breeds and coat types available at PawPerfect.'></head>"
        "<body><h1>Cat Grooming Products and Accessories for Your Feline Friend</h1>"
        "<p>Browse products.</p></body></html>"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Core problem input: messy catalog spec that agent must process ---
messy_catalog = {
    "store": "PawPerfect Pet Supplies",
    "base_url": "https://www.pawperfect.com",
    "new_section": {
        "name": "Dog Grooming Shampoos & Conditioners",
        "description_raw": (
            "This is the page for all of our the dog shampoo products. "
            "We carry shampoos and conditioners for dogs of all sizes. "
            "If you are looking for a shampoo that is good for sensitive skin or a whitening formula, "
            "we have got you covered. Our shampoos are made with natural ingredients."
        ),
        "parent_category": "Dog Grooming",
        "grandparent_category": "Pet Grooming",
        "current_bad_url": "https://www.pawperfect.com/category/Pet-Grooming/Dog-Grooming/Shampoos-And-Conditioners",
        "active_filters": [
            {"name": "Coat Type", "values": ["short", "long", "double", "curly"]},
            {"name": "Skin Concern", "values": ["sensitive", "whitening", "moisturizing", "shedding"]},
            {"name": "Brand", "values": ["FurGlow", "HydraCoat", "PupFresh"]},
            {"name": "Price Range", "values": ["under-10", "10-20", "over-20"]},
        ],
        "sample_filter_urls": [
            "https://www.pawperfect.com/category/Pet-Grooming/Dog-Grooming/Shampoos-And-Conditioners?coat_type=long&skin_concern=sensitive",
            "https://www.pawperfect.com/category/Pet-Grooming/Dog-Grooming/Shampoos-And-Conditioners?brand=FurGlow&price=10-20",
        ],
        "products": [
            {"id": "sh001", "name": "FurGlow Oatmeal Shampoo", "price": 12.99, "rating": 4.6, "reviews": 312},
            {"id": "sh002", "name": "HydraCoat Conditioning Shampoo", "price": 15.49, "rating": 4.4, "reviews": 187},
            {"id": "sh003", "name": "PupFresh Whitening Shampoo", "price": 9.99, "rating": 4.7, "reviews": 523},
        ],
        "faq_questions_raw": [
            "What shampoo is good for a dog with sensitive skin?",
            "Can I use human shampoo on my dog?",
            "How often should I bathe my dog?",
            "What is the best whitening shampoo for dogs?",
        ],
        "clicks_from_homepage": 5,
        "target_keyword": "dog shampoo",
        "secondary_keyword": "dog grooming shampoo",
    }
}

with open(os.path.join(workspace, "catalog_spec.json"), "w") as f:
    json.dump(messy_catalog, f, indent=2)

# Create a placeholder for the expected output location (agent discovers where to put it)
os.makedirs(os.path.join(workspace, "seo"), exist_ok=True)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in Path(workspace).rglob('*') if _.is_file()) if False else 'many'}")