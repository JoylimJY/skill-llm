import sys
import os
import json
import re
from datetime import datetime

def read_all_text_files(workspace):
    texts = []
    for root, _, files in os.walk(workspace):
        for f in files:
            if f.lower().endswith(('.txt','.md','.out','.log')):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fd:
                        texts.append(fd.read())
                except Exception:
                    continue
    return texts

def check_winner_in_texts(texts, entries):
    # Entries is list of tuples: (Name, Email)
    found_winner = None
    for text in texts:
        text_low = text.lower()
        # Look for name and email pairs from entries
        for name, email in entries:
            if name.lower() in text_low and email.lower() in text_low:
                # Found a winner candidate
                found_winner = (name, email)
                break
        if found_winner:
            break
    return found_winner

def check_timestamp_present(texts):
    # Look for an ISO 8601 or similar UTC timestamp
    # Common pattern: YYYY-MM-DD hh:mm:ss (UTC|utc)
    timestamp_found = False
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}.*utc', re.IGNORECASE)
    for t in texts:
        if pattern.search(t):
            timestamp_found = True
            break
    return timestamp_found

def check_selection_method(texts):
    # Check for phrases indicating cryptographically secure randomness
    keywords = ['cryptographically random', 'cryptographically secure', 'secure randomness']
    for t in texts:
        tl = t.lower()
        if any(k in tl for k in keywords):
            return True
    return False

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Missing workspace argument"}]}))
        return

    workspace = sys.argv[1]
    entries = [
        ("Alice Smith", "alice@example.com"),
        ("Bob Jones", "bob@example.com"),
        ("Carol White", "carol@example.com"),
        ("David Green", "david@example.com"),
        ("Eva Blue", "eva@example.com")
    ]

    texts = read_all_text_files(workspace)

    checks = []

    # Check 1: Exactly one winner chosen from list
    winner = check_winner_in_texts(texts, entries)
    passed_winner = winner is not None
    detail_winner = f"Winner found: {winner[0]} <{winner[1]}>" if winner else "No winner information found"
    checks.append({"name": "winner_found", "passed": passed_winner, "detail": detail_winner})

    # Check 2: Timestamp present in output
    timestamp_present = check_timestamp_present(texts)
    checks.append({"name": "timestamp_present", "passed": timestamp_present, "detail": "Timestamp with UTC found" if timestamp_present else "No timestamp found"})

    # Check 3: Selection method described as cryptographically random
    method_present = check_selection_method(texts)
    checks.append({"name": "cryptographically_random_selection", "passed": method_present, "detail": "Method properly mentioned" if method_present else "Selection method missing or unclear"})

    # Check 4: No duplicate winners (only one winner required)
    # Here only one winner expected, so pass if winner found
    checks.append({"name": "no_duplicates", "passed": passed_winner, "detail": "Single winner means no duplicates"})

    score = sum(1 for c in checks if c.get('passed')) / len(checks)
    passed = score == 1.0

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))

if __name__ == '__main__':
    main()
