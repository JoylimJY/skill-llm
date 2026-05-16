#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the netease-music-assistant task.
"""
import os
import json
import random
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── 1. Distractor files ─────────────────────────────────────────────────────
distractor_dirs = [
    workspace / "logs",
    workspace / "cache" / "temp",
    workspace / "config" / "backup",
    workspace / "scripts" / "utils",
    workspace / "data" / "raw",
    workspace / "data" / "processed",
    workspace / "tmp" / "sessions",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor JSON files
(workspace / "config" / "backup" / "old-preference-v1.json").write_text(json.dumps({
    "version": 1,
    "keywords": ["old", "deprecated"],
    "updatedAt": "2024-01-01T00:00:00.000Z"
}, indent=2))

(workspace / "logs" / "app.log").write_text(
    "2026-06-01 10:00:00 INFO  Starting music assistant\n"
    "2026-06-01 10:00:01 DEBUG Loaded config\n"
    "2026-06-01 10:00:02 INFO  Connected to NCM API\n"
)

(workspace / "logs" / "error.log").write_text(
    "2026-05-30 22:13:44 ERROR Failed to fetch playlist: timeout\n"
)

(workspace / "cache" / "temp" / "session_abc123.json").write_text(json.dumps({
    "session": "abc123",
    "expires": "2026-06-01T12:00:00Z"
}))

(workspace / "scripts" / "utils" / "helper.sh").write_text(
    "#!/bin/bash\necho 'helper utility'\n"
)

(workspace / "data" / "raw" / "songs_dump.csv").write_text(
    "id,name,artist,duration\n"
    "1234567,Test Song,Test Artist,240000\n"
    "7654321,Another Song,Another Artist,180000\n"
)

(workspace / "data" / "processed" / "stats.json").write_text(json.dumps({
    "totalSongs": 200,
    "processed": True,
    "genres": ["pop", "rock", "jazz"]
}))

(workspace / "tmp" / "sessions" / "active.lock").write_text("locked")

(workspace / "config" / "app-config.yaml").write_text(
    "server:\n  host: localhost\n  port: 3000\ndebug: false\n"
)

(workspace / "scripts" / "deploy.sh").write_text(
    "#!/bin/bash\necho 'deploy script'\n"
)

(workspace / "cache" / "search_cache.json").write_text(json.dumps({
    "lastSearch": "jazz piano",
    "results": [],
    "cachedAt": "2026-05-20T08:00:00Z"
}))

# ── 2. STALE ncm-preference.json (older than 24h to force re-analysis) ──────
stale_time = datetime.now(timezone.utc) - timedelta(hours=36)
stale_preference = {
    "overallProfile": "用户偏好轻音乐和流行乐",
    "recentTrend": "近期多听纯音乐",
    "keywords": ["轻音乐", "流行"],
    "temporalPattern": {
        "peakHours": ["22-24"],
        "peakDays": ["weekday-evening"],
        "cycleSummary": "工作日深夜集中红心，以放松类为主"
    },
    "contentTags": ["轻音乐", "流行", "华语"],
    "updatedAt": stale_time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{stale_time.microsecond//1000:03d}Z"
}
ncm_config_dir = Path("/root/.config/ncm")
ncm_config_dir.mkdir(parents=True, exist_ok=True)
(ncm_config_dir / "ncm-preference.json").write_text(json.dumps(stale_preference, ensure_ascii=False, indent=2))

# ── 3. ncm-history.json with some already-recommended playlists ─────────────
# These IDs must appear in mock search results so deduplication is tested
already_recommended = {
    "recommendedPlaylists": [
        {"id": "3778678", "name": "深夜放松轻音乐", "recommendedAt": "2026-06-01T08:00:00.000Z"},
        {"id": "2145765628", "name": "纯音乐精选", "recommendedAt": "2026-05-31T20:00:00.000Z"},
        {"id": "19723756", "name": "爵士咖啡馆", "recommendedAt": "2026-05-30T10:00:00.000Z"},
    ]
}
(ncm_config_dir / "ncm-history.json").write_text(json.dumps(already_recommended, ensure_ascii=False, indent=2))

# ── 4. Mock ncm-cli script (returns deterministic data) ─────────────────────
# The mock will handle:
#   - playlist liked (heartbeat songs)
#   - search playlist/album/song
#   - playlist collected
#   - playlist create
#   - playlist tracks add

mock_ncm_cli = r"""#!/usr/bin/env python3
import sys
import json
import hashlib

args = sys.argv[1:]

def make_hex_id(numeric_id):
    # Simulate an encrypted ID (32-char hex) - this is the WRONG format for links
    return hashlib.md5(str(numeric_id).encode()).hexdigest()

