import os
import json
import random

random.seed(42)

# Create deep directory structure with distractors
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "config",
    "logs",
    "output",
    "tmp",
    "docs/internal",
    "docs/api",
    "tests/unit",
    "tests/integration",
    ".cache/trends",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "config/app.yaml": "env: production\nlog_level: info\nmax_retries: 3\n",
    "config/slack_config.json": json.dumps({"channel": "#ai-trends", "username": "TrendBot", "icon_emoji": ":robot_face:"}),
    "logs/2024-01-10.log": "[INFO] Search completed. 142 tweets fetched.\n[INFO] Deduplication pass: 18 removed.\n[WARN] Rate limit approaching.\n",
    "logs/2024-01-11.log": "[INFO] Posted 6 tweets to Slack.\n[INFO] Marked 6 URLs as posted.\n",
    "data/archive/trends_2024_01_08.json": json.dumps([{"url": "https://x.com/user1/status/111", "text": "archived tweet"}]),
    "data/archive/trends_2024_01_09.json": json.dumps([{"url": "https://x.com/user2/status/222", "text": "another archived tweet"}]),
    "docs/internal/curation_notes.md": "# Notes\n- Prefer practitioners over hype accounts\n- Balance language coverage\n",
    "docs/api/xurl_reference.txt": "xurl: CLI for X (Twitter) API access\nUsage: xurl search --query '...' --lang ja --min-likes 100\n",
    "tests/unit/test_format.js": "// Unit tests for format-blocks\ndescribe('formatBlocks', () => { it('should format correctly', () => {}); });\n",
    "tests/integration/test_pipeline.js": "// Integration test placeholder\n",
    "tmp/search_cache.tmp": "cache_v1|2024-01-11|stale\n",
    ".cache/trends/last_run.json": json.dumps({"timestamp": "2024-01-11T09:00:00Z", "count": 6}),
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# THE MAIN PROBLEM INPUT: raw messy tweet search results
# These simulate output from `node scripts/ai_trends.js search`
# Contains: 
# - hype/clickbait accounts (must be excluded)
# - tweets below like threshold (should be excluded by the script, but included here as noise)
# - a mix of JP and EN tweets
# - already-posted URLs (must be caught by check-recent)
# - valid practitioner tweets to select from
raw_tweets = [
    # --- ENGLISH tweets (technically valid, must select 3-5) ---
    {
        "id": "1745000000001",
        "url": "https://x.com/karpathy/status/1745000000001",
        "text": "Just shipped tokenization changes in llm.c - now uses tiktoken BPE instead of custom code. ~40% faster on encoding and the vocab coverage is much better for multilingual text. The diff is surprisingly small.",
        "author": "karpathy",
        "author_name": "Andrej Karpathy",
        "likes": 8420,
        "lang": "en",
        "hype_flag": False,
    },
    {
        "id": "1745000000002",
        "url": "https://x.com/simonw/status/1745000000002",
        "text": "New llm plugin: llm-gemini now supports the Files API - you can pass PDFs, images, audio directly to Gemini models. Tested with a 300-page technical manual, works well. pip install llm-gemini",
        "author": "simonw",
        "author_name": "Simon Willison",
        "likes": 1832,
        "lang": "en",
        "hype_flag": False,
    },
    {
        "id": "1745000000003",
        "url": "https://x.com/fchollet/status/1745000000003",
        "text": "People keep confusing 'reasoning' with 'pattern matching over reasoning traces in training data'. These are different things with very different generalization properties. The conflation is causing a lot of confusion in capability assessments.",
        "author": "fchollet",
        "author_name": "François Chollet",
        "likes": 3211,
        "lang": "en",
        "hype_flag": False,
    },
    {
        "id": "1745000000004",
        "url": "https://x.com/skirano/status/1745000000004",  # ALREADY POSTED - must be excluded
        "text": "Using structured outputs + tool calling together unlocks some really powerful patterns. Here's a pattern I've been using for reliable multi-step extraction pipelines.",
        "author": "skirano",
        "author_name": "Pietro Schirano",
        "likes": 921,
        "lang": "en",
        "hype_flag": False,
    },
    {
        "id": "1745000000005",
        "url": "https://x.com/aiHYPE_daily/status/1745000000005",  # HYPE ACCOUNT - must exclude
        "text": "🚨🚨 BREAKING: NEW AI MODEL JUST DROPPED AND IT'S GOING TO CHANGE EVERYTHING FOREVER. AGI IS HERE. YOU NEED TO SEE THIS NOW!!!",
        "author": "aiHYPE_daily",
        "author_name": "AI Hype Daily",
        "likes": 15200,
        "lang": "en",
        "hype_flag": True,
    },
    {
        "id": "1745000000006",
        "url": "https://x.com/ylecun/status/1745000000006",
        "text": "New paper from our team: Energy-based models for compositional generalization. We show that EBMs can compose concepts at test time without retraining. Code + models released.",
        "author": "ylecun",
        "author_name": "Yann LeCun",
        "likes": 2100,
        "lang": "en",
        "hype_flag": False,
    },
    # BELOW THRESHOLD (likes < 500 for EN) - should not be selected
    {
        "id": "1745000000007",
        "url": "https://x.com/randomdev/status/1745000000007",
        "text": "Using RAG with pgvector in production for 3 months. Biggest lesson: chunking strategy matters 10x more than embedding model choice.",
        "author": "randomdev",
        "author_name": "Random Dev",
        "likes": 287,
        "lang": "en",
        "hype_flag": False,
    },
    # --- JAPANESE tweets (must select 3-5) ---
    {
        "id": "1745000000010",
        "url": "https://x.com/yamada_ml/status/1745000000010",
        "text": "Claude 3.5 SonnetでRAGシステムを本番運用して3ヶ月。ハルシネーション率が従来比で62%減少した。キーはrerankerの設計とチャンク戦略の組み合わせ。詳細をZennに書きました。",
        "author": "yamada_ml",
        "author_name": "山田 健一",
        "likes": 1205,
        "lang": "ja",
        "hype_flag": False,
    },
    {
        "id": "1745000000011",
        "url": "https://x.com/tanaka_aidev/status/1745000000011",
        "text": "LangGraphでエージェント設計する際、ノード間のstate管理を間違えると無限ループにはまる。TypedDictで型を厳密に定義して、条件分岐に必ずフォールバックを入れるのが必須。",
        "author": "tanaka_aidev",
        "author_name": "田中 AI開発",
        "likes": 892,
        "lang": "ja",
        "hype_flag": False,
    },
    {
        "id": "1745000000012",
        "url": "https://x.com/hype_jp_ai/status/1745000000012",  # HYPE - must exclude
        "text": "【速報】ついにAGIが完成！！！人類の仕事がなくなる！！全員今すぐチェックして！！！衝撃的すぎる！！",
        "author": "hype_jp_ai",
        "author_name": "AI速報まとめ",
        "likes": 4300,
        "lang": "ja",
        "hype_flag": True,
    },
    {
        "id": "1745000000013",
        "url": "https://x.com/suzuki_nlp/status/1745000000013",
        "text": "日本語LLM評価ベンチマークJMMLUの最新版が公開。GPT-4oが依然トップだが、Qwen2.5-72Bが僅差で追随。特に法律・医療ドメインでの差が縮まっている。",
        "author": "suzuki_nlp",
        "author_name": "鈴木 NLP研究",
        "likes": 677,
        "lang": "ja",
        "hype_flag": False,
    },
    {
        "id": "1745000000014",
        "url": "https://x.com/ito_prompteng/status/1745000000014",
        "text": "プロンプトエンジニアリングで見落とされがちなのが「出力フォーマットの強制」。JSONスキーマを直接プロンプトに埋め込むとパース失敗率が1/10になる実績あり。",
        "author": "ito_prompteng",
        "author_name": "伊藤 プロンプト研究",
        "likes": 543,
        "lang": "ja",
        "hype_flag": False,
    },
    # BELOW THRESHOLD (likes < 100 for JA) - should not be selected
    {
        "id": "1745000000015",
        "url": "https://x.com/newbie_ai/status/1745000000015",
        "text": "AIすごいですね〜",
        "author": "newbie_ai",
        "author_name": "AI初心者",
        "likes": 45,
        "lang": "ja",
        "hype_flag": False,
    },
    {
        "id": "1745000000016",
        "url": "https://x.com/nakamura_eng/status/1745000000016",
        "text": "Fine-tuningよりもRLHFよりも、まずシステムプロンプトの設計に時間をかけるべき。95%のユースケースはそれで解決する。残り5%のためにfine-tuningを検討する順番。",
        "author": "nakamura_eng",
        "author_name": "中村 エンジニア",
        "likes": 1120,
        "lang": "ja",
        "hype_flag": False,
    },
]

