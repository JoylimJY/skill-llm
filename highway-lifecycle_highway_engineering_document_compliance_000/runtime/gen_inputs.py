import os
import json
from pathlib import Path

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "project/arch/drawings",
    "project/arch/calculations",
    "project/geotechnical/boring_logs",
    "project/geotechnical/lab_reports",
    "project/traffic/flow_analysis",
    "project/traffic/signal_design",
    "project/env_assessment/noise",
    "project/env_assessment/water",
    "project/cost_estimate/2023",
    "project/cost_estimate/2024_revision",
    "project/schedule/milestones",
    "project/correspondence/letters",
    "project/correspondence/approvals",
    "references",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "project/arch/drawings/plan_view_v3.dwg.txt":
        "Plan view drawing - Sheet 3 of 12. Scale 1:500. Do not scale from this drawing.",
    "project/arch/drawings/elevation_A1.txt":
        "Elevation drawing A1. Pier heights vary 8.5m to 12.3m. Foundation type: bored pile.",
    "project/arch/calculations/wind_load_analysis.txt":
        "Wind load calculation per GB50009-2012. Basic wind pressure 0.55kN/m2. Height factor 1.42.",
    "project/arch/calculations/seismic_calc.txt":
        "Seismic calculation per GB18306-2015. Peak ground acceleration 0.10g. Site class II.",
    "project/geotechnical/boring_logs/BH-01.txt":
        "Borehole BH-01. Depth 35m. SPT values: 0-5m N=8, 5-10m N=15, 10-20m N=32, 20-35m N>50.",
    "project/geotechnical/boring_logs/BH-02.txt":
        "Borehole BH-02. Depth 40m. Groundwater encountered at 3.5m depth. Clay layer 0-8m.",
    "project/geotechnical/lab_reports/soil_classification.txt":
        "Soil classification test results. Sample ID: S-01 through S-15. Plasticity index 18-24.",
    "project/traffic/flow_analysis/AADT_projection.txt":
        "Annual Average Daily Traffic projection. Year 2025: 18,500 vehicles/day. Design year 2045: 32,000 vehicles/day.",
    "project/traffic/signal_design/intersection_timing.txt":
        "Signal timing plan. Cycle length 120s. Phase splits: NS 60%, EW 40%.",
    "project/env_assessment/noise/noise_prediction.txt":
        "Noise prediction model results. Daytime: 62.3 dB(A). Nighttime: 54.1 dB(A). Mitigation required.",
    "project/env_assessment/water/water_quality.txt":
        "Water quality assessment. River crossing category: Class III. Protective measures required.",
    "project/cost_estimate/2024_revision/BOQ_summary.txt":
        "Bill of Quantities summary. Total estimated cost: CNY 285,000,000. Contingency 10%.",
    "project/schedule/milestones/construction_schedule.txt":
        "Construction milestone schedule. Piling start: Q1 2025. Superstructure: Q3 2025. Completion: Q4 2026.",
    "project/correspondence/approvals/EIA_approval_2024.txt":
        "Environmental Impact Assessment approval letter. Approved by provincial authority. Reference: ZJEP-2024-0892.",
}
for rel_path, content in distractors.items():
    (workspace / rel_path).write_text(content, encoding="utf-8")

# ── Main problem file: messy bridge design spec with deliberate issues ────────
# The document has MULTIPLE embedded issues the agent must find:
#
# ISSUE 1 (上下文一致性, 高): 
#   Section 2.1 says main beam concrete is C50, Section 4.3 says C40 → conflict
#
# ISSUE 2 (上下文一致性, 高):
#   Section 2.3 says steel plate is Q355D, Section 5.1 says Q235C → conflict
#
# ISSUE 3 (上下文一致性, 中):
#   Section 3.2 gives prestress friction coefficient μ=0.25, Section 6.1 says μ=0.20 → conflict
#
# ISSUE 4 (规范符合性, 高):
#   Section 7.1 cites JT/T 329-2010 for anticorrosion — this is outdated, should be JT/T 329-2025
#
# ISSUE 5 (规范符合性, 中):
#   Section 4.1 specifies site steel connections use Sa3 derusting — 
#   per SKILL.md engineering knowledge, Sa3 is NOT achievable on-site; 
#   site work must use St3 (manual/power tool treatment)
#
# ISSUE 6 (规范符合性, 中):
#   Section 8.2 applies railway corrosion classification JC3 to a rural highway bridge
#   — per SKILL.md, rural area → JC2; also railway norms don't apply to highway
#
# ISSUE 7 (上下文一致性, 低):
#   Section 3.2 says positioning bar spacing is 80cm, Section 3.4 says 100cm → conflict
#
# ISSUE 8 (上下文一致性, 一致 - should NOT be flagged as error):
#   Section 2.2 specifies water-cement ratio 0.38, range given as ≤0.40 → satisfies range → CONSISTENT

