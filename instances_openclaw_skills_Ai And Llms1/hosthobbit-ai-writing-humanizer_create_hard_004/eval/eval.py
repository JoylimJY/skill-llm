import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        s = s.lower()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^a-z0-9$\-\. ]", "", s)
        return s
    except Exception:
        return ""


def contains_ai_tell(text):
    """Check if text contains AI tells as actual writing patterns (not quoted references)."""
    ntext = norm(text)
    
    # AI tell phrases to check
    ai_phrases = [
        'at the end of the day',
        'i hope this helps',
        'it is important to remember',
        'first',
        'secondly',
        'finally',
        'in conclusion',
        'let me know if you have any questions'
    ]
    
    for phrase in ai_phrases:
        # Check if phrase exists in normalized text
        if phrase in ntext:
            # Check if it appears in quotes in original text (quoted reference is OK)
            # Look for the phrase surrounded by quotes in the original
            quote_pattern = r'["\'].*?' + re.escape(phrase) + r'.*?["\']'
            if re.search(quote_pattern, text, re.IGNORECASE):
                # Phrase appears in quotes - likely a reference, not an AI tell
                continue
            
            # Check if phrase appears at the very end (performative closing)
            # This is a strong indicator of AI writing
            if phrase in ntext[-100:]:
                return True
            
            # For "at the end of the day" - check if it's used as a transition
            if phrase == 'at the end of the day':
                # If it appears more than once, it's likely being used as a transition
                count = ntext.count(phrase)
                if count > 1:
                    return True
            
            # For "i hope this helps" - only flag if at end of text
            if phrase == 'i hope this helps':
                # Check if it's near the end (performative closing)
                if phrase in ntext[-50:]:
                    return True
                # Otherwise it's likely a quoted reference
                continue
            
            # For "it is important to remember" - check if used as filler
            if phrase == 'it is important to remember':
                return True
    
    return False


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = ws / 'cleaned.txt'
    inp = ws / 'input.txt'

    try:
        exists = out.exists()
        checks.append({"name": "output_exists", "passed": exists, "detail": "cleaned.txt present" if exists else "cleaned.txt is missing"})
    except Exception as e:
        checks.append({"name": "output_exists", "passed": False, "detail": f"error checking output existence: {e}"})

    try:
        if exists:
            text = out.read_text(encoding='utf-8', errors='replace')
            ntext = norm(text)
            has_maya = 'maya chen' in ntext
            has_date = '2025-04-18' in text or '2025 04 18' in text
            has_amount = '1840' in ntext and 'dollar' in ntext
            
            # Check for AI tells (more lenient - allows quoted references)
            has_ai_tells = contains_ai_tell(text)
            no_hedge = not has_ai_tells
            
            checks.append({"name": "preserve_key_facts", "passed": has_maya and has_date and has_amount, "detail": f"maya={has_maya}, date={has_date}, amount={has_amount}"})
            checks.append({"name": "remove_ai_tells", "passed": no_hedge, "detail": f"hedging/stock phrases removed={no_hedge}"})
        else:
            checks.append({"name": "preserve_key_facts", "passed": False, "detail": "cannot inspect missing output"})
            checks.append({"name": "remove_ai_tells", "passed": False, "detail": "cannot inspect missing output"})
    except Exception as e:
        checks.append({"name": "content_checks", "passed": False, "detail": f"error reading/parsing output: {e}"})

    try:
        marker = (ws / 'marker.txt').read_text(encoding='utf-8', errors='replace')
        marker_ok = 'MARKER_AI_HUMANIZER_7F3A' in marker
        checks.append({"name": "marker_present", "passed": marker_ok, "detail": "marker found" if marker_ok else "marker missing or altered"})
    except Exception as e:
        checks.append({"name": "marker_present", "passed": False, "detail": f"error reading marker: {e}"})

    try:
        total = len(checks)
        passed = sum(1 for c in checks if c.get('passed'))
        score = (passed / total) if total else 0.0
        result = {"passed": passed == total and total > 0, "score": score, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()