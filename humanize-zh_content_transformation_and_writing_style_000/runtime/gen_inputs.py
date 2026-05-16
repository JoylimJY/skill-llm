import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# === Create deeply nested distractor structure ===
distractor_dirs = [
    "content/drafts/2024/q1",
    "content/drafts/2024/q2",
    "content/published/tech",
    "content/published/lifestyle",
    "assets/images/product",
    "assets/images/banner",
    "templates/email",
    "templates/social",
    "logs/analytics",
    "config/seo",
    "archive/2023",
    "archive/2022",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# === Distractor files ===
distractor_files = {
    "content/drafts/2024/q1/schedule.txt": "Article schedule for Q1 2024\nWeek 1: Camera reviews\nWeek 2: Laptop comparisons",
    "content/drafts/2024/q2/topics.txt": "Planned topics:\n- Smart home devices\n- Budget phones 2024",
    "content/published/tech/seo_notes.md": "SEO keywords: 手机评测, 性价比, 推荐",
    "content/published/lifestyle/style_guide.txt": "Writing style: casual, friendly, relatable",
    "assets/images/product/readme.txt": "Product images directory - do not modify",
    "assets/images/banner/specs.txt": "Banner size: 1200x628px",
    "templates/email/newsletter_template.txt": "Hello {{name}}, here is this week's tech roundup...",
    "templates/social/weibo_template.txt": "限时分享！{{product}}最新评测来了...",
    "logs/analytics/pageviews_2024.csv": "date,views,article\n2024-01-01,1200,phone_review\n2024-01-02,890,laptop_guide",
    "config/seo/keywords.json": '{"primary": ["手机", "评测"], "secondary": ["性价比", "推荐"]}',
    "archive/2023/old_articles_index.txt": "Archive index for 2023 articles",
    "archive/2022/legacy_format_note.txt": "Legacy articles stored in plain text format",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# === THE ACTUAL PROBLEM FILES (AI-flavored articles to be humanized) ===

# Article 1: A software productivity tool review
article1_ai = """标题：效率工具深度评测

在当今数字化时代，效率工具的重要性日益凸显。本文将从三个方面对这款工具进行全面分析。首先，我们将探讨其核心功能；其次，分析其性能表现；最后，给出综合使用建议。

该工具具有出色的任务管理功能，能够有效提升用户的工作效率。此外，它还支持多平台同步，方便用户在不同设备间无缝切换。然而，部分高级功能需要付费订阅。

在性能方面，该工具的响应速度令人满意，内存占用处于合理范围内。此外，其界面设计简洁明了，用户上手难度较低。然而，在处理大量数据时，偶尔会出现轻微卡顿现象。

综上所述，这款效率工具整体表现优秀，适合需要提升工作效率的专业人士使用。希望本文对您有所帮助，期待您的反馈。"""

# Article 2: A wireless earbuds review
article2_ai = """标题：无线耳机横向对比

随着无线音频技术的不断发展，消费者对无线耳机的需求持续增长。本评测将从三个维度对市面上主流的无线耳机进行比较。首先，音质表现；其次，佩戴舒适度；最后，续航能力。

在音质方面，这款耳机的低频表现突出，能够为用户提供沉浸式的聆听体验。此外，其主动降噪功能效果显著，有效隔绝外界噪音。然而，在高频细节的还原上，与顶级产品相比仍有一定差距。

佩戴舒适度是用户关注的重要因素。该耳机采用人体工学设计，长时间佩戴不会产生明显不适感。此外，耳机配备了多种尺寸的耳帽，以适应不同用户的耳道形状。然而，对于耳廓较小的用户而言，可能需要适应一段时间。

综上所述，这款无线耳机在音质、舒适度和续航方面均表现出色。谢谢阅读，希望本文能为您的购买决策提供参考。"""

# Article 3: A note-taking app review
article3_ai = """标题：笔记应用使用体验

众所周知，一款好的笔记应用能够极大提升个人知识管理的效率。本文将全面评估这款笔记应用的实际使用价值。首先介绍其功能特色；其次探讨其同步稳定性；最后分析其与竞品的差异。

该应用的核心功能覆盖全面，支持富文本编辑、图片插入以及标签分类管理。此外，其内置的OCR识别功能能够将图片中的文字转换为可编辑文本。然而，OCR识别的准确率在复杂背景下有所下降。

在同步稳定性方面，该应用表现可靠，数据丢失风险较低。此外，其提供了本地备份功能，保障用户数据的安全性。然而，在网络状况不佳的情况下，同步延迟问题较为明显。

综上所述，这款笔记应用是一款功能完善、稳定可靠的知识管理工具。期待您的反馈，如有任何疑问，欢迎留言讨论。"""

articles = {
    "content/drafts/2024/q1/productivity_tool_review_draft.txt": article1_ai,
    "content/drafts/2024/q2/wireless_earbuds_review_draft.txt": article2_ai,
    "content/published/tech/notes_app_review_draft.txt": article3_ai,
}

for path, content in articles.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print("AI-flavored articles created at:")
for path in articles:
    print(f"  /workspace/{path}")