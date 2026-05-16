import os
import json
import zipfile
import random
import struct
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "reports/drafts",
    "reports/final",
    "config",
    "logs",
    "notebooks",
    "docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "data/archive/old_export_2021.txt": "Legacy export stub - do not use",
    "data/processed/summary_2022.csv": "date,steps,calories\n2022-01-01,8000,320\n2022-01-02,7500,305\n",
    "config/user_settings.json": json.dumps({"units": "metric", "timezone": "Asia/Shanghai", "locale": "zh-CN"}),
    "config/thresholds_old.yaml": "rhr_max: 85\nhrv_min: 20\nsteps_daily: 8000\n",
    "logs/parse_errors.log": "2024-01-15 03:12:44 WARNING: Skipped malformed record at line 48291\n2024-01-16 07:00:01 INFO: Parse complete\n",
    "notebooks/eda_scratch.py": "# scratch pad\nimport json\ndata = json.load(open('../data/processed/summary_2022.csv'))\n",
    "docs/reference_rhr_table.txt": "This file intentionally left incomplete. See SKILL.md for authoritative tables.\n",
    "reports/drafts/template_v1.html": "<html><body><h1>Draft Report</h1><p>TODO: replace with generated content</p></body></html>",
    "data/raw/README.txt": "Place export.zip in this directory before running analysis pipeline.",
    "config/pipeline_config.json": json.dumps({"parse_chunk_size": 524288, "output_dir": "/tmp", "report_name": "health_report.html"}),
    "logs/previous_run.log": "2024-03-10 10:05:00 INFO: parse_health.py started\n2024-03-10 10:05:45 INFO: parse_health.py complete. Records: 1482930\n",
    "reports/final/.gitkeep": "",
}
for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── parse_health.py ─────────────────────────────────────────────────────────
parse_script = r'''#!/usr/bin/env python3
"""
Streaming Apple Health export.zip parser.
Usage: python3 parse_health.py <export.zip> <output_chart_data.json>
"""
import sys, zipfile, json, re, statistics
from xml.etree.ElementTree import iterparse
from collections import defaultdict
from datetime import datetime

def parse(zip_path, out_path):
    monthly = defaultdict(lambda: defaultdict(list))

    with zipfile.ZipFile(zip_path, 'r') as zf:
        xml_names = [n for n in zf.namelist() if n.endswith('.xml') and 'export' in n.lower()]
        if not xml_names:
            xml_names = [n for n in zf.namelist() if n.endswith('.xml')]
        if not xml_names:
            print("ERROR: No XML found in zip", file=sys.stderr)
            sys.exit(1)
        xml_name = xml_names[0]
        with zf.open(xml_name) as f:
            context = iterparse(f, events=('end',))
            for event, elem in context:
                if elem.tag != 'Record':
                    elem.clear()
                    continue
                rtype = elem.get('type','')
                val   = elem.get('value','')
                sdate = elem.get('startDate','')
                src   = elem.get('sourceName','')
                try:
                    dt = datetime.fromisoformat(sdate[:10])
                    ym = dt.strftime('%Y-%m')
                except Exception:
                    elem.clear()
                    continue

                try:
                    fval = float(val)
                except Exception:
                    elem.clear()
                    continue

                if 'HeartRate' in rtype and 'Resting' not in rtype and 'HRV' not in rtype:
                    monthly['rhr'][ym].append(fval)
                elif 'RestingHeartRate' in rtype:
                    monthly['rhr'][ym].append(fval)
                elif 'HeartRateVariabilitySDNN' in rtype:
                    monthly['hrv'][ym].append((fval, src))
                elif 'VO2Max' in rtype:
                    monthly['vo2max'][ym].append(fval)
                elif 'StepCount' in rtype:
                    monthly['steps'][ym].append(fval)
                elif 'OxygenSaturation' in rtype:
                    monthly['spo2'][ym].append(fval)
                elif 'BodyMass' in rtype:
                    monthly['weight'][ym].append(fval)
                elif 'SleepAnalysis' in rtype:
                    monthly['sleep'][ym].append(val)

                elem.clear()

    result = {}

    # RHR monthly median
    rhr_series = {}
    for ym, vals in sorted(monthly['rhr'].items()):
        if vals:
            rhr_series[ym] = round(statistics.median(vals), 1)
    result['rhr'] = rhr_series

    # HRV monthly median, segment by device era
    hrv_series = {}
    for ym, pairs in sorted(monthly['hrv'].items()):
        vals = [v for v, _ in pairs]
        if vals:
            hrv_series[ym] = round(statistics.median(vals), 1)
    result['hrv'] = hrv_series

    # VO2Max monthly last
    vo2_series = {}
    for ym, vals in sorted(monthly['vo2max'].items()):
        if vals:
            vo2_series[ym] = round(vals[-1], 1)
    result['vo2max'] = vo2_series

    # Steps monthly sum
    steps_series = {}
    for ym, vals in sorted(monthly['steps'].items()):
        steps_series[ym] = int(sum(vals))
    result['steps'] = steps_series

    # SpO2 monthly median
    spo2_series = {}
    for ym, vals in sorted(monthly['spo2'].items()):
        if vals:
            spo2_series[ym] = round(statistics.median(vals), 1)
    result['spo2'] = spo2_series

    # Weight monthly last (raw unit from HealthKit, typically lb)
    weight_series = {}
    for ym, vals in sorted(monthly['weight'].items()):
        if vals:
            weight_series[ym] = round(vals[-1], 1)
    result['weight'] = weight_series

    # Sleep stage summary (simplified)
    sleep_series = {}
    for ym, stages in sorted(monthly['sleep'].items()):
        total = len(stages)
        deep = stages.count('HKCategoryValueSleepAnalysisAsleepDeep')
        rem  = stages.count('HKCategoryValueSleepAnalysisAsleepREM')
        core = stages.count('HKCategoryValueSleepAnalysisAsleepCore')
        awake= stages.count('HKCategoryValueSleepAnalysisAwake')
        sleep_series[ym] = {
            'total': total, 'deep': deep, 'rem': rem,
            'core': core, 'awake': awake,
            'deep_pct': round(deep/total*100,1) if total else 0,
            'rem_pct':  round(rem/total*100,1)  if total else 0,
        }
    result['sleep'] = sleep_series

    with open(out_path, 'w', encoding='utf-8') as fout:
        json.dump(result, fout, ensure_ascii=False, indent=2)

    print(f"[parse_health] Done. Output: {out_path}")
    months = max(len(rhr_series), len(hrv_series), len(vo2_series), 1)
    print(f"[parse_health] Months parsed: {months}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: parse_health.py <export.zip> <output.json>", file=sys.stderr)
        sys.exit(1)
    parse(sys.argv[1], sys.argv[2])
'''

