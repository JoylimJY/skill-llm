import json
import os
import re
from datetime import datetime

def check_winner_output(text, entries):
    # Check for presence of winner name and email from entries
    passed_name = any(e["Name"].lower() in text.lower() for e in entries)
    passed_email = any(e["Email"].lower() in text.lower() for e in entries)

    # Check mention of selection method
    passed_method = any(keyword in text.lower() for keyword in ["cryptographically", "secure", "random"])

    # Check for timestamp presence (very loose)
    passed_timestamp = bool(re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}:\d{1,2}:\d{1,2}', text))

    details = []
    details.append({"name": "Winner Name Present", "passed": passed_name, "detail": "Winner name found in output." if passed_name else "Winner name missing."})
    details.append({"name": "Winner Email Present", "passed": passed_email, "detail": "Winner email found in output." if passed_email else "Winner email missing."})
    details.append({"name": "Selection Method Mention", "passed": passed_method, "detail": "Cryptographically secure randomness mentioned." if passed_method else "Selection method missing or unclear."})
    details.append({"name": "Timestamp Present", "passed": passed_timestamp, "detail": "Timestamp string found." if passed_timestamp else "No timestamp found."})

    score = sum(d["passed"] for d in details) / len(details)
    passed = score == 1.0
    return passed, score, details

def main(workspace):
    entries = [
        {"Name": "Alice Smith", "Email": "alice@example.com"},
        {"Name": "Bob Johnson", "Email": "bob@example.com"},
        {"Name": "Carol Lee", "Email": "carol@example.com"},
        {"Name": "David Brown", "Email": "david@example.com"},
        {"Name": "Eve Davis", "Email": "eve@example.com"}
    ]

    # Scan workspace files for output containing winner details
    score_best = 0.0
    passed_best = False
    details_best = []

    for root, _, files in os.walk(workspace):
        for filename in files:
            # Consider .txt, .md, and no-extension files
            if filename.lower().endswith(('.txt', '.md')) or '.' not in filename:
                try:
                    path = os.path.join(root, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        passed, score, details = check_winner_output(content, entries)
                        if score > score_best:
                            score_best = score
                            passed_best = passed
                            details_best = details
                except Exception:
                    continue

    result = {"passed": passed_best, "score": score_best, "checks": details_best}
    print(json.dumps(result))

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
