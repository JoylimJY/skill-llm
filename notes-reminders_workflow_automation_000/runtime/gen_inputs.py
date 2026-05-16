import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta
import pytz

random.seed(42)

workspace = Path("/workspace")

# ── directory structure with distractors ──────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "logs",
    "config",
    "archive/2024/Q1",
    "archive/2024/Q2",
    "tmp",
    "docs",
    "reports",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "config/app.yaml": "server:\n  port: 8080\n  debug: false\n",
    "config/db.json": json.dumps({"host": "localhost", "port": 5432, "db": "prod"}),
    "logs/app.log": "2026-01-10 INFO Server started\n2026-01-10 WARN Low memory\n",
    "data/raw/users.csv": "id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n",
    "data/processed/summary.txt": "Total users: 2\nActive: 1\n",
    "archive/2024/Q1/report.md": "# Q1 Report\nRevenue: 120k\n",
    "archive/2024/Q2/report.md": "# Q2 Report\nRevenue: 145k\n",
    "tmp/scratch.txt": "temp data ignore\n",
    "docs/onboarding.txt": "Welcome to the team!\nPlease read the handbook.\n",
    "reports/weekly.txt": "Week 3 summary: all green\n",
}
for rel, content in distractor_files.items():
    (workspace / rel).write_text(content, encoding="utf-8")

# ── SKILL.md (already in workspace per problem statement) ────────────────────
skill_md = """\
---
name: notes-reminders
description: Manage quick notes and time-based reminders.
metadata:
  {
    "openclaw":
      {
        "emoji": "📌",
        "requires": { "scripts": ["scripts/notes.js", "scripts/reminders.js"] },
      },
  }
---

# notes-reminders

メモとリマインダーの管理。

## メモ

```bash
# メモ追加
node scripts/notes.js add --title="アイデア" --content="新機能のアイデア..."

# メモ検索
node scripts/notes.js search --query="アイデア" --limit=10
```

## リマインダー

```bash
# リマインダー追加
node scripts/reminders.js add \\
  --message="ミーティング準備" \\
  --remind_at="2026-02-25T10:00:00+09:00" \\
  --channel=C0AHBLQ0P32

# 未発火リマインダー一覧
node scripts/reminders.js list

# 発火チェック（期限到来のリマインダーを取得）
node scripts/reminders.js check-and-fire
```

## リマインダー発火ワークフロー

`check-and-fire` の結果に fired リマインダーがあれば、該当チャネルにメッセージを送信:
`リマインダー: {message}`

## 時刻の扱い

ユーザーが「明日10時にリマインドして」等と言った場合:
- Asia/Tokyo タイムゾーンで解釈
- ISO 8601 形式に変換して --remind_at に渡す
"""
(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── The messy meeting notes file ──────────────────────────────────────────────
# We fix a reference "today" so the agent can reason deterministically.
# The file itself contains the date so agent knows the context.
# Two reminders: one already in the past (should fire), one in the future (should not).
# "Today" in the file is 2026-01-15 (Thursday). The agent must interpret times in Asia/Tokyo.

meeting_notes = """\
=== チームシンク 議事録 ===
日時: 2026年1月15日（木）午後2時
参加者: 田中、鈴木、山田、Priya

■ 議題1: 新機能 API 設計
- REST か GraphQL かで意見が割れた
- Priya が GraphQL のメリットをまとめてくれる予定
- 決定: 来週のスプリントで PoC を実施する
- 関連キーワード: API設計, GraphQL, REST比較, マイクロサービス

■ 議題2: パフォーマンス改善
- DBクエリが遅い問題が本番で発生中
- 田中が N+1 クエリの調査をする
- インデックス最適化の提案あり
- 関連キーワード: パフォーマンス, DBチューニング, N+1問題

■ 議題3: リリーススケジュール
- v2.3.0 は 2026年1月20日リリース予定
- QA チェックは 1月17日（土）に実施
- デプロイ担当: 鈴木

■ アクション & リマインダー:
[REMINDER] 田中: N+1クエリ調査レポート提出 → 2026-01-15T09:00:00+09:00 / channel=C0AHBLQ0P32
[REMINDER] 鈴木: v2.3.0 デプロイ作業開始確認 → 2026-01-20T09:00:00+09:00 / channel=C1DEPLOYOP9
[REMINDER] Priya: GraphQLメリットまとめ送付 → 2026-01-16T15:00:00+09:00 / channel=C2GRAPHQLCH

■ 備考:
次回ミーティングは来週木曜日 午後2時。
ランチはピザの予定。
"""

(workspace / "data/raw/meeting_notes_2026-01-15.txt").write_text(
    meeting_notes, encoding="utf-8"
)

# ── data store files that the mock scripts will use ───────────────────────────
# Initialize empty stores
(workspace / "data/notes_store.json").write_text("[]", encoding="utf-8")
(workspace / "data/reminders_store.json").write_text("[]", encoding="utf-8")

print("Workspace generated successfully.")
print("Meeting notes written to: data/raw/meeting_notes_2026-01-15.txt")