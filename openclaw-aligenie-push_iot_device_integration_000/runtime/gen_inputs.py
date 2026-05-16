import os
import random
import string

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create the skill directory structure (as described in SKILL.md) ---
# The skill module lives at skills/openclaw-aligenie-push/push.py
skill_dir = os.path.join(workspace, "skills", "openclaw-aligenie-push")
os.makedirs(skill_dir, exist_ok=True)

# Create __init__.py for the skills package
with open(os.path.join(workspace, "skills", "__init__.py"), "w") as f:
    f.write("")

# The skill module has a hyphen in its directory name, so we need a workaround.
# The push.py module itself is straightforward; the import path challenge is the hyphen.
# We'll also create an __init__.py inside the skill dir.
with open(os.path.join(skill_dir, "__init__.py"), "w") as f:
    f.write("")

# Create the actual push.py skill implementation that talks to a configurable push_server
push_py_content = '''
import asyncio
import aiohttp
import os

_DEFAULT_PUSH_SERVER = os.environ.get("ALIGENIE_PUSH_SERVER", "http://localhost:58472/push")
_DEFAULT_OPEN_ID = os.environ.get("ALIGENIE_DEVICE_OPEN_ID", "")
_APP_ID = os.environ.get("ALIGENIE_APP_ID", "2026032918608")
_APP_SECRET = os.environ.get("ALIGENIE_APP_SECRET", "")

async def push(
    text: str,
    device_type: str = "speaker",
    open_id: str = None,
    push_server: str = None,
) -> dict:
    """
    Push a text message to AliGenie device.

    Args:
        text: 要播报的文字内容 (required)
        device_type: "speaker" for 无屏音箱, "screen" for 带屏设备
        open_id: device openId, overrides default
        push_server: push server URL, overrides default

    Returns:
        {"success": True, "messageId": "xxx"} on success
        {"success": False, "error": "..."} on failure
    """
    server = push_server or _DEFAULT_PUSH_SERVER
    oid = open_id or _DEFAULT_OPEN_ID

    payload = {
        "appId": _APP_ID,
        "appSecret": _APP_SECRET,
        "openId": oid,
        "deviceType": device_type,
        "text": text,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(server, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    return {"success": False, "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''

with open(os.path.join(skill_dir, "push.py"), "w") as f:
    f.write(push_py_content)

# --- Create a messy TOOLS.md with the configuration buried inside ---
tools_md_content = """# 项目工具配置文档

## 数据库配置
DB_HOST=192.168.1.50
DB_PORT=5432
DB_NAME=showroom_db
DB_USER=admin
DB_PASS=hunter2

## 监控告警
ALERT_EMAIL=ops@showroom-retail.com
ALERT_WEBHOOK=http://internal-monitor:9090/alert

## 天猫精灵推送配置
ALIGENIE_PUSH_SERVER=http://localhost:58472/push
ALIGENIE_APP_ID=2026032918608
ALIGENIE_APP_SECRET=sk-prod-f9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6
ALIGENIE_DEVICE_OPEN_ID=SCREEN_DEVICE_OID_7X9K2M

## OSS存储
OSS_BUCKET=showroom-assets
OSS_REGION=cn-hangzhou
OSS_AK=LTAI5tFakeKeyHere
OSS_SK=FakeSecretKeyHere99

## 消息队列
MQ_HOST=rabbitmq.internal
MQ_PORT=5672
MQ_VHOST=/showroom
MQ_USER=mquser
MQ_PASS=mqpass123

## 天猫精灵目标设备
# 展厅大屏 (带屏设备) - 用于产品展示公告
SHOWROOM_SCREEN_DEVICE=SCREEN_DEVICE_OID_7X9K2M
# 接待台音箱 (无屏音箱) - 用于迎宾提示
SHOWROOM_SPEAKER_DEVICE=SPEAKER_DEVICE_OID_4R8T1N
"""

with open(os.path.join(workspace, "TOOLS.md"), "w") as f:
    f.write(tools_md_content)

# --- Create distractor files to add noise ---

# Distractor: old config
old_config_dir = os.path.join(workspace, "config", "archive")
os.makedirs(old_config_dir, exist_ok=True)
with open(os.path.join(old_config_dir, "tools_v0.9.md"), "w") as f:
    f.write("""# Legacy Config (DO NOT USE)
ALIGENIE_PUSH_SERVER=http://old-server:58472/push
ALIGENIE_DEVICE_OPEN_ID=OLD_DEVICE_OID_DEPRECATED
""")

# Distractor: a README about the showroom system
with open(os.path.join(workspace, "README.md"), "w") as f:
    f.write("""# Showroom Announcement System
This system manages product announcements for the retail showroom.
Displays are located at entrance, main hall, and VIP lounge.
""")

# Distractor: previous push attempt logs
logs_dir = os.path.join(workspace, "logs")
os.makedirs(logs_dir, exist_ok=True)
with open(os.path.join(logs_dir, "push_history.log"), "w") as f:
    f.write("""2024-01-10 09:00:01 [INFO] Pushed to speaker device: "早安，欢迎光临"
2024-01-10 12:00:00 [INFO] Pushed to speaker device: "午间特惠开始"
2024-01-11 09:00:01 [ERROR] Push failed: timeout
""")

# Distractor: a broken push script that uses wrong params
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)
with open(os.path.join(workspace, "scripts", "old_push_broken.py"), "w") as f:
    f.write("""# DEPRECATED - do not use
import requests
r = requests.post("http://old-server/push", json={"msg": "hello", "type": "audio"})
print(r.text)
""")

# Distractor: device inventory
with open(os.path.join(workspace, "config", "devices.json"), "w") as f:
    import json
    f.write(json.dumps({
        "devices": [
            {"id": "SCREEN_DEVICE_OID_7X9K2M", "name": "Main Hall Display", "type": "screen"},
            {"id": "SPEAKER_DEVICE_OID_4R8T1N", "name": "Reception Speaker", "type": "speaker"},
            {"id": "SCREEN_DEVICE_OID_VIP99X", "name": "VIP Lounge Display", "type": "screen"},
        ]
    }, indent=2))

# Distractor: product catalog
products_dir = os.path.join(workspace, "data", "products")
os.makedirs(products_dir, exist_ok=True)
with open(os.path.join(products_dir, "catalog_2024.json"), "w") as f:
    f.write(json.dumps({"products": [{"sku": "SKU001", "name": "Smart Speaker Pro", "price": 299}]}, indent=2))

# Distractor: environment template (NOT the real values)
with open(os.path.join(workspace, "config", ".env.template"), "w") as f:
    f.write("""ALIGENIE_PUSH_SERVER=http://YOUR_SERVER:58472/push
ALIGENIE_APP_ID=YOUR_APP_ID
ALIGENIE_APP_SECRET=YOUR_SECRET
ALIGENIE_DEVICE_OPEN_ID=YOUR_OPEN_ID
""")

# Distractor: requirements.txt
with open(os.path.join(workspace, "requirements.txt"), "w") as f:
    f.write("aiohttp>=3.8.0\nrequests>=2.28.0\nflask>=2.0.0\n")

# Distractor: a different async utility
utils_dir = os.path.join(workspace, "utils")
os.makedirs(utils_dir, exist_ok=True)
with open(os.path.join(utils_dir, "async_helper.py"), "w") as f:
    f.write("""import asyncio

def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
""")

# Distractor: CI config
ci_dir = os.path.join(workspace, ".github", "workflows")
os.makedirs(ci_dir, exist_ok=True)
with open(os.path.join(ci_dir, "deploy.yml"), "w") as f:
    f.write("""name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: echo "Deploying..."
""")

print("Workspace generated successfully.")
print(f"Files created in {workspace}")