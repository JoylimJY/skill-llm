import os
import json
from pathlib import Path

WORKSPACE = Path("/workspace")

# ─── KB Directory Structure ───────────────────────────────────────────────────

kb_products = {
    "CDSS系统": {
        "filename": "CDSS-标准单产品硬件资源测算.md",
        "elements": ["年门诊人次", "年出院人次", "医护人员总数"]
    },
    "VTE系统": {
        "filename": "VTE-标准单产品硬件资源测算.md",
        "elements": ["年出院人次", "外科床位数", "ICU床位数", "医护人员总数"]
    },
    "病历质控系统": {
        "filename": "病历质控-标准单产品硬件资源测算.md",
        "elements": ["年门诊人次", "年出院人次", "医护人员总数"]
    },
    "单病种系统": {
        "filename": "单病种-标准单产品硬件资源测算.md",
        "elements": ["年出院人次", "单病种病种数量", "医护人员总数"]
    },
    "智医助理-基层人工智能辅助诊疗系统": {
        "filename": "智医助理-标准单产品硬件资源测算.md",
        "elements": ["日均门诊量", "接入科室数量", "医护人员总数", "历史病历数据量"]
    },
}

def make_md_content(product_display_name: str, elements: list[str]) -> str:
    numbered = "\n".join(f"{i+1}. {e}" for i, e in enumerate(elements))
    return f"""# {product_display_name} 标准单产品硬件资源测算

## 概述

本文档描述了 {product_display_name} 的标准硬件资源测算方法，用于指导项目实施阶段的服务器资源规划。

## 适用范围

适用于医疗机构部署 {product_display_name} 时的硬件资源预估。

## 服务器资源评估输入项

{numbered}

## 服务器配置建议

根据以上输入项，参考标准配置表进行测算。

### 最低配置

| 资源类型 | 规格 |
|----------|------|
| CPU      | 8核  |
| 内存     | 32GB |
| 存储     | 500GB |

### 推荐配置

| 资源类型 | 规格  |
|----------|-------|
| CPU      | 16核  |
| 内存     | 64GB  |
| 存储     | 2TB   |

## 备注

实际资源配置需根据医院具体规模和业务量进行调整。
"""

# ─── Create KB files ──────────────────────────────────────────────────────────

for product_dir, info in kb_products.items():
    product_path = WORKSPACE / "kb" / product_dir
    product_path.mkdir(parents=True, exist_ok=True)
    
    md_file = product_path / info["filename"]
    md_file.write_text(make_md_content(product_dir, info["elements"]), encoding="utf-8")

# ─── Create the compare_elements.py script ───────────────────────────────────

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

compare_script = scripts_dir / "compare_elements.py"
compare_script.write_text(r'''#!/usr/bin/env python3
"""
compare_elements.py - Compare provided evaluation elements against standard requirements.
Usage: python3 scripts/compare_elements.py '<json_input>'
"""

import sys
import json
import os
import re
from pathlib import Path


def normalize(text: str) -> str:
    """Normalize text for comparison: strip spaces, lowercase."""
    return re.sub(r'\s+', '', text).lower()


def find_product_file(product_name: str, kb_dir: str) -> Path | None:
    """Find the standard resource calculation file for a given product."""
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        return None
    
    norm_product = normalize(product_name)
    
    for subdir in kb_path.iterdir():
        if not subdir.is_dir():
            continue
        norm_dir = normalize(subdir.name)
        # Support fuzzy matching: product name is contained in directory name or vice versa
        if norm_product in norm_dir or norm_dir in norm_product:
            # Find the standard calculation file
            for f in subdir.glob("*标准单产品硬件资源测算.md"):
                return f
    
    return None


def extract_required_elements(md_file: Path) -> list[str]:
    """Extract numbered items from the '服务器资源评估输入项' section."""
    content = md_file.read_text(encoding="utf-8")
    
    # Find the section
    section_pattern = re.compile(
        r'##\s*服务器资源评估输入项\s*\n(.*?)(?=\n##|\Z)',
        re.DOTALL
    )
    match = section_pattern.search(content)
    if not match:
        return []
    
    section_text = match.group(1)
    
    # Extract numbered items
    items = re.findall(r'^\d+\.\s+(.+)$', section_text, re.MULTILINE)
    return [item.strip() for item in items]


def check_element_satisfied(required: str, provided_list: list[str]) -> bool:
    """Check if a required element is satisfied by any item in the provided list."""
    norm_required = normalize(required)
    for provided in provided_list:
        norm_provided = normalize(provided)
        # Partial match: required element name is contained in provided value
        if norm_required in norm_provided or norm_provided in norm_required:
            return True
    return False


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No input provided"}))
        sys.exit(1)
    
    try:
        input_data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
    
    product = input_data.get("product", "")
    provided_elements = input_data.get("provided_elements", [])
    kb_dir = input_data.get("kb_dir", "/Users/hushuai/.openclaw/workspace-ClinicalManager/kb")
    
    # Find product file
    md_file = find_product_file(product, kb_dir)
    if md_file is None:
        print(json.dumps({
            "status": "error",
            "message": f"Product file not found for: {product}",
            "details": {"satisfied": [], "missing": [], "is_complete": False}
        }))
        sys.exit(1)
    
    # Extract required elements
    required_elements = extract_required_elements(md_file)
    if not required_elements:
        print(json.dumps({
            "status": "error",
            "message": "No evaluation elements found in product file",
            "details": {"satisfied": [], "missing": [], "is_complete": False}
        }))
        sys.exit(1)
    
    # Compare
    satisfied = []
    missing = []
    for req in required_elements:
        if check_element_satisfied(req, provided_elements):
            satisfied.append(req)
        else:
            missing.append(req)
    
    is_complete = len(missing) == 0
    
    if is_complete:
        result = {
            "status": "ok",
            "message": "ok",
            "details": {
                "satisfied": satisfied,
                "missing": [],
                "is_complete": True
            }
        }
    else:
        missing_str = "、".join(missing)
        result = {
            "status": "missing",
            "message": f"缺少的评估要点：{missing_str}",
            "details": {
                "satisfied": satisfied,
                "missing": missing,
                "is_complete": False
            }
        }
    
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
''', encoding="utf-8")

