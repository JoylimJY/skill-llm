import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory structure (realistic distractor files) ---
dirs = [
    "scripts",
    "docs/gjb",
    "docs/wiring",
    "records/2024Q1",
    "records/2024Q2",
    "specs/rotor",
    "specs/stator",
    "specs/bearing",
    "qc/incoming",
    "qc/final",
    "tools/calibration",
    "tools/fixtures",
    "reports/archive",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- The real assembly_checklist.py script (as referenced in SKILL.md) ---
checklist_script = r'''#!/usr/bin/env python3
"""Assembly Checklist Script for Military Motor Assembly (FRM motor series)."""

import argparse
import sys

STAGE_ITEMS = {
    "rotor": [
        "[ROTOR-01] 转子铁心外径检验（D±IT8，卡尺）",
        "[ROTOR-02] 转子铁心内径检验（d+H7，塞规）",
        "[ROTOR-03] 槽形检验（符合图样，样板）",
        "[ROTOR-04] 叠压系数检验（≥0.95，测量计算）",
        "[ROTOR-05] 压装压力确认（5~10MPa，油压机≥50kN）",
        "[ROTOR-06] 保压时间确认（≥30s）",
        "[ROTOR-07] 铁心松动检查（不得有松动）",
        "[ROTOR-08] 禁止强行敲击铁心确认",
    ],
    "stator": [
        "[STATOR-01] 定子嵌线前绝缘检查",
        "[STATOR-02] 嵌线工艺符合WI-EM-001",
        "[STATOR-03] 预烘温度确认（120℃×2h）",
        "[STATOR-04] 真空浸漆参数（-0.08MPa，15~30min）",
        "[STATOR-05] 滴干时间确认（≥30min）",
        "[STATOR-06] 固化参数确认（130℃×4h）",
        "[STATOR-07] 浸漆后绝缘检验",
        "[STATOR-08] 防火安全确认（浸漆区禁烟火）",
    ],
    "bearing": [
        "[BEARING-01] 轴承型号核对（符合图样）",
        "[BEARING-02] 精度等级核对（P0/P6）",
        "[BEARING-03] 游隙确认（高温电机C3）",
        "[BEARING-04] 滚动体外观检查（无损伤、无异常声响）",
        "[BEARING-05] 润滑脂温度等级确认",
        "[BEARING-06] 加热方式确认（油浴80~100℃，≤120℃；或感应加热）",
        "[BEARING-07] 压装力施加方式（沿内圈，禁止外圈受力）",
        "[BEARING-08] 禁止锤击轴承确认",
    ],
}

STAGE_ITEMS["full"] = (
    STAGE_ITEMS["rotor"] +
    STAGE_ITEMS["stator"] +
    STAGE_ITEMS["bearing"] +
    [
        "[ELEC-01] 绝缘电阻≥100MΩ（兆欧表500V）",
        "[ELEC-02] 耐压试验1500V/1mA/1min（耐压仪）",
        "[ELEC-03] 空载电流≤额定电流30%（功率分析仪）",
        "[ELEC-04] 空载转速额定转速±5%（转速表）",
        "[ELEC-05] 振动≤2.8mm/s G6.3（振动仪）",
        "[ELEC-06] 噪音≤65dB(A)（声级计）",
        "[FINAL-01] 整机外观检查",
        "[FINAL-02] 铭牌核对",
        "[FINAL-03] GJB质量记录齐全",
    ]
)

def main():
    parser = argparse.ArgumentParser(description="Motor Assembly Checklist")
    parser.add_argument("--stage", required=True,
                        choices=["rotor", "stator", "bearing", "full"],
                        help="Assembly stage to generate checklist for")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: stdout)")
    parser.add_argument("--interactive", action="store_true",
                        help="Interactive confirmation mode")
    args = parser.parse_args()

    items = STAGE_ITEMS.get(args.stage, [])
    header = f"=== Motor Assembly Checklist: Stage [{args.stage.upper()}] ===\n"
    header += f"Total items: {len(items)}\n"
    header += "=" * 50 + "\n"

    lines = [header]
    for i, item in enumerate(items, 1):
        if args.interactive:
            print(f"[{i}/{len(items)}] {item}")
            print("  Confirmed? [Y/n]: ", end="", flush=True)
            resp = input()
            status = "SKIP" if resp.strip().lower() == "n" else "OK"
            lines.append(f"{item} --> {status}")
        else:
            lines.append(f"[ ] {item}")

    footer = "\n--- END OF CHECKLIST ---\n"
    lines.append(footer)
    content = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Checklist saved to: {args.output}", file=sys.stderr)
    else:
        print(content)

if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "assembly_checklist.py").write_text(checklist_script, encoding="utf-8")

# --- Distractor docs ---
distractor_docs = {
    "docs/gjb/GJB_overview.txt": "本文件为概述，详细内容参见各FRM表单。\n版本：Draft\n注意：表单编号以正式发布为准。",
    "docs/gjb/retention_policy_DRAFT.txt": "草稿文件 - 未经审核\n所有质量记录保存5年（草稿，已废弃）\n请以正式SKILL.md为准。",
    "docs/wiring/WI-EM-001_ref.txt": "定子绕组嵌线作业指导书参考\n详见gjb-document-generator技能。",
    "docs/wiring/coil_spec.txt": "线圈规格：AWG22，绝缘等级F级，额定温升80K",
    "specs/rotor/rotor_dim.txt": "转子外径: 85.00mm (-0.02/+0.00)\n转子内径: 30.00mm H7\n叠压系数要求: ≥0.95",
    "specs/stator/stator_winding.txt": "定子绕组参数：串联匝数180T，并联支路数2",
    "specs/bearing/bearing_list.txt": "轴承型号: 6206-2RS\n精度: P6\n游隙: C3\n润滑脂: 高温型（≤150℃）",
    "specs/bearing/bearing_wrong_temp.txt": "注意：旧版工艺要求加热至150℃（已废弃，请以最新规范为准）",
    "qc/incoming/incoming_check_2024Q1.csv": "批次,零件,检验结果\nBT240101,转子铁心,合格\nBT240102,磁钢,合格\nBT240103,轴承6206,合格",
    "qc/final/final_report_template.txt": "整机测试报告模板\n[填写测试数据]\n测试员：___\n日期：___",
    "records/2024Q1/FRM-ASM-001_sample.txt": "转子铁心压装记录样本\n压装压力: 7.5MPa\n保压时间: 45s\n结论: 合格",
    "records/2024Q2/FRM-ASM-004_sample.txt": "轴承装配记录样本\n加热温度: 95℃\n装配方式: 内圈受力\n结论: 合格",
    "tools/calibration/torque_wrench_cal.txt": "扭矩扳手校准记录\nM6量程: 5~25 N·m\n校准日期: 2024-03-01\n有效期: 2025-03-01",
    "tools/fixtures/fixture_list.txt": "工装清单\n- 上压模 (P/N: TL-001)\n- 下心轴 (P/N: TL-002)\n- 轴承内圈压套 (P/N: TL-003)",
    "reports/archive/old_report_2023.json": json.dumps({"note": "archived", "year": 2023, "status": "superseded"}, ensure_ascii=False, indent=2),
}

for rel_path, content in distractor_docs.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# --- The SKILL.md (agent's reference) ---
skill_md = r"""---
name: motor-assembly-process
description: 电机装配工艺助手 | 生成军用电机装配作业指导书
version: 1.2.0
---

# 电机装配工艺助手 v1.2

## 装配检查清单脚本

```bash
python scripts/assembly_checklist.py --stage rotor
python scripts/assembly_checklist.py --stage stator
python scripts/assembly_checklist.py --stage bearing
python scripts/assembly_checklist.py --stage full --output checklist_full.txt
python scripts/assembly_checklist.py --stage full --interactive
```

## 九、质量记录（GJB规范）

| 记录名称 | 表单编号 | 保存期限 |
|---------|---------|---------|
| 转子铁心压装记录 | FRM-ASM-001 | 5年 |
| 磁钢安装记录 | FRM-ASM-002 | 10年 |
| 动平衡记录 | FRM-ASM-003 | 10年 |
| 定子嵌线检验记录 | FRM-EM-001 | 10年 |
| 轴承装配记录 | FRM-ASM-004 | 5年 |
| 整机测试报告 | FRM-ASM-005 | 10年 |

## 八、电气测试

| 测试项目 | 要求 | 设备 |
|---------|------|------|
| 绝缘电阻 | ≥100MΩ | 兆欧表500V |
| 耐压试验 | 1500V/1mA/1min | 耐压仪 |
| 空载电流 | ≤额定电流30% | 功率分析仪 |
| 空载转速 | 额定转速±5% | 转速表 |
| 振动 | ≤2.8mm/s(G6.3) | 振动仪 |
| 噪音 | ≤65dB(A) | 声级计 |

## 三、转子动平衡

| 转子类型 | 平衡等级 | 最大残余不平衡量 |
|---------|---------|---------------|
| 普通转子 | G6.3 | 6.3mm/s |
| 电机转子 | G2.5 | 2.5mm/s |
| 精密主轴 | G1.0 | 1.0mm/s |
| 高速（>10000rpm） | G0.4 | 0.4mm/s |

## 六、轴承装配

- 轴承加热：油浴加热至80~100℃（≤120℃），或感应加热
- 压装力沿轴承内圈施加，禁止外圈受力
- 加热温度≤120℃，防止轴承硬度降低
- 禁止用锤子直接敲击轴承
"""
(WORKSPACE / "SKILL.md").write_text(skill_md, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created under: {WORKSPACE}")