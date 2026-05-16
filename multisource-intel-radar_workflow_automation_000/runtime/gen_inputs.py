import os
import random
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "assets",
    "references",
    "logs",
    "archive/2024-q4",
    "archive/2025-q1",
    "tmp/cache",
    "tmp/raw_feeds",
    "config",
    "reports/drafts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "logs" / "fetch_2025-05-01.log").write_text(
    "INFO: fetched 42 items\nWARN: timeout on feed #7\nINFO: 38 stored\n"
)
(workspace / "logs" / "fetch_2025-05-02.log").write_text(
    "INFO: fetched 51 items\nINFO: 50 stored\n"
)
(workspace / "archive/2024-q4" / "digest_2024-11-15.md").write_text(
    "# Old Digest\nNo longer relevant.\n"
)
(workspace / "archive/2025-q1" / "digest_2025-01-20.md").write_text(
    "# Q1 Digest\nSome Q1 content here.\n"
)
(workspace / "tmp" / "cache" / "feed_cache.json").write_text(
    json.dumps({"last_run": "2025-05-01T09:30:00Z", "cached_items": 120})
)
(workspace / "tmp" / "raw_feeds" / "raw_yt.xml").write_text(
    '<?xml version="1.0"?><feed><title>YouTube Raw</title></feed>\n'
)
(workspace / "config" / "settings.yaml").write_text(
    "time_window_hours: 48\nmax_items: 10\nlanguage: zh-CN\n"
)
(workspace / "config" / "keywords_legacy.txt").write_text(
    "startup\ngrowth\nfintech\n"
)
(workspace / "reports" / "drafts" / "draft_report.txt").write_text(
    "Draft report - not finalized.\n"
)
(workspace / "tmp" / "raw_feeds" / "raw_xhs.json").write_text(
    json.dumps({"source": "xhs", "items": [], "status": "pending"})
)
(workspace / "assets" / "wechat_watchlist.txt").write_text(
    "运营研究社\n增长黑客官方\n硅谷101\n刘润\n"
)
(workspace / "assets" / "xhs_watchlist.txt").write_text(
    "产品经理张三\nAI创业日记\n增长案例库\n"
)

# ── Messy OPML file (the primary input) ─────────────────────────────────────
# Contains: well-formed entries, malformed entries (missing xmlUrl), 
# entries with wrong category nesting, duplicate feeds, non-RSS entries

opml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Roger Yang - Follow List</title>
    <dateCreated>Mon, 01 Jan 2025 00:00:00 GMT</dateCreated>
  </head>
  <body>
    <outline text="Tech &amp; AI" title="Tech &amp; AI">
      <outline type="rss" text="Paul Graham Essays" title="Paul Graham Essays"
        xmlUrl="https://www.paulgraham.com/rss.xml"
        htmlUrl="https://www.paulgraham.com/"/>
      <outline type="rss" text="AI创业内参" title="AI创业内参"
        xmlUrl="https://rss.example.com/ai-startup"
        htmlUrl="https://ai-startup.example.com/"/>
      <outline type="rss" text="增长黑客周报" title="增长黑客周报"
        xmlUrl="https://rss.example.com/growth-hacker"
        htmlUrl="https://growthhacker.example.com/"/>
      <!-- Malformed: missing xmlUrl -->
      <outline type="rss" text="硅谷早知道" title="硅谷早知道"
        htmlUrl="https://svzao.example.com/"/>
      <!-- Duplicate of first entry -->
      <outline type="rss" text="Paul Graham Essays (copy)" title="Paul Graham Essays"
        xmlUrl="https://www.paulgraham.com/rss.xml"
        htmlUrl="https://www.paulgraham.com/"/>
    </outline>
    <outline text="Finance" title="Finance">
      <outline type="rss" text="金融八卦女" title="金融八卦女"
        xmlUrl="https://rss.example.com/jrbgn"
        htmlUrl="https://jrbgn.example.com/"/>
      <outline type="rss" text="36氪融资快讯" title="36氪融资快讯"
        xmlUrl="https://rss.36kr.com/feed"
        htmlUrl="https://36kr.com/"/>
      <!-- Malformed: empty xmlUrl -->
      <outline type="rss" text="虎嗅财经" title="虎嗅财经"
        xmlUrl=""
        htmlUrl="https://huxiu.com/"/>
    </outline>
    <outline text="Founders" title="Founders">
      <outline type="rss" text="Y Combinator Blog" title="Y Combinator Blog"
        xmlUrl="https://www.ycombinator.com/blog/rss/"
        htmlUrl="https://www.ycombinator.com/blog/"/>
      <outline type="rss" text="SaaS创始人日记" title="SaaS创始人日记"
        xmlUrl="https://rss.example.com/saas-founder"
        htmlUrl="https://saasfonder.example.com/"/>
      <!-- Non-RSS type, should be handled gracefully -->
      <outline type="atom" text="Indie Hackers" title="Indie Hackers"
        xmlUrl="https://www.indiehackers.com/feed.xml"
        htmlUrl="https://www.indiehackers.com/"/>
    </outline>
    <outline text="WeChat OA (No RSS)" title="WeChat OA (No RSS)">
      <!-- No xmlUrl - manual scan required -->
      <outline text="运营研究社" title="运营研究社"
        htmlUrl="https://mp.weixin.qq.com/account/yyyjsh"/>
      <outline text="刘润" title="刘润"
        htmlUrl="https://mp.weixin.qq.com/account/liurun"/>
    </outline>
    <!-- Top-level entry without category -->
    <outline type="rss" text="Reddit r/entrepreneur" title="Reddit r/entrepreneur"
      xmlUrl="https://www.reddit.com/r/entrepreneur/.rss"
      htmlUrl="https://www.reddit.com/r/entrepreneur/"/>
  </body>
