import json
import re
import sys
from pathlib import Path


def normalize(text):
    text = text.lower()
    text = re.sub(r"[\s\W_]+", " ", text)
    return text.strip()


def extract_marker_value(marker_text, key):
    """Extract value for a given key from marker text."""
    pattern = rf'{key}:\s*(.+)'
    match = re.search(pattern, marker_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    output_file = workspace / 'output.txt'
    marker_file = workspace / 'input_marker.txt'

    try:
        marker_text = marker_file.read_text(encoding='utf-8')
    except Exception as e:
        marker_text = ''
        checks.append({"name": "read_marker_file", "passed": False, "detail": f"Could not read marker file: {e}"})
    else:
        checks.append({"name": "read_marker_file", "passed": True, "detail": "Marker file read successfully."})

    try:
        output_text = output_file.read_text(encoding='utf-8')
    except Exception as e:
        output_text = ''
        checks.append({"name": "output_exists", "passed": False, "detail": f"Missing or unreadable output.txt: {e}"})
    else:
        checks.append({"name": "output_exists", "passed": True, "detail": "output.txt exists and is readable."})

    try:
        # Check for codename in both normalized form (orbit 7) and original form (ORBIT-7)
        c1 = 'orbit 7' in normalize(output_text) or 'ORBIT-7' in output_text or 'orbit-7' in output_text
        detail = 'Contains project codename ORBIT-7.' if c1 else 'Does not contain project codename ORBIT-7.'
        checks.append({"name": "codename_present", "passed": c1, "detail": detail})
    except Exception as e:
        checks.append({"name": "codename_present", "passed": False, "detail": f"Error checking codename: {e}"})

    try:
        # Extract expected date from marker file
        expected_date = extract_marker_value(marker_text, 'DATE_MARKER')
        date_ok = False
        
        if expected_date:
            # Check for the exact date format from marker
            date_ok = expected_date in output_text
            # Also check normalized versions
            if not date_ok:
                normalized_date = normalize(expected_date)
                date_ok = normalized_date in normalize(output_text)
            # Check for common date format variations
            if not date_ok:
                # Try to match year, month, day components
                date_parts = re.findall(r'\d{4}|\d{2}', expected_date)
                if len(date_parts) >= 3:
                    year = date_parts[0]
                    # Check if year appears in output
                    date_ok = year in output_text or year in normalize(output_text)
        else:
            # Fallback: check for any recognizable date pattern
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            ]
            for pattern in date_patterns:
                if re.search(pattern, output_text, re.IGNORECASE):
                    date_ok = True
                    break
        
        detail = 'Contains a recognizable date marker.' if date_ok else 'No recognizable date found.'
        checks.append({"name": "date_present", "passed": date_ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "date_present", "passed": False, "detail": f"Error checking date: {e}"})

    try:
        signoff_ok = any(s in normalize(output_text) for s in ['best regards', 'regards', 'sincerely'])
        detail = 'Ends with or includes a friendly sign-off.' if signoff_ok else 'No friendly sign-off found.'
        checks.append({"name": "signoff_present", "passed": signoff_ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "signoff_present", "passed": False, "detail": f"Error checking sign-off: {e}"})

    try:
        if marker_text:
            # Check for marker keywords in normalized form (underscores become spaces)
            marker_ok = 'project codename' in normalize(marker_text) and 'orbit 7' in normalize(marker_text)
        else:
            marker_ok = False
        detail = 'Marker file contains expected benchmark markers.' if marker_ok else 'Marker file missing expected benchmark markers.'
        checks.append({"name": "marker_validation", "passed": marker_ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "marker_validation", "passed": False, "detail": f"Error validating marker file: {e}"})

    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / len(checks) if checks else 0.0
    result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()