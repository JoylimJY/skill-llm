import os
import json
import random

random.seed(42)

base = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "raw_feeds/domestic/tech",
    "raw_feeds/domestic/military",
    "raw_feeds/international/tech",
    "raw_feeds/international/military",
    "archive/2024-01",
    "archive/2024-02",
    "config",
    "logs",
    "templates",
    "scripts",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "config/scraper_config.yaml": "interval: 3600\ntimeout: 30\nretry: 3\n",
    "config/source_list.txt": "36kr\njiqizhixin\nithome\ntechcrunch\ndefensenews\n",
    "logs/scraper_2024-06-01.log": "[INFO] Fetched 36kr: 200 OK\n[INFO] Fetched TechCrunch: 200 OK\n[WARN] jiqizhixin timeout\n",
    "logs/scraper_2024-06-02.log": "[INFO] All sources fetched successfully.\n",
    "archive/2024-01/summary.md": "# January Summary\nNo items archived.\n",
    "archive/2024-02/summary.md": "# February Summary\nNo items archived.\n",
    "templates/report_template.html": "<html><body>{{content}}</body></html>\n",
    "scripts/fetch_36kr.py": "# placeholder fetcher\npass\n",
    "scripts/fetch_techcrunch.py": "# placeholder fetcher\npass\n",
    "tmp/cache.json": '{"last_run": "2024-06-01T00:00:00Z"}\n',
    "tmp/dedup_hashes.txt": "a1b2c3\nd4e5f6\n",
}
for path, content in distractors.items():
    with open(os.path.join(base, path), "w", encoding="utf-8") as f:
        f.write(content)

# --- Raw news feed files (messy, mixed quality) ---

# domestic/tech feeds
domestic_tech_feeds = [
    {
        "source": "36氪",
        "source_url": "https://36kr.com/information/tech/",
        "source_type": "official_media",
        "items": [
            {
                "title": "华为发布新一代昇腾910C芯片，算力提升40%",
                "url": "https://36kr.com/p/2024060101",
                "date": "2024-06-03",
                "summary": "华为正式发布昇腾910C AI训练芯片，官方称相较前代产品算力提升40%，已面向国内云厂商开放采购。",
                "credibility": "high",
                "duplicate_flag": False,
            },
            {
                "title": "字节跳动推出豆包大模型1.5版本",
                "url": "https://36kr.com/p/2024060102",
                "date": "2024-06-02",
                "summary": "字节跳动旗下豆包大模型发布1.5版本，在多项中文推理基准测试中超越同期竞品。",
                "credibility": "high",
                "duplicate_flag": False,
            },
        ],
    },
    {
        "source": "IT之家",
        "source_url": "https://www.ithome.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "小米15系列正式亮相，搭载骁龙8 Gen4",
                "url": "https://www.ithome.com/0/787/001.htm",
                "date": "2024-06-01",
                "summary": "小米正式发布小米15系列手机，全系搭载高通骁龙8 Gen4处理器，支持90W有线快充。",
                "credibility": "high",
                "duplicate_flag": False,
            },
            {
                "title": "【论坛爆料】疑似iPhone 17 Pro渲染图曝光",
                "url": "https://bbs.ithome.com/thread/123456",
                "date": "2024-06-03",
                "summary": "某匿名网友在论坛发帖称获得了iPhone 17 Pro的CAD渲染图，真实性未经证实。",
                "credibility": "low",
                "source_type_override": "forum",
                "duplicate_flag": False,
            },
        ],
    },
    {
        "source": "机器之心",
        "source_url": "https://www.jiqizhixin.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "清华大学发布新型具身智能机器人研究成果",
                "url": "https://www.jiqizhixin.com/articles/2024-06-03",
                "date": "2024-06-03",
                "summary": "清华大学交叉信息研究院发布最新具身智能研究，机器人在复杂操作任务上准确率达92%。",
                "credibility": "high",
                "duplicate_flag": False,
            },
            {
                "title": "字节跳动豆包大模型新版本发布",
                "url": "https://www.jiqizhixin.com/articles/2024-06-02b",
                "date": "2024-06-02",
                "summary": "豆包大模型1.5版本上线，中文理解和代码生成能力有所提升。",
                "credibility": "high",
                "duplicate_flag": True,  # duplicate of 36kr item
            },
        ],
    },
]