</opml>
'''

(workspace / "assets" / "follow.opml").write_text(opml_content, encoding="utf-8")

# ── scripts/parse_opml.py ────────────────────────────────────────────────────
# The script parses OPML and writes assets/feeds.txt
# It deduplicates by xmlUrl, skips entries with missing/empty xmlUrl,
# marks no-xmlUrl entries as manual-scan-required in a separate section.

parse_opml_script = '''#!/usr/bin/env python3
"""
parse_opml.py  –  Normalize an OPML subscription list into assets/feeds.txt

Usage:
    python scripts/parse_opml.py [opml_path]

Default opml_path: assets/follow.opml
Output: assets/feeds.txt

Output format (feeds.txt):
    Each RSS/Atom feed on its own line:
        <xmlUrl>  TAB  <title>  TAB  <category>

    At the end, a section for manual-scan entries:
        ## MANUAL_SCAN_REQUIRED
        <htmlUrl>  TAB  <title>  TAB  <category>
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_opml(path: str) -> tuple[list[dict], list[dict]]:
    tree = ET.parse(path)
    root = tree.getroot()
    body = root.find("body")

    feeds = []
    manual = []
    seen_urls = set()

    def walk(node, category="Uncategorized"):
        for outline in node.findall("outline"):
            child_outlines = outline.findall("outline")
            # If this outline is a category grouping
            title = outline.get("title") or outline.get("text") or ""
            xml_url = outline.get("xmlUrl", "").strip()
            html_url = outline.get("htmlUrl", "").strip()
            o_type = outline.get("type", "").lower()

            if child_outlines:
                # It\'s a folder/category
                walk(outline, title)
            else:
                # Leaf node
                if xml_url:
                    if xml_url not in seen_urls:
                        seen_urls.add(xml_url)
                        feeds.append({
                            "xmlUrl": xml_url,
                            "title": title,
                            "category": category,
                        })
                    # else: duplicate, skip silently
                elif html_url:
                    # No RSS feed - manual scan
                    manual.append({
                        "htmlUrl": html_url,
                        "title": title,
                        "category": category,
                    })
                # else: no url at all, skip

    walk(body)
    return feeds, manual


def main():
    opml_path = sys.argv[1] if len(sys.argv) > 1 else "assets/follow.opml"
    out_path = Path("assets/feeds.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    feeds, manual = parse_opml(opml_path)

    lines = []
    for f in feeds:
        lines.append(f"{f[\'xmlUrl\']}\\t{f[\'title\']}\\t{f[\'category\']}")

    if manual:
        lines.append("")
        lines.append("## MANUAL_SCAN_REQUIRED")
        for m in manual:
            lines.append(f"{m[\'htmlUrl\']}\\t{m[\'title\']}\\t{m[\'category\']}")

    out_path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(f"[parse_opml] Wrote {len(feeds)} feeds + {len(manual)} manual entries to {out_path}")


if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "parse_opml.py").write_text(parse_opml_script, encoding="utf-8")

# ── scripts/build_digest.py ──────────────────────────────────────────────────
# Reads assets/feeds.txt, "fetches" feeds (mocked via local fixtures),
# filters by keyword whitelist within 48h window,
# applies weighted scoring, outputs structured digest data to stdout/file.

build_digest_script = '''#!/usr/bin/env python3
"""
build_digest.py  –  Fetch, filter, score and prepare digest items.

