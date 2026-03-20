import sys
import os
import json
import datetime
from docx import Document


def check_tracked_changes_present(doc_path):
    # Check the XML manually for tracked changes tags
    # docx python lib cannot detect inserted/deleted tags, so parse raw XML
    import zipfile
    with zipfile.ZipFile(doc_path) as z:
        content = z.read('word/document.xml').decode('utf-8')
    found_ins = '<w:ins ' in content
    found_del = '<w:del ' in content
    return found_ins and found_del


def check_phrase_replaced(doc, old_phrase='30 days', new_phrase='60 days'):
    # Checks no '30 days' remains and at least one '60 days' exists
    text = '\n'.join([p.text for p in doc.paragraphs])
    no_old = old_phrase not in text
    has_new = new_phrase in text
    return no_old and has_new


def check_toc_present(doc_path):
    # Check document.xml contains TableOfContents element
    import zipfile
    with zipfile.ZipFile(doc_path) as z:
        content = z.read('word/document.xml').decode('utf-8')
    return '<w:fldSimple w:instr="TOC' in content or '<w:sdt>' in content and 'Table of Contents' in content


def check_footer_page_numbers(doc_path):
    # Check at least one footer has text 'Page' and a page number field reference
    import zipfile
    with zipfile.ZipFile(doc_path) as z:
        footers = [name for name in z.namelist() if name.startswith('word/footer') and name.endswith('.xml')]
        if not footers:
            return False
        for footer_file in footers:
            content = z.read(footer_file).decode('utf-8')
            if 'Page ' in content and 'w:fldChar' in content and 'w:instrText' in content:
                return True
    return False


def main(workspace):
    input_doc = os.path.join(workspace, 'input.docx')
    output_doc = os.path.join(workspace, 'output.docx')

    checks = []

    # Check output.docx exists
    exists = os.path.exists(output_doc)
    checks.append({
        'name': 'Output file exists',
        'passed': exists,
        'detail': 'output.docx found' if exists else 'output.docx missing'
    })

    if not exists:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
        return

    try:
        doc = Document(output_doc)
    except Exception as e:
        checks.append({'name': 'Document Open', 'passed': False, 'detail': f'Failed to open document: {e}'})
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
        return

    # Check tracked changes present
    tc = check_tracked_changes_present(output_doc)
    checks.append({'name': 'Tracked changes present', 'passed': tc,
                   'detail': 'Tracked insertion and deletion tags found' if tc else 'Missing tracked changes XML tags'})

    # Check phrase replaced from "30 days" to "60 days"
    phr = check_phrase_replaced(doc)
    checks.append({'name': 'Phrase replaced with tracked changes', 'passed': phr,
                   'detail': 'No "30 days" and "60 days" present' if phr else '"30 days" remains or "60 days" missing'})

    # Check TOC present
    toc = check_toc_present(output_doc)
    checks.append({'name': 'Table of Contents insertion', 'passed': toc,
                   'detail': 'TOC field found in document' if toc else 'TOC field missing'})

    # Check footer with page numbering
    foot = check_footer_page_numbers(output_doc)
    checks.append({'name': 'Footer with page numbers', 'passed': foot,
                   'detail': 'Footer with page number field found' if foot else 'Footer or page numbers missing'})

    passed = all(c['passed'] for c in checks)
    score = float(passed)

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main(sys.argv[1])
