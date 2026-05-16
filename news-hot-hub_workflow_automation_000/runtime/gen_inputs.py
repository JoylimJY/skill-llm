import os
import json
import stat
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "news-hot-hub/scripts",
    "news-hot-hub/references",
    "news-hot-hub/logs",
    "news-hot-hub/cache",
    "news-hot-hub/output",
    "news-hot-hub/tests",
    "news-hot-hub/config",
    "reports/daily",
    "reports/archive",
    "data/raw",
    "data/processed",
    "dashboard/static",
    "dashboard/templates",
    "pipeline/jobs",
    "pipeline/hooks",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "news-hot-hub/logs/2024-01-10.log": "INFO: fetch zhihu completed\nWARN: toutiao timeout\n",
    "news-hot-hub/logs/2024-01-11.log": "INFO: all platforms fetched\n",
    "news-hot-hub/cache/.gitkeep": "",
    "news-hot-hub/config/settings.ini": "[defaults]\nlimit=10\ntimeout=30\nretry=3\n",
    "news-hot-hub/config/platforms.json": json.dumps({"enabled": ["zhihu", "toutiao", "aibase"], "disabled": []}),
    "news-hot-hub/tests/test_schema.py": "# placeholder tests\nimport unittest\nclass TestSchema(unittest.TestCase):\n    pass\n",
    "reports/daily/2024-01-10.json": json.dumps({"date": "2024-01-10", "status": "archived"}),
    "reports/archive/README.placeholder": "Archive storage for old reports.",
    "data/raw/sample_zhihu.json": json.dumps({"stale": True, "data": []}),
    "data/processed/merged_20240110.json": json.dumps({"merged": [], "source": "legacy"}),
    "dashboard/static/style.css": "body { font-family: sans-serif; }",
    "dashboard/templates/index.html": "<html><body>Dashboard</body></html>",
    "pipeline/jobs/daily_fetch.sh": "#!/bin/bash\necho 'legacy pipeline - deprecated'\n",
    "pipeline/hooks/post_fetch.py": "# deprecated hook\npass\n",
    "news-hot-hub/output/.gitkeep": "",
}
for rel_path, content in distractor_files.items():
    p = WORKSPACE / rel_path
    p.write_text(content)

# ── requirements.txt ────────────────────────────────────────────────────────
(WORKSPACE / "news-hot-hub/requirements.txt").write_text(
    "requests>=2.28.0\nbeautifulsoup4>=4.11.0\nlxml>=4.9.0\n"
)