# Simulated heartbeat/liked songs
LIKED_SONGS = [
    # Recent 20 songs (indices 0-19) - used for recentTrend
    {"id": "101", "name": "夜的第七章", "artists": [{"name": "周杰伦"}], "album": {"name": "依然范特西"}, 
     "duration": 237000, "songTag": ["华语", "流行", "R&B"],
     "extMap": {"addTime": 1748390400000}},  # 2025-05-28 00:00 UTC
    {"id": "102", "name": "稻香", "artists": [{"name": "周杰伦"}], "album": {"name": "魔杰座"},
     "duration": 223000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1748304000000}},
    {"id": "103", "name": "告白气球", "artists": [{"name": "周杰伦"}], "album": {"name": "周杰伦的床边故事"},
     "duration": 215000, "songTag": ["华语", "流行", "情歌"],
     "extMap": {"addTime": 1748217600000}},
    {"id": "104", "name": "青花瓷", "artists": [{"name": "周杰伦"}], "album": {"name": "我很忙"},
     "duration": 239000, "songTag": ["华语", "古风", "流行"],
     "extMap": {"addTime": 1748131200000}},
    {"id": "105", "name": "晴天", "artists": [{"name": "周杰伦"}], "album": {"name": "叶惠美"},
     "duration": 269000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1748044800000}},
    {"id": "106", "name": "Simple Love", "artists": [{"name": "周杰伦"}], "album": {"name": "范特西"},
     "duration": 234000, "songTag": ["华语", "流行", "R&B"],
     "extMap": {"addTime": 1747958400000}},
    {"id": "107", "name": "以父之名", "artists": [{"name": "周杰伦"}], "album": {"name": "叶惠美"},
     "duration": 438000, "songTag": ["华语", "嘻哈", "流行"],
     "extMap": {"addTime": 1747872000000}},
    {"id": "108", "name": "退后", "artists": [{"name": "周杰伦"}], "album": {"name": "叶惠美"},
     "duration": 270000, "songTag": ["华语", "流行", "R&B"],
     "extMap": {"addTime": 1747785600000}},
    {"id": "109", "name": "止战之殇", "artists": [{"name": "周杰伦"}], "album": {"name": "十一月的萧邦"},
     "duration": 250000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1747699200000}},
    {"id": "110", "name": "菊花台", "artists": [{"name": "周杰伦"}], "album": {"name": "依然范特西"},
     "duration": 288000, "songTag": ["华语", "古风", "流行"],
     "extMap": {"addTime": 1747612800000}},
    {"id": "111", "name": "千里之外", "artists": [{"name": "周杰伦"}, {"name": "费玉清"}], "album": {"name": "依然范特西"},
     "duration": 265000, "songTag": ["华语", "流行", "古风"],
     "extMap": {"addTime": 1747526400000}},
    {"id": "112", "name": "发如雪", "artists": [{"name": "周杰伦"}], "album": {"name": "十一月的萧邦"},
     "duration": 262000, "songTag": ["华语", "古风"],
     "extMap": {"addTime": 1747440000000}},
    {"id": "113", "name": "东风破", "artists": [{"name": "周杰伦"}], "album": {"name": "叶惠美"},
     "duration": 300000, "songTag": ["华语", "古风", "流行"],
     "extMap": {"addTime": 1747353600000}},
    {"id": "114", "name": "七里香", "artists": [{"name": "周杰伦"}], "album": {"name": "七里香"},
     "duration": 329000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1747267200000}},
    {"id": "115", "name": "布拉格广场", "artists": [{"name": "蔡依林"}, {"name": "周杰伦"}], "album": {"name": "城堡"},
     "duration": 266000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1747180800000}},
    {"id": "116", "name": "龙卷风", "artists": [{"name": "周杰伦"}], "album": {"name": "Jay"},
     "duration": 237000, "songTag": ["华语", "流行", "R&B"],
     "extMap": {"addTime": 1747094400000}},
    {"id": "117", "name": "爱在西元前", "artists": [{"name": "周杰伦"}], "album": {"name": "Jay"},
     "duration": 233000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1747008000000}},
    {"id": "118", "name": "黑色幽默", "artists": [{"name": "周杰伦"}], "album": {"name": "Jay"},
     "duration": 300000, "songTag": ["华语", "流行", "R&B"],
     "extMap": {"addTime": 1746921600000}},
    {"id": "119", "name": "可爱女人", "artists": [{"name": "周杰伦"}], "album": {"name": "Jay"},
     "duration": 252000, "songTag": ["华语", "流行"],
     "extMap": {"addTime": 1746835200000}},
    {"id": "120", "name": "完美主义", "artists": [{"name": "周杰伦"}], "album": {"name": "Jay"},
     "duration": 252000, "songTag": ["华语", "流行", "R&B"],
     "extMap": {"addTime": 1746748800000}},
    # Older songs (indices 20-199)
    {"id": "201", "name": "Fly Me To The Moon", "artists": [{"name": "Frank Sinatra"}], "album": {"name": "It Might As Well Be Swing"},
     "duration": 148000, "songTag": ["爵士", "经典"],
     "extMap": {"addTime": 1746662400000}},
    {"id": "202", "name": "Take Five", "artists": [{"name": "Dave Brubeck"}], "album": {"name": "Time Out"},
     "duration": 324000, "songTag": ["爵士", "器乐"],
     "extMap": {"addTime": 1746576000000}},
    {"id": "203", "name": "月光奏鸣曲", "artists": [{"name": "贝多芬"}], "album": {"name": "贝多芬钢琴奏鸣曲"},
     "duration": 900000, "songTag": ["古典", "钢琴", "器乐"],
     "extMap": {"addTime": 1746489600000}},
]
# Fill up to 200 songs with generic entries
for i in range(len(LIKED_SONGS), 200):
    LIKED_SONGS.append({
        "id": str(300 + i),
        "name": f"歌曲{300+i}",
        "artists": [{"name": "艺人A"}],
        "album": {"name": "专辑B"},
        "duration": 200000 + i * 1000,
        "songTag": ["华语", "流行"],
        "extMap": {"addTime": 1746000000000 - i * 86400000}
    })

