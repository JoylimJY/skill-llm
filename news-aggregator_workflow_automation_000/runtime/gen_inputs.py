import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "archives/2024/Q1/raw",
    "archives/2024/Q2/raw",
    "archives/2024/Q3/processed",
    "archives/2024/Q4/processed",
    "config/sources",
    "config/filters",
    "logs/fetcher",
    "logs/processor",
    "drafts/tech",
    "drafts/military",
    "templates",
    "cache/html",
    "cache/json",
    "scripts/helpers",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "config/sources/old_sources.yaml": """
sources:
  - name: Reuters
    url: http://reuters.com
    category: international
  - name: BBC
    url: http://bbc.com
    category: international
""",
    "config/sources/deprecated.json": json.dumps({
        "version": "0.9",
        "sources": ["cnn.com", "fox.com"],
        "note": "deprecated as of v1.0"
    }, indent=2),
    "config/filters/keywords_old.txt": "\n".join([
        "missile", "satellite", "AI", "chip", "warfare",
        "semiconductor", "drone", "cybersecurity"
    ]),
    "logs/fetcher/fetch_2024_01.log": "\n".join([
        "[2024-01-15 08:00:01] INFO Fetching 36kr...",
        "[2024-01-15 08:00:03] INFO Success: 12 articles",
        "[2024-01-15 08:00:05] WARN Timeout: jiqizhixin.com",
        "[2024-01-15 08:00:07] INFO Fetching guancha.cn...",
        "[2024-01-15 08:00:09] INFO Success: 8 articles",
    ]),
    "logs/processor/proc_2024_01.log": "\n".join([
        "[2024-01-15 09:00:01] INFO Processing batch 1",
        "[2024-01-15 09:00:02] INFO Filtered 3 duplicates",
        "[2024-01-15 09:00:03] INFO Output written to archives/2024/Q1/raw/output.md",
    ]),
    "archives/2024/Q1/raw/output.md": """## 科技新闻

1. [旧文章标题](http://example.com/old1)
   来源：36氪 | 时间：2024-01-15
   要点：这是一条旧的科技新闻要点示例。

## 军事新闻

1. [旧军事新闻](http://example.com/old2)
   来源：观察者网 | 时间：2024-01-15
   要点：这是一条旧的军事新闻要点示例。
""",
    "drafts/tech/notes.txt": "Draft notes: AI chip exports, TSMC capacity update, OpenAI partnership",
    "drafts/military/notes.txt": "Draft notes: South China Sea patrol, NATO exercises, hypersonic test",
    "templates/briefing_template.txt": """[TEMPLATE - DO NOT USE DIRECTLY]
Date: {date}
Prepared by: {author}
Section: {section}
""",
    "cache/json/last_run.json": json.dumps({
        "last_run": "2024-11-01T06:00:00Z",
        "articles_fetched": 45,
        "articles_filtered": 12,
        "output_file": "daily_briefing.md"
    }, indent=2),
    "cache/html/placeholder.txt": "HTML cache placeholder - cache expired",
    "scripts/helpers/dedup.py": """# Deduplication helper (legacy)
def dedup(articles):
    seen = set()
    result = []
    for a in articles:
        key = a.get('title','')
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result
""",
    "archives/2024/Q3/processed/summary.json": json.dumps({
        "period": "2024-Q3",
        "total_articles": 180,
        "tech": 95,
        "military": 85,
        "sources_used": ["36kr", "guancha", "techcrunch", "defensenews"]
    }, indent=2),
    "archives/2024/Q4/processed/summary.json": json.dumps({
        "period": "2024-Q4",
        "total_articles": 210,
        "tech": 120,
        "military": 90,
        "sources_used": ["36kr", "jiqizhixin", "ithome", "thepaper", "wired", "arsTechnica"]
    }, indent=2),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ─── Mock server data file ───────────────────────────────────────────────────
# This file is read by the mock Flask server at runtime.
# It contains a realistic, mixed-quality set of articles:
#   - authoritative articles (should be INCLUDED)
#   - forum posts / anonymous / second-hand (should be EXCLUDED)