# ── hub.py — unified dispatcher ─────────────────────────────────────────────
hub_py = r'''#!/usr/bin/env python3
"""
hub.py — news-hot-hub unified dispatcher
Supports: fetch <platform>[,platform2] [subcommand] [--limit N]
          all [--limit N]
          compare [--limit N]
          status
"""
import sys
import os
import json
import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPTS_DIR = Path(__file__).parent
PLATFORM_MAP = {
    "zhihu": "zhihu", "zh": "zhihu",
    "toutiao": "toutiao", "tt": "toutiao",
    "aibase": "aibase", "ab": "aibase",
}
PLATFORMS_ALL = ["zhihu", "toutiao", "aibase"]
PLATFORM_NAMES = {"zhihu": "知乎", "toutiao": "今日头条", "aibase": "AIBase"}

def get_limit(args):
    limit = int(os.environ.get("HOT_HUB_LIMIT", 25))
    if "--limit" in args:
        idx = args.index("--limit")
        if idx + 1 < len(args):
            limit = int(args[idx + 1])
    return limit

def load_platform_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def fetch_platform(platform, subcommand=None, limit=25):
    try:
        mod = load_platform_module(platform)
        if subcommand:
            result = mod.fetch(limit=limit, subcommand=subcommand)
        else:
            result = mod.fetch(limit=limit)
        return {"platform": PLATFORM_NAMES[platform], "success": True, "data": result}
    except Exception as e:
        return {"platform": PLATFORM_NAMES[platform], "success": False, "error": str(e)}

def cmd_status():
    for p in PLATFORMS_ALL:
        path = SCRIPTS_DIR / f"{p}.py"
        ok = path.exists()
        print(json.dumps({"platform": PLATFORM_NAMES[p], "available": ok, "path": str(path)}))

def cmd_fetch(args):
    # args after 'fetch': platform_spec [subcommand] [--limit N]
    clean_args = [a for a in args if not a.startswith("--") and a not in [str(x) for x in range(1000)]]
    # remove --limit and its value
    filtered = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a == "--limit":
            skip_next = True
            continue
        filtered.append(a)

    if not filtered:
        print(json.dumps({"error": "No platform specified"}))
        return

    platform_spec = filtered[0]
    subcommand = filtered[1] if len(filtered) > 1 else None
    limit = get_limit(args)

    platforms_raw = platform_spec.split(",")
    platforms = []
    for p in platforms_raw:
        p = p.strip()
        canonical = PLATFORM_MAP.get(p)
        if canonical:
            platforms.append(canonical)
        else:
            print(json.dumps({"error": f"Unknown platform: {p}"}))
            return

    for p in platforms:
        if p == "aibase":
            result = fetch_platform(p, subcommand=subcommand, limit=limit)
        else:
            result = fetch_platform(p, limit=limit)
        print(json.dumps(result, ensure_ascii=False))

def cmd_all(args):
    limit = get_limit(args)
    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_platform, p, limit=limit): p for p in PLATFORMS_ALL}
        for f in as_completed(futures):
            p = futures[f]
            results[p] = f.result()
    for p in PLATFORMS_ALL:
        print(json.dumps(results[p], ensure_ascii=False))

def cmd_compare(args):
    limit = get_limit(args)
    from collections import Counter
    import re
    all_items = {}
    for p in PLATFORMS_ALL:
        r = fetch_platform(p, limit=limit)
        if r["success"]:
            data = r["data"]
            items = data.get("data", [])
            titles = [item.get("title", "") for item in items]
            all_items[PLATFORM_NAMES[p]] = titles

    stop_words = set("的了是在和与或对于及其为以上下中内外前后新大小".split() + list("的了是在"))
    word_counter = Counter()
    per_platform = {}
    for platform_name, titles in all_items.items():
        words = []
        for title in titles:
            tokens = re.findall(r'[\u4e00-\u9fff]{2,}', title)
            words.extend(tokens)
        platform_counter = Counter(w for w in words if w not in stop_words)
        per_platform[platform_name] = [{"word": w, "count": c} for w, c in platform_counter.most_common(10)]
        word_counter.update(platform_counter)

    top_keywords = [{"word": w, "count": c} for w, c in word_counter.most_common(20)]
    output = {
        "top_keywords": top_keywords,
        "per_platform": per_platform
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: hub.py <command> [options]")
        sys.exit(1)

    cmd = args[0]
    rest = args[1:]

    if cmd == "status":
        cmd_status()
    elif cmd == "fetch":
        cmd_fetch(rest)
    elif cmd == "all":
        cmd_all(rest)
    elif cmd == "compare":
        cmd_compare(rest)
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
(WORKSPACE / "news-hot-hub/scripts/hub.py").write_text(hub_py)

# ── zhihu.py ────────────────────────────────────────────────────────────────
zhihu_py = r'''#!/usr/bin/env python3
"""知乎热搜 mock fetcher"""
import json

MOCK_DATA = [
    "人工智能如何改变医疗行业",
    "2024年最值得关注的科技趋势",
    "ChatGPT对教育的深远影响",
    "大模型训练成本为何如此高昂",
    "国产芯片发展现状与未来",
    "电动汽车续航焦虑如何解决",
    "年轻人为何越来越不想结婚",
    "房价下跌对普通家庭意味着什么",
    "量子计算机距离实用化还有多远",
    "中国制造业转型升级的挑战",
    "社交媒体算法如何影响认知",
    "气候变化对农业的具体影响",
    "创业失败率为何高达90%",
    "数字人民币推广进展如何",
    "元宇宙概念是否已经破灭",
    "短视频对阅读习惯的冲击",
    "碳中和目标实现难点分析",
    "机器人取代人类工作的速度",
    "互联网大厂裁员潮背后原因",
    "外卖行业的可持续发展困境",
    "新能源汽车电池回收问题",
    "在线教育行业整顿后的现状",
    "医疗AI诊断的准确率现状",
    "区块链技术实际落地案例",
    "算法推荐是否加剧社会分裂",
]

def fetch(limit=25, subcommand=None):
    items = [{"rank": i+1, "title": t, "hot_score": (25-i)*1000 + 500}
             for i, t in enumerate(MOCK_DATA[:limit])]
    return {
        "type": "hot_search",
        "platform": "zhihu",
        "count": len(items),
        "data": items
    }

