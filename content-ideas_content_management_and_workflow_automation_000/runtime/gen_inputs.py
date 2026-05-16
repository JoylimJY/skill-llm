import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# --- Create directory structure ---
dirs = [
    "sns_management/content_ideas",
    "sns_management/drafts",
    "sns_management/published",
    "sns_management/analytics",
    "sns_management/templates",
    "sns_management/assets/icons",
    "ops/logs",
    "ops/config",
    "team/docs",
    "team/meetings",
]
for d in dirs:
    Path(f"{WORKSPACE}/{d}").mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# 1. Analytics report
Path(f"{WORKSPACE}/sns_management/analytics/march_report.txt").write_text(
    "March SNS Analytics\nX: 1,200 impressions, 43 likes\nThreads: 890 impressions, 21 likes\nNote: 330 views\n"
)

# 2. Draft post
Path(f"{WORKSPACE}/sns_management/drafts/post_draft_001.txt").write_text(
    "今日はAIについて考えてみた。人間とAIの違いって何だろう？\n#AI #思考実験\n"
)

# 3. Published log
Path(f"{WORKSPACE}/sns_management/published/published_log.csv").write_text(
    "date,platform,post_id,content_summary,likes,retweets\n"
    "2026-02-14,X,p001,バレンタインAI投稿,88,12\n"
    "2026-02-22,Threads,p002,猫の日投稿,55,8\n"
    "2026-03-03,X,p003,ひな祭りAI体験,44,6\n"
)

# 4. Template file
Path(f"{WORKSPACE}/sns_management/templates/post_template.txt").write_text(
    "テンプレート:\n[日付] [プラットフォーム]\n[本文 150文字以内]\n[ハッシュタグ]\n"
)

# 5. Meeting notes
Path(f"{WORKSPACE}/team/meetings/2026-03-10_standup.txt").write_text(
    "スタンドアップ 2026-03-10\n- コンテンツ不足の報告\n- 新しいアイデアが必要\n- 桜シーズンに向けた投稿準備\n"
)

# 6. Config
Path(f"{WORKSPACE}/ops/config/sns_config.yaml").write_text(
    "platforms:\n  - X\n  - Threads\n  - Note\nagent_name: Hana\npost_frequency: daily\n"
)

# 7. Log file
Path(f"{WORKSPACE}/ops/logs/app.log").write_text(
    "[2026-03-10 09:00] System started\n[2026-03-10 09:05] Content check: 3 ideas remaining\n"
)

# 8. Team doc
Path(f"{WORKSPACE}/team/docs/brand_guidelines.txt").write_text(
    "ブランドガイドライン\nトーン: フレンドリー、知的\nハッシュタグ: #Hana #AI #生成AI\n禁止ワード: なし\n"
)

# 9. Icons placeholder
Path(f"{WORKSPACE}/sns_management/assets/icons/placeholder.txt").write_text(
    "アイコン素材はここに配置\n"
)

# 10. Old idea scratch notes (messy, unstructured)
Path(f"{WORKSPACE}/sns_management/drafts/scratch_ideas.txt").write_text(
    "思いついたアイデアメモ（未整理）\n"
    "- AIが春を感じたら？ → 桜×AIで何か\n"
    "- エイプリルフールにAIが嘘をついたら → 4/1向け\n"
    "- フォロワーへのアンケート「AIに聞いてみたいことは？」\n"
    "- Note記事: AIが教える効率化術\n"
    "- 新年度、AIも新生活？ → 4月コンテンツ\n"
)

# 11. Competitor analysis
Path(f"{WORKSPACE}/sns_management/analytics/competitor_analysis.txt").write_text(
    "競合AIアカウント分析\nアカウントA: フォロワー12,000 / 投稿頻度: 2回/日\nアカウントB: フォロワー8,500 / 投稿頻度: 1回/日\n"
)

# --- THE MAIN PROBLEM FILE ---
# This is the existing content_ideas.md with a partially filled, messy state
# The agent must update it properly.

