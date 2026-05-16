import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "reports/weekly",
    "reports/monthly",
    "config",
    "logs",
    "src/parsers",
    "src/utils",
    "assets/images",
    "assets/thumbnails",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractors
distractor_files = {
    "config/settings.yaml": "api_timeout: 30\nretry_count: 3\noutput_dir: ./data/processed\n",
    "config/schema.json": json.dumps({"version": "1.0", "fields": ["id", "name", "value"]}),
    "data/raw/weibo_trends_2025.csv": "rank,title,reads\n1,热点A,1000000\n2,热点B,800000\n3,热点C,600000\n",
    "data/raw/twitter_trends.json": json.dumps([{"rank": 1, "topic": "#Tech", "tweets": 50000}]),
    "data/processed/last_run_summary.txt": "Last successful run: 2025-01-10 08:00:00\nItems fetched: 50\n",
    "data/archive/old_trends_jan.json": json.dumps({"source": "douyin", "date": "2025-01-01", "items": []}),
    "logs/scraper.log": "2025-01-10 INFO: Scraper started\n2025-01-10 INFO: Fetched 50 items\n2025-01-10 INFO: Done\n",
    "reports/weekly/week01_summary.txt": "Top trend this week: 国庆节\nAvg hotness: 5000000\n",
    "reports/monthly/jan_report.txt": "Monthly report placeholder. Data pending.\n",
    "src/parsers/weibo_parser.py": "def parse_weibo(data):\n    return []\n",
    "src/utils/format_helper.py": "def format_number(n):\n    return f'{n:,}'\n",
    "assets/images/placeholder.txt": "Image assets stored here.\n",
    "assets/thumbnails/readme.txt": "Thumbnail cache directory.\n",
}
for path, content in distractor_files.items():
    full = os.path.join(workspace, path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# Create the SKILL.md
skill_md = """\
---
name: douyin-hot-trend
description: 获取抖音热榜/热搜榜数据，包含热门视频、挑战赛、音乐等多领域热门内容，并输出标题、热度值、跳转链接及封面图（如有）。
version: 1.1.0
---

# 抖音热榜

## 技能概述

此技能用于抓取抖音热榜数据，包括：
- 热点标题
- 热度值
- 详情跳转链接
- **封面图（如有）** ✅ 新增
- 热门标签
- 内容类型

## 获取热榜

获取热榜（默认 50 条，按榜单顺序返回）：

```bash
node scripts/douyin.js hot
```

获取热榜前 N 条：

```bash
node scripts/douyin.js hot 10
```

## 输出格式示例

```
🔥 抖音热榜 TOP 5
======================================================================

 1. 国防部正告日方
    🔥 热度: 11,849,702
    🏷️ 标签: 3
    🔗 链接: https://www.douyin.com/search/%E5%9B%BD%E9%98%B2%E9%83%A8%E6%AD%A3%E5%91%8A%E6%97%A5%E6%96%B9

 2. 中国女篮81:68马里女篮
    🔥 热度: 11,776,764
    🏷️ 标签: 1
    🔗 链接: https://www.douyin.com/search/%E4%B8%AD%E5%9B%BD%E5%A5%B3%E7%AF%AE81%3A68%E9%A9%AC%E9%87%8C%E5%A5%B3%E7%AF%AE
```

**注意：** 链接为纯文本 URL，可直接复制使用，无 HTML 标签包装。

## 返回数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | number | 榜单排名（从 1 开始） |
| title | string | 热点标题 |
| popularity | number | 热度值（HotValue，已转为数字；解析失败时为 0） |
| link | string | 热点详情链接 |
| **cover** | **string \\| null** | **封面图 URL（新增）** |
| label | string \\| null | 标签/标识 |
| type | string | 内容类型（视频、音乐、挑战赛等） |

## 版本更新日志

### v1.1.0 (2025-02-27)

- ✨ **新增封面图字段**
- ✨ 优化数据输出格式
- ✨ 改进错误处理机制

### v1.0.0

- 初始版本
- 支持基本热榜获取

## 数据来源

抖音网页端公开接口

## 注意事项

- 该接口为网页端公开接口，返回结构可能变动
- 访问频繁可能触发风控
- **封面图：** 并非所有热点都有封面图，部分条目可能为空
"""
with open(os.path.join(workspace, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# Create the mock douyin.js script with realistic output
# It will generate exactly N items when called: node scripts/douyin.js hot N
# Items alternate: even-indexed ones have cover URLs, odd-indexed ones have null covers
# Some items have label=null, some have labels
# Popularity is always a big integer

douyin_js = r"""#!/usr/bin/env node

const args = process.argv.slice(2);
const cmd = args[0];
const limit = parseInt(args[1]) || 50;

if (cmd !== 'hot') {
    console.error('Unknown command. Use: node scripts/douyin.js hot [N]');
    process.exit(1);
}

const mockData = [];
const titles = [
    "国防部正告日方", "中国女篮81:68马里女篮", "神舟二十号发射成功",
    "全国暴雨红色预警", "杭州亚运会开幕式", "华为发布新款手机",
    "A股突破3500点", "台风路径最新消息", "诺贝尔物理学奖揭晓",
    "冬奥会中国夺金", "嫦娥七号任务启动", "全国高考成绩发布",
    "特斯拉降价风波", "世界杯预选赛中国队", "故宫夜游开放",
    "央行降准降息", "北京初雪落下", "新冠疫苗更新接种",
    "刘翔回忆录发布", "乒乓球世界冠军赛", "深圳楼市新政",
    "人工智能立法出台", "长三角一体化新规", "黄河流域治理成果",
    "大熊猫新生双胞胎", "敦煌文物数字修复", "南海巡逻新进展",
    "国产大飞机首航", "网络安全法修订", "北斗导航系统升级",
    "冰雪经济热潮", "农村振兴新政策", "海南自贸港进展",
    "粤港澳大湾区建设", "中医药国际推广", "清洁能源占比新高",
    "芯片自主化突破", "航母编队南海演习", "青藏铁路扩能改造",
    "港珠澳大桥通车周年", "大运河申遗成果", "黑洞照片更新发布",
    "月球土壤研究成果", "深海探测器下潜记录", "国产操作系统进展",
    "义乌出口创新高", "中非合作论坛峰会", "数字人民币推广",
    "老龄化社会新政策", "高校扩招最新消息",
];
const types = ["视频", "话题", "挑战赛", "音乐", "视频", "话题", "挑战赛", "视频"];
const basePopularity = 11849702;

for (let i = 0; i < Math.min(limit, titles.length); i++) {
    const hasCover = (i % 3 !== 2); // every 3rd item has no cover
    const hasLabel = (i % 4 !== 1); // every 4th item has no label
    mockData.push({
        rank: i + 1,
        title: titles[i],
        popularity: basePopularity - i * 73412,
        link: `https://www.douyin.com/search/${encodeURIComponent(titles[i])}`,
        cover: hasCover ? `https://p3-sign.douyinpic.com/tos-cn-i-0813/${i+1}abcdef~tplv-dy-crop-center.jpeg` : null,
        label: hasLabel ? String(i % 5 + 1) : null,
        type: types[i % types.length],
    });
}

// Print human-readable output matching SKILL.md format
console.log(`🔥 抖音热榜 TOP ${mockData.length}`);
console.log('======================================================================');
console.log('');
for (const item of mockData) {
    const popStr = item.popularity.toLocaleString('en-US');
    console.log(` ${item.rank}. ${item.title}`);
    console.log(`    🔥 热度: ${popStr}`);
    if (item.label !== null) {
        console.log(`    🏷️ 标签: ${item.label}`);
    }
    console.log(`    🔗 链接: ${item.link}`);
    if (item.cover) {
        console.log(`    🖼️ 封面: ${item.cover}`);
    }
    console.log('');
}
"""

scripts_dir = os.path.join(workspace, "scripts")
douyin_path = os.path.join(scripts_dir, "douyin.js")
with open(douyin_path, "w", encoding="utf-8") as f:
    f.write(douyin_js)

# Make it executable
os.chmod(douyin_path, os.stat(douyin_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files) + 2} (distractor files + SKILL.md + douyin.js)")