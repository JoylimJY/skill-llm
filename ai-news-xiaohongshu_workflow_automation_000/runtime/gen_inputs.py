import os
import json
import random
import stat
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
skill_root = Path("/root/.openclaw/workspace/skills/ai-news-xiaohongshu")
scripts_dir = skill_root / "scripts"
references_dir = skill_root / "references"
output_dir = skill_root / "output"

for d in [skill_root, scripts_dir, references_dir, output_dir,
          workspace / "distractors" / "marketing" / "drafts",
          workspace / "distractors" / "social" / "weibo",
          workspace / "distractors" / "social" / "douyin",
          workspace / "distractors" / "data" / "raw_feeds",
          workspace / "distractors" / "templates" / "html",
          workspace / "distractors" / "archive" / "2024",
          workspace / "distractors" / "config"]:
    d.mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = [
    (workspace / "distractors" / "marketing" / "drafts" / "old_copy.md",
     "# Old AI News\n## March 2024\nSome outdated content about GPT-3.5...\n"),
    (workspace / "distractors" / "social" / "weibo" / "post_template.txt",
     "微博发帖模板\n转发+评论抽奖\n#AI#科技#"),
    (workspace / "distractors" / "social" / "douyin" / "script_idea.txt",
     "抖音脚本\n开场白: 大家好我是xxx\n..."),
    (workspace / "distractors" / "data" / "raw_feeds" / "rss_dump.xml",
     '<?xml version="1.0"?><rss><channel><title>AI News</title></channel></rss>'),
    (workspace / "distractors" / "templates" / "html" / "cover_v1.html",
     "<html><body><h1>Old Template</h1><p>DO NOT USE - deprecated v1</p></body></html>"),
    (workspace / "distractors" / "templates" / "html" / "cover_v2.html",
     "<html><body><h1>Cover v2</h1><p>Wrong ratio 16:9</p></body></html>"),
    (workspace / "distractors" / "archive" / "2024" / "news_2024_03.json",
     json.dumps([{"title":"Old news","url":"http://old.com","date":"2024-03-01"}])),
    (workspace / "distractors" / "config" / "wrong_format.json",
     json.dumps({"format":"wrong","fields":["headline","body","link"]})),
    (workspace / "distractors" / "config" / "api_keys_SAMPLE.txt",
     "# Sample - DO NOT USE\nAPI_KEY=YOUR_KEY_HERE\n"),
    (workspace / "distractors" / "marketing" / "content_calendar.csv",
     "date,platform,topic,status\n2024-01-01,xiaohongshu,AI news,done\n"),
    (workspace / "distractors" / "social" / "hashtags.txt",
     "#科技 #AI #人工智能 #大模型 #AIGC\n"),
    (workspace / "distractors" / "data" / "raw_feeds" / "news_wrong_schema.json",
     json.dumps([{"headline":"OpenAI news","body":"content","link":"http://openai.com","published":"2h ago","domain":"openai.com"}])),
]

for path, content in distractors:
    path.write_text(content, encoding="utf-8")

# --- The actual skill script (create-xiaohongshu-content.js) ---
# This is the core proprietary script the agent must call correctly.
create_script = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

// ─── Parse CLI arguments ───────────────────────────────────────────────
const args = process.argv.slice(2);
let newsData = null;
let useDemo = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--use-demo') {
    useDemo = true;
  } else if (args[i] === '--news-json' && args[i + 1]) {
    try {
      newsData = JSON.parse(args[i + 1]);
      i++;
    } catch (e) {
      console.error('ERROR: Invalid JSON in --news-json argument.');
      console.error(e.message);
      process.exit(1);
    }
  }
}

// ─── Demo data ────────────────────────────────────────────────────────
const DEMO_NEWS = [
  {
    title: '【演示】OpenAI 发布 GPT-5 Turbo',
    content: 'OpenAI 宣布推出 GPT-5 Turbo，推理速度提升 300%，支持 200k 上下文。',
    url: 'https://openai.com/demo-news',
    time: '2 小时前',
    source: 'openai.com'
  },
  {
    title: '【演示】阿里千问 Qwen3 开源',
    content: '阿里云发布千问 Qwen3 全系列开源模型，最大参数量达 2350 亿。',
    url: 'https://qwen.aliyun.com/demo',
    time: '5 小时前',
    source: 'qwen.aliyun.com'
  },
  {
    title: '【演示】MiniMax 获 5 亿美元融资',
    content: 'MiniMax 完成新一轮 5 亿美元融资，估值突破百亿美元。',
    url: 'https://minimax.io/demo',
    time: '8 小时前',
    source: 'minimax.io'
  }
];