# domestic/military feeds
domestic_military_feeds = [
    {
        "source": "观察者网",
        "source_url": "https://www.guancha.cn/",
        "source_type": "official_media",
        "items": [
            {
                "title": "解放军在南海举行例行军事演习",
                "url": "https://www.guancha.cn/military/2024_06_03_001.shtml",
                "date": "2024-06-03",
                "summary": "中国人民解放军南部战区在南海相关海域组织例行性军事演练，相关部门发布航行警告。",
                "credibility": "high",
                "duplicate_flag": False,
            },
        ],
    },
    {
        "source": "澎湃新闻",
        "source_url": "https://www.thepaper.cn/",
        "source_type": "official_media",
        "items": [
            {
                "title": "国产航母山东舰完成年度战备训练任务",
                "url": "https://www.thepaper.cn/newsDetail_forward_2024060301",
                "date": "2024-06-03",
                "summary": "据国防部官方发布，山东舰航母编队圆满完成2024年度第一阶段战备训练任务，整体作战能力稳步提升。",
                "credibility": "high",
                "duplicate_flag": False,
            },
            {
                "title": "【网帖转载】某不知名博主称亲眼目睹新型舰艇下水",
                "url": "https://www.thepaper.cn/newsDetail_forward_2024060302",
                "date": "2024-06-02",
                "summary": "二手转载自微博某匿名账号，内容真实性无法核实，原帖已被删除。",
                "credibility": "low",
                "source_type_override": "anonymous_secondhand",
                "duplicate_flag": False,
            },
        ],
    },
]

# international/tech feeds
international_tech_feeds = [
    {
        "source": "TechCrunch",
        "source_url": "https://techcrunch.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "OpenAI Announces GPT-5 with Extended Context Window",
                "url": "https://techcrunch.com/2024/06/03/openai-gpt5-announcement",
                "date": "2024-06-03",
                "summary": "OpenAI officially unveiled GPT-5, featuring a 2M token context window and improved multi-step reasoning capabilities.",
                "credibility": "high",
                "duplicate_flag": False,
            },
        ],
    },
    {
        "source": "The Verge",
        "source_url": "https://www.theverge.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "Apple Intelligence Features Delayed to iOS 18.2",
                "url": "https://www.theverge.com/2024/6/3/apple-intelligence-delay",
                "date": "2024-06-03",
                "summary": "Apple confirmed that key AI features branded as 'Apple Intelligence' will ship in iOS 18.2, not the initial iOS 18.0 release.",
                "credibility": "high",
                "duplicate_flag": False,
            },
            {
                "title": "OpenAI GPT-5 Drops with Massive Context Support",
                "url": "https://www.theverge.com/2024/6/3/openai-gpt5",
                "date": "2024-06-03",
                "summary": "OpenAI's latest model GPT-5 is now available, boasting a 2 million token context and better reasoning.",
                "credibility": "high",
                "duplicate_flag": True,  # duplicate of TechCrunch item
            },
        ],
    },
    {
        "source": "Ars Technica",
        "source_url": "https://arstechnica.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "TSMC Begins Mass Production of 2nm Chips Ahead of Schedule",
                "url": "https://arstechnica.com/tech-policy/2024/06/tsmc-2nm-production",
                "date": "2024-06-02",
                "summary": "TSMC announced it has begun volume production of 2nm process node chips, approximately two months ahead of analyst expectations.",
                "credibility": "high",
                "duplicate_flag": False,
            },
        ],
    },
]

