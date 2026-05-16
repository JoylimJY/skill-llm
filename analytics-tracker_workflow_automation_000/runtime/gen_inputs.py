import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "analytics/raw_data",
    "analytics/processed",
    "analytics/archive/2025",
    "analytics/archive/2026/q1",
    "reports/weekly",
    "reports/monthly",
    "config",
    "scripts",
    "assets/images",
    "assets/templates",
    "notes/drafts",
    "notes/published",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
# 1. Old archived report (wrong format, old data)
(workspace / "analytics/archive/2025/week50_report.txt").write_text(
    "Week 50 2025 Report\nX followers: 120\nThreads: 45\n(old format, do not use)"
)

# 2. A broken JSON file
(workspace / "analytics/archive/2026/q1/broken_metrics.json").write_text(
    '{"x": {"followers": , "likes": 8}, "threads": {}}'
)

# 3. A config file with misleading thresholds
(workspace / "config/old_kpi_thresholds.yaml").write_text(
    "# DEPRECATED - DO NOT USE\nX:\n  followers_target: 50\n  avg_likes: 5\nThreads:\n  followers_target: 25\n"
)

# 4. A sample template (wrong/old format)
(workspace / "assets/templates/report_template_v1.md").write_text(
    "# Weekly SNS Report\n## Platform Summary\n- X: N/A\n- Threads: N/A\n- Note: N/A\n(v1 template - outdated)"
)

# 5. Random script files
(workspace / "scripts/fetch_data.sh").write_text(
    "#!/bin/bash\n# Placeholder script - not functional\necho 'Fetching data...'"
)
(workspace / "scripts/process.py").write_text(
    "# Old processing script\n# TODO: update for 2026\nprint('processing...')"
)

# 6. Notes drafts
(workspace / "notes/drafts/post_ideas.txt").write_text(
    "AI tips post idea\nMorning routine thread\nQ&A session on Threads"
)

# 7. Another distractor
(workspace / "notes/published/article_20260115.txt").write_text(
    "Title: How I use AI daily\nPV: 230\nSuki: 45\nPublished: 2026-01-15"
)

# 8. Platform username info (distractor - slightly off)
(workspace / "config/platform_usernames.txt").write_text(
    "X: @Yuki_Sakura_Official\nThreads: @yukisakura\nNote: yukisakura_note\n(tentative usernames - not confirmed)"
)

# 9. Random metrics dump (unstructured)
(workspace / "analytics/raw_data/misc_notes.txt").write_text(
    "Feb 3 - posted about AI tools, got good response\nFeb 5 - threads post flopped\nNeed to check best time to post"
)

# 10. Archive placeholder
(workspace / "analytics/archive/2026/q1/placeholder.txt").write_text(
    "Archive folder for Q1 2026 data"
)

# 11. Monthly report stub (wrong structure)
(workspace / "reports/monthly/jan2026_stub.txt").write_text(
    "January 2026 summary stub - incomplete"
)

# --- THE REAL INPUT DATA THE AGENT MUST PROCESS ---

# Follower history raw CSV (X platform)
x_followers_csv = """date,followers,memo
2026-02-01,312,開始
2026-02-08,341,AIツール投稿がバズった
2026-02-15,378,コンスタントな投稿継続
2026-02-22,405,フォロワーキャンペーン実施
"""
(workspace / "analytics/raw_data/x_followers_weekly.csv").write_text(x_followers_csv)

# Follower history raw CSV (Threads platform)
threads_followers_csv = """date,followers,memo
2026-02-01,87,開始
2026-02-08,96,初週
2026-02-15,108,交流強化
2026-02-22,121,コラボ効果
"""
(workspace / "analytics/raw_data/threads_followers_weekly.csv").write_text(threads_followers_csv)

# Follower history raw CSV (Note platform)
note_followers_csv = """date,followers,memo
2026-02-01,34,開始
2026-02-08,38,記事公開
2026-02-15,41,シェア増加
2026-02-22,47,人気記事効果
"""
(workspace / "analytics/raw_data/note_followers_weekly.csv").write_text(note_followers_csv)

# Weekly engagement data (week of 2026-02-16)
# X posts that week
x_posts = [
    {"id": "x001", "content": "AIを使って業務効率化した話", "impressions": 4200, "likes": 87, "reposts": 23, "replies": 15},
    {"id": "x002", "content": "毎朝のルーティンをAIが変えた", "impressions": 2100, "likes": 34, "reposts": 8, "replies": 6},
    {"id": "x003", "content": "おすすめAIツール5選", "impressions": 6800, "likes": 142, "reposts": 56, "replies": 29},
    {"id": "x004", "content": "今週の学び：失敗から得たこと", "impressions": 1800, "likes": 21, "reposts": 4, "replies": 11},
    {"id": "x005", "content": "質問：皆さんどんなAIツール使ってますか？", "impressions": 3300, "likes": 65, "reposts": 12, "replies": 48},
]

# Threads posts that week
threads_posts = [
    {"id": "t001", "content": "AIツールで時間短縮できた体験談", "likes": 32, "reposts": 7, "comments": 9},
    {"id": "t002", "content": "Noteに新記事書きました！", "likes": 14, "reposts": 3, "comments": 2},
    {"id": "t003", "content": "朝活始めて1ヶ月の変化", "likes": 28, "reposts": 5, "comments": 6},
]

# Note articles that week
note_articles = [
    {"id": "n001", "content": "ChatGPTを使った議事録自動化の全手順", "pv": 890, "suki": 67, "comments": 12},
    {"id": "n002", "content": "AI初心者が最初にやるべきこと", "pv": 1240, "suki": 103, "comments": 18},
]

engagement_data = {
    "week_of": "2026-02-16",
    "x": x_posts,
    "threads": threads_posts,
    "note": note_articles
}

(workspace / "analytics/raw_data/week_20260216_engagement.json").write_text(
    json.dumps(engagement_data, ensure_ascii=False, indent=2)
)

# Also write a separate processed dir placeholder
(workspace / "analytics/processed/.gitkeep").write_text("")

# A misleading "report" in the reports folder that is not properly formatted
(workspace / "reports/weekly/draft_week8.txt").write_text(
    "Draft notes for week 8:\n- X had good engagement\n- Note article did well\n- Need formal report\n(raw notes only)"
)

print("Workspace setup complete.")
print(f"Files created in {workspace}")