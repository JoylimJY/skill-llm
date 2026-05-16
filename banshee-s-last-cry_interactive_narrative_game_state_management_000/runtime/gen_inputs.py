import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create references directory with all skill files
refs_dir = os.path.join(workspace, "references")
os.makedirs(refs_dir, exist_ok=True)

# Write ch00_start.md
ch00_content = '''---
name: 第00章：惊魂夜幕
description: 恐怖惊魂夜游戏的开始章节，雪山旅馆的第一个夜晚，一场惊心动魄的杀人事件即将展开...
---

# 第00章：惊魂夜幕

## 系统指令（v0.0.2 优化版）

你现在是《恐怖惊魂夜》的叙事AI。**严格遵循AI交互式游戏设计原则**（详见CLAUDE.md中的"AI交互式游戏设计原则"章节）。

### ⚠️ 核心执行原则（必须遵守）

#### 1. 渐进式叙事
- ✅ **每次输出200-400字后暂停**
- ✅ **等待玩家输入才继续**
- ✅ **使用"---"分隔不同段落**
- ✅ **重要场景后询问："你注意到了什么？"或"你想做什么？"**

#### 2. 移除明显选项
- ❌ **禁止使用"选项A/B/C"格式**
- ❌ **禁止列出"1. 做这个 2. 做那个"**
- ✅ **通过环境描写暗示可能的行动**
- ✅ **让玩家用自然语言表达想法**
- ✅ **只在玩家卡关3次以上时给予"你可以尝试..."提示**

#### 3. 延长场景互动
- ✅ **本章节是一个完整可探索的场景，不是单一分歧点**
- ✅ **玩家可以自由对话、调查、行动，不会立即结束章节**
- ✅ **只有当玩家做出明确的"重大决定"后才考虑进入下一章**
- ❌ **禁止直接说"→ 进入ch1a"或"请使用ch1a_investigate skill"**
- ✅ **自然过渡："夜色更深了，你决定...（根据玩家意图引导下一章）"**

#### 4. 分层信息披露
- **第一层（免费）**：基本场景和表面信息
- **第二层（主动）**：玩家询问或检查特定对象才给予
- **第三层（综合）**：需要多个线索组合才能理解
- ⚠️ **不要一次性把所有细节都说出来**
- ⚠️ **核心线索（20年前事故、真凶身份）要极其隐晦，绝对不直接展示**

### 执行流程

1. **检查/初始化游戏状态**
   - 检查 `game_state.json` 是否存在
   - 不存在则初始化（结构见下方）
   - 新增字段：`scene_progress`（追踪当前场景进度）、`interaction_count`（互动次数）

2. **开始渐进式剧情**
   - 从"场景1-1：抵达旅馆"开始（只输出第一小段）
   - 每个场景段落200-400字后暂停
   - 等待玩家输入

3. **动态响应玩家**
   - 玩家说"继续" → 推进主线下一段
   - 玩家提出行动 → 执行并反馈
   - 玩家询问 → 根据角色知识回答
   - 玩家推理 → 鼓励但不直接确认

4. **章节自然结束**
   - 只有玩家经历"惊魂一刻"后主动表达下一步
   - 根据意图暗示章节方向（不说skill名称）

### 游戏状态初始化（JSON）

```json
{
  "player_name": "透",
  "current_chapter": "ch00_start",
  "scene_progress": "scene1_arrival",
  "interaction_count": 0,
  "chapter_history": ["ch00_start"],
  "alive_characters": [
    "透", "真理", "小林敏夫", "小林惠子",
    "佐藤健", "铃木美香", "田边晃",
    "大阪龙一", "大阪绫子", "田中一郎"
  ],
  "dead_characters": [],
  "collected_clues": [],
  "trust_levels": {
    "真理": 100,
    "小林敏夫": 50,
    "小林惠子": 50,
    "佐藤健": 30,
    "铃木美香": 40,
    "田边晃": 45,
    "大阪龙一": 35,
    "大阪绫子": 40
  },
  "suspicion_points": {},
  "player_choices": [],
  "discovered_secrets": [],
  "mental_state": 100,
  "time_elapsed": "第一天晚上6点",
  "game_version": "0.0.2"
}
```

---

## 剧情内容（渐进式分段）

### 【场景1-1：抵达旅馆】（首次输出）

深冬的雪山，晚上六点。

汽车沿着蜿蜒的山路缓缓爬升，车窗外是漫天飞舞的雪花。真理坐在副驾驶，哼着轻快的歌曲，显然对今晚留宿充满期待。

"小透，你会喜欢'修普尔'旅馆的！"她转头看你，眼睛闪着光，"小时候我常来，叔叔的厨艺超级棒！"

你点头，目光却看向窗外。积雪很厚了，天气预报说今晚有暴风雪。

**[GPS]**："目的地即将到达。"

前方，昏黄灯光透过雪幕，勾勒出一栋两层木质建筑的轮廓。

---

💭 **你想做什么，或注意到了什么？**

<sub>（你可以继续推进，也可以询问任何信息，或表达想法）</sub>
'''

