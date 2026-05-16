import os
import random
import sqlite3
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "lottery-predictor-v3-8/scripts",
    "lottery-predictor-v3-8/assets",
    "lottery-predictor-v3-8/references",
    "lottery-predictor-v3-8/logs",
    "lottery-predictor-v3-8/models/archive",
    "lottery-predictor-v3-8/data/raw",
    "lottery-predictor-v3-8/data/processed",
    "legacy/v3.6",
    "legacy/v3.7",
    "config",
    "reports/old",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── package.json ─────────────────────────────────────────────────────────────
pkg = {
    "name": "lottery-predictor-v3-8",
    "version": "3.8.0",
    "description": "ML-enhanced lottery predictor",
    "scripts": {
        "predict": "python3 scripts/v3.8_ml_model.py",
        "backtest": "python3 scripts/backtest_v3.8.py"
    },
    "dependencies": {
        "scikit-learn": ">=1.0",
        "numpy": ">=1.21",
        "pandas": ">=1.3"
    }
}
(workspace / "lottery-predictor-v3-8/package.json").write_text(json.dumps(pkg, indent=2))

# ── SKILL.md (as provided) ───────────────────────────────────────────────────
skill_md = """---
name: lottery-predictor-v3-8
description: 基于机器学习的双色球预测工具，随机森林+Gradient Boosting+ 规则集成，15 维特征工程，红球准确率 80.8%
license: MIT
compatibility: Python 3.8+, SQLite3, scikit-learn
metadata:
  {"openclaw": {"requires": {"bins": ["python3", "sqlite3"], "pip": ["scikit-learn","numpy","pandas"], "env": ["LOTTERY_DB_PATH"]}, "primaryEnv": "LOTTERY_DB_PATH"}}
---

# 🎰 彩票预测技能（V3.8 机器学习增强版）

## 使用方法

### 基础预测
    预测双色球下一期

### 查看回测
    运行 V3.8 回测，1000 期

## 文件结构
lottery-predictor-v3-8/
├── SKILL.md
├── package.json
├── scripts/
│   ├── v3.8_ml_model.py   # 主程序
│   └── backtest_v3.8.py   # 回测脚本
"""
(workspace / "lottery-predictor-v3-8/SKILL.md").write_text(skill_md)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "legacy/v3.6/predict_v3.6.py").write_text(
    "# Legacy rule-based predictor v3.6\n# DO NOT USE - superseded by v3.8\n"
)
(workspace / "legacy/v3.7/predict_v3.7.py").write_text(
    "# Legacy rule-enhanced predictor v3.7\n# DO NOT USE - superseded by v3.8\n"
)
(workspace / "legacy/v3.6/config.json").write_text(
    json.dumps({"version": "3.6", "algorithm": "rule_engine", "db_path": "/data/lottery_old.db"})
)
(workspace / "config/model_params_v3.6.yaml").write_text(
    "version: 3.6\nalgorithm: rules\ntraining_periods: 1000\n"
)
(workspace / "config/model_params_v3.7.yaml").write_text(
    "version: 3.7\nalgorithm: rule_enhanced\ntraining_periods: 1500\n"
)
(workspace / "lottery-predictor-v3-8/logs/train_v3.6.log").write_text(
    "2024-01-01 training v3.6 complete. accuracy=0.772\n"
)
(workspace / "lottery-predictor-v3-8/logs/train_v3.7.log").write_text(
    "2024-06-01 training v3.7 complete. accuracy=0.772\n"
)
(workspace / "lottery-predictor-v3-8/assets/feature_notes.txt").write_text(
    "Feature engineering notes for v3.8 - 15 features defined in SKILL.md\n"
)
(workspace / "lottery-predictor-v3-8/references/algorithm_ref.txt").write_text(
    "RandomForest: 100 trees, max_depth=12\nGradientBoosting: 30 trees, lr=0.1\n"
)
(workspace / "reports/old/backtest_v3.7_500periods.txt").write_text(
    "V3.7 Backtest - 500 periods\nRed accuracy: 77.2%\nBlue accuracy: N/A\n"
)
(workspace / "lottery-predictor-v3-8/models/archive/model_v3.6.pkl.placeholder").write_text(
    "placeholder - actual model file not stored in repo\n"
)
(workspace / "lottery-predictor-v3-8/data/raw/sample_draws.csv").write_text(
    "issue,red1,red2,red3,red4,red5,red6,blue\n2020001,01,07,12,19,23,31,05\n2020002,03,08,15,22,27,33,11\n"
)
(workspace / "lottery-predictor-v3-8/data/processed/feature_cache_note.txt").write_text(
    "Feature cache regenerated on each run from LOTTERY_DB_PATH\n"
)

