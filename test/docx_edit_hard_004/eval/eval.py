import sys
import os
import json
import zipfile
import datetime
from lxml import etree

workspace = sys.argv[1]

result = {"passed": False, "score": 0.0, "checks": []}

output_path = os.path.join(workspace, 'updated_contract.docx')

# Check file exists
if not os.path.isfile(output_path):
    result['checks'].append({"name": "File exists", "passed": False, "detail": 'updated_contract.docx not found'})
    print(json.dumps(result))
    sys.exit(0)
else:
    result['checks'].append({"name": "File exists", "passed": True, "detail": 'File found'})

# Helper function to read document.xml content

def read_doc_xml(docx_path):
    with zipfile.ZipFile(docx_path, 'r') as zf:
        with zf.open('word/document.xml') as doc_xml:
            return etree.parse(doc_xml)

# Parse the document.xml
try:
    tree = read_doc_xml(output_path)
except Exception as e:
    result['checks'].append({"name": "Parse document.xml", "passed": False, "detail": f'Failed to parse document.xml: {e}'})
    print(json.dumps(result))
    sys.exit(0)

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

doc_root = tree.getroot()

# Check tracked changes for warranty period update: '12 months' replaced by '24 months', with <w:del> and <w:ins> tags, author=Claude, date=2025-01-01T12:00:00Z

# Search for w:del containing '12 months' and w:ins containing '24 months'
def find_tracked_changes(tree):
    dels = tree.findall('.//w:del', ns)
    ins = tree.findall('.//w:ins', ns)

    found_del = False
    found_ins = False
    for d in dels:
        text_del = ''.join(d.xpath('.//w:delText/text()', namespaces=ns))
        if '12 months' in text_del:
            author = d.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author')
            date = d.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date')
            if author == 'Claude' and date and date.startswith('2025-01-01'):
                found_del = True
                break

    for i in ins:
        text_ins = ''.join(i.xpath('.//w:t/text()', namespaces=ns))
        if '24 months' in text_ins:
            author = i.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author')
            date = i.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date')
            if author == 'Claude' and date and date.startswith('2025-01-01'):
                found_ins = True
                break

    return found_del and found_ins

tracked_change_check = find_tracked_changes(tree)
result['checks'].append({"name": "Tracked changes for warranty period update", "passed": tracked_change_check, "detail": 'Expected tracked deletion of "12 months" and insertion of "24 months" with author Claude and date 2025-01-01.' if tracked_change_check else 'Tracked changes for warranty update missing or incorrect.'})

# Check numeric list contains the new bullet clause under Terms and Conditions
# We look for a paragraph with text "The client agrees to provide timely feedback within 10 business days." that is numbered

paragraphs = doc_root.findall('.//w:p', ns)

found_new_clause = False

for p in paragraphs:
    # Extract text content in paragraph
    texts = p.findall('.//w:t', ns)
    full_text = ''.join([t.text for t in texts if t.text])
    if 'The client agrees to provide timely feedback within 10 business days.' in full_text:
        # Check numbering properties
        numPr = p.find('.//w:numPr', ns)
        if numPr is not None:
            found_new_clause = True
            break

result['checks'].append({"name": "New clause insertion as numbered bullet", "passed": found_new_clause, "detail": ('Found new clause as numbered bullet item.' if found_new_clause else 'New clause missing or not numbered.')})

# Check footer presence with page numbers starting from 1, right aligned, Arial 10pt font
# Footer usually in word/footer1.xml or similar, relationships in _rels
# Will check zip contents
with zipfile.ZipFile(output_path, 'r') as zipf:
    footer_files = [f for f in zipf.namelist() if f.startswith('word/footer') and f.endswith('.xml')]
    footer_page_num_ok = False
    footer_arial_10pt_ok = False
    for footer_file in footer_files:
        f_xml = etree.fromstring(zipf.read(footer_file))
        # Search for PAGE fields w:fldChar with w:instrText containing PAGE
        instr_texts = f_xml.findall('.//w:instrText', ns)
        has_page_field = any('PAGE' in (it.text or '') for it in instr_texts)

        # Search for right aligned paragraph
        paragraphs_footer = f_xml.findall('.//w:p', ns)
        right_aligned = False
        arial_10pt = False
        for p in paragraphs_footer:
            jc = p.find('.//w:jc', ns)
            if jc is not None and jc.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') == 'right':
                right_aligned = True
            # Check runs font and size
            runs = p.findall('.//w:r', ns)
            for r in runs:
                rFonts = r.find('.//w:rFonts', ns)
                sz = r.find('.//w:sz', ns) or r.find('.//w:szCs', ns)
                font_ok = rFonts is not None and rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii') == 'Arial'
                size_ok = sz is not None and sz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') == '20' # 10pt = 20 half-points
                if font_ok and size_ok:
                    arial_10pt = True
        if has_page_field and right_aligned and arial_10pt:
            footer_page_num_ok = True
            footer_arial_10pt_ok = True
            break

result['checks'].append({"name": "Footer with right-aligned page numbers in Arial 10pt", "passed": footer_page_num_ok and footer_arial_10pt_ok, "detail": ('Footer with page numbers right aligned and Arial 10pt found.' if footer_page_num_ok and footer_arial_10pt_ok else 'Footer page numbering or style missing or incorrect.')})

# Since prompt requires tracked changes not accepted, check document.xml does contain tracked changes
# Simple heuristic: presence of <w:ins> or <w:del> elements
ins_elements = doc_root.findall('.//w:ins', ns)
del_elements = doc_root.findall('.//w:del', ns)
tracked_changes_exist = len(ins_elements) > 0 and len(del_elements) > 0
result['checks'].append({"name": "Tracked changes preserved", "passed": tracked_changes_exist, "detail": ('Tracked changes are present in the document.' if tracked_changes_exist else 'No tracked changes found; expected to be preserved.')})

# Calculate overall pass: all checks passed
all_passed = all(c['passed'] for c in result['checks'])
result['passed'] = all_passed
result['score'] = float(sum(c['passed'] for c in result['checks'])) / len(result['checks']) if result['checks'] else 0.0

print(json.dumps(result))
