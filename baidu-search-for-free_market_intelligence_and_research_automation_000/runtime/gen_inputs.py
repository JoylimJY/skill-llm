import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── 1. Mock baidusearch package ──────────────────────────────────────────────
os.makedirs(f"{BASE}/baidusearch", exist_ok=True)

with open(f"{BASE}/baidusearch/__init__.py", "w") as f:
    f.write("")

# The mock search returns deterministic results keyed by query
mock_search_module = textwrap.dedent('''
import re

_MOCK_DB = {
    "新能源汽车市场份额": [
        {"title": "2024年中国新能源汽车市场份额分析报告", "abstract": "2024年中国新能源汽车市场份额持续扩大，比亚迪领跑全球...", "url": "http://mock.local/article/nev-market-2024", "rank": 1},
        {"title": "新能源汽车销量排行榜TOP10", "abstract": "最新数据显示，新能源汽车渗透率已突破40%，多品牌竞争格局形成...", "url": "http://mock.local/article/nev-top10", "rank": 2},
        {"title": "比亚迪vs特斯拉：中国市场争夺战", "abstract": "比亚迪在中国市场以绝对优势领先，特斯拉份额有所下滑...", "url": "http://mock.local/article/byd-vs-tesla", "rank": 3},
        {"title": "新能源补贴政策2024最新解读", "abstract": "国家对新能源汽车的补贴政策进行了调整，购置税减免延续...", "url": "http://mock.local/article/nev-policy", "rank": 4},
        {"title": "造车新势力季度交付量汇总", "abstract": "蔚来、小鹏、理想三家新势力季度交付量创历史新高...", "url": "http://mock.local/article/newforce-delivery", "rank": 5},
        {"title": "传统车企转型新能源进展报告", "abstract": "大众、丰田等传统车企加速新能源转型，电动化进程提速...", "url": "http://mock.local/article/legacy-nev", "rank": 6},
        {"title": "充电桩基础设施建设现状", "abstract": "截至2024年，全国充电桩数量超过800万个，公共桩密度提升...", "url": "http://mock.local/article/charging-infra", "rank": 7},
        {"title": "新能源汽车出口数据分析", "abstract": "中国新能源汽车出口量大幅增长，欧洲和东南亚成为主要市场...", "url": "http://mock.local/article/nev-export", "rank": 8},
    ],
    "智能家居市场竞争格局": [
        {"title": "2024智能家居市场规模与竞争格局", "abstract": "智能家居市场规模突破5000亿元，小米、华为、阿里争相布局...", "url": "http://mock.local/article/smarthome-market", "rank": 1},
        {"title": "小米智能家居生态链深度解析", "abstract": "小米米家生态链产品覆盖率全面，AIoT设备连接数超7亿...", "url": "http://mock.local/article/xiaomi-smarthome", "rank": 2},
        {"title": "华为全屋智能解决方案评测", "abstract": "华为全屋智能以鸿蒙OS为核心，打造统一智能家居平台...", "url": "http://mock.local/article/huawei-smarthome", "rank": 3},
        {"title": "智能家居标准互通问题待解", "abstract": "Matter协议推进，但各厂商生态壁垒依然显著...", "url": "http://mock.local/article/smarthome-standard", "rank": 4},
        {"title": "海外品牌在华智能家居市场遇冷", "abstract": "亚马逊、Google等海外品牌在华份额持续萎缩...", "url": "http://mock.local/article/overseas-smarthome", "rank": 5},
    ],
}

_MOCK_PAGES = {
    "http://mock.local/article/nev-market-2024": {
        "title": "2024年中国新能源汽车市场份额分析报告",
        "text": "根据中国汽车工业协会最新发布的数据，2024年上半年中国新能源汽车销量达到494.4万辆，同比增长32%。其中，比亚迪以绝对优势占据市场份额第一位，累计销量超过160万辆。新能源汽车渗透率已从2023年底的35.7%提升至2024年6月的41.1%。\\n\\n从细分市场来看，纯电动汽车（BEV）销量为356万辆，插电混动（PHEV）销量为138万辆，PHEV增速显著高于BEV。价格带分布上，15-25万元区间竞争最为激烈，特斯拉Model 3、比亚迪海豹、小鹏P7等产品在此区间形成直接竞争。\\n\\n政策层面，2024年新能源汽车购置税减免政策延续，对10万元以下新能源乘用车给予全额免税，有效刺激了入门级市场需求。行业预测，2024年全年新能源汽车销量有望突破1100万辆。"
    },
    "http://mock.local/article/nev-top10": {
        "title": "新能源汽车销量排行榜TOP10",
        "text": "2024年上半年新能源汽车单月销量TOP10品牌排名如下：1. 比亚迪 26.8万辆，2. 特斯拉中国 7.2万辆，3. 五菱汽车 6.1万辆，4. 吉利汽车 5.9万辆，5. 理想汽车 4.7万辆，6. 问界 4.3万辆，7. 蔚来 2.1万辆，8. 小鹏 1.9万辆，9. 零跑 1.8万辆，10. 深蓝汽车 1.7万辆。"
    },
    "http://mock.local/article/byd-vs-tesla": {
        "title": "比亚迪vs特斯拉：中国市场争夺战",
        "text": "2024年，比亚迪在中国市场的份额持续巩固。数据显示，比亚迪在国内新能源市场占有率约为34%，而特斯拉中国约为8.5%。比亚迪依靠完整的垂直整合产业链，在成本控制上具备明显优势，其刀片电池技术和DM-i超级混动技术获得市场高度认可。"
    },
    "http://mock.local/article/smarthome-market": {
        "title": "2024智能家居市场规模与竞争格局",
        "text": "2024年中国智能家居市场规模预计达到5823亿元，同比增长18.3%。市场格局呈现明显的寡头竞争态势：小米以生态链模式占据最大份额，华为凭借鸿蒙操作系统构建统一平台，阿里巴巴天猫精灵生态也保持稳定增长。行业痛点在于各平台互联互通标准不统一，用户体验碎片化问题仍待解决。"
    },
    "http://mock.local/article/xiaomi-smarthome": {
        "title": "小米智能家居生态链深度解析",
        "text": "小米米家平台截至2024年Q2已接入AIoT设备超过7.3亿台，活跃用户突破8000万。生态链涵盖照明、家电、安防、健康等多个品类，形成完整的智能家居闭环体验。小米智能家居的核心优势在于其高性价比定位和庞大的用户基础。"
    },
}

def search(query, num_results=10):
    """Mock Baidu search returning deterministic results."""
    matched = None
    for key in _MOCK_DB:
        if key in query or query in key:
            matched = _MOCK_DB[key]
            break
    if matched is None:
        # Return generic fallback
        matched = [
            {"title": f"关于{query}的搜索结果{i+1}", "abstract": f"这是关于{query}的第{i+1}条摘要信息。", "url": f"http://mock.local/article/generic-{i+1}", "rank": i+1}
            for i in range(10)
        ]
    return matched[:num_results]

def fetch_page(url):
    """Mock fetch returning page data by URL."""
    if url in _MOCK_PAGES:
        return _MOCK_PAGES[url]
    return {"title": f"Page at {url}", "text": f"Content from {url}. This page contains information relevant to the search query."}
''')

