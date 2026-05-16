import os
import random

random.seed(42)

# Create directory structure
dirs = [
    "workspace",
    "workspace/tools",
    "workspace/docs",
    "workspace/docs/drafts",
    "workspace/docs/archive",
    "workspace/assets",
    "workspace/assets/images",
    "workspace/assets/templates",
    "workspace/scripts",
    "workspace/output",
    "workspace/config",
    "workspace/tests",
    "workspace/tests/fixtures",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# === Create the bespoke tools/md2docx.py ===
md2docx_code = '''\
"""
md2docx: Two-stage Markdown to Word document converter.

Stage 1: Pandoc converts Markdown to .docx
Stage 2: python-docx post-processing for Chinese fonts and table borders
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("ERROR: python-docx is not installed. Run: pip install python-docx")
    sys.exit(1)


def _set_cell_border(cell, **kwargs):
    """
    Set cell border for a table cell.

    Args:
        cell: The table cell to set borders on.
        **kwargs: Border sides (top, bottom, left, right) with border properties.
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("left", "top", "right", "bottom", "insideH", "insideV"):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = "w:{}".format(edge)
            element = OxmlElement(tag)
            for key in ["sz", "val", "color", "space", "shadow"]:
                if key in edge_data:
                    element.set(qn("w:{}".format(key)), edge_data[key])
            tcBorders.append(element)
    tcPr.append(tcBorders)


def _add_table_borders(document: Document) -> None:
    """
    Add borders to all tables in the document.

    Args:
        document: The python-docx Document object to process.
    """
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                _set_cell_border(
                    cell,
                    top={"val": "single", "sz": "4", "color": "000000"},
                    bottom={"val": "single", "sz": "4", "color": "000000"},
                    left={"val": "single", "sz": "4", "color": "000000"},
                    right={"val": "single", "sz": "4", "color": "000000"},
                )


def _set_chinese_fonts(document: Document) -> None:
    """
    Set Chinese fonts for all paragraphs in the document.
    Uses Microsoft YaHei for headings and SimSun for body text.

    Args:
        document: The python-docx Document object to process.
    """
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Microsoft YaHei"
            # Set East Asian font via XML
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                rPr.insert(0, rFonts)
            rFonts.set(qn("w:eastAsia"), "SimSun")
            rFonts.set(qn("w:ascii"), "Microsoft YaHei")
            rFonts.set(qn("w:hAnsi"), "Microsoft YaHei")


def convert_md_to_docx(
    input_file: str,
    output_file: str,
    template: Optional[str] = None,
    reference_docx: Optional[str] = None,
) -> None:
    """
    Convert a Markdown file to Word document using two-stage pipeline.

    Stage 1: Pandoc converts Markdown to .docx
    Stage 2: python-docx post-processes fonts and table borders

    Args:
        input_file: Path to the input Markdown file (must be UTF-8 encoded).
        output_file: Path to the output Word document (.docx).
        template: Optional path to a Word template file.
        reference_docx: Optional path to a reference .docx for styles.

    Raises:
        FileNotFoundError: If input_file does not exist.
        RuntimeError: If Pandoc conversion fails.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}\\n"
            f"Suggestion: Check the file path and ensure the file exists."
        )

    # Stage 1: Pandoc conversion
    cmd = ["pandoc", str(input_path), "-o", str(output_file), "--from=markdown", "--to=docx"]

    if reference_docx:
        cmd += [f"--reference-doc={reference_docx}"]
    elif template:
        cmd += [f"--reference-doc={template}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Pandoc conversion failed.\\n"
            f"Command: {' '.join(cmd)}\\n"
            f"Error: {e.stderr}\\n"
            f"Suggestion: Ensure Pandoc >= 2.0 is installed and the input file is valid Markdown."
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Pandoc not found. Please install Pandoc >= 2.0.\\n"
            "Suggestion: Visit https://pandoc.org/installing.html for installation instructions."
        )

    # Stage 2: python-docx post-processing
    document = Document(output_file)
    _add_table_borders(document)
    _set_chinese_fonts(document)
    document.save(output_file)


def main() -> None:
    """CLI entry point for md2docx converter."""
    if len(sys.argv) < 3:
        print("Usage: python md2docx.py <input.md> <output.docx> [--template=<template.docx>]")
        print("       python md2docx.py <input.md> <output.docx> [--reference-docx=<ref.docx>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    template = None
    reference_docx = None

    for arg in sys.argv[3:]:
        if arg.startswith("--template="):
            template = arg.split("=", 1)[1]
        elif arg.startswith("--reference-docx="):
            reference_docx = arg.split("=", 1)[1]

    try:
        convert_md_to_docx(input_file, output_file, template=template, reference_docx=reference_docx)
        print(f"Successfully converted '{input_file}' to '{output_file}'")
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open("workspace/tools/md2docx.py", "w", encoding="utf-8") as f:
    f.write(md2docx_code)

with open("workspace/tools/__init__.py", "w", encoding="utf-8") as f:
    f.write("")

# === Create the complex Markdown input file ===
spec_md = """\
# 智能仓储管理系统 产品规格说明书

## 1. 产品概述

本文档描述**智能仓储管理系统 (IWMS) v3.2** 的技术规格与功能需求。
系统采用分布式微服务架构，支持*高并发*和*高可用*部署场景。

## 2. 系统架构

### 2.1 核心组件

系统由以下六个核心组件构成：

#### 2.1.1 数据采集层

负责从各类传感器和 RFID 设备采集实时数据。

#### 2.1.2 数据处理层

对原始数据进行清洗、转换和聚合处理。

##### 2.1.2.1 批处理模块

适用于历史数据分析和报表生成。

###### 2.1.2.1.1 调度策略

支持 Cron 表达式配置定时任务。

### 2.2 技术栈

系统依赖以下技术组件：

1. **后端框架**: Spring Boot 3.1 + Spring Cloud
2. **数据库**: PostgreSQL 15 (主库) + Redis 7.0 (缓存)
3. **消息队列**: Apache Kafka 3.4
4. **容器化**: Docker + Kubernetes 1.27
5. **监控**: Prometheus + Grafana

## 3. 功能模块

### 3.1 库存管理

- 实时库存盘点
- 入库/出库操作记录
- 批次追踪与过期预警
- 自动补货触发机制
  - 基于最低库存阈值
  - 基于历史消耗预测
  - 基于季节性调整因子

### 3.2 性能指标对比

| 指标 | v2.x | v3.2 | 提升幅度 |
|------|------|------|----------|
| 并发处理能力 (TPS) | 5,000 | 50,000 | 10x |
| 平均响应时间 (ms) | 120 | 18 | 85% ↓ |
| 数据存储容量 (TB) | 10 | 500 | 50x |
| 系统可用性 (SLA) | 99.5% | 99.99% | +0.49% |
| 故障恢复时间 (RTO) | 4h | 15min | 94% ↓ |

### 3.3 API 接口规范

核心 RESTful API 端点如下：

```python
# 库存查询接口示例
import requests

def query_inventory(sku_id: str, warehouse_id: str) -> dict:
    url = f"https://api.iwms.internal/v3/inventory/{sku_id}"
    params = {"warehouse": warehouse_id, "include_reserved": True}
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()
```

### 3.4 部署要求

#### 3.4.1 最低硬件规格

| 节点类型 | CPU | 内存 | 存储 |
|----------|-----|------|------|
| 主控节点 | 16 核 | 64 GB | 2 TB SSD |
| 数据节点 | 8 核 | 32 GB | 10 TB HDD |
| 边缘节点 | 4 核 | 8 GB | 500 GB SSD |

## 4. 安全规范

> **重要提示**: 所有 API 调用必须使用 mTLS 双向认证。
> 密钥轮换周期不得超过 **90 天**。
> 违反安全规范将导致合规审计不通过。

### 4.1 访问控制矩阵

| 角色 | 读取 | 写入 | 删除 | 管理 |
|------|------|------|------|------|
| 操作员 | ✓ | ✓ | ✗ | ✗ |
| 主管 | ✓ | ✓ | ✓ | ✗ |
| 管理员 | ✓ | ✓ | ✓ | ✓ |
| 审计员 | ✓ | ✗ | ✗ | ✗ |

## 5. 变更记录

1. **v3.2.0** - 引入分布式锁机制，解决并发写冲突
2. **v3.1.5** - 优化查询性能，引入索引覆盖策略
3. **v3.0.0** - 架构重构，迁移至微服务体系
"""

with open("workspace/docs/drafts/product_spec_v3.2.md", "w", encoding="utf-8") as f:
    f.write(spec_md)

# === Distractor files ===

# Old archive markdown (not the target)
old_spec = """\
# 旧版规格文档 v1.0
这是已废弃的规格文档，请勿使用。
"""
with open("workspace/docs/archive/product_spec_v1.md", "w", encoding="utf-8") as f:
    f.write(old_spec)

# A broken JSON config
with open("workspace/config/app_config.json", "w", encoding="utf-8") as f:
    f.write('{"database": "postgresql", "port": 5432, "debug": true,}')  # intentionally broken

# A requirements.txt distractor
with open("workspace/config/requirements.txt", "w", encoding="utf-8") as f:
    f.write("flask==2.3.0\nrequests==2.31.0\nnumpy==1.26.0\n")

# Some random scripts
with open("workspace/scripts/data_cleanup.py", "w", encoding="utf-8") as f:
    f.write("# Data cleanup script\nimport os\nprint('cleanup')\n")

with open("workspace/scripts/deploy.sh", "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\necho 'Deploying application...'\n")

# Fixture files for tests
with open("workspace/tests/fixtures/sample_data.csv", "w", encoding="utf-8") as f:
    f.write("sku,qty,warehouse\nA001,100,WH01\nB002,50,WH02\n")

with open("workspace/tests/fixtures/test_config.yaml", "w", encoding="utf-8") as f:
    f.write("test_mode: true\nverbose: false\ntimeout: 30\n")

# A misleading .docx-like file (actually just text)
with open("workspace/docs/archive/old_report.txt", "w", encoding="utf-8") as f:
    f.write("This is an old report in plain text format.\n")

# Assets placeholder
with open("workspace/assets/templates/placeholder.txt", "w", encoding="utf-8") as f:
    f.write("Place Word templates here.\n")

with open("workspace/assets/images/placeholder.txt", "w", encoding="utf-8") as f:
    f.write("Place image assets here.\n")

# Output directory placeholder
with open("workspace/output/.gitkeep", "w", encoding="utf-8") as f:
    f.write("")

# Another distractor markdown
with open("workspace/docs/drafts/meeting_notes.md", "w", encoding="utf-8") as f:
    f.write("# 会议纪要\n## 2026-03-15\n- 讨论了新版本发布计划\n- 确认了测试时间表\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs, files in os.walk("workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")