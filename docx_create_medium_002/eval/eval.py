import sys
import os
import zipfile
import json
from lxml import etree

def find_docx(workspace):
    candidates = []
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if f.lower().endswith('.docx'):
                candidates.append(os.path.join(root, f))
    # prefer report.docx
    for c in candidates:
        if 'report' in os.path.basename(c).lower():
            return c
    return candidates[0] if candidates else None

def get_xml(docx_path, member):
    with zipfile.ZipFile(docx_path) as z:
        if member in z.namelist():
            return z.read(member)
    return None

def parse_xml(data):
    if data is None:
        return None
    try:
        return etree.fromstring(data)
    except Exception:
        return None

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
}

def get_all_text(element):
    texts = []
    for t in element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            texts.append(t.text)
    return ' '.join(texts)

def get_all_text_flat(root):
    all_text = ''
    for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            all_text += t.text + ' '
    return all_text.lower()

def main():
    workspace = sys.argv[1]
    checks = []

    docx_path = find_docx(workspace)
    if not docx_path:
        checks.append({'name': 'file_exists', 'passed': False, 'detail': 'No .docx file found in workspace'})
        score = 0.0
        print(json.dumps({'passed': False, 'score': score, 'checks': checks}))
        return

    checks.append({'name': 'file_exists', 'passed': True, 'detail': f'Found: {os.path.basename(docx_path)}'})

    # Check it's a valid zip
    try:
        with zipfile.ZipFile(docx_path) as z:
            names = z.namelist()
        valid_zip = True
    except Exception as e:
        valid_zip = False
        names = []

    checks.append({'name': 'valid_docx_zip', 'passed': valid_zip, 'detail': 'File is a valid ZIP/DOCX' if valid_zip else 'File is not a valid ZIP'})

    if not valid_zip:
        score = sum(1 for c in checks if c['passed']) / len(checks)
        print(json.dumps({'passed': False, 'score': score, 'checks': checks}))
        return

    doc_xml_data = get_xml(docx_path, 'word/document.xml')
    root = parse_xml(doc_xml_data)

    all_text = get_all_text_flat(root) if root is not None else ''

    # Check US Letter page size in document settings
    page_size_ok = False
    if root is not None:
        # Look for pgSz elements
        for pgSz in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pgSz'):
            w_attr = pgSz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
            h_attr = pgSz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}h')
            if w_attr and h_attr:
                try:
                    w_val = int(w_attr)
                    h_val = int(h_attr)
                    # US Letter: 12240 x 15840 (allow small tolerance)
                    if abs(w_val - 12240) <= 20 and abs(h_val - 15840) <= 20:
                        page_size_ok = True
                except ValueError:
                    pass
    checks.append({'name': 'us_letter_page_size', 'passed': page_size_ok, 'detail': 'Page size is US Letter (12240x15840 DXA)' if page_size_ok else 'Page size is not US Letter'})

    # Check title 'Q3 2024 Business Report'
    title_ok = 'q3 2024 business report' in all_text
    checks.append({'name': 'title_text', 'passed': title_ok, 'detail': 'Title text found' if title_ok else 'Title text not found'})

    # Check subtitle
    subtitle_ok = 'finance department' in all_text
    checks.append({'name': 'subtitle_text', 'passed': subtitle_ok, 'detail': 'Subtitle with Finance Department found' if subtitle_ok else 'Subtitle not found'})

    # Check date
    date_ok = 'october 15, 2024' in all_text or 'october 15 2024' in all_text
    checks.append({'name': 'date_text', 'passed': date_ok, 'detail': 'Date text found' if date_ok else 'Date text not found'})

    # Check headings
    exec_summary_ok = 'executive summary' in all_text
    checks.append({'name': 'heading_executive_summary', 'passed': exec_summary_ok, 'detail': 'Executive Summary heading found' if exec_summary_ok else 'Not found'})

    key_metrics_ok = 'key metrics' in all_text
    checks.append({'name': 'heading_key_metrics', 'passed': key_metrics_ok, 'detail': 'Key Metrics heading found' if key_metrics_ok else 'Not found'})

    action_items_ok = 'action items' in all_text
    checks.append({'name': 'heading_action_items', 'passed': action_items_ok, 'detail': 'Action Items heading found' if action_items_ok else 'Not found'})

    # Check revenue paragraph
    revenue_ok = 'revenue increased' in all_text and '12%' in all_text
    checks.append({'name': 'revenue_paragraph', 'passed': revenue_ok, 'detail': 'Revenue paragraph found' if revenue_ok else 'Not found'})

    # Check table content
    table_ok = False
    total_revenue_ok = '$4.2m' in all_text or '4.2m' in all_text
    new_customers_ok = '127' in all_text
    retention_ok = '94%' in all_text
    table_ok = total_revenue_ok and new_customers_ok and retention_ok
    checks.append({'name': 'table_data_rows', 'passed': table_ok, 'detail': 'Table data rows found' if table_ok else f'Missing: revenue={total_revenue_ok}, customers={new_customers_ok}, retention={retention_ok}'})

    # Check table header shading
    shading_ok = False
    if root is not None:
        for shd in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd'):
            fill = shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill', '')
            if fill.upper() == 'D5E8F0':
                shading_ok = True
                break
    checks.append({'name': 'table_header_shading', 'passed': shading_ok, 'detail': 'Table header shading D5E8F0 found' if shading_ok else 'Header shading not found'})

    # Check table uses DXA width (not percentage)
    table_width_ok = False
    if root is not None:
        for tbl in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl'):
            for tblW in tbl.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblW'):
                type_attr = tblW.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', '')
                w_attr = tblW.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w', '')
                if type_attr.lower() == 'dxa':
                    try:
                        w_val = int(w_attr)
                        if w_val > 8000:  # Should be around 9360
                            table_width_ok = True
                    except ValueError:
                        pass
    checks.append({'name': 'table_width_dxa', 'passed': table_width_ok, 'detail': 'Table uses DXA width' if table_width_ok else 'Table DXA width not found or too small'})

    # Check bullet list items
    enterprise_ok = 'enterprise sales team' in all_text or 'expand enterprise' in all_text
    marketing_ok = 'q4 marketing' in all_text or 'marketing campaign' in all_text
    pricing_ok = 'pricing strategy' in all_text
    bullets_ok = enterprise_ok and marketing_ok and pricing_ok
    checks.append({'name': 'bullet_list_items', 'passed': bullets_ok, 'detail': 'All 3 bullet items found' if bullets_ok else f'Missing: enterprise={enterprise_ok}, marketing={marketing_ok}, pricing={pricing_ok}'})

    # Check bullets use numbering (not unicode bullets manually inserted)
    numbering_ok = False
    if root is not None:
        for numPr in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr'):
            numbering_ok = True
            break
    checks.append({'name': 'bullets_use_numbering', 'passed': numbering_ok, 'detail': 'Bullets use proper numbering config' if numbering_ok else 'No numbering config found (unicode bullets may have been used)'})

    # Check footer content
    footer_ok = False
    confidential_ok = False
    page_num_footer_ok = False
    with zipfile.ZipFile(docx_path) as z:
        footer_files = [n for n in z.namelist() if 'footer' in n.lower() and n.endswith('.xml')]
        for ff in footer_files:
            try:
                footer_data = z.read(ff)
                footer_root = parse_xml(footer_data)
                if footer_root is not None:
                    footer_text = get_all_text_flat(footer_root)
                    if 'confidential' in footer_text:
                        confidential_ok = True
                    # Check for page number field (fldChar or PAGE)
                    footer_str = footer_data.decode('utf-8', errors='ignore').lower()
                    if 'page' in footer_str and ('fldchar' in footer_str or 'instrtext' in footer_str or 'pagenumber' in footer_str or 'current' in footer_str):
                        page_num_footer_ok = True
            except Exception:
                pass
    footer_ok = confidential_ok
    checks.append({'name': 'footer_confidential_text', 'passed': confidential_ok, 'detail': 'Footer contains Q3 2024 Confidential text' if confidential_ok else 'Footer confidential text not found'})
    checks.append({'name': 'footer_page_number', 'passed': page_num_footer_ok, 'detail': 'Footer contains page number field' if page_num_footer_ok else 'Footer page number field not found'})

    # Check Arial font usage
    arial_ok = False
    if root is not None:
        doc_str = doc_xml_data.decode('utf-8', errors='ignore').lower()
        if 'arial' in doc_str:
            arial_ok = True
        else:
            # Check styles.xml
            styles_data = get_xml(docx_path, 'word/styles.xml')
            if styles_data:
                if b'arial' in styles_data.lower():
                    arial_ok = True
    checks.append({'name': 'arial_font', 'passed': arial_ok, 'detail': 'Arial font used' if arial_ok else 'Arial font not found'})

    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    print(json.dumps({'passed': passed, 'score': round(score, 4), 'checks': checks}))

if __name__ == '__main__':
    main()
