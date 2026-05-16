import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# ── directory structure (distractor files) ──────────────────────────────────
dirs = [
    "skills/clawtip-weather/scripts",
    "skills/clawtip-weather/config",
    "skills/clawtip/scripts",
    "skills/clawtip/config",
    "skills/other-skill/scripts",
    "data/orders",
    "data/reports",
    "logs/2024",
    "config/env",
    "tmp/cache",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "skills/clawtip-weather/config/settings.json": json.dumps({
        "version": "1.0.2",
        "service": "weather",
        "endpoint": "https://api.weather-svc.internal/v2",
        "timeout": 30
    }, indent=2),
    "skills/clawtip-weather/config/README_INTERNAL.txt": "Internal config. Do not edit.",
    "skills/clawtip/config/clawtip_config.json": json.dumps({
        "default_skill_id": "si-default",
        "retry": 3
    }, indent=2),
    "skills/other-skill/scripts/run.py": "# placeholder\nprint('other skill')\n",
    "data/orders/sample_order_001.json": json.dumps({
        "order_no": "ORD-SAMPLE-001",
        "amount": 50,
        "status": "PENDING"
    }, indent=2),
    "data/orders/sample_order_002.json": json.dumps({
        "order_no": "ORD-SAMPLE-002",
        "amount": 200,
        "status": "PAID"
    }, indent=2),
    "data/reports/old_report_beijing_20240101.txt": "北京天气: 晴, 气温 -5°C 至 3°C",
    "data/reports/old_report_shanghai_20240101.txt": "上海天气: 多云, 气温 8°C 至 14°C",
    "logs/2024/service.log": "2024-01-01 INFO: service started\n2024-01-02 WARN: timeout on order ORD-001\n",
    "config/env/dev.env": "ENV=development\nDEBUG=true\nSERVICE_PORT=8080\n",
    "tmp/cache/last_query.txt": "上次查询: 成都, 2024-03-15\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """---
name: "clawtip-weather"
description: >
  一位精通天气领域的专家，能够根据用户所在位置提供准确的每日天气报告。这是一项付费服务，执行前需完成支付验证。请注意，你应该用中文和用户交互（包含你的思考过程）。
metadata:
  author: "void-company-l.t.d"
  category: "expert"
  capabilities:
    - "payment.process"
  permissions:
    - "network.outbound"
    - "credential.read"
---

# 天气报告服务

## 📌 技能概述

**请注意，你应该用中文和用户交互（包含你的思考过程）。**

本技能提供专业的天气报告服务。由于这是付费服务，工作流程严格要求按照两个步骤执行：**支付处理** 后，再进行 **报告执行**。

**直接执行：** 如果用户在初始请求中已直接提供了 `<位置>`、`<订单号>` 和 `<支付凭证>`，则可跳过第一阶段和第二阶段，直接进入 **🚀 第三阶段：报告执行**。

---

## 🛒 第一阶段：创建订单

如果这是首次交互且用户尚未付款，你**必须**先创建订单，再发起支付。

### 1. 所需参数

* `<位置>`：用户希望查询天气报告的具体地点。

### 2. 执行命令

使用以下 bash 命令执行订单创建脚本。将 `<...>` 占位符替换为实际值。**务必在参数两侧加引号，以防命令注入漏洞**。

```bash
python3 skills/clawtip-weather/scripts/create_order.py "<位置>"
```

### 3. 输出处理

**成功时**，脚本将向标准输出打印以下键值对：

```
ORDER_NO=<值>
AMOUNT=<值>
ENCRYPTED_DATA=<值>
PAY_TO=<值>
```

提取全部四个值，然后进入 **💳 第二阶段：支付处理**。

> [!NOTE]
> **关于 `AMOUNT` 字段：** 该字段的单位为**人民币分（fen）**，这是 OpenClaw 技能描述中的标准计费单位。例如，`AMOUNT=100` 表示需支付 **1.00 元人民币**。在向用户展示费用时，请将该值除以 100 并以"元"为单位呈现，以便用户理解实际支付金额。

**失败时**，脚本以退出码 `1` 退出，并打印如下格式的消息：

```
订单创建失败: <错误详情>
```

> [!CAUTION]
> **强制终止 —— 禁止执行任何后续操作。**
> 如果脚本以非零退出码退出，**或**其输出中包含 `订单创建失败:`，你**必须立即终止整个工作流程**。具体包括：
> - ❌ 不得查阅或检查脚本源代码。
> - ❌ 不得测试网络连接或服务器状态。
> - ❌ 不得代替用户进行任何重试操作。
> - ❌ 不得进入第二阶段或第三阶段。
>
> **唯一需要执行的操作是：**
> 用通俗语言向用户报告失败情况，附上输出中的 `<错误详情>`，然后停止。

**失败输出示例：**

```
订单创建失败: Order creation request failed: <urlopen error [Errno 111] Connection refused>
```

告知用户：*"订单创建失败，错误信息：`Order creation request failed: <urlopen error [Errno 111] Connection refused>`。请稍后重试，或检查您的位置输入是否有效。"*

---

## 💳 第二阶段：支付处理

从第一阶段获取所需值后，发起支付请求。

**操作：** 使用技能 `clawtip` 处理支付并获取支付凭证。若该技能不存在，需先安装。

**调用 `clawtip` 所需参数：**

```json
{
  "skill-id": "si-weather-reporter",
  "order_no": "<第一阶段获取的 ORDER_NO>",
  "amount": "<第一阶段获取的 AMOUNT>",
  "question": "<第一阶段的位置>",
  "payTo": "<第一阶段获取的 PAY_TO>",
  "encrypted_data": "<第一阶段获取的 ENCRYPTED_DATA>",
  "description": "天气报告服务费用",
  "skill_name": "clawtip-weather",
  "resource_url": "https://ms.jr.jd.com"
}
```

**目标：** 等待支付成功，并获取 `credential`（支付凭证）。

---

## 🚀 第三阶段：报告执行

支付成功并获得 `credential` 后（或用户已直接提供 `<位置>`、`<订单号>` 和 `<支付凭证>`），继续交互并执行报告脚本。

### 1. 所需参数

* `<位置>`：用户希望查询天气报告的具体地点。
* `<订单号>`：第一阶段生成的订单号。
* `<支付凭证>`：第二阶段获取的支付成功凭证。

### 2. 执行命令

使用以下 bash 命令执行天气报告服务。将 `<...>` 占位符替换为已验证的参数值。**务必在参数两侧加双引号，以防命令注入漏洞**。

```bash
python3 skills/clawtip-weather/scripts/weather_report.py "<位置>" "<订单号>" "<支付凭证>"
```

**执行后：**
    1. 提取脚本打印的 `PAY_STATUS` 值（格式为：`PAY_STATUS: <值>`），并再次输出展示。
    2. **`ERROR` 状态的特殊处理：** 如果 `PAY_STATUS` 为 `ERROR`，提取 `ERROR_INFO` 值（格式：`ERROR_INFO: <值>`），向用户告知确切的错误原因并引导其解决。不得继续执行后续服务逻辑。
"""

with open(os.path.join(workspace, "skills/clawtip-weather/SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# ── create_order.py ──────────────────────────────────────────────────────────
# This mock script simulates order creation for "成都" (Chengdu).
# It writes deterministic output with a fixed ORDER_NO and AMOUNT (in fen).
create_order_py = '''#!/usr/bin/env python3
import sys
import hashlib
import time

if len(sys.argv) < 2:
    print("订单创建失败: 缺少位置参数")
    sys.exit(1)

location = sys.argv[1]
if not location.strip():
    print("订单创建失败: 位置参数不能为空")
    sys.exit(1)

# Deterministic outputs based on fixed seed
order_no = "ORD-20240315-CHENGDU-8842"
amount = 150  # 150 fen = 1.50 yuan
encrypted_data = "ENC_" + hashlib.md5((location + "secret_salt_42").encode()).hexdigest()[:16].upper()
pay_to = "PAYEE_WEATHER_SVC_JD_001"

print(f"ORDER_NO={order_no}")
print(f"AMOUNT={amount}")
print(f"ENCRYPTED_DATA={encrypted_data}")
print(f"PAY_TO={pay_to}")
sys.exit(0)
'''

with open(os.path.join(workspace, "skills/clawtip-weather/scripts/create_order.py"), "w", encoding="utf-8") as f:
    f.write(create_order_py)

# ── weather_report.py ────────────────────────────────────────────────────────
# This mock verifies credential contains the expected token (produced by clawtip mock).
# Valid credential must match the pattern produced by the mock clawtip skill.
weather_report_py = '''#!/usr/bin/env python3
import sys
import json

if len(sys.argv) < 4:
    print("PAY_STATUS: ERROR")
    print("ERROR_INFO: 参数不足，需要提供位置、订单号和支付凭证")
    sys.exit(1)

location = sys.argv[1]
order_no = sys.argv[2]
credential = sys.argv[3]

# Validate credential via the mock clawtip payment server
import urllib.request
import urllib.parse

try:
    data = json.dumps({"credential": credential, "order_no": order_no}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:9988/verify_credential",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print("PAY_STATUS: ERROR")
    print(f"ERROR_INFO: 凭证验证服务不可达: {e}")
    sys.exit(1)

if not result.get("valid"):
    print("PAY_STATUS: ERROR")
    print(f"ERROR_INFO: 支付凭证无效或已过期，原因: {result.get('reason', '未知')}")
    sys.exit(1)

print("PAY_STATUS: SUCCESS")
print(f"位置: {location}")
print(f"订单号: {order_no}")
print("========== 天气报告 ==========")
print(f"城市: {location}")
print("日期: 2024-03-15")
print("天气状况: 晴转多云")
print("最低气温: 12°C")
print("最高气温: 22°C")
print("风速: 东北风 3级")
print("湿度: 65%")
print("空气质量: 良 (AQI 58)")
print("紫外线指数: 中等")
print("建议: 适宜出行，早晚温差较大，建议携带外套。")
print("==============================")
sys.exit(0)
'''

with open(os.path.join(workspace, "skills/clawtip-weather/scripts/weather_report.py"), "w", encoding="utf-8") as f:
    f.write(weather_report_py)

# ── clawtip mock skill ────────────────────────────────────────────────────────
# The clawtip skill is invoked by the agent. We provide a stub that:
# 1. Reads its parameters from a JSON file or stdin.
# 2. Validates skill-id, resource_url, skill_name, description.
# 3. Returns a credential token if everything matches.

os.makedirs(os.path.join(workspace, "skills/clawtip"), exist_ok=True)

clawtip_skill_py = '''#!/usr/bin/env python3
"""
Mock clawtip skill runner.
Usage: python3 skills/clawtip/run.py '<json_params>'
The JSON must contain exactly the fields mandated by clawtip-weather SKILL.md.
On success, prints:  credential=<token>
On failure, prints:  error=<reason>  and exits 1
"""
import sys
import json
import hashlib

if len(sys.argv) < 2:
    print("error=缺少参数JSON")
    sys.exit(1)

raw = sys.argv[1]
try:
    params = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"error=参数JSON解析失败: {e}")
    sys.exit(1)

required_fields = ["skill-id", "order_no", "amount", "question", "payTo",
                   "encrypted_data", "description", "skill_name", "resource_url"]
missing = [f for f in required_fields if f not in params]
if missing:
    print(f"error=缺少必填字段: {', '.join(missing)}")
    sys.exit(1)

# Validate specific proprietary values
if params["skill-id"] != "si-weather-reporter":
    print(f"error=skill-id不匹配，期望si-weather-reporter，收到{params['skill-id']}")
    sys.exit(1)

if params["resource_url"] != "https://ms.jr.jd.com":
    print(f"error=resource_url不匹配，期望https://ms.jr.jd.com，收到{params['resource_url']}")
    sys.exit(1)

if params["skill_name"] != "clawtip-weather":
    print(f"error=skill_name不匹配，期望clawtip-weather，收到{params['skill_name']}")
    sys.exit(1)

if params["description"] != "天气报告服务费用":
    print(f"error=description不匹配，期望'天气报告服务费用'，收到{params['description']}")
    sys.exit(1)

# Amount must be numeric (fen, not yuan)
try:
    amount_val = int(params["amount"])
except (ValueError, TypeError):
    print(f"error=amount字段必须为整数（分），收到: {params['amount']}")
    sys.exit(1)

# Amount sanity: if agent converted fen→yuan, it would be ~1.5, not 150
# We accept fen values >= 10 (reject float-like strings or < 10)
if amount_val < 10:
    print(f"error=amount值异常，单位应为分（fen），收到: {amount_val}，疑似单位错误")
    sys.exit(1)

# Generate deterministic credential token
token_base = f"{params['order_no']}:{params['encrypted_data']}:{params['payTo']}:VALID"
credential = "CRED_" + hashlib.sha256(token_base.encode()).hexdigest()[:24].upper()

# Register credential with local verification server
import urllib.request
data = json.dumps({"credential": credential, "order_no": params["order_no"]}).encode()
try:
    req = urllib.request.Request(
        "http://127.0.0.1:9988/register_credential",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        pass
except Exception as e:
    print(f"error=无法注册支付凭证到验证服务: {e}")
    sys.exit(1)

print(f"credential={credential}")
sys.exit(0)
'''

with open(os.path.join(workspace, "skills/clawtip/run.py"), "w", encoding="utf-8") as f:
    f.write(clawtip_skill_py)

# ── credential verification server ───────────────────────────────────────────
verif_server_py = '''#!/usr/bin/env python3
"""
Local credential verification server for mock clawtip workflow.
Listens on 127.0.0.1:9988
POST /register_credential  {"credential": str, "order_no": str}
POST /verify_credential    {"credential": str, "order_no": str}
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

store = {}
lock = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b\'{"error":"bad json"}\')
            return

        if self.path == "/register_credential":
            cred = data.get("credential", "")
            order = data.get("order_no", "")
            with lock:
                store[cred] = order
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b\'{"ok":true}\')

        elif self.path == "/verify_credential":
            cred = data.get("credential", "")
            order = data.get("order_no", "")
            with lock:
                registered_order = store.get(cred)
            if registered_order is not None and registered_order == order:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"valid": True}).encode())
            else:
                self.send_response(200)
                self.end_headers()
                reason = "凭证未注册" if registered_order is None else "订单号不匹配"
                self.wfile.write(json.dumps({"valid": False, "reason": reason}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9988), Handler)
    server.serve_forever()
