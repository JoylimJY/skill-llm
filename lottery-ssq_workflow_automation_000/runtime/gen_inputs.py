import os
import json
import csv
import random
import datetime

random.seed(42)

BASE = "/workspace/lottery-ssq"

# Create full directory structure
dirs = [
    f"{BASE}/data",
    f"{BASE}/scripts",
    f"{BASE}/outputs",
    f"{BASE}/backtests",
    f"{BASE}/docs",
    f"{BASE}/logs",
    f"{BASE}/archive/2023",
    f"{BASE}/archive/2022",
    f"{BASE}/tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── config.json (intentionally set to "stable" with conservative params) ──────
config = {
    "candidate_pool_size": 500,
    "hot_cold_cycles": {
        "short": 10,
        "medium": 20,
        "long": 30
    },
    "hot_cold_weights": {
        "short": 0.5,
        "medium": 0.3,
        "long": 0.2
    },
    "filters": {
        "ac_value_min": 4,
        "ac_value_max": 8,
        "span_min": 10,
        "span_max": 25,
        "tail_sum_min": 10,
        "tail_sum_max": 30,
        "odd_even_ratio": ["2:4", "3:3", "4:2"]
    },
    "blue_ball": {
        "zones": [[1, 5], [6, 11], [12, 16]],
        "prefer_missing_min": 3
    },
    "strategy": "stable",
    "output_main": 2,
    "output_backup": 3
}
with open(f"{BASE}/config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

# ── Generate realistic ssq_history.csv with 3420 rows ─────────────────────────
def gen_red_balls():
    return sorted(random.sample(range(1, 34), 6))

def gen_blue_ball():
    return random.randint(1, 16)

start_date = datetime.date(2003, 2, 24)
rows = []
issue_num = 2003001

for i in range(3420):
    # advance date roughly every 3-4 days
    delta = random.choice([3, 3, 4, 4, 7])
    start_date += datetime.timedelta(days=delta)
    reds = gen_red_balls()
    blue = gen_blue_ball()
    year = start_date.year
    issue = f"{year}{(i % 150 + 1):03d}"
    rows.append({
        "issue": issue,
        "date": start_date.strftime("%Y-%m-%d"),
        "red1": reds[0],
        "red2": reds[1],
        "red3": reds[2],
        "red4": reds[3],
        "red5": reds[4],
        "red6": reds[5],
        "blue": blue,
        "sales": random.randint(200000000, 800000000),
        "pool": random.randint(100000000, 2000000000),
    })

fieldnames = ["issue", "date", "red1", "red2", "red3", "red4", "red5", "red6", "blue", "sales", "pool"]
with open(f"{BASE}/data/ssq_history.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# ── scripts/update_ssq_history.py ─────────────────────────────────────────────
update_script = '''#!/usr/bin/env python3
"""
双色球历史数据更新脚本
从本地数据源刷新并追加最新一期数据（沙盒模式：直接追加模拟数据）
"""
import csv
import os
import random
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "ssq_history.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

random.seed(999)

def read_last_issue(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if rows:
        last = rows[-1]
        return last["issue"], last["date"]
    return None, None

def gen_new_entry(last_date_str):
    last_date = datetime.date.fromisoformat(last_date_str)
    new_date = last_date + datetime.timedelta(days=3)
    reds = sorted(random.sample(range(1, 34), 6))
    blue = random.randint(1, 16)
    issue = new_date.strftime("%Y") + f"{random.randint(100,150):03d}"
    return {
        "issue": issue,
        "date": new_date.strftime("%Y-%m-%d"),
        "red1": reds[0], "red2": reds[1], "red3": reds[2],
        "red4": reds[3], "red5": reds[4], "red6": reds[5],
        "blue": blue,
        "sales": random.randint(200000000, 800000000),
        "pool": random.randint(100000000, 2000000000),
    }

last_issue, last_date = read_last_issue(DATA_FILE)
if last_issue is None:
    print("[ERROR] 历史数据文件为空或缺失")
    exit(1)

new_entry = gen_new_entry(last_date)
fieldnames = ["issue","date","red1","red2","red3","red4","red5","red6","blue","sales","pool"]
with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writerow(new_entry)

log_msg = f"[UPDATE] 已追加期号 {new_entry[\'issue\']} 日期 {new_entry[\'date\']} 红球 {[new_entry[\'red\'+str(i)] for i in range(1,7)]} 蓝球 {new_entry[\'blue\']}\\n"
with open(os.path.join(LOG_DIR, "update.log"), "a", encoding="utf-8") as lf:
    lf.write(log_msg)

print(f"[OK] 数据更新完成: {new_entry[\'issue\']} / {new_entry[\'date\']}")
print(f"[INFO] 当前共 {sum(1 for _ in open(DATA_FILE, encoding=\'utf-8\')) - 1} 条历史记录")
'''
with open(f"{BASE}/scripts/update_ssq_history.py", "w", encoding="utf-8") as f:
    f.write(update_script)

# ── scripts/generate_ssq.py ───────────────────────────────────────────────────
generate_script = r'''#!/usr/bin/env python3
"""
双色球选号生成脚本 v2
策略: stable / balanced / aggressive
输出: 2注主推 + 3注备选
"""
import csv
import json
import os
import random
import itertools
import datetime
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATA_FILE = os.path.join(BASE_DIR, "data", "ssq_history.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_history(filepath):
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            reds = [int(row[f"red{i}"]) for i in range(1,7)]
            blue = int(row["blue"])
            rows.append({"reds": reds, "blue": blue, "date": row["date"], "issue": row["issue"]})
    return rows

def compute_freq(history, n):
    recent = history[-n:]
    red_count = Counter()
    blue_count = Counter()
    for entry in recent:
        for r in entry["reds"]:
            red_count[r] += 1
        blue_count[entry["blue"]] += 1
    return red_count, blue_count

def weighted_red_score(ball, history, weights, cycles):
    score = 0.0
    for key, w in weights.items():
        n = cycles[key]
        freq, _ = compute_freq(history, n)
        total = sum(freq.values()) or 1
        score += w * (freq[ball] / total)
    return score

def weighted_blue_score(ball, history, weights, cycles, prefer_missing_min):
    score = 0.0
    for key, w in weights.items():
        n = cycles[key]
        _, bfreq = compute_freq(history, n)
        total = sum(bfreq.values()) or 1
        score += w * (bfreq[ball] / total)
    # missing bonus
    missing = 0
    for entry in reversed(history):
        if entry["blue"] == ball:
            break
        missing += 1
    if missing >= prefer_missing_min:
        score += 0.05 * (missing / 10.0)
    return score

def compute_ac(balls):
    diffs = set()
    for i in range(len(balls)):
        for j in range(i+1, len(balls)):
            diffs.add(abs(balls[i] - balls[j]))
    return len(diffs) - (len(balls) - 1)

def compute_span(balls):
    return max(balls) - min(balls)

def tail_sum(balls):
    return sum(b % 10 for b in balls)

def odd_even_ratio(balls):
    odds = sum(1 for b in balls if b % 2 == 1)
    evens = len(balls) - odds
    return f"{odds}:{evens}"

def zone_of_red(balls):
    z1 = sum(1 for b in balls if 1 <= b <= 11)
    z2 = sum(1 for b in balls if 12 <= b <= 22)
    z3 = sum(1 for b in balls if 23 <= b <= 33)
    return f"{z1}-{z2}-{z3}"

def zone_of_blue(ball, zones):
    for zi, (lo, hi) in enumerate(zones, 1):
        if lo <= ball <= hi:
            return f"区{zi}"
    return "未知"

def strategy_params(strategy):
    if strategy == "stable":
        return {"ac_min": 4, "ac_max": 8, "span_min": 10, "span_max": 25, "ts_min": 10, "ts_max": 30, "top_red": 15, "top_blue": 6}
    elif strategy == "balanced":
        return {"ac_min": 3, "ac_max": 9, "span_min": 8, "span_max": 28, "ts_min": 8, "ts_max": 35, "top_red": 20, "top_blue": 8}
    elif strategy == "aggressive":
        return {"ac_min": 2, "ac_max": 10, "span_min": 5, "span_max": 30, "ts_min": 5, "ts_max": 40, "top_red": 25, "top_blue": 10}
    else:
        raise ValueError(f"未知策略: {strategy}")

def main():
    cfg = load_config()
    history = load_history(DATA_FILE)
    strategy = cfg.get("strategy", "stable")
    cycles = cfg["hot_cold_cycles"]
    weights = cfg["hot_cold_weights"]
    pool_size = cfg["candidate_pool_size"]
    prefer_missing_min = cfg["blue_ball"]["prefer_missing_min"]
    blue_zones = cfg["blue_ball"]["zones"]
    sp = strategy_params(strategy)

    # Score all red balls
    red_scores = {}
    for ball in range(1, 34):
        red_scores[ball] = weighted_red_score(ball, history, weights, cycles)
    top_reds = sorted(red_scores, key=lambda b: red_scores[b], reverse=True)[:sp["top_red"]]

    # Score all blue balls
    blue_scores = {}
    for ball in range(1, 17):
        blue_scores[ball] = weighted_blue_score(ball, history, weights, cycles, prefer_missing_min)
    top_blues = sorted(blue_scores, key=lambda b: blue_scores[b], reverse=True)[:sp["top_blue"]]

    # Generate candidate combos
    random.seed(2024)
    all_combos = list(itertools.combinations(top_reds, 6))
    random.shuffle(all_combos)
    candidates = all_combos[:pool_size]

    # Filter and score
    scored = []
    for combo in candidates:
        balls = list(combo)
        ac = compute_ac(balls)
        span = compute_span(balls)
        ts = tail_sum(balls)
        oe = odd_even_ratio(balls)
        if not (sp["ac_min"] <= ac <= sp["ac_max"]):
            continue
        if not (sp["span_min"] <= span <= sp["span_max"]):
            continue
        if not (sp["ts_min"] <= ts <= sp["ts_max"]):
            continue
        red_score = sum(red_scores[b] for b in balls)
        scored.append((balls, red_score, ac, span, ts, oe))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Pick best blue per combo
    results = []
    for balls, rscore, ac, span, ts, oe in scored[:20]:
        best_blue = max(top_blues, key=lambda b: blue_scores[b])
        total_score = rscore + blue_scores[best_blue]
        zone = zone_of_red(balls)
        bzone = zone_of_blue(best_blue, blue_zones)
        ball_sum = sum(balls)
        results.append({
            "reds": sorted(balls),
            "blue": best_blue,
            "score": round(total_score, 6),
            "odd_even": oe,
            "red_zone": zone,
            "sum": ball_sum,
            "span": span,
            "ac": ac,
            "blue_zone": bzone,
            "strategy": strategy,
        })

    main_picks = results[:2]
    backup_picks = results[2:5]

    # Output
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(OUTPUT_DIR, f"ssq_{strategy}_{now}.json")
    output = {
        "generated_at": now,
        "strategy": strategy,
        "main_picks": main_picks,
        "backup_picks": backup_picks,
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] 选号完成，策略: {strategy}")
    print(f"[主推] {len(main_picks)} 注")
    for i, p in enumerate(main_picks, 1):
        print(f"  #{i}: 红球 {p['reds']} 蓝球 {p['blue']}  评分={p['score']}  奇偶={p['odd_even']}  和值={p['sum']}  极距={p['span']}  AC={p['ac']}")
    print(f"[备选] {len(backup_picks)} 注")
    for i, p in enumerate(backup_picks, 1):
        print(f"  #{i}: 红球 {p['reds']} 蓝球 {p['blue']}  评分={p['score']}  奇偶={p['odd_even']}  和值={p['sum']}  极距={p['span']}  AC={p['ac']}")
    print(f"[输出] {out_file}")

if __name__ == "__main__":
    main()
'''
with open(f"{BASE}/scripts/generate_ssq.py", "w", encoding="utf-8") as f:
    f.write(generate_script)

# ── scripts/backtest_ssq.py ───────────────────────────────────────────────────
backtest_script = r'''#!/usr/bin/env python3
"""
双色球回测脚本
读取 outputs/ 目录中最新的选号结果，与历史数据最后N期对比，输出命中统计
"""
import csv
import json
import os
import glob
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "ssq_history.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
BACKTEST_DIR = os.path.join(BASE_DIR, "backtests")
os.makedirs(BACKTEST_DIR, exist_ok=True)

def load_history(filepath, n=50):
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            reds = [int(row[f"red{i}"]) for i in range(1,7)]
            blue = int(row["blue"])
            rows.append({"reds": reds, "blue": blue, "date": row["date"], "issue": row["issue"]})
    return rows[-n:]

def match_prize(pred_reds, pred_blue, actual_reds, actual_blue):
    red_hit = len(set(pred_reds) & set(actual_reds))
    blue_hit = (pred_blue == actual_blue)
    if red_hit == 6 and blue_hit: return "一等奖"
    if red_hit == 6: return "二等奖"
    if red_hit == 5 and blue_hit: return "三等奖"
    if red_hit == 5 or (red_hit == 4 and blue_hit): return "四等奖"
    if red_hit == 4 or (red_hit == 3 and blue_hit): return "五等奖"
    if blue_hit: return "六等奖"
    return "未中奖"

# Find latest output file
files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "ssq_*.json")))
if not files:
    print("[ERROR] outputs/ 目录中没有选号文件，请先运行 generate_ssq.py")
    exit(1)

latest = files[-1]
with open(latest, "r", encoding="utf-8") as f:
    sel = json.load(f)

strategy = sel.get("strategy", "unknown")
all_picks = sel.get("main_picks", []) + sel.get("backup_picks", [])
history = load_history(DATA_FILE, n=30)

results = []
for pick in all_picks:
    pick_type = "主推" if all_picks.index(pick) < 2 else "备选"
    for entry in history:
        prize = match_prize(pick["reds"], pick["blue"], entry["reds"], entry["blue"])
        results.append({
            "pick_type": pick_type,
            "reds": pick["reds"],
            "blue": pick["blue"],
            "vs_issue": entry["issue"],
            "vs_date": entry["date"],
            "prize": prize,
        })

prize_counts = {}
for r in results:
    prize_counts[r["prize"]] = prize_counts.get(r["prize"], 0) + 1

now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bt_file = os.path.join(BACKTEST_DIR, f"backtest_{strategy}_{now}.json")
output = {
    "source_file": os.path.basename(latest),
    "strategy": strategy,
    "tested_issues": len(history),
    "total_picks": len(all_picks),
    "prize_summary": prize_counts,
    "details": results[:50],
}
with open(bt_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"[OK] 回测完成，策略={strategy}，测试期数={len(history)}")
print(f"[统计] {prize_counts}")
print(f"[输出] {bt_file}")
'''
with open(f"{BASE}/scripts/backtest_ssq.py", "w", encoding="utf-8") as f:
    f.write(backtest_script)

# ── docs/strategy.md ─────────────────────────────────────────────────────────
strategy_doc = """# 策略说明

## 策略类型

### stable（稳健）
- AC 值范围：4-8
- 极距范围：10-25
- 尾数和范围：10-30
- 候选红球数：15
- 候选蓝球数：6
- 适合保守型选手

### balanced（均衡）
- AC 值范围：3-9
- 极距范围：8-28
- 尾数和范围：8-35
- 候选红球数：20
- 候选蓝球数：8
- 默认推荐策略

### aggressive（激进）
- AC 值范围：2-10
- 极距范围：5-30
- 尾数和范围：5-40
- 候选红球数：25
- 候选蓝球数：10
- 适合高风险偏好用户，追求覆盖面

## 冷热周期权重
- 默认权重：短期(10期)0.5，中期(20期)0.3，长期(30期)0.2
- 激进模式建议短期加权更高

## AC 值说明
AC 值（Arithmetic Complexity）反映号码之间的差异多样性。
较高的 AC 值意味着号码组合更分散。
"""
with open(f"{BASE}/docs/strategy.md", "w", encoding="utf-8") as f:
    f.write(strategy_doc)

# ── Distractor files ──────────────────────────────────────────────────────────
with open(f"{BASE}/logs/system.log", "w") as f:
    f.write("2024-01-01 00:00:00 [INFO] System started\n")
    f.write("2024-01-01 00:01:00 [INFO] Config loaded\n")

with open(f"{BASE}/archive/2023/ssq_archive_2023.csv", "w") as f:
    f.write("issue,date,red1,red2,red3,red4,red5,red6,blue\n")
    f.write("2023001,2023-01-03,5,12,17,22,28,33,9\n")

with open(f"{BASE}/archive/2022/ssq_archive_2022.csv", "w") as f:
    f.write("issue,date,red1,red2,red3,red4,red5,red6,blue\n")
    f.write("2022001,2022-01-04,3,8,14,19,25,31,6\n")

with open(f"{BASE}/tmp/temp_analysis.txt", "w") as f:
    f.write("临时分析文件 - 请勿修改\n")
    f.write("red_hot_candidates: 7,13,15,21,25,30\n")

with open(f"{BASE}/tmp/draft_config.json", "w") as f:
    json.dump({"strategy": "balanced", "note": "draft only"}, f)

with open(f"{BASE}/.gitignore", "w") as f:
    f.write("outputs/\nbacktests/\nlogs/\n*.pyc\n__pycache__/\n")

with open(f"{BASE}/docs/changelog.md", "w") as f:
    f.write("# Changelog\n\n## v2.0.0\n- 动态冷热周期\n- 多策略支持\n## v1.0.0\n- 基础选号\n")

# Mark that scripts need execution permissions
for script in ["update_ssq_history.py", "generate_ssq.py", "backtest_ssq.py"]:
    path = f"{BASE}/scripts/{script}"
    assert os.path.exists(path), f"Script missing: {path}"

print("[gen_inputs] Workspace initialized successfully.")
print(f"[gen_inputs] History rows: 3420")
print(f"[gen_inputs] Config strategy: stable (agent must change to aggressive)")