if (!newsData || newsData.length === 0) {
  useDemo = true;
  newsData = DEMO_NEWS;
  console.log('[INFO] Using demo data (no --news-json provided or empty array)');
} else {
  // Validate schema
  for (const item of newsData) {
    if (!item.title || !item.url) {
      console.error('ERROR: Each news item must have at least "title" and "url" fields.');
      console.error('Required fields: title, content, url, time, source');
      process.exit(1);
    }
    // Fill defaults for optional fields
    if (!item.content) item.content = item.title;
    if (!item.time) item.time = '未知时间';
    if (!item.source) {
      try { item.source = new URL(item.url).hostname.replace('www.', ''); }
      catch { item.source = 'unknown'; }
    }
  }
  console.log(`[INFO] Using real data: ${newsData.length} news items`);
}

// ─── Determine output directory ───────────────────────────────────────
const today = new Date();
const dateStr = today.toISOString().slice(0, 10);

const skillRoot = path.resolve(__dirname, '..');
const outputBase = path.join(skillRoot, 'output');

if (!fs.existsSync(outputBase)) fs.mkdirSync(outputBase, { recursive: true });

// Find next available index
let idx = 1;
while (fs.existsSync(path.join(outputBase, `${dateStr}-${String(idx).padStart(2, '0')}`))) {
  idx++;
}
const outDir = path.join(outputBase, `${dateStr}-${String(idx).padStart(2, '0')}`);
fs.mkdirSync(outDir, { recursive: true });

console.log(`[INFO] Output directory: ${outDir}`);

// ─── Generate xiaohongshu copy ────────────────────────────────────────
const demoLabel = useDemo ? ' (演示模式)' : '';
const topNews = newsData.slice(0, 5);

const copyLines = [
  `🔥 AI 圈又炸了！今日重磅资讯速递${demoLabel}`,
  '',
  '家人们谁懂啊，今天 AI 圈动作太多了😱',
  '给大家整理好最新资讯，快来看看！',
  '',
  '📌 今日核心资讯：',
];

topNews.forEach((n, i) => {
  const emojis = ['🚀', '💰', '🛠️', '🤖', '📱'];
  copyLines.push(`${emojis[i % emojis.length]} ${n.title}`);
  copyLines.push(`   ${n.content.slice(0, 60)}${n.content.length > 60 ? '...' : ''}`);
  copyLines.push('');
});

copyLines.push('💡 个人解读：');
copyLines.push('AI 进化速度远超预期，建议大家保持学习节奏 💪');
copyLines.push('');
copyLines.push('👇 想要 AI 工具包的宝子评论区扣"666"');
copyLines.push('📌 关注我，每日更新 AI 前沿资讯');
copyLines.push('');
copyLines.push('#AI #大模型 #人工智能 #科技资讯 #AIGC');

const copyContent = copyLines.join('\n');
fs.writeFileSync(path.join(outDir, 'xiaohongshu-copy.md'), copyContent, 'utf8');
console.log('[INFO] Generated xiaohongshu-copy.md');

// ─── Generate news-summary.md ─────────────────────────────────────────
const summaryLines = [
  `# AI 资讯汇总 - ${dateStr}${demoLabel}`,
  '',
  '| 时间 | 公司/项目 | 核心内容 | 来源 |',
  '|------|----------|---------|------|',
];

newsData.forEach(n => {
  const company = n.source || '-';
  const core = n.content.slice(0, 40).replace(/\|/g, '｜');
  summaryLines.push(`| ${n.time} | ${company} | ${core} | [链接](${n.url}) |`);
});

fs.writeFileSync(path.join(outDir, 'news-summary.md'), summaryLines.join('\n'), 'utf8');
console.log('[INFO] Generated news-summary.md');

// ─── Generate sources.md ──────────────────────────────────────────────
const sourcesLines = [
  `# 原始来源链接 - ${dateStr}${demoLabel}`,
  '',
];
newsData.forEach((n, i) => {
  sourcesLines.push(`${i + 1}. **${n.title}**`);
  sourcesLines.push(`   - 来源：${n.source}`);
  sourcesLines.push(`   - 链接：${n.url}`);
  sourcesLines.push(`   - 时间：${n.time}`);
  sourcesLines.push('');
});
fs.writeFileSync(path.join(outDir, 'sources.md'), sourcesLines.join('\n'), 'utf8');
console.log('[INFO] Generated sources.md');

// ─── Generate cover.html ──────────────────────────────────────────────
// 3:4 ratio, 1080x1440px, 2 screens (pages), with dividing line between screens
const page1News = topNews.slice(0, 3);
const page2News = topNews.slice(3, 6);