Usage:
    python scripts/build_digest.py --keywords 创业,AI,增长,金融,出海,SaaS \\
                                   --feeds assets/feeds.txt \\
                                   --hours 48 \\
                                   --out assets/digest_raw.json

Scoring weights (hardcoded per spec):
    relevance      40%
    actionability  30%
    novelty        20%
    evidence       10%

Anti-noise: drops items flagged as generic/motivational with no new evidence.
Outputs JSON with:
    {
      "scanned": N,
      "matched": N,
      "shortlisted": N,
      "items": [...],        # up to 8 items, scored desc
      "dropped_noise": [...] # items filtered out with reason
    }
"""

import sys
import json
import argparse
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Deterministic mock feed data ─────────────────────────────────────────────
# Seeded so eval is reproducible. Simulates what would come back from real feeds.

MOCK_ITEMS = [
    {
        "title": "AI 创业公司如何用增长黑客策略获取首批1000用户 [案例复盘]",
        "summary": "某AI SaaS创业团队分享了详细的增长实验数据：通过内容矩阵+私域转化，首月获客成本降低68%。文中附有完整的漏斗数据与AB测试结论。",
        "link": "https://ai-startup.example.com/growth-1000-users",
        "published_offset_hours": 10,
        "source_title": "AI创业内参",
        "is_noise": False,
        "scores": {"relevance": 0.95, "actionability": 0.85, "novelty": 0.80, "evidence": 0.90},
    },
    {
        "title": "金融科技赛道2025年Q2融资地图：哪些方向拿到钱了？",
        "summary": "梳理了2025年Q2已披露的金融科技融资事件，涵盖消费金融、B端SaaS、保险科技三个子赛道，含具体金额与投资方。",
        "link": "https://rss.36kr.com/items/fintech-q2-2025",
        "published_offset_hours": 20,
        "source_title": "36氪融资快讯",
        "is_noise": False,
        "scores": {"relevance": 0.88, "actionability": 0.70, "novelty": 0.75, "evidence": 0.85},
    },
    {
        "title": "努力就会成功！坚持下去创业路上你不孤单",
        "summary": "每天进步一点点，成功终将属于你！加油每一位创业者！",
        "link": "https://motivational.example.com/post-123",
        "published_offset_hours": 5,
        "source_title": "AI创业内参",
        "is_noise": True,
        "noise_reason": "Generic motivational post with no new evidence or data",
        "scores": {"relevance": 0.30, "actionability": 0.10, "novelty": 0.05, "evidence": 0.05},
    },
    {
        "title": "增长实验：用AI写作工具将EDM打开率提升40%的完整SOP",
        "summary": "附可直接复用的Prompt模板和邮件结构，基于500封真实邮件的A/B测试数据。适合0-1阶段SaaS团队。",
        "link": "https://growthhacker.example.com/ai-edm-sop",
        "published_offset_hours": 35,
        "source_title": "增长黑客周报",
        "is_noise": False,
        "scores": {"relevance": 0.90, "actionability": 0.95, "novelty": 0.70, "evidence": 0.88},
    },
    {
        "title": "出海SaaS: 东南亚市场用户调研报告（含付费意愿数据）",
        "summary": "针对越南、印尼、泰国三国共1200名SaaS用户的付费行为调研，揭示本地化定价的关键变量。",
        "link": "https://saasfonder.example.com/sea-research",
        "published_offset_hours": 42,
        "source_title": "SaaS创始人日记",
        "is_noise": False,
        "scores": {"relevance": 0.82, "actionability": 0.78, "novelty": 0.88, "evidence": 0.80},
    },
    {
        "title": "YC W25 Demo Day: 10个最值得关注的AI创业项目",
        "summary": "从商业模式、市场规模、团队背景三个维度点评YC W25批次中AI赛道的top10项目，附创始人LinkedIn和产品demo链接。",
        "link": "https://www.ycombinator.com/blog/yc-w25-ai-picks",
        "published_offset_hours": 8,
        "source_title": "Y Combinator Blog",
        "is_noise": False,
        "scores": {"relevance": 0.85, "actionability": 0.72, "novelty": 0.78, "evidence": 0.70},
    },
    {
        "title": "又一篇谈AI的文章：AI改变了一切（重复观点）",
        "summary": "AI正在改变世界，每个人都应该拥抱AI，不拥抱AI就会被淘汰。这是一个不可逆的趋势。",
        "link": "https://generic.example.com/ai-changes-everything",
        "published_offset_hours": 15,
        "source_title": "Paul Graham Essays",
        "is_noise": True,
        "noise_reason": "Repeated opinion without new evidence",
        "scores": {"relevance": 0.55, "actionability": 0.10, "novelty": 0.05, "evidence": 0.08},
    },
    {
        "title": "金融监管新规解读：2025年支付牌照收紧对创业公司的影响",
        "summary": "详解2025年7月起实施的新支付监管框架，分析对独立开发者和创业公司的合规成本，附律师建议的三种应对路径。",
        "link": "https://jrbgn.example.com/payment-regulation-2025",
        "published_offset_hours": 28,
        "source_title": "金融八卦女",
        "is_noise": False,
        "scores": {"relevance": 0.80, "actionability": 0.82, "novelty": 0.85, "evidence": 0.78},
    },
    {
        "title": "Reddit r/entrepreneur: How I hit $10k MRR with an AI tool for Chinese market",
        "summary": "Detailed breakdown of a solo founder\'s journey building an AI writing tool specifically for Chinese SMBs, including pricing experiments and churn analysis. MRR chart included.",
        "link": "https://www.reddit.com/r/entrepreneur/comments/ai10k-mrr",
        "published_offset_hours": 18,
        "source_title": "Reddit r/entrepreneur",
        "is_noise": False,
        "scores": {"relevance": 0.78, "actionability": 0.88, "novelty": 0.75, "evidence": 0.82},
    },
    {
        "title": "Indie Hackers: Building in public - week 47 update (SaaS metrics)",
        "summary": "Weekly metrics dump: 1240 users, $3.2k MRR, 4.2% churn. Key insight: onboarding video cut churn by 1.8pp. Full cohort table attached.",
        "link": "https://www.indiehackers.com/post/week-47-saas-metrics",
        "published_offset_hours": 30,
        "source_title": "Indie Hackers",
        "is_noise": False,
        "scores": {"relevance": 0.72, "actionability": 0.80, "novelty": 0.65, "evidence": 0.90},
    },
    # Item published 55 hours ago - outside 48h window
    {
        "title": "过期文章：三年前的增长复盘（窗口外）",
        "summary": "这篇文章发布超过48小时，应被时间窗口过滤掉。",
        "link": "https://old.example.com/old-growth",
        "published_offset_hours": 55,
        "source_title": "增长黑客周报",
        "is_noise": False,
        "scores": {"relevance": 0.88, "actionability": 0.80, "novelty": 0.70, "evidence": 0.85},
    },
]

WEIGHTS = {"relevance": 0.40, "actionability": 0.30, "novelty": 0.20, "evidence": 0.10}

def compute_score(scores: dict) -> float:
    return sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

def keyword_match(item: dict, keywords: list[str]) -> bool:
    text = (item["title"] + " " + item["summary"]).lower()
    return any(kw.lower() in text for kw in keywords)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", default="创业,AI,增长,金融")
    parser.add_argument("--feeds", default="assets/feeds.txt")
    parser.add_argument("--hours", type=int, default=48)
    parser.add_argument("--out", default="assets/digest_raw.json")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.hours)

    scanned = 0
    matched = 0
    dropped_noise = []
    candidates = []

    for item in MOCK_ITEMS:
        pub_time = now - timedelta(hours=item["published_offset_hours"])
        if pub_time < cutoff:
            # Outside time window
            continue

        scanned += 1

        if not keyword_match(item, keywords):
            continue

        if item.get("is_noise"):
            dropped_noise.append({
                "title": item["title"],
                "source": item["source_title"],
                "reason": item.get("noise_reason", "Noise"),
            })
            continue

        matched += 1
        score = compute_score(item["scores"])
        candidates.append({
            "title": item["title"],
            "summary": item["summary"],
            "link": item["link"],
            "source": item["source_title"],
            "score": round(score, 4),
            "scores_detail": item["scores"],
            "published_hours_ago": item["published_offset_hours"],
        })

    # Sort by composite score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Hard cap: max 8 items for shortlist (digest kept under 10 total)
    shortlisted = candidates[:8]

    result = {
        "scanned": scanned,
        "matched": matched,
        "shortlisted": len(shortlisted),
        "top3_count": min(3, len(shortlisted)),
        "items": shortlisted,
        "dropped_noise": dropped_noise,
        "keywords_used": keywords,
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build_digest] scanned={result[\'scanned\']} matched={result[\'matched\']} shortlisted={result[\'shortlisted\']} noise_dropped={len(dropped_noise)}")
    print(f"[build_digest] Wrote digest data to {args.out}")

if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "build_digest.py").write_text(build_digest_script, encoding="utf-8")

# ── references/scoring-and-ops.md ────────────────────────────────────────────
scoring_md = """# Scoring and Ops Reference