# Simulated search results for playlists
PLAYLIST_RESULTS = {
    "周杰伦": [
        {"id": "7183729472", "encryptedId": make_hex_id("7183729472"), "name": "周杰伦经典金曲合集", "playCount": 5000000, "trackCount": 88, "coverImgUrl": "https://p2.music.126.net/abc1.jpg"},
        {"id": "3778678", "encryptedId": make_hex_id("3778678"), "name": "深夜放松轻音乐", "playCount": 2000000, "trackCount": 50, "coverImgUrl": "https://p2.music.126.net/abc2.jpg"},  # ALREADY IN HISTORY
        {"id": "859547772", "encryptedId": make_hex_id("859547772"), "name": "周杰伦 青春回忆", "playCount": 3000000, "trackCount": 60, "coverImgUrl": "https://p2.music.126.net/abc3.jpg"},
        {"id": "2306549272", "encryptedId": make_hex_id("2306549272"), "name": "Jay Chou 华语经典", "playCount": 1500000, "trackCount": 45, "coverImgUrl": "https://p2.music.126.net/abc4.jpg"},
    ],
    "华语流行": [
        {"id": "2145765628", "encryptedId": make_hex_id("2145765628"), "name": "纯音乐精选", "playCount": 8000000, "trackCount": 100, "coverImgUrl": "https://p2.music.126.net/xyz1.jpg"},  # ALREADY IN HISTORY
        {"id": "3184080602", "encryptedId": make_hex_id("3184080602"), "name": "华语流行 · 精选100首", "playCount": 12000000, "trackCount": 100, "coverImgUrl": "https://p2.music.126.net/xyz2.jpg"},
        {"id": "5383658", "encryptedId": make_hex_id("5383658"), "name": "华语经典 20年", "playCount": 6000000, "trackCount": 80, "coverImgUrl": "https://p2.music.126.net/xyz3.jpg"},
        {"id": "19723756", "encryptedId": make_hex_id("19723756"), "name": "爵士咖啡馆", "playCount": 900000, "trackCount": 40, "coverImgUrl": "https://p2.music.126.net/xyz4.jpg"},  # ALREADY IN HISTORY
    ],
    "古风": [
        {"id": "901567", "encryptedId": make_hex_id("901567"), "name": "古风意境 · 中国风精选", "playCount": 4000000, "trackCount": 60, "coverImgUrl": "https://p2.music.126.net/gf1.jpg"},
        {"id": "2031574926", "encryptedId": make_hex_id("2031574926"), "name": "唐风宋韵", "playCount": 2500000, "trackCount": 55, "coverImgUrl": "https://p2.music.126.net/gf2.jpg"},
        {"id": "3778678", "encryptedId": make_hex_id("3778678"), "name": "深夜放松轻音乐", "playCount": 2000000, "trackCount": 50, "coverImgUrl": "https://p2.music.126.net/abc2.jpg"},  # ALREADY IN HISTORY (duplicate cross-search)
    ],
    "R&B": [
        {"id": "472407578", "encryptedId": make_hex_id("472407578"), "name": "R&B 精选夜听", "playCount": 7000000, "trackCount": 75, "coverImgUrl": "https://p2.music.126.net/rb1.jpg"},
        {"id": "2145765628", "encryptedId": make_hex_id("2145765628"), "name": "纯音乐精选", "playCount": 8000000, "trackCount": 100, "coverImgUrl": "https://p2.music.126.net/xyz1.jpg"},  # ALREADY IN HISTORY
    ],
}

