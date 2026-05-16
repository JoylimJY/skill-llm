import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# Create the full skill directory structure as it would exist in the wild
skill_dir = os.path.join(workspace, "skills", "daily-fun-content")
scripts_dir = os.path.join(skill_dir, "scripts")
cache_dir = os.path.join(skill_dir, "cache")

os.makedirs(scripts_dir, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)

# Create distractor files and a realistic project structure
distractor_dirs = [
    os.path.join(workspace, "skills", "perplexity-search", "scripts"),
    os.path.join(workspace, "skills", "perplexity-search", "cache"),
    os.path.join(workspace, "skills", "glm-web-search", "scripts"),
    os.path.join(workspace, "skills", "weather-report", "scripts"),
    os.path.join(workspace, "skills", "weather-report", "cache"),
    os.path.join(workspace, "config"),
    os.path.join(workspace, "logs"),
    os.path.join(workspace, "tmp"),
    os.path.join(workspace, "docs"),
    os.path.join(workspace, "cron-jobs"),
]

for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    os.path.join(workspace, "skills", "perplexity-search", "scripts", "search.mjs"): "// perplexity search script\nexport async function search(query) { return []; }\n",
    os.path.join(workspace, "skills", "perplexity-search", "cache", "results.json"): json.dumps({"query": "test", "results": []}, indent=2),
    os.path.join(workspace, "skills", "glm-web-search", "scripts", "query.mjs"): "// glm web search\nexport default async function query(q) { return null; }\n",
    os.path.join(workspace, "skills", "weather-report", "scripts", "fetch.mjs"): "// weather fetcher\n",
    os.path.join(workspace, "skills", "weather-report", "cache", "today.json"): json.dumps({"city": "Shanghai", "temp": 22, "weather": "sunny"}),
    os.path.join(workspace, "config", "cron.yaml"): "crons:\n  - name: weather\n    schedule: '0 7 * * *'\n  - name: news\n    schedule: '0 8 * * *'\n",
    os.path.join(workspace, "config", "skills.json"): json.dumps({"installed": ["perplexity-search", "glm-web-search", "weather-report"], "version": "2.1.0"}, indent=2),
    os.path.join(workspace, "logs", "cron.log"): "2026-03-09 06:00:01 [INFO] Starting daily fun content generation\n2026-03-09 06:00:02 [ERROR] Cache file not found\n2026-03-09 06:00:02 [INFO] Retrying...\n",
    os.path.join(workspace, "logs", "heartbeat.log"): "2026-03-09 08:00:00 [INFO] Heartbeat tick\n2026-03-09 08:00:00 [WARN] daily-fun cache empty, skipping fun content\n",
    os.path.join(workspace, "tmp", "scratch.json"): json.dumps({"note": "temporary scratch data, ignore"}),
    os.path.join(workspace, "docs", "HEARTBEAT.md"): "# Heartbeat Documentation\n\n## Overview\nThe heartbeat system runs every 30 minutes...\n\n## Integrations\n- Weather\n- News digest\n- TODO: fun content (not yet configured)\n",
    os.path.join(workspace, "cron-jobs", "schedule.txt"): "0 6 * * * /usr/bin/node /workspace/skills/weather-report/scripts/fetch.mjs\n0 7 * * * /usr/bin/node /workspace/skills/perplexity-search/scripts/search.mjs\n",
}

for fpath, content in distractor_files.items():
    with open(fpath, "w") as f:
        f.write(content)

