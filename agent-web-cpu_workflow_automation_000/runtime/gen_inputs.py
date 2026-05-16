import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# Create deeply nested distractor structure
distractor_dirs = [
    "projects/blog_tool/src",
    "projects/blog_tool/tests",
    "projects/blog_tool/config",
    "projects/seo_suite/scripts",
    "projects/seo_suite/data",
    "archives/2024/q1",
    "archives/2024/q2",
    "logs/access",
    "logs/error",
    "tmp/cache",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "projects/blog_tool/src/main.py": "# main entry\ndef run(): pass\n",
    "projects/blog_tool/src/utils.py": "import re\ndef slugify(s): return re.sub(r'[^a-z0-9]', '-', s.lower())\n",
    "projects/blog_tool/tests/test_main.py": "def test_run(): assert True\n",
    "projects/blog_tool/config/settings.ini": "[app]\ndebug=false\nport=8080\n",
    "projects/seo_suite/scripts/crawl.sh": "#!/bin/bash\ncurl -s https://example.com\n",
    "projects/seo_suite/data/keywords.csv": "keyword,volume\nAI写作,5000\n博客优化,3200\n内容营销,4100\n",
    "archives/2024/q1/report.txt": "Q1 traffic: 12000 visits\n",
    "archives/2024/q2/report.txt": "Q2 traffic: 15800 visits\n",
    "logs/access/2024-12.log": "GET / 200\nGET /api 404\n",
    "logs/error/2024-12.log": "ERROR: timeout on /api/v2\n",
    "tmp/cache/session.bin": "BINARYDATA\x00\x01\x02\n",
}
for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content, encoding="utf-8", errors="replace")

# Create the SKILL_DIR for the agent-web-cpu skill
skill_dir = workspace / "skills" / "agent-web-cpu"
skill_dir.mkdir(parents=True, exist_ok=True)

# Create a MESSY, partially outdated apps.json (missing _schema, old format entries, and one entry with missing fields)
# The agent must recognize this needs to be handled according to SKILL.md spec
apps_json = {
    "apps": [
        {
            "id": "35fa46fd2f9b57f814018134ef14ae1f",
            "name": "博文框架",
            "description": "内容策划编辑：生成高效的文章标题与创作大纲",
            "keywords": ["博文", "文章", "大纲", "写作", "标题"],
            "createdAt": "2026-04-01T08:49:00+08:00"
        },
        {
            "id": "cc2a9e1f4d3b8c7e6f5a0912345678ab",
            "name": "爆款润色助手",
            "description": "将普通文章改写为吸引眼球的爆款内容，提升传播力",
            "keywords": ["润色", "改写", "爆款", "传播", "吸引"],
            "createdAt": "2026-04-10T10:00:00+08:00"
        },
        {
            "id": "deadbeef1234567890abcdef01020304",
            "name": "SEO关键词优化",
            "description": "分析并优化文章的SEO关键词，提升搜索引擎排名",
            "keywords": ["SEO", "关键词", "搜索", "排名", "优化"],
            "createdAt": "2026-04-15T14:30:00+08:00"
        }
    ]
    # NOTE: deliberately missing "_schema" key to make it messy/outdated
}
(skill_dir / "apps.json").write_text(json.dumps(apps_json, ensure_ascii=False, indent=2), encoding="utf-8")

# Create a task description file that the agent should NOT treat as hints
# (just context documents, no solution hints)
(workspace / "task_context" ).mkdir(parents=True, exist_ok=True)
(workspace / "task_context" / "new_app_request.txt").write_text(
    "申请注册新应用\n"
    "应用ID: f7e6d5c4b3a291807f6e5d4c3b2a1908\n"
    "来源: 内容运营团队\n"
    "用途: 用于生成科技博客正文内容\n",
    encoding="utf-8"
)
(workspace / "task_context" / "cleanup_request.txt").write_text(
    "请移除已废弃的应用: SEO关键词优化\n"
    "原因: 该功能已整合到其他工具中，不再单独使用\n",
    encoding="utf-8"
)
(workspace / "task_context" / "matching_query.txt").write_text(
    "需要找到最适合处理以下需求的应用:\n"
    "「帮我润色这篇博文，让它变成爆款内容\」\n",
    encoding="utf-8"
)

# Create a mock server script that the agent might use (but it's not a hint - it's part of infrastructure)
# The mock server will be started by setup_script
mock_server_script = '''#!/usr/bin/env python3
"""Mock transweb.cn server for testing app registration."""
from flask import Flask, request, Response
import sys

app = Flask(__name__)

MOCK_APPS = {
    "f7e6d5c4b3a291807f6e5d4c3b2a1908": {
        "name": "科技博客生成器",
        "description": "专业的科技领域博客文章生成工具，支持深度分析与趋势预测",
        "meta": "科技博客生成工具 - 深度内容创作助手"
    }
}

@app.route("/")
def index():
    app_id = request.args.get("id", "")
    if app_id in MOCK_APPS:
        data = MOCK_APPS[app_id]
        html = f"""<!DOCTYPE html>
<html>
<head>
<title>{data["meta"]}</title>
<meta name="description" content="{data["description"]}">
</head>
<body>
<h1>{data["name"]}</h1>
<p class="subtitle">{data["description"]}</p>
<div class="app-info">
  <span>应用ID: {app_id}</span>
</div>
</body>
</html>"""
        return Response(html, mimetype="text/html")
    return Response("<html><body><h1>应用未找到</h1></body></html>", status=404, mimetype="text/html")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7788
    app.run(host="0.0.0.0", port=port, debug=False)
'''
(workspace / "mock_transweb_server.py").write_text(mock_server_script, encoding="utf-8")

# Create a hosts-override note (the agent needs to know the mock server is at localhost:7788)
# but we don't tell them HOW to solve - just that the transweb.cn simulation is at localhost:7788
(workspace / "task_context" / "environment_info.txt").write_text(
    "测试环境说明:\n"
    "本地模拟服务已在 http://localhost:7788 运行，模拟 transweb.cn 的应用信息接口。\n"
    "获取应用信息时，请使用 http://localhost:7788/?id={app_id} 替代 https://transweb.cn/?id={app_id}\n",
    encoding="utf-8"
)

print(f"Workspace initialized at: {workspace}")
print(f"Skill directory: {skill_dir}")
print(f"apps.json created with 3 apps (missing _schema key)")