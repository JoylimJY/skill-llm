import os
import json
import random

random.seed(42)

# Create directory structure
dirs = [
    "workspace/reviews/raw",
    "workspace/reviews/processed",
    "workspace/reviews/archive",
    "workspace/config",
    "workspace/logs",
    "workspace/models/weights",
    "workspace/models/vocab",
    "workspace/output/reports",
    "workspace/output/exports",
    "workspace/tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/config/db_config.yaml": "host: localhost\nport: 5432\ndb: reviews_db\nuser: analyst\n",
    "workspace/config/pipeline_settings.json": json.dumps({"batch_size": 32, "language": "zh", "model": "v2.1"}, ensure_ascii=False, indent=2),
    "workspace/logs/pipeline_2024_01.log": "2024-01-10 09:12:34 INFO Processing batch 001\n2024-01-10 09:13:01 INFO Batch complete: 128 records\n2024-01-10 09:14:22 WARN Encoding issue in record 77\n",
    "workspace/logs/pipeline_2024_02.log": "2024-02-15 11:00:00 INFO Starting daily pipeline\n2024-02-15 11:02:45 INFO 256 reviews processed\n",
    "workspace/models/vocab/stopwords_zh.txt": "的\n了\n和\n是\n就\n都\n而\n及\n与\n这\n那\n",
    "workspace/models/weights/model_metadata.json": json.dumps({"version": "2.1", "trained_on": "2024-01", "accuracy": 0.87}),
    "workspace/reviews/archive/batch_001_summary.txt": "Batch 001: 128 reviews, avg sentiment 0.62, top keyword: 质量\n",
    "workspace/reviews/archive/batch_002_summary.txt": "Batch 002: 256 reviews, avg sentiment 0.71, top keyword: 快递\n",
    "workspace/tmp/scratch.txt": "temp working file - do not use\n",
    "workspace/output/exports/schema_v1.json": json.dumps({"fields": ["review_id", "sentiment", "keywords", "readability"]}),
    "workspace/output/reports/sample_report_old.txt": "Old format report - deprecated\nReview analysis for Q4 2023\n",
}

for path, content in distractor_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# The actual input: a batch of Chinese customer reviews to analyze
# Each review is carefully crafted to require specific SKILL.md features:
# Review 1: Sarcasm via "厉害了" + 🙄🙄🙄 (must flip to negative)
# Review 2: Positive sentiment, classical Chinese elements (high readability score)
# Review 3: Internet slang "yyds", mixed language, buried lead structure
# Review 4: Rhetorical question + "也是醉了" sarcasm marker
# Review 5: Long complex text with technical jargon, high readability

reviews = [
    {
        "id": "R001",
        "text": "厉害了这个商品，质量真是厉害了🙄🙄🙄，用了三天就坏了，客服态度也是醉了，完全不处理投诉，简直让人无语。强烈建议大家不要购买。"
    },
    {
        "id": "R002",
        "text": "此物件做工精良，用料上乘，观之赏心悦目，触之质感极佳。商家诚信经营，快递迅速，包装完善，实乃购物之佳选。非常满意，强烈推荐！😊❤️"
    },
    {
        "id": "R003",
        "text": "这个产品yyds！界面设计很nice，操作简单，feature很多。虽然有一些bug需要修复，但总体来说是我用过最好的同类产品，开发团队很用心，期待后续更新。"
    },
    {
        "id": "R004",
        "text": "这也算好产品？发货三周才到，包装破损严重，产品和图片完全不符，这服务也能叫服务？呵呵，你开心就好。😤👎下次绝对不会再来了。"
    },
    {
        "id": "R005",
        "text": "本产品采用第三代纳米复合材料技术，具备超高分子聚合物基底结构，经ISO9001及CE双重国际认证体系认证，在高温高压环境下仍可保持卓越的物理化学性能稳定性。适用于航空航天、精密制造、生物医疗等尖端领域，专业技术人员操作必读详细说明书后方可使用。"
    }
]

with open("workspace/reviews/raw/customer_reviews_batch_007.json", "w", encoding="utf-8") as f:
    json.dump(reviews, f, ensure_ascii=False, indent=2)

# Also place a plain text version as distractor
with open("workspace/reviews/raw/batch_007_metadata.txt", "w", encoding="utf-8") as f:
    f.write("Batch 007 - Received 2024-03-15\nSource: Mobile App Reviews\nTotal records: 5\nEncoding: UTF-8\nPriority: HIGH - Content moderation required\n")

print("Workspace generated successfully.")
print("Input file: workspace/reviews/raw/customer_reviews_batch_007.json")