mock_data = {
    "tech": [
        {
            "title": "华为发布最新麒麟芯片，性能大幅提升",
            "url": "https://36kr.com/p/100001",
            "source": "36氪",
            "time": "2025-06-10",
            "summary": "华为正式发布麒麟X90芯片，采用3nm制程，性能较上代提升40%，主要用于旗舰手机系列。",
            "credibility": "authoritative"
        },
        {
            "title": "OpenAI推出GPT-5模型，推理能力突破性进展",
            "url": "https://techcrunch.com/2025/06/10/openai-gpt5",
            "source": "TechCrunch",
            "time": "2025-06-10",
            "summary": "OpenAI发布GPT-5，在数学推理和代码生成基准测试中均超越人类专家水平。",
            "credibility": "authoritative"
        },
        {
            "title": "【论坛爆料】某大厂内部正在秘密研发量子计算机，消息来源匿名",
            "url": "https://bbs.techforum.cn/post/88888",
            "source": "论坛帖子",
            "time": "2025-06-09",
            "summary": "匿名网友称某科技巨头正在秘密研发量子计算机，但未提供任何证据。",
            "credibility": "forum"
        },
        {
            "title": "英伟达H200 GPU出货量创历史新高",
            "url": "https://www.theverge.com/2025/06/10/nvidia-h200",
            "source": "The Verge",
            "time": "2025-06-10",
            "summary": "英伟达表示H200 GPU第二季度出货量达到历史峰值，数据中心需求持续强劲。",
            "credibility": "authoritative"
        },
        {
            "title": "听说苹果要出折叠屏了？网友转发朋友圈截图",
            "url": "https://weibo.com/rumors/apple-fold-2025",
            "source": "二手转载",
            "time": "2025-06-08",
            "summary": "网传苹果将发布折叠屏手机，但该消息来源于一条朋友圈截图，真实性存疑。",
            "credibility": "secondhand"
        },
        {
            "title": "机器之心：大模型在医疗影像诊断中准确率超过90%",
            "url": "https://www.jiqizhixin.com/articles/2025-06-10-medical-ai",
            "source": "机器之心",
            "time": "2025-06-10",
            "summary": "最新研究显示，基于Transformer架构的医疗影像大模型在肺癌筛查准确率达92.3%。",
            "credibility": "authoritative"
        },
        {
            "title": "匿名知情人士：某半导体公司即将宣布重大裁员",
            "url": "https://anonymous.leak-site.net/semi-layoff",
            "source": "匿名消息",
            "time": "2025-06-09",
            "summary": "匿名消息称某半导体企业将在本月底裁员30%，公司未予置评。",
            "credibility": "anonymous"
        },
    ],
    "military": [
        {
            "title": "解放军在南海举行大规模联合演习",
            "url": "https://www.guancha.cn/military/2025_06_10_exercise",
            "source": "观察者网",
            "time": "2025-06-10",
            "summary": "中国人民解放军在南海组织多兵种联合演习，重点演练登陆作战和防空作战科目。",
            "credibility": "authoritative"
        },
        {
            "title": "美国国防部宣布向台湾出售最新型防空导弹系统",
            "url": "https://www.defensenews.com/2025/06/10/us-taiwan-missiles",
            "source": "Defense News",
            "time": "2025-06-10",
            "summary": "五角大楼宣布批准向台湾出售价值19亿美元的PAC-3 MSE防空导弹系统。",
            "credibility": "authoritative"
        },
        {
            "title": "军事论坛网友称亲眼目睹新型隐形战机试飞，图片模糊",
            "url": "https://lt.cjdby.net/thread/stealth-jet-sighting",
            "source": "论坛帖子",
            "time": "2025-06-09",
            "summary": "论坛用户发帖称在某地目击新型隐形战机，附图片模糊，未经官方证实。",
            "credibility": "forum"
        },
        {
            "title": "北约举行年度最大规模军事演习，参与兵力逾10万",
            "url": "https://www.militarytimes.com/2025/06/10/nato-exercise",
            "source": "Military Times",
            "time": "2025-06-10",
            "summary": "北约在东欧举行代号'钢铁盾牌2025'的年度军演，共32个成员国超10万名士兵参与。",
            "credibility": "authoritative"
        },
        {
            "title": "转发：据说俄罗斯正在开发新型核动力无人潜艇（来源：某Telegram频道）",
            "url": "https://t.me/mil_rumors/20250609",
            "source": "二手转载",
            "time": "2025-06-09",
            "summary": "Telegram军事频道流传消息称俄研发核动力UUV，未经任何官方渠道确认。",
            "credibility": "secondhand"
        },
        {
            "title": "澎湃新闻：中国新型055型驱逐舰完成首次远海训练任务",
            "url": "https://www.thepaper.cn/newsDetail_forward_055destroyer",
            "source": "澎湃新闻",
            "time": "2025-06-10",
            "summary": "055型万吨级驱逐舰编队圆满完成为期60天的首次远洋训练，标志着海军远海作战能力新突破。",
            "credibility": "authoritative"
        },
    ]
}

mock_data_path = os.path.join(workspace, "config", "mock_news_data.json")
with open(mock_data_path, "w", encoding="utf-8") as f:
    json.dump(mock_data, f, ensure_ascii=False, indent=2)