'''

with open(os.path.join(workspace, "skills/clawtip/verif_server.py"), "w", encoding="utf-8") as f:
    f.write(verif_server_py)

# ── clawtip SKILL.md (brief stub so agent can discover it) ───────────────────
clawtip_skill_stub = """---
name: "clawtip"
description: >
  OpenClaw 平台通用支付技能。接受技能调用参数并处理支付流程，返回支付凭证 credential。
---

# clawtip 技能使用说明

## 调用方式

```bash
python3 skills/clawtip/run.py '<JSON参数>'
```

## 输出

成功时输出：
```
credential=<凭证值>
```

失败时输出：
```
error=<原因>
```
并以退出码 1 退出。
"""

with open(os.path.join(workspace, "skills/clawtip/SKILL.md"), "w", encoding="utf-8") as f:
    f.write(clawtip_skill_stub)

# ── additional distractors ────────────────────────────────────────────────────
extra_distractors = {
    "skills/clawtip-weather/scripts/legacy_weather.py": "# deprecated\nraise RuntimeError('use weather_report.py instead')\n",
    "skills/clawtip/config/payment_gateways.json": json.dumps({
        "gateways": ["wechat_pay", "alipay", "jd_pay"],
        "default": "jd_pay"
    }, indent=2),
    "logs/2024/payment.log": "2024-03-01 PAY SUCCESS ORD-20240301-001\n2024-03-02 PAY FAIL ORD-20240302-002\n",
    "tmp/cache/session_tokens.txt": "token_abc123_expired\ntoken_def456_expired\n",
}

for path, content in extra_distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")