# Create the SKILL.md for the daily-fun-content skill
skill_md = '''---
name: daily-fun-content
description: "每日趣味内容生成器 - 每天早上搜索网络，预缓存一天的笑话、热梗、聊天技巧。包括搞笑段子、网络热梗解释、高情商对话示例。用 cron 触发，内容缓存到文件，心跳时随机取用。"
license: MIT
metadata:
  clawdbot:
    emoji: "🎉"
    os: ["darwin", "linux"]
    requires:
      env: []
---

# Daily Fun Content

每天早上自动搜索网络，生成并缓存一天的趣味内容。

## 功能

- **搞笑段子** - 从网络搜索最新笑话、段子
- **网络热梗** - 搜索最近流行的梗、表情包梗、流行语
- **聊天技巧** - 高情商对话示例、接话技巧
- **预缓存** - 每天早上生成 6-8 条内容，存到 `cache/daily-fun.json`
- **随机取用** - 心跳时从缓存随机取一条分享

## 使用方式

### 1. 每日生成（Cron）

每天早上 6:00 自动生成：

```bash
openclaw cron add \\
  --name "Daily Fun Content Generator" \\
  --cron "0 6 * * *" \\
  --tz "Asia/Shanghai" \\
  --session isolated \\
  --wake now \\
  --message "Generate daily fun content: search web for jokes, memes, and chat tips. Cache 6-8 items to cache/daily-fun.json"
```

### 2. 手动生成

```bash
node {baseDir}/scripts/generate.mjs
```

### 3. 获取内容

心跳时调用：

```bash
node {baseDir}/scripts/get-content.mjs
```

返回随机一条缓存的内容。

## 内容格式

缓存文件 `cache/daily-fun.json`：

```json
{
  "date": "2026-03-09",
  "generated": "2026-03-09T06:00:00Z",
  "items": [
    {
      "type": "joke",
      "content": "朋友问我\'你周末干嘛了\'，我说\'躺了一天\'。他说\'那多无聊啊\'。我说\'你不懂，躺平也是一种技术，我得练\'。"
    },
    {
      "type": "meme",
      "title": "我悟了",
      "content": "最近\'我悟了\'这个梗挺火。用法：当别人说了个常识，你装作恍然大悟。\\n朋友：\'多喝水对身体好\'\\n你：\'我悟了\'"
    },
    {
      "type": "chat_tip",
      "content": "别人问\'在干嘛\'，别说\'没干嘛\'。说\'刚在想你上次说的那个事\'或者\'在发呆，你呢？\'— 把球抛回去，对话才能继续。"
    }
  ]
}
```

## 内容类型

| 类型 | 说明 | 来源 |
|------|------|------|
| `joke` | 搞笑段子、生活笑话 | 搜索"最新笑话 2026"、"搞笑段子" |
| `meme` | 网络热梗、流行语 | 搜索"最近流行梗"、"网络热词 2026" |
| `chat_tip` | 聊天技巧、高情商对话 | 搜索"聊天技巧"、"高情商回复" |

## 搜索策略

生成时会搜索：
1. 中文搞笑内容（豆瓣、知乎、微博等）
2. 最近 7 天的网络热梗
3. 实用的聊天技巧

确保内容：
- 真正好笑，不冷
- 热梗解释清楚用法
- 聊天技巧实用不油腻
- 不冒犯、不敏感

## 心跳集成

更新 `HEARTBEAT.md`：

```markdown
### 6. 趣味内容分享（每 2-3 小时）
- **条件**：距离上次分享 > 2 小时
- **动作**：`node skills/daily-fun-content/scripts/get-content.mjs`
- **报告**：直接分享返回的内容
- **回退**：如果缓存为空，现场生成一条
```

## 文件结构

```
skills/daily-fun-content/
├── SKILL.md              # 本文件
├── scripts/
│   ├── generate.mjs      # 每日生成脚本
│   └── get-content.mjs   # 获取随机内容
└── cache/
    └── daily-fun.json    # 缓存文件（gitignore）
```

## 依赖

- 需要网络搜索能力（可用 `perplexity` skill 或 `glm-web-search` skill）
- Node.js 18+

## 发布到 ClawHub

```bash
# 1. 测试
node scripts/generate.mjs
node scripts/get-content.mjs

# 2. 发布
clawhub publish ./skills/daily-fun-content \\
  --slug daily-fun-content \\
  --name "Daily Fun Content" \\
  --version 1.0.0 \\
  --changelog "Initial release - daily jokes, memes, and chat tips"
```
'''