# ── generate_report.py ──────────────────────────────────────────────────────
generate_script = r'''#!/usr/bin/env python3
"""
Generate personalised HTML health report.
Usage:
  python3 generate_report.py <chart_data.json> <output.html>
    --gender   <male|female|other>
    --age      <int>
    --height   <cm>
    --weight-unit <lb|kg>
    --conditions  <comma-separated, e.g. "hyperthyroidism,hypertension">
    --activity  <sedentary|light|active|athlete>
    --verdict  "<overall assessment text>"
"""
import sys, json, argparse, statistics
from pathlib import Path

WEIGHT_CONV = {'lb': 0.4536, 'kg': 1.0}

def build_reference(gender: str, age: int, activity: str, conditions: list) -> dict:
    ref = {}
    # RHR reference by gender+age bracket
    rhr_table = {
        ('female', '18-25'): (54, 60, 73, 82),
        ('female', '26-35'): (55, 61, 74, 83),
        ('female', '36-45'): (56, 62, 75, 84),
        ('male',   '18-25'): (49, 55, 68, 77),
        ('male',   '26-35'): (50, 56, 69, 78),
        ('male',   '36-45'): (51, 57, 70, 79),
    }
    g = gender if gender in ('male','female') else 'female'
    if age <= 25:   ab = '18-25'
    elif age <= 35: ab = '26-35'
    else:           ab = '36-45'
    key = (g, ab)
    rhr_ref = rhr_table.get(key, (55, 61, 74, 83))
    ref['rhr_excellent'] = rhr_ref[0]
    ref['rhr_good']      = rhr_ref[1]
    ref['rhr_normal']    = rhr_ref[2]
    ref['rhr_high']      = rhr_ref[3]

    # Conditions adjustment
    ref['conditions'] = conditions
    if 'hyperthyroidism' in conditions or 'hypothyroidism' in conditions:
        ref['thyroid_note'] = True
    if 'hypertension' in conditions:
        ref['rhr_target_strict'] = 70  # stricter target
    if 'anemia' in conditions:
        ref['anemia_note'] = True
    if 'arrhythmia' in conditions:
        ref['hrv_unreliable'] = True

    # HRV reference by age
    if age <= 30:
        ref['hrv_low'] = 25; ref['hrv_high'] = 50
    elif age <= 40:
        ref['hrv_low'] = 20; ref['hrv_high'] = 45
    else:
        ref['hrv_low'] = 15; ref['hrv_high'] = 40

    # VO2Max reference
    vo2_table = {
        ('female','20-29'): (29, 34, 43, 48),
        ('female','30-39'): (28, 33, 41, 46),
        ('male',  '20-29'): (38, 43, 51, 56),
        ('male',  '30-39'): (35, 41, 49, 53),
    }
    if age <= 29:   vab = '20-29'
    elif age <= 39: vab = '30-39'
    else:           vab = '30-39'
    vkey = (g, vab)
    vo2_ref = vo2_table.get(vkey, (28, 33, 41, 46))
    ref['vo2_poor']      = vo2_ref[0]
    ref['vo2_fair']      = vo2_ref[1]
    ref['vo2_good']      = vo2_ref[2]
    ref['vo2_excellent'] = vo2_ref[3]

    # Steps target by activity
    steps_target = {'sedentary': 6000, 'light': 8000, 'active': 10000, 'athlete': 12000}
    ref['steps_target'] = steps_target.get(activity, 8000)

    return ref


def classify_rhr(median_rhr, ref):
    if median_rhr < ref['rhr_excellent']:
        return '优秀'
    elif median_rhr <= ref['rhr_good']:
        return '良好'
    elif median_rhr <= ref['rhr_normal']:
        return '正常'
    elif median_rhr <= ref['rhr_high']:
        return '偏高'
    else:
        return '过高'


def classify_vo2(vo2, ref):
    if vo2 < ref['vo2_poor']:
        return '差'
    elif vo2 < ref['vo2_fair']:
        return '一般'
    elif vo2 < ref['vo2_good']:
        return '良好'
    elif vo2 < ref['vo2_excellent']:
        return '优秀'
    else:
        return '精英'


def compute_bmi(weight_vals, weight_unit, height_cm):
    if not weight_vals:
        return None
    raw_w = list(weight_vals.values())[-1]
    kg = raw_w * WEIGHT_CONV.get(weight_unit, 1.0)
    h_m = height_cm / 100.0
    return round(kg / (h_m * h_m), 1)


def generate_html(data, ref, args, verdict):
    months = sorted(set(
        list(data.get('rhr',{}).keys()) +
        list(data.get('hrv',{}).keys()) +
        list(data.get('vo2max',{}).keys())
    ))

    rhr_vals  = [data['rhr'].get(m)  for m in months]
    hrv_vals  = [data['hrv'].get(m)  for m in months]
    vo2_vals  = [data['vo2max'].get(m) for m in months]
    step_vals = [data['steps'].get(m,0) for m in months]
    spo2_vals = [data['spo2'].get(m)  for m in months]

    bmi = compute_bmi(data.get('weight',{}), args.weight_unit, args.height)
    bmi_str = f"{bmi}" if bmi else "N/A"

    valid_rhr = [v for v in rhr_vals if v is not None]
    rhr_median = round(statistics.median(valid_rhr),1) if valid_rhr else None
    rhr_class  = classify_rhr(rhr_median, ref) if rhr_median else "数据不足"

    valid_vo2 = [v for v in vo2_vals if v is not None]
    vo2_latest = valid_vo2[-1] if valid_vo2 else None
    vo2_class  = classify_vo2(vo2_latest, ref) if vo2_latest else "数据不足"

    valid_hrv = [v for v in hrv_vals if v is not None]
    hrv_median = round(statistics.median(valid_hrv),1) if valid_hrv else None

    thyroid_banner = ""
    if ref.get('thyroid_note'):
        thyroid_banner = "<div class='alert'>⚠️ 检测到甲状腺病史：RHR/HRV/VO₂Max 异常时请先排除甲状腺因素，建议结合治疗前后数据对比。</div>"

    strict_rhr_note = ""
    if ref.get('rhr_target_strict'):
        strict_rhr_note = f"<p>因存在高血压病史，RHR 目标更严格：&lt;{ref['rhr_target_strict']} bpm</p>"

    conditions_display = ", ".join(ref.get('conditions', [])) or "无"

    steps_target = ref['steps_target']

    hrv_status = "数据不足"
    if hrv_median is not None:
        if hrv_median < ref['hrv_low']:
            hrv_status = f"偏低（{hrv_median} ms，参考低值 {ref['hrv_low']} ms）—交感亢奋风险"
        elif hrv_median > ref['hrv_high']:
            hrv_status = f"偏高（{hrv_median} ms，参考高值 {ref['hrv_high']} ms）"
        else:
            hrv_status = f"正常（{hrv_median} ms）"

    def js_arr(lst):
        return "[" + ",".join("null" if v is None else str(v) for v in lst) + "]"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Apple Health 个性化分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  body{{font-family:sans-serif;margin:20px;background:#f9f9f9;}}
  .card{{background:#fff;border-radius:8px;padding:20px;margin:16px 0;box-shadow:0 1px 4px #0002;}}
  .alert{{background:#fff3cd;border-left:4px solid #f0ad4e;padding:10px 16px;margin:12px 0;border-radius:4px;}}
  h1{{color:#1d3557;}} h2{{color:#457b9d;}}
  table{{border-collapse:collapse;width:100%;}} td,th{{border:1px solid #ddd;padding:6px 10px;}}
  th{{background:#457b9d;color:#fff;}}
  .badge{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.85em;}}
  .good{{background:#d4edda;color:#155724;}} .warn{{background:#fff3cd;color:#856404;}}
  .bad{{background:#f8d7da;color:#721c24;}} .info{{background:#d1ecf1;color:#0c5460;}}
</style>
</head>
<body>
<h1>🍎 Apple Health 个性化分析报告</h1>
<div class="card">
  <h2>用户画像</h2>
  <table>
    <tr><th>性别</th><td>{args.gender}</td><th>年龄</th><td>{args.age}</td></tr>
    <tr><th>身高</th><td>{args.height} cm</td><th>BMI</th><td>{bmi_str}</td></tr>
    <tr><th>体重单位</th><td>{args.weight_unit}</td><th>运动习惯</th><td>{args.activity}</td></tr>
    <tr><th>已知病史</th><td colspan="3">{conditions_display}</td></tr>
  </table>
  {thyroid_banner}
  {strict_rhr_note}
</div>

<div class="card">
  <h2>综合评估</h2>
  <p>{verdict}</p>
  <table>
    <tr><th>指标</th><th>值</th><th>评级</th><th>参考范围</th></tr>
    <tr><td>静息心率 RHR</td><td>{rhr_median if rhr_median else 'N/A'} bpm</td>
        <td><span class="badge info">{rhr_class}</span></td>
        <td>优秀&lt;{ref['rhr_excellent']} 良好≤{ref['rhr_good']} 正常≤{ref['rhr_normal']} 偏高≤{ref['rhr_high']}</td></tr>
    <tr><td>HRV SDNN</td><td>{hrv_median if hrv_median else 'N/A'} ms</td>
        <td><span class="badge info">{hrv_status}</span></td>
        <td>低&lt;{ref['hrv_low']} 正常{ref['hrv_low']}-{ref['hrv_high']} 良好&gt;{ref['hrv_high']}</td></tr>
    <tr><td>VO₂Max</td><td>{vo2_latest if vo2_latest else 'N/A'}</td>
        <td><span class="badge info">{vo2_class}</span></td>
        <td>差&lt;{ref['vo2_poor']} 一般≥{ref['vo2_poor']} 良好≥{ref['vo2_fair']} 优秀≥{ref['vo2_good']} 精英≥{ref['vo2_excellent']}</td></tr>
    <tr><td>步数目标</td><td colspan="3">每日 {steps_target}+ 步（基于活动习惯: {args.activity}）</td></tr>
  </table>
</div>

<div class="card">
  <h2>趋势图表</h2>
  <canvas id="rhrChart" height="80"></canvas>
  <canvas id="hrvChart" height="80"></canvas>
  <canvas id="vo2Chart" height="80"></canvas>
  <canvas id="stepsChart" height="80"></canvas>
  <canvas id="spo2Chart" height="80"></canvas>
</div>

<script>
const months = {js_arr([f'"{m}"' for m in months]).replace('"null"','null')};
const labels = {json.dumps(months)};

new Chart(document.getElementById('rhrChart'), {{
  type:'line',
  data:{{ labels, datasets:[{{label:'静息心率 RHR (bpm)', data:{js_arr(rhr_vals)}, borderColor:'#e63946', fill:false}}] }},
  options:{{ plugins:{{title:{{display:true,text:'静息心率趋势'}}}} }}
}});
new Chart(document.getElementById('hrvChart'), {{
  type:'line',
  data:{{ labels, datasets:[{{label:'HRV SDNN (ms)', data:{js_arr(hrv_vals)}, borderColor:'#2a9d8f', fill:false}}] }},
  options:{{ plugins:{{title:{{display:true,text:'HRV 趋势'}}}} }}
}});
new Chart(document.getElementById('vo2Chart'), {{
  type:'line',
  data:{{ labels, datasets:[{{label:'VO₂Max', data:{js_arr(vo2_vals)}, borderColor:'#457b9d', fill:false}}] }},
  options:{{ plugins:{{title:{{display:true,text:'VO₂Max 趋势'}}}} }}
}});
new Chart(document.getElementById('stepsChart'), {{
  type:'bar',
  data:{{ labels, datasets:[{{label:'月步数', data:{js_arr(step_vals)}, backgroundColor:'#a8dadc'}}] }},
  options:{{ plugins:{{title:{{display:true,text:'月步数趋势'}}}} }}
}});
new Chart(document.getElementById('spo2Chart'), {{
  type:'line',
  data:{{ labels, datasets:[{{label:'血氧 SpO₂ (%)', data:{js_arr(spo2_vals)}, borderColor:'#f4a261', fill:false}}] }},
  options:{{ plugins:{{title:{{display:true,text:'血氧趋势'}}}} }}
}});
</script>

<div class="card">
  <h2>数据质量说明</h2>
  <ul>
    <li>体重原始单位：{args.weight_unit}（已自动换算至 kg 计算 BMI）</li>
    <li>步数：已按日汇总去重</li>
    <li>睡眠分期：Series 6+ 设备支持 Deep/REM/Core 分期</li>
    <li>分析时间跨度：{len(months)} 个月</li>
  </ul>
</div>
</body>
</html>"""
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('chart_data')
    ap.add_argument('output_html')
    ap.add_argument('--gender',      required=True)
    ap.add_argument('--age',         type=int, required=True)
    ap.add_argument('--height',      type=float, required=True)
    ap.add_argument('--weight-unit', required=True, dest='weight_unit')
    ap.add_argument('--conditions',  default='')
    ap.add_argument('--activity',    required=True)
    ap.add_argument('--verdict',     required=True)
    args = ap.parse_args()

    conds = [c.strip() for c in args.conditions.split(',') if c.strip()]
    ref   = build_reference(args.gender, args.age, args.activity, conds)

    with open(args.chart_data, 'r', encoding='utf-8') as f:
        data = json.load(f)

    html = generate_html(data, ref, args, args.verdict)

    with open(args.output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[generate_report] Report written: {args.output_html}")

if __name__ == '__main__':
    main()
'''