const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080">
  <title>AI 日报封面 - ${dateStr}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px;
      font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
      background: #0a0a1a;
    }
    /* Each page is exactly 3:4 = 1080x1440 */
    .page {
      width: 1080px;
      height: 1440px;
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 80px 60px;
    }
    .page-divider {
      width: 1080px;
      height: 8px;
      background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
    }
    .page-1 {
      background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    .page-2 {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    .badge {
      background: rgba(102, 126, 234, 0.3);
      border: 1px solid #667eea;
      color: #a78bfa;
      font-size: 28px;
      padding: 10px 30px;
      border-radius: 50px;
      margin-bottom: 40px;
      letter-spacing: 4px;
    }
    .main-title {
      font-size: 90px;
      font-weight: 900;
      color: #fff;
      text-align: center;
      line-height: 1.1;
      margin-bottom: 20px;
      text-shadow: 0 0 40px rgba(167, 139, 250, 0.6);
    }
    .sub-title {
      font-size: 40px;
      color: #a78bfa;
      text-align: center;
      margin-bottom: 60px;
    }
    .date-label {
      font-size: 32px;
      color: rgba(255,255,255,0.5);
      margin-bottom: 60px;
    }
    .news-card {
      width: 100%;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(102,126,234,0.3);
      border-radius: 20px;
      padding: 36px 44px;
      margin-bottom: 30px;
    }
    .news-card .news-title {
      font-size: 38px;
      color: #fff;
      font-weight: 700;
      margin-bottom: 16px;
      line-height: 1.3;
    }
    .news-card .news-meta {
      font-size: 28px;
      color: rgba(255,255,255,0.5);
    }
    .section-label {
      font-size: 36px;
      color: #667eea;
      font-weight: 700;
      width: 100%;
      text-align: left;
      margin-bottom: 30px;
      padding-bottom: 16px;
      border-bottom: 2px solid rgba(102,126,234,0.3);
    }
    .demo-watermark {
      position: absolute;
      bottom: 40px;
      right: 60px;
      font-size: 24px;
      color: rgba(255,255,255,0.2);
    }
    .highlight-stat {
      display: inline-block;
      background: linear-gradient(90deg, #667eea, #764ba2);
      color: #fff;
      font-size: 32px;
      font-weight: 700;
      padding: 8px 24px;
      border-radius: 8px;
      margin: 0 6px;
    }
  </style>
</head>
<body>

<!-- 第1屏：标题页 -->
<div class="page page-1">
  <div class="badge">🤖 AI 日报</div>
  <h1 class="main-title">今日 AI 速递</h1>
  <p class="sub-title">重磅资讯 · 精选整理</p>
  <p class="date-label">📅 ${dateStr}</p>
  <div style="display:flex; gap:30px; margin-bottom:50px;">
    <span class="highlight-stat">${newsData.length} 条资讯</span>
    <span class="highlight-stat">24h 内</span>
  </div>
  ${page1News.map(n => `
  <div class="news-card">
    <div class="news-title">${n.title.replace(/【演示】/g, '')}</div>
    <div class="news-meta">📍 ${n.source} &nbsp;·&nbsp; ⏰ ${n.time}</div>
  </div>`).join('')}
  ${useDemo ? '<div class="demo-watermark">演示模式</div>' : ''}
</div>

<!-- 屏间分隔线（便于精准截图） -->
<div class="page-divider"></div>

<!-- 第2屏：详细内容 -->
<div class="page page-2">
  <div class="section-label">📋 详细资讯</div>
  ${(page2News.length > 0 ? page2News : page1News).map((n, i) => `
  <div class="news-card">
    <div class="news-title">${i + 1}. ${n.title.replace(/【演示】/g, '')}</div>
    <div class="news-meta" style="color:rgba(255,255,255,0.7);font-size:26px;margin-top:12px;">${n.content.slice(0, 80)}</div>
    <div class="news-meta" style="margin-top:12px;">📍 ${n.source} &nbsp;·&nbsp; ⏰ ${n.time}</div>
  </div>`).join('')}
  <div style="margin-top:40px;font-size:30px;color:rgba(255,255,255,0.4);">
    🔗 关注作者获取更多 AI 资讯
  </div>
  ${useDemo ? '<div class="demo-watermark">演示模式</div>' : ''}
</div>

</body>
</html>`;

fs.writeFileSync(path.join(outDir, 'cover.html'), htmlContent, 'utf8');
console.log('[INFO] Generated cover.html');

// ─── Done ─────────────────────────────────────────────────────────────
console.log('');
console.log('✅ 内容生成完成！');
console.log(`📁 输出目录: ${outDir}`);
console.log('   - xiaohongshu-copy.md');
console.log('   - cover.html');
console.log('   - news-summary.md');
console.log('   - sources.md');
if (useDemo) {
  console.log('');
  console.log('⚠️  当前为演示模式。使用 --news-json 参数传入真实数据。');
}
""";

(scripts_dir / "create-xiaohongshu-content.js").write_text(create_script, encoding="utf-8")

# run-full-flow.js (demo mode convenience wrapper)
run_full_flow = r"""#!/usr/bin/env node
'use strict';
const { execSync } = require('child_process');
const path = require('path');

console.log('Running full flow with demo data...');
const scriptPath = path.join(__dirname, 'create-xiaohongshu-content.js');
execSync(`node "${scriptPath}" --use-demo`, { stdio: 'inherit' });
"""
(scripts_dir / "run-full-flow.js").write_text(run_full_flow, encoding="utf-8")

# references/user-config.md
(references_dir / "user-config.md").write_text("""# 用户配置

## 引流话术
📌 关注我，每日更新 AI 前沿资讯
👉 评论区留言"资料"获取 AI 工具包

## 资讯偏好
- 侧重国内+国外平衡
- 默认 3-5 条核心资讯
- HTML 需要 2 屏
""", encoding="utf-8")

# references/openclaw-integration.md
(references_dir / "openclaw-integration.md").write_text("""# OpenClaw 集成说明

## 调用方式
OpenClaw 主流程搜索后调用脚本：

```bash
node scripts/create-xiaohongshu-content.js --news-json '<JSON_ARRAY>'
```

## JSON 格式
每个 item 需要包含：
- title: 标题
- content: 摘要内容
- url: 原文链接
- time: 发布时间（如 "2 小时前"）
- source: 来源域名
""", encoding="utf-8")

# The input news data file the agent needs to use (raw, slightly messy)
raw_news = [
    {
        "title": "Anthropic 发布 Claude 3.7 Sonnet，编程能力大幅提升",
        "content": "Anthropic 宣布推出 Claude 3.7 Sonnet 模型，在 SWE-bench 基准测试中得分 62.3%，超越 GPT-4o。同时引入「扩展思考」模式，支持长达 128k token 上下文。",
        "url": "https://www.anthropic.com/news/claude-3-7-sonnet",
        "time": "3 小时前",
        "source": "anthropic.com"
    },
    {
        "title": "DeepSeek 开源 V3-0324 版本，推理性能领先",
        "content": "DeepSeek 发布 DeepSeek-V3-0324 更新版本，在数学推理和代码生成任务上性能显著提升，继续保持开源大模型性能第一。",
        "url": "https://github.com/deepseek-ai/DeepSeek-V3",
        "time": "6 小时前",
        "source": "github.com"
    },
    {
        "title": "阿里千问 Qwen2.5-Max 登顶 LMSYS 排行榜",
        "content": "阿里巴巴旗下千问 Qwen2.5-Max 模型在 LMSYS Chatbot Arena 排行榜上超越 GPT-4o，位列全球第二，中文能力尤其突出。",
        "url": "https://qwenlm.github.io/blog/qwen2.5-max/",
        "time": "12 小时前",
        "source": "qwenlm.github.io"
    },
    {
        "title": "Google 发布 Gemini 2.0 Flash Thinking 正式版",
        "content": "Google DeepMind 发布 Gemini 2.0 Flash Thinking 正式版，支持多模态输入，响应速度比上一代提升 40%，API 已对开发者开放。",
        "url": "https://deepmind.google/technologies/gemini/flash-thinking/",
        "time": "18 小时前",
        "source": "deepmind.google"
    },
    {
        "title": "字节跳动 Seed1.5-VL 视觉语言模型开源",
        "content": "字节跳动开源 Seed1.5-VL 视觉语言大模型，在多个多模态基准测试中达到 SOTA 水平，支持商业使用。",
        "url": "https://github.com/ByteDance/Seed-VL",
        "time": "20 小时前",
        "source": "github.com"
    }
]

(workspace / "raw_news_input.json").write_text(
    json.dumps(raw_news, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# Additional distractors to confuse the agent
(workspace / "distractors" / "data" / "raw_feeds" / "wrong_news_format.json").write_text(
    json.dumps([
        {"headline": "Wrong schema", "body": "wrong", "link": "http://wrong.com", "timestamp": "1h ago"},
        {"headline": "Another wrong", "body": "wrong too", "link": "http://wrong2.com", "timestamp": "2h ago"},
    ], ensure_ascii=False, indent=2),
    encoding="utf-8"
)

(workspace / "distractors" / "templates" / "html" / "wrong_ratio.html").write_text(
    "<html><body style='width:1920px;height:1080px'>Wrong 16:9 ratio template</body></html>",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Skill root: {skill_root}")
print(f"Raw news input: {workspace}/raw_news_input.json")
print(f"Script: {scripts_dir}/create-xiaohongshu-content.js")