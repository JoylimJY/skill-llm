import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "config",
    "config/feeds",
    "config/filters",
    "logs",
    "logs/archive",
    "cache",
    "cache/html",
    "cache/json",
    "output",
    "scripts",
    "scripts/deprecated",
    "templates",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/feeds/rss_old.xml": """<?xml version="1.0"?>
<rss version="2.0">
  <channel><title>Old Feed</title><link>http://example.com</link></channel>
</rss>""",
    "config/feeds/sources_v0.json": json.dumps({
        "version": "0.9",
        "sources": ["http://old-source.com", "http://legacy-news.net"],
        "deprecated": True
    }, indent=2),
    "config/filters/keyword_blacklist.txt": "\n".join([
        "spam", "advertisement", "promoted", "click here", "buy now"
    ]),
    "config/filters/domain_whitelist_draft.txt": "\n".join([
        "# DRAFT - not finalized",
        "techcrunch.com",
        "36kr.com",
        "theverge.com",
    ]),
    "logs/archive/2024-01-15.log": """[INFO] Fetch started
[WARN] Timeout on source: old-military.net
[ERROR] Parse failure on: broken-feed.xml
[INFO] Completed with 3 errors""",
    "logs/run_20240310.log": """Fetched 42 articles
Filtered 18 duplicates
Output written to: /tmp/report_old.md""",
    "cache/html/techcrunch_cache.html": "<html><body><h1>Cache placeholder</h1></body></html>",
    "cache/json/last_run_meta.json": json.dumps({
        "last_run": "2024-03-10T08:00:00Z",
        "articles_fetched": 42,
        "status": "stale"
    }, indent=2),
    "scripts/deprecated/old_fetcher.py": """# DEPRECATED - use new workflow
import urllib.request
def fetch(url):
    return urllib.request.urlopen(url).read()
""",
    "scripts/run_aggregator.sh": """#!/bin/bash
# Placeholder - workflow runner
echo "Starting aggregation..."
python scripts/aggregate.py --config config/feeds/sources.json
""",
    "templates/report_template_draft.md": """# Draft Template (not final)
