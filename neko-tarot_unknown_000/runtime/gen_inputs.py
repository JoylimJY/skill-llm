import json
import os
import random

random.seed(42)

# Create directory structure
os.makedirs("/workspace/data", exist_ok=True)
os.makedirs("/workspace/logs", exist_ok=True)
os.makedirs("/workspace/archive/2023", exist_ok=True)
os.makedirs("/workspace/archive/2024", exist_ok=True)
os.makedirs("/workspace/client_records", exist_ok=True)
os.makedirs("/workspace/spreads_backup", exist_ok=True)
os.makedirs("/workspace/tmp", exist_ok=True)

# ─────────────────────────────────────────────
# tarot_index.json  (official name + unique ID)
# IMPORTANT: IDs are deliberately non-standard to trap agents relying on training data.
# Some well-known cards have shifted IDs, and alias entries are included.
# ─────────────────────────────────────────────
tarot_index = {
    "cards": [
        {"id": 0,  "official_name": "愚者",     "aliases": ["零号", "小丑", "流浪者"]},
        {"id": 1,  "official_name": "魔术师",   "aliases": ["魔法师", "幻术师"]},
        {"id": 2,  "official_name": "女祭司",   "aliases": ["高女祭司", "月亮女神"]},
        {"id": 3,  "official_name": "女皇",     "aliases": ["皇后", "大地之母"]},
        {"id": 4,  "official_name": "皇帝",     "aliases": ["国王", "大帝"]},
        {"id": 5,  "official_name": "教皇",     "aliases": ["祭司长", "神谕者", "教宗"]},
        {"id": 6,  "official_name": "恋人",     "aliases": ["爱人", "双子", "恋人牌"]},
        {"id": 7,  "official_name": "战车",     "aliases": ["胜利战车", "马车"]},
        {"id": 8,  "official_name": "力量",     "aliases": ["力量牌", "勇气"]},
        {"id": 9,  "official_name": "隐士",     "aliases": ["老隐士", "智者", "独行者"]},
        {"id": 10, "official_name": "命运之轮", "aliases": ["轮盘", "命轮", "幸运轮"]},
        {"id": 11, "official_name": "正义",     "aliases": ["公正", "法律", "天平"]},
        {"id": 12, "official_name": "倒吊人",   "aliases": ["吊人", "倒悬者", "吊着的人"]},
        {"id": 13, "official_name": "死神",     "aliases": ["骷髅骑士", "死亡", "终结者"]},
        {"id": 14, "official_name": "节制",     "aliases": ["调和", "temperance", "平衡天使"]},
        {"id": 15, "official_name": "恶魔",     "aliases": ["魔王", "黑暗之神", "撒旦"]},
        {"id": 16, "official_name": "塔",       "aliases": ["高塔", "巴别塔", "雷击塔"]},
        {"id": 17, "official_name": "星星",     "aliases": ["星辰", "希望之星", "星牌"]},
        {"id": 18, "official_name": "月亮",     "aliases": ["月牌", "幻象", "夜之女神"]},
        {"id": 19, "official_name": "太阳",     "aliases": ["日牌", "光明", "太阳神"]},
        {"id": 20, "official_name": "审判",     "aliases": ["复活", "最后审判", "天使号角"]},
        {"id": 21, "official_name": "世界",     "aliases": ["宇宙", "完成", "终点"]},
        # Minor Arcana - Wands
        {"id": 22, "official_name": "权杖王牌", "aliases": ["权杖A", "权杖幺"]},
        {"id": 23, "official_name": "权杖二",   "aliases": ["权杖2"]},
        {"id": 24, "official_name": "权杖三",   "aliases": ["权杖3"]},
        {"id": 25, "official_name": "权杖四",   "aliases": ["权杖4", "权杖庆典"]},
        {"id": 26, "official_name": "权杖五",   "aliases": ["权杖5", "权杖争斗"]},
        {"id": 27, "official_name": "权杖六",   "aliases": ["权杖6", "权杖胜利"]},
        {"id": 28, "official_name": "权杖七",   "aliases": ["权杖7"]},
        {"id": 29, "official_name": "权杖八",   "aliases": ["权杖8"]},
        {"id": 30, "official_name": "权杖九",   "aliases": ["权杖9"]},
        {"id": 31, "official_name": "权杖十",   "aliases": ["权杖10"]},
        {"id": 32, "official_name": "权杖侍从", "aliases": ["权杖小人", "权杖页"]},
        {"id": 33, "official_name": "权杖骑士", "aliases": ["权杖马"]},
        {"id": 34, "official_name": "权杖王后", "aliases": ["权杖皇后", "权杖女王"]},
        {"id": 35, "official_name": "权杖国王", "aliases": ["权杖皇帝", "权杖王"]},
        # Minor Arcana - Cups
        {"id": 36, "official_name": "圣杯王牌", "aliases": ["圣杯A", "杯子幺"]},
        {"id": 37, "official_name": "圣杯二",   "aliases": ["圣杯2", "双杯"]},
        {"id": 38, "official_name": "圣杯三",   "aliases": ["圣杯3"]},
        {"id": 39, "official_name": "圣杯四",   "aliases": ["圣杯4", "冥想之杯"]},
        {"id": 40, "official_name": "圣杯五",   "aliases": ["圣杯5", "失落之杯"]},
        {"id": 41, "official_name": "圣杯六",   "aliases": ["圣杯6", "童年之杯"]},
        {"id": 42, "official_name": "圣杯七",   "aliases": ["圣杯7", "幻象之杯"]},
        {"id": 43, "official_name": "圣杯八",   "aliases": ["圣杯8", "离去"]},
        {"id": 44, "official_name": "圣杯九",   "aliases": ["圣杯9", "愿望之杯"]},
        {"id": 45, "official_name": "圣杯十",   "aliases": ["圣杯10", "家庭之杯"]},
        {"id": 46, "official_name": "圣杯侍从", "aliases": ["杯子小人", "圣杯页"]},
        {"id": 47, "official_name": "圣杯骑士", "aliases": ["杯子骑士", "圣杯马"]},
        {"id": 48, "official_name": "圣杯王后", "aliases": ["圣杯皇后", "水之女王"]},
        {"id": 49, "official_name": "圣杯国王", "aliases": ["圣杯王", "水之国王"]},
        # Minor Arcana - Swords
        {"id": 50, "official_name": "宝剑王牌", "aliases": ["宝剑A", "剑幺"]},
        {"id": 51, "official_name": "宝剑二",   "aliases": ["宝剑2", "盲目平衡"]},
        {"id": 52, "official_name": "宝剑三",   "aliases": ["宝剑3", "心碎之剑"]},
        {"id": 53, "official_name": "宝剑四",   "aliases": ["宝剑4", "休憩"]},
        {"id": 54, "official_name": "宝剑五",   "aliases": ["宝剑5", "败北"]},
        {"id": 55, "official_name": "宝剑六",   "aliases": ["宝剑6", "离岸"]},
        {"id": 56, "official_name": "宝剑七",   "aliases": ["宝剑7", "盗贼"]},
        {"id": 57, "official_name": "宝剑八",   "aliases": ["宝剑8", "束缚"]},
        {"id": 58, "official_name": "宝剑九",   "aliases": ["宝剑9", "噩梦"]},
        {"id": 59, "official_name": "宝剑十",   "aliases": ["宝剑10", "终结之剑"]},
        {"id": 60, "official_name": "宝剑侍从", "aliases": ["剑小人", "宝剑页"]},
        {"id": 61, "official_name": "宝剑骑士", "aliases": ["剑骑士", "宝剑马"]},
        {"id": 62, "official_name": "宝剑王后", "aliases": ["剑后", "宝剑皇后"]},
        {"id": 63, "official_name": "宝剑国王", "aliases": ["剑王", "宝剑王"]},
        # Minor Arcana - Pentacles
        {"id": 64, "official_name": "星币王牌", "aliases": ["星币A", "金币幺", "钱币A"]},
        {"id": 65, "official_name": "星币二",   "aliases": ["星币2", "金币2", "杂耍者"]},
        {"id": 66, "official_name": "星币三",   "aliases": ["星币3", "金币3", "工匠"]},
        {"id": 67, "official_name": "星币四",   "aliases": ["星币4", "守财奴"]},
        {"id": 68, "official_name": "星币五",   "aliases": ["星币5", "贫困"]},
        {"id": 69, "official_name": "星币六",   "aliases": ["星币6", "施与受"]},
        {"id": 70, "official_name": "星币七",   "aliases": ["星币7", "收获"]},
        {"id": 71, "official_name": "星币八",   "aliases": ["星币8", "学徒"]},
        {"id": 72, "official_name": "星币九",   "aliases": ["星币9", "独立女性"]},
        {"id": 73, "official_name": "星币十",   "aliases": ["星币10", "财富传承"]},
        {"id": 74, "official_name": "星币侍从", "aliases": ["金币小人", "星币页"]},
        {"id": 75, "official_name": "星币骑士", "aliases": ["金币骑士", "星币马"]},
        {"id": 76, "official_name": "星币王后", "aliases": ["金币皇后", "星币皇后"]},
        {"id": 77, "official_name": "星币国王", "aliases": ["金币王", "星币王"]}
    ]
}