# Write the mock server script
mock_server_script = '''#!/usr/bin/env python3
"""
Mock News Aggregator Server
Simulates the news source endpoints defined in SKILL.md
"""
import json
import os
from flask import Flask, jsonify, Response

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "../config/mock_news_data.json")

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ── Domestic Tech Sources ──────────────────────────────────────────
@app.route("/36kr/tech")
def kr36_tech():
    data = load_data()
    articles = [a for a in data["tech"] if "36kr" in a["url"] or "36氪" in a["source"]]
    return jsonify({"source": "36氪", "articles": articles})

@app.route("/jiqizhixin")
def jiqizhixin():
    data = load_data()
    articles = [a for a in data["tech"] if "jiqizhixin" in a["url"]]
    return jsonify({"source": "机器之心", "articles": articles})

# ── Domestic Military Sources ──────────────────────────────────────
@app.route("/guancha")
def guancha():
    data = load_data()
    articles = [a for a in data["military"] if "guancha" in a["url"]]
    return jsonify({"source": "观察者网", "articles": articles})

@app.route("/thepaper")
def thepaper():
    data = load_data()
    articles = [a for a in data["military"] if "thepaper" in a["url"]]
    return jsonify({"source": "澎湃新闻", "articles": articles})

# ── International Tech Sources ─────────────────────────────────────
@app.route("/techcrunch")
def techcrunch():
    data = load_data()
    articles = [a for a in data["tech"] if "techcrunch" in a["url"]]
    return jsonify({"source": "TechCrunch", "articles": articles})

@app.route("/theverge")
def theverge():
    data = load_data()
    articles = [a for a in data["tech"] if "theverge" in a["url"]]
    return jsonify({"source": "The Verge", "articles": articles})

# ── International Military Sources ────────────────────────────────
@app.route("/defensenews")
def defensenews():
    data = load_data()
    articles = [a for a in data["military"] if "defensenews" in a["url"]]
    return jsonify({"source": "Defense News", "articles": articles})

@app.route("/militarytimes")
def militarytimes():
    data = load_data()
    articles = [a for a in data["military"] if "militarytimes" in a["url"]]
    return jsonify({"source": "Military Times", "articles": articles})

# ── Mixed / All ────────────────────────────────────────────────────
@app.route("/all/tech")
def all_tech():
    data = load_data()
    return jsonify({"category": "tech", "articles": data["tech"]})

@app.route("/all/military")
def all_military():
    data = load_data()
    return jsonify({"category": "military", "articles": data["military"]})

@app.route("/all")
def all_articles():
    data = load_data()
    return jsonify(data)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "mock-news-aggregator"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''

mock_server_path = os.path.join(workspace, "scripts", "mock_news_server.py")
with open(mock_server_path, "w", encoding="utf-8") as f:
    f.write(mock_server_script)

# Write SKILL.md into workspace (as the agent's reference)
skill_md = """---
name: news-aggregator
version: 1.0.3
description: 国内外社会、科技、军事新闻汇总。自动搜索、筛选、整理新闻要点。
license: MIT
---

# News Aggregator

聚合国内外社会、科技、军事新闻，自动筛选要点。

## 新闻源

### 国内科技
- 36氪 (https://36kr.com/information/tech/)
- 机器之心 (https://www.jiqizhixin.com/)
- 量子位 (https://www.1baijia.com/)
- IT之家 (https://www.ithome.com/)

### 国内军事
- 观察者网 (https://www.guancha.cn/)
- 澎湃新闻 (https://www.thepaper.cn/)
- 腾讯军事 (https://new.qq.com/om/mil/)

### 国际科技
- TechCrunch
- The Verge
- Wired
- Ars Technica

### 国际军事
- Defense News
- Jane's Defence
- Military Times

## 工作流

1. **搜索** - 用 tavily 或 web_fetch 搜索各源
2. **筛选** - 过滤重复、过期、不可靠来源
3. **整理** - 按类别整理，每条含标题、来源、要点
4. **输出** - 生成结构化汇总

## 可信度规则

**优先：**
- 官方媒体报道
- 权威机构发布

**谨慎：**
- 论坛帖子
- 匿名消息
- 二手转载

## 输出格式

```markdown
## 科技新闻

1. [标题](链接)
   来源：xxx | 时间：xxx
   要点：xxx

## 军事新闻

1. [标题](链接)
   来源：xxx | 时间：xxx
   要点：xxx
```
"""

skill_md_path = os.path.join(workspace, "SKILL.md")
with open(skill_md_path, "w", encoding="utf-8") as f:
    f.write(skill_md)

print("Workspace generated successfully.")
print(f"Mock data: {mock_data_path}")
print(f"Mock server: {mock_server_path}")