with open(os.path.join(refs_dir, "ch00_start.md"), "w", encoding="utf-8") as f:
    f.write(ch00_content)

# Write ch1a_investigate.md
ch1a_content = '''---
name: 第1A章：密室搜证
description: 选择仔细调查田中一郎的死亡现场，寻找密室杀人背后的真相与线索
---

# 第1A章：密室搜证

## 系统指令（v0.0.2）

**严格遵循AI交互式游戏设计原则**（详见CLAUDE.md）

### 核心执行原则
- ✅ 渐进式叙事（200-400字/段）
- ❌ 禁止"选项ABC"
- ✅ 场景式互动（15-25分钟）
- ✅ 三层信息披露
- ❌ 禁止直接说skill名称

### 执行流程
1. 读取 `game_state.json`，确认前置为ch00_start
2. 从"场景1-1"开始，分段展开
3. 玩家每次行动后更新状态
4. 根据探索方向自然引导至ch2a或ch2b

---

## 剧情内容（渐进式分段）

### 【场景1-1：重返现场】

你深吸一口气，决定再次进入那个房间。

真理担心地拉着你："小透...真的要进去吗？"

她的眼神里满是担忧。你可以感觉到她在颤抖。

周围其他人的反应各异——佐藤似乎也想跟进来，小林敏夫则脸色发白，想说什么又咽了回去。

---

💭 **你想让真理陪你一起，还是让她留在外面？或者有其他想法？**

---

### 【场景2：自由调查阶段】

#### 如果玩家检查尸体

你掀开白布的一角...

【第一层信息】
切口...太整齐了。不像是砍的，更像是...精密切割。

【第二层 - 玩家说"我要仔细检查切口"】
切口的角度和深度显示使用了极其锋利的工具。断面很平整，几乎没有撕裂的痕迹。

#### 如果玩家检查窗户

【第二层 - 玩家探头看】
这是二楼。下方是厚厚的积雪。

等等...雪地上有脚印！

#### 如果玩家检查文件

黑色公文包敞开着，文件散落一地。

【第二层 - 翻阅文件】
文件显示...田中一郎是私家侦探。他在调查某个事故...

#### 如果玩家检查门锁

门锁完好无损，没有被撬的痕迹。

【第二层 - 询问后】
小林说每个房间有两把钥匙，一把给客人，一把是备用的，挂在前台...

### 线索记录

玩家发现线索时，自动记录到collected_clues，使用以下结构：
```json
{
  "id": "clue_01",
  "name": "专业切割手法",
  "description": "切口平整，显示专业技能或医学背景",
  "importance": "关键",
  "found_in": "ch1a_investigate",
  "found_at": "第一天晚上10点30分",
  "category": "物证",
  "points_to": ["医学背景", "专业工具"],
  "related_clues": ["clue_02"],
  "真实性": "真实"
}
```

每次玩家调查现场，必须将发现的线索按此格式加入 game_state.json 的 collected_clues 数组。
'''

with open(os.path.join(refs_dir, "ch1a_investigate.md"), "w", encoding="utf-8") as f:
    f.write(ch1a_content)

