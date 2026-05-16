import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "health_records/2023/q1",
    "health_records/2023/q2",
    "health_records/2024/bloodwork",
    "health_records/2024/imaging",
    "device_exports/apple_health/weekly",
    "device_exports/apple_health/monthly",
    "supplements/current",
    "supplements/discontinued",
    "notes/doctor_visits",
    "notes/symptoms_log",
    "lifestyle/diet_logs",
    "lifestyle/exercise_logs",
    "reports/archive",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "health_records/2023/q1/checkup_notes.txt": "Annual checkup March 2023. No significant findings. Follow up in 12 months.",
    "health_records/2023/q2/allergy_test.txt": "Dust mite allergy confirmed. Cat dander mild reaction. Pollen moderate.",
    "health_records/2024/imaging/chest_xray_2024.txt": "Chest X-ray report: Lungs clear, no infiltrates. Heart size normal. No acute findings.",
    "device_exports/apple_health/monthly/2024_jan_summary.csv": "metric,value\nresting_hr,62\nsteps_avg,7200\nactive_calories,380",
    "device_exports/apple_health/monthly/2024_feb_summary.csv": "metric,value\nresting_hr,64\nsteps_avg,6800\nactive_calories,350",
    "supplements/discontinued/old_stack_2023.txt": "Stopped taking: Ashwagandha 600mg (caused vivid dreams), ZMA (no noticeable effect). Discontinued Jan 2024.",
    "notes/doctor_visits/gastro_consult_2023.txt": "Gastroenterologist visit Oct 2023. IBS-D diagnosis. Advised low-FODMAP diet trial. No red flags.",
    "notes/symptoms_log/random_headaches_q3_2023.txt": "Sporadic tension headaches noted July-Sept 2023. Linked to screen time. Resolved with breaks.",
    "lifestyle/diet_logs/typical_day.txt": "Breakfast: eggs + avocado. Lunch: salad with chicken. Dinner: varies. Coffee: 2 cups/day before noon. Alcohol: 1-2 drinks/week.",
    "lifestyle/exercise_logs/2024_training_plan.txt": "Goal: maintain aerobic base. 3x strength/week, 2x zone 2 cardio/week. No current injuries.",
    "reports/archive/2022_annual_summary.txt": "2022 health summary. Overall good health. Vitamin D deficiency noted (18 ng/mL). Started D3+K2 supplementation.",
    "health_records/2024/bloodwork/interpretation_notes.txt": "Patient self-notes: ferritin was low last year, now normalized after iron-rich diet changes.",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content, encoding="utf-8")

# ── Primary input: multi-source health data dump ────────────────────────────
# This is the main file the agent must process.
# It contains Apple Watch data, blood test results, supplements, and symptoms.
# Deliberately messy / unstructured to require careful parsing.

