#!/usr/bin/env python3
"""
Generate the sandbox workspace for the OFD document digitization task.
Creates a realistic OFD file (which is a ZIP containing XML), distractor files,
and the skill scripts at the expected path.
"""
import os
import zipfile
import io
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "incoming_documents/2024/Q1",
    "incoming_documents/2024/Q2",
    "incoming_documents/archive",
    "processed/text",
    "processed/markdown",
    "processed/pdf",
    "reports/monthly",
    "reports/annual",
    "scripts",
    "config",
    "logs",
    "temp",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "incoming_documents/2024/Q1/scan_001.jpg.bak": b"FAKEJPEG_BINARY_DATA_PLACEHOLDER",
    "incoming_documents/2024/Q1/index.csv": "文件名,日期,状态\n公告001.ofd,2024-01-15,待处理\n公告002.pdf,2024-01-18,已处理\n",
    "incoming_documents/2024/Q2/notes.txt": "Q2季度文件待归档，联系张主任确认。\n",
    "incoming_documents/archive/old_format.wps": b"WPS_LEGACY_BINARY",
    "processed/text/sample_old.txt": "这是一个旧版本的文本提取示例，格式可能不完整。\n",
    "processed/pdf/conversion_log.txt": "2024-01-10 PDF转换完成 3个文件\n2024-01-11 PDF转换失败 1个文件\n",
    "reports/monthly/january_report.txt": "一月份归档报告：共处理文件45份，成功43份，失败2份。\n",
    "reports/annual/2023_summary.txt": "2023年度文件归档总结报告\n总计：547份文件\n电子版：423份\n纸质版：124份\n",
    "config/settings.ini": "[archive]\nbase_path=/workspace/incoming_documents\noutput_format=both\nencoding=utf-8\n",
    "logs/conversion.log": "2024-01-15 09:00:01 INFO 开始转换任务\n2024-01-15 09:00:05 ERROR 文件损坏: bad_file.ofd\n2024-01-15 09:01:00 INFO 任务完成\n",
    "temp/session_cache.tmp": "CACHE_V2_SESSION_2024011509001234",
    "config/namespace_map.json": '{"ofd": "http://www.ofdspec.org/2016", "xlink": "http://www.w3.org/1999/xlink"}\n',
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    mode = "wb" if isinstance(content, bytes) else "w"
    enc = None if isinstance(content, bytes) else "utf-8"
    with open(full_path, mode, encoding=enc) as f:
        f.write(content)

# ── Skill scripts (ofd_to_text.py and ofd_to_markdown.py) ───────────────────
# These scripts already exist in the skill workspace per SKILL.md.
# We implement them faithfully according to the SKILL.md specification.

OFD_TO_TEXT_PY = '''\
#!/usr/bin/env python3
"""提取 OFD 文档纯文本内容"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://www.ofdspec.org/2016"

def extract_text(ofd_path):
    ofd_path = Path(ofd_path)
    if not ofd_path.exists():
        print(f"错误：OFD 文件不存在: {ofd_path}", file=sys.stderr)
        sys.exit(1)
    if not zipfile.is_zipfile(ofd_path):
        print(f"错误：文件不是有效的 OFD (ZIP) 格式: {ofd_path}", file=sys.stderr)
        sys.exit(1)

    texts = []
    with zipfile.ZipFile(ofd_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith(".xml"):
                with zf.open(name) as f:
                    try:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        for elem in root.iter(f"{{{NS}}}TextCode"):
                            t = (elem.text or "").strip()
                            if t:
                                texts.append(t)
                        for elem in root.iter(f"{{{NS}}}TextContent"):
                            t = (elem.text or "").strip()
                            if t:
                                texts.append(t)
                    except ET.ParseError:
                        pass
    return "\\n".join(texts)

def main():
    if len(sys.argv) < 2:
        print("用法: python ofd_to_text.py <ofd文件路径> [输出文件]")
        sys.exit(1)
    ofd_path = sys.argv[1]
    text = extract_text(ofd_path)
    if len(sys.argv) >= 3:
        out_path = sys.argv[2]
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"文本已写入: {out_path}")
    else:
        print(text)

if __name__ == "__main__":
    main()
'''

