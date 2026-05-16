import os
import json
import random

random.seed(42)

# Create directory structure
dirs = [
    "scripts",
    "references",
    "assets",
    "logs",
    "data/raw",
    "data/processed",
    "archive/2026-03",
    "archive/2026-02",
    "reports/drafts",
    "reports/final",
    "config",
    "tests",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── scripts/generate_report_content.py ─────────────────────────────────────
generate_report_content_py = '''#!/usr/bin/env python3
"""
generate_report_content.py
Creates report structure, populates it, and renders Markdown output.
"""

import json
from datetime import datetime

CATEGORY_MAP = {
    "安全监管与风险警示": 1,
    "产业生态与市场动态": 2,
    "技术发展与社区生态": 3,
    "AI产业宏观趋势": 4,
    "政策与监管": 5,
    "其他重要科技进展": 6,
}

RISK_LEVEL_LABELS = {
    "high": "🔴 高风险",
    "medium": "🟡 中风险",
    "low": "🟢 低风险",
}


def create_report_structure(date_str: str) -> dict:
    """Create a standard report structure for the given date."""
    return {
        "date": date_str,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categories": {
            "安全监管与风险警示": [],
            "产业生态与市场动态": [],
            "技术发展与社区生态": [],
            "AI产业宏观趋势": [],
            "政策与监管": [],
            "其他重要科技进展": [],
        },
        "stats": {
            "total": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
        },
    }


def add_item_to_structure(structure: dict, item: dict) -> None:
    """
    Add a news item to the report structure.
    item must have keys: title, summary, source, category, risk_level, url (optional)
    category must be one of the six standard categories (Chinese name).
    risk_level must be one of: 'high', 'medium', 'low'
    """
    category = item.get("category", "其他重要科技进展")
    if category not in structure["categories"]:
        category = "其他重要科技进展"

    structure["categories"][category].append(item)
    structure["stats"]["total"] += 1

    risk = item.get("risk_level", "low")
    if risk == "high":
        structure["stats"]["high_risk"] += 1
    elif risk == "medium":
        structure["stats"]["medium_risk"] += 1
    else:
        structure["stats"]["low_risk"] += 1


def generate_markdown_content(structure: dict) -> str:
    """Render the report structure as a Markdown string."""
    date_str = structure["date"]
    stats = structure["stats"]
    generated_at = structure["generated_at"]

    lines = []
    lines.append(f"# OpenClaw {date_str}资讯汇总")
    lines.append("")

    # Section 1
    lines.append("## 一、当日资讯概况")
    lines.append("")
    lines.append(f"- 资讯总数：**{stats[\'total\']}** 条")
    lines.append(f"- 高风险资讯：**{stats[\'high_risk\']}** 条")
    lines.append(f"- 中风险资讯：**{stats[\'medium_risk\']}** 条")
    lines.append(f"- 低风险资讯：**{stats[\'low_risk\']}** 条")
    lines.append("")

    # Section 2
    lines.append("## 二、详细分类资讯")
    lines.append("")

    category_order = [
        "安全监管与风险警示",
        "产业生态与市场动态",
        "技术发展与社区生态",
        "AI产业宏观趋势",
        "政策与监管",
        "其他重要科技进展",
    ]

    for idx, cat_name in enumerate(category_order, 1):
        items = structure["categories"].get(cat_name, [])
        lines.append(f"### {idx}. {cat_name}")
        if not items:
            lines.append("")
            lines.append("_本日无相关资讯_")
            lines.append("")
            continue
        lines.append("")
        for item in items:
            risk_label = RISK_LEVEL_LABELS.get(item.get("risk_level", "low"), "🟢 低风险")
            lines.append(f"#### {item.get(\'title\', \'（无标题）\')} [{risk_label}]")
            lines.append("")
            lines.append(f"**摘要**：{item.get(\'summary\', \'\')}")
            lines.append("")
            lines.append(f"**来源**：{item.get(\'source\', \'未知来源\')}")
            if item.get("url"):
                lines.append(f"**链接**：{item[\'url\']}")
            lines.append("")

    # Section 3
    lines.append("## 三、核心分析与展望")
    lines.append("")
    high_items = [
        item
        for cat in structure["categories"].values()
        for item in cat
        if item.get("risk_level") == "high"
    ]
    if high_items:
        lines.append("### 风险提示")
        lines.append("")
        for item in high_items:
            lines.append(f"- **{item[\'title\']}**：{item.get(\'summary\', \'\')[:80]}...")
        lines.append("")
    lines.append("### 关注重点")
    lines.append("")
    lines.append("请重点关注安全监管与风险警示类资讯，及时响应高风险事项。")
    lines.append("")
    lines.append("### 未来展望")
    lines.append("")
    lines.append("持续监控OpenClaw生态动态，跟踪技术发展与政策变化趋势。")
    lines.append("")

    # Section 4
    lines.append("## 四、附录")
    lines.append("")
    lines.append(f"- 数据生成时间：{generated_at}")
    lines.append(f"- 报告日期：{date_str}")
    lines.append("- 技能版本：1.0.0")
    lines.append("")

    return "\\n".join(lines)
'''

with open("scripts/generate_report_content.py", "w", encoding="utf-8") as f:
    f.write(generate_report_content_py)

# ── scripts/search_openclaw_news.py ────────────────────────────────────────
search_openclaw_news_py = '''#!/usr/bin/env python3
"""
search_openclaw_news.py
Generates search queries and formats raw search results.
"""

def generate_search_queries(date_str: str) -> list:
    """Generate standard search queries for the given date."""
    return [
        f"OpenClaw {date_str} 安全漏洞 监管预警 合规要求",
        f"OpenClaw {date_str} 云服务 企业部署 产品发布",
        f"OpenClaw {date_str} GitHub进展 版本更新 bug修复",
        f"OpenClaw {date_str} AI芯片 算力成本 技术架构",
        f"OpenClaw {date_str} 政府政策 法规标准",
    ]


def format_search_results(results: list) -> list:
    """Format raw search result dicts into standardized news items."""
    formatted = []
    for r in results:
        formatted.append({
            "title": r.get("title", ""),
            "summary": r.get("snippet", r.get("summary", "")),
            "source": r.get("source", r.get("domain", "未知来源")),
            "url": r.get("url", r.get("link", "")),
            "raw_category": r.get("category", ""),
            "raw_risk": r.get("risk", ""),
        })
    return formatted


def generate_daily_report_content(data: list, date_str: str) -> str:
    """Convenience wrapper: classify items and return markdown string."""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from generate_report_content import create_report_structure, add_item_to_structure, generate_markdown_content
    structure = create_report_structure(date_str)
    for item in data:
        add_item_to_structure(structure, item)
    return generate_markdown_content(structure)
'''

with open("scripts/search_openclaw_news.py", "w", encoding="utf-8") as f:
    f.write(search_openclaw_news_py)

# ── references/news_template.md ────────────────────────────────────────────
news_template_md = """# OpenClaw [日期]资讯汇总

## 一、当日资讯概况
[总体统计和关键发现，包括资讯总数、高/中/低风险分布]

## 二、详细分类资讯

### 1. 安全监管与风险警示
[安全漏洞、监管预警、合规要求等 — 高优先级]

### 2. 产业生态与市场动态
[云服务、企业部署、产品发布等 — 高优先级]

### 3. 技术发展与社区生态
[GitHub进展、版本更新、bug修复等 — 中优先级]

### 4. AI产业宏观趋势
[AI芯片、算力成本、技术架构等 — 中优先级]

### 5. 政策与监管
[政府政策、法规标准等 — 高优先级]

### 6. 其他重要科技进展
[新材料、新能源汽车、显示技术等 — 低优先级]

## 三、核心分析与展望
[风险提示、关注重点、未来展望]

## 四、附录
[数据来源、生成时间、技能版本等]
"""
with open("references/news_template.md", "w", encoding="utf-8") as f:
    f.write(news_template_md)

# ── references/usage_examples.md ───────────────────────────────────────────
usage_examples_md = """# 使用示例与最佳实践

## 基本使用场景

### 场景一：生成当日资讯报告
```python
import sys
sys.path.insert(0, 'scripts')
from generate_report_content import create_report_structure, add_item_to_structure, generate_markdown_content

structure = create_report_structure("2026-03-15")
add_item_to_structure(structure, {
    "title": "示例资讯",
    "summary": "摘要内容",
    "source": "来源网站",
    "category": "技术发展与社区生态",
    "risk_level": "low"
})
content = generate_markdown_content(structure)
print(content)
```

## 输出格式说明
- 报告必须包含四个标准章节（一、二、三、四）
- 分类必须严格使用六个标准类别名称
- 风险等级必须为 high / medium / low

## 分类关键词速查
| 类别 | 核心关键词 |
|------|-----------|
| 安全监管与风险警示 | 安全、漏洞、工信部、网信办、数据泄露 |
| 产业生态与市场动态 | 华为云、腾讯云、上线、发布、价格 |
| 技术发展与社区生态 | GitHub、issue、PR、版本、bug |
| AI产业宏观趋势 | AI芯片、算力、投资、融资、竞争 |
| 政策与监管 | 政策、法规、两会、科技部 |
| 其他重要科技进展 | 碳纤维、新能源汽车、显示技术 |
"""
with open("references/usage_examples.md", "w", encoding="utf-8") as f:
    f.write(usage_examples_md)

# ── assets/config_template.json ────────────────────────────────────────────
config_template = {
    "skill_version": "1.0.0",
    "search_config": {
        "engines": ["web_search", "knowledge_answer"],
        "time_range": "24h",
        "priority_domains": [
            "miit.gov.cn", "cac.gov.cn", "github.com",
            "xinhuanet.com", "people.com.cn"
        ],
        "max_results_per_query": 10
    },
    "categories_config": [
        {
            "id": 1,
            "name": "安全监管与风险警示",
            "keywords": ["安全", "漏洞", "监管", "风险", "预警", "工信部", "网信办", "应急中心", "数据泄露"],
            "priority": "high",
            "risk_default": "high"
        },
        {
            "id": 2,
            "name": "产业生态与市场动态",
            "keywords": ["华为云", "腾讯云", "阿里云", "云服务", "企业部署", "上线", "发布", "价格"],
            "priority": "high",
            "risk_default": "medium"
        },
        {
            "id": 3,
            "name": "技术发展与社区生态",
            "keywords": ["GitHub", "社区", "issue", "PR", "版本", "更新", "bug", "修复", "功能"],
            "priority": "medium",
            "risk_default": "medium"
        },
        {
            "id": 4,
            "name": "AI产业宏观趋势",
            "keywords": ["AI芯片", "算力", "投资", "融资", "股价", "市值", "财报", "竞争"],
            "priority": "medium",
            "risk_default": "medium"
        },
        {
            "id": 5,
            "name": "政策与监管",
            "keywords": ["政策", "法规", "两会", "政府工作报告", "科技部", "标准", "监管", "规划"],
            "priority": "high",
            "risk_default": "high"
        },
        {
            "id": 6,
            "name": "其他重要科技进展",
            "keywords": ["碳纤维", "新能源汽车", "显示技术", "电池", "新材料"],
            "priority": "low",
            "risk_default": "low"
        }
    ],
    "report_config": {
        "template": "references/news_template.md",
        "output_format": "markdown",
        "sections": ["概况", "详细分类", "核心分析", "附录"],
        "include_risk_summary": True
    }
}
with open("assets/config_template.json", "w", encoding="utf-8") as f:
    json.dump(config_template, f, ensure_ascii=False, indent=2)

# ── RAW INPUT: data/raw/news_items_2026-03-15.json ─────────────────────────
# Deliberately messy: some items have vague categories, wrong/missing fields,
# and ambiguous content to force proper SKILL.md classification.
raw_news_items = [
    {
        "id": "N001",
        "headline": "工信部网络安全局发布OpenClaw高危漏洞预警通告",
        "snippet": "工信部网络安全局于2026年3月15日发布紧急预警，OpenClaw v2.3.1存在远程代码执行漏洞（CVE-2026-1234），风险等级超危，要求相关企业立即排查并升级。",
        "domain": "miit.gov.cn",
        "link": "https://miit.gov.cn/security/2026031501",
        "tags": ["安全", "工信部", "漏洞"]
    },
    {
        "id": "N002",
        "headline": "华为云正式发布OpenClaw企业版托管服务",
        "snippet": "华为云在MWC 2026上宣布正式上线OpenClaw企业版云托管服务，支持一键部署，定价99元/月起，面向中小企业开放注册。",
        "domain": "huaweicloud.com",
        "link": "https://huaweicloud.com/product/openclaw-enterprise",
        "tags": ["华为云", "发布", "企业部署"]
    },
    {
        "id": "N003",
        "headline": "OpenClaw GitHub仓库合并重大PR：支持多模态工具调用",
        "snippet": "OpenClaw核心团队在GitHub合并了#PR-892，该PR引入了多模态工具调用框架，解决了issue#774中报告的bug，版本升级至v2.4.0-beta。",
        "domain": "github.com",
        "link": "https://github.com/openclaw/openclaw/pull/892",
        "tags": ["GitHub", "PR", "版本更新", "bug修复"]
    },
    {
        "id": "N004",
        "headline": "碳纤维新材料突破：抗拉强度提升40%，或用于AI服务器散热",
        "snippet": "国内某材料研究院宣布突破碳纤维制备技术，新材料抗拉强度提升40%，导热系数提高20%，被认为可用于下一代AI服务器散热解决方案。",
        "domain": "materials-tech.cn",
        "link": "https://materials-tech.cn/carbon-fiber-2026",
        "tags": ["碳纤维", "新材料", "散热"]
    },
    {
        "id": "N005",
        "headline": "科技部发布《人工智能开源软件安全管理办法（征求意见稿）》",
        "snippet": "科技部于3月15日发布《人工智能开源软件安全管理办法（征求意见稿）》，要求所有开源AI框架（含OpenClaw）建立漏洞响应机制，征求意见截止4月15日。",
        "domain": "most.gov.cn",
        "link": "https://most.gov.cn/kjbgz/2026/031501",
        "tags": ["科技部", "政策", "法规", "标准"]
    },
    {
        "id": "N006",
        "headline": "英伟达发布GB300 AI芯片，算力成本降低35%",
        "snippet": "英伟达在GTC 2026上发布GB300 GPU，单卡算力达到2000 TFLOPS，单位算力成本较上一代降低35%，OpenClaw等主流AI框架已完成适配。",
        "domain": "nvidia.com",
        "link": "https://nvidia.com/gb300",
        "tags": ["AI芯片", "算力", "英伟达"]
    },
    {
        "id": "N007",
        "headline": "OpenClaw数据处理模块发现中危SQL注入漏洞",
        "snippet": "安全研究员在OpenClaw数据处理模块中发现中危SQL注入漏洞，CVSS评分6.5，攻击者可借此读取后端数据库部分内容，官方已确认并计划在v2.3.2中修复。",
        "domain": "securitybug.io",
        "link": "https://securitybug.io/openclaw-sqli-2026",
        "tags": ["漏洞", "安全", "中危"]
    },
    {
        "id": "N008",
        "headline": "比亚迪发布搭载OpenClaw的新能源汽车智能驾驶系统",
        "snippet": "比亚迪与OpenClaw团队合作，在旗舰车型上搭载基于OpenClaw的智能驾驶决策系统，支持L3级自动驾驶，预计2026年Q3量产交付。",
        "domain": "byd.com",
        "link": "https://byd.com/tech/openclaw-driving",
        "tags": ["新能源汽车", "比亚迪", "自动驾驶"]
    },
    {
        "id": "N009",
        "headline": "腾讯云OpenClaw托管服务宣布降价20%，竞争格局加剧",
        "snippet": "腾讯云宣布其OpenClaw托管服务全系列降价20%，此举被认为是应对华为云同日发布企业版服务的直接竞争回应，市场价格战升温。",
        "domain": "cloud.tencent.com",
        "link": "https://cloud.tencent.com/act/openclaw-promo",
        "tags": ["腾讯云", "价格", "竞争", "市场"]
    },
    {
        "id": "N010",
        "headline": "OpenClaw社区论坛统计：3月第二周issue关闭率达87%",
        "snippet": "根据OpenClaw社区周报，3月8日至14日共新增issue 143个，关闭127个，关闭率87%，社区活跃度较上月提升15%，功能性bug修复速度显著加快。",
        "domain": "community.openclaw.io",
        "link": "https://community.openclaw.io/weekly/2026-03-w2",
        "tags": ["社区", "issue", "修复", "统计"]
    },
    {
        "id": "N011",
        "headline": "网信办约谈三家OpenClaw云服务商，要求整改数据出境违规问题",
        "snippet": "网信办于3月15日对三家使用OpenClaw框架的云服务商进行约谈，指出其存在数据出境审批缺失问题，要求30日内完成整改并提交合规报告。",
        "domain": "cac.gov.cn",
        "link": "https://cac.gov.cn/notice/2026031502",
        "tags": ["网信办", "监管", "数据泄露", "合规"]
    },
    {
        "id": "N012",
        "headline": "全球AI投资报告：OpenClaw生态企业融资总额超120亿元",
        "snippet": "全球知名投资机构发布2026年Q1 AI投资报告，OpenClaw生态相关企业累计融资超120亿元，同比增长230%，成为最受资本青睐的开源AI框架生态之一。",
        "domain": "pitchbook.com",
        "link": "https://pitchbook.com/reports/ai-2026q1",
        "tags": ["投资", "融资", "市值", "AI"]
    }
]

with open("data/raw/news_items_2026-03-15.json", "w", encoding="utf-8") as f:
    json.dump(raw_news_items, f, ensure_ascii=False, indent=2)

# ── Distractor files ────────────────────────────────────────────────────────
# logs/
with open("logs/search_log_2026-03-14.txt", "w") as f:
    f.write("2026-03-14 08:00:01 INFO  Search started\n")
    f.write("2026-03-14 08:00:05 INFO  Found 8 results\n")
    f.write("2026-03-14 08:01:22 INFO  Report generated\n")

with open("logs/error_log_2026-03-13.txt", "w") as f:
    f.write("2026-03-13 09:15:33 ERROR Search timeout on query 3\n")
    f.write("2026-03-13 09:15:34 WARN  Retrying...\n")

# archive/
with open("archive/2026-03/report_2026-03-14.md", "w") as f:
    f.write("# OpenClaw 2026-03-14资讯汇总\n\n(Archived report placeholder)\n")

with open("archive/2026-03/report_2026-03-13.md", "w") as f:
    f.write("# OpenClaw 2026-03-13资讯汇总\n\n(Archived report placeholder)\n")

with open("archive/2026-02/report_2026-02-28.md", "w") as f:
    f.write("# OpenClaw 2026-02-28资讯汇总\n\n(Archived report placeholder)\n")

# data/processed
with open("data/processed/classified_2026-03-14.json", "w") as f:
    json.dump({"date": "2026-03-14", "items": [], "note": "previous day processed"}, f)

# reports/drafts
with open("reports/drafts/draft_template.md", "w") as f:
    f.write("# DRAFT - Do not use\nThis is a draft template under revision.\n")

# config/
with open("config/scheduler.json", "w") as f:
    json.dump({"cron": "0 8 * * *", "timezone": "Asia/Shanghai", "enabled": True}, f, indent=2)

with open("config/notifier.yaml", "w") as f:
    f.write("notifier:\n  email: ops@example.com\n  slack_webhook: ''\n  threshold: high\n")

# tests/
with open("tests/test_classify.py", "w") as f:
    f.write("# Unit tests for classification logic\n# TODO: implement\n")

with open("tests/sample_item.json", "w") as f:
    json.dump({"title": "test", "summary": "test summary", "source": "test", "category": "技术发展与社区生态", "risk_level": "low"}, f)

# root-level distractor
with open("requirements.txt", "w") as f:
    f.write("requests>=2.28.0\npython-dateutil>=2.8.2\njinja2>=3.1.0\nrich>=13.0.0\n")

with open("pipeline_notes.txt", "w") as f:
    f.write("Pipeline v1.2 notes:\n- Step 1: Fetch raw news\n- Step 2: Classify\n- Step 3: Generate report\nSee scripts/ for implementation.\n")

print("Workspace initialized successfully.")
print("Key files created:")
print("  scripts/generate_report_content.py")
print("  scripts/search_openclaw_news.py")
print("  references/news_template.md")
print("  references/usage_examples.md")
print("  assets/config_template.json")
print("  data/raw/news_items_2026-03-15.json  <-- 12 raw news items to process")