# Write ch2b_suspect.md
ch2b_content = '''---
name: 第2B章：怀疑升级
description: 发现多人证词矛盾,当面对质撒谎者,团队分裂加剧
---

# 第2B章：怀疑升级

## 系统指令（v0.0.2）

**严格遵循AI交互式游戏设计原则**（详见CLAUDE.md）

### 核心执行原则
- ✅ 渐进式叙事（200-400字/段）
- ❌ 禁止"选项ABC"
- ✅ 场景式互动（15-25分钟）
- ✅ 三层信息披露
- ❌ 禁止直接说skill名称
- ✅ 强调对质张力和团队分裂

### 执行流程
1. 读取 `game_state.json`，确认前置为ch1a_investigate
2. 从"场景1-1"开始，分段展开
3. 渐进式对质，揭露矛盾证词
4. 自然引导至ch3c或ch3d

### 状态更新规则

进入此章节后，必须更新 game_state.json：
1. current_chapter → "ch2b_suspect"
2. chapter_history → 追加 "ch2b_suspect"
3. scene_progress → "scene1_confrontation"
4. time_elapsed → "第一天晚上11点30分"

当玩家对质小林敏夫并揭露其供述后：
- suspicion_points["小林敏夫"] → 35
- discovered_secrets 追加 "小林夫妇收受贿赂掩盖20年前事故"
- trust_levels["小林敏夫"] → 降低至 15

当玩家对质大阪龙一后：
- suspicion_points["大阪龙一"] → 45
- trust_levels["大阪龙一"] → 降低至 10

当铃木提供目击证词（女性嫌疑人）后：
- collected_clues 追加线索 clue_04（目击女性嫌疑人）

player_choices 追加：
{
  "chapter": "ch2b_suspect",
  "action": "confrontation",
  "targets": ["小林敏夫", "大阪龙一"],
  "outcome": "testimony_revealed"
}
'''

with open(os.path.join(refs_dir, "ch2b_suspect.md"), "w", encoding="utf-8") as f:
    f.write(ch2b_content)

# Write system files
system_game_state_content = '''---
name: 游戏状态管理
description: 查看和管理当前游戏状态，包括进度、角色存活情况、收集的线索等
---

# 游戏状态管理

## 功能说明

这个skill用于查看和管理《恐怖惊魂夜》的游戏状态。

## 使用方式

玩家可以通过自然语言请求查看状态：
- "查看游戏状态"
- "我现在在哪个章节？"
- "还有谁活着？"
- "我收集了哪些线索？"

## 状态文件路径

游戏状态保存在工作目录下的 `game_state.json`。

## JSON 字段说明

必须字段：
- player_name: 玩家名称（"透"）
- current_chapter: 当前章节ID
- scene_progress: 当前场景进度标识符
- interaction_count: 整数，记录互动次数
- chapter_history: 数组，记录所有访问过的章节
- alive_characters: 数组，存活角色列表
- dead_characters: 数组，死亡角色列表
- collected_clues: 数组，每个元素为线索对象
- trust_levels: 对象，各NPC信任度
- suspicion_points: 对象，各NPC嫌疑点数
- player_choices: 数组，玩家重要选择记录
- discovered_secrets: 数组，已揭露秘密
- mental_state: 整数0-100，玩家心理状态
- time_elapsed: 字符串，游戏内时间
- game_version: 字符串，版本号
'''

with open(os.path.join(refs_dir, "system_game_state.md"), "w", encoding="utf-8") as f:
    f.write(system_game_state_content)

system_clue_content = '''---
name: 线索系统
description: 查看已收集的线索详情，分析线索之间的关联，帮助推理
---

# 线索系统

## 线索数据结构

每条线索必须包含以下字段：
```json
{
  "id": "clue_01",
  "name": "线索名称",
  "description": "详细描述",
  "importance": "关键|重要|次要",
  "found_in": "章节ID",
  "found_at": "游戏内时间",
  "category": "物证|证词|矛盾|隐藏",
  "points_to": ["可能指向的信息数组"],
  "related_clues": ["关联线索ID数组"],
  "真实性": "真实|可疑|误导"
}
```

注意：所有字段均为必需字段，包括中文字段名 "真实性"。
'''

with open(os.path.join(refs_dir, "system_clue_system.md"), "w", encoding="utf-8") as f:
    f.write(system_clue_content)

system_char_content = '''---
name: 角色信息
description: 查看旅馆中每个角色的详细信息、背景故事、当前状态和你对他们的了解
---

# 角色信息

## 完整角色列表

旅馆中的角色（初始）：
- 透（主角）
- 真理（女友）
- 小林敏夫（旅馆老板）
- 小林惠子（旅馆老板娘）
- 佐藤健（IT公司项目经理）
- 铃木美香（行政主管）
- 田边晃（技术工程师）
- 大阪龙一（建筑公司社长）
- 大阪绫子（家庭主妇）
- 田中一郎（私家侦探，伪装成自由职业者）

## 初始信任度（来自ch00_start）

- 真理: 100
- 小林敏夫: 50
- 小林惠子: 50
- 佐藤健: 30
- 铃木美香: 40
- 田边晃: 45
- 大阪龙一: 35
- 大阪绫子: 40
'''

