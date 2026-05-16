import os
import json
import time
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

# Beijing timezone
BEIJING_TZ = timezone(timedelta(hours=8))
now_beijing = datetime.now(BEIJING_TZ)
today_beijing = now_beijing.date()

# Yesterday and two days ago for distractors
yesterday = today_beijing - timedelta(days=1)
two_days_ago = today_beijing - timedelta(days=2)

BASE = Path("/root/.openclaw")
WORKSPACE = BASE / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)

# Team members per SKILL.md
AGENTS = [
    ("main",      "芮芮",  "总助理",         "📋"),
    ("architect", "小明",  "系统架构师",      "🏗️"),
    ("ops",       "小王",  "运维工程师",      "🔧"),
    ("stock",     "小钱",  "股票助手",        "💰"),
    ("xiaolan",   "小蓝",  "浏览器操作助手",  "🌐"),
    ("content",   "小圆",  "内容写手",        "📝"),
    ("aigf",      "aigf",  "临时项目开发",    "💕"),
    ("xiaotian",  "小天",  "灵感记录",        "✨"),
]

# Today's work messages per agent (realistic, varied)
TODAY_MESSAGES = {
    "main": [
        "DM from ou_abc123: 帮我整理一下今天的会议纪要",
        "DM from ou_abc123: 帮我整理一下今天的会议纪要",  # duplicate
        "DM from ou_def456: 查询一下本周的团队进度",
        "DM from ou_ghi789: 发送日报给所有成员",
    ],
    "architect": [
        "DM from ou_arch001: 设计微服务拆分方案",
        "DM from ou_arch001: 评审API接口文档",
        "DM from ou_arch002: 数据库schema优化建议",
        "DM from ou_arch001: 设计微服务拆分方案",  # duplicate
    ],
    "ops": [
        "DM from ou_ops001: 检查服务器CPU使用率",
        "DM from ou_ops002: 更新Docker镜像到最新版本",
        "DM from ou_ops001: 检查服务器CPU使用率",  # duplicate
        "DM from ou_ops003: 配置监控告警规则",
    ],
    "stock": [
        "DM from ou_stock01: 分析今日A股大盘走势",
        "DM from ou_stock02: 查询贵州茅台最新股价",
    ],
    "xiaolan": [
        "DM from ou_blue01: 帮我打开淘宝搜索耳机",
        "DM from ou_blue02: 截图当前页面",
        "DM from ou_blue01: 帮我打开淘宝搜索耳机",  # duplicate
    ],
    "content": [
        "DM from ou_cont01: 写一篇关于AI发展的文章",
        "DM from ou_cont02: 优化产品介绍文案",
        "DM from ou_cont03: 生成5条社交媒体推文",
    ],
    "aigf": [],  # no work today
    "xiaotian": [
        "DM from ou_xt001: 记录一个关于量子计算的灵感",
        "DM from ou_xt001: 记录一个关于量子计算的灵感",  # duplicate
        "DM from ou_xt002: 整理本周的创意想法",
    ],
}

# Yesterday's distractor messages
YESTERDAY_MESSAGES = {
    "main": ["DM from ou_abc123: 昨天的工作内容"],
    "architect": ["DM from ou_arch001: 昨天设计了数据库"],
    "ops": ["DM from ou_ops001: 昨天重启了服务器"],
}

def make_jsonl_record(text, ts_offset_seconds=0):
    """Create a realistic JSONL record in the expected format."""
    ts = now_beijing.timestamp() + ts_offset_seconds
    record = {
        "type": "message",
        "timestamp": ts,
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
    }
    return json.dumps(record, ensure_ascii=False)

def make_noise_record(text):
    """Create a non-message record (distractor)."""
    record = {
        "type": "tool_call",
        "timestamp": now_beijing.timestamp(),
        "tool": "search",
        "input": text
    }
    return json.dumps(record, ensure_ascii=False)

def make_assistant_record(text):
    """Create an assistant message record (should NOT be extracted)."""
    record = {
        "type": "message",
        "timestamp": now_beijing.timestamp(),
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
    }
    return json.dumps(record, ensure_ascii=False)

