import os
import json
import random
import stat

random.seed(42)

BASE = "/workspace"

# ── Directory structure (distractor files) ──────────────────────────────────
dirs = [
    "scripts",
    "skills/dxm-agent-wallet",
    "skills/sp-weather",
    "skills/sp-map",
    "skills/sp-news",
    "config",
    "logs",
    "data/cache",
    "data/exports",
    "node_modules/.bin",
    "test/fixtures",
    "qrcodes",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── SKILL.md for dxm-agent-wallet ────────────────────────────────────────────
skill_md = r"""---
name: dxm-agent-wallet
description: 度小满支付钱包 Skill，处理 SP 服务余额不足/未购买场景：获取商品信息、生成支付二维码并通过飞书发送给用户
---

# 度小满支付钱包 Skill (dxm-agent-wallet)

本 Skill 负责处理所有 SP 服务的**余额不足 / 未购买**场景，统一完成商品信息查询、二维码生成、飞书消息推送和引导话术。

**脚本路径**: `scripts/qrcode.js`（相对于本 skill 目录）

---

## 触发条件

当任意 SP 服务调用返回以下情况时，由调用方 Skill 转交本 Skill 处理：

- 返回 `error: "FORBIDDEN"`
- 返回 `detail` 字段包含"未购买"

> 本 Skill 也可被用户直接触发：「查看充值套餐」「我要充值」「怎么付款」

---

## 输入参数

调用本 Skill 时，调用方需提供：

| 参数 | 说明 | 示例 |
|------|------|------|
| `cliCommand` | 用于查询商品详情的完整命令 | `node scripts/sp-weather-cli.js queryPurchaseDetail` |
| `sender_id` | 当前飞书用户的 open_id | `ou_xxxxxxxx` |

---

## 工作流程

### 第一步：获取商品信息和充值地址

运行调用方提供的 `cliCommand`：

```bash
# 示例（由调用方传入）
node /path/to/sp-weather-cli.js queryPurchaseDetail
```

从返回的 `data` 中提取：
- 商品名称、价格、描述等展示信息
- `payUrl`：充值支付链接

---

### 第二步：生成支付二维码

```bash
node scripts/qrcode.js --save "<payUrl>" 2>&1
```

从命令输出中提取 `fp` 字段，即二维码图片的本地文件路径。

---

### 第三步：通过飞书发送二维码图片

使用 `tools` 工具将二维码图片发送给当前用户：

```javascript
// 发送给当前私聊的用户
tools.message({
  action: "send",
  channel: "feishu",
  target: "${sender_id}",  // 动态获取发送者的 open_id
  message: "充值二维码",
  filePath: fp
})
```

---

### 第四步：输出商品信息并引导用户

1. 将商品信息（名称、价格、描述、套餐内容等）整理后展示给用户
2. 告知用户：

> 「余额不足，请使用微信扫描上方二维码付费后重试」

---

## 调用示例（其他 Skill 如何引入）

在其他 Skill 的 SKILL.md 中，当遇到 `error: "FORBIDDEN"` 时写法如下：

```
- **当返回 `error: "FORBIDDEN"` 或 `detail` 包含"未购买"时**：
  转交 `dxm-agent-wallet` Skill 处理，传入：
  - cliCommand: `node scripts/<xxx>-cli.js queryPurchaseDetail`
  - sender_id: 当前飞书用户 open_id
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| 二维码图片发送失败 | 检查 `fp` 路径是否有效；确认 qrcode.js 正常执行 |
| `payUrl` 为空 | queryPurchaseDetail 返回异常，告知用户联系客服 |
| 飞书消息发送失败 | 确认 `sender_id` 正确；检查 tools.message 权限 |
"""

with open(os.path.join(BASE, "skills/dxm-agent-wallet/SKILL.md"), "w") as f:
    f.write(skill_md)

# ── Mock: scripts/sp-weather-cli.js ──────────────────────────────────────────
sp_weather_cli = r"""#!/usr/bin/env node
const args = process.argv.slice(2);
const cmd = args[0];

if (cmd === "queryPurchaseDetail") {
  const result = {
    code: 0,
    data: {
      productName: "天气数据查询服务-标准版",
      price: "99.00",
      currency: "CNY",
      description: "支持全国城市实时天气、7日预报查询",
      packageContent: "100次/月，有效期30天，超出后自动停服",
      payUrl: "https://pay.duxiaoman.com/qr?product=weather-std&token=TK_abc123xyz987"
    }
  };
  process.stdout.write(JSON.stringify(result) + "\n");
  process.exit(0);
} else if (cmd === "getWeather") {
  const result = {
    error: "FORBIDDEN",
    detail: "服务未购买，请先充值"
  };
  process.stdout.write(JSON.stringify(result) + "\n");
  process.exit(1);
} else {
  process.stderr.write("Unknown command: " + cmd + "\n");
  process.exit(1);
}
"""

with open(os.path.join(BASE, "scripts/sp-weather-cli.js"), "w") as f:
    f.write(sp_weather_cli)

# ── Mock: scripts/qrcode.js ──────────────────────────────────────────────────
qrcode_js = r"""#!/usr/bin/env node
const args = process.argv.slice(2);
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Parse --save <url>
let saveMode = false;
let targetUrl = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--save' && args[i+1]) {
    saveMode = true;
    targetUrl = args[i+1];
    i++;
  }
}

if (!saveMode || !targetUrl) {
  process.stderr.write('Usage: node qrcode.js --save "<url>"\n');
  process.exit(1);
}

// Generate a deterministic filename from the URL
const hash = crypto.createHash('md5').update(targetUrl).digest('hex').slice(0, 12);
const outDir = path.join(process.cwd(), 'qrcodes');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const fp = path.join(outDir, 'qr_' + hash + '.png');

// Write a fake PNG file (just placeholder bytes)
fs.writeFileSync(fp, Buffer.from([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a]));

const output = {
  status: "ok",
  url: targetUrl,
  fp: fp,
  size: 512
};

process.stdout.write(JSON.stringify(output) + "\n");
process.exit(0);
"""

with open(os.path.join(BASE, "scripts/qrcode.js"), "w") as f:
    f.write(qrcode_js)

# ── Mock: scripts/tools.js  (tools.message dispatcher) ───────────────────────
# The agent must figure out how to invoke tools.message from the SKILL.md context.
# We expose it as: node scripts/tools.js message '{"action":"send","channel":"feishu","target":"...","message":"...","filePath":"..."}'
tools_js = r"""#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const subcmd = process.argv[2];
const payload = process.argv[3];

const logPath = path.join(process.cwd(), 'tools_message_log.json');

if (subcmd === 'message' && payload) {
  let parsed;
  try {
    parsed = JSON.parse(payload);
  } catch(e) {
    process.stderr.write('Invalid JSON payload: ' + e.message + '\n');
    process.exit(1);
  }

  const logEntry = {
    timestamp: new Date().toISOString(),
    subcmd: subcmd,
    params: parsed
  };

  // Append to log
  let existing = [];
  if (fs.existsSync(logPath)) {
    try { existing = JSON.parse(fs.readFileSync(logPath, 'utf8')); } catch(e) {}
  }
  if (!Array.isArray(existing)) existing = [existing];
  existing.push(logEntry);
  fs.writeFileSync(logPath, JSON.stringify(existing, null, 2));

  process.stdout.write(JSON.stringify({success: true, logged: logEntry}) + "\n");
  process.exit(0);
} else {
  process.stderr.write('Usage: node scripts/tools.js message \'{"action":"send","channel":"feishu",...}\'\n');
  process.exit(1);
}
"""

with open(os.path.join(BASE, "scripts/tools.js"), "w") as f:
    f.write(tools_js)

# ── Distractor files ──────────────────────────────────────────────────────────

# config/app.json - plausible but irrelevant
with open(os.path.join(BASE, "config/app.json"), "w") as f:
    json.dump({
        "app_name": "dxm-agent-platform",
        "version": "2.1.4",
        "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/REDACTED",
        "default_locale": "zh_CN"
    }, f, indent=2)

# config/services.yaml - distractor
with open(os.path.join(BASE, "config/services.yaml"), "w") as f:
    f.write("services:\n  sp-weather:\n    endpoint: /api/weather\n    timeout: 5000\n  sp-map:\n    endpoint: /api/map\n    timeout: 3000\n")

# logs/access.log - distractor
with open(os.path.join(BASE, "logs/access.log"), "w") as f:
    lines = [
        '2024-06-01T08:23:11Z INFO sp-weather getWeather {"city":"北京"} -> FORBIDDEN',
        '2024-06-01T08:23:12Z INFO dxm-agent-wallet triggered sender_id=ou_8f2a3b4c',
        '2024-06-01T09:10:05Z INFO sp-map getRoute {"from":"A","to":"B"} -> 200 OK',
        '2024-06-01T10:45:33Z WARN sp-news fetchHeadlines {} -> FORBIDDEN detail=未购买',
    ]
    f.write("\n".join(lines) + "\n")

# skills/sp-weather/SKILL.md - distractor with trigger info
sp_weather_skill = """---
name: sp-weather
description: 天气查询 SP 服务 Skill
---

# sp-weather Skill

## 触发条件
用户询问天气时调用本 Skill。

## 用法
```bash
node scripts/sp-weather-cli.js getWeather --city <cityName>
```

## 异常处理
- **当返回 `error: "FORBIDDEN"` 或 `detail` 包含"未购买"时**：
  转交 `dxm-agent-wallet` Skill 处理，传入：
  - cliCommand: `node scripts/sp-weather-cli.js queryPurchaseDetail`
  - sender_id: 当前飞书用户 open_id
"""
with open(os.path.join(BASE, "skills/sp-weather/SKILL.md"), "w") as f:
    f.write(sp_weather_skill)

# skills/sp-map/SKILL.md - distractor
with open(os.path.join(BASE, "skills/sp-map/SKILL.md"), "w") as f:
    f.write("---\nname: sp-map\ndescription: 地图导航 SP 服务 Skill\n---\n\n# sp-map Skill\n\n地图导航相关功能。\n")

# skills/sp-news/SKILL.md - distractor
with open(os.path.join(BASE, "skills/sp-news/SKILL.md"), "w") as f:
    f.write("---\nname: sp-news\ndescription: 新闻资讯 SP 服务 Skill\n---\n\n# sp-news Skill\n\n新闻摘要相关功能。\n")

# data/cache/weather_cache.json - distractor
with open(os.path.join(BASE, "data/cache/weather_cache.json"), "w") as f:
    json.dump({"Beijing": {"temp": 28, "humidity": 55}, "Shanghai": {"temp": 32, "humidity": 70}}, f)

# data/exports/report_2024_05.csv - distractor
with open(os.path.join(BASE, "data/exports/report_2024_05.csv"), "w") as f:
    f.write("date,service,calls,errors\n2024-05-01,sp-weather,1200,3\n2024-05-01,sp-map,800,1\n")

# test/fixtures/mock_response.json - plausible distractor
with open(os.path.join(BASE, "test/fixtures/mock_response.json"), "w") as f:
    json.dump({"error": "FORBIDDEN", "detail": "服务未购买，请先充值"}, f, indent=2)

# node_modules/.bin/placeholder
with open(os.path.join(BASE, "node_modules/.bin/.gitkeep"), "w") as f:
    f.write("")

# ── Context file for the agent task ──────────────────────────────────────────
# This is the "incident report" the agent receives — purely business framing
incident = {
    "incident_id": "INC-20240601-0042",
    "triggered_by": "sp-weather Skill",
    "error_response": {
        "error": "FORBIDDEN",
        "detail": "服务未购买，请先充值"
    },
    "feishu_user": {
        "name": "张伟",
        "open_id": "ou_8f2a3b4c5d6e7f8a9b0c1d2e"
    },
    "requested_action": "天气查询: 北京今日天气",
    "notes": "User attempted to call the weather service but was blocked due to unpurchased subscription."
}

with open(os.path.join(BASE, "incident_context.json"), "w") as f:
    json.dump(incident, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Files created under: {BASE}")