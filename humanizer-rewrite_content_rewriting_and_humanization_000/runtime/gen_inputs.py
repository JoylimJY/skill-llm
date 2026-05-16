import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/marketing/campaigns/2024/q4",
    "workspace/marketing/campaigns/2024/q3",
    "workspace/marketing/templates",
    "workspace/marketing/archive",
    "workspace/content/drafts",
    "workspace/content/published",
    "workspace/content/reviews",
    "workspace/analytics/reports",
    "workspace/analytics/raw",
    "workspace/hr/announcements",
    "workspace/tech/docs",
    "workspace/tech/specs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractors = {
    "workspace/marketing/campaigns/2024/q4/budget_plan.txt": "Q4 Marketing Budget\nTotal: ¥500,000\nDigital: ¥200,000\nPrint: ¥100,000\nEvents: ¥200,000",
    "workspace/marketing/campaigns/2024/q3/performance_report.txt": "Q3 Campaign Performance\nCTR: 2.3%\nConversion: 1.1%\nROI: 340%",
    "workspace/marketing/templates/email_template.txt": "亲爱的客户，\n感谢您一直以来对我们的支持...",
    "workspace/marketing/archive/2023_summary.txt": "2023年度营销总结\n全年营收增长15%",
    "workspace/content/published/product_v1.txt": "我们的产品在市场上取得了显著的成绩。",
    "workspace/content/reviews/review_notes.txt": "审稿意见：文章需要更自然的表达，减少AI感。",
    "workspace/analytics/reports/monthly_traffic.txt": "月度流量报告\n页面访问: 45,231\n独立访客: 12,088",
    "workspace/analytics/raw/raw_data.csv": "date,visits,conversions\n2024-01-01,1200,45\n2024-01-02,1350,52",
    "workspace/hr/announcements/holiday_notice.txt": "关于春节放假安排的通知\n根据国家法定节假日安排...",
    "workspace/tech/docs/api_reference.txt": "API参考文档\nGET /api/v1/users\nPOST /api/v1/products",
    "workspace/tech/specs/system_requirements.txt": "系统需求\nCPU: 4核\n内存: 8GB\n存储: 100GB",
    "workspace/content/drafts/old_draft.txt": "这是一篇旧草稿，内容已过时。",
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN TASK FILE: A clearly AI-generated article about a product launch
ai_article = """随着人工智能技术的飞速发展，智能家居领域迎来了前所未有的变革。在当今社会，越来越多的家庭开始关注智能家居产品的使用体验与实际价值。我们公司推出的"智家Pro 3.0"产品，凭借其卓越的技术性能和人性化的设计理念，在市场上获得了广泛的认可。

值得注意的是，智家Pro 3.0采用了业界领先的AI芯片，处理速度较上一代提升了300%。此外，该产品还配备了全新的语音识别系统，识别准确率高达99.7%。与此同时，其能耗管理系统也进行了全面优化，整体能耗降低了40%。

在用户体验方面，智家Pro 3.0进行了大量的改进与优化。首先，其界面设计更加简洁直观，用户可以轻松上手。其次，系统的响应速度得到了显著提升，延迟时间控制在50毫秒以内。最后，该产品还支持多平台互联，可与市面上主流的智能设备无缝对接。

综上所述，智家Pro 3.0是一款集先进技术与优质体验于一身的智能家居产品。它的推出不仅标志着我们公司在技术创新方面迈出了重要一步，也为广大用户带来了更加便捷、智能的生活方式。未来，我们将继续深耕智能家居领域，不断探索技术边界，为用户创造更多价值。智家Pro 3.0的成功发布让我们对未来充满期待，相信在科技的引领下，智能生活将变得更加美好，未来可期。
"""

article_path = "workspace/content/drafts/product_launch_article.txt"
with open(article_path, "w", encoding="utf-8") as f:
    f.write(ai_article)

print("Workspace generated successfully.")
print(f"Main task file: {article_path}")
print(f"Total distractor files: {len(distractors)}")