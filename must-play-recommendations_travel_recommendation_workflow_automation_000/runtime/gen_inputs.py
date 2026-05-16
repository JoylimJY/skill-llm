import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "travel_platform/config",
    "travel_platform/logs",
    "travel_platform/cache/poi",
    "travel_platform/cache/flights",
    "travel_platform/data/cities",
    "travel_platform/data/attractions",
    "travel_platform/scripts/utils",
    "travel_platform/scripts/parsers",
    "travel_platform/reports/draft",
    "travel_platform/reports/final",
    "travel_platform/templates",
    "travel_platform/tests",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "travel_platform/config/db_config.json": json.dumps({
        "host": "localhost",
        "port": 5432,
        "database": "travel_db",
        "user": "admin"
    }, indent=2),
    "travel_platform/config/app_settings.yaml": """
app:
  name: TravelRecommender
  version: 2.1.0
  debug: false
cache:
  ttl: 3600
  max_size: 1000
""",
    "travel_platform/logs/error.log": """2026-04-01 08:23:11 ERROR Failed to fetch poi data for city: 拉萨
2026-04-01 09:45:02 ERROR Timeout on ai-search query
2026-04-01 11:12:33 WARN Rate limit approaching for search-poi
""",
    "travel_platform/logs/access.log": """2026-04-01 08:00:00 GET /api/search?city=北京 200 OK
2026-04-01 08:01:00 GET /api/recommend?city=上海 200 OK
2026-04-01 08:02:00 GET /api/poi?city=成都&level=4 200 OK
""",
    "travel_platform/data/cities/china_cities.json": json.dumps({
        "cities": ["北京", "上海", "成都", "西安", "杭州", "广州", "深圳", "重庆", "武汉", "南京"],
        "total": 10
    }, indent=2),
    "travel_platform/data/attractions/sample_5a.json": json.dumps({
        "note": "This is stale cached data - DO NOT USE",
        "city": "成都",
        "attractions": [
            {"name": "都江堰", "level": "5A"},
            {"name": "峨眉山", "level": "5A"}
        ]
    }, indent=2),
    "travel_platform/data/attractions/ticket_rules.txt": """LEGACY TICKET RULES (DEPRECATED v1.0)
FREE: No charge
PAID: Check price
UNKNOWN: Contact venue
Note: These rules are outdated, do not apply them.
""",
    "travel_platform/scripts/utils/date_helper.py": """import datetime

def get_today():
    return datetime.date.today().isoformat()

def format_timestamp(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')
""",
    "travel_platform/scripts/parsers/json_parser.py": """import json

def parse_poi_response(raw):
    data = json.loads(raw)
    return data.get('data', {}).get('itemList', [])

def parse_ai_response(raw):
    data = json.loads(raw)
    return data.get('data', '')
""",
    "travel_platform/scripts/parsers/markdown_formatter.py": """# Old formatter - OUTDATED
# This formatter uses a different format than current spec
def format_attraction(name, address):
    return f'## {name}\\nAddress: {address}\\n'
""",
    "travel_platform/templates/recommendation_template.md": """# City Attractions
This is an old template. Format may not match current spec.
## Attractions
- Attraction 1
- Attraction 2
""",
    "travel_platform/tests/test_search.py": """import unittest

class TestSearch(unittest.TestCase):
    def test_poi_search(self):
        # Placeholder test
        pass
    def test_ai_search(self):
        # Placeholder test
        pass
""",
    "travel_platform/reports/draft/chengdu_old_report.md": """# 成都景点推荐 (旧版草稿 - 2025年)
此报告已过期，请重新生成。
- 都江堰
- 峨眉山风景区
""",
    "travel_platform/cache/poi/beijing_5a.json": json.dumps({
        "cached_at": "2025-01-01",
        "city": "北京",
        "items": ["故宫", "颐和园", "长城"]
    }, indent=2),
    "travel_platform/cache/flights/cache_index.txt": "Cache entries: 1024\nLast cleared: 2026-03-15\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Create a misleading "instructions" file that has WRONG format info
wrong_instructions = """INTERNAL MEMO - DO NOT FOLLOW
Subject: Chengdu Report Format (SUPERSEDED)

Format attractions as plain text list:
1. Name | Address | Level
2. ...

Only include 5A attractions. No need for ai-search.
Ticket info: just write "paid" or "free".
"""
with open(os.path.join(workspace, "travel_platform/reports/draft/format_instructions_OLD.txt"), 'w', encoding='utf-8') as f:
    f.write(wrong_instructions)

# Create a task brief file (the actual task context for the agent)
task_brief = """TASK BRIEF
==========
Customer Service Request #20260401-CD

A user has sent the following message to our travel assistant:
"请问成都有什么必玩景点？帮我推荐一下！"

Please produce a comprehensive attraction recommendation report for Chengdu (成都).
Save the final report as: chengdu_recommendations.md
"""
with open(os.path.join(workspace, "task_brief.txt"), 'w', encoding='utf-8') as f:
    f.write(task_brief)

print("Workspace generated successfully.")