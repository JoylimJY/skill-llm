import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create realistic directory structure with distractor files
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "config",
    "logs",
    "src/utils",
    "src/parsers",
    "tests",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic project files that should NOT mislead the agent
distractor_files = {
    "config/app.yaml": """
app_name: content-analytics
version: 1.2.0
environment: production
database:
  host: localhost
  port: 5432
  name: analytics_db
cache:
  ttl: 3600
""",
    "config/categories_old.json": json.dumps([
        {"id": "OUTDATED_001", "name": "前端"},
        {"id": "OUTDATED_002", "name": "后端"},
        {"id": "OUTDATED_003", "name": "AI"}
    ], ensure_ascii=False, indent=2),
    "data/raw/sample_articles.csv": """title,author,views,likes
Old Article 1,Author A,1000,50
Old Article 2,Author B,2000,100
Old Article 3,Author C,500,20
""",
    "data/processed/summary_2023.json": json.dumps({
        "period": "2023-Q4",
        "total_articles": 1500,
        "note": "This is historical data, not current rankings"
    }, indent=2),
    "logs/scraper.log": """2024-01-15 08:00:01 INFO Starting data collection
2024-01-15 08:00:05 INFO Fetched 20 articles from category 前端
2024-01-15 08:00:07 INFO Fetched 20 articles from category 后端
2024-01-15 08:00:09 WARNING Rate limit approaching
2024-01-15 08:00:10 INFO Collection complete
""",
    "src/utils/helpers.js": """
// Utility functions
function formatDate(timestamp) {
    return new Date(timestamp).toISOString();
}

function calculateScore(views, likes, collects) {
    // Legacy scoring formula - DEPRECATED
    return views * 0.5 + likes * 2;
}

module.exports = { formatDate, calculateScore };
""",
    "src/parsers/json_parser.py": """
import json

def parse_articles(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data

def extract_metrics(article):
    return {
        'title': article.get('title', ''),
        'views': article.get('viewCount', 0),
        'likes': article.get('likeCount', 0),
    }
""",
    "tests/test_parser.py": """
import unittest

class TestParser(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
""",
    "reports/archive/q3_trends.json": json.dumps({
        "quarter": "Q3-2024",
        "top_categories": ["前端", "后端"],
        "note": "Archived report - do not use for current analysis"
    }, ensure_ascii=False, indent=2),
    "reports/drafts/template.md": """# Trends Report Template

## Section 1: Overview
[Insert overview here]

## Section 2: Top Articles by Category
[Insert article data here]

## Section 3: Engagement Analysis
[Insert engagement metrics here]
""",
    "data/raw/category_mapping.txt": """This file contains an UNOFFICIAL mapping - may be outdated.
Frontend -> fe_001
Backend -> be_002
AI -> ai_003
NOTE: Use the official API to get current category IDs
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create the mock juejin.js script that simulates the real tool
# This is the core script the agent must use
mock_juejin_script = r"""#!/usr/bin/env node
'use strict';

const CATEGORIES = [
  { "id": "6809637769959178254", "name": "前端" },
  { "id": "6809637769959178255", "name": "后端" },
  { "id": "6809637769959178256", "name": "Android" },
  { "id": "6809637769959178257", "name": "iOS" },
  { "id": "6809637769959178258", "name": "人工智能" },
  { "id": "6809637769959178260", "name": "开发工具" },
  { "id": "6809637769959178261", "name": "代码人生" },
  { "id": "6809637769959178262", "name": "阅读" }
];

// Deterministic article generation based on category and type
function generateArticles(categoryId, type, limit) {
  const categoryMap = {
    "6809637769959178254": "前端",
    "6809637769959178255": "后端",
    "6809637769959178256": "Android",
    "6809637769959178257": "iOS",
    "6809637769959178258": "人工智能",
    "6809637769959178260": "开发工具",
    "6809637769959178261": "代码人生",
    "6809637769959178262": "阅读"
  };

  const catName = categoryMap[categoryId] || "未知";

  // Seed data per category - deterministic
  const articleTemplates = {
    "6809637769959178254": [
      { title: "深入理解Vue3响应式原理", author: "张三丰", viewCount: 45200, likeCount: 1823, collectCount: 934, commentCount: 267 },
      { title: "React 18新特性完全指南", author: "李小明", viewCount: 38900, likeCount: 1567, collectCount: 823, commentCount: 189 },
      { title: "TypeScript高级类型体操实战", author: "王大锤", viewCount: 52100, likeCount: 2103, collectCount: 1102, commentCount: 341 },
      { title: "前端性能优化：从理论到实践", author: "赵云飞", viewCount: 31400, likeCount: 1234, collectCount: 678, commentCount: 156 },
      { title: "CSS Grid布局完全教程", author: "陈晓华", viewCount: 28700, likeCount: 987, collectCount: 512, commentCount: 98 },
      { title: "Vite vs Webpack深度对比分析", author: "刘建国", viewCount: 41300, likeCount: 1689, collectCount: 891, commentCount: 213 },
      { title: "微前端架构设计与实践", author: "周杰伦", viewCount: 35600, likeCount: 1445, collectCount: 756, commentCount: 178 },
    ],
    "6809637769959178255": [
      { title: "Spring Boot微服务最佳实践", author: "孙悟空", viewCount: 49300, likeCount: 1978, collectCount: 1045, commentCount: 312 },
      { title: "MySQL索引优化深度解析", author: "猪八戒", viewCount: 43800, likeCount: 1756, collectCount: 934, commentCount: 287 },
      { title: "Redis分布式锁实现原理", author: "沙悟净", viewCount: 56700, likeCount: 2234, collectCount: 1189, commentCount: 398 },
      { title: "Kubernetes生产环境部署指南", author: "唐僧", viewCount: 38200, likeCount: 1534, collectCount: 812, commentCount: 201 },
      { title: "Go语言并发编程实战", author: "白龙马", viewCount: 33500, likeCount: 1345, collectCount: 712, commentCount: 167 },
      { title: "分布式事务解决方案对比", author: "哪吒", viewCount: 47100, likeCount: 1890, collectCount: 1001, commentCount: 334 },
      { title: "Elasticsearch实战搜索引擎", author: "二郎神", viewCount: 40600, likeCount: 1623, collectCount: 856, commentCount: 245 },
    ],
    "6809637769959178258": [
      { title: "大模型微调实战：从零开始", author: "爱因斯坦", viewCount: 67800, likeCount: 2789, collectCount: 1456, commentCount: 523 },
      { title: "LangChain构建AI应用完全指南", author: "图灵", viewCount: 58400, likeCount: 2345, collectCount: 1234, commentCount: 456 },
      { title: "Stable Diffusion提示词工程", author: "牛顿", viewCount: 45900, likeCount: 1867, collectCount: 978, commentCount: 312 },
      { title: "RAG检索增强生成技术解析", author: "欧拉", viewCount: 52300, likeCount: 2112, collectCount: 1109, commentCount: 389 },
      { title: "向量数据库选型与实践", author: "高斯", viewCount: 38700, likeCount: 1556, collectCount: 823, commentCount: 234 },
      { title: "ChatGPT API集成开发实战", author: "费曼", viewCount: 71200, likeCount: 2934, collectCount: 1567, commentCount: 612 },
      { title: "强化学习入门到精通", author: "玻尔", viewCount: 33400, likeCount: 1345, collectCount: 712, commentCount: 178 },
    ]
  };

  const defaults = Array.from({length: 20}, (_, i) => ({
    title: `${catName}文章${i+1}`,
    author: `作者${i+1}`,
    viewCount: Math.floor(10000 + i * 1500),
    likeCount: Math.floor(400 + i * 80),
    collectCount: Math.floor(200 + i * 40),
    commentCount: Math.floor(50 + i * 20)
  }));

  const templates = articleTemplates[categoryId] || defaults;

  // For 'new' type, shuffle differently (reverse order as deterministic "new" behavior)
  let articles = [...templates];
  if (type === 'new') {
    articles = articles.reverse();
  }

  return articles.slice(0, parseInt(limit) || 20).map((a, i) => ({
    title: a.title,
    brief: `这是关于${a.title}的精彩摘要，涵盖核心技术要点和实践经验。`,
    author: a.author,
    articleId: `${categoryId}${String(i).padStart(4, '0')}`,
    popularity: a.likeCount + a.collectCount,
    viewCount: a.viewCount,
    likeCount: a.likeCount,
    collectCount: a.collectCount,
    commentCount: a.commentCount,
    url: `https://juejin.cn/post/${categoryId}${String(i).padStart(4, '0')}`,
    tags: [catName, type === 'hot' ? '热门' : '最新']
  }));
}

const args = process.argv.slice(2);
const command = args[0];

if (command === 'categories') {
  console.log(JSON.stringify(CATEGORIES, null, 2));
} else if (command === 'articles') {
  const categoryId = args[1];
  const type = args[2] || 'hot';
  const limit = args[3] || 20;

  if (!categoryId) {
    console.error('Error: category_id is required');
    process.exit(1);
  }

  const articles = generateArticles(categoryId, type, limit);
  console.log(JSON.stringify(articles, null, 2));
} else {
  console.error(`Unknown command: ${command}`);
  console.error('Usage: node scripts/juejin.js <categories|articles> [args...]');
  process.exit(1);
}
"""

with open(os.path.join(workspace, "scripts/juejin.js"), "w", encoding="utf-8") as f:
    f.write(mock_juejin_script)

# Add a few more distractor files
package_json = {
    "name": "content-analytics-tool",
    "version": "2.1.0",
    "description": "Content analytics and trend analysis tool",
    "scripts": {
        "start": "node src/index.js",
        "test": "jest"
    },
    "dependencies": {
        "axios": "^1.4.0",
        "lodash": "^4.17.21"
    }
}
with open(os.path.join(workspace, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# A misleading "old" trends report to confuse agents that don't run the tool
old_trends = {
    "generated_at": "2023-06-01",
    "WARNING": "This file is outdated. Regenerate using the juejin.js tool.",
    "categories": [
        {"id": "WRONG_ID_FRONTEND", "name": "前端", "articles": []},
        {"id": "WRONG_ID_BACKEND", "name": "后端", "articles": []}
    ]
}
with open(os.path.join(workspace, "reports/archive/old_trends_OUTDATED.json"), "w", encoding="utf-8") as f:
    json.dump(old_trends, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")