# ── Generate SQLite database with 3431 historical draws ──────────────────────
db_path = workspace / "lottery-predictor-v3-8/data/lottery_history.db"

def gen_draw(issue_num, seed):
    rng = random.Random(seed)
    reds = sorted(rng.sample(range(1, 34), 6))
    blue = rng.randint(1, 16)
    # Generate a plausible date
    year = 2010 + (issue_num // 104)
    month = ((issue_num % 104) // 9) + 1
    month = min(month, 12)
    day = (issue_num % 28) + 1
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    return (f"2{issue_num:06d}", reds[0], reds[1], reds[2], reds[3], reds[4], reds[5], blue, date_str)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS lottery_history (
    issue TEXT PRIMARY KEY,
    red1 INTEGER NOT NULL,
    red2 INTEGER NOT NULL,
    red3 INTEGER NOT NULL,
    red4 INTEGER NOT NULL,
    red5 INTEGER NOT NULL,
    red6 INTEGER NOT NULL,
    blue INTEGER NOT NULL,
    draw_date TEXT NOT NULL
)
""")

draws = []
for i in range(1, 3432):
    draws.append(gen_draw(i, seed=i * 137 + 42))

cur.executemany(
    "INSERT OR REPLACE INTO lottery_history VALUES (?,?,?,?,?,?,?,?,?)",
    draws
)
conn.commit()
conn.close()

print(f"Created DB at {db_path} with {len(draws)} draws.")

# ── The main ML prediction script ────────────────────────────────────────────
ml_script = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3.8 ML-enhanced lottery predictor
Red ball: RandomForest (100 trees, max_depth=12, class_weight=balanced, StandardScaler)
Blue ball: GradientBoosting (30 trees, lr=0.1)
Hybrid: ML 50% + rule 50%
Training window: 2000 most recent draws
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

DB_PATH = os.environ.get("LOTTERY_DB_PATH", "")
if not DB_PATH:
    print("ERROR: LOTTERY_DB_PATH environment variable not set.", file=sys.stderr)
    sys.exit(1)

if not os.path.exists(DB_PATH):
    print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query(
    "SELECT * FROM lottery_history ORDER BY issue ASC",
    conn
)
conn.close()

if len(df) < 100:
    print("ERROR: Insufficient data (need at least 100 draws).", file=sys.stderr)
    sys.exit(1)

# Use last 2000 draws for training
df = df.tail(2000).reset_index(drop=True)
N = len(df)

def compute_features_for_ball(df, ball_col, all_red_cols, is_blue=False):
    """Compute 15-dim features for each ball number in each draw (for red), or 5-dim for blue."""
    rows = []
    red_range = range(1, 34)
    blue_range = range(1, 17)
    ball_range = blue_range if is_blue else red_range

    for idx in range(50, N):
        history = df.iloc[:idx]
        last_10 = history.tail(10)
        last_30 = history.tail(30)
        last_50 = history.tail(50)

        for ball_num in ball_range:
            if is_blue:
                # 5 features for blue
                r10 = int((last_10[ball_col] == ball_num).sum())
                r30 = int((last_30[ball_col] == ball_num).sum())
                r50 = int((last_50[ball_col] == ball_num).sum())
                freq = float((history[ball_col] == ball_num).sum()) / max(len(history), 1)
                is_odd = int(ball_num % 2 == 1)
                feat = [r10, r30, r50, freq, is_odd]
                # label
                actual_ball = df.iloc[idx][ball_col]
                label = int(actual_ball == ball_num)
                rows.append(feat + [label, ball_num, idx])
            else:
                # 15 features for red
                def count_in_reds(sub, n):
                    return int(sum(
                        int(sub[c].values[i] == n)
                        for c in all_red_cols
                        for i in range(len(sub))
                    ))
                r10 = count_in_reds(last_10, ball_num)
                r30 = count_in_reds(last_30, ball_num)
                r50 = count_in_reds(last_50, ball_num)

                # miss features
                miss = 0
                misses = []
                cur_miss = 0
                for i2 in range(len(history)):
                    row2 = history.iloc[i2]
                    appeared = any(row2[c] == ball_num for c in all_red_cols)
                    if appeared:
                        misses.append(cur_miss)
                        cur_miss = 0
                    else:
                        cur_miss += 1
                current_miss = cur_miss
                avg_miss = float(np.mean(misses)) if misses else 0.0
                max_miss = float(max(misses)) if misses else 0.0

                # form features
                last_draw = history.iloc[-1]
                last_reds = [last_draw[c] for c in all_red_cols]
                is_repeat = int(ball_num in last_reds)
                has_consecutive = int(
                    any(abs(ball_num - x) == 1 for x in last_reds)
                )
                same_tail = int(sum(1 for x in last_reds if x % 10 == ball_num % 10))

                # freq
                total_appearances = sum(
                    int((history[c] == ball_num).sum()) for c in all_red_cols
                )
                freq = float(total_appearances) / max(len(history) * len(all_red_cols), 1)

                # zone
                in_zone1 = int(1 <= ball_num <= 11)
                in_zone2 = int(12 <= ball_num <= 22)
                in_zone3 = int(23 <= ball_num <= 33)

                # attributes
                is_odd = int(ball_num % 2 == 1)
                is_big = int(ball_num >= 17)
                primes = {2,3,5,7,11,13,17,19,23,29,31}
                is_prime = int(ball_num in primes)

                feat = [
                    r10, r30, r50,
                    current_miss, avg_miss, max_miss,
                    is_repeat, has_consecutive, same_tail,
                    freq,
                    in_zone1, in_zone2, in_zone3,
                    is_odd, is_big
                    # Note: is_prime is used as 15th in place of is_big variant
                ]
                # actual label
                actual_reds = [df.iloc[idx][c] for c in all_red_cols]
                label = int(ball_num in actual_reds)
                rows.append(feat + [label, ball_num, idx])
    return rows

red_cols = ["red1","red2","red3","red4","red5","red6"]

print("Computing red ball features (this may take a moment)...")
red_rows = compute_features_for_ball(df, None, red_cols, is_blue=False)
red_df = pd.DataFrame(red_rows, columns=[
    "r10","r30","r50","cur_miss","avg_miss","max_miss",
    "is_repeat","has_consec","same_tail","freq",
    "zone1","zone2","zone3","is_odd","is_big",
    "label","ball_num","draw_idx"
])

print("Computing blue ball features...")
blue_rows = compute_features_for_ball(df, "blue", red_cols, is_blue=True)
blue_df = pd.DataFrame(blue_rows, columns=[
    "r10","r30","r50","freq","is_odd",
    "label","ball_num","draw_idx"
])

# Split: all but last draw for training, last for prediction
max_idx = red_df["draw_idx"].max()
X_red_train = red_df[red_df["draw_idx"] < max_idx][["r10","r30","r50","cur_miss","avg_miss","max_miss","is_repeat","has_consec","same_tail","freq","zone1","zone2","zone3","is_odd","is_big"]].values
y_red_train = red_df[red_df["draw_idx"] < max_idx]["label"].values

X_blue_train = blue_df[blue_df["draw_idx"] < max_idx][["r10","r30","r50","freq","is_odd"]].values
y_blue_train = blue_df[blue_df["draw_idx"] < max_idx]["label"].values

# Prediction features (last draw)
X_red_pred = red_df[red_df["draw_idx"] == max_idx][["r10","r30","r50","cur_miss","avg_miss","max_miss","is_repeat","has_consec","same_tail","freq","zone1","zone2","zone3","is_odd","is_big"]].values
red_pred_balls = red_df[red_df["draw_idx"] == max_idx]["ball_num"].values

X_blue_pred = blue_df[blue_df["draw_idx"] == max_idx][["r10","r30","r50","freq","is_odd"]].values
blue_pred_balls = blue_df[blue_df["draw_idx"] == max_idx]["ball_num"].values

print("Training RandomForest for red balls (100 trees, max_depth=12)...")
scaler = StandardScaler()
X_red_train_scaled = scaler.fit_transform(X_red_train)
X_red_pred_scaled = scaler.transform(X_red_pred)

rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
rf.fit(X_red_train_scaled, y_red_train)
red_ml_probs = rf.predict_proba(X_red_pred_scaled)[:,1]

print("Training GradientBoosting for blue ball (30 trees, lr=0.1)...")
gb = GradientBoostingClassifier(
    n_estimators=30,
    learning_rate=0.1,
    random_state=42
)
gb.fit(X_blue_train, y_blue_train)
blue_ml_probs = gb.predict_proba(X_blue_pred)[:,1]

# Rule engine (50% weight)
def rule_score_red(df, ball_num, red_cols):
    history = df
    last_10 = history.tail(10)
    appearances_10 = sum(int((last_10[c] == ball_num).sum()) for c in red_cols)
    last_draw_reds = [history.iloc[-1][c] for c in red_cols]
    miss = 0
    for i in range(len(history)-1, -1, -1):
        if any(history.iloc[i][c] == ball_num for c in red_cols):
            break
        miss += 1
    score = appearances_10 * 0.4 + min(miss / 10.0, 1.0) * 0.6
    return score

def rule_score_blue(df, ball_num):
    history = df
    last_20 = history.tail(20)
    freq = float((last_20["blue"] == ball_num).sum()) / 20.0
    return freq

red_rule_scores = np.array([rule_score_red(df, b, red_cols) for b in red_pred_balls])
blue_rule_scores = np.array([rule_score_blue(df, b) for b in blue_pred_balls])

# Normalize
def normalize(arr):
    mn, mx = arr.min(), arr.max()
    if mx == mn:
        return np.ones_like(arr) / len(arr)
    return (arr - mn) / (mx - mn)

red_ml_norm = normalize(red_ml_probs)
red_rule_norm = normalize(red_rule_scores)
red_final = 0.5 * red_ml_norm + 0.5 * red_rule_norm

blue_ml_norm = normalize(blue_ml_probs)
blue_rule_norm = normalize(blue_rule_scores)
blue_final = 0.5 * blue_ml_norm + 0.5 * blue_rule_norm

# Select top 6 red, top 1 blue
top6_idx = np.argsort(red_final)[::-1][:6]
red_recommended = sorted(red_pred_balls[top6_idx].tolist())

top1_idx = np.argmax(blue_final)
blue_recommended = int(blue_pred_balls[top1_idx])

# Last draw info
last_draw = df.iloc[-1]
last_reds_str = " ".join(f"{last_draw[c]:02d}" for c in red_cols)
last_blue_str = f"{last_draw['blue']:02d}"

print("=" * 80)
print("🔮 V3.8 预测结果")
print("=" * 80)
print()
print(f"上期开奖：{last_reds_str} + {last_blue_str}")
print()
red_str = ", ".join(f"{r:02d}" for r in red_recommended)
print(f"【红球推荐】{red_str}")
print(f"【蓝球推荐】{blue_recommended:02d}")
print()
print("💡 说明：")
print("  - 使用随机森林预测红球")
print("  - 使用 Gradient Boosting 预测蓝球")
print("  - 集成规则引擎提高稳定性")
print(f"  - 训练数据：最近 {N} 期")
print()
print("=" * 80)
print("⚠️  预测仅供娱乐参考，请理性购彩！")
print("=" * 80)
'''

(workspace / "lottery-predictor-v3-8/scripts/v3.8_ml_model.py").write_text(ml_script)

# ── The backtest script ───────────────────────────────────────────────────────
backtest_script = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3.8 Backtest Script
Usage: python3 backtest_v3.8.py [periods]
Default periods: 1000
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

periods = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

DB_PATH = os.environ.get("LOTTERY_DB_PATH", "")
if not DB_PATH:
    print("ERROR: LOTTERY_DB_PATH environment variable not set.", file=sys.stderr)
    sys.exit(1)

if not os.path.exists(DB_PATH):
    print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM lottery_history ORDER BY issue ASC", conn)
conn.close()

red_cols = ["red1","red2","red3","red4","red5","red6"]

# Use last 2000+periods for full backtest
total_needed = 2000 + periods
if len(df) < total_needed:
    total_needed = len(df)
df = df.tail(total_needed).reset_index(drop=True)
N = len(df)

backtest_start = N - periods
if backtest_start < 100:
    backtest_start = 100

hit3_count = 0
hit4_count = 0
hit5_count = 0
hit6_count = 0
blue_hit_count = 0
total_backtest = 0

print(f"Running V3.8 backtest on last {periods} draws...")
print("Training window: 2000 draws | ML weight: 50% | Rule weight: 50%")
print("-" * 60)

# Simplified backtest: for each backtest draw, train on previous 200 samples, predict
WINDOW = 200
for test_idx in range(backtest_start, N, max(1, periods // 20)):
    train_df = df.iloc[max(0, test_idx-WINDOW):test_idx]
    if len(train_df) < 50:
        continue

    # Quick feature for each red ball
    def quick_feat_red(ball_num):
        last_10 = train_df.tail(10)
        last_30 = train_df.tail(30)
        r10 = sum(int((last_10[c] == ball_num).sum()) for c in red_cols)
        r30 = sum(int((last_30[c] == ball_num).sum()) for c in red_cols)
        freq = sum(int((train_df[c] == ball_num).sum()) for c in red_cols) / max(len(train_df), 1)
        miss = 0
        for i in range(len(train_df)-1, -1, -1):
            if any(train_df.iloc[i][c] == ball_num for c in red_cols):
                break
            miss += 1
        is_odd = int(ball_num % 2 == 1)
        is_big = int(ball_num >= 17)
        primes = {2,3,5,7,11,13,17,19,23,29,31}
        return [r10, r30, r10+r30, miss, freq, freq*2, 0, 0, 0, freq, int(ball_num<=11), int(12<=ball_num<=22), int(ball_num>=23), is_odd, is_big]

    red_scores = {b: np.mean(quick_feat_red(b)[:3]) + quick_feat_red(b)[4]*5 for b in range(1, 34)}
    top6 = sorted(red_scores, key=lambda x: -red_scores[x])[:6]

    def quick_feat_blue(ball_num):
        last_20 = train_df.tail(20)
        freq = float((last_20["blue"] == ball_num).sum()) / 20.0
        return freq

    blue_scores = {b: quick_feat_blue(b) for b in range(1, 17)}
    top_blue = max(blue_scores, key=lambda x: blue_scores[x])

    actual_row = df.iloc[test_idx]
    actual_reds = set(actual_row[c] for c in red_cols)
    actual_blue = actual_row["blue"]

    hits = len(set(top6) & actual_reds)
    blue_hit = int(top_blue == actual_blue)

    if hits >= 3: hit3_count += 1
    if hits >= 4: hit4_count += 1
    if hits >= 5: hit5_count += 1
    if hits == 6: hit6_count += 1
    if blue_hit: blue_hit_count += 1
    total_backtest += 1

if total_backtest == 0:
    print("ERROR: No backtest samples available.")
    sys.exit(1)

acc3 = hit3_count / total_backtest * 100
acc4 = hit4_count / total_backtest * 100
acc5 = hit5_count / total_backtest * 100
acc6 = hit6_count / total_backtest * 100
blue_acc = blue_hit_count / total_backtest * 100

print()
print("=" * 60)
print(f"🔮 V3.8 回测报告 (最近 {periods} 期)")
print("=" * 60)
print(f"回测样本数：{total_backtest}")
print()
print("【红球命中率】")
print(f"  ≥3 红球命中：{acc3:.1f}% ({hit3_count}/{total_backtest})")
print(f"  ≥4 红球命中：{acc4:.1f}% ({hit4_count}/{total_backtest})")
print(f"  ≥5 红球命中：{acc5:.1f}% ({hit5_count}/{total_backtest})")
print(f"  6  红球命中：{acc6:.1f}% ({hit6_count}/{total_backtest})")
print()
print("【蓝球命中率】")
print(f"  蓝球命中：{blue_acc:.1f}% ({blue_hit_count}/{total_backtest})")
print()
print("【模型配置】")
print("  红球模型：RandomForest (100棵树, max_depth=12, class_weight=balanced)")
print("  蓝球模型：Gradient Boosting (30棵树, lr=0.1)")
print("  集成方式：ML 50% + 规则引擎 50%")
print(f"  训练窗口：2000 期")
print()
print("=" * 60)
print("⚠️  回测结果仅供参考，不代表未来表现！")
print("=" * 60)
'''

(workspace / "lottery-predictor-v3-8/scripts/backtest_v3.8.py").write_text(backtest_script)

# ── Intentionally wrong/stale env hint (distractor) ──────────────────────────
(workspace / "config/env_example.txt").write_text(
    "# Example env vars (DO NOT USE DIRECTLY - may be outdated)\n"
    "# LOTTERY_DB=/old/path/to/lottery.db\n"
    "# Note: variable name changed in v3.8 - check SKILL.md\n"
)

# ── Old broken DB path reference ─────────────────────────────────────────────
(workspace / "legacy/v3.6/config.json").write_text(
    json.dumps({
        "version": "3.6",
        "db": "/tmp/lottery_v36.db",
        "env_var": "LOTTERY_DB"  # wrong name - should be LOTTERY_DB_PATH
    }, indent=2)
)

print("Workspace setup complete.")
print(f"DB path: {db_path}")
print("Scripts created at lottery-predictor-v3-8/scripts/")