health_data_dump = """
=== 用户健康数据包 / User Health Data Package ===
生成日期: 2025年1月15日 (小寒节气后第8天)
用户基本信息: 男性，34岁，互联网产品经理，北京，长期久坐，出差频繁

--- Apple Watch / HealthKit 数据（本周：2025-01-06 至 2025-01-12）---
静息心率:
  周一: 68 bpm
  周二: 71 bpm
  周三: 69 bpm
  周四: 73 bpm
  周五: 72 bpm
  周六: 67 bpm
  周日: 66 bpm
  本周均值: 69.4 bpm

HRV (RMSSD, ms):
  周一: 38
  周二: 31
  周三: 35
  周四: 27  ← 最低值
  周五: 29
  周六: 41
  周日: 44
  本周均值: 35.0 ms

睡眠数据（Apple Watch 检测）：
  周一夜: 总睡眠 6h12m | 深睡 52min (14.0%) | REM 78min | 核心睡眠 172min | 觉醒 3次
  周二夜: 总睡眠 5h48m | 深睡 44min (12.6%) | REM 61min | 核心睡眠 159min | 觉醒 5次
  周三夜: 总睡眠 6h35m | 深睡 61min (15.5%) | REM 82min | 核心睡眠 189min | 觉醒 2次
  周四夜: 总睡眠 5h22m | 深睡 38min (11.8%) | REM 55min | 核心睡眠 147min | 觉醒 6次 ← 最差
  周五夜: 总睡眠 6h04m | 深睡 49min (13.5%) | REM 71min | 核心睡眠 164min | 觉醒 4次
  周六夜: 总睡眠 7h38m | 深睡 74min (16.2%) | REM 98min | 核心睡眠 214min | 觉醒 1次
  周日夜: 总睡眠 7h15m | 深睡 68min (15.6%) | REM 91min | 核心睡眠 196min | 觉醒 2次
  本周平均总睡眠: 6h24m

步数/活动：
  日均步数: 6,340步
  日均活动消耗: 412 kcal
  本周运动记录: 周二力量训练55min, 周五力量训练50min, 周六慢跑40min
  久坐: 大多数工作日久坐超过6小时

血氧 (SpO2): 均值 96.8%，最低95%（周四夜间）

VO2 Max (Apple Watch 估算): 42 mL/kg/min

呼吸频率 (睡眠中): 16.2 次/分 (平均)

--- 近期体检报告（2024年12月，一个月前）---
血常规:
  血红蛋白: 148 g/L (参考值 130-175) — 正常
  白细胞: 6.2 × 10^9/L (参考值 4-10) — 正常
  血小板: 221 × 10^9/L — 正常

生化指标:
  空腹血糖: 5.4 mmol/L (参考值 3.9-6.1) — 正常偏高区
  总胆固醇: 5.1 mmol/L (参考值 <5.2) — 临界
  LDL: 3.2 mmol/L (参考值 <3.4) — 临界
  HDL: 1.3 mmol/L (参考值 >1.0) — 正常
  甘油三酯: 1.8 mmol/L (参考值 <1.7) — 轻度偏高
  ALT: 28 U/L — 正常
  AST: 22 U/L — 正常
  肌酐: 82 μmol/L — 正常
  尿酸: 412 μmol/L (参考值 <420) — 正常高限

炎症指标:
  超敏C反应蛋白 (hsCRP): 2.8 mg/L (参考值 <1.0 为低风险；1-3 中等风险；>3 高风险) — 中等风险

甲状腺功能:
  TSH: 2.1 mIU/L — 正常
  FT4: 14.3 pmol/L — 正常

维生素D: 32 ng/mL (参考值 30-100) — 正常低限（刚过临界）

铁蛋白: 68 ng/mL — 正常

--- 当前补剂清单 ---
1. Omega-3 鱼油 (EPA 600mg + DHA 400mg) — 每日1次，随餐，已服用8个月
2. 维生素D3 2000 IU + K2 100mcg — 每日1次，早晨，已服用14个月
3. 镁 (甘氨酸镁) 200mg — 每晚睡前，已服用3个月，主观感受：入睡改善但仍觉早醒
4. 肌酸一水化合物 5g — 每日运动后，已服用6周
5. 乳清蛋白粉 (每勺25g蛋白) — 运动后一勺，非运动日有时一勺，已服用2年
6. 维生素B群 (B12 500mcg + 完整B族) — 每日早晨，已服用2个月
7. 褪黑素 0.5mg — 最近两周开始，睡前30分钟，主观感受：入睡稍快，但凌晨仍会醒

--- 近期主观症状与状态描述 ---
- 近2周明显感到疲劳感加重，下午三四点容易犯困，即使睡够6.5小时也感觉没有恢复
- 工作压力：本月项目冲刺期，连续11天工作，周末仅休息半天
- 情绪：容易烦躁，对小事容易发火，事后觉得自己反应过度
- 消化：近1周饭后腹胀明显，大便不成形，一日1-2次
- 口干：早晨起床明显口干，喝水后缓解
- 怕冷：手脚偏凉，办公室开空调后明显
- 皮肤：近期后背轻微出现小红疹（3-4颗），轻微瘙痒
- 出汗：运动时出汗正常，但工作紧张时有时手心微汗
- 头部：近1周有2次轻微颈后酸痛，与久坐相关
- 上周周四是状态最差的一天：睡眠最短，HRV最低，当天有重要产品评审会议

--- 既往重要健康背景 ---
- 2023年诊断IBS-D（肠易激综合征腹泻型），已改善但压力下易复发
- 2022年维生素D严重不足 (18 ng/mL)，现已纠正
- 有花粉/尘螨过敏史，春季明显，冬季轻微
- 无高血压、糖尿病、心脏病家族史
- 父亲有高尿酸病史
- 长期轻度睡眠不足史（近3年平均睡眠约6-6.5小时）

=== 数据包结束 ===
"""

input_file = workspace / "health_data_2025_jan.txt"
input_file.write_text(health_data_dump, encoding="utf-8")

# ── Additional contextual file: previous month's brief summary ───────────────
prev_summary = """
2024年12月健康简要记录:
- 12月睡眠相对较好，平均6.8小时
- HRV均值约42ms，较稳定
- 无明显不适症状
- 开始补充褪黑素0.5mg（12月底开始）
- 甘油三酯月末体检发现轻度偏高，医生建议注意饮食
- 情绪平稳，工作节奏正常
"""
(workspace / "notes/symptoms_log/dec_2024_summary.txt").write_text(prev_summary, encoding="utf-8")

# ── Placeholder for agent output (does NOT exist yet) ───────────────────────
# Agent must create: health_analysis_report.md

print("Workspace generated successfully.")
print(f"Primary input file: {input_file}")
print("Agent must create: health_analysis_report.md")