# Generate session files for today and distractors
for agent_id, name, role, emoji in AGENTS:
    sessions_dir = BASE / "agents" / agent_id / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create today's session file
    session_id_today = f"sess_{agent_id}_{today_beijing.strftime('%Y%m%d')}_001"
    today_file = sessions_dir / f"{session_id_today}.jsonl"
    
    messages_today = TODAY_MESSAGES.get(agent_id, [])
    lines = []
    
    # Add some noise records first
    lines.append(make_noise_record(f"系统初始化 {agent_id}"))
    lines.append(json.dumps({"type": "session_start", "agent_id": agent_id, "timestamp": now_beijing.timestamp()}, ensure_ascii=False))
    
    for i, msg in enumerate(messages_today):
        lines.append(make_jsonl_record(msg, ts_offset_seconds=i*60))
        # Intersperse assistant responses
        lines.append(make_assistant_record(f"好的，我来处理：{msg}"))
        lines.append(make_noise_record(f"执行工具调用 step {i}"))
    
    # Also add a non-DM user message (should NOT be extracted)
    lines.append(make_jsonl_record("系统消息：请更新状态", ts_offset_seconds=len(messages_today)*60 + 30))
    
    today_file.write_text("\n".join(lines), encoding="utf-8")
    
    # Set mtime to today (Beijing time) - use current time
    current_ts = now_beijing.timestamp()
    os.utime(str(today_file), (current_ts, current_ts))
    
    # Create yesterday's session file (DISTRACTOR - should NOT be used)
    session_id_yesterday = f"sess_{agent_id}_{yesterday.strftime('%Y%m%d')}_001"
    yesterday_file = sessions_dir / f"{session_id_yesterday}.jsonl"
    
    yesterday_msgs = YESTERDAY_MESSAGES.get(agent_id, [f"DM from ou_old001: 昨日{name}的工作内容"])
    y_lines = []
    y_lines.append(json.dumps({"type": "session_start", "agent_id": agent_id}, ensure_ascii=False))
    for msg in yesterday_msgs:
        y_lines.append(make_jsonl_record(msg, ts_offset_seconds=-86400))
    yesterday_file.write_text("\n".join(y_lines), encoding="utf-8")
    
    # Set mtime to yesterday
    yesterday_ts = current_ts - 86400
    os.utime(str(yesterday_file), (yesterday_ts, yesterday_ts))
    
    # Create an older session file (DISTRACTOR)
    session_id_old = f"sess_{agent_id}_{two_days_ago.strftime('%Y%m%d')}_001"
    old_file = sessions_dir / f"{session_id_old}.jsonl"
    old_lines = [
        json.dumps({"type": "session_start"}, ensure_ascii=False),
        make_jsonl_record(f"DM from ou_old999: 两天前的旧工作内容 for {agent_id}", ts_offset_seconds=-172800),
    ]
    old_file.write_text("\n".join(old_lines), encoding="utf-8")
    old_ts = current_ts - 172800
    os.utime(str(old_file), (old_ts, old_ts))
    
    # Create a second today session for some agents (to test "latest" file logic)
    if agent_id in ["architect", "ops", "main"]:
        session_id_today2 = f"sess_{agent_id}_{today_beijing.strftime('%Y%m%d')}_002"
        today_file2 = sessions_dir / f"{session_id_today2}.jsonl"
        extra_lines = [
            json.dumps({"type": "session_start", "agent_id": agent_id}, ensure_ascii=False),
            make_jsonl_record(f"DM from ou_extra01: 额外的{name}工作内容（第二个session）", ts_offset_seconds=3600),
        ]
        today_file2.write_text("\n".join(extra_lines), encoding="utf-8")
        # This file has a slightly newer mtime (latest)
        os.utime(str(today_file2), (current_ts + 3600, current_ts + 3600))

# Create distractor files in workspace
WORKSPACE_DISTRACTORS = [
    ("old-report-2024-01-01.md", "# 旧日报\n一些旧的内容"),
    ("config.json", '{"version": "1.0", "team": "ai-assistants"}'),
    ("notes.txt", "一些随机的笔记内容\n不相关的信息"),
    ("template.md", "# 模板文件\n这是一个示例模板，不是正式日报"),
    ("team-config.yaml", "agents:\n  - main\n  - architect\n  - ops"),
    ("archive/daily-report-2024-12-01.md", "# 12月1日日报\n旧内容"),
    ("logs/system.log", "2024-01-01 00:00:00 INFO system started\n2024-01-01 00:01:00 INFO all agents ready"),
    ("temp/draft.md", "# 草稿\n未完成的内容"),
    ("scripts/collect.py", "# 数据收集脚本\nprint('collecting...')"),
    ("reports/weekly-summary.md", "# 周报\n本周总结"),
]

for rel_path, content in WORKSPACE_DISTRACTORS:
    full_path = WORKSPACE / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# Create distractor agent directories that are NOT in the team config
extra_agent_dir = BASE / "agents" / "unknown_bot" / "sessions"
extra_agent_dir.mkdir(parents=True, exist_ok=True)
extra_session = extra_agent_dir / "sess_unknown_20240101_001.jsonl"
extra_session.write_text(
    json.dumps({"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "DM from ou_hack01: 这是一个未知bot的消息"}]}}, ensure_ascii=False),
    encoding="utf-8"
)

print(f"Setup complete. Today (Beijing): {today_beijing}")
print(f"Sessions created for agents: {[a[0] for a in AGENTS]}")
print(f"Workspace distractors: {len(WORKSPACE_DISTRACTORS)} files")