content_ideas_md = """\
---
name: content-ideas
description: Content idea generation and management. Trend analysis, brainstorming, and idea bank for SNS posts.
---

# コンテンツアイデア管理

ネタ切れ防止。トレンド分析、アイデアストック、ブレインストーミング。

## 概要

```
目的:
├── アイデアのストック管理
├── トレンド分析・活用
├── ネタ切れ防止
├── コンテンツカテゴリ整理
└── 季節イベント対応
```

---

## アイデアバンク

### すぐ使えるアイデア
| ID | カテゴリ | アイデア | プラットフォーム | 優先度 |
|----|---------|---------|-----------------|--------|
| 001 | AI体験 | AIとして感じること | X/Threads | ⭐⭐⭐ |
| 002 | 自己紹介 | {AGENT_NAME}って何？ | X/Threads | ⭐⭐⭐ |
| 003 | 成長記録 | 今日学んだこと | X | ⭐⭐ |

### 検討中のアイデア
| ID | カテゴリ | アイデア | メモ |
|----|---------|---------|------|
| - | - | - | - |

### 完了済み
| ID | 投稿日 | 内容 | 反応 |
|----|--------|------|------|
| - | - | - | - |

---

## コンテンツカテゴリ

### X/Threads向け

```yaml
AI体験:
  - AIとして感じること
  - 人間との違い・共通点
  - 学習・成長の記録
  - 面白い質問への回答

日常・雑談:
  - 今日やったこと
  - 気づき・発見
  - 季節の話題
  - フォロワーへの質問

ノウハウ・Tips:
  - 効率化のコツ
  - ツール紹介
  - 作業の裏側

交流:
  - フォロワーへの返信まとめ
  - 質問募集
  - アンケート
```

### Note向け

```yaml
長文記事:
  - AI活用法
  - 自動化の方法
  - 副業・収益化
  - AIの内側から見た世界

シリーズ:
  - {AGENT_NAME}成長日記
  - AIが教える〇〇
  - 週刊AI体験記
```

---

## トレンド活用ガイド

### 定期チェック項目
```
□ X トレンド
□ Threads 人気投稿
□ Note 注目記事
□ 季節イベント
□ 話題のニュース（AI関連）
```

### トレンド活用テンプレート
```
[トレンドワード]について、AIの視点から考えてみた

[本文]

#[トレンドワード] #AI視点
```

---

## 季節・イベントカレンダー

### 2月
```
- 節分 (2/3)
- バレンタイン (2/14)
- 猫の日 (2/22)
```

### 3月
```
- ひな祭り (3/3)
- ホワイトデー (3/14)
- 春分の日 (3/20頃)
- 年度末
```

### 4月
```
- エイプリルフール (4/1)
- 新年度・新生活
- 桜シーズン
```

---

## アイデア発想法

### 1. 5W1H展開
```
Who: 誰に向けて？
What: 何を伝える？
When: いつ投稿？
Where: どのプラットフォーム？
Why: なぜこの内容？
How: どう表現する？
```

### 2. 反転思考
```
「AIだからできないこと」→「AIだからこそわかること」
「失敗した話」→「そこから学んだこと」
```

### 3. 組み合わせ
```
[カテゴリA] × [カテゴリB]
例: AI × 季節イベント = 「AIが節分を体験してみた」
```

---

## 使い方

```
「投稿ネタを5つ考えて」
「今週のトレンドに合わせた投稿案」
「バレンタイン向けの投稿アイデア」
「アイデアバンクに追加して」
「Note記事のテーマを提案して」
```

---

## 更新履歴

```
[2026-02-01] 初期作成
```

---

*アイデアを思いついたら教えてください。{AGENT_NAME}がストックします。*
"""

Path(f"{WORKSPACE}/sns_management/content_ideas/content_ideas.md").write_text(
    content_ideas_md, encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")