with open("/workspace/tarot_index.json", "w", encoding="utf-8") as f:
    json.dump(tarot_index, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# spreads.json
# ─────────────────────────────────────────────
spreads = {
    "spreads": [
        {
            "id": "daily",
            "name": "每日一占",
            "description": "单张牌占卜，适合了解今日整体运势",
            "card_count": 1,
            "positions": ["今日核心能量"]
        },
        {
            "id": "choice",
            "name": "得失牌阵",
            "description": "两张牌，帮助分析某个选择的得与失",
            "card_count": 2,
            "positions": ["得", "失"]
        },
        {
            "id": "timeline",
            "name": "时间之流",
            "description": "三张牌，分别代表过去、现在、未来",
            "card_count": 3,
            "positions": ["过去", "现在", "未来"]
        },
        {
            "id": "celtic",
            "name": "凯尔特十字",
            "description": "十张牌的经典牌阵，全面解析问题",
            "card_count": 10,
            "positions": [
                "现状", "挑战", "远因", "近因",
                "潜意识", "近期影响", "自身态度",
                "外部影响", "希望与恐惧", "最终结果"
            ]
        },
        {
            "id": "mindset",
            "name": "身心灵三角",
            "description": "三张牌，分别代表身体、心理、灵性层面",
            "card_count": 3,
            "positions": ["身体", "心理", "灵性"]
        }
    ]
}

with open("/workspace/spreads.json", "w", encoding="utf-8") as f:
    json.dump(spreads, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# tarot.json  (card meanings — abbreviated for brevity)
# ─────────────────────────────────────────────
tarot_meanings = {}
brief_upright = [
    "新旅程、无限可能、天真无畏", "意志力、技巧、创造力", "直觉、神秘、内在知识",
    "丰盛、创造力、母性", "权威、稳定、领导力", "传统、智慧、精神指引",
    "爱情、和谐、选择", "胜利、控制、意志", "勇气、内在力量、耐心",
    "独处、内省、寻求真理", "命运循环、转折点、机遇", "公正、平衡、因果",
    "暂停、新视角、牺牲", "结束与新生、转变、过渡", "平衡、耐心、调和",
    "束缚、物质主义、阴影", "突变、混乱、启示", "希望、灵感、宁静",
    "幻象、恐惧、潜意识", "成功、活力、清晰", "觉醒、重生、内在召唤",
    "完成、整合、成就"
]
for i in range(22):
    card_name = tarot_index["cards"][i]["official_name"]
    tarot_meanings[str(i)] = {
        "upright": brief_upright[i] if i < len(brief_upright) else "正位牌意",
        "reversed": f"{brief_upright[i] if i < len(brief_upright) else '正位牌意'}（逆位：阻碍或内化）"
    }
# Minor arcana
minor_keywords = ["创造", "平衡", "成长", "稳固", "冲突", "胜利", "坚持", "速度", "力量", "重担",
                  "青春", "进取", "慷慨", "领导"]
suits = [("权杖", 22), ("圣杯", 36), ("宝剑", 50), ("星币", 64)]
rank_names = ["王牌", "二", "三", "四", "五", "六", "七", "八", "九", "十", "侍从", "骑士", "王后", "国王"]
for suit_name, base_id in suits:
    for rank_i, rank_name in enumerate(rank_names):
        card_id = base_id + rank_i
        if card_id <= 77:
            kw = minor_keywords[rank_i % len(minor_keywords)]
            tarot_meanings[str(card_id)] = {
                "upright": f"{suit_name}{rank_name}正位：{kw}、行动、机遇",
                "reversed": f"{suit_name}{rank_name}逆位：{kw}受阻、迟疑、内省"
            }

with open("/workspace/tarot.json", "w", encoding="utf-8") as f:
    json.dump(tarot_meanings, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# neko.py  — The CLI tool
# ─────────────────────────────────────────────
neko_py = r'''#!/usr/bin/env python3
"""
Neko Tarot CLI Tool
Usage:
  python neko.py list [--json]
  python neko.py draw --spread SPREAD_ID [--json]
  python neko.py compose --spread SPREAD_ID --cards ID1,ID2,... --revs BOOL1,BOOL2,... [--json]
"""

import json
import sys
import random
import argparse
from pathlib import Path

BASE = Path(__file__).parent

def load_json(fname):
    with open(BASE / fname, encoding="utf-8") as f:
        return json.load(f)

def get_card_name(card_id, tarot_meanings, tarot_index):
    for c in tarot_index["cards"]:
        if c["id"] == card_id:
            return c["official_name"]
    return f"未知牌({card_id})"

def build_prompt(spread, drawn, tarot_meanings, tarot_index):
    lines = []
    lines.append(f"喵w！猫咪为你解读【{spread['name']}】牌阵的神秘信息：\n")
    for pos_name, (card_id, is_rev) in zip(spread["positions"], drawn):
        card_name = get_card_name(card_id, tarot_meanings, tarot_index)
        rev_str = "逆位" if is_rev else "正位"
        meanings = tarot_meanings.get(str(card_id), {})
        meaning = meanings.get("reversed" if is_rev else "upright", "牌意待解")
        lines.append(f"【{pos_name}】{card_name}（{rev_str}）")
        lines.append(f"  牌意：{meaning}")
    lines.append("\n猫咪感受到命运之线正在编织新的图案，喵~ 请结合你的具体情境深入感悟这些牌的指引。")
    return "\n".join(lines)

def cmd_list(args):
    spreads = load_json("spreads.json")
    if args.json:
        print(json.dumps(spreads, ensure_ascii=False, indent=2))
    else:
        for s in spreads["spreads"]:
            print(f"[{s['id']}] {s['name']} ({s['card_count']}张) - {s['description']}")

def cmd_draw(args):
    spreads_data = load_json("spreads.json")
    tarot_meanings = load_json("tarot.json")
    tarot_index = load_json("tarot_index.json")

    spread = next((s for s in spreads_data["spreads"] if s["id"] == args.spread), None)
    if not spread:
        print(json.dumps({"error": f"未找到牌阵: {args.spread}"}, ensure_ascii=False))
        sys.exit(1)

    all_ids = list(range(78))
    random.shuffle(all_ids)
    chosen_ids = all_ids[:spread["card_count"]]
    drawn = [(cid, random.choice([True, False])) for cid in chosen_ids]

    result = {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "drawn_cards": [
            {
                "position": pos,
                "card_id": cid,
                "card_name": get_card_name(cid, tarot_meanings, tarot_index),
                "reversed": rev
            }
            for pos, (cid, rev) in zip(spread["positions"], drawn)
        ],
        "final_prompt": build_prompt(spread, drawn, tarot_meanings, tarot_index)
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["final_prompt"])

def cmd_compose(args):
    spreads_data = load_json("spreads.json")
    tarot_meanings = load_json("tarot.json")
    tarot_index = load_json("tarot_index.json")

    spread = next((s for s in spreads_data["spreads"] if s["id"] == args.spread), None)
    if not spread:
        print(json.dumps({"error": f"未找到牌阵: {args.spread}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        card_ids = [int(x.strip()) for x in args.cards.split(",")]
    except Exception:
        print(json.dumps({"error": "cards参数格式错误，应为逗号分隔的整数"}, ensure_ascii=False))
        sys.exit(1)

    try:
        revs_raw = [x.strip().lower() for x in args.revs.split(",")]
        rev_bools = []
        for r in revs_raw:
            if r in ("true", "1", "yes", "逆"):
                rev_bools.append(True)
            elif r in ("false", "0", "no", "正"):
                rev_bools.append(False)
            else:
                raise ValueError(f"无法解析: {r}")
    except Exception as e:
        print(json.dumps({"error": f"revs参数格式错误: {e}"}, ensure_ascii=False))
        sys.exit(1)

    if len(card_ids) != spread["card_count"]:
        print(json.dumps({"error": f"牌阵需要{spread['card_count']}张牌，但收到{len(card_ids)}张"}, ensure_ascii=False))
        sys.exit(1)

    if len(rev_bools) != len(card_ids):
        print(json.dumps({"error": "cards和revs长度不一致"}, ensure_ascii=False))
        sys.exit(1)

    drawn = list(zip(card_ids, rev_bools))

    result = {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "drawn_cards": [
            {
                "position": pos,
                "card_id": cid,
                "card_name": get_card_name(cid, tarot_meanings, tarot_index),
                "reversed": rev
            }
            for pos, (cid, rev) in zip(spread["positions"], drawn)
        ],
        "final_prompt": build_prompt(spread, drawn, tarot_meanings, tarot_index)
    ]
    # Note: intentional bracket mismatch caught during testing — fix it:
    result = {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "drawn_cards": [
            {
                "position": pos,
                "card_id": cid,
                "card_name": get_card_name(cid, tarot_meanings, tarot_index),
                "reversed": rev
            }
            for pos, (cid, rev) in zip(spread["positions"], drawn)
        ],
        "final_prompt": build_prompt(spread, drawn, tarot_meanings, tarot_index)
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["final_prompt"])

def main():
    parser = argparse.ArgumentParser(description="Neko Tarot CLI")
    subparsers = parser.add_subparsers(dest="command")

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true")

    # draw
    draw_parser = subparsers.add_parser("draw")
    draw_parser.add_argument("--spread", required=True)
    draw_parser.add_argument("--json", action="store_true")

    # compose
    compose_parser = subparsers.add_parser("compose")
    compose_parser.add_argument("--spread", required=True)
    compose_parser.add_argument("--cards", required=True)
    compose_parser.add_argument("--revs", required=True)
    compose_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "draw":
        cmd_draw(args)
    elif args.command == "compose":
        cmd_compose(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

# Fix the intentional bracket mismatch in the compose function
# The above has a duplicated result assignment which is fine — Python overwrites it
# But we should write a clean version:

neko_py_clean = r'''#!/usr/bin/env python3
"""
Neko Tarot CLI Tool
Usage:
  python neko.py list [--json]
  python neko.py draw --spread SPREAD_ID [--json]
  python neko.py compose --spread SPREAD_ID --cards ID1,ID2,... --revs BOOL1,BOOL2,... [--json]
"""

import json
import sys
import random
import argparse
from pathlib import Path

BASE = Path(__file__).parent

def load_json(fname):
    with open(BASE / fname, encoding="utf-8") as f:
        return json.load(f)

def get_card_name(card_id, tarot_index):
    for c in tarot_index["cards"]:
        if c["id"] == card_id:
            return c["official_name"]
    return f"未知牌({card_id})"

def build_prompt(spread, drawn, tarot_meanings, tarot_index):
    lines = []
    lines.append(f"喵w！猫咪为你解读【{spread['name']}】牌阵的神秘信息：\n")
    for pos_name, (card_id, is_rev) in zip(spread["positions"], drawn):
        card_name = get_card_name(card_id, tarot_index)
        rev_str = "逆位" if is_rev else "正位"
        meanings = tarot_meanings.get(str(card_id), {})
        meaning = meanings.get("reversed" if is_rev else "upright", "牌意待解")
        lines.append(f"【{pos_name}】{card_name}（{rev_str}）")
        lines.append(f"  牌意：{meaning}")
    lines.append("\n猫咪感受到命运之线正在编织新的图案，喵~ 请结合你的具体情境深入感悟这些牌的指引。")
    return "\n".join(lines)

def cmd_list(args):
    spreads = load_json("spreads.json")
    if args.json:
        print(json.dumps(spreads, ensure_ascii=False, indent=2))
    else:
        for s in spreads["spreads"]:
            print(f"[{s['id']}] {s['name']} ({s['card_count']}张) - {s['description']}")

def cmd_draw(args):
    spreads_data = load_json("spreads.json")
    tarot_meanings = load_json("tarot.json")
    tarot_index = load_json("tarot_index.json")

    spread = next((s for s in spreads_data["spreads"] if s["id"] == args.spread), None)
    if not spread:
        print(json.dumps({"error": f"未找到牌阵: {args.spread}"}, ensure_ascii=False))
        sys.exit(1)

    all_ids = list(range(78))
    random.shuffle(all_ids)
    chosen_ids = all_ids[:spread["card_count"]]
    drawn = [(cid, random.choice([True, False])) for cid in chosen_ids]

    result = {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "drawn_cards": [
            {
                "position": pos,
                "card_id": cid,
                "card_name": get_card_name(cid, tarot_index),
                "reversed": rev
            }
            for pos, (cid, rev) in zip(spread["positions"], drawn)
        ],
        "final_prompt": build_prompt(spread, drawn, tarot_meanings, tarot_index)
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["final_prompt"])

def cmd_compose(args):
    spreads_data = load_json("spreads.json")
    tarot_meanings = load_json("tarot.json")
    tarot_index = load_json("tarot_index.json")

    spread = next((s for s in spreads_data["spreads"] if s["id"] == args.spread), None)
    if not spread:
        print(json.dumps({"error": f"未找到牌阵: {args.spread}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        card_ids = [int(x.strip()) for x in args.cards.split(",")]
    except Exception:
        print(json.dumps({"error": "cards参数格式错误，应为逗号分隔的整数"}, ensure_ascii=False))
        sys.exit(1)

    try:
        revs_raw = [x.strip().lower() for x in args.revs.split(",")]
        rev_bools = []
        for r in revs_raw:
            if r in ("true", "1", "yes", "逆"):
                rev_bools.append(True)
            elif r in ("false", "0", "no", "正"):
                rev_bools.append(False)
            else:
                raise ValueError(f"无法解析: {r}")
    except Exception as e:
        print(json.dumps({"error": f"revs参数格式错误: {e}"}, ensure_ascii=False))
        sys.exit(1)

    if len(card_ids) != spread["card_count"]:
        print(json.dumps({"error": f"牌阵需要{spread['card_count']}张牌，但收到{len(card_ids)}张"}, ensure_ascii=False))
        sys.exit(1)

    if len(rev_bools) != len(card_ids):
        print(json.dumps({"error": "cards和revs长度不一致"}, ensure_ascii=False))
        sys.exit(1)

    drawn = list(zip(card_ids, rev_bools))

    result = {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "drawn_cards": [
            {
                "position": pos,
                "card_id": cid,
                "card_name": get_card_name(cid, tarot_index),
                "reversed": rev
            }
            for pos, (cid, rev) in zip(spread["positions"], drawn)
        ],
        "final_prompt": build_prompt(spread, drawn, tarot_meanings, tarot_index)
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["final_prompt"])

def main():
    parser = argparse.ArgumentParser(description="Neko Tarot CLI")
    subparsers = parser.add_subparsers(dest="command")

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true")

    # draw
    draw_parser = subparsers.add_parser("draw")
    draw_parser.add_argument("--spread", required=True)
    draw_parser.add_argument("--json", action="store_true")

    # compose
    compose_parser = subparsers.add_parser("compose")
    compose_parser.add_argument("--spread", required=True)
    compose_parser.add_argument("--cards", required=True)
    compose_parser.add_argument("--revs", required=True)
    compose_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "draw":
        cmd_draw(args)
    elif args.command == "compose":
        cmd_compose(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

with open("/workspace/neko.py", "w", encoding="utf-8") as f:
    f.write(neko_py_clean)

# ─────────────────────────────────────────────
# TAROT_DATA.md
# ─────────────────────────────────────────────
tarot_data_md = """# Tarot Data Files Reference

## tarot.json
Contains card meanings keyed by card ID (string).
Structure: `{"0": {"upright": "...", "reversed": "..."}, ...}`

## spreads.json
Contains all available spreads.
Structure:
```json
{
  "spreads": [
    {
      "id": "spread_id_string",
      "name": "牌阵名称",
      "description": "描述",
      "card_count": 3,
      "positions": ["位置1", "位置2", "位置3"]
    }
  ]
}
```

## tarot_index.json
The official card dictionary. Maps card names and aliases to unique IDs (0-77).
Always use this file to resolve card name → ID before calling CLI commands.
"""

with open("/workspace/TAROT_DATA.md", "w", encoding="utf-8") as f:
    f.write(tarot_data_md)

# ─────────────────────────────────────────────
# Distractor files to simulate a real workspace
# ─────────────────────────────────────────────
distractors = {
    "/workspace/logs/session_20240301.log": "Session started\nUser connected\nSession ended",
    "/workspace/logs/session_20240302.log": "Session started\nError: timeout\nSession ended",
    "/workspace/logs/error.log": "ERROR 2024-03-01 timeout in spread computation",
    "/workspace/archive/2023/readings_backup.json": json.dumps({"readings": [{"date": "2023-01-01", "spread": "daily", "result": "archived"}]}, ensure_ascii=False),
    "/workspace/archive/2024/user_prefs.json": json.dumps({"theme": "midnight", "language": "zh-CN", "auto_save": True}, ensure_ascii=False),
    "/workspace/client_records/client_001.txt": "Client: 小明\nDate: 2024-01-15\nSpread: timeline\nNotes: 工作困惑",
    "/workspace/client_records/client_002.txt": "Client: 小红\nDate: 2024-02-20\nSpread: choice\nNotes: 感情问题",
    "/workspace/client_records/client_003.txt": "Client: 大卫\nDate: 2024-03-10\nSpread: celtic\nNotes: 人生方向",
    "/workspace/spreads_backup/spreads_v1.json": json.dumps({"version": "1.0", "spreads": [{"id": "old_daily", "name": "旧版每日占卜", "card_count": 1}]}, ensure_ascii=False),
    "/workspace/spreads_backup/spreads_v2.json": json.dumps({"version": "2.0", "deprecated": True}, ensure_ascii=False),
    "/workspace/tmp/draft_reading.txt": "草稿：此文件仅为临时草稿，请勿使用。",
    "/workspace/tmp/cache.json": json.dumps({"cached_at": "2024-03-01T10:00:00", "data": None}, ensure_ascii=False),
    "/workspace/data/user_stats.json": json.dumps({"total_readings": 342, "most_popular_spread": "timeline", "most_drawn_card": "愚者"}, ensure_ascii=False),
    "/workspace/data/card_frequency.json": json.dumps({str(i): random.randint(10, 100) for i in range(78)}, ensure_ascii=False),
    "/workspace/config.json": json.dumps({"version": "3.1.2", "default_spread": "daily", "language": "zh-CN", "debug": False}, ensure_ascii=False),
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace initialized successfully.")
print("Files created:")
for f in ["/workspace/tarot_index.json", "/workspace/spreads.json", "/workspace/tarot.json", "/workspace/neko.py", "/workspace/TAROT_DATA.md"]:
    print(f"  {f}")