OFD_TO_MARKDOWN_PY = '''\
#!/usr/bin/env python3
"""将 OFD 文档转换为 Markdown 格式"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://www.ofdspec.org/2016"

def is_heading(text):
    """启发式标题检测：短文本、包含特定模式"""
    text = text.strip()
    if not text:
        return False
    # 短文本（少于30字符）且不含句号
    if len(text) <= 30 and "。" not in text and "，" not in text:
        # 以数字编号开头，或全部大写汉字模式
        import re
        if re.match(r"^[一二三四五六七八九十\\d]+[、.．]", text):
            return True
        if re.match(r"^第[一二三四五六七八九十\\d]+[条章节款]", text):
            return True
        if re.match(r"^\\d+\\.\\s", text):
            return True
    return False

def parse_table(table_elem):
    """解析表格元素"""
    rows = []
    for row_elem in table_elem.iter(f"{{{NS}}}Row"):
        cells = []
        for cell_elem in row_elem.iter(f"{{{NS}}}Cell"):
            cell_texts = []
            for tc in cell_elem.iter(f"{{{NS}}}TextCode"):
                t = (tc.text or "").strip()
                if t:
                    cell_texts.append(t)
            cells.append(" ".join(cell_texts))
        if cells:
            rows.append(cells)
    return rows

def extract_markdown(ofd_path):
    ofd_path = Path(ofd_path)
    if not ofd_path.exists():
        print(f"错误：OFD 文件不存在: {ofd_path}", file=sys.stderr)
        sys.exit(1)
    if not zipfile.is_zipfile(ofd_path):
        print(f"错误：文件不是有效的 OFD (ZIP) 格式: {ofd_path}", file=sys.stderr)
        sys.exit(1)

    md_parts = []
    with zipfile.ZipFile(ofd_path, "r") as zf:
        for name in sorted(zf.namelist()):
            if name.endswith(".xml") and "Doc_0" in name:
                with zf.open(name) as f:
                    try:
                        tree = ET.parse(f)
                        root = tree.getroot()

                        # 处理表格
                        for table_elem in root.iter(f"{{{NS}}}Table"):
                            rows = parse_table(table_elem)
                            if rows:
                                # 构建 Markdown 表格
                                max_cols = max(len(r) for r in rows)
                                header = rows[0]
                                # 补齐列数
                                header += [""] * (max_cols - len(header))
                                md_parts.append("| " + " | ".join(header) + " |")
                                md_parts.append("| " + " | ".join(["---"] * max_cols) + " |")
                                for row in rows[1:]:
                                    row += [""] * (max_cols - len(row))
                                    md_parts.append("| " + " | ".join(row) + " |")
                                md_parts.append("")

                        # 处理段落
                        for para_elem in root.iter(f"{{{NS}}}Paragraph"):
                            texts = []
                            for tc in para_elem.iter(f"{{{NS}}}TextCode"):
                                t = (tc.text or "").strip()
                                if t:
                                    texts.append(t)
                            combined = "".join(texts)
                            if not combined:
                                continue
                            if is_heading(combined):
                                md_parts.append(f"## {combined}")
                            else:
                                md_parts.append(combined)
                            md_parts.append("")

                        # 如果没有 Paragraph，退回到 TextCode
                        paragraphs_found = list(root.iter(f"{{{NS}}}Paragraph"))
                        if not paragraphs_found:
                            for tc in root.iter(f"{{{NS}}}TextCode"):
                                t = (tc.text or "").strip()
                                if t:
                                    if is_heading(t):
                                        md_parts.append(f"## {t}")
                                    else:
                                        md_parts.append(t)
                                    md_parts.append("")

                    except ET.ParseError:
                        pass

    return "\\n".join(md_parts)

def main():
    if len(sys.argv) < 2:
        print("用法: python ofd_to_markdown.py <ofd文件路径> [输出文件]")
        sys.exit(1)
    ofd_path = sys.argv[1]
    md = extract_markdown(ofd_path)
    if len(sys.argv) >= 3:
        out_path = sys.argv[2]
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Markdown 已写入: {out_path}")
    else:
        print(md)

if __name__ == "__main__":
    main()
'''

INSTALL_DEPS_PY = '''\
#!/usr/bin/env python3
"""安装可选依赖"""
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml",
                       "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
print("依赖安装完成")
'''

scripts = {
    "scripts/ofd_to_text.py": OFD_TO_TEXT_PY,
    "scripts/ofd_to_markdown.py": OFD_TO_MARKDOWN_PY,
    "scripts/install_dependencies.py": INSTALL_DEPS_PY,
}
for rel, content in scripts.items():
    p = os.path.join(WORKSPACE, rel)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

# ── Build the actual OFD file ────────────────────────────────────────────────
# OFD is a ZIP with:
#   OFD.xml           (document manifest)
#   Doc_0/Document.xml  (content pages)
#   Doc_0/Pages/Page_0/Content.xml  (actual text/table content)

NS_OFD = "http://www.ofdspec.org/2016"

OFD_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<ofd:OFD xmlns:ofd="http://www.ofdspec.org/2016" Version="1.0" DocType="OFD">
  <ofd:DocBody>
    <ofd:DocInfo>
      <ofd:DocID>DOC-2024-PROCUREMENT-001</ofd:DocID>
      <ofd:Title>2024年度政府采购公告</ofd:Title>
      <ofd:Author>政府采购管理办公室</ofd:Author>
      <ofd:CreationDate>2024-03-15</ofd:CreationDate>
    </ofd:DocInfo>
    <ofd:DocRoot>Doc_0/Document.xml</ofd:DocRoot>
  </ofd:DocBody>