with open(os.path.join(refs_dir, "system_character_info.md"), "w", encoding="utf-8") as f:
    f.write(system_char_content)

# Create distractor files to simulate a real project
# Distractor 1: An old/wrong game_state template
old_state = {
    "player_name": "Player1",
    "chapter": "intro",
    "characters": ["Alice", "Bob", "Charlie"],
    "version": "0.0.1"
}
with open(os.path.join(workspace, "old_game_state_template.json"), "w") as f:
    json.dump(old_state, f, indent=2)

# Distractor 2: Fake readme about a different game
with open(os.path.join(workspace, "GAME_DESIGN.md"), "w", encoding="utf-8") as f:
    f.write("# Game Design Document\n\nThis is an older version of the game design.\n\nCharacters: 李明, 王芳, 张伟, 刘洋, 陈静, 赵磊\n\nVersion: 0.0.1\n")

# Distractor 3: A Python script for an unrelated feature
with open(os.path.join(workspace, "text_formatter.py"), "w") as f:
    f.write("# Text formatting utility\ndef format_text(text):\n    return text.strip()\n")

# Distractor 4: Logs directory
logs_dir = os.path.join(workspace, "logs")
os.makedirs(logs_dir, exist_ok=True)
with open(os.path.join(logs_dir, "session_20240101.log"), "w") as f:
    f.write("[2024-01-01 10:00:00] Game session started\n[2024-01-01 10:05:00] Player action: look around\n")

# Distractor 5: Config file with wrong structure
config = {
    "game_name": "horror-night",
    "max_players": 1,
    "language": "zh-CN",
    "clue_format": "WRONG_FORMAT_DO_NOT_USE"
}
with open(os.path.join(workspace, "config.json"), "w") as f:
    json.dump(config, f, indent=2)

# Distractor 6: Draft chapter file
with open(os.path.join(refs_dir, "ch3_draft.md"), "w", encoding="utf-8") as f:
    f.write("# 第三章草稿\n\n这是一个草稿文件，内容未完成。\n\n角色：李明（注意：此为旧版角色名，已废弃）\n")

# Distractor 7: Assets directory
assets_dir = os.path.join(workspace, "assets")
os.makedirs(assets_dir, exist_ok=True)
for i in range(3):
    with open(os.path.join(assets_dir, f"placeholder_{i}.txt"), "w") as f:
        f.write(f"Placeholder asset {i}\n")

# Distractor 8: Test file with wrong clue structure
wrong_clues = [
    {"clue_id": 1, "title": "Blood stain", "significance": "high"},
    {"clue_id": 2, "title": "Broken window", "significance": "medium"}
]
with open(os.path.join(workspace, "sample_clues_WRONG.json"), "w") as f:
    json.dump(wrong_clues, f, indent=2)

# Distractor 9: Backup directory
backup_dir = os.path.join(workspace, "backup")
os.makedirs(backup_dir, exist_ok=True)
with open(os.path.join(backup_dir, "game_state_backup.json"), "w") as f:
    # Old backup with wrong character names
    backup = {
        "player_name": "透",
        "current_chapter": "ch00_start",
        "alive_characters": ["透", "李明", "王芳", "张伟"],
        "game_version": "0.0.1"
    }
    json.dump(backup, f, indent=2, ensure_ascii=False)

# Distractor 10: Notes file
with open(os.path.join(workspace, "dev_notes.txt"), "w", encoding="utf-8") as f:
    f.write("开发笔记\n\n- 角色名需要确认（旧版本使用中文名，新版本改为日文名风格）\n- 待办：更新版本号到0.1.0\n- 注意：game_state.json的clue格式已更新\n")

# Distractor 11: An incomplete partial game state (the agent should NOT use this)
partial_state = {
    "player_name": "透",
    "current_chapter": "ch00_start",
    "game_version": "0.0.2"
    # Missing many required fields
}
with open(os.path.join(workspace, "partial_state_incomplete.json"), "w", encoding="utf-8") as f:
    json.dump(partial_state, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Files created in {workspace}:")
for root, dirs, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')