import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory Structure ---
dirs = [
    "references",
    "references/archives",
    "references/templates",
    "company/strategy",
    "company/reports/2024",
    "company/reports/2025",
    "tools/scrapers",
    "tools/parsers",
    "logs",
    "drafts",
    "config",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- SKILL.md (core documentation) ---
skill_md = '''---
name: ai-news-collector
description: AI 新闻聚合与热度排序工具。当用户询问 AI 领域最新动态时触发，如："今天有什么 AI 新闻？""总结一下这周的 AI 动态""最近有什么火的 AI 产品？""AI 圈最近在讨论什么？"。覆盖：新产品发布、研究论文、行业动态、融资新闻、开源项目更新、社区病毒传播现象、AI 工具/Agent 热门项目。输出中文摘要列表，按热度排序，附带原文链接。
---

# AI News Collector

收集、聚合并按热度排序 AI 领域新闻。

## 核心原则

**不要只搜"AI news today"。** 泛搜索返回的是 SEO 聚合页和趋势预测文章，会系统性遗漏社区级病毒传播现象（如开源工具爆火、Meme 级事件）。必须用多维度、分层搜索策略。

## 工作流程

### 1. 多维度分层搜索（最少 8 次，建议 10-12 次）

按以下 **6 个维度** 依次执行搜索，每个维度至少 1 次：

#### 维度 A：周报/Newsletter 聚合（最优先 🔑）

这是信息密度最高的来源，一篇文章可覆盖 10+ 条新闻。

```
搜索词：
- "last week in AI" [当前月份年份]
- "AI weekly roundup" [当前月份年份]
- "the batch AI newsletter"
- site:substack.com AI news [当前月份]
```

发现周报后，用 web_fetch 获取全文，从中提取所有新闻线索。

#### 维度 B：社区热度/病毒传播（关键维度 🔑）

捕捉自下而上的社区爆款，这类信息泛搜索几乎无法触达。

```
搜索词：
- "viral AI tool" OR "viral AI agent"
- "AI trending" site:reddit.com OR site:news.ycombinator.com
- "GitHub trending AI" OR "AI open source trending"
- AI buzzing OR "everyone is talking about" AI
- "most popular AI" this week
```

#### 维度 C：产品发布与模型更新

```
搜索词：
- "AI model release" OR "LLM launch" [当前月份]
- "AI product launch" [当前月份年份]
- OpenAI OR Anthropic OR Google OR Meta AI announcement
- "大模型 发布" OR "AI 新产品"
```

#### 维度 D：融资与商业

```
搜索词：
- "AI startup funding" [当前月份年份]
- "AI acquisition" OR "AI IPO"
- "AI 融资" OR "人工智能投资"
```

#### 维度 E：研究突破

```
搜索词：
- "AI breakthrough" OR "AI paper" [当前月份]
- "state of the art" machine learning
- "AI 论文" OR "机器学习突破"
```

#### 维度 F：监管与政策

```
搜索词：
- "AI regulation" OR "AI policy" [当前月份年份]
- "AI law" OR "AI governance" 
- "AI 监管" OR "人工智能法案"
```

### 2. 交叉验证与补漏

初轮搜索完成后，检查是否有遗漏：

- 如果 Newsletter 中提到了某个项目/事件但初轮搜索未覆盖 → 对该项目专项搜索
- 如果同一事件被 3+ 个不同来源提及 → 大概率是热点，深入搜索获取更多细节
- 如果中文媒体和英文媒体的热点完全不同 → 两边都要覆盖

### 3. 搜索关键词设计原则（反模式清单）

| ❌ 不要这样搜 | ✅ 应该这样搜 | 原因 |
|---|---|---|
| "AI news today February 2026" | "AI weekly roundup February 2026" | 前者返回聚合页，后者返回策划内容 |
| "AI news today" | "viral AI tool" + "AI model release" 分开搜 | 泛搜无法覆盖社区现象 |
| "artificial intelligence breaking news" | 按维度分类搜索 | 过于宽泛，返回噪音 |
| 搜索词中加具体年月日 | 用 "this week" "today" "latest" | 日期反而会偏向预测/展望文章 |
| 只搜 3 次就开始写 | 至少 8 次，覆盖 6 个维度 | 3 次搜索覆盖率不到 30% |

### 4. 热度综合判断

基于以下信号评估每条新闻热度（1-5 星）：

| 信号 | 权重 | 说明 |
|------|------|------|
| 多家媒体报道同一事件 | ⭐⭐⭐ 高 | 3+ 来源 = 确认热点 |
| 社区病毒传播证据 | ⭐⭐⭐ 高 | GitHub star 暴涨、Twitter 刷屏、HN 首页 |
| 来自权威来源（顶会、大厂官宣） | ⭐⭐⭐ 高 | 但注意大厂 PR 不等于真热点 |
| 实际用户体验分享 | ⭐⭐ 中 | 有人真的在用 > 只是发布了 |
| 技术突破性/影响范围 | ⭐⭐ 中 | |
| 争议性（安全、伦理讨论） | ⭐⭐ 中 | 争议往往说明影响力大 |
| 时效性（越新越热） | ⭐ 中低 | 辅助排序 |

### 5. 输出格式

按热度降序排列，输出 **15-25 条**新闻：

```
## 🔥 AI 新闻速递（YYYY-MM-DD）

### ⭐⭐⭐⭐⭐ 热度最高

1. **[新闻标题]**
   > 一句话摘要（不超过 50 字）
   > 🔗 [来源名称](URL)

### ⭐⭐⭐⭐ 高热度

2. ...

### ⭐⭐⭐ 中等热度

...

---
📊 本次共收集 XX 条新闻 | 搜索 XX 次 | 覆盖维度：A/B/C/D/E/F | 更新时间：HH:MM
```

### 6. 去重与合并

- 同一事件被多家报道时，合并为一条，选择最权威/详细的来源
- 在摘要中注明"多家媒体报道"以体现热度
- 改名/更名的项目视为同一事件（如 Clawdbot → Moltbot → OpenClaw）

## 推荐新闻源

详见 [references/sources.md](references/sources.md)。

## 注意事项

- 优先使用 HTTPS 链接
- 遇到付费墙/无法访问的内容，标注"需订阅"
- 保持客观，不对新闻内容做主观评价
- 搜索不足 8 次不要开始输出
- 如果某个维度搜索结果为空，换关键词再搜一次
'''

(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

# --- references/sources.md ---
sources_md = '''# AI 新闻源推荐列表

## Newsletter / 周报（信息密度最高 🔑）

| 来源 | 网址 | 特点 |
|------|------|------|
| Last Week in AI | lastweekin.ai / medium.com/last-week-in-ai | 每周最全面的 AI 新闻汇总 |
| The Batch (Andrew Ng) | deeplearning.ai/the-batch | 权威周报 |
| Import AI (Jack Clark) | importai.net | Anthropic 联创的 AI 周报 |
| Platformer (Casey Newton) | platformer.news | 科技深度分析，覆盖 AI |
| The Neuron | theneurondaily.com | 每日 AI 简报 |
| Ben\'s Bites | bensbites.com | AI 产品/工具为主 |
| AI Tidbits | aitidbits.substack.com | AI 动态精选 |
| TLDR AI | tldr.tech/ai | 每日 AI 简报 |
| Interconnects | interconnects.ai | 深度技术分析 |

## 关键 Substack / 独立博客

| 来源 | 网址 | 特点 |
|------|------|------|
| Gary Marcus | garymarcus.substack.com | AI 批评性分析，常首发安全/争议话题 |
| Simon Willison | simonwillison.net | LLM 安全、工具生态，社区现象第一手报道 |
| Ethan Mollick | oneusefulthing.substack.com | Wharton 教授，AI 应用洞察 |
| Lenny\'s Newsletter | lennysnewsletter.com | AI 产品/增长 |
| Understanding AI | understandingai.org | 趋势分析与预测 |
| Nathan Lebenz (Cognitive Revolution) | cognitiverevolution.substack.com | AI 深度访谈 |

## 国际主流媒体

| 来源 | 网址 | 侧重 |
|------|------|------|
| TechCrunch AI | techcrunch.com/category/artificial-intelligence | 产品、融资 |
| The Verge AI | theverge.com/ai-artificial-intelligence | 产品、行业 |
| Ars Technica | arstechnica.com/ai | 深度分析 |
| VentureBeat AI | venturebeat.com/ai | 企业 AI |
| MIT Tech Review | technologyreview.com/artificial-intelligence | 研究、趋势 |
| Wired AI | wired.com/tag/artificial-intelligence | 行业影响 |
| CNBC Tech | cnbc.com/technology | 商业+科技交叉 |
| Scientific American | scientificamerican.com | 科学视角 AI |
| The Information | theinformation.com | 深度报道（付费） |

## 国内媒体

| 来源 | 网址 | 侧重 |
|------|------|------|
| 机器之心 | jiqizhixin.com | 技术、论文 |
| 量子位 | qbitai.com | 产品、行业 |
| 36氪 AI | 36kr.com/information/AI | 融资、产品 |
| InfoQ AI | infoq.cn/topic/AI | 技术实践 |
| 新智元 | xinzhiyuan.com | 行业动态 |
| AI 科技评论 | leiphone.com/category/ai | 技术、产品 |

## 社区与论坛（捕捉病毒传播 🔑）

| 来源 | 网址 | 特点 |
|------|------|------|
| Hacker News | news.ycombinator.com | 技术讨论热度，开源项目首发 |
| Reddit r/MachineLearning | reddit.com/r/MachineLearning | 学术前沿 |
| Reddit r/artificial | reddit.com/r/artificial | 综合讨论 |
| Reddit r/LocalLLaMA | reddit.com/r/LocalLLaMA | 本地模型、开源工具热度 |
| Reddit r/singularity | reddit.com/r/singularity | AI 社区热议 |
| Twitter/X | twitter.com | 实时动态，病毒传播首发地 |
| 即刻 AI 圈子 | okjike.com | 国内社区讨论 |
| V2EX | v2ex.com | 开发者视角 |
| 知乎 | zhihu.com | 深度技术讨论 |

## 安全与批评视角

| 来源 | 网址 | 特点 |
|------|------|------|
| Palo Alto Networks Blog | paloaltonetworks.com/blog | AI 安全预警 |
| 1Password Blog | 1password.com/blog | Agent 安全分析 |
| Trail of Bits | blog.trailofbits.com | AI 安全研究 |

## 学术与研究

| 来源 | 网址 | 特点 |
|------|------|------|
| arXiv CS.AI | arxiv.org/list/cs.AI/recent | 最新论文 |
| arXiv CS.LG | arxiv.org/list/cs.LG/recent | 机器学习论文 |
| Papers With Code | paperswithcode.com | 论文+代码 |
| Google AI Blog | ai.googleblog.com | 谷歌研究 |
| OpenAI Blog | openai.com/blog | OpenAI 动态 |
| Anthropic News | anthropic.com/news | Anthropic 动态 |
| DeepMind Blog | deepmind.com/blog | DeepMind 研究 |
| Meta AI | ai.meta.com/blog | Meta 研究 |
| Hugging Face Blog | huggingface.co/blog | 开源生态 |

## 开源项目追踪

| 来源 | 网址 | 特点 |
|------|------|------|
| GitHub Trending | github.com/trending | 热门项目，必查 |
| Product Hunt AI | producthunt.com/topics/artificial-intelligence | 新产品发布 |
| Awesome LLM | github.com/Hannibal046/Awesome-LLM | LLM 资源汇总 |
| Hugging Face Models | huggingface.co/models | 新模型发布 |

## 搜索关键词矩阵

每个维度对应的推荐搜索词：

**Newsletter/周报**：
- `"last week in AI" [月份 年份]`
- `"AI weekly roundup" [月份 年份]`
- `site:substack.com AI news [月份]`

**社区病毒传播**：
- `"viral AI tool" OR "viral AI agent"`
- `"AI trending" site:reddit.com`
- `"GitHub trending AI"`
- `AI "everyone is talking about"`

**产品发布**：
- `"AI model release" OR "LLM launch" [月份]`
- `OpenAI OR Anthropic OR Google announcement`
- `"大模型发布" OR "AI 新产品"`

**研究突破**：
- `"AI breakthrough" OR "state of the art" [月份]`
- `"AI paper" OR "machine learning research"`

**融资商业**：
- `"AI startup funding" [月份 年份]`
- `"AI acquisition" OR "AI IPO"`

**监管政策**：
- `"AI regulation" OR "AI policy" [月份 年份]`
- `"AI law" OR "AI 监管"`
'''

(workspace / "references" / "sources.md").write_text(sources_md, encoding="utf-8")

# --- Distractor files ---

# Old partial draft with wrong format
(workspace / "drafts" / "old_news_attempt.md").write_text(
    "# AI News\n1. GPT-5 released\n2. Some funding\n3. New paper\n\nOnly 3 items, incomplete.\n",
    encoding="utf-8"
)

# A fake config file
(workspace / "config" / "collector_config.yaml").write_text(
    "version: 1\nsources:\n  - hacker_news\n  - techcrunch\nmax_results: 5\nlanguage: en\n",
    encoding="utf-8"
)

# A misleading template that uses WRONG format (no footer, no stars)
(workspace / "references" / "templates" / "wrong_template.md").write_text(
    "# Weekly AI Summary\n\n## Top Stories\n1. Story one\n2. Story two\n\n## Funding\n- Company raised $50M\n",
    encoding="utf-8"
)

# Archive of old reports (distractors)
for i, month in enumerate(["2024-10", "2024-11", "2024-12"]):
    (workspace / "company" / "reports" / "2024" / f"ai_report_{month}.txt").write_text(
        f"Old report for {month}. Contains outdated news. Do not use.\n"
        + "\n".join([f"- Item {j}: some old AI news" for j in range(5)]),
        encoding="utf-8"
    )

# A Python scraper stub (distractor)
(workspace / "tools" / "scrapers" / "rss_scraper.py").write_text(
    '#!/usr/bin/env python3\n"""Stub scraper - not functional"""\nimport feedparser\n\ndef scrape(url):\n    # TODO: implement\n    pass\n',
    encoding="utf-8"
)

# A parser stub (distractor)
(workspace / "tools" / "parsers" / "html_parser.py").write_text(
    '#!/usr/bin/env python3\n"""Stub HTML parser"""\nfrom bs4 import BeautifulSoup\n\ndef parse(html):\n    soup = BeautifulSoup(html, "lxml")\n    return soup.get_text()\n',
    encoding="utf-8"
)

# Log files (distractors)
(workspace / "logs" / "scraper.log").write_text(
    "[2024-12-01 10:00:00] ERROR: Connection timeout to reddit.com\n"
    "[2024-12-01 10:01:00] INFO: Fetched 3 results from hackernews\n"
    "[2024-12-01 10:02:00] WARN: Only 3 searches completed, output suppressed\n",
    encoding="utf-8"
)

# A note file with wrong search count
(workspace / "company" / "strategy" / "research_notes.txt").write_text(
    "Strategy note: we typically do 3-4 searches max to save API quota.\n"
    "Format: just list items 1-10, no star ratings needed.\n"
    "Output in English is fine for internal use.\n",
    encoding="utf-8"
)

# References archive (distractor)
(workspace / "references" / "archives" / "2024_sources.json").write_text(
    json.dumps({
        "archived_sources": ["techcrunch.com", "wired.com"],
        "note": "These sources were checked in 2024. May be outdated."
    }, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# Company report 2025 placeholder
(workspace / "company" / "reports" / "2025" / "placeholder.txt").write_text(
    "2025 reports directory. No reports yet.\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")