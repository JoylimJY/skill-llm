import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def normalize(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower()) if isinstance(s, str) else ''


def fuzzy_contains(haystack, needle):
    return normalize(needle) in normalize(haystack)


def main():
    checks = []
    try:
        workspace = Path(sys.argv[1])
    except Exception as e:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "argument", "passed": False, "detail": f"Missing or invalid workspace argument: {e}"}]}
        print(json.dumps(result))
        return

    # Check 1: source files exist
    try:
        txt = workspace / 'source_article.txt'
        pdf = workspace / 'source_article.pdf'
        txt_exists = txt.exists()
        pdf_exists = pdf.exists()
        passed = txt_exists and pdf_exists
        detail = f"source_article.txt exists={txt_exists}; source_article.pdf exists={pdf_exists}"
    except Exception as e:
        passed = False
        detail = f"Error checking source files: {e}"
    checks.append({"name": "input_files_exist", "passed": passed, "detail": detail})

    # Check 2: marker content is present in text file
    try:
        content, err = safe_read_text(workspace / 'source_article.txt')
        if content is None:
            passed = False
            detail = f"Could not read source_article.txt: {err}"
        else:
            passed = fuzzy_contains(content, 'KB-MARKER-7F3A2D')
            detail = f"Marker found={passed}"
    except Exception as e:
        passed = False
        detail = f"Error validating marker: {e}"
    checks.append({"name": "marker_present", "passed": passed, "detail": detail})

    # Check 3: PDF contains recognizable article title/marker text
    try:
        import PyPDF2
        pdf_path = workspace / 'source_article.pdf'
        if not pdf_path.exists():
            passed = False
            detail = 'source_article.pdf missing'
        else:
            text = ''
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        try:
                            text += page.extract_text() or ''
                        except Exception:
                            pass
                passed = fuzzy_contains(text, 'Quarterly Process Review') and fuzzy_contains(text, 'KB-MARKER-7F3A2D')
                detail = f"Extracted text length={len(text)}; title+marker present={passed}"
            except Exception as e:
                passed = False
                detail = f"Could not parse PDF: {e}"
    except Exception as e:
        passed = False
        detail = f"PDF validation setup error: {e}"
    checks.append({"name": "pdf_text_check", "passed": passed, "detail": detail})

    # Check 4: metadata JSON exists and matches marker
    try:
        meta_path = workspace / 'expected_marker.json'
        if not meta_path.exists():
            passed = False
            detail = 'expected_marker.json missing'
        else:
            try:
                meta = json.loads(meta_path.read_text(encoding='utf-8', errors='ignore'))
                passed = fuzzy_contains(str(meta.get('marker', '')), 'KB-MARKER-7F3A2D')
                detail = f"Marker field present={passed}"
            except Exception as e:
                passed = False
                detail = f"Malformed JSON: {e}"
    except Exception as e:
        passed = False
        detail = f"Error validating metadata: {e}"
    checks.append({"name": "metadata_json", "passed": passed, "detail": detail})

    score = sum(1 for c in checks if c.get('passed')) / len(checks) if checks else 0.0
    result = {"passed": all(c.get('passed') for c in checks), "score": score, "checks": checks}
    try:
        print(json.dumps(result))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()