if __name__ == "__main__":
    import sys
    limit = 25
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx+1])
    print(json.dumps(fetch(limit=limit), ensure_ascii=False, indent=2))
'''
(WORKSPACE / "news-hot-hub/scripts/zhihu.py").write_text(zhihu_py)

# ── toutiao.py ──────────────────────────────────────────────────────────────
toutiao_py = r'''#!/usr/bin/env python3
"""今日头条热榜 mock fetcher"""
import json

MOCK_DATA = [
    "人工智能大模型最新进展",
    "全球芯片产业竞争格局",
    "新冠变异株再度引发关注",
    "国内经济复苏数据出炉",
    "电动车自燃事故频发原因",
    "房地产政策最新调整方向",
    "大学生就业难问题深度解析",
    "中美关系最新动态",
    "碳排放交易市场扩容",
    "AI绘画版权争议持续发酵",
    "老龄化社会养老压力分析",
    "国产大飞机商业运营进展",
    "网红经济泡沫是否破裂",
    "量子通信技术突破新纪录",
    "智能驾驶监管新规落地",
    "外卖骑手权益保障新政",
    "直播带货乱象整治行动",
    "高铁网络继续扩张计划",
    "数据安全法实施效果评估",
    "气候峰会中国承诺落实情况",
    "元宇宙平台用户流失问题",
    "医保目录调整影响分析",
    "农村电商发展最新数据",
    "5G应用落地典型案例",
    "智慧城市建设标准出台",
]

def fetch(limit=25, subcommand=None):
    items = [{"rank": i+1, "title": t, "comment_count": (25-i)*200 + 100, "read_count": (25-i)*5000}
             for i, t in enumerate(MOCK_DATA[:limit])]
    return {
        "type": "hot_board",
        "platform": "toutiao",
        "count": len(items),
        "data": items
    }

if __name__ == "__main__":
    import sys
    limit = 25
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx+1])
    print(json.dumps(fetch(limit=limit), ensure_ascii=False, indent=2))
'''
(WORKSPACE / "news-hot-hub/scripts/toutiao.py").write_text(toutiao_py)

# ── aibase.py ───────────────────────────────────────────────────────────────
aibase_py = r'''#!/usr/bin/env python3
"""AIBase mock fetcher — supports hot-search (news) and daily"""
import json

MOCK_NEWS = [
    "OpenAI发布GPT-5技术预览版",
    "谷歌Gemini Ultra击败人类专家",
    "Meta开源最新LLaMA模型",
    "微软Copilot企业版全面上线",
    "Anthropic Claude 3发布性能报告",
    "百度文心大模型4.0正式亮相",
    "华为盘古大模型行业应用案例",
    "AI Agent自主完成复杂编程任务",
    "扩散模型视频生成质量新突破",
    "多模态大模型跨语言理解能力",
    "AI在药物研发中的成功案例",
    "强化学习机器人学会精细操作",
    "大模型幻觉问题研究新进展",
    "AI代码生成工具市场份额分析",
    "向量数据库成为AI基础设施",
    "边缘计算AI部署挑战与方案",
    "AI伦理框架国际标准进展",
    "检索增强生成RAG技术最佳实践",
    "AI芯片能效比再创新高",
    "开源大模型生态系统发展现状",
    "AI翻译质量超越专业译员测试",
    "智能体编排框架技术对比",
    "AI安全红队测试方法论",
    "神经网络可解释性研究突破",
    "AI在气候科学预测中的应用",
]

MOCK_DAILY = [
    "【每日精选】大模型技术进展汇总",
    "【AI日报】今日最重要的10篇论文",
    "GPT-5训练数据规模首次披露",
    "AI行业融资动态：本周重点投融资",
    "开源社区：本周最热Github项目",
    "学术前沿：ICML最新接收论文解读",
    "产业动态：AI应用落地企业案例",
    "政策速递：全球AI监管新进展",
    "技术深度：Transformer架构演进史",
    "工具推荐：提升AI开发效率的新工具",
    "观点碰撞：AGI时间线专家争论",
    "数据集发布：本周公开数据资源",
    "模型评测：主流LLM基准测试对比",
    "硬件进展：AI训练芯片新品发布",
    "应用案例：AI医疗影像诊断实测",
]