(workspace / "scripts" / "parse_health.py").write_text(parse_script)
(workspace / "scripts" / "generate_report.py").write_text(generate_script)

# ── Synthetic Apple Health XML ───────────────────────────────────────────────
def fmt_date(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S +0800")

records = []
base = datetime(2023, 1, 1)

rng = random.Random(42)

for day_offset in range(540):  # ~18 months of data
    d = base + timedelta(days=day_offset)

    # RestingHeartRate: 62-72 bpm (female, slight elevation due to hyperthyroidism)
    rhr_val = rng.uniform(63, 74)
    records.append(
        f'<Record type="HKQuantityTypeIdentifierRestingHeartRate" '
        f'sourceName="Apple\u00a0Watch" unit="count/min" '
        f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
        f'value="{rhr_val:.1f}"/>'
    )

    # HRV SDNN every 3 days
    if day_offset % 3 == 0:
        hrv_val = rng.uniform(28, 52)
        records.append(
            f'<Record type="HKQuantityTypeIdentifierHeartRateVariabilitySDNN" '
            f'sourceName="Apple\u00a0Watch Series\u00a07" unit="ms" '
            f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
            f'value="{hrv_val:.1f}"/>'
        )

    # StepCount (multiple small records per day, simulating Watch + iPhone)
    for _ in range(rng.randint(4, 8)):
        steps = rng.randint(800, 2200)
        records.append(
            f'<Record type="HKQuantityTypeIdentifierStepCount" '
            f'sourceName="iPhone" unit="count" '
            f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
            f'value="{steps}"/>'
        )

    # VO2Max weekly
    if day_offset % 7 == 0:
        vo2 = rng.uniform(37.0, 42.0)  # female 34yo, slightly below "good" bracket
        records.append(
            f'<Record type="HKQuantityTypeIdentifierVO2Max" '
            f'sourceName="Apple\u00a0Watch Series\u00a07" unit="mL/min\u00b7kg" '
            f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
            f'value="{vo2:.1f}"/>'
        )

    # OxygenSaturation: every 5 days
    if day_offset % 5 == 0:
        spo2 = rng.uniform(96.5, 99.0)
        records.append(
            f'<Record type="HKQuantityTypeIdentifierOxygenSaturation" '
            f'sourceName="Apple\u00a0Watch Series\u00a07" unit="%" '
            f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
            f'value="{spo2:.1f}"/>'
        )

    # BodyMass: weekly, in lb (Apple Health default!)
    if day_offset % 7 == 0:
        # 138 lb ± 2 lb
        weight_lb = rng.uniform(136.0, 140.0)
        records.append(
            f'<Record type="HKQuantityTypeIdentifierBodyMass" '
            f'sourceName="iPhone" unit="lb" '
            f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
            f'value="{weight_lb:.1f}"/>'
        )

    # Sleep (every day, simple stages)
    for stage in ['HKCategoryValueSleepAnalysisAsleepCore',
                  'HKCategoryValueSleepAnalysisAsleepDeep',
                  'HKCategoryValueSleepAnalysisAsleepREM',
                  'HKCategoryValueSleepAnalysisAwake']:
        count = rng.randint(1, 3)
        for _ in range(count):
            records.append(
                f'<Record type="HKCategoryTypeIdentifierSleepAnalysis" '
                f'sourceName="Apple\u00a0Watch Series\u00a07" '
                f'startDate="{fmt_date(d)}" endDate="{fmt_date(d)}" '
                f'value="{stage}"/>'
            )

xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml_content += '<HealthData locale="en_US">\n'
xml_content += '\n'.join(records)
xml_content += '\n</HealthData>\n'

# Write export.zip into data/raw/
export_zip_path = workspace / "data" / "raw" / "export.zip"
with zipfile.ZipFile(export_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("apple_health_export/export.xml", xml_content)

print(f"[gen_inputs] export.zip created: {export_zip_path} ({export_zip_path.stat().st_size // 1024} KB)")
print(f"[gen_inputs] XML records: {len(records)}")
print("[gen_inputs] Workspace ready.")