## Technology
{tech_items}
## Military
{mil_items}
""",
    "data/raw/sample_articles.jsonl": "\n".join([
        json.dumps({"title": "Old article 1", "source": "unknown blog", "date": "2023-01-01"}),
        json.dumps({"title": "Old article 2", "source": "forum post", "date": "2023-06-15"}),
    ]),
    "data/processed/dedup_index.json": json.dumps({
        "hashes": ["abc123", "def456", "ghi789"],
        "last_updated": "2024-01-01"
    }, indent=2),
    "output/.gitkeep": "",
}

for rel_path, content in distractors.items():
    path = workspace / rel_path
    path.write_text(content, encoding="utf-8")

# ── Mock server data (served by Flask in setup) ─────────────────────────────
# This data represents what the mock news sites will serve.
# It intentionally mixes reliable (official/authoritative) and unreliable
# (forum, anonymous, second-hand) sources to test credibility filtering.

mock_news_data = {
    # Domestic Tech sources
    "36kr": {
        "url_path": "/36kr",
        "articles": [
            {
                "title": "阿里巴巴发布新一代AI大模型通义千问3.0",
                "link": "http://localhost:8765/36kr/article/1",
                "source": "36氪",
                "date": "2025-06-10",
                "summary": "阿里巴巴正式发布通义千问3.0，支持200万token上下文，在多项基准测试中超越GPT-4o。",
                "credibility": "official"
            },
            {
                "title": "【论坛爆料】某大厂秘密研发量子芯片？",
                "link": "http://localhost:8765/36kr/article/2",
                "source": "36氪论坛 匿名用户",
                "date": "2025-06-09",
                "summary": "匿名消息称某互联网大厂正在秘密研发量子芯片，尚未得到官方确认。",
                "credibility": "forum_anonymous"
            }
        ]
    },
    "jiqizhixin": {
        "url_path": "/jiqizhixin",
        "articles": [
            {
                "title": "Nature发文：新型神经形态芯片实现人脑级别能效",
                "link": "http://localhost:8765/jiqizhixin/article/1",
                "source": "机器之心",
                "date": "2025-06-10",
                "summary": "研究人员在Nature上发表论文，介绍了一种新型神经形态芯片，能效达到人脑水平，为边缘AI计算带来突破。",
                "credibility": "official"
            }
        ]
    },
    "ithome": {
        "url_path": "/ithome",
        "articles": [
            {
                "title": "华为鸿蒙OS 5.0正式推送：新增AI助手深度集成",
                "link": "http://localhost:8765/ithome/article/1",
                "source": "IT之家",
                "date": "2025-06-11",
                "summary": "华为鸿蒙OS 5.0开始向Mate和P系列旗舰机型推送，新增盘古AI助手深度集成，支持全场景智能调度。",
                "credibility": "official"
            },
            {
                "title": "转载：某博主称小米将发布折叠屏平板",
                "link": "http://localhost:8765/ithome/article/2",
                "source": "IT之家 转载自微博",
                "date": "2025-06-10",
                "summary": "二手转载：据微博博主爆料，小米或将发布折叠屏平板，消息来源未经核实。",
                "credibility": "second_hand"
            }
        ]
    },
    # Domestic Military sources
    "guancha": {
        "url_path": "/guancha",
        "articles": [
            {
                "title": "解放军东部战区组织联合海空演训",
                "link": "http://localhost:8765/guancha/article/1",
                "source": "观察者网",
                "date": "2025-06-11",
                "summary": "中国人民解放军东部战区宣布，近期组织了多兵种联合海空演训，重点演练海上封控和精确打击能力。",
                "credibility": "official"
            }
        ]
    },
    "thepaper": {
        "url_path": "/thepaper",
        "articles": [
            {
                "title": "国防部发言人：中国军队将继续开展正常训练演习",
                "link": "http://localhost:8765/thepaper/article/1",
                "source": "澎湃新闻",
                "date": "2025-06-11",
                "summary": "国防部新闻发言人表示，中国军队将根据年度计划继续开展正常训练演习，维护地区和平稳定。",
                "credibility": "official"
            },
            {
                "title": "【网传】某军事论坛帖子：解放军新型无人机曝光",
                "link": "http://localhost:8765/thepaper/article/2",
                "source": "澎湃 转载 军事论坛",
                "date": "2025-06-10",
                "summary": "来自匿名军事论坛的帖子声称曝光解放军新型隐身无人机，图片真实性存疑，官方未予置评。",
                "credibility": "forum_anonymous"
            }
        ]
    },
    # International Tech sources
    "techcrunch": {
        "url_path": "/techcrunch",
        "articles": [
            {
                "title": "OpenAI Launches GPT-5 with Real-Time Multimodal Reasoning",
                "link": "http://localhost:8765/techcrunch/article/1",
                "source": "TechCrunch",
                "date": "2025-06-11",
                "summary": "OpenAI officially released GPT-5, featuring real-time multimodal reasoning across text, images, and audio, claiming a 40% improvement on benchmark evaluations.",
                "credibility": "official"
            }
        ]
    },
    "theverge": {
        "url_path": "/theverge",
        "articles": [
            {
                "title": "Apple Announces M5 MacBook Pro with 48-hour Battery Life",
                "link": "http://localhost:8765/theverge/article/1",
                "source": "The Verge",
                "date": "2025-06-10",
                "summary": "Apple unveiled the new MacBook Pro powered by the M5 chip, boasting up to 48 hours of battery life and a significantly improved neural engine for on-device AI tasks.",
                "credibility": "official"
            },
            {
                "title": "Rumor: Anonymous source claims Apple to buy Netflix",
                "link": "http://localhost:8765/theverge/article/2",
                "source": "The Verge - Rumor Mill",
                "date": "2025-06-09",
                "summary": "An anonymous industry source claims Apple is in talks to acquire Netflix, but multiple analysts say the rumor is unsubstantiated.",
                "credibility": "forum_anonymous"
            }
        ]
    },
    "arstechnica": {
        "url_path": "/arstechnica",
        "articles": [
            {
                "title": "TSMC Begins Mass Production of 1nm Chips at Arizona Fab",
                "link": "http://localhost:8765/arstechnica/article/1",
                "source": "Ars Technica",
                "date": "2025-06-11",
                "summary": "TSMC announced the start of mass production of 1nm-class chips at its new Arizona facility, marking a major milestone for US semiconductor manufacturing.",
                "credibility": "official"
            }
        ]
    },
    # International Military sources
    "defensenews": {
        "url_path": "/defensenews",
        "articles": [
            {
                "title": "Pentagon Awards $2.5B Contract for Next-Gen Destroyer Program",
                "link": "http://localhost:8765/defensenews/article/1",
                "source": "Defense News",
                "date": "2025-06-11",
                "summary": "The US Department of Defense awarded a $2.5 billion contract to Huntington Ingalls Industries for the DDG(X) next-generation destroyer program, expected to replace aging Arleigh Burke-class vessels.",
                "credibility": "official"
            }
        ]
    },
    "janes": {
        "url_path": "/janes",
        "articles": [
            {
                "title": "UK Royal Air Force Receives First Batch of F-35B Upgrades",
                "link": "http://localhost:8765/janes/article/1",
                "source": "Jane's Defence",
                "date": "2025-06-10",
                "summary": "The UK Royal Air Force has received the first upgraded F-35B aircraft with Block 4 software, enabling expanded weapons integration and enhanced electronic warfare capabilities.",
                "credibility": "official"
            }
        ]
    },
    "militarytimes": {
        "url_path": "/militarytimes",
        "articles": [
            {
                "title": "NATO Expands Eastern Flank with New Rapid Response Brigade",
                "link": "http://localhost:8765/militarytimes/article/1",
                "source": "Military Times",
                "date": "2025-06-11",
                "summary": "NATO announced the activation of a new multinational rapid response brigade in Poland, increasing forward-deployed forces on the Eastern flank amid ongoing security concerns.",
                "credibility": "official"
            },
            {
                "title": "Forum Post: Alleged leaked doc shows secret US weapon specs",
                "link": "http://localhost:8765/militarytimes/article/2",
                "source": "Military Times Forums - Anonymous",
                "date": "2025-06-10",
                "summary": "An anonymous forum post claims to show leaked specifications of a classified US weapon system. Pentagon declined to comment; authenticity unverified.",
                "credibility": "forum_anonymous"
            }
        ]
    }
}

# Save mock data for the Flask server
(workspace / "config" / "mock_news_data.json").write_text(
    json.dumps(mock_news_data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# Write the Flask mock server script
mock_server_script = '''#!/usr/bin/env python3
"""Mock news server - serves fake articles for all sources in SKILL.md"""
import json
import sys
from pathlib import Path
from flask import Flask, jsonify

app = Flask(__name__)

data_path = Path("/workspace/config/mock_news_data.json")
NEWS_DATA = json.loads(data_path.read_text(encoding="utf-8"))

def make_html_page(source_key):
    if source_key not in NEWS_DATA:
        return "<html><body><h1>Not Found</h1></body></html>", 404
    articles = NEWS_DATA[source_key]["articles"]
    items = ""
    for a in articles:
        items += f"""
        <article>
          <h2><a href="{a['link']}">{a['title']}</a></h2>
          <p class="source">Source: {a['source']}</p>
          <p class="date">Date: {a['date']}</p>
          <p class="summary">{a['summary']}</p>
          <p class="credibility">credibility: {a['credibility']}</p>
        </article>"""
    return f"<html><body><h1>News</h1>{items}</body></html>"

@app.route("/36kr")
def route_36kr():
    return make_html_page("36kr")

@app.route("/jiqizhixin")
def route_jiqizhixin():
    return make_html_page("jiqizhixin")

@app.route("/ithome")
def route_ithome():
    return make_html_page("ithome")

@app.route("/guancha")
def route_guancha():
    return make_html_page("guancha")

@app.route("/thepaper")
def route_thepaper():
    return make_html_page("thepaper")

@app.route("/techcrunch")
def route_techcrunch():
    return make_html_page("techcrunch")

@app.route("/theverge")
def route_theverge():
    return make_html_page("theverge")

@app.route("/arstechnica")
def route_arstechnica():
    return make_html_page("arstechnica")

@app.route("/defensenews")
def route_defensenews():
    return make_html_page("defensenews")

@app.route("/janes")
def route_janes():
    return make_html_page("janes")

@app.route("/militarytimes")
def route_militarytimes():
    return make_html_page("militarytimes")

@app.route("/api/all")
def all_data():
    return jsonify(NEWS_DATA)

# Individual article endpoints
@app.route("/<source>/article/<int:idx>")
def article_detail(source, idx):
    if source not in NEWS_DATA:
        return "Not found", 404
    articles = NEWS_DATA[source]["articles"]
    if idx < 1 or idx > len(articles):
        return "Not found", 404
    a = articles[idx-1]
    return f"""<html><body>
    <h1>{a['title']}</h1>
    <p>Source: {a['source']}</p>
    <p>Date: {a['date']}</p>
    <p>{a['summary']}</p>
    <p>credibility: {a['credibility']}</p>
    </body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''

(workspace / "scripts" / "mock_news_server.py").write_text(mock_server_script, encoding="utf-8")

# Write a hosts-override file so the agent can map domain names to localhost
hosts_override = """# Mock server mappings for news aggregator skill
# All SKILL.md domains point to localhost:8765
# Use these paths:
#   36kr        -> http://localhost:8765/36kr
#   jiqizhixin  -> http://localhost:8765/jiqizhixin
#   ithome      -> http://localhost:8765/ithome
#   guancha     -> http://localhost:8765/guancha
#   thepaper    -> http://localhost:8765/thepaper
#   techcrunch  -> http://localhost:8765/techcrunch
#   theverge    -> http://localhost:8765/theverge
#   arstechnica -> http://localhost:8765/arstechnica
#   defensenews -> http://localhost:8765/defensenews
#   janes       -> http://localhost:8765/janes
#   militarytimes -> http://localhost:8765/militarytimes
"""
(workspace / "config" / "mock_server_routes.txt").write_text(hosts_override, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")