with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# Create the generate.mjs script - it reads the cache file to verify it's valid,
# then outputs confirmation. In the real world this would call AI APIs, but here
# it validates and reports on whatever cache/daily-fun.json exists.
generate_mjs = r"""#!/usr/bin/env node
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const cacheFile = join(__dirname, '..', 'cache', 'daily-fun.json');

if (!existsSync(cacheFile)) {
  console.error('ERROR: cache/daily-fun.json not found');
  process.exit(1);
}

let data;
try {
  data = JSON.parse(readFileSync(cacheFile, 'utf-8'));
} catch (e) {
  console.error('ERROR: Invalid JSON in cache/daily-fun.json:', e.message);
  process.exit(1);
}

// Validate required top-level fields
if (!data.date || !data.generated || !Array.isArray(data.items)) {
  console.error('ERROR: Missing required fields: date, generated, items');
  process.exit(1);
}

// Validate date format YYYY-MM-DD
if (!/^\d{4}-\d{2}-\d{2}$/.test(data.date)) {
  console.error('ERROR: date must be YYYY-MM-DD format, got:', data.date);
  process.exit(1);
}

// Validate generated format ISO 8601
if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(data.generated)) {
  console.error('ERROR: generated must be ISO 8601 UTC format (YYYY-MM-DDThh:mm:ssZ), got:', data.generated);
  process.exit(1);
}

// Validate item count 6-8
if (data.items.length < 6 || data.items.length > 8) {
  console.error(`ERROR: items count must be 6-8, got ${data.items.length}`);
  process.exit(1);
}

// Validate each item
for (let i = 0; i < data.items.length; i++) {
  const item = data.items[i];
  const validTypes = ['joke', 'meme', 'chat_tip'];
  if (!validTypes.includes(item.type)) {
    console.error(`ERROR: item[${i}] has invalid type: ${item.type}. Must be one of: ${validTypes.join(', ')}`);
    process.exit(1);
  }
  if (!item.content || typeof item.content !== 'string' || item.content.trim() === '') {
    console.error(`ERROR: item[${i}] missing or empty content field`);
    process.exit(1);
  }
  if (item.type === 'meme') {
    if (!item.title || typeof item.title !== 'string' || item.title.trim() === '') {
      console.error(`ERROR: item[${i}] is type 'meme' but missing required 'title' field`);
      process.exit(1);
    }
  }
}

// Check type distribution - must have at least one of each type
const types = data.items.map(i => i.type);
const hasJoke = types.includes('joke');
const hasMeme = types.includes('meme');
const hasChatTip = types.includes('chat_tip');

if (!hasJoke) { console.error('ERROR: Must have at least one joke item'); process.exit(1); }
if (!hasMeme) { console.error('ERROR: Must have at least one meme item'); process.exit(1); }
if (!hasChatTip) { console.error('ERROR: Must have at least one chat_tip item'); process.exit(1); }

console.log(`✓ Cache validated successfully`);
console.log(`  Date: ${data.date}`);
console.log(`  Generated: ${data.generated}`);
console.log(`  Items: ${data.items.length}`);
console.log(`  Types: ${[...new Set(types)].join(', ')}`);
"""

with open(os.path.join(scripts_dir, "generate.mjs"), "w", encoding="utf-8") as f:
    f.write(generate_mjs)

# Create get-content.mjs - returns a random item from cache
get_content_mjs = r"""#!/usr/bin/env node
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const cacheFile = join(__dirname, '..', 'cache', 'daily-fun.json');

if (!existsSync(cacheFile)) {
  console.error('Cache file not found. Run generate.mjs first.');
  process.exit(1);
}

let data;
try {
  data = JSON.parse(readFileSync(cacheFile, 'utf-8'));
} catch (e) {
  console.error('Invalid cache file:', e.message);
  process.exit(1);
}

if (!data.items || data.items.length === 0) {
  console.error('Cache is empty.');
  process.exit(1);
}

const item = data.items[Math.floor(Math.random() * data.items.length)];

if (item.type === 'meme') {
  console.log(`[${item.type}] ${item.title}: ${item.content}`);
} else {
  console.log(`[${item.type}] ${item.content}`);
}
"""

with open(os.path.join(scripts_dir, "get-content.mjs"), "w", encoding="utf-8") as f:
    f.write(get_content_mjs)

# Create a broken/incomplete cache file as a distractor (wrong format, wrong location)
wrong_cache = {
    "jokes": ["This is in the wrong format", "Also wrong"],
    "count": 2
}
with open(os.path.join(workspace, "tmp", "old-fun-cache.json"), "w", encoding="utf-8") as f:
    json.dump(wrong_cache, f, indent=2)

# Create a partial/malformed daily-fun.json in the wrong location as a trap
partial_cache = {
    "date": "2026-03-09",
    "items": [
        {"type": "joke", "content": "This is incomplete - only 3 items, wrong location, and meme has no title"},
        {"type": "meme", "content": "No title field here - this is wrong"},
        {"type": "chat_tip", "content": "Also this file is in the wrong directory"}
    ]
}
with open(os.path.join(workspace, "skills", "daily-fun-content", "daily-fun.json"), "w", encoding="utf-8") as f:
    json.dump(partial_cache, f, indent=2, ensure_ascii=False)

print("Workspace setup complete.")
print(f"Skill directory: {skill_dir}")
print(f"Scripts: {scripts_dir}")
print(f"Cache dir (empty, no daily-fun.json): {cache_dir}")