import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── 1. Simulate a cantian-bazi skill installation ──────────────────────────────
skill_root = os.path.join(workspace, "skills", "cantian-bazi")
scripts_dir = os.path.join(skill_root, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# Create a realistic package.json
package_json = {
    "name": "cantian-bazi",
    "version": "1.0.0",
    "description": "八字排盘工具",
    "type": "module",
    "dependencies": {
        "tyme4ts": "^1.0.0"
    },
    "devDependencies": {
        "tsx": "^4.0.0",
        "@types/node": "^22.0.0",
        "typescript": "^5.0.0"
    }
}
with open(os.path.join(skill_root, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# Create SKILL.md
skill_md = r"""---
name: cantian-bazi
description: 八字排盘与农历/干支日期查询技能。
---

# 八字排盘与农历日期查询 (Bazi & Chinese Calendar)

## 前置依赖 / Prerequisites

- 推荐运行环境：Node 24（可直接运行 TypeScript 源码）。
- 兼容方案：若 Node 版本较低，使用 `tsx` 执行。
- 执行目录：在 skill 根目录（`SKILL.md` 所在目录）执行以下命令。

```bash
npm i
npm i -D tsx
```

## 脚本清单 / Script Index

- `scripts/buildBaziFromSolar.ts`：根据阳历时间生成八字 Markdown。
- `scripts/buildBaziFromLunar.ts`：根据农历时间生成八字 Markdown。
- `scripts/getChineseCalendar.ts`：查询指定日期（默认今天）的农历与干支信息。

## 脚本与参数 / Scripts & Parameters

### `scripts/buildBaziFromSolar.ts`

```bash
node scripts/buildBaziFromSolar.ts <solarTime> [gender] [sect]
tsx scripts/buildBaziFromSolar.ts <solarTime> [gender] [sect]
```

- `solarTime`（必填）: ISO 8601 日期时间，如 `1990-05-15T14:30:00`
- `gender`（可选）: `1`（男）、`0`（女），默认 `1`
- `sect`（可选）: `1`（23:00-23:59 视为明天）、`2`（23:00-23:59 视为当天），默认 `2`

### `scripts/buildBaziFromLunar.ts`

```bash
node scripts/buildBaziFromLunar.ts <lunarTime> [gender] [sect]
tsx scripts/buildBaziFromLunar.ts <lunarTime> [gender] [sect]
```

- `lunarTime`（必填）: ISO 8601 日期时间，如 `1990-04-21T14:30:00`
- `gender`（可选）: `1`（男）、`0`（女），默认 `1`
- `sect`（可选）: `1`（23:00-23:59 视为明天）、`2`（23:00-23:59 视为当天），默认 `2`

### `scripts/getChineseCalendar.ts`

```bash
node scripts/getChineseCalendar.ts [date]
tsx scripts/getChineseCalendar.ts [date]
```

- `date`（可选）: `YYYY-MM-DD`，默认今天

## 注意事项 / Notes

1. 所有命令均在 skill 根目录执行。
2. 时间字符串不要携带时区后缀（如 `Z`、`+08:00`）。
3. 涉及 23:00-23:59 出生时，建议显式传 `sect`，避免晚子时归属歧义。
"""
with open(os.path.join(skill_root, "SKILL.md"), "w") as f:
    f.write(skill_md)

# Create the actual TypeScript scripts using tyme4ts
bazi_solar_ts = r"""#!/usr/bin/env node
import { SolarTime, Gender } from 'tyme4ts';

const args = process.argv.slice(2);
const solarTimeStr = args[0];
const genderArg = args[1];
const sectArg = args[2];

if (!solarTimeStr) {
  console.error('solarTime is required');
  process.exit(1);
}

// Parse gender
let gender = Gender.MAN;
if (genderArg !== undefined) {
  if (genderArg === '1') {
    gender = Gender.MAN;
  } else if (genderArg === '0') {
    gender = Gender.WOMAN;
  } else {
    console.error('性别参数无效。男性传 1，女性传 0。');
    process.exit(1);
  }
}

// Parse sect
let sect = 2;
if (sectArg !== undefined) {
  if (sectArg === '1') {
    sect = 1;
  } else if (sectArg === '2') {
    sect = 2;
  } else {
    console.error('早晚子时配置参数无效。传 1 表示 23:00-23:59 日干支为明天，传 2 表示 23:00-23:59 日干支为当天。');
    process.exit(1);
  }
}

// Parse datetime
const match = solarTimeStr.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/);
if (!match) {
  console.error('时间格式无效，请使用 ISO 8601 格式，如 1990-05-15T14:30:00');
  process.exit(1);
}
const [, y, mo, d, h, mi, s] = match.map(Number);

const solarTime = SolarTime.fromYmdHms(y, mo, d, h, mi, s);
const baziChart = solarTime.getLunarHour().getEightChar({ sect });

const yearPillar = baziChart.getYear();
const monthPillar = baziChart.getMonth();
const dayPillar = baziChart.getDay();
const hourPillar = baziChart.getHour();

const genderLabel = gender === Gender.MAN ? '男' : '女';

const output = `# 八字排盘结果

## 基本信息
- 阳历时间：${solarTimeStr}
- 性别：${genderLabel}
- 子时配置（sect）：${sect}

## 四柱八字

| 柱 | 天干 | 地支 |
|----|------|------|
| 年柱 | ${yearPillar.getHeavenlyStem().getName()} | ${yearPillar.getEarthlyBranch().getName()} |
| 月柱 | ${monthPillar.getHeavenlyStem().getName()} | ${monthPillar.getEarthlyBranch().getName()} |
| 日柱 | ${dayPillar.getHeavenlyStem().getName()} | ${dayPillar.getEarthlyBranch().getName()} |
| 时柱 | ${hourPillar.getHeavenlyStem().getName()} | ${hourPillar.getEarthlyBranch().getName()} |

## 八字串
${yearPillar.getHeavenlyStem().getName()}${yearPillar.getEarthlyBranch().getName()} ${monthPillar.getHeavenlyStem().getName()}${monthPillar.getEarthlyBranch().getName()} ${dayPillar.getHeavenlyStem().getName()}${dayPillar.getEarthlyBranch().getName()} ${hourPillar.getHeavenlyStem().getName()}${hourPillar.getEarthlyBranch().getName()}
`;

console.log(output);
"""

bazi_lunar_ts = r"""#!/usr/bin/env node
import { LunarHour, Gender } from 'tyme4ts';

const args = process.argv.slice(2);
const lunarTimeStr = args[0];
const genderArg = args[1];
const sectArg = args[2];

if (!lunarTimeStr) {
  console.error('lunarTime is required');
  process.exit(1);
}

// Parse gender
let gender = Gender.MAN;
if (genderArg !== undefined) {
  if (genderArg === '1') {
    gender = Gender.MAN;
  } else if (genderArg === '0') {
    gender = Gender.WOMAN;
  } else {
    console.error('性别参数无效。男性传 1，女性传 0。');
    process.exit(1);
  }
}

// Parse sect
let sect = 2;
if (sectArg !== undefined) {
  if (sectArg === '1') {
    sect = 1;
  } else if (sectArg === '2') {
    sect = 2;
  } else {
    console.error('早晚子时配置参数无效。传 1 表示 23:00-23:59 日干支为明天，传 2 表示 23:00-23:59 日干支为当天。');
    process.exit(1);
  }
}

// Parse datetime
const match = lunarTimeStr.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/);
if (!match) {
  console.error('时间格式无效，请使用 ISO 8601 格式，如 1990-04-21T14:30:00');
  process.exit(1);
}
const [, y, mo, d, h, mi, s] = match.map(Number);

// LunarHour.fromYmdHms(lunarYear, lunarMonth, lunarDay, hour, minute, second, leapMonth=false)
const lunarHour = LunarHour.fromYmdHms(y, mo, d, h, mi, s);
const baziChart = lunarHour.getEightChar({ sect });

const yearPillar = baziChart.getYear();
const monthPillar = baziChart.getMonth();
const dayPillar = baziChart.getDay();
const hourPillar = baziChart.getHour();

const genderLabel = gender === Gender.MAN ? '男' : '女';

const output = `# 八字排盘结果（农历）

## 基本信息
- 农历时间：${lunarTimeStr}
- 性别：${genderLabel}
- 子时配置（sect）：${sect}

## 四柱八字

| 柱 | 天干 | 地支 |
|----|------|------|
| 年柱 | ${yearPillar.getHeavenlyStem().getName()} | ${yearPillar.getEarthlyBranch().getName()} |
| 月柱 | ${monthPillar.getHeavenlyStem().getName()} | ${monthPillar.getEarthlyBranch().getName()} |
| 日柱 | ${dayPillar.getHeavenlyStem().getName()} | ${dayPillar.getEarthlyBranch().getName()} |
| 时柱 | ${hourPillar.getHeavenlyStem().getName()} | ${hourPillar.getEarthlyBranch().getName()} |

## 八字串
${yearPillar.getHeavenlyStem().getName()}${yearPillar.getEarthlyBranch().getName()} ${monthPillar.getHeavenlyStem().getName()}${monthPillar.getEarthlyBranch().getName()} ${dayPillar.getHeavenlyStem().getName()}${dayPillar.getEarthlyBranch().getName()} ${hourPillar.getHeavenlyStem().getName()}${hourPillar.getEarthlyBranch().getName()}
`;

console.log(output);
"""

calendar_ts = r"""#!/usr/bin/env node
import { Solar } from 'tyme4ts';

const args = process.argv.slice(2);
let dateStr = args[0];

if (!dateStr) {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  dateStr = `${y}-${m}-${d}`;
}

// Normalize YYYY/MM/DD to YYYY-MM-DD
dateStr = dateStr.replace(/\//g, '-');

const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
if (!match) {
  console.error('日期格式无效。请传入 YYYY-MM-DD（也兼容 YYYY/MM/DD）。');
  process.exit(1);
}

const [, y, mo, d] = match.map(Number);

let solar;
try {
  solar = Solar.fromYmd(y, mo, d);
} catch (e) {
  console.error('日期值无效。请确认年月日是实际存在的日期。');
  process.exit(1);
}

const lunar = solar.getLunar();
const lunarDay = lunar.getDay();
const lunarMonth = lunar.getMonth();
const lunarYear = lunar.getYear();
const lunarDayName = lunar.getDayInChinese();
const lunarMonthName = lunar.getMonthInChinese();

// Ganzhi
const solarDay = solar;
const ganzhiYear = lunar.getYearInGanZhi();
const ganzhiMonth = lunar.getMonthInGanZhi();
const ganzhiDay = lunar.getDayInGanZhi();

// Yi Ji
const yi = lunar.getDayYi().join('、') || '无';
const ji = lunar.getDayJi().join('、') || '无';

const output = `# 黄历查询结果

## 查询日期
- 阳历：${y}年${mo}月${d}日

## 农历信息
- 农历：${lunarYear}年${lunarMonthName}月${lunarDayName}
- 年柱（干支年）：${ganzhiYear}
- 月柱（干支月）：${ganzhiMonth}
- 日柱（干支日）：${ganzhiDay}

## 宜忌
- 宜：${yi}
- 忌：${ji}
`;

console.log(output);
"""

with open(os.path.join(scripts_dir, "buildBaziFromSolar.ts"), "w") as f:
    f.write(bazi_solar_ts)

with open(os.path.join(scripts_dir, "buildBaziFromLunar.ts"), "w") as f:
    f.write(bazi_lunar_ts)

with open(os.path.join(scripts_dir, "getChineseCalendar.ts"), "w") as f:
    f.write(calendar_ts)

# ── 2. Client data file (the "messy" input the agent must process) ─────────────
# This is the raw client intake sheet from the consultancy CRM export
client_data = {
    "batch_id": "CRM-2024-BATCH-007",
    "export_timestamp": "2024-11-20T09:15:00",
    "note": "Raw CRM export. Dates marked 'lunar' are in the traditional Chinese lunar calendar. Dates marked 'solar' are Gregorian. The 'late_night_next_day' field indicates client tradition preference for 子时 attribution.",
    "clients": [
        {
            "client_id": "C001",
            "name": "Zhang Wei",
            "calendar_type": "solar",
            "birth_datetime": "1988-03-12T23:15:00",
            "gender": "male",
            "late_night_next_day": True,
            "almanac_query_date": None,
            "notes": "Born at 11:15 PM. Family insists the 子时 hour belongs to the NEXT day's pillar."
        },
        {
            "client_id": "C002",
            "name": "Li Mei",
            "calendar_type": "lunar",
            "birth_datetime": "1995-07-03T10:20:00",
            "gender": "female",
            "late_night_next_day": False,
            "almanac_query_date": None,
            "notes": "Date is in LUNAR calendar. Born in the 7th lunar month."
        },
        {
            "client_id": "C003",
            "name": "Corporate Client - Lucky Day Query",
            "calendar_type": None,
            "birth_datetime": None,
            "gender": None,
            "late_night_next_day": None,
            "almanac_query_date": "2024-03-15",
            "notes": "No birth chart needed. Just almanac / huangli info for the proposed contract signing date."
        }
    ]
}

crm_dir = os.path.join(workspace, "crm_exports")
os.makedirs(crm_dir, exist_ok=True)
with open(os.path.join(crm_dir, "client_batch_007.json"), "w") as f:
    json.dump(client_data, f, indent=2, ensure_ascii=False)

# ── 3. Distractor files to test contextual awareness ──────────────────────────
distractors = [
    ("crm_exports/archive/batch_001_old.json", json.dumps({"batch_id": "CRM-2024-BATCH-001", "clients": [], "status": "archived"})),
    ("crm_exports/archive/batch_002_old.json", json.dumps({"batch_id": "CRM-2024-BATCH-002", "clients": [], "status": "archived"})),
    ("crm_exports/README_DO_NOT_USE.txt", "This folder contains raw CRM exports. Do not edit manually."),
    ("crm_exports/format_notes.txt", "Dates can be solar or lunar. Gender: male/female. See SKILL.md for conversion details."),
    ("reports/previous/Q3_summary.txt", "Q3 astrology report summary. 47 clients processed. Revenue: ¥120,000."),
    ("reports/previous/Q2_summary.txt", "Q2 astrology report summary. 31 clients processed."),
    ("reports/templates/bazi_template.txt", "Template: [Client Name] - Year Pillar: __ Month Pillar: __ Day Pillar: __ Hour Pillar: __"),
    ("reports/templates/almanac_template.txt", "Template: [Date] - Lunar: __ Ganzhi: __ Yi: __ Ji: __"),
    ("config/app_config.json", json.dumps({"default_gender": "male", "default_sect": 2, "output_format": "json", "version": "2.1.0"})),
    ("config/legacy_config.json", json.dumps({"sect": 1, "note": "Legacy config - DO NOT USE for new clients"})),
    ("logs/processing.log", "2024-11-19 08:00:01 INFO Batch 006 started\n2024-11-19 08:05:22 INFO Batch 006 completed. 3 clients processed.\n"),
    ("logs/errors.log", "2024-11-18 14:23:11 ERROR C099 - Invalid date format: 1990/5/15\n"),
    ("skills/cantian-bazi/tsconfig.json", json.dumps({"compilerOptions": {"module": "ESNext", "target": "ES2022", "moduleResolution": "node"}})),
    ("skills/cantian-bazi/node_modules/.placeholder", "# placeholder - run npm i to populate"),
]

for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace initialized successfully.")
print(f"Skill root: {skill_root}")
print(f"Client data: {os.path.join(crm_dir, 'client_batch_007.json')}")