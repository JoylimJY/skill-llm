import sys
import json
import os
from docx import Document


def check_tracked_changes_and_comment(doc_path):
    # Load docx file
    doc = Document(doc_path)

    results = []

    # Step 1: Check that 'Introduction' heading is replaced with 'Project Overview'
    # We expect a top-level heading (level=1) with text 'Project Overview'
    heading_found = False
    for para in doc.paragraphs:
        if para.style.name.startswith('Heading 1') and 'Project Overview' in para.text:
            heading_found = True
            heading_para = para
            break

    results.append({
        'name': 'Heading replaced with Project Overview',
        'passed': heading_found,
        'detail': 'Found heading with text: ' + (heading_para.text if heading_found else 'None')
    })

    # Step 2: Check that all occurrences of '30 days' are removed and '60 days' inserted with tracked changes
    # Because python-docx does not support tracked changes directly, we'll check text content
    full_text = '\n'.join(p.text for p in doc.paragraphs)
    has_30_days = '30 days' in full_text
    has_60_days = '60 days' in full_text

    results.append({
        'name': '30 days replaced with 60 days in text',
        'passed': (not has_30_days) and has_60_days,
        'detail': f'30 days present: {has_30_days}, 60 days present: {has_60_days}'
    })

    # Step 3: Check that a comment with expected text is added on paragraph containing 'Project Overview'
    # python-docx does not expose comments, so fallback: Check comments.xml for comment text
    import zipfile
    comments_found = False

    with zipfile.ZipFile(doc_path) as zf:
        if 'word/comments.xml' in zf.namelist():
            comments_xml = zf.read('word/comments.xml').decode('utf-8')
            # Check for marker comment text with XML entities
            expected_comment_text = 'Updated heading to reflect scope change'
            if expected_comment_text in comments_xml:
                comments_found = True

    results.append({
        'name': 'Comment with correct text present',
        'passed': comments_found,
        'detail': f'Comment present: {comments_found}'
    })

    # Overall
    all_passed = all(r['passed'] for r in results)
    score = float(all_passed)

    print(json.dumps({
        'passed': all_passed,
        'score': score,
        'checks': results
    }))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'arg check', 'passed': False, 'detail': 'Usage: eval_script.py <workspace>'}]}))
        sys.exit(1)
    workspace = sys.argv[1]
    output_docx = os.path.join(workspace, 'output.docx')
    if not os.path.exists(output_docx):
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'output.docx exists', 'passed': False, 'detail': 'output.docx not found'}]}))
        sys.exit(1)
    check_tracked_changes_and_comment(output_docx)
