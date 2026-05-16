import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create the material-review skill directory structure
skill_dir = workspace / "material-review"
skill_dir.mkdir(exist_ok=True)

refs_dir = skill_dir / "references"
refs_dir.mkdir(exist_ok=True)

scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(exist_ok=True)

output_dir = skill_dir / "output"
output_dir.mkdir(exist_ok=True)

# Create distractor files to simulate a real messy workspace
distractor_dirs = [
    workspace / "old_submissions" / "2023Q4",
    workspace / "old_submissions" / "2024Q1",
    workspace / "platform_exports" / "raw",
    workspace / "platform_exports" / "processed",
    workspace / "templates" / "v1",
    workspace / "templates" / "v2",
    workspace / "logs",
    workspace / "archive" / "completed",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = [
    (workspace / "old_submissions" / "2023Q4" / "submission_001.json", {"system": "旧系统A", "status": "approved"}),
    (workspace / "old_submissions" / "2023Q4" / "issues_001.json", {"issues": [], "total": 0}),
    (workspace / "old_submissions" / "2024Q1" / "submission_draft.json", {"system": "医保系统", "status": "draft"}),
    (workspace / "platform_exports" / "raw" / "catalog_export_20240301.json", {"tables": 42, "systems": 8}),
    (workspace / "platform_exports" / "processed" / "summary.json", {"processed": True, "date": "2024-03-01"}),
    (workspace / "templates" / "v1" / "template_v1.json", {"version": "1.0", "deprecated": True}),
    (workspace / "templates" / "v2" / "template_v2.json", {"version": "2.0", "current": True}),
    (workspace / "logs" / "audit_20240101.log", "审核日志：系统A 通过\n系统B 退回\n"),
    (workspace / "logs" / "audit_20240201.log", "审核日志：系统C 通过\n"),
    (workspace / "archive" / "completed" / "final_report_Q4.md", "# Q4审核报告\n已完成12个系统审核。"),
]

for path, content in distractors:
    if isinstance(content, dict):
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")

# Create the SKILL.md
skill_md_content = '''---
name: material-review
description: Use when user wants to review material forms for data sharing catalogs, field completeness, platform consistency, and issue-list output.
metadata: {"openclaw":{"emoji":"📋","requires":{"anyBins":["markdownlint-cli2"]}}}
---

# Material Review

材料审核助手，面向《数据共享清单（试运行环节）》和平台编目核验，提供 6 步审核流程。

## 核心原则

| 原则 | 说明 |
|------|------|
| **先核对再结论** | 先逐项核对字段和平台信息，再给出通过/退回建议 |
| **问题必须可追溯** | 每条问题都要写清：位置、现状、规则依据、修正建议 |
| **先文档后平台** | 先做表单完整性检查，再做系统对接与编目一致性核验 |

## 6 步审核流程

```text
1. 范围确认 → 2. 字段完整性 → 3. 特殊字段规则 → 4. 数据表筛选 → 5. 平台一致性核验 → 6. 问题清单输出
```

### 步骤 1: 范围确认

**目标**：确认本次审核对象与边界，避免漏审。

- 核对材料版本是否为《数据共享清单（试运行环节）》模板
- 记录系统名称、单位及科室、联系人、数据库对接方式
- 确认审核范围：仅审核业务相关、拟共享的数据表

### 步骤 2: 字段完整性

**目标**：先卡住必填项，避免进入后续环节才发现基础信息缺失。

- 除备注外均按必填处理
- 重点检查易漏字段：系统上线时间、数据资源摘要、目前数据量、数据项中文描述
- 检查易错填写：数据增量写成数字、上线时间写成 `/` 等无效值

### 步骤 3: 特殊字段规则

**目标**：处理高频退回项，保证可审核、可落地。

- **数据增量**：当目前数据量超过 10000 且持续新增时必填；若明确全量更新可不填
- **数据项中文描述**：每个字段必须有中文描述，不能为空，且不能与英文名完全一致
- **共享类型**：一般不可直接写「不予共享」；若确需不共享，必须给出法律或制度依据

### 步骤 4: 数据表筛选

**目标**：只保留应共享的业务表，减少无效编目和后续维护成本。

- 剔除业务无关表（如配置表、日志表等）
- 对目前数据量为 0 的表单独标注，要求确认是否仍需保留
- 逐表核对：中文表名、英文表名、摘要、更新频率、字段定义是否完整

### 步骤 5: 平台一致性核验

**目标**：校验材料与平台现状是否一致，明确对接状态和差异。

- 在平台前台/后台检索系统，确认是否已对接
- 若未对接，明确标注「未对接」
- 若已对接，核对四类差异：系统名称、数据表数量、表名映射、未编目表
- 检查平台表更新情况：超过半年未更新需标注
- 检查平台字段中文名：中文名为「默认信息」或直接英文时需标注
- `TIMEFLAG` 为系统统一字段，中文名为默认信息时可忽略

### 步骤 6: 问题清单输出

**目标**：输出可直接回传给填报单位的整改清单。

- 按「必填缺失 / 规则不符 / 平台不一致 / 待确认」分类
- 每条问题都给出修正动作，不只指出错误
- 一次只处理一个系统，完成后再进入下一个系统

## 审核节奏

```text
1) 先过"字段完整性+特殊规则"
2) 再做"平台检索+一致性比对"
3) 输出问题清单并等待用户确认
4) 用户确认后再继续下一个系统
```

## 输出格式速查

| 要素 | 要求 |
|------|------|
| 问题定位 | 明确到字段名/数据表名/系统名称 |
| 规则依据 | 对应模板要求或审核规则 |
| 风险描述 | 不改会导致什么后果（如审核不通过、无法编目） |
| 修正建议 | 可执行动作，避免笼统建议 |
'''

(workspace / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

# Create the main submission data that the agent needs to review
# This is a structured JSON representing a data sharing catalog submission
# with multiple deliberate violations
submission_data = {
    "meta": {
        "template_version": "数据共享清单（试运行环节）",
        "submission_date": "2025-01-15",
        "reviewer_note": "请对以下系统的共享清单进行审核，输出问题清单报告"
    },
    "system_info": {
        "system_name": "城市综合执法管理系统",
        "department": "市城市管理局执法支队",
        "contact_person": "张工",
        "contact_phone": "021-12345678",
        "db_connection_type": "数据库直连",
        "system_online_date": "/",          # VIOLATION: invalid value for required field
        "data_resource_summary": ""         # VIOLATION: empty required field
    },
    "data_tables": [
        {
            "table_name_cn": "行政执法案件表",
            "table_name_en": "admin_enforcement_case",
            "summary": "记录行政执法案件的基本信息，包括案件编号、违规类型、处罚结果等",
            "update_frequency": "每日",
            "current_data_volume": 158000,
            "data_increment": "",           # VIOLATION: volume > 10000, should check if continuously growing
            "is_continuously_growing": True, # meta flag for eval
            "sharing_type": "无条件共享",
            "fields": [
                {"field_en": "case_id", "field_cn": "案件编号", "description": "唯一标识执法案件的编号"},
                {"field_en": "violation_type", "field_cn": "违规类型", "description": "violation_type"},  # VIOLATION: cn desc == en name
                {"field_en": "penalty_result", "field_cn": "处罚结果", "description": ""},               # VIOLATION: empty description
                {"field_en": "TIMEFLAG", "field_cn": "默认信息", "description": "系统时间戳字段"}         # OK: TIMEFLAG exemption applies
            ]
        },
        {
            "table_name_cn": "执法人员信息表",
            "table_name_en": "enforcement_officer",
            "summary": "执法人员基本档案信息",
            "update_frequency": "按需更新",
            "current_data_volume": 320,
            "data_increment": "",           # OK: volume <= 10000, not required
            "is_continuously_growing": False,
            "sharing_type": "不予共享",     # VIOLATION: no legal basis provided
            "legal_basis": "",              # VIOLATION: legal basis missing
            "fields": [
                {"field_en": "officer_id", "field_cn": "人员编号", "description": "执法人员唯一标识"},
                {"field_en": "officer_name", "field_cn": "姓名", "description": "执法人员姓名"},
                {"field_en": "TIMEFLAG", "field_cn": "默认信息", "description": "时间戳"}  # OK: TIMEFLAG exemption
            ]
        },
        {
            "table_name_cn": "系统配置参数表",
            "table_name_en": "sys_config_params",
            "summary": "系统运行配置参数",
            "update_frequency": "不定期",
            "current_data_volume": 45,
            "data_increment": "",
            "is_continuously_growing": False,
            "sharing_type": "无条件共享",
            "fields": [
                {"field_en": "param_key", "field_cn": "参数键", "description": "配置参数名称"},
                {"field_en": "param_value", "field_cn": "参数值", "description": "配置参数数值"}
            ]
            # NOTE: This is a config table - should be flagged for removal (步骤4)
        },
        {
            "table_name_cn": "违章停车记录表",
            "table_name_en": "illegal_parking_record",
            "summary": "",                  # VIOLATION: empty summary (required field)
            "update_frequency": "实时",
            "current_data_volume": 0,       # VIOLATION: zero data volume - needs confirmation
            "data_increment": "",
            "is_continuously_growing": False,
            "sharing_type": "条件共享",
            "fields": [
                {"field_en": "plate_number", "field_cn": "车牌号", "description": "车辆牌照号码"},
                {"field_en": "location", "field_cn": "location", "description": "停车地点"}  # VIOLATION: cn name == en name
            ]
        }
    ],
    "platform_info": {
        "platform_connection_status": "已对接",
        "platform_system_name": "城市综合执法系统",  # DISCREPANCY: name differs from system_info.system_name
        "platform_table_count": 2,          # DISCREPANCY: submission has 4 tables, platform has 2
        "platform_tables": [
            {
                "table_name": "admin_enforcement_case",
                "last_updated": "2024-05-10",   # VIOLATION: > 6 months ago from submission date 2025-01-15
                "fields_with_issues": [
                    {"field_en": "violation_type", "field_cn": "默认信息"}  # VIOLATION: non-TIMEFLAG field with "默认信息"
                ]
            },
            {
                "table_name": "enforcement_officer",
                "last_updated": "2024-12-20",   # OK: within 6 months
                "fields_with_issues": []
            }
        ],
        "uncatalogued_tables": ["illegal_parking_record", "sys_config_params"]
    }
}

submission_file = workspace / "城市综合执法管理系统_共享清单.json"
submission_file.write_text(json.dumps(submission_data, ensure_ascii=False, indent=2), encoding="utf-8")

# Create a minimal stub for the audit script (it exists but agent should use SKILL.md rules)
audit_script_content = '''#!/usr/bin/env python3
"""
Material Review Audit Script
This script processes submission documents for data sharing catalog review.
Run with: python material_review_audit.py --help for usage.
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Material Review Audit")
    parser.add_argument("--submission", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(f"Processing: {args.submission}")
    print("Note: This script requires .docx format inputs. For JSON inputs, apply rules manually per SKILL.md.")
    sys.exit(0)

if __name__ == "__main__":
    main()
'''
scripts_dir.joinpath("material_review_audit.py").write_text(audit_script_content, encoding="utf-8")

# Create reference markdown files (minimal stubs - the real rules are in SKILL.md)
(refs_dir / "field-completeness.md").write_text(
    "# 字段完整性\n\n除备注字段外，所有字段均为必填。\n详见主文档 SKILL.md。\n", encoding="utf-8"
)
(refs_dir / "special-field-rules.md").write_text(
    "# 特殊字段规则\n\n数据增量、中文描述、共享类型的特殊判定规则详见主文档 SKILL.md。\n", encoding="utf-8"
)
(refs_dir / "platform-consistency.md").write_text(
    "# 平台一致性\n\nTIMEFLAG 为系统统一字段，中文名为默认信息时可忽略。其他字段不可忽略。\n详见主文档 SKILL.md。\n", encoding="utf-8"
)
(refs_dir / "issue-template.md").write_text(
    "# 问题清单模板\n\n按「必填缺失 / 规则不符 / 平台不一致 / 待确认」分类输出问题。\n每条问题需包含：位置、现状、规则依据、修正建议。\n", encoding="utf-8"
)

# Additional distractor files in material-review dir
(skill_dir / "README_OLD.md").write_text("# 旧版说明\n此文件已废弃，请参考最新SKILL.md。\n", encoding="utf-8")
(skill_dir / "审核记录_历史.json").write_text(
    json.dumps({"history": [{"date": "2024-09-01", "system": "人社系统", "result": "通过"}]}, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Key file: {submission_file}")
print("Agent must review '城市综合执法管理系统_共享清单.json' and produce 'audit_report.md'")