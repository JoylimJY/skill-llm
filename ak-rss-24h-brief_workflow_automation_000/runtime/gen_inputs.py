#!/usr/bin/env python3
"""
Generates the sandbox workspace for the ak-rss-24h-brief evaluation task.
Creates a functional generate_brief.py, a local OPML file, distractor files,
and a mock RSS server script.
"""

import os
import sys
import random
import textwrap
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "feeds/opml",
    "feeds/archive",
    "config",
    "logs",
    "docs",
    "output/drafts",
    "output/published",
    "tools/parsers",
    "tools/formatters",
    "cache/rss",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/settings.yaml": """\
# Application configuration
app_name: rss-aggregator
version: 2.1.0
log_level: INFO
output_dir: ./output
cache_ttl: 3600
max_retries: 3
""",
    "config/categories.json": """\
{
  "categories": ["AI工程", "编程语言", "系统架构", "开源项目", "数据科学"],
  "default": "综合技术"
}
""",
    "docs/brief_format_OLD.md": """\
# DEPRECATED - Old Brief Format (v1)
## Format (v1 - no longer used)
- Title | Link | Summary
- Single line format
This format was replaced in 2024. Do not use.
""",
    "docs/workflow.md": """\
# Editorial Workflow
1. Curate feeds
2. Run aggregation
3. Review output
4. Publish to newsletter
Contact: editorial@company.internal
""",
    "logs/run_2025-01-10.log": """\
2025-01-10 08:00:01 INFO  Starting feed fetch
2025-01-10 08:00:15 INFO  Fetched 47 feeds, 312 articles
2025-01-10 08:00:22 INFO  Filtered to 28 articles in window
2025-01-10 08:00:45 INFO  Brief generated: output/daily_brief_2025-01-10.md
""",
    "logs/errors_2025-01-11.log": """\
2025-01-11 08:01:02 ERROR Feed timeout: https://example-blog.com/rss
2025-01-11 08:01:02 ERROR Feed timeout: https://another-blog.net/atom.xml
2025-01-11 08:01:45 WARN  Only 3 articles found in window, below minimum
""",
    "feeds/archive/brief_2025-01-09.md": """\
# 技术资讯简报（最近 24 小时）

