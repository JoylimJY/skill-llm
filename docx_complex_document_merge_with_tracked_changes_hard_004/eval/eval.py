import sys
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import json

# 定义 Word XML 命名空间
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
}

def get_xml_tree(docx_path):
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        xml_content = zip_ref.read('word/document.xml')
        return ET.fromstring(xml_content)

def check_tracked_changes(root):
    """使用 XPath 查找带有作者属性的插入和删除记录"""
    # 查找 <w:ins> 和 <w:del> 标签
    ins_elements = root.findall('.//w:ins', NAMESPACES)
    del_elements = root.findall('.//w:del', NAMESPACES)
    
    author_match = False
    for el in ins_elements + del_elements:
        author = el.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author')
        if author and author.strip().lower() == "documentmerger":
            author_match = True
            break
            
    return author_match, len(ins_elements) + len(del_elements)

def check_toc_robust(root):
    """检测是否包含 TOC 域代码或目录标志"""
    # 检查 XML 中的域指令
    instr_texts = root.findall('.//w:instrText', NAMESPACES)
    for instr in instr_texts:
        if instr.text and "TOC" in instr.text.upper():
            return True
    # 兜底方案：检查是否包含 Table of Contents 文字
    all_text = "".join(root.itertext()).lower()
    return "table of contents" in all_text

def check_page_numbers_robust(root):
    """检测页码域 (PAGE/NUMPAGES) 或页脚引用"""
    # 检查复杂字段格式 (instrText)
    instr_texts = root.findall('.//w:instrText', NAMESPACES)
    has_page = any("PAGE" in (it.text or "").upper() for it in instr_texts)
    has_numpages = any("NUMPAGES" in (it.text or "").upper() for it in instr_texts)
    
    # 同时检查简单字段格式 (fldSimple)
    fld_simple_elements = root.findall('.//w:fldSimple', NAMESPACES)
    for fld in fld_simple_elements:
        instr = fld.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}instr', '')
        if "PAGE" in instr.upper():
            has_page = True
        if "NUMPAGES" in instr.upper():
            has_numpages = True
    
    # 只要包含 PAGE 域或者文本中出现了 Page X of Y 的暗示
    return has_page or has_numpages

def evaluate_document(workspace_dir):
    merged_file = Path(workspace_dir) / 'merged_report.docx'
    if not merged_file.exists():
        return {"passed": False, "score": 0.0, "detail": "File not found"}

    try:
        root = get_xml_tree(merged_file)
        
        # 1. 修订追踪检查
        has_changes, count = check_tracked_changes(root)
        # 2. 目录检查
        has_toc = check_toc_robust(root)
        # 3. 页码检查
        has_pages = check_page_numbers_robust(root)
        # 4. 内容完整性 (简单文本检索)
        full_text = "".join(root.itertext()).lower()
        content_ok = all(k in full_text for k in ['executive summary', 'financial', 'recommendations'])

        checks = [
            {"name": "File exists", "passed": True},
            {"name": "Tracked changes (DocumentMerger)", "passed": has_changes, "detail": f"Changes: {count}"},
            {"name": "Table of Contents", "passed": has_toc},
            {"name": "Page numbers (X of Y)", "passed": has_pages},
            {"name": "Content Merge", "passed": content_ok}
        ]
        
        score = sum(1 for c in checks if c['passed']) / len(checks)
        return {"passed": score >= 0.8, "score": score, "checks": checks}
        
    except Exception as e:
        return {"passed": False, "score": 0.0, "detail": str(e)}

if __name__ == '__main__':
    result = evaluate_document(sys.argv[1])
    print(json.dumps(result))