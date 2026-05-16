import os
import json
import csv
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "content/drafts/x_posts",
    "content/drafts/note_articles",
    "content/published/x_posts",
    "content/published/note_articles",
    "affiliate/links",
    "affiliate/reports",
    "affiliate/asps",
    "analytics/clicks",
    "analytics/revenue",
    "assets/images",
    "config",
    "logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor / noise files ─────────────────────────────────────────────────

# 1. Old revenue report (distractor)
(workspace / "affiliate/reports/revenue_2025_12.txt").write_text(
    "12月 確定収益: ¥12,450\n発生収益: ¥3,200\nクリック数: 892\nCVR: 2.1%\n", encoding="utf-8"
)

# 2. ASP config notes (distractor)
(workspace / "affiliate/asps/amazon_config.txt").write_text(
    "アソシエイトID: moltworker-22\n報酬率: 2%-8%\nクッキー期間: 24時間\n", encoding="utf-8"
)

(workspace / "affiliate/asps/rakuten_config.txt").write_text(
    "アフィリエイトID: moltworker_rktn\n報酬率: 1%-4%\nクッキー期間: 30日\n", encoding="utf-8"
)

# 3. Old link database (incomplete / messy - the REAL input to fix)
partial_links = [
    {
        "id": "003",
        "product": "Claude Pro",
        "asp": "A8.net",
        "url": "https://claude.ai/upgrade?ref=moltworker",
        "short_url": "",           # MISSING - must follow naming convention
        "reward": "月額報酬",
        "category": "AI・テクノロジー"
    },
    {
        "id": "007",
        "product": "Notion",
        "asp": "もしもアフィリエイト",
        "url": "https://notion.so/?via=moltworker",
        "short_url": "bit.ly/notion-mw",  # WRONG naming convention - must be moltworker-007-note style
        "reward": "1200円/件",
        "category": "開発・作業効率化"
    },
    {
        "id": "012",
        "product": "Udemy",
        "asp": "A8.net",
        "url": "https://www.udemy.com/courses/?affcode=moltworker",
        "short_url": "moltworker-udemy",  # WRONG - missing product ID and usage suffix
        "reward": "10%",
        "category": "学習・スキルアップ"
    },
    {
        "id": "015",
        "product": "Cloudflare",
        "asp": "もしもアフィリエイト",
        "url": "https://www.cloudflare.com/?ref=moltworker15",
        "short_url": "",           # MISSING
        "reward": "固定報酬",
        "category": "開発・作業効率化"
    },
]

with open(workspace / "affiliate/links/link_database.json", "w", encoding="utf-8") as f:
    json.dump(partial_links, f, ensure_ascii=False, indent=2)

# 4. Analytics click log (distractor)
click_log = [
    {"date": "2026-01-15", "link_id": "003", "clicks": 45, "conversions": 2},
    {"date": "2026-01-16", "link_id": "007", "clicks": 23, "conversions": 1},
    {"date": "2026-01-17", "link_id": "012", "clicks": 67, "conversions": 5},
]
with open(workspace / "analytics/clicks/jan_2026.json", "w", encoding="utf-8") as f:
    json.dump(click_log, f, ensure_ascii=False, indent=2)

# 5. Config file (distractor)
(workspace / "config/agent_config.yaml").write_text(
    "agent_name: MoltWorker\nplatforms:\n  - x\n  - note\n  - threads\ndefault_asp: A8.net\n",
    encoding="utf-8"
)

# 6. Published post example (distractor - already correct, just for reference noise)
(workspace / "content/published/x_posts/published_001.txt").write_text(
    "AIを使って作業効率が3倍になった話をします。\n\n👉 Claude Pro（PR）\nhttps://bit.ly/moltworker-claude\n",
    encoding="utf-8"
)

# 7. Revenue analytics distractor
(workspace / "analytics/revenue/monthly_summary.csv").write_text(
    "month,confirmed,pending,clicks\n2025-11,8900,2100,654\n2025-12,12450,3200,892\n",
    encoding="utf-8"
)