## Scoring Weights
| Dimension        | Weight |
|------------------|--------|
| Relevance        | 40%    |
| Actionability    | 30%    |
| Novelty          | 20%    |
| Evidence Density | 10%    |

## Filter Pipeline
scanned → matched → shortlisted → top3

## Anti-Noise Rules
- Drop generic motivational content
- Drop repeated opinions without new data
- Prefer concrete case studies with numbers

## Output Cap
- Max 10 items in digest total (top3 + watchlist = max 8)
- Next experiment: exactly 1 concrete operational move

## Cadence
- Morning: 09:30 strategic
- Evening: 18:30 tactical
"""
(workspace / "references" / "scoring-and-ops.md").write_text(scoring_md, encoding="utf-8")

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """---
name: multisource-intel-radar
description: Build and run a high-signal information radar for C-end founders and operators across YouTube, X/Twitter, Reddit, WeChat Official Accounts, and Xiaohongshu. Use when the user wants OPML/RSS ingestion, keyword-whitelist filtering (创业/AI/增长/金融), daily digests, noise reduction, and action-oriented summaries.
---

# Multi-Source Intel Radar

Create a founder-grade signal system: less junk, more decisions.

## Inputs
- OPML file (default: `/Users/rogeryang/Downloads/follow.opml`)
- Keyword whitelist (default: 创业, AI, 增长, 金融)
- Optional source lists for non-RSS channels (X list links, subreddit list, WeChat/XHS accounts)