# Simulate collected playlists (already subscribed)
COLLECTED_PLAYLISTS = [
    {"id": "2031574926", "name": "唐风宋韵"},  # This is in search results - should be excluded
]

# ── Command routing ──────────────────────────────────────────────────────────
def cmd_liked():
    songs = LIKED_SONGS[:200]
    print(json.dumps({"code": 200, "songs": songs}))

def cmd_search(keyword, search_type="playlist", limit=20):
    results = PLAYLIST_RESULTS.get(keyword, [])[:int(limit)]
    if search_type == "playlist":
        print(json.dumps({"code": 200, "result": {"playlists": results, "playlistCount": len(results)}}))
    elif search_type == "album":
        albums = [{"id": r["id"], "encryptedId": r["encryptedId"], "name": r["name"], "artist": {"name": "艺人"}, "coverImgUrl": r["coverImgUrl"]} for r in results]
        print(json.dumps({"code": 200, "result": {"albums": albums}}))
    elif search_type == "song":
        songs_r = [{"id": r["id"], "encryptedId": r["encryptedId"], "name": r["name"], "artists": [{"name": "艺人"}], "album": {"name": "专辑", "coverImgUrl": r["coverImgUrl"]}, "duration": 240000} for r in results]
        print(json.dumps({"code": 200, "result": {"songs": songs_r, "songCount": len(songs_r)}}))
    else:
        print(json.dumps({"code": 200, "result": {}}))

def cmd_collected():
    print(json.dumps({"code": 200, "playlist": COLLECTED_PLAYLISTS}))

def cmd_playlist_create(name):
    print(json.dumps({"code": 200, "id": "9999888777", "name": name}))

def cmd_playlist_tracks_add(playlist_id, track_ids):
    print(json.dumps({"code": 200, "status": "success", "trackCount": len(track_ids.split(","))}))

# Parse arguments
if len(args) == 0:
    print(json.dumps({"code": 400, "error": "no command"}))
    sys.exit(1)

cmd = args[0]

if cmd == "playlist" and len(args) > 1 and args[1] == "liked":
    cmd_liked()
elif cmd == "search":
    keyword = ""
    stype = "playlist"
    limit = 20
    i = 2
    # Parse flags: ncm-cli search --keyword <kw> --type <type> --limit <n>
    while i < len(args):
        if args[i] == "--keyword" and i+1 < len(args):
            keyword = args[i+1]; i += 2
        elif args[i] == "--type" and i+1 < len(args):
            stype = args[i+1]; i += 2
        elif args[i] == "--limit" and i+1 < len(args):
            limit = int(args[i+1]); i += 2
        else:
            i += 1
    cmd_search(keyword, stype, limit)
elif cmd == "playlist" and len(args) > 1 and args[1] == "collected":
    cmd_collected()
elif cmd == "playlist" and len(args) > 1 and args[1] == "create":
    name = args[2] if len(args) > 2 else "新建歌单"
    cmd_playlist_create(name)
elif cmd == "playlist" and len(args) > 1 and args[1] == "tracks" and len(args) > 2 and args[2] == "add":
    playlist_id = ""
    track_ids = ""
    i = 3
    while i < len(args):
        if args[i] == "--playlist-id" and i+1 < len(args):
            playlist_id = args[i+1]; i += 2
        elif args[i] == "--track-ids" and i+1 < len(args):
            track_ids = args[i+1]; i += 2
        else:
            i += 1
    cmd_playlist_tracks_add(playlist_id, track_ids)
else:
    print(json.dumps({"code": 400, "error": f"unknown command: {' '.join(args)}"}))
"""

# Write the mock script
mock_script_path = Path("/usr/local/bin/ncm-cli")
mock_script_path.write_text(mock_ncm_cli)
mock_script_path.chmod(0o755)

# ── 5. Write task instruction file ─────────────────────────────────────────
# The agent reads the task from the prompt; we just set up the environment.
# BUT we include a task.txt as the "inbox" for the agent
task_txt = """## 任务说明

请帮我完成以下音乐助手工作：

1. 分析我的红心歌单，了解我的音乐偏好（如果偏好缓存已过期，请重新分析）
2. 基于我的偏好，为我推荐适合周末傍晚收听的歌单（请排除已推荐过的内容）
3. 帮我设置：每天早上 8:30 自动推送一次音乐推荐
4. 请将推荐结果输出到文件 recommendation_output.md

注意：任务 3 的调度配置除了写入配置文件，还需要注册到系统定时任务中生效。
"""
(workspace / "task.txt").write_text(task_txt)

print("✅ Workspace generated successfully.")
print(f"   - Stale preference cache: /root/.config/ncm/ncm-preference.json")
print(f"   - History with 3 excluded IDs: /root/.config/ncm/ncm-history.json")
print(f"   - Mock ncm-cli: /usr/local/bin/ncm-cli")
print(f"   - Task file: {workspace}/task.txt")