with open("data/raw/tweets_search_result.json", "w", encoding="utf-8") as f:
    json.dump(raw_tweets, f, ensure_ascii=False, indent=2)

# Recently posted URLs (for deduplication check)
recently_posted = [
    "https://x.com/skirano/status/1745000000004",
    "https://x.com/old_user/status/1744000000001",
    "https://x.com/old_user/status/1744000000002",
]

with open("data/processed/recently_posted.json", "w") as f:
    json.dump({"posted_urls": recently_posted, "last_updated": "2024-01-11T08:00:00Z"}, f, indent=2)

# Mock scripts/ai_trends.js - a stub that the real script would be
# (agent must use the data files, not rely on the script doing the work)
os.makedirs("scripts", exist_ok=True)
ai_trends_js = r"""#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);
const command = args[0];

const RAW_TWEETS_PATH = path.join(__dirname, '../data/raw/tweets_search_result.json');
const RECENT_PATH = path.join(__dirname, '../data/processed/recently_posted.json');
const MARK_PATH = path.join(__dirname, '../data/processed/recently_posted.json');

if (command === 'search') {
  const tweets = JSON.parse(fs.readFileSync(RAW_TWEETS_PATH, 'utf-8'));
  console.log(JSON.stringify(tweets, null, 2));
  process.exit(0);
}

if (command === 'check-recent') {
  const data = JSON.parse(fs.readFileSync(RECENT_PATH, 'utf-8'));
  console.log(JSON.stringify(data.posted_urls, null, 2));
  process.exit(0);
}

if (command === 'format-blocks') {
  // Parse --tweets and --summary args
  let tweets = null;
  let summary = '';
  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--tweets' && args[i+1]) { tweets = JSON.parse(args[i+1]); i++; }
    else if (args[i].startsWith('--tweets=')) { tweets = JSON.parse(args[i].slice('--tweets='.length)); }
    else if (args[i] === '--summary' && args[i+1]) { summary = args[i+1]; i++; }
    else if (args[i].startsWith('--summary=')) { summary = args[i].slice('--summary='.length); }
  }
  const blocks = {
    summary: summary,
    tweet_count: tweets ? tweets.length : 0,
    blocks_formatted: true,
    tweets: tweets
  };
  console.log(JSON.stringify(blocks, null, 2));
  process.exit(0);
}

if (command === 'mark-posted') {
  let urls = [];
  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--urls' && args[i+1]) { urls = JSON.parse(args[i+1]); i++; }
    else if (args[i].startsWith('--urls=')) { urls = JSON.parse(args[i].slice('--urls='.length)); }
  }
  const data = JSON.parse(fs.readFileSync(MARK_PATH, 'utf-8'));
  data.posted_urls = [...new Set([...data.posted_urls, ...urls])];
  data.last_updated = new Date().toISOString();
  fs.writeFileSync(MARK_PATH, JSON.stringify(data, null, 2));
  console.log(JSON.stringify({marked: urls.length, total: data.posted_urls.length}));
  process.exit(0);
}

console.error('Unknown command: ' + command);
process.exit(1);
"""
with open("scripts/ai_trends.js", "w") as f:
    f.write(ai_trends_js)

# Mock xurl binary
xurl_script = """#!/bin/bash
echo '{"status": "ok", "message": "xurl mock - use scripts/ai_trends.js for data"}' 
"""
with open("/usr/local/bin/xurl", "w") as f:
    f.write(xurl_script)

# Mock openclaw binary
openclaw_script = r"""#!/bin/bash
# Mock openclaw - records calls
LOGFILE="/workspace/logs/openclaw_calls.log"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] openclaw $@" >> "$LOGFILE"
if [[ "$1" == "message" && "$2" == "send" ]]; then
  echo '{"ok": true, "ts": "1705000000.000001", "channel": "C123456"}'
fi
"""
with open("/usr/local/bin/openclaw", "w") as f:
    f.write(openclaw_script)

print("Workspace initialized successfully.")
print(f"Raw tweets: {len(raw_tweets)} entries written to data/raw/tweets_search_result.json")
print(f"Recently posted: {len(recently_posted)} URLs in data/processed/recently_posted.json")