- [RSS Source](https://example.com/old-opml.opml)

## **AI工程**
- [Old Article Title](https://example.com/old-article)
  这是一篇关于旧技术的文章摘要。

---
Overall Summary: 这是旧版本的简报，仅供参考。
""",
    "feeds/archive/brief_2025-01-08.md": """\
# 技术资讯简报（最近 24 小时）

- [RSS Source](https://example.com/old-opml.opml)

## **开源项目**
- [Another Old Article](https://example.com/another-old)
  开源工具相关的技术分析。

---
Overall Summary: 本期聚焦开源生态进展。
""",
    "tools/parsers/opml_validator.py": """\
#!/usr/bin/env python3
# Legacy OPML validator - not used in current pipeline
import xml.etree.ElementTree as ET
def validate(path):
    try:
        ET.parse(path)
        return True
    except ET.ParseError:
        return False
if __name__ == '__main__':
    import sys
    print(validate(sys.argv[1]))
""",
    "tools/formatters/markdown_lint.py": """\
#!/usr/bin/env python3
# Markdown formatter utility - checks heading syntax
import re, sys
def check_headings(text):
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith('##') and not re.match(r'## \\*\\*.*\\*\\*', line):
            issues.append(f'Line {i}: heading not bold-wrapped')
    return issues
""",
    "output/drafts/.gitkeep": "",
    "cache/rss/.gitkeep": "",
}

for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content, encoding="utf-8")

# ── Local OPML file (agent must discover --opml-file parameter) ──────────────
# Points to localhost mock server
opml_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
    <title>Tech Blogs Feed Bundle</title>
  </head>
  <body>
    <outline text="AI Engineering" title="AI Engineering">
      <outline type="rss" text="AI Research Blog" title="AI Research Blog"
               xmlUrl="http://127.0.0.1:18765/feeds/ai-research.xml"
               htmlUrl="http://127.0.0.1:18765/"/>
      <outline type="rss" text="ML Practitioner" title="ML Practitioner"
               xmlUrl="http://127.0.0.1:18765/feeds/ml-practitioner.xml"
               htmlUrl="http://127.0.0.1:18765/"/>
    </outline>
    <outline text="Programming" title="Programming">
      <outline type="rss" text="Systems Dev Blog" title="Systems Dev Blog"
               xmlUrl="http://127.0.0.1:18765/feeds/systems-dev.xml"
               htmlUrl="http://127.0.0.1:18765/"/>
      <outline type="rss" text="Open Source Weekly" title="Open Source Weekly"
               xmlUrl="http://127.0.0.1:18765/feeds/open-source.xml"
               htmlUrl="http://127.0.0.1:18765/"/>
    </outline>
    <outline text="Data Science" title="Data Science">
      <outline type="rss" text="Data Insights" title="Data Insights"
               xmlUrl="http://127.0.0.1:18765/feeds/data-insights.xml"
               htmlUrl="http://127.0.0.1:18765/"/>
    </outline>
  </body>
</opml>
"""
opml_path = workspace / "feeds" / "opml" / "tech_feeds.opml"
opml_path.write_text(opml_content, encoding="utf-8")

# ── Mock RSS server script ────────────────────────────────────────────────────
# Generates RSS feeds with articles dated within last 24 hours
now_utc = datetime.now(timezone.utc)

def rfc822(dt):
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

# Articles per feed – all within last 24h window
feeds_data = {
    "ai-research": {
        "title": "AI Research Blog",
        "link": "http://127.0.0.1:18765/",
        "description": "Latest AI research and engineering",
        "category": "AI Engineering",
        "items": [
            {
                "title": "Scaling Laws Revisited: A Practical Guide for 2025",
                "link": "http://127.0.0.1:18765/articles/scaling-laws-2025",
                "description": "An in-depth analysis of how neural scaling laws apply to modern LLM training runs, with empirical results from recent large-scale experiments showing diminishing returns at extreme scales.",
                "pubdate": rfc822(now_utc - timedelta(hours=3)),
            },
            {
                "title": "Fine-tuning vs RAG: When to Use Which",
                "link": "http://127.0.0.1:18765/articles/finetune-vs-rag",
                "description": "A comprehensive decision framework for choosing between fine-tuning and retrieval-augmented generation, covering cost, latency, accuracy tradeoffs with benchmark results.",
                "pubdate": rfc822(now_utc - timedelta(hours=8)),
            },
            {
                "title": "Attention Mechanism Optimizations in Production",
                "link": "http://127.0.0.1:18765/articles/attention-prod",
                "description": "Practical techniques for reducing attention computation cost in production deployments, including FlashAttention integration and KV-cache management strategies.",
                "pubdate": rfc822(now_utc - timedelta(hours=15)),
            },
        ],
    },
    "ml-practitioner": {
        "title": "ML Practitioner",
        "link": "http://127.0.0.1:18765/",
        "description": "Hands-on machine learning engineering",
        "category": "AI Engineering",
        "items": [
            {
                "title": "Building Reliable ML Pipelines with DVC",
                "link": "http://127.0.0.1:18765/articles/dvc-pipelines",
                "description": "Step-by-step walkthrough of building reproducible machine learning pipelines using DVC, covering data versioning, experiment tracking, and CI/CD integration for model deployment.",
                "pubdate": rfc822(now_utc - timedelta(hours=6)),
            },
            {
                "title": "Model Monitoring in the Wild",
                "link": "http://127.0.0.1:18765/articles/model-monitoring",
                "description": "Real-world strategies for detecting data drift, concept drift, and model degradation in production ML systems, with examples from high-traffic recommendation systems.",
                "pubdate": rfc822(now_utc - timedelta(hours=20)),
            },
        ],
    },
    "systems-dev": {
        "title": "Systems Dev Blog",
        "link": "http://127.0.0.1:18765/",
        "description": "Systems programming and infrastructure",
        "category": "Programming",
        "items": [
            {
                "title": "Async Rust Patterns for High-Performance Services",
                "link": "http://127.0.0.1:18765/articles/async-rust",
                "description": "Deep dive into advanced async Rust patterns for building high-throughput network services, covering tokio runtime internals, backpressure handling, and zero-copy I/O techniques.",
                "pubdate": rfc822(now_utc - timedelta(hours=5)),
            },
            {
                "title": "Linux Kernel Memory Management Explained",
                "link": "http://127.0.0.1:18765/articles/linux-mm",
                "description": "A detailed exploration of the Linux kernel's memory management subsystem, including slab allocator, huge pages, NUMA-aware allocation, and recent improvements in kernel 6.x.",
                "pubdate": rfc822(now_utc - timedelta(hours=18)),
            },
        ],
    },
    "open-source": {
        "title": "Open Source Weekly",
        "link": "http://127.0.0.1:18765/",
        "description": "Open source project highlights",
        "category": "Programming",
        "items": [
            {
                "title": "PostgreSQL 17 New Features Deep Dive",
                "link": "http://127.0.0.1:18765/articles/pg17",
                "description": "Comprehensive review of PostgreSQL 17's major additions including improved logical replication, enhanced JSON functions, better parallel query execution, and significant vacuum performance improvements.",
                "pubdate": rfc822(now_utc - timedelta(hours=12)),
            },
            {
                "title": "The State of WebAssembly in 2025",
                "link": "http://127.0.0.1:18765/articles/wasm-2025",
                "description": "Analysis of WebAssembly ecosystem maturity in 2025, covering component model adoption, WASI preview 2, toolchain improvements, and emerging use cases beyond the browser.",
                "pubdate": rfc822(now_utc - timedelta(hours=22)),
            },
        ],
    },
    "data-insights": {
        "title": "Data Insights",
        "link": "http://127.0.0.1:18765/",
        "description": "Data science and analytics",
        "category": "Data Science",
        "items": [
            {
                "title": "Columnar Storage Formats: Parquet vs Arrow vs ORC",
                "link": "http://127.0.0.1:18765/articles/columnar-formats",
                "description": "Technical comparison of columnar storage formats used in modern data lakes, benchmarking read/write performance, compression ratios, and query engine compatibility across multiple workloads.",
                "pubdate": rfc822(now_utc - timedelta(hours=9)),
            },
            {
                "title": "Feature Store Architecture Patterns",
                "link": "http://127.0.0.1:18765/articles/feature-stores",
                "description": "Survey of production feature store architectures, comparing offline and online serving approaches, consistency guarantees, point-in-time correctness, and integration with training pipelines.",
                "pubdate": rfc822(now_utc - timedelta(hours=21)),
            },
        ],
    },
}

def make_rss(feed_key, feed_info):
    items_xml = ""
    for item in feed_info["items"]:
        items_xml += f"""
    <item>
      <title><![CDATA[{item['title']}]]></title>
      <link>{item['link']}</link>
      <description><![CDATA[{item['description']}]]></description>
      <pubDate>{item['pubdate']}</pubDate>
      <guid>{item['link']}</guid>
    </item>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title><![CDATA[{feed_info['title']}]]></title>
    <link>{feed_info['link']}</link>
    <description><![CDATA[{feed_info['description']}]]></description>
    {items_xml}
  </channel>
</rss>"""

# Write individual RSS files for reference (server will serve these)
rss_dir = workspace / "cache" / "rss"
for key, info in feeds_data.items():
    rss_xml = make_rss(key, info)
    (rss_dir / f"{key}.xml").write_text(rss_xml, encoding="utf-8")

# Write the mock server script
mock_server_script = '''#!/usr/bin/env python3
"""Local mock RSS/feed server for testing."""
import sys
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
RSS_DIR = WORKSPACE / "cache" / "rss"

class FeedHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        path = self.path.lstrip("/")
        if path.startswith("feeds/"):
            fname = path[len("feeds/"):]
            fpath = RSS_DIR / fname
            if fpath.exists():
                content = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18765
    server = HTTPServer(("127.0.0.1", port), FeedHandler)
    print(f"Mock feed server running on 127.0.0.1:{port}", flush=True)
    server.serve_forever()
'''
(workspace / "tools" / "mock_feed_server.py").write_text(mock_server_script, encoding="utf-8")

# ── Main generate_brief.py script ────────────────────────────────────────────
generate_brief_script = r'''#!/usr/bin/env python3
"""
AK RSS 24h Brief Generator
Reads RSS/Atom feeds from an OPML source, fetches articles from the last N hours,
and generates a Chinese categorized brief.
"""

import argparse
import sys
import re
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import time

try:
    import feedparser
    import requests
    from dateutil import parser as dateparser
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    sys.exit(1)


# ── Category mapping heuristics ──────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "AI工程": ["ai", "ml", "machine learning", "neural", "llm", "gpt", "model", "transformer",
               "deep learning", "training", "inference", "embedding", "finetuning", "rag",
               "attention", "scaling", "dataset", "dvc", "monitoring"],
    "编程语言": ["rust", "python", "golang", "java", "kotlin", "swift", "typescript", "c++",
                "async", "concurrency", "compiler", "runtime", "language"],
    "系统架构": ["linux", "kernel", "memory", "distributed", "microservice", "container",
                "kubernetes", "docker", "network", "performance", "latency", "throughput",
                "infrastructure", "cloud"],
    "开源项目": ["postgresql", "postgres", "webassembly", "wasm", "open source", "github",
                "release", "version", "library", "framework", "cli", "tool"],
    "数据科学": ["data", "parquet", "arrow", "orc", "feature store", "pipeline", "analytics",
                "columnar", "lake", "warehouse", "etl", "spark", "dask"],
}


def categorize(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in kws if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "综合技术"


# ── Deterministic Chinese summary generator ──────────────────────────────────
SUMMARY_TEMPLATES = [
    "深入探讨{topic}的核心原理与工程实践，涵盖{aspect}等关键技术点，为相关从业者提供系统性参考。",
    "结合{topic}的最新进展，分析{aspect}的实现路径与权衡取舍，总结可直接应用于生产的优化策略。",
    "从理论与实践角度审视{topic}，重点阐述{aspect}的设计决策与性能影响，提供详尽的基准测试结果。",
    "系统梳理{topic}的发展脉络，聚焦{aspect}领域的新特性与使用场景，具有较强的工程参考价值。",
    "针对{topic}提出全面的技术解析，重点讨论{aspect}中的常见挑战与应对方案，适合有一定背景的技术读者。",
]

TOPIC_MAP = {
    "scaling": "神经网络规模定律",
    "fine-tun": "模型微调与检索增强",
    "rag": "检索增强生成",
    "attention": "注意力机制优化",
    "dvc": "机器学习流水线管理",
    "monitor": "模型生产监控",
    "rust": "异步Rust编程",
    "linux": "Linux内核内存管理",
    "postgres": "PostgreSQL数据库",
    "wasm": "WebAssembly生态",
    "columnar": "列式存储格式",
    "feature": "特征存储架构",
}

ASPECT_MAP = {
    "scaling": "数据量、算力与模型容量的权衡",
    "fine-tun": "成本、延迟与准确率的多维对比",
    "rag": "检索质量与生成一致性",
    "attention": "FlashAttention与KV缓存管理",
    "dvc": "数据版本控制与实验复现",
    "monitor": "数据漂移与概念漂移检测",
    "rust": "Tokio运行时与零拷贝I/O",
    "linux": "Slab分配器与NUMA感知调度",
    "postgres": "逻辑复制与并行查询执行",
    "wasm": "组件模型与WASI工具链",
    "columnar": "读写性能与压缩比基准测试",
    "feature": "在线/离线服务一致性与时间点正确性",
}


def generate_chinese_summary(title: str, description: str, item_link: str) -> str:
    """Generate a deterministic Chinese summary based on article content."""
    text = (title + " " + description).lower()
    
    topic = "相关技术"
    aspect = "核心实现与工程实践"
    
    for key, val in TOPIC_MAP.items():
        if key in text:
            topic = val
            break
    
    for key, val in ASPECT_MAP.items():
        if key in text:
            aspect = val
            break
    
    # Use hash of link to deterministically pick template
    h = int(hashlib.md5(item_link.encode()).hexdigest(), 16)
    template = SUMMARY_TEMPLATES[h % len(SUMMARY_TEMPLATES)]
    
    return template.format(topic=topic, aspect=aspect)


# ── OPML parsing ─────────────────────────────────────────────────────────────
def parse_opml(content: str):
    """Parse OPML XML and return list of (title, xmlUrl) tuples."""
    feeds = []
    try:
        root = ET.fromstring(content)
        for outline in root.iter("outline"):
            xml_url = outline.get("xmlUrl") or outline.get("xmlurl")
            title = outline.get("title") or outline.get("text") or "Unknown"
            if xml_url:
                feeds.append((title, xml_url))
    except ET.ParseError as e:
        print(f"OPML parse error: {e}", file=sys.stderr)
    return feeds


def load_opml(opml_url=None, opml_file=None, timeout=15):
    """Load OPML from URL or file."""
    if opml_file:
        opml_source = opml_file
        with open(opml_file, "r", encoding="utf-8") as f:
            content = f.read()
    elif opml_url:
        opml_source = opml_url
        resp = requests.get(opml_url, timeout=timeout)
        resp.raise_for_status()
        content = resp.text
    else:
        raise ValueError("Must provide --opml-url or --opml-file")
    
    return opml_source, parse_opml(content)


# ── Feed fetching ─────────────────────────────────────────────────────────────
def fetch_feed(title, url, cutoff_dt, timeout=15):
    """Fetch a single RSS/Atom feed and return recent articles."""
    try:
        resp = requests.get(url, timeout=timeout, 
                           headers={"User-Agent": "AK-RSS-Brief/1.0"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        articles = []
        for entry in feed.entries:
            # Try to get published time
            pub = None
            for attr in ("published_parsed", "updated_parsed", "created_parsed"):
                val = getattr(entry, attr, None)
                if val:
                    try:
                        pub = datetime(*val[:6], tzinfo=timezone.utc)
                        break
                    except Exception:
                        pass
            
            if pub is None:
                # Try string parsing
                for attr in ("published", "updated"):
                    val = getattr(entry, attr, None)
                    if val:
                        try:
                            pub = dateparser.parse(val)
                            if pub and pub.tzinfo is None:
                                pub = pub.replace(tzinfo=timezone.utc)
                            break
                        except Exception:
                            pass
            
            if pub is None or pub < cutoff_dt:
                continue
            
            link = getattr(entry, "link", "") or ""
            entry_title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            # Strip HTML tags from summary
            summary = re.sub(r"<[^>]+>", " ", summary).strip()
            
            if entry_title and link:
                articles.append({
                    "title": entry_title,
                    "link": link,
                    "summary": summary,
                    "pub": pub,
                    "feed_title": title,
                })
        return articles
    except Exception as e:
        return []


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate a 24h RSS brief in Chinese")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--opml-url", help="URL of the OPML file")
    group.add_argument("--opml-file", help="Local path to OPML file")
    
    parser.add_argument("--hours", type=int, default=24,
                        help="Time window in hours (default: 24)")
    parser.add_argument("--min-items", type=int, default=5,
                        help="Minimum output items (default: 5)")
    parser.add_argument("--max-items", type=int, default=10,
                        help="Maximum output items (default: 10)")
    parser.add_argument("--timeout", type=int, default=15,
                        help="Network timeout in seconds (default: 15)")
    parser.add_argument("--max-feeds", type=int, default=200,
                        help="Max feeds to fetch (default: 200)")
    parser.add_argument("--workers", type=int, default=10,
                        help="Concurrent workers (default: 10)")
    
    args = parser.parse_args()
    
    if not args.opml_url and not args.opml_file:
        print("Error: must provide --opml-url or --opml-file", file=sys.stderr)
        sys.exit(1)
    
    # Load OPML
    try:
        opml_source, feeds = load_opml(
            opml_url=args.opml_url,
            opml_file=args.opml_file,
            timeout=args.timeout,
        )
    except Exception as e:
        print(f"Failed to load OPML: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not feeds:
        print("No feeds found in OPML", file=sys.stderr)
        sys.exit(1)
    
    # Limit feeds
    feeds = feeds[:args.max_feeds]
    
    # Compute cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    
    # Fetch all feeds concurrently
    all_articles = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_feed, title, url, cutoff, args.timeout): (title, url)
            for title, url in feeds
        }
        for future in as_completed(futures):
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception:
                pass
    
    if len(all_articles) < args.min_items:
        print(f"Warning: only {len(all_articles)} articles found (min: {args.min_items})",
              file=sys.stderr)
        if not all_articles:
            sys.exit(1)
    
    # Sort by pub date descending, cap at max_items
    all_articles.sort(key=lambda a: a["pub"], reverse=True)
    selected = all_articles[:args.max_items]
    
    # Categorize articles
    categorized = {}
    for art in selected:
        cat = categorize(art["title"], art["summary"])
        categorized.setdefault(cat, []).append(art)
    
    # ── Build output ─────────────────────────────────────────────────────────
    lines = []
    lines.append(f"# 技术资讯简报（最近 {args.hours} 小时）")
    lines.append("")
    lines.append(f"- [RSS Source]({opml_source})")
    lines.append("")
    
    for cat_name, articles in categorized.items():
        lines.append(f"## **{cat_name}**")
        for art in articles:
            ch_summary = generate_chinese_summary(art["title"], art["summary"], art["link"])
            lines.append(f"- [{art['title']}]({art['link']})")
            lines.append(f"  {ch_summary}")
            lines.append("")
    
    # Overall summary
    cat_names = "、".join(categorized.keys())
    total = len(selected)
    lines.append("---")
    lines.append(f"Overall Summary: 本期共收录 {total} 篇近 {args.hours} 小时内的技术文章，"
                 f"涵盖 {cat_names} 等方向，聚焦工程实践与前沿技术动态。")
    
    print("\n".join(lines))


if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "generate_brief.py").write_text(generate_brief_script, encoding="utf-8")

# ── Misleading/incomplete config (distractor) ─────────────────────────────────
bad_config = """\
# Attempted brief generation config - INCOMPLETE
# This was an attempt to configure the brief generator but the command is wrong
# DO NOT USE THIS
[brief]
source = feeds/opml/tech_feeds.opml
output = output/brief.txt
format = plain_text
hours = 48
"""
(workspace / "config" / "brief_config_BROKEN.ini").write_text(bad_config, encoding="utf-8")

# Another distractor: a shell script with wrong invocation
wrong_script = """\
#!/bin/bash
# OUTDATED - wrong parameters, do not use
python3 scripts/generate_brief.py \\
  --url feeds/opml/tech_feeds.opml \\
  --window 48 \\
  --limit 20
"""
(workspace / "tools" / "run_brief_OLD.sh").write_text(wrong_script, encoding="utf-8")

print(f"Workspace initialized at {workspace}")
print(f"  - OPML file: {opml_path}")
print(f"  - Script: {workspace / 'scripts' / 'generate_brief.py'}")
print(f"  - Mock server: {workspace / 'tools' / 'mock_feed_server.py'}")
print(f"  - RSS feeds: {rss_dir}")
print(f"  - Distractor files: {len(distractors)}")