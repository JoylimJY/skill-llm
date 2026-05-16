import os
import random
import csv

random.seed(42)

# --- Directory structure ---
dirs = [
    "scripts",
    "docs/standards",
    "docs/templates",
    "data/incoming",
    "data/archive",
    "reports/draft",
    "reports/final",
    "config",
    "logs",
    "tools/calibration",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
distractors = {
    "docs/standards/GJB9001C_summary.txt": (
        "GJB9001C-2017 质量管理体系要求\n"
        "本文档为内部摘要，非正式标准文本。\n"
        "适用范围：所有军用电机生产线。\n"
    ),
    "docs/standards/GJB179A_sampling.txt": (
        "GJB179A 计数抽样方案\n"
        "S-3级: 批量2-50, 样本3, 判定[0,1]\n"
        "S-4级: 批量51-500, 样本13, 判定[0,1]\n"
        "II级: 批量501-3200, 样本50, 判定[1,2]\n"
        "III级: 批量3201-35000, 样本125, 判定[2,3]\n"
    ),
    "docs/templates/inspection_checklist_v3.md": (
        "# 检验清单 v3\n\n"
        "- 外观检查\n"
        "- 绝缘电阻\n"
        "- 耐压\n"
        "- 空载运行\n"
    ),
    "config/report_config.yaml": (
        "report_version: 1.2.0\n"
        "output_dir: reports/\n"
        "default_locale: zh_CN\n"
        "encoding: utf-8\n"
    ),
    "logs/system.log": (
        "[2024-03-01 08:00:01] System started\n"
        "[2024-03-01 08:05:22] IQC session opened\n"
        "[2024-03-01 09:30:11] Report generated: B2024001\n"
        "[2024-03-01 10:15:44] PQC session closed\n"
    ),
    "data/archive/batch_B2023099.csv": (
        "batch_id,supplier,material,qty,result\n"
        "B2023099,精诚磁材,硅钢片,200,PASS\n"
    ),
    "tools/calibration/torque_wrench_cal.txt": (
        "力矩扳手校准记录\n"
        "设备编号: TW-007\n"
        "校准日期: 2024-01-15\n"
        "下次校准: 2025-01-15\n"
        "校准员: 张工\n"
    ),
    "tools/calibration/micrometer_cal.txt": (
        "千分尺校准记录\n"
        "设备编号: MC-012\n"
        "精度: ±0.001mm\n"
        "校准日期: 2024-02-01\n"
    ),
    "reports/draft/draft_fqc_20240010.txt": (
        "草稿 - 未提交\n"
        "型号: PMSM-1kW\n"
        "序列号: 20240010\n"
        "状态: 待审核\n"
    ),
    "data/incoming/supplier_list.txt": (
        "已认证供应商列表:\n"
        "1. 北方磁材有限公司\n"
        "2. 华电绝缘材料厂\n"
        "3. 精密轴承集团\n"
        "4. 联合电磁线厂\n"
    ),
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- The core inspection_report.py script ---
# This is the key proprietary script referenced in SKILL.md
script_content = r'''#!/usr/bin/env python3
"""Military Motor Inspection Report Generator - GJB Standard System"""
import argparse
import sys
import os
from datetime import datetime

VALID_TYPES = {
    "iqc": "来料检验报告",
    "pqc": "过程检验报告",
    "fqc": "成品检验报告",
    "oqc": "出厂检验报告",
}

def generate_iqc(supplier, batch):
    lines = [
        "=" * 60,
        "        来料检验报告 (IQC)",
        "=" * 60,
        f"供应商: {supplier}",
        f"批次号: {batch}",
        f"检验日期: {datetime.now().strftime('%Y-%m-%d')}",
        f"执行标准: GJB179A / GJB360B",
        "",
        "【磁性材料检验】",
        "  硅钢片厚度:     0.35±0.02mm    抽样级别: II级",
        "  硅钢片表面涂层: 均匀无脱落     抽样级别: I级",
        "  磁通密度:       ≥1.5T@5000A/m  抽样级别: S-4",
        "  磁钢牌号Br:     符合图样       抽样级别: S-3",
        "  磁钢尺寸:       ±0.05mm        抽样级别: II级",
        "",
        "【绝缘材料检验】",
        "  槽绝缘厚度:     0.25±0.02mm    抽样级别: II级",
        "  耐温等级:       F级(155℃)     抽样级别: S-3",
        "  击穿电压:       ≥6kV/mm        抽样级别: S-4",
        "",
        "【轴承检验】",
        "  外观:           无划伤无锈蚀",
        "  游隙:           符合C3组",
        "  旋转灵活性:     无异响",
        "",
        "【电磁线检验】",
        "  线径:           ±0.01mm",
        "  绝缘厚度:       符合QZ-2标准",
        "  耐电压:         2000V/1min不击穿",
        "  软化延伸率:     ≥20%",
        "",
        "检验结论: □合格  □不合格",
        f"检验员: ___________  审核: ___________  批准: ___________",
        "=" * 60,
    ]
    return "\n".join(lines)

def generate_pqc(model, sn):
    lines = [
        "=" * 60,
        "        过程检验报告 (PQC)",
        "=" * 60,
        f"产品型号: {model}",
        f"序列号: {sn}",
        f"检验日期: {datetime.now().strftime('%Y-%m-%d')}",
        f"执行标准: GJB2153 / GJB1184",
        "",
        "【定子检验】",
        "  槽满率:       45%~55%          嵌线后",
        "  直流电阻:     三相不平衡≤2%   嵌线后",
        "  绝缘电阻:     ≥100MΩ          浸漆前/后",
        "  匝间绝缘:     无击穿           浸漆前",
        "  相间绝缘:     无短路           浸漆前",
        "",
        "【转子检验】",
        "  动平衡:       G2.5级           磁钢安装后",
        "  轴向跳动:     ≤0.02mm          压装后",
        "  径向跳动:     ≤0.03mm          压装后",
        "",
        "【整机装配检验】",
        "  气隙均匀性:   偏差≤10%均值",
        "  端盖同轴度:   ≤0.03mm",
        "  螺栓力矩:     符合工艺文件",
        "  轴承游隙:     转动灵活无卡滞",
        "",
        "检验结论: □合格  □不合格",
        f"检验员: ___________  审核: ___________  批准: ___________",
        "=" * 60,
    ]
    return "\n".join(lines)

def generate_fqc(model, sn):
    lines = [
        "=" * 60,
        "        成品检验报告 (FQC)",
        "=" * 60,
        f"产品型号: {model}",
        f"序列号: {sn}",
        f"检验日期: {datetime.now().strftime('%Y-%m-%d')}",
        f"执行标准: GJB2153 / GJB423",
        "",
        "【电气性能检验】",
        "  空载电流:     ≤额定电流30%     功率分析仪",
        "  空载转速:     额定转速±5%      光电转速仪",
        "  绝缘电阻:     ≥100MΩ           500V兆欧表",
        "  耐电压:       1500V/1mA/1min   耐压仪",
        "  接地电阻:     ≤0.1Ω            接地电阻仪",
        "  振动:         ≤2.8mm/s         振动仪",
        "  噪音:         ≤65dB(A)         声级计",
        "",
        "【环境试验（GJB423）】",
        "  高温试验:     85℃×2h          首批/定期",
        "  低温试验:     -40℃×2h         首批/定期",
        "  湿热试验:     40℃×95%RH×48h   首批/定期",
        "  振动试验:     GJB360B方法      首批",
        "  冲击试验:     50g/11ms         首批",
        "",
        "检验结论: □合格  □不合格",
        f"检验员: ___________  审核: ___________  批准: ___________",
        "=" * 60,
    ]
    return "\n".join(lines)

def generate_oqc(model, sn):
    lines = [
        "=" * 60,
        "        出厂检验报告 (OQC)",
        "=" * 60,
        f"产品型号: {model}",
        f"序列号: {sn}",
        f"检验日期: {datetime.now().strftime('%Y-%m-%d')}",
        f"执行标准: GJB9001C-2017 / GJB179A",
        "",
        "【出厂检验项目清单】",
        "  □ 外观检查:     无损伤、无锈蚀、标识清晰",
        "  □ 型号规格核对: 与合同/技术协议一致",
        "  □ 绝缘电阻:     ≥100MΩ",
        "  □ 耐压:         1500V/1mA/1min无击穿",
        "  □ 空载运行:     30min，无异响、无振动",
        "  □ 负载运行:     额定负载30min，温升正常",
        "  □ 噪声:         ≤65dB(A)",
        "  □ 振动:         ≤2.8mm/s",
        "  □ 随机文件:     检验报告、合格证、说明书",
        "",
        "【抽样方案（GJB179A）】",
        "  检验级别: II级   批量范围: 501~3200",
        "  样本量: 50       判定数组: [1,2]",
        "",
        "检验结论: □合格  □不合格",
        f"检验员: ___________  审核: ___________  批准: ___________",
        "=" * 60,
    ]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Military Motor Inspection Report Generator"
    )
    parser.add_argument("--list", action="store_true", help="List all inspection types")
    parser.add_argument("--type", choices=list(VALID_TYPES.keys()), help="Inspection type")
    parser.add_argument("--supplier", help="Supplier name (IQC only)")
    parser.add_argument("--batch", help="Batch ID (IQC only)")
    parser.add_argument("--model", help="Motor model (PQC/FQC/OQC)")
    parser.add_argument("--sn", help="Serial number (PQC/FQC/OQC)")
    parser.add_argument("--output", help="Output file path (OQC only)")

    args = parser.parse_args()

    if args.list:
        print("支持的检验类型:")
        for k, v in VALID_TYPES.items():
            print(f"  {k:6s} -> {v}")
        return

    if not args.type:
        print("错误: 请指定检验类型 (--type)", file=sys.stderr)
        sys.exit(1)

    report = ""
    if args.type == "iqc":
        if not args.supplier or not args.batch:
            print("错误: IQC报告需要 --supplier 和 --batch 参数", file=sys.stderr)
            sys.exit(1)
        report = generate_iqc(args.supplier, args.batch)

    elif args.type == "pqc":
        if not args.model or not args.sn:
            print("错误: PQC报告需要 --model 和 --sn 参数", file=sys.stderr)
            sys.exit(1)
        report = generate_pqc(args.model, args.sn)

    elif args.type == "fqc":
        if not args.model or not args.sn:
            print("错误: FQC报告需要 --model 和 --sn 参数", file=sys.stderr)
            sys.exit(1)
        report = generate_fqc(args.model, args.sn)

    elif args.type == "oqc":
        if not args.model or not args.sn:
            print("错误: OQC报告需要 --model 和 --sn 参数", file=sys.stderr)
            sys.exit(1)
        report = generate_oqc(args.model, args.sn)

    if args.output and args.type == "oqc":
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"OQC报告已写入: {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
'''

with open("scripts/inspection_report.py", "w", encoding="utf-8") as f:
    f.write(script_content)

# --- The messy batch intake CSV that the agent must parse ---
# Contains: one IQC entry, one PQC entry, one OQC entry
# Fields are inconsistent (extra whitespace, mixed case hints, some irrelevant columns)
intake_csv_content = """\
record_id,stage,  supplier  ,batch_code,motor_model,serial_no,qty_received,notes
REC-001,incoming quality control,北方磁材有限公司,B2024033,N/A,N/A,150,首批磁性材料入库
REC-002, Process Inspection ,N/A,N/A,PMSM-1kW,20240078,1,定子嵌线完成待检
REC-003,outgoing quality control,N/A,N/A, BLDC-200W ,20240091,1,出厂前最终检验
"""

with open("data/incoming/batch_intake_log.csv", "w", encoding="utf-8") as f:
    f.write(intake_csv_content)

# --- Additional distractor in data/incoming ---
with open("data/incoming/README_DO_NOT_USE.txt", "w", encoding="utf-8") as f:
    f.write(
        "此目录存放原始入库记录，所有文件格式不保证规范。\n"
        "请联系质量部核实数据后再处理。\n"
        "注意: batch_intake_log.csv 可能含有错误数据。\n"
    )

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    for fn in files:
        print(f"  {os.path.join(root, fn)}")