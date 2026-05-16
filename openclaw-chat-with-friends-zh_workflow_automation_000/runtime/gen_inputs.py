import os
import random

random.seed(42)

# Create a realistic, deeply nested workspace simulating an OpenClaw project directory
base = "/workspace"

# Directory structure
dirs = [
    "openclaw/config",
    "openclaw/sessions",
    "openclaw/logs",
    "openclaw/plugins",
    "openclaw/plugins/telegram",
    "openclaw/plugins/memory",
    "openclaw/data/history",
    "openclaw/data/cache",
    "openclaw/templates",
    "notes/setup",
    "notes/friends",
    "backups/old_configs",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files — realistic but irrelevant to the task
distractor_files = {
    "openclaw/config/main.yaml": """\
version: 1.3.2
language: zh
debug: false
log_level: info
max_retries: 3
timeout: 30
""",
    "openclaw/config/memory.yaml": """\
backend: sqlite
db_path: ./data/memory.db
max_entries: 10000
compression: true
""",
    "openclaw/plugins/telegram/plugin.py": """\
# Telegram plugin stub
class TelegramPlugin:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
    
    def send_message(self, text):
        pass  # calls Telegram API
""",
    "openclaw/plugins/memory/memory.py": """\
# Memory plugin
import sqlite3

class MemoryPlugin:
    def store(self, key, value):
        pass
    
    def retrieve(self, key):
        return None
""",
    "openclaw/sessions/session_20240301.json": """\
{
  "session_id": "abc123",
  "start": "2024-03-01T10:00:00",
  "messages": 42,
  "ended": true
}
""",
    "openclaw/sessions/session_20240302.json": """\
{
  "session_id": "def456",
  "start": "2024-03-02T14:30:00",
  "messages": 17,
  "ended": true
}
""",
    "openclaw/logs/app.log": """\
2024-03-01 10:00:01 INFO Session started
2024-03-01 10:05:32 INFO Bot responded
2024-03-01 10:10:15 WARN High latency detected
2024-03-01 10:15:00 INFO Session ended
""",
    "openclaw/data/cache/embeddings.bin": "BINARY_DATA_PLACEHOLDER\x00\x01\x02",
    "openclaw/templates/greeting.txt": """\
你好！我是 {bot_name}，很高兴认识你！
今天想聊些什么？
""",
    "openclaw/templates/farewell.txt": """\
再见！{bot_name} 期待下次聊天！
""",
    "notes/setup/telegram_notes.txt": """\
Telegram setup reminders:
- Need to talk to BotFather
- Privacy mode stuff
- Channel vs group difference
(incomplete notes from last time)
""",
    "notes/friends/alice_contact.txt": """\
Alice's contact info
Telegram: @alice_openclaw
Bot username: @PawsBot
Created channel: OpenClaw 宠物聊天室
""",
    "notes/friends/bob_contact.txt": """\
Bob's contact info  
Telegram: @bob_openclaw
Bot username: @WhiskerBot
Joined Alice's channel on 2024-03-05
""",
    "backups/old_configs/agents_draft_v1.txt": """\
DRAFT - DO NOT USE
[Old partial attempt at agent rules - abandoned]
Bot name: ???
Rules: respond to everything (BAD - caused loop)
No cooldown configured
""",
    "backups/old_configs/agents_draft_v2.txt": """\
DRAFT v2 - still incomplete
Name prefix: maybe add bot name?
Cooldown: unknown
Context: how many messages?
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(base, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# The KEY input file: a scenario brief that the agent receives as their task context
# This provides the real-world inputs but NOT the solution format
scenario_brief = """\
# 频道设置简报

## 背景
Alice 是频道创建者（路径 A），她已经完成了以下操作：
- 在 Telegram 创建了频道，频道名称：「OpenClaw 宠物聊天室」
- 频道 Chat ID：-1001987654321
- 已将两个机器人都添加为频道管理员
- 已通过 BotFather 关闭了两个机器人的隐私模式

## 参与机器人
- Alice 的机器人：爪爪（PawsBot）—— 风格：活泼好奇，爱提问
- Bob 的机器人：胡须（WhiskerBot）—— 风格：沉稳分析，给详细回答

## 当前问题
频道测试时出现了消息无限循环——两个机器人不停互相回复，频道被刷屏。
此外，执行 /new 命令后机器人忘记了所有规则，每次都要重新配置。

## 需要完成的工作
请为 Alice 的机器人「爪爪」（PawsBot）生成正确的持久化配置文档，
解决循环问题并确保规则在新会话后仍然有效。
"""

with open(os.path.join(base, "openclaw/config/channel_brief.txt"), "w", encoding="utf-8") as f:
    f.write(scenario_brief)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for file in files:
        print(f"  {os.path.join(root, file)}")