with open(f"{BASE}/baidusearch/baidusearch.py", "w") as f:
    f.write(mock_search_module)

# ── 2. scripts/ directory with required tools ────────────────────────────────
os.makedirs(f"{BASE}/scripts", exist_ok=True)

# scripts/baidu_search.py
baidu_search_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """百度搜索脚本，支持命令行参数调用"""
    import argparse
    import json
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from baidusearch.baidusearch import search

    def main():
        parser = argparse.ArgumentParser(description="百度搜索")
        parser.add_argument("query", help="搜索关键词")
        parser.add_argument("--num", type=int, default=10, help="返回结果数量")
        args = parser.parse_args()

        results = search(args.query, num_results=args.num)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    if __name__ == "__main__":
        main()
''')

with open(f"{BASE}/scripts/baidu_search.py", "w") as f:
    f.write(baidu_search_script)

# scripts/fetch_url.py
fetch_url_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """网页内容抓取和解析脚本"""
    import argparse
    import json
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from baidusearch.baidusearch import fetch_page

    def fetch_url(url, max_chars=None):
        """获取并解析网页内容"""
        data = fetch_page(url)
        if max_chars and data.get("text"):
            data = dict(data)
            data["text"] = data["text"][:max_chars]
        return data

    def main():
        parser = argparse.ArgumentParser(description="网页内容抓取")
        parser.add_argument("url", help="目标URL")
        parser.add_argument("--max-chars", type=int, default=None, help="最大字符数")
        args = parser.parse_args()

        content = fetch_url(args.url, max_chars=args.max_chars)
        print(json.dumps(content, ensure_ascii=False, indent=2))

    if __name__ == "__main__":
        main()
''')

with open(f"{BASE}/scripts/fetch_url.py", "w") as f:
    f.write(fetch_url_script)

