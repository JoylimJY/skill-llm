import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "references",
    "references/old_versions",
    "assets",
    "assets/maps",
    "assets/npcs",
    "design_docs",
    "design_docs/lore",
    "design_docs/mechanics",
    "scratch",
    "scratch/experiments",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# distractor: partial world design doc (NOT a hint, just theme notes)
with open(os.path.join(workspace, "design_docs/lore/world_notes.txt"), "w") as f:
    f.write("""海底遗迹世界观草稿
===================
故事背景：2387年，人类在深海发现了一座沉没已久的古代海底基地——"深渊站"。
玩家扮演一名深海考古学家，潜入基地寻找传说中的"海渊核心"。

地点构想（草稿，未定稿）：
- 潜水艇停靠坞
- 氧气补给室
- 指挥室（锁着的？）
- 动力舱
- 实验室？
- 最终宝库

敌人构想：
- 变异章鱼兵（守门的）
- 腐化研究员（友善？）

注意：以上只是头脑风暴，不代表最终设计。
""")

# distractor: old broken game.py (syntax errors, wrong schema)
with open(os.path.join(workspace, "references/old_versions/game_v0.py"), "w") as f:
    f.write("""# OLD VERSION - DO NOT USE - broken schema
rooms = {
    "start": {
        "description": "A broken room.",  # wrong key: should be 'desc'
        "connections": {"north": "hall"},  # wrong key: should be 'exits'
    }
}

npcs_list = [  # wrong: should be a dict
    {"id": "guard", "health": 50}  # wrong keys
]

def run():
    pass  # incomplete
""")

# distractor: item catalogue CSV
with open(os.path.join(workspace, "assets/item_catalogue.csv"), "w") as f:
    f.write("""item_id,display_name,type,effect_code
oxygen_tank,氧气瓶,consumable,HP_RESTORE_25
power_cell,能量电池,key_item,UNLOCK_DOOR
ancient_trident,远古三叉戟,weapon,ATK_BOOST_10
pressure_suit,耐压战甲,armor,DEF_BOOST_5
deep_core,海渊核心,quest,QUEST_COMPLETE
""")

# distractor: NPC dialogue script (wrong format, for reference only)
with open(os.path.join(workspace, "assets/npcs/dialogue_draft.json"), "w") as f:
    f.write("""{
  "腐化研究员": {
    "lines": [
      {"trigger": "hello", "response": "...在深渊里太久了..."},
      {"trigger": "core", "response": "核心在最里面的宝库...小心守卫..."}
    ]
  },
  "变异章鱼兵": {
    "lines": []
  }
}
""")

# distractor: map layout image description (text only, not the actual map)
with open(os.path.join(workspace, "assets/maps/layout_description.txt"), "w") as f:
    f.write("""地图布局说明（文字版）
潜水艇停靠坞 --北--> 主走廊
主走廊 --东--> 氧气室
主走廊 --西--> 动力舱
主走廊 --北--> 指挥室（锁着）
动力舱 --北--> 实验室
实验室 --东--> 宝库（终点）

注意：这是早期草图，路径可能变化。
""")

# distractor: game-systems reference (partial, incomplete)
with open(os.path.join(workspace, "references/game-systems.md"), "w") as f:
    f.write("""# Game Systems Reference (Partial Draft)

## Combat System
- Turn-based: player attacks first, then enemy
- Damage = random range around attack stat
- Death condition: hp <= 0

## Item Effects
- heal: restore HP
- power: increase attack
- None: no effect

## Quest Flags
Use player["flags"] dict to track progress.
Example: player["flags"]["quest_started"] = True

(This document is incomplete. See main SKILL.md for full template.)
""")

# distractor: world-design reference stub
with open(os.path.join(workspace, "references/world-design.md"), "w") as f:
    f.write("""# World Design Reference (Stub)

## Story Structure
1. Introduction room - orient player
2. Mid-game rooms - exploration and conflict
3. Boss room - key challenge
4. Treasure/goal room - locked, requires key or boss defeat

## Tips
- Keep room descriptions atmospheric
- Exits must be consistent (if A->north->B, then B->south->A)
- NPC dialogue keys should be short trigger words
""")

# distractor: examples stub
with open(os.path.join(workspace, "references/examples.md"), "w") as f:
    f.write("""# Examples (Stub)

See the default template in SKILL.md for a working 3-room example.
Extend by adding more rooms to the `rooms` dict.
""")

# distractor: mechanics scratch notes
with open(os.path.join(workspace, "design_docs/mechanics/combat_notes.txt"), "w") as f:
    f.write("""战斗机制笔记
- 玩家初始HP: 100
- 普通攻击: 10
- 怪物攻击力建议: 5-15之间
- boss攻击力: 15-20
- 注意：击败boss后需要解锁宝库

道具系统：
- 治疗类：使用后消耗，回复生命
- 增益类：使用后提升属性，消耗
""")

# distractor: scratch experiment (incomplete, non-functional)
with open(os.path.join(workspace, "scratch/experiments/test_combat.py"), "w") as f:
    f.write("""# Scratch experiment - not final
import random

def quick_combat_test():
    player_hp = 100
    enemy_hp = 40
    while player_hp > 0 and enemy_hp > 0:
        enemy_hp -= random.randint(8, 12)
        if enemy_hp > 0:
            player_hp -= random.randint(6, 10)
    print("Result:", "win" if enemy_hp <= 0 else "lose")

quick_combat_test()
""")

# distractor: requirements / dependencies note
with open(os.path.join(workspace, "scratch/requirements_notes.txt"), "w") as f:
    f.write("""游戏依赖说明
- 只需要Python标准库（random模块）
- 单文件运行：python game.py
- 不需要额外安装任何包
""")

# distractor: author notes
with open(os.path.join(workspace, "design_docs/author_notes.txt"), "w") as f:
    f.write("""项目负责人：海洋游戏工作室
目标平台：CLI / Terminal
目标受众：硬核文字冒险爱好者
预计发布：原型Demo阶段

核心玩法循环：
探索 → 收集氧气瓶 → 对话NPC获取线索 → 击败变异章鱼兵 → 进入宝库 → 获得海渊核心
""")

# distractor: changelog
with open(os.path.join(workspace, "CHANGELOG.txt"), "w") as f:
    f.write("""CHANGELOG
=========
v0.1 - 初始草稿，世界观设定
v0.2 - 添加NPC对话草稿
v0.3 - 战斗系统设计讨论
（game.py 尚未创建）
""")

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for file in files:
        path = os.path.join(root, file)
        print(f"  {path}")