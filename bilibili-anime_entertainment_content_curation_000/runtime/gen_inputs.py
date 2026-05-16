import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create deeply nested distractor files
dirs = [
    workspace / "entertainment/cache",
    workspace / "entertainment/logs",
    workspace / "entertainment/config",
    workspace / "data/raw/bilibili",
    workspace / "data/processed",
    workspace / "data/archive",
    workspace / "scripts/crawlers",
    workspace / "scripts/parsers",
    workspace / "reports/old",
    workspace / "reports/templates",
    workspace / "tmp",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor: old anime report (wrong format, wrong season, stale)
old_report = """# B站动漫排行 2024

随便列几个番:
- 鬼灭之刃
- 进击的巨人
- 咒术回战
"""
(workspace / "reports/old" / "old_anime_list.txt").write_text(old_report, encoding="utf-8")

# Distractor: raw JSON scrape (messy, incomplete)
raw_scrape = {
    "timestamp": "2023-11-01",
    "source": "bilibili",
    "data": [
        {"title": "某番剧", "views": 1234567, "danmaku": 89012},
        {"title": "另一番剧", "views": None, "danmaku": "unknown"},
    ]
}
(workspace / "data/raw/bilibili" / "scrape_2023.json").write_text(
    json.dumps(raw_scrape, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Distractor: config file referencing old endpoints
config = {
    "api_base": "https://api.bilibili.com/old",
    "season": "2023_autumn",
    "categories": ["action", "romance", "fantasy"],
    "deprecated_endpoint": "/pgc/season/rank/web/list"
}
(workspace / "entertainment/config" / "api_config.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Distractor: logs with noise
log_content = "\n".join([
    "2024-01-15 10:23:11 INFO Fetching anime data...",
    "2024-01-15 10:23:12 ERROR Connection timeout",
    "2024-01-15 10:23:13 INFO Retrying...",
    "2024-01-15 10:23:15 WARN Rate limit hit",
    "2024-01-15 10:23:20 INFO Partial data retrieved: 5/20 entries",
])
(workspace / "entertainment/logs" / "fetch_2024.log").write_text(log_content, encoding="utf-8")

# Distractor: a template with wrong/partial format
template_wrong = """# Anime Rankings

## Top Shows
{shows}

## By Genre
{genre_table}
"""
(workspace / "reports/templates" / "template_v0.md").write_text(template_wrong, encoding="utf-8")

# Distractor: crawler script stub (empty/broken)
crawler_stub = """#!/usr/bin/env python3
# TODO: implement bilibili crawler
import requests

def fetch_rankings():
    pass  # not implemented

if __name__ == '__main__':
    fetch_rankings()
"""
(workspace / "scripts/crawlers" / "bili_crawler.py").write_text(crawler_stub, encoding="utf-8")

# Distractor: parser with irrelevant logic
parser_content = """import re

def parse_episode(text):
    match = re.search(r'第(\\d+)集', text)
    return int(match.group(1)) if match else None

def parse_follower_count(text):
    # expects format like "123.4万"
    match = re.search(r'([\\d.]+)万', text)
    return float(match.group(1)) * 10000 if match else None
"""
(workspace / "scripts/parsers" / "text_parser.py").write_text(parser_content, encoding="utf-8")

# Distractor: processed data that is stale and irrelevant
processed = {
    "season": "2022_spring",
    "processed_at": "2022-04-30",
    "anime": []
}
(workspace / "data/processed" / "season_2022_spring.json").write_text(
    json.dumps(processed, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Distractor: archive with old ranking format
(workspace / "data/archive" / "ranking_2021.csv").write_text(
    "rank,title,score\n1,鬼灭之刃,9.8\n2,奥特曼,8.5\n3,火影忍者,9.1\n",
    encoding="utf-8"
)

# Distractor: tmp file with garbage
(workspace / "tmp" / "session_cache.bin").write_bytes(bytes(random.getrandbits(8) for _ in range(256)))

# Distractor: another config
(workspace / "entertainment/config" / "display_settings.json").write_text(
    json.dumps({"theme": "dark", "lang": "zh-CN", "max_items": 10}, ensure_ascii=False), encoding="utf-8"
)

# NOW: Create the mock server data file that the setup script will use
mock_data = {
    "season_info": {
        "note": "This mock server serves as a local Bilibili data proxy. Query /rankings for hot anime."
    },
    "rankings": [
        {
            "rank": 1,
            "title": "神之塔：新生",
            "is_sequel": False,
            "genres": ["热血", "冒险", "奇幻"],
            "synopsis": "少年贝姆进入神秘的塔，为了见到塔顶上的人踏上征途。塔内每一层都隐藏着残酷的试炼与阴谋。他将与形形色色的同伴和敌人相遇，逐渐揭开塔的秘密。",
            "episode_current": 8,
            "episode_total": 13,
            "update_day": "周三",
            "followers_wan": 142.3,
            "followers_certain": True,
            "danmaku_rank": 1,
            "first_air_this_season": True
        },
        {
            "rank": 2,
            "title": "败犬女主太多了！第二季",
            "is_sequel": True,
            "genres": ["恋爱", "日常", "喜剧"],
            "synopsis": "犬山玉子与苏志原纯太的恋爱关系续篇。上一季末尾的告白余波仍在持续，新的角色加入带来更多混乱与笑点。",
            "episode_current": 5,
            "episode_total": 12,
            "update_day": "周六",
            "followers_wan": 98.7,
            "followers_certain": True,
            "danmaku_rank": 2,
            "first_air_this_season": False
        },
        {
            "rank": 3,
            "title": "偶像大师闪耀色彩 第2季",
            "is_sequel": True,
            "genres": ["音乐", "日常", "偶像"],
            "synopsis": "283Pro的偶像们迎来新的挑战舞台。第二季将聚焦各单元的深层成长与竞争，音乐风格更加多元。",
            "episode_current": 4,
            "episode_total": 13,
            "update_day": "周日",
            "followers_wan": 67.2,
            "followers_certain": True,
            "danmaku_rank": 5,
            "first_air_this_season": False
        },
        {
            "rank": 4,
            "title": "迷宫饭",
            "is_sequel": False,
            "genres": ["奇幻", "冒险", "美食"],
            "synopsis": "勇者莱奥斯的妹妹被龙吃掉，为了在地下迷宫中救出她，一行人开始了以迷宫怪物为食的冒险。结合料理与战斗的独特魅力，每集都有令人垂涎的怪物料理登场。",
            "episode_current": 24,
            "episode_total": 24,
            "update_day": "已完结",
            "followers_wan": None,
            "followers_certain": False,
            "danmaku_rank": 3,
            "first_air_this_season": True
        },
        {
            "rank": 5,
            "title": "暗杀教室 重制版",
            "is_sequel": False,
            "genres": ["热血", "校园", "喜剧"],
            "synopsis": "末日博士变成了章鱼怪教师，要求学生在毕业前杀死自己，否则地球将被摧毁。E班的学生们在杀人训练与青春成长中找到了真正的人生意义。",
            "episode_current": 6,
            "episode_total": 25,
            "update_day": "周五",
            "followers_wan": 88.1,
            "followers_certain": True,
            "danmaku_rank": 4,
            "first_air_this_season": True
        },
        {
            "rank": 6,
            "title": "物语系列 最终季",
            "is_sequel": True,
            "genres": ["悬疑", "奇幻", "日常"],
            "synopsis": "阿良良木历的故事迎来终章。历经多年的物怪缘分将在最终季彻底收束，粉丝期待已久的完结篇。",
            "episode_current": 3,
            "episode_total": 6,
            "update_day": "周四",
            "followers_wan": None,
            "followers_certain": False,
            "danmaku_rank": 6,
            "first_air_this_season": False
        },
        {
            "rank": 7,
            "title": "推特女孩",
            "is_sequel": False,
            "genres": ["恋爱", "日常", "喜剧"],
            "synopsis": "高中生中村在推特上偶然关注了同班同学，却发现对方在网络上展现的是截然不同的一面。线上线下的反差与距离感构成了这部清新爱情故事的核心张力。",
            "episode_current": 7,
            "episode_total": 12,
            "update_day": "周二",
            "followers_wan": 54.6,
            "followers_certain": True,
            "danmaku_rank": 7,
            "first_air_this_season": True
        },
        {
            "rank": 8,
            "title": "我的青春恋爱物语 剧场版",
            "is_sequel": True,
            "genres": ["恋爱", "悬疑"],
            "synopsis": "八幡与雪乃的后续故事在剧场版中延续，原著党期待已久的深度诠释终于到来。",
            "episode_current": 1,
            "episode_total": 1,
            "update_day": "已上映",
            "followers_wan": 45.0,
            "followers_certain": True,
            "danmaku_rank": 9,
            "first_air_this_season": False
        },
        {
            "rank": 9,
            "title": "凶兆侦探事务所",
            "is_sequel": False,
            "genres": ["悬疑", "推理", "超自然"],
            "synopsis": "能看见不吉祥预兆的侦探和擅长解读凶兆的搭档，在神秘都市中调查超自然犯罪事件。每一案件背后都藏着令人意想不到的真相与人性反思。",
            "episode_current": 9,
            "episode_total": 12,
            "update_day": "周一",
            "followers_wan": None,
            "followers_certain": False,
            "danmaku_rank": 8,
            "first_air_this_season": True
        },
        {
            "rank": 10,
            "title": "时光代理人 第二季",
            "is_sequel": True,
            "genres": ["奇幻", "悬疑", "热血"],
            "synopsis": "李子铭与陆光的相册探案之旅再度开启。第二季扩展了时光代理人的世界观，涉及更深层的时间悖论与情感纠葛。",
            "episode_current": 2,
            "episode_total": 16,
            "update_day": "周六",
            "followers_wan": 112.5,
            "followers_certain": True,
            "danmaku_rank": 10,
            "first_air_this_season": False
        }
    ]
}

(workspace / "mock_server_data.json").write_text(
    json.dumps(mock_data, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Create mock server script
mock_server_script = '''#!/usr/bin/env python3
"""
Mock local Bilibili-like data server.
Serves anime ranking data for the current season.
"""
import json
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_FILE = Path("/workspace/mock_server_data.json")

def load_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

@app.route("/rankings", methods=["GET"])
def get_rankings():
    data = load_data()
    return jsonify(data["rankings"])

@app.route("/season_info", methods=["GET"])
def get_season_info():
    data = load_data()
    return jsonify(data["season_info"])

@app.route("/anime/<int:rank>", methods=["GET"])
def get_anime_detail(rank):
    data = load_data()
    for anime in data["rankings"]:
        if anime["rank"] == rank:
            return jsonify(anime)
    return jsonify({"error": "not found"}), 404

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Bilibili mock server running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''

(workspace / "scripts" / "mock_server.py").write_text(mock_server_script, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created in: {workspace.absolute()}")