# international/military feeds
international_military_feeds = [
    {
        "source": "Defense News",
        "source_url": "https://www.defensenews.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "US Navy Awards $2.8B Contract for Next-Gen Destroyer Program",
                "url": "https://www.defensenews.com/naval/2024/06/03/us-navy-destroyer-contract",
                "date": "2024-06-03",
                "summary": "The US Navy has awarded a $2.8 billion contract to Bath Iron Works for the construction of two DDG(X) next-generation destroyers.",
                "credibility": "high",
                "duplicate_flag": False,
            },
        ],
    },
    {
        "source": "Military Times",
        "source_url": "https://www.militarytimes.com/",
        "source_type": "official_media",
        "items": [
            {
                "title": "NATO Announces Largest Air Defense Exercise Since Cold War",
                "url": "https://www.militarytimes.com/news/2024/06/03/nato-air-defense-exercise",
                "date": "2024-06-03",
                "summary": "NATO launched 'Baltic Shield 2024', its largest coordinated air defense exercise since the Cold War, involving 24 member nations.",
                "credibility": "high",
                "duplicate_flag": False,
            },
            {
                "title": "【Anonymous Forum Post】Leaked: Secret US Weapons Deployment Plans",
                "url": "https://reddit.com/r/conspiracy/2024/leaked-weapons-plans",
                "date": "2024-06-01",
                "summary": "An anonymous user on Reddit claims to have leaked documents about secret US weapons deployment. No official source has confirmed this.",
                "credibility": "low",
                "source_type_override": "forum_anonymous",
                "duplicate_flag": False,
            },
        ],
    },
]

# Write feed files
feed_map = {
    "raw_feeds/domestic/tech/feeds.json": domestic_tech_feeds,
    "raw_feeds/domestic/military/feeds.json": domestic_military_feeds,
    "raw_feeds/international/tech/feeds.json": international_tech_feeds,
    "raw_feeds/international/military/feeds.json": international_military_feeds,
}

for rel_path, data in feed_map.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Write a messy mixed-format file with some already-processed but oddly formatted items
mixed_raw = """SOURCE: Wired
URL: https://www.wired.com/story/google-deepmind-alphafold3-proteins
DATE: 2024-06-02
TITLE: Google DeepMind's AlphaFold 3 Predicts Drug Interactions with Unprecedented Accuracy
SUMMARY: DeepMind announced AlphaFold 3, capable of modeling interactions between proteins and small drug molecules, potentially transforming pharmaceutical research.
CREDIBILITY: high
CATEGORY: tech
---
SOURCE: Jane's Defence
URL: https://www.janes.com/defence-news/2024/06/02/ukraine-receives-f16s
DATE: 2024-06-02
TITLE: Ukraine Officially Receives First Batch of F-16 Fighter Jets
SUMMARY: Ukraine confirmed delivery of the first operational F-16 aircraft from allied nations, marking a significant milestone in Western military support.
CREDIBILITY: high
CATEGORY: military
---
SOURCE: anonymous_blog
URL: https://somerandomblog.net/military-insider-claims
DATE: 2024-06-03
TITLE: INSIDER CLAIMS: Secret military operation underway
SUMMARY: An anonymous blogger claims insider knowledge of a secret military operation. No corroborating sources.
CREDIBILITY: low
CATEGORY: military
---
SOURCE: 量子位
URL: https://www.1baijia.com/article/2024060301
DATE: 2024-06-03
TITLE: 国内首个万亿参数大模型通过可信AI认证
SUMMARY: 由国内头部AI公司联合发布的万亿参数大模型正式通过中国信通院可信AI认证，标志着国产大模型进入新阶段。
CREDIBILITY: high
CATEGORY: tech
"""
with open(os.path.join(base, "raw_feeds/mixed_sources.txt"), "w", encoding="utf-8") as f:
    f.write(mixed_raw)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for fname in files:
        print(os.path.join(root, fname).replace(base, ""))