def fetch(limit=25, subcommand=None):
    if subcommand == "daily":
        items = [{"rank": i+1, "title": t, "category": "daily"}
                 for i, t in enumerate(MOCK_DAILY[:limit])]
        return {
            "type": "daily",
            "platform": "aibase",
            "count": len(items),
            "data": items
        }
    elif subcommand == "all":
        news_items = [{"rank": i+1, "title": t, "category": "news"}
                      for i, t in enumerate(MOCK_NEWS[:limit])]
        daily_items = [{"rank": i+1, "title": t, "category": "daily"}
                       for i, t in enumerate(MOCK_DAILY[:limit])]
        return {
            "type": "all",
            "platform": "aibase",
            "count": len(news_items) + len(daily_items),
            "data": news_items + daily_items
        }
    else:
        items = [{"rank": i+1, "title": t, "category": "news"}
                 for i, t in enumerate(MOCK_NEWS[:limit])]
        return {
            "type": "news",
            "platform": "aibase",
            "count": len(items),
            "data": items
        }

if __name__ == "__main__":
    import sys
    limit = 25
    subcommand = None
    args = sys.argv[1:]
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx+1])
    for a in args:
        if a in ("daily", "all", "news"):
            subcommand = a
    print(json.dumps(fetch(limit=limit, subcommand=subcommand), ensure_ascii=False, indent=2))
