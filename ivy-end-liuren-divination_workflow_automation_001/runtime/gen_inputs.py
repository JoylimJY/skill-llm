import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── liuren.js (the actual skill script, verbatim from SKILL.md) ──────────────
liuren_js = r"""#!/usr/bin/env node

/**
 * Xiao Liu Ren Divination (Time-based)
 * Supports custom time input for prediction.
 */

const LIUREN = [
  { name: "大安 (Da An)", element: "木", meaning: "身不动时，五行属木，颜色青龙，方位正东。寓意：事事昌隆，身心安泰，失物在东，久病向安。" },
  { name: "留连 (Liu Lian)", element: "土", meaning: "卒未归时，五行属土，颜色玄武，方位北方。寓意：事不易成，凡事拖延，纠缠不清，防小人。" },
  { name: "速喜 (Su Xi)", element: "火", meaning: "人便至时，五行属火，颜色朱雀，方位南方。寓意：喜事在即，即刻见效，音信将至，大吉大利。" },
  { name: "赤口 (Chi Kou)", element: "金", meaning: "官事凶时，五行属金，颜色白虎，方位西方。寓意：口舌是非，惊恐怪异，出行不吉，防官非。" },
  { name: "小吉 (Xiao Ji)", element: "水", meaning: "人来喜时，五行属水，颜色六合，方位北方。寓意：吉人天相，诸事遂心，桃花运佳，合作顺利。" },
  { name: "空亡 (Kong Wang)", element: "土", meaning: "音信稀时，五行属土，颜色勾陈，方位中央。寓意：诸事不顺，音信全无，谋事落空，宜守不宜进。" }
];

const EARTHLY_BRANCHES = [
  "子 (23-01)", "丑 (01-03)", "寅 (03-05)", "卯 (05-07)", "辰 (07-09)", "巳 (09-11)",
  "午 (11-13)", "未 (13-15)", "申 (15-17)", "酉 (17-19)", "戌 (19-21)", "亥 (21-23)"
];

function getLunarDate(date) {
  try {
    const formatter = new Intl.DateTimeFormat('zh-CN-u-ca-chinese', {
        month: 'numeric',
        day: 'numeric'
    });
    const parts = formatter.formatToParts(date);
    const month = parseInt(parts.find(p => p.type === 'month').value);
    const day = parseInt(parts.find(p => p.type === 'day').value);
    return { month, day };
  } catch (e) {
    return { 
      month: date.getMonth() + 1, 
      day: date.getDate() 
    };
  }
}

function getEarthlyBranchIndex(hours) {
  if (hours >= 23 || hours < 1) return 1; // Zi
  if (hours < 3) return 2; // Chou
  if (hours < 5) return 3; // Yin
  if (hours < 7) return 4; // Mao
  if (hours < 9) return 5; // Chen
  if (hours < 11) return 6; // Si
  if (hours < 13) return 7; // Wu
  if (hours < 15) return 8; // Wei
  if (hours < 17) return 9; // Shen
  if (hours < 19) return 10; // You
  if (hours < 21) return 11; // Xu
  return 12; // Hai
}

function main() {
  const args = process.argv.slice(2);
  let now;
  
  if (args.length > 0) {
    now = new Date(args.join(' '));
    if (isNaN(now.getTime())) {
      console.error("Invalid date format. Using current time.");
      now = new Date();
    }
  } else {
    now = new Date();
  }
  
  const { month, day } = getLunarDate(now);
  const hourIndex = getEarthlyBranchIndex(now.getHours()); 
  
  let p1 = (month - 1) % 6;
  let p2 = (p1 + day - 1) % 6;
  let p3 = (p2 + hourIndex - 1) % 6;
  
  const result1 = LIUREN[p1];
  const result2 = LIUREN[p2];
  const result3 = LIUREN[p3];
  
  const output = {
    target_time: {
      solar: now.toLocaleString(),
      lunar_approx: `${month}月${day}日`,
      earthly_branch: EARTHLY_BRANCHES[hourIndex - 1]
    },
    sequence: {
      month_palace: { name: result1.name, element: result1.element },
      day_palace:   { name: result2.name, element: result2.element },
      hour_palace:  { name: result3.name, element: result3.element, meaning: result3.meaning }
    }
  };

  console.log(JSON.stringify(output, null, 2));
}

main();
"""

with open(os.path.join(workspace, "liuren.js"), "w", encoding="utf-8") as f:
    f.write(liuren_js)

# ── Consultation schedule (the real task input) ───────────────────────────────
# These are the 5 slots the agent must run divinations for and report.
consultation_slots = [
    {"slot_id": "S001", "client": "Zhang Wei",   "datetime": "2025-03-15 09:30"},
    {"slot_id": "S002", "client": "Li Fang",     "datetime": "2025-06-21 14:00"},
    {"slot_id": "S003", "client": "Wang Hao",    "datetime": "2025-09-09 23:15"},
    {"slot_id": "S004", "client": "Chen Mei",    "datetime": "2025-11-01 06:45"},
    {"slot_id": "S005", "client": "Zhao Qiang",  "datetime": "2025-12-22 18:55"},
]

with open(os.path.join(workspace, "consultation_schedule.json"), "w", encoding="utf-8") as f:
    json.dump(consultation_slots, f, ensure_ascii=False, indent=2)

# ── Distractor directory structure ────────────────────────────────────────────
dirs = [
    "app/config",
    "app/models",
    "app/routes",
    "app/utils",
    "data/raw",
    "data/processed",
    "docs/api",
    "docs/internal",
    "tests/unit",
    "tests/integration",
    "scripts/deploy",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "app/config/settings.yaml": "env: production\ndebug: false\nport: 3000\n",
    "app/config/db.json": json.dumps({"host": "localhost", "port": 5432, "name": "wellness_db"}, indent=2),
    "app/models/user.js": "class User { constructor(id, name) { this.id = id; this.name = name; } }\nmodule.exports = User;\n",
    "app/models/session.js": "class Session { constructor(uid, ts) { this.uid = uid; this.ts = ts; } }\nmodule.exports = Session;\n",
    "app/routes/health.js": "const express = require('express');\nconst router = express.Router();\nrouter.get('/health', (req, res) => res.json({status:'ok'}));\nmodule.exports = router;\n",
    "app/utils/logger.js": "const log = (msg) => console.log(`[LOG] ${msg}`);\nmodule.exports = { log };\n",
    "data/raw/clients_2024.csv": "id,name,dob\n1,Zhang Wei,1990-03-15\n2,Li Fang,1985-06-21\n3,Wang Hao,1992-09-09\n",
    "data/processed/summary_2024.json": json.dumps({"total_clients": 3, "year": 2024}, indent=2),
    "docs/api/endpoints.md": "# API Endpoints\n\n## GET /health\nReturns server status.\n\n## POST /session\nCreates a new session.\n",
    "docs/internal/architecture.md": "# Architecture\n\nThe app uses a three-tier model: frontend, backend, database.\n",
    "tests/unit/user.test.js": "const User = require('../../app/models/user');\ntest('User instantiation', () => { const u = new User(1,'A'); expect(u.name).toBe('A'); });\n",
    "tests/integration/session.test.js": "// Integration test placeholder\nconsole.log('session integration test');\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying to production...'\nnpm install --production\nnode app/index.js\n",
    "data/raw/old_divination_log.txt": (
        "2024-01-10 10:00 | Client: Old User | Result: ??? (legacy system, data lost)\n"
        "2024-02-14 15:30 | Client: Another User | Result: ??? (legacy system, data lost)\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created: liuren.js, consultation_schedule.json + {len(distractor_files)} distractor files")