# scripts/search_and_fetch.py
search_and_fetch_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """搜索并自动解析网页内容的完整流程脚本"""
    import argparse
    import json
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from baidusearch.baidusearch import search
    from scripts.fetch_url import fetch_url

    def main():
        parser = argparse.ArgumentParser(description="搜索并解析网页")
        parser.add_argument("query", help="搜索关键词")
        parser.add_argument("--num", type=int, default=5, help="搜索结果数量")
        args = parser.parse_args()

        results = search(args.query, num_results=args.num)
        output = []
        for r in results:
            page = fetch_url(r["url"])
            output.append({
                "rank": r["rank"],
                "search_title": r["title"],
                "search_abstract": r["abstract"],
                "url": r["url"],
                "page_title": page.get("title", ""),
                "page_text_preview": page.get("text", "")[:300]
            })
        print(json.dumps(output, ensure_ascii=False, indent=2))

    if __name__ == "__main__":
        main()
''')

with open(f"{BASE}/scripts/search_and_fetch.py", "w") as f:
    f.write(search_and_fetch_script)

# ── 3. Distractor files ───────────────────────────────────────────────────────

# config/
with open(f"{BASE}/config/app_config.json", "w") as f:
    json.dump({"version": "1.2.3", "search_timeout": 30, "max_retries": 3, "encoding": "utf-8"}, f, indent=2)

with open(f"{BASE}/config/keywords.txt", "w") as f:
    f.write("新能源汽车\n智能家居\n人工智能\n云计算\n区块链\n")

# data/
with open(f"{BASE}/data/previous_search_log.csv", "w") as f:
    f.write("date,query,num_results,status\n")
    f.write("2024-01-15,新能源汽车,10,success\n")
    f.write("2024-01-16,智能手机市场,5,success\n")
    f.write("2024-01-17,半导体行业,8,rate_limited\n")

with open(f"{BASE}/data/market_segments.json", "w") as f:
    json.dump({
        "automotive": ["新能源汽车", "自动驾驶", "车联网"],
        "consumer_electronics": ["智能家居", "可穿戴设备", "TWS耳机"],
        "enterprise": ["云计算", "大数据", "SaaS"]
    }, f, ensure_ascii=False, indent=2)

# archive/
with open(f"{BASE}/archive/2023/q1/search_results_q1.json", "w") as f:
    json.dump([{"query": "5G手机", "results_count": 10, "date": "2023-01-10"}], f, ensure_ascii=False, indent=2)

with open(f"{BASE}/archive/2023/q2/search_results_q2.json", "w") as f:
    json.dump([{"query": "新能源汽车", "results_count": 15, "date": "2023-04-20"}], f, ensure_ascii=False, indent=2)

with open(f"{BASE}/archive/2024/q1/competitor_snapshot.json", "w") as f:
    json.dump({"snapshot_date": "2024-01-01", "topics": ["新能源", "AI大模型"], "notes": "Q1 baseline"}, f, indent=2)

# logs/
with open(f"{BASE}/logs/search_errors.log", "w") as f:
    f.write("[2024-06-01 09:12:33] ERROR: 503 Service Unavailable - Baidu rate limit\n")
    f.write("[2024-06-01 09:13:45] INFO: Retry successful after 62 seconds\n")
    f.write("[2024-06-02 14:55:01] WARNING: fetch_url timeout for http://example-blocked-site.com\n")

with open(f"{BASE}/logs/pipeline_run.log", "w") as f:
    f.write("Pipeline started at 2024-06-15 08:00:00\n")
    f.write("Query: 新能源汽车市场份额 | Results: 10 | Status: OK\n")
    f.write("Pipeline finished at 2024-06-15 08:00:45\n")

# cache/
with open(f"{BASE}/cache/url_cache_index.json", "w") as f:
    json.dump({"cached_urls": [], "last_cleared": "2024-06-01"}, f, indent=2)

# tmp/
with open(f"{BASE}/tmp/scratch_notes.txt", "w") as f:
    f.write("TODO: research new energy vehicle trends\n")
    f.write("Need market share data for BYD and Tesla China\n")
    f.write("Check smart home competition landscape\n")

# root level distractor
with open(f"{BASE}/requirements.txt", "w") as f:
    f.write("baidusearch\nrequests\nbeautifulsoup4\nlxml\n")

with open(f"{BASE}/pipeline_config.yaml", "w") as f:
    f.write("search:\n  default_num_results: 10\n  delay_seconds: 15\nfetch:\n  timeout: 30\n  max_chars: 5000\n")

print("Workspace generated successfully.")