design_doc = """\
# 云岭特大桥预应力混凝土连续箱梁桥设计说明书
## 项目概况

本项目为浙江省云岭高速公路控制性工程——云岭特大桥，全长1240m，主跨80+3×130+80m预应力混凝土连续箱梁。
桥址区为乡村区域，距工业污染源距离大于50km。设计使用年限100年，公路等级：高速公路。

---

## 第2章 主梁结构设计

### 2.1 主梁材料
主梁混凝土强度等级采用 **C50**，水下承台采用C35，桥墩墩身采用C40。
预应力筋采用高强低松弛钢绞线，强度等级fpk=1860MPa。

### 2.2 配合比设计
混凝土配合比设计水胶比为0.38，满足规范对C50混凝土水胶比不大于0.40的要求。
骨料最大粒径25mm，水泥用量380kg/m³。

### 2.3 钢板材料
主梁横隔梁钢板采用 **Q355D** 钢，厚度16mm，符合抗震延性要求。

---

## 第3章 预应力体系

### 3.1 预应力束布置
纵向预应力束采用12-15.2钢绞线，每束面积2100mm²，布置于箱梁顶底板及腹板。

### 3.2 预应力参数
- 孔道摩擦系数：μ = **0.25**
- 孔道偏差系数：k = 0.0015
- 定位筋间距：**80cm**
- 张拉控制应力：σcon = 0.75fpk = 1395MPa

### 3.3 张拉顺序
先张腹板束，后张顶板束，最后张底板束。两端同步张拉，超张拉5%后锚固。

### 3.4 定位筋要求
预应力管道定位筋间距应不大于 **100cm**，焊接固定于普通钢筋骨架上。
定位精度：平面位置偏差不超过±5mm。

---

## 第4章 防腐与防护

### 4.1 钢结构除锈处理
桥面系钢横梁在工地现场安装前，采用喷砂处理达到 **Sa3级** 除锈标准。
钢板表面粗糙度Ra≥60μm，处理后4小时内完成底漆涂装。

### 4.2 涂层体系
底漆：环氧富锌底漆，干膜厚度75μm×2道
中间漆：环氧云铁中间漆，干膜厚度100μm×2道
面漆：脂肪族聚氨酯面漆，干膜厚度60μm×2道

### 4.3 混凝土防腐
主梁混凝土强度等级 **C40**，保护层厚度不小于40mm，满足100年设计使用寿命要求。

---

## 第5章 连接设计

### 5.1 工地栓焊混合连接
工地连接采用 **Q235C** 钢板（厚度12mm）制作连接板，高强螺栓10.9级，
摩擦面采用喷砂处理，抗滑移系数μs≥0.40。

### 5.2 焊接要求
全熔透对接焊缝按一级焊缝验收，超声波检测100%。

---

## 第6章 施工技术要求

### 6.1 预应力施工
孔道摩擦系数取 μ = **0.20**，偏差系数 k = 0.0015。
灌浆料水灰比不大于0.30，泌水率不超过0%。

### 6.2 模板工程
悬臂挂篮模板刚度验算按1.2倍荷载进行，挠度不超过L/400。

---

## 第7章 规范引用

### 7.1 引用规范清单
本设计依据以下现行规范：
- 《公路桥涵设计通用规范》JTG D60-2015
- 《公路钢筋混凝土及预应力混凝土桥涵设计规范》JTG 3362-2018
- 《钢结构防腐涂装通用技术条件》**JT/T 329-2010**
- 《公路桥涵施工技术规范》JTG/T 3650-2020
- 《预应力混凝土用钢绞线》GB/T 5224-2014

---

## 第8章 耐久性设计

### 8.1 设计使用年限
本桥设计使用年限100年，钢筋混凝土构件按JTG 3362-2018第6章进行耐久性验算。

### 8.2 腐蚀环境分类
本桥腐蚀环境参照铁路桥梁规范TB/T 1979进行分类，划定为 **JC3（工业区）** 腐蚀环境等级，
涂层总厚度不低于320μm。

---

## 附录A：主要技术指标汇总

| 指标 | 数值 |
|------|------|
| 主梁混凝土 | C50 |
| 桥墩混凝土 | C40 |
| 预应力钢绞线 | 1860MPa |
| 摩擦系数μ（设计） | 0.25 |
| 摩擦系数μ（施工） | 0.20 |

---
*文件版本：Draft-Rev03 | 编制日期：2025-01-15 | 编制人：王工*
"""

(workspace / "project" / "design_spec_yunling_bridge.md").write_text(
    design_doc, encoding="utf-8"
)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")