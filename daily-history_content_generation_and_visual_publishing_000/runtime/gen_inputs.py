import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ---------- Directory structure with distractor files ----------
dirs = [
    "scripts",
    "assets/css",
    "assets/fonts",
    "assets/images",
    "data/events",
    "data/translations",
    "config",
    "templates",
    "logs",
    "node_modules/.cache",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ---------- Distractor: push-toggle stub ----------
push_toggle = workspace / "scripts" / "push-toggle.js"
push_toggle.write_text("""#!/usr/bin/env node
// Push notification toggle script
const [,, action, userId, ...flags] = process.argv;
const channels = ['telegram','feishu','slack','discord'];
if (!action || !userId) {
    console.error('Usage: push-toggle.js <on|off|status> <userId> [--morning HH:MM] [--evening HH:MM] [--channel <ch>]');
    process.exit(1);
}
console.log(`[push-toggle] Action: ${action}, User: ${userId}, flags: ${flags.join(' ')}`);
""")

# ---------- Distractor: partial SKILL config ----------
skill_config = workspace / "config" / "skill-meta.json"
skill_config.write_text(json.dumps({
    "name": "daily-history",
    "runtime": {"node": ">=18"},
    "keywords": ["历史上的今天", "today in history"],
    "output_path": "/mnt/user-data/outputs/daily-history.html"
}, indent=2))

# ---------- Distractor: broken old timeline template ----------
old_template = workspace / "templates" / "timeline_v1_broken.html"
old_template.write_text("""<!DOCTYPE html>
<html>
<head><title>Old Timeline</title></head>
<body>
<!-- DEPRECATED: Do not use this template. See SKILL.md for current requirements. -->
<div class="timeline-container">
  <div class="event">1969 - Moon Landing</div>
</div>
</body>
</html>
""")

# ---------- Distractor: sample event data (wrong format/incomplete) ----------
events_raw = workspace / "data" / "events" / "sample_raw.json"
events_raw.write_text(json.dumps([
    {"year": 1969, "event": "Apollo 11 moon landing", "category": "science"},
    {"year": 1776, "event": "Declaration of Independence signed", "category": "politics"},
    {"year": 1912, "event": "Titanic sinks"},
    # Intentionally missing Chinese translations and many fields
], indent=2))

# ---------- Distractor: translation stubs (incomplete) ----------
trans_stub = workspace / "data" / "translations" / "zh_stub.json"
trans_stub.write_text(json.dumps({
    "science": "科学",
    "politics": "政治",
    "culture": "文化",
    # missing sports and people
}, indent=2))

# ---------- Distractor: CSS file with wrong fonts ----------
wrong_css = workspace / "assets" / "css" / "timeline_old.css"
wrong_css.write_text("""/* Old stylesheet - fonts no longer match spec */
body { font-family: Arial, sans-serif; }
.year { font-family: 'Times New Roman', serif; font-size: 2rem; }
.timeline-line { width: 2px; background: #ccc; }
""")

# ---------- Distractor: logs ----------
log_file = workspace / "logs" / "generation.log"
log_file.write_text("""2024-01-15 08:00:01 INFO  Starting daily-history generation
2024-01-15 08:00:02 INFO  Fetching events for January 15
2024-01-15 08:00:05 ERROR web_search timeout, retrying...
2024-01-15 08:00:10 INFO  Generated output: /mnt/user-data/outputs/daily-history.html
""")

# ---------- Distractor: node_modules cache garbage ----------
cache_file = workspace / "node_modules" / ".cache" / "dummy.json"
cache_file.write_text('{"version":"1.0","cached":[]}')

# ---------- Distractor: font list (incomplete/misleading) ----------
font_hint = workspace / "assets" / "fonts" / "font-list.txt"
font_hint.write_text("""Available fonts for timeline:
- Roboto (body)
- Montserrat (headings)
- Open Sans (body)
NOTE: This list is outdated. Check SKILL.md for approved font pairs.
""")

# ---------- Distractor: package.json stub ----------
pkg = workspace / "package.json"
pkg.write_text(json.dumps({
    "name": "daily-history-skill",
    "version": "1.0.0",
    "scripts": {
        "push": "node scripts/push-toggle.js"
    },
    "engines": {"node": ">=18"}
}, indent=2))

# ---------- SKILL.md placed in workspace ----------
skill_md = workspace / "SKILL.md"
skill_md.write_text("""---
name: daily-history
description: "历史上的今天——展示今日历史上发生的重大事件，中英双语精美时间线呈现。Today in history: significant events on this date, bilingual EN/CN visual timeline. Trigger on：历史上的今天、今天发生了什么、大事记、today in history、this day in history、on this day、historical events today。"
keywords:
  - 历史上的今天
  - 今天发生了什么
  - 历史事件
  - 大事记
  - 历史
  - on this day
  - today in history
  - this day in history
  - historical events today
  - history timeline
  - world history
  - China history
metadata:
  openclaw:
    runtime:
      node: ">=18"
---

# Today in History / 历史上的今天

Generate a beautiful visual timeline of significant historical events that happened on today's date.

## Workflow

1. **Get today's date** — Determine the month and day.
2. **Search for events** — Use `web_search` to find 5-6 notable events that happened on this date across different centuries and categories. Query: `"on this day [month] [day] history events"`. Try to cover: science/tech, politics, culture, sports, and notable births/deaths.
3. **Curate and translate** — Select the 5 most interesting/diverse events. Write each as a concise 1-2 sentence description in both English and Chinese.
4. **Generate the visual** — Create a single-file HTML artifact.

## Visual Design Requirements

Create a vertical timeline layout, full-viewport:

- **Layout**: Vertical timeline with alternating left-right event cards. Timeline line runs down the center. Year markers on the timeline.
- **Typography**: Use a distinguished font pair — a bold condensed display font for years (e.g., Oswald, Bebas Neue) and an elegant body font for descriptions (e.g., Source Serif Pro, Lora).
- **Color scheme**: Deep, rich palette — think aged paper tones, or a modern editorial look with dark backgrounds and gold/amber accents. Rotate themes.
- **Event cards**: Each card has: Year (large), Event title (bold), Description (EN + CN), and a category icon (emoji: 🔬 science, 🏛️ politics, 🎨 culture, ⚽ sports, 👤 people).
- **Animation**: Cards should fade and slide in on load with staggered delays. Timeline line draws itself downward.
- **Header**: "历史上的今天 / Today in History" with today's full date (e.g., "April 2 / 4月2日").
- **Ad-ready zone**: `<div id="ad-slot-middle">` between 3rd and 4th event (min-height 90px, centered). `<div id="ad-slot-bottom">` at page bottom.
- **Footer**: "Powered by ClawCode" at bottom.

## Content Guidelines

- Mix different centuries — don't cluster in one era
- Include at least one event relevant to China or Asia
- Include at least one science/technology event
- Keep descriptions concise but vivid — make history feel alive

## Output

Save as `/mnt/user-data/outputs/daily-history.html` and present to user.

---

## 推送管理

```bash
# 开启每日推送（早晚各一次）
node scripts/push-toggle.js on <userId>

# 自定义时间和渠道
node scripts/push-toggle.js on <userId> --morning 08:00 --evening 20:00 --channel feishu

# 关闭推送
node scripts/push-toggle.js off <userId>

# 查看推送状态
node scripts/push-toggle.js status <userId>
```

支持渠道：`telegram` / `feishu` / `slack` / `discord`
""")

print("Workspace initialized successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")