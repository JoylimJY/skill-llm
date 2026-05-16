import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# === Directory structure ===
dirs = [
    "scripts",
    "references",
    "drawings/stator",
    "drawings/rotor",
    "drawings/assembly",
    "drawings/archive",
    "reports/previous",
    "reports/drafts",
    "specs/electromagnetic",
    "specs/structural",
    "tools",
    "bom",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# === scripts/drawing_checklist.py ===
# This is the actual script the agent should invoke
checklist_script = '''\
#!/usr/bin/env python3
"""Motor Drawing Review Checklist Script v1.2"""
import argparse
import sys
from datetime import date

FULL_CHECKLIST = """
=== 电机图纸完整审图清单 ===
生成日期：{date}

【A. 图纸信息核对】
A1. 图纸编号、版本号、日期填写完整
A2. 图纸名称与设计任务书一致
A3. 审核人、设计人签名栏齐全

【B. 极槽配合检查】
B1. 极数(2P)确认，与转速规格匹配
B2. 槽数(Q)确认，与极数配合合理
B3. 每极每相槽数 q=Q/(2pm) 计算核实，q≥0.5
B4. 极槽比LCM验证，LCM过大需评估振动风险
B5. 绕组排布（60°/120°相带）标注明确

【C. 关键尺寸检查】
C1. 定子外径、内径标注完整
C2. 转子外径 = 定子内径 - 2×气隙，核实
C3. 气隙长度（0.3~1.0mm范围）且有公差标注
C4. 铁心长度与设计书一致
C5. 轴径、轴承位尺寸标注完整

【D. 公差配合验证】
D1. 轴承位（轴）：h6/k6/m6
D2. 机座止口：H7（孔）
D3. 轴承室（孔）：H7
D4. 键槽：N9/P9（符合GB/T 1095）
D5. 转轴光滑段：h6(IT6)

【E. 形位公差检查】
E1. 定子内圆跳动 ≤ 0.03mm
E2. 转子外圆跳动 ≤ 0.03mm
E3. 轴伸跳动 ≤ 0.03mm
E4. 轴承位圆柱度 IT6
E5. 止口平面度 ≤ 0.02mm

【F. 技术要求审核】
F1. 材料牌号明确（硅钢片型号、磁钢牌号）
F2. 表面处理要求（防锈/涂覆）
F3. 热处理要求（调质/渗碳/未要求需注明）
F4. 动平衡等级（G2.5或G6.3）标注
F5. 绝缘等级（E/B/F/H）标注
F6. 温升限值有具体数值

【G. 标注规范检查】
G1. 粗糙度标注正确（轴承位Ra≤1.6μm）
G2. 形位公差有基准标注
G3. 未注公差说明（GB/T 1804-m）
G4. 倒角标注完整
"""

ELECTROMAGNETIC_CHECKLIST = """
=== 电磁设计图纸审图清单 ===
生成日期：{date}

【B. 极槽配合检查】
B1. 极数(2P)确认
B2. 槽数(Q)确认
B3. q=Q/(2pm) 核实
B4. LCM验证
B5. 绕组排布

【C. 关键电磁尺寸】
C1. 气隙长度及公差
C2. 铁心长度
C3. 定子槽型尺寸
"""

STRUCTURAL_CHECKLIST = """
=== 结构设计图纸审图清单 ===
生成日期：{date}

【D. 公差配合】
D1-D5 见完整清单

【E. 形位公差】
E1-E5 见完整清单

【G. 标注规范】
G1-G4 见完整清单
"""

def main():
    parser = argparse.ArgumentParser(description="Motor Drawing Checklist Generator")
    parser.add_argument("--type", choices=["full", "electromagnetic", "structural"], default="full")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    today = date.today().strftime("%Y-%m-%d")

    if args.type == "full":
        content = FULL_CHECKLIST.format(date=today)
    elif args.type == "electromagnetic":
        content = ELECTROMAGNETIC_CHECKLIST.format(date=today)
    else:
        content = STRUCTURAL_CHECKLIST.format(date=today)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"清单已保存至: {args.output}")
    else:
        print(content)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts/drawing_checklist.py"), "w", encoding="utf-8") as f:
    f.write(checklist_script)

# === references/gdt-reference.md ===
gdt_ref = """\
# GD&T 形位公差参考规范 v1.2

## 电机常用公差配合

### 轴承配合（GB/T 275）
- 轴承内径与轴（轴承位）：轴用 k6（过盈量小，标准），重载用 m6
- 轴承外径与轴承室（孔）：孔用 H7（正常），重载用 JS7

### 止口配合
- 机座止口（孔）：H7，端盖止口（轴）：h6 或 js6

### 键槽配合（GB/T 1095）
- 普通平键槽宽：N9（毂孔），P9（轴）

## 形位公差数值
| 部位 | 公差类型 | 允许值 |
|------|---------|--------|
| 定子内圆 | 圆跳动 | ≤0.03mm |
| 转子外圆 | 圆跳动 | ≤0.03mm |
| 轴伸端 | 圆跳动 | ≤0.03mm |
| 轴承位 | 圆柱度 | IT6 |
| 端盖止口 | 平面度 | ≤0.02mm |

## 粗糙度要求
| 表面 | Ra (μm) |
|------|---------|
| 轴承位 | 0.8~1.6 |
| 转子外圆 | 0.8~1.6 |
| 止口配合面 | 1.6~3.2 |
| 键槽侧面 | 1.6~3.2 |
| 键槽底面 | 3.2~6.3 |
"""
with open(os.path.join(workspace, "references/gdt-reference.md"), "w", encoding="utf-8") as f:
    f.write(gdt_ref)

# === THE MAIN PROBLEM INPUT: flawed motor drawing specification ===
# This file has INTENTIONAL errors the agent must identify
motor_drawing_spec = """\
图纸编号：DWG-PUMP-4P-2024-001
图纸名称：YE3-132M-4极三相异步电动机定转子总成图
版本：A0
设计人：李工
日期：2024-05-10

==== 电磁参数 ====
极数 2P = 4
槽数 Q = 18
相数 m = 3
（注：每极每相槽数未计算，请审图时核实）

备注：极槽配合选用18槽4极，绕组采用60°相带。

==== 关键尺寸 ====
定子外径：Φ210mm
定子内径：Φ132mm
转子外径：Φ131mm  （← 设计值，气隙约0.5mm）
气隙长度：0.5mm    （← 无公差标注）
铁心长度：145mm

轴径（轴承位A端）：Φ45mm，公差 H7  （← 轴用H7标注）
轴径（轴承位B端）：Φ40mm，公差 h6
轴承室（端盖孔A端）：Φ85mm，公差 H7
轴伸端轴径：Φ38mm，公差 k6

键槽宽度：12mm，公差 H9   （← 键槽轴端公差H9）
键槽深度：5mm，无公差标注

==== 形位公差 ====
定子内圆跳动：0.05mm  （← 超标）
转子外圆跳动：0.03mm  ✓
轴伸跳动：0.03mm  ✓
轴承位圆柱度：IT7     （← 应为IT6）
止口平面度：0.02mm  ✓

==== 技术要求 ====
1. 定子铁心材料：硅钢片（牌号未注明）
2. 转子：铸铝转子
3. 表面处理：本体喷灰漆（型号未注明）
4. 热处理：轴调质处理 HB220~260
5. 动平衡：G6.3
6. 绝缘等级：F级
7. 温升：（未标注具体限值）
8. 粗糙度：轴承位 Ra3.2（← 应为0.8~1.6μm）

==== 标注规范 ====
- 未注公差：图纸中无未注公差说明（← 缺少GB/T 1804-m说明）
- 倒角：主要倒角已标注C1.5
- 形位公差基准：已标注基准A、B
"""

with open(os.path.join(workspace, "drawings/assembly/motor_drawing_spec_DWG-PUMP-4P-2024-001.txt"), "w", encoding="utf-8") as f:
    f.write(motor_drawing_spec)

# === Distractor files ===
# Previous reports (old format, not what agent should produce)
old_report = """\
审图记录
图号：DWG-2023-015
审图人：王工
意见：气隙标注不清，建议修改。
结论：退回修改
"""
with open(os.path.join(workspace, "reports/previous/review_DWG2023-015.txt"), "w", encoding="utf-8") as f:
    f.write(old_report)

with open(os.path.join(workspace, "reports/previous/review_DWG2023-016.txt"), "w", encoding="utf-8") as f:
    f.write("审图记录\n图号：DWG-2023-016\n结论：通过\n")

# BOM distractor
bom_content = """\
序号,零件名称,材料,数量,备注
1,定子铁心,50W470,1,冲压叠压
2,转子铁心,50W470,1,冲压叠压
3,转轴,45#钢,1,调质
4,端盖A,HT200,1,铸造
5,端盖B,HT200,1,铸造
6,轴承6209,GCr15,2,标准件
"""
with open(os.path.join(workspace, "bom/BOM-PUMP-4P-2024-001.csv"), "w", encoding="utf-8") as f:
    f.write(bom_content)

# Specs electromagnetic
em_spec = """\
YE3-132M-4极电机电磁设计参数
额定功率：7.5kW
额定电压：380V
额定转速：1440rpm
效率：IE3
功率因数：0.86
"""
with open(os.path.join(workspace, "specs/electromagnetic/YE3-132M-4P-em-design.txt"), "w", encoding="utf-8") as f:
    f.write(em_spec)

# Structural specs
struct_spec = """\
YE3-132M-4极电机结构设计参数
机座号：132M
安装方式：B3
防护等级：IP55
冷却方式：IC411
"""
with open(os.path.join(workspace, "specs/structural/YE3-132M-4P-struct.txt"), "w", encoding="utf-8") as f:
    f.write(struct_spec)

# Archive drawings (distractors)
for idx in range(1, 5):
    with open(os.path.join(workspace, f"drawings/archive/DWG-OLD-{idx:03d}.txt"), "w", encoding="utf-8") as f:
        f.write(f"归档图纸 DWG-OLD-{idx:03d}\n版本：已废止\n")

# Tools distractor
with open(os.path.join(workspace, "tools/tolerance_calculator.py"), "w", encoding="utf-8") as f:
    f.write("# 公差计算辅助工具（仅供参考）\n# 用法：python tools/tolerance_calculator.py\n")

# Draft report (incomplete, wrong format - distractor)
draft = """\
草稿审图意见：
- 气隙没公差
- 轴承位公差错
（未完成，待整理）
"""
with open(os.path.join(workspace, "reports/drafts/draft_review_001.txt"), "w", encoding="utf-8") as f:
    f.write(draft)

# Stator drawing (partial dimensions, distractor)
with open(os.path.join(workspace, "drawings/stator/stator_detail_132M.txt"), "w", encoding="utf-8") as f:
    f.write("定子冲片详图\n外径：210mm\n内径：132mm\n槽型：梨形槽\n槽深：22mm\n槽宽：8.5mm\n")

# Rotor drawing (distractor)
with open(os.path.join(workspace, "drawings/rotor/rotor_detail_132M.txt"), "w", encoding="utf-8") as f:
    f.write("转子详图\n外径：131mm\n槽型：闭口斜槽\n槽数：28\n斜槽：1个定子槽距\n")

print("Workspace setup complete.")
print(f"Files created in {workspace}")