'''
(WORKSPACE / "news-hot-hub/scripts/aibase.py").write_text(aibase_py)

# ── references ───────────────────────────────────────────────────────────────
arch_md = """# Architecture Design

## System Overview
The hub uses a dispatcher + plugin architecture:
- `hub.py` is the single entry point
- Each platform script exposes a `fetch(limit, subcommand)` function
- ThreadPoolExecutor for parallel fetching in `all` command

## Data Flow
User CLI → hub.py → platform module → JSON Lines stdout

## Extension
Add new platform: create `scripts/<name>.py` with `fetch()`, register in PLATFORM_MAP.
"""
(WORKSPACE / "news-hot-hub/references/architecture.md").write_text(arch_md)

schema_md = """# Data Schema

## fetch / all output
JSON Lines: one JSON object per line per platform.
```json
{"platform": "知乎", "success": true, "data": {"type": "hot_search", "count": 25, "data": [{"rank": 1, "title": "...", "hot_score": 24500}]}}
```

## compare output
Single JSON with:
- `top_keywords`: list of {word, count} sorted by count desc
- `per_platform`: dict keyed by platform display name, each value list of {word, count}

## Error format
```json
{"platform": "知乎", "success": false, "error": "timeout"}
```
"""
(WORKSPACE / "news-hot-hub/references/data-schema.md").write_text(schema_md)

platform_md = """# Platform Guide

## Adding a new platform
1. Create `scripts/<platform>.py`
2. Implement `fetch(limit=25, subcommand=None) -> dict`
3. Register abbreviation in hub.py PLATFORM_MAP

## AIBase specifics
- Default (no subcommand): returns AI news
- subcommand=daily: returns AI daily digest
- subcommand=all: returns both news + daily

## Authentication
Current platforms use public endpoints, no auth required.
"""
(WORKSPACE / "news-hot-hub/references/platform-guide.md").write_text(platform_md)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """---
name: news-hot-hub
description: 新闻热点数据聚合器——整合知乎、今日头条、AIBase三大平台热搜数据。支持单独获取任一平台热榜，也支持一次性获取所有平台数据并汇总输出。当用户提到"热搜聚合"、"全平台热点"、"各平台热门话题"、"热榜整合"、"热点数据采集"、"我要看全网热点"、"刷一下各平台热榜"、"一键获取热榜"、"知乎头条热榜"、"全网热点"、"多平台热搜"时使用此技能。也可以单独触发某个平台：提到"知乎热搜/知乎热门/知乎数据"触发知乎，提到"头条热榜/今日头条"触发头条，提到"AIBase/AI基地/AI新闻/AI日报"触发AIBase。
---

# news Hot Hub — 中文热点数据聚合器

## 概述

整合知乎、今日头条、AIBase三大中文平台的热搜/热门数据。采用「调度器 + 独立脚本」插件式架构，每个平台一个独立 Python 脚本，由统一的 `hub.py` 调度。

## 目录结构

```
news-hot-hub/
├── SKILL.md                 # 本文件 — AI Agent 技能指令
├── requirements.txt         # Python 依赖
├── scripts/                 # 可执行脚本
│   ├── hub.py               # 统一调度入口 ★
│   ├── zhihu.py             # 知乎（已实现）
│   ├── toutiao.py           # 今日头条（已实现）
│   └── aibase.py            # AIBase（已实现）
└── references/              # 参考文档
    ├── architecture.md      # 架构设计
    ├── data-schema.md       # 数据格式规范
    └── platform-guide.md    # 平台接入指南
```

## 安装

```bash
pip install -r ${SKILL_DIR}/requirements.txt
```

核心依赖：`requests`, `beautifulsoup4`, `lxml`

## CLI 使用

统一入口：`${SKILL_DIR}/scripts/hub.py`

```bash
python ${SKILL_DIR}/scripts/hub.py <command> [options]
```

### 平台标识

| 全称 | 缩写 | 中文 |
|---|---|---|
| `zhihu` | `zh` | 知乎 |
| `toutiao` | `tt` | 今日头条 |
| `aibase` | `ab` | AIBase |

### 命令一览

| 命令 | 说明 | 选项 |
|---|---|---|
| `fetch <platform>` | 获取指定平台热榜 | `--limit N` |
| `all` | 并行获取全部平台 | `--limit N` |
| `compare` | 跨平台热点词频对比 | `--limit N` |
| `status` | 检查各平台脚本可用性 | — |

### 使用示例

```bash
# 单平台获取
python ${SKILL_DIR}/scripts/hub.py fetch zhihu
python ${SKILL_DIR}/scripts/hub.py fetch toutiao --limit 20
python ${SKILL_DIR}/scripts/hub.py fetch aibase
python ${SKILL_DIR}/scripts/hub.py fetch aibase daily

# 多平台
python ${SKILL_DIR}/scripts/hub.py fetch zhihu,toutiao

# 全部平台
python ${SKILL_DIR}/scripts/hub.py all

# 跨平台对比
python ${SKILL_DIR}/scripts/hub.py compare

# 检查可用性
python ${SKILL_DIR}/scripts/hub.py status
```

## 触发逻辑

Agent 加载本 skill 后，根据用户意图判断调用方式：

1. **只提单一平台** → `fetch <platform>`
2. **提到多个平台** → `fetch <p1>,<p2>` 逗号分隔
3. **"全部"/"所有"/"一键"/"全平台"** → `all`
4. **"对比"/"比较"/"交叉分析"** → `compare`
5. **不明确** → 询问用户需要哪个/哪些平台

### AIBase子命令映射

| 用户意图 | 子命令 |
|---|---|
| AI新闻 | `fetch aibase`（默认 hot-search → news）|
| AI日报 | `fetch aibase daily` |
| AI新闻+日报 | `fetch aibase all` |

## 输出格式

### fetch / all

JSON Lines（每行一个平台结果）：

```json
{"platform": "知乎", "success": true, "data": {"type": "hot_search", "count": 25, "data": [...]}}
```

### compare

跨平台词频分析 JSON，包含 `top_keywords` 和 `per_platform` 字段。

> 详细数据格式见 `references/data-schema.md`

## 环境变量

| 变量 | 说明 |
|---|---|
| `HOT_HUB_LIMIT` | 全局默认 limit，CLI `--limit` 可覆盖 |

## 参考文档

需要深入了解时，按需读取 `references/` 目录下的文档：

- **架构设计** → `references/architecture.md`：系统架构、数据流、扩展机制
- **数据格式** → `references/data-schema.md`：各平台 JSON 输出字段详细定义
- **接入指南** → `references/platform-guide.md`：新平台接入步骤、脚本模板、认证说明

## 快速参考

| 需求 | 命令 |
|---|---|
| 知乎热搜 | `fetch zhihu` |
| 头条热榜 | `fetch toutiao` |
| AIBase新闻 | `fetch aibase` |
| AI日报 | `fetch aibase daily` |
| 全部平台 | `all` |
| 词频对比 | `compare` |
| 可用性检查 | `status` |
"""
(WORKSPACE / "news-hot-hub/SKILL.md").write_text(skill_md)

print("Workspace initialized successfully.")
print(f"Files created: {list(WORKSPACE.rglob('*'))}")