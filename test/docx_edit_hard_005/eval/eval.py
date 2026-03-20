import sys
import os
import json
import zipfile
from lxml import etree


def check_docx_file_exists(path):
    return os.path.exists(path) and path.endswith('.docx') and os.path.getsize(path) > 0


def extract_xml(docx_path, xml_filename):
    with zipfile.ZipFile(docx_path, 'r') as zipf:
        with zipf.open(xml_filename) as f:
            return f.read()


def parse_xml(xml_bytes):
    return etree.fromstring(xml_bytes)


def check_text_and_tracked_change(root, old_text, new_text, author):
    # Search for tracked deletions of old_text and insertions of new_text with correct author
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    # find deletions with old_text
    dels = root.findall('.//w:del', namespaces=ns)
    ins = root.findall('.//w:ins', namespaces=ns)

    found_del = False
    found_ins = False

    old_text_str = old_text.strip().replace(' ', '')
    new_text_str = new_text.strip().replace(' ', '')

    for d in dels:
        author_attrib = d.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author')
        del_text_elems = d.findall('.//w:delText', namespaces=ns)
        combined_text = ''.join([dt.text for dt in del_text_elems if dt.text])
        combined_text_stripped = combined_text.strip().replace(' ', '')
        if author_attrib == author and old_text_str in combined_text_stripped:
            found_del = True
            break

    for i in ins:
        author_attrib = i.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author')
        t_elems = i.findall('.//w:t', namespaces=ns)
        combined_text = ''.join([t.text for t in t_elems if t.text])
        combined_text_stripped = combined_text.strip().replace(' ', '')
        if author_attrib == author and new_text_str in combined_text_stripped:
            found_ins = True
            break

    return found_del and found_ins


def check_comment_text(path, expected_comment_text):
    # comments stored in word/comments.xml
    try:
        with zipfile.ZipFile(path, 'r') as zipf:
            with zipf.open('word/comments.xml') as f:
                tree = etree.parse(f)
                root = tree.getroot()
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                comments = root.findall('w:comment', namespaces=ns)

                for c in comments:
                    # Extract all text in this comment
                    texts = c.findall('.//w:t', namespaces=ns)
                    combined = ''.join([t.text for t in texts if t.text])
                    if expected_comment_text in combined:
                        return True
    except KeyError:
        return False

    return False


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace path arg."}]}))
        sys.exit(1)

    workspace = sys.argv[1]

    docx_path = os.path.join(workspace, 'contract_edited.docx')

    checks = []

    # Check file exists and non-empty
    exists = check_docx_file_exists(docx_path)
    checks.append({"name": "file_exists", "passed": exists, "detail": "contract_edited.docx file found." if exists else "File missing or empty."})

    passed = exists

    if exists:
        # Extract document.xml
        xmlbytes = extract_xml(docx_path, 'word/document.xml')
        root = parse_xml(xmlbytes)

        # Check tracked changes text "Payment terms: net 30 days" replaced by "Payment terms: net 60 days"
        tc_pass = check_text_and_tracked_change(root, 'Payment terms: net 30 days', 'Payment terms: net 60 days', 'Claude')
        checks.append({"name": "tracked_change", "passed": tc_pass, "detail": "Tracked changes for payment terms verified." if tc_pass else "Tracked changes missing or incorrect."})

        # Check comment text presence
        comment_pass = check_comment_text(docx_path, 'Extended payment term per client request.')
        checks.append({"name": "comment_presence", "passed": comment_pass, "detail": "Comment with required text found." if comment_pass else "Required comment missing."})

        passed = passed and tc_pass and comment_pass

    score = float(passed)

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))


if __name__ == '__main__':
    main()