## Output Contract
Always output:
1. **Top 3 must-read signals** (one-line why + one action + clickable source link)
2. **Top 5 watchlist items** (with source link)
3. **Dropped noise summary** (what got filtered and why)
4. **Filter transparency** (counts + rates: scanned -> matched -> shortlisted -> top3)
5. **Next experiment** (one concrete growth/ops move)

## Workflow

### Step 1) Ingest feed sources
- Parse OPML with `scripts/parse_opml.py`
- Generate normalized feed list: `assets/feeds.txt`

### Step 2) Fetch + filter
- Run `scripts/build_digest.py` with keyword whitelist
- Time window default: last 48h
- Keep only items that match whitelist in title/summary
- For Xiaohongshu: do browser search (not watchlist-dependent), using keyword combos like:
  - 创业 AI 增长
  - AI 产品 复盘
  - 增长运营 案例
  Then append top findings with profile/note links.

### Step 3) Score items
Use this weighted scoring:
- Relevance to whitelist (40%)
- Actionability in 7 days (30%)
- Novelty / non-obviousness (20%)
- Evidence density (10%)

### Step 4) Summarize for execution
For each selected item, provide:
- Core insight (1 sentence)
- Why it matters for current product
- Suggested action today (1 step)

## Source Coverage Notes
- YouTube/X/Reddit often available via RSSHub or platform feeds in OPML
- WeChat OA and Xiaohongshu are often not natively RSS; add via:
  - RSS bridge links (if available)
  - Manual watchlist files (`assets/wechat_watchlist.txt`, `assets/xhs_watchlist.txt`)
- If a source has no feed, include it in watchlist and mark as **manual scan required**

## Anti-Noise Rules
- Do not output generic motivational posts
- Drop repeated观点 without new evidence
- Prefer first-hand data / concrete case over opinion
- Keep digest under 10 items total

## Daily Cadence (recommended)
- 09:30: morning digest (strategic)
- 18:30: evening digest (tactical)

## Keyword Defaults
创业, AI, 增长, 金融

If user provides new keywords, merge and deduplicate.

## Files
- Parser: `scripts/parse_opml.py`
- Digest builder: `scripts/build_digest.py`
- Notes: `references/scoring-and-ops.md`
"""
(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

print("Workspace setup complete.")
print(f"Files created: {list(workspace.rglob('*'))}")