compare_script.chmod(0o755)

# ─── Distractor files ─────────────────────────────────────────────────────────

# Old assessment forms (distractors)
old_forms_dir = WORKSPACE / "legacy" / "old_assessment_forms"
old_forms_dir.mkdir(parents=True, exist_ok=True)

(old_forms_dir / "2022_CDSS_assessment_draft.txt").write_text(
    "旧版CDSS评估表（2022年）\n年门诊人次：8万\n年出院人次：3000\n（此版本已废弃）\n", encoding="utf-8"
)

(old_forms_dir / "2021_VTE_initial_requirements.txt").write_text(
    "VTE系统初期需求（2021年）\n外科床位数：150\n（此版本已废弃）\n", encoding="utf-8"
)

# Project documents (distractors)
project_docs_dir = WORKSPACE / "projects" / "2024_deployments"
project_docs_dir.mkdir(parents=True, exist_ok=True)

(project_docs_dir / "deployment_schedule.txt").write_text(
    "2024年部署计划\nQ1: CDSS系统 - 某三甲医院\nQ2: VTE系统 - 某二甲医院\nQ3: 单病种系统 - 某专科医院\n",
    encoding="utf-8"
)

(project_docs_dir / "client_contact_list.csv").write_text(
    "客户名称,联系人,电话\n某三甲医院,张主任,13800138000\n某二甲医院,李院长,13900139000\n",
    encoding="utf-8"
)

# Meeting notes (distractors)
meetings_dir = WORKSPACE / "internal" / "meetings" / "2024"
meetings_dir.mkdir(parents=True, exist_ok=True)

(meetings_dir / "2024_03_15_sales_meeting.md").write_text(
    "# 2024-03-15 销售会议记录\n\n## 议题\n- VTE系统推进情况\n- 新客户开拓\n\n## 结论\n- 下周跟进评估要点收集\n",
    encoding="utf-8"
)

(meetings_dir / "2024_04_20_technical_review.md").write_text(
    "# 技术评审会议\n\n## 单病种系统优化讨论\n\n建议增加对历史数据的分析维度。\n",
    encoding="utf-8"
)

# Fake/outdated KB files (distractors - in wrong location)
fake_kb_dir = WORKSPACE / "archive" / "kb_backup_2023"
fake_kb_dir.mkdir(parents=True, exist_ok=True)

(fake_kb_dir / "VTE-旧版评估.md").write_text(
    "# VTE旧版评估（2023年，已废弃）\n## 服务器资源评估输入项\n1. 年出院人次\n2. 外科床位数\n（旧版，请勿使用）\n",
    encoding="utf-8"
)

# Temp files (distractors)
temp_dir = WORKSPACE / "tmp"
temp_dir.mkdir(parents=True, exist_ok=True)

(temp_dir / "scratch_notes.txt").write_text(
    "临时笔记：\n- 记得更新VTE文件\n- 单病种系统需要确认病种数量\n",
    encoding="utf-8"
)

(temp_dir / "test_run_20240301.json").write_text(
    json.dumps({"product": "CDSS系统", "result": "ok", "date": "2024-03-01"}, ensure_ascii=False),
    encoding="utf-8"
)

# Config files (distractors)
config_dir = WORKSPACE / "config"
config_dir.mkdir(parents=True, exist_ok=True)

(config_dir / "app_config.json").write_text(
    json.dumps({
        "kb_default_path": "/Users/hushuai/.openclaw/workspace-ClinicalManager/kb",
        "supported_products": ["CDSS系统", "VTE系统", "病历质控系统", "单病种系统", "智医助理-基层人工智能辅助诊疗系统"],
        "version": "1.2.0"
    }, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# ─── The actual task input file ───────────────────────────────────────────────
# This is the "client submission" that the agent needs to validate

client_submission = WORKSPACE / "incoming" / "client_hw_assessment_submission.txt"
client_submission.parent.mkdir(parents=True, exist_ok=True)

client_submission.write_text(
    """硬件资源评估要点提交单
提交日期：2024-05-10
销售负责人：王工

===== 客户A：某三甲医院 =====
产品：单病种系统
已提供评估要点：
- 年出院人次：18000人次
- 单病种病种数量：25个病种
- 医护人员总数：850人

===== 客户B：某二甲医院 =====
产品：VTE系统
已提供评估要点：
- 年出院人次：6500人次
- 外科床位数：120张

===== 备注 =====
请尽快完成核查，下周五前需要出具服务器配置方案。
""",
    encoding="utf-8"
)

print("Workspace setup complete.")
print(f"  KB products: {list(kb_products.keys())}")
print(f"  Client submission: {client_submission}")
print(f"  Scripts: {compare_script}")