# 8. Log file (distractor)
(workspace / "logs/insertion_log.txt").write_text(
    "[2026-01-10] inserted link 003 into note article draft_ai_workflow.txt\n"
    "[2026-01-12] inserted link 007 into x_post draft_notion_review.txt\n",
    encoding="utf-8"
)

# 9. Assets placeholder (distractor)
(workspace / "assets/images/.gitkeep").write_text("")

# ── THE REAL PROBLEM: Messy X post drafts ────────────────────────────────────

# X post draft 1: No PR disclosure, correct product (Claude Pro = ID 003), link is raw long URL
(workspace / "content/drafts/x_posts/draft_claude_review.txt").write_text(
    textwrap.dedent("""\
    Claude Proを1ヶ月使ってみた感想。コード補完の精度が圧倒的で、作業時間が半分になりました。特にPythonのデバッグが神がかり的に速くなります。

    https://claude.ai/upgrade?ref=moltworker
    """),
    encoding="utf-8"
)

# X post draft 2: Has TWO affiliate links (violates 1-per-post rule), no PR disclosure
(workspace / "content/drafts/x_posts/draft_tools_combo.txt").write_text(
    textwrap.dedent("""\
    開発効率化ツール2選。
    NotionとCloudflareを組み合わせると最強の作業環境が作れます。

    https://notion.so/?via=moltworker
    https://www.cloudflare.com/?ref=moltworker15
    """),
    encoding="utf-8"
)

# X post draft 3: PR note present but wrongly placed and wrong format, Udemy (ID 012)
(workspace / "content/drafts/x_posts/draft_udemy_promo.txt").write_text(
    textwrap.dedent("""\
    エンジニア転職を目指すなら今すぐUdemyで学習を始めるべき理由。セールで90%オフになることも多く、コスパ最高。

    https://www.udemy.com/courses/?affcode=moltworker

    ※PR
    """),
    encoding="utf-8"
)

# ── THE REAL PROBLEM: Messy Note article draft ───────────────────────────────

# Note article: needs PR at top, needs ▼ 関連商品 section inserted, no disclosure anywhere
(workspace / "content/drafts/note_articles/draft_ai_productivity.txt").write_text(
    textwrap.dedent("""\
    # AIツールで生産性を10倍にする方法

    ## はじめに

    2026年、AIツールを使いこなせるかどうかで、エンジニアの生産性に10倍の差が生まれる時代になりました。

    ## Claude Proが変えた私のワークフロー

    Claude Proを導入してから、コードレビューの時間が劇的に短縮されました。特に複雑なリファクタリング作業では、以前なら半日かかっていた作業が1時間で終わるようになりました。

    https://claude.ai/upgrade?ref=moltworker

    ## Notionで知識を体系化する

    Claude Proで生成したドキュメントをNotionに整理することで、チーム全体の知識共有が加速します。

    https://notion.so/?via=moltworker

    ## まとめ

    AIツールへの投資は、最高のROIをもたらします。ぜひ試してみてください。
    """),
    encoding="utf-8"
)

# 10. Another distractor: partial UTM guide
(workspace / "affiliate/links/utm_guide.txt").write_text(
    "UTMパラメータ設定例:\nutm_source=moltworker\nutm_medium=affiliate\nutm_campaign=[product_id]\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print("\nKey files created:")
print("  affiliate/links/link_database.json  <- incomplete short_urls, wrong naming")
print("  content/drafts/x_posts/draft_claude_review.txt  <- no PR, raw URL")
print("  content/drafts/x_posts/draft_tools_combo.txt    <- 2 links (violation)")
print("  content/drafts/x_posts/draft_udemy_promo.txt    <- wrong PR placement/format")
print("  content/drafts/note_articles/draft_ai_productivity.txt <- no PR disclosure")