</ofd:OFD>
'''

DOCUMENT_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<ofd:Document xmlns:ofd="http://www.ofdspec.org/2016">
  <ofd:CommonData>
    <ofd:PageArea>
      <ofd:PhysicalBox>0 0 210 297</ofd:PhysicalBox>
    </ofd:PageArea>
  </ofd:CommonData>
  <ofd:Pages>
    <ofd:Page ID="1" BaseLoc="Pages/Page_0/Content.xml"/>
  </ofd:Pages>
</ofd:Document>
'''

CONTENT_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<ofd:Page xmlns:ofd="http://www.ofdspec.org/2016">
  <ofd:Content>
    <ofd:Layer ID="1">

      <ofd:Paragraph>
        <ofd:TextObject ID="1" Font="1" Size="16">
          <ofd:TextCode>2024年度政府采购公告</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="2" Font="1" Size="12">
          <ofd:TextCode>第一条 采购目的</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="3" Font="1" Size="10">
          <ofd:TextCode>根据《中华人民共和国政府采购法》及相关法规，本办公室决定就2024年度办公设备及耗材采购项目面向社会公开招标。本次采购旨在满足各部门日常办公需求，提升行政效率，降低采购成本。</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="4" Font="1" Size="12">
          <ofd:TextCode>第二条 采购范围</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="5" Font="1" Size="10">
          <ofd:TextCode>本次采购范围包括：打印机、复印机、扫描仪及相关耗材，具体品目及数量见附件采购清单。采购预算总额为人民币壹佰伍拾万元整（¥1,500,000.00）。</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Table ID="10">
        <ofd:Row>
          <ofd:Cell>
            <ofd:TextObject ID="11" Font="1" Size="10">
              <ofd:TextCode>品目编号</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="12" Font="1" Size="10">
              <ofd:TextCode>品目名称</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="13" Font="1" Size="10">
              <ofd:TextCode>数量</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="14" Font="1" Size="10">
              <ofd:TextCode>预算单价（元）</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
        </ofd:Row>
        <ofd:Row>
          <ofd:Cell>
            <ofd:TextObject ID="21" Font="1" Size="10">
              <ofd:TextCode>A001</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="22" Font="1" Size="10">
              <ofd:TextCode>激光打印机</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="23" Font="1" Size="10">
              <ofd:TextCode>50台</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="24" Font="1" Size="10">
              <ofd:TextCode>3500</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
        </ofd:Row>
        <ofd:Row>
          <ofd:Cell>
            <ofd:TextObject ID="31" Font="1" Size="10">
              <ofd:TextCode>A002</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="32" Font="1" Size="10">
              <ofd:TextCode>彩色复印机</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="33" Font="1" Size="10">
              <ofd:TextCode>20台</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="34" Font="1" Size="10">
              <ofd:TextCode>28000</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
        </ofd:Row>
        <ofd:Row>
          <ofd:Cell>
            <ofd:TextObject ID="41" Font="1" Size="10">
              <ofd:TextCode>A003</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="42" Font="1" Size="10">
              <ofd:TextCode>高速扫描仪</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="43" Font="1" Size="10">
              <ofd:TextCode>15台</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
          <ofd:Cell>
            <ofd:TextObject ID="44" Font="1" Size="10">
              <ofd:TextCode>12000</ofd:TextCode>
            </ofd:TextObject>
          </ofd:Cell>
        </ofd:Row>
      </ofd:Table>

      <ofd:Paragraph>
        <ofd:TextObject ID="50" Font="1" Size="12">
          <ofd:TextCode>第三条 投标要求</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="51" Font="1" Size="10">
          <ofd:TextCode>投标单位须具备合法经营资质，在中华人民共和国境内注册，具有良好的商业信誉和健全的财务制度。投标截止日期为2024年4月30日17时00分，逾期不予受理。</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="52" Font="1" Size="10">
          <ofd:TextCode>政府采购管理办公室</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

      <ofd:Paragraph>
        <ofd:TextObject ID="53" Font="1" Size="10">
          <ofd:TextCode>2024年3月15日</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Paragraph>

    </ofd:Layer>
  </ofd:Content>
</ofd:Page>
'''

# Build the OFD zip in memory then write to disk
ofd_buffer = io.BytesIO()
with zipfile.ZipFile(ofd_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("OFD.xml", OFD_XML.encode("utf-8"))
    zf.writestr("Doc_0/Document.xml", DOCUMENT_XML.encode("utf-8"))
    zf.writestr("Doc_0/Pages/Page_0/Content.xml", CONTENT_XML.encode("utf-8"))

ofd_target = os.path.join(WORKSPACE, "incoming_documents/2024/Q1/procurement_notice_2024.ofd")
with open(ofd_target, "wb") as f:
    f.write(ofd_buffer.getvalue())

print(f"Workspace generated at {WORKSPACE}")
print(f"OFD file: {ofd_target}")
print(f"Scripts: {list(scripts.keys())}")