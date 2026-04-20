import json
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r"[\s\*_\-\(\)\[\]\{\}:,.;!]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    target = workspace / 'data' / 'birthdays.md'

    try:
        exists = target.exists()
        checks.append({"name": "birthdays_file_exists", "passed": exists, "detail": "Found file" if exists else "Missing /data/birthdays.md"})
    except Exception as e:
        checks.append({"name": "birthdays_file_exists", "passed": False, "detail": f"Error checking file existence: {e}"})

    content = ""
    try:
        if target.exists():
            content = target.read_text(encoding='utf-8', errors='replace')
        has_lina = 'lina' in normalize(content) and '07.09.1994' in content
        checks.append({"name": "lina_added", "passed": has_lina, "detail": "Lina birthday present" if has_lina else "Lina entry not found or date mismatch"})
    except Exception as e:
        checks.append({"name": "lina_added", "passed": False, "detail": f"Error reading/parsing file: {e}"})

    try:
        norm = normalize(content)
        has_markers = all(marker in norm for marker in ["markeralpha", "markerbeta", "markergamma"])
        checks.append({"name": "preserve_existing_entries", "passed": has_markers, "detail": "All marker entries preserved" if has_markers else "One or more marker entries missing"})
    except Exception as e:
        checks.append({"name": "preserve_existing_entries", "passed": False, "detail": f"Error checking preserved entries: {e}"})

    try:
        # Soft formatting check: markdown list entries with bold names and dates somewhere in the file
        lines = [ln.strip() for ln in content.splitlines() if ln.strip().startswith('-')]
        formatted = any('**' in ln and re.search(r"\d{2}\.\d{2}(?:\.\d{4})?", ln) for ln in lines)
        checks.append({"name": "markdown_format", "passed": formatted, "detail": "Markdown list formatting looks correct" if formatted else "No suitably formatted markdown list entry found"})
    except Exception as e:
        checks.append({"name": "markdown_format", "passed": False, "detail": f"Error validating format: {e}"})

    try:
        # Check sorting by month/day in a forgiving way for lines with explicit dates
        entries = []
        for ln in content.splitlines():
            m = re.search(r"-\s*\*\*(.+?)\*\*\s*-\s*(\d{2})\.(\d{2})\.(\d{4})?", ln)
            if m:
                entries.append((int(m.group(3)), int(m.group(2)), ln))
        sorted_ok = entries == sorted(entries, key=lambda x: (x[0], x[1])) or len(entries) <= 1
        checks.append({"name": "sorted_by_date", "passed": sorted_ok, "detail": "Entries appear sorted" if sorted_ok else "Entries not sorted by month/day"})
    except Exception as e:
        checks.append({"name": "sorted_by_date", "passed": False, "detail": f"Error checking sort order: {e}"})

    try:
        total = len(checks)
        passed = sum(1 for c in checks if c.get('passed'))
        result = {"passed": passed == total, "score": (passed / total) if total else 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed":false,"score":0.0,"checks":[]}')

if __name__ == '__main__':
    main()
