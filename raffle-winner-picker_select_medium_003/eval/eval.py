import sys
import os
import json
import re
from datetime import datetime

def find_file_with_ext(dir_path, ext):
    for fname in os.listdir(dir_path):
        if fname.lower().endswith(ext.lower()):
            return os.path.join(dir_path, fname)
    return None

def read_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""

def case_insensitive_search(text, keywords):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)

def extract_winners_and_runnerups(text):
    # Try to extract names/emails/IDs from the text
    # A robust approach: find lines containing known participant emails or names
    # We expect at least 4 winners + 2 runner-ups = 6 unique individuals
    # Return two lists: winners and runner_ups

    # For test participants, we know the emails from gen_inputs_script
    participants = {
        "alice@example.com": "Alice Smith",
        "bob@example.com": "Bob Jones",
        "carol@example.com": "Carol White",
        "david@example.com": "David Brown",
        "eva@example.com": "Eva Green",
        "frank@example.com": "Frank Black",
        "grace@example.com": "Grace Liu",
        "henry@example.com": "Henry Ford",
        "ivy@example.com": "Ivy Scott",
        "jack@example.com": "Jack Lee",
        "kara@example.com": "Kara Wang",
        "leo@example.com": "Leo Kim"
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    winner_lines = []
    runnerup_lines = []

    winner_section = False
    runnerup_section = False

    for line in lines:
        low = line.lower()
        if "winner" in low:
            winner_section = True
            runnerup_section = False
            continue
        if "runner-up" in low or "runnerups" in low or "runner ups" in low:
            runnerup_section = True
            winner_section = False
            continue
        # Collect lines that possibly contain participant info
        # Look for name or email matches
        for email, name in participants.items():
            if email.lower() in low or name.lower() in low:
                if winner_section:
                    winner_lines.append(line)
                elif runnerup_section:
                    runnerup_lines.append(line)
                break

    # Extract unique emails/names from the winner and runnerup lines
    def extract_people(lines):
        found = set()
        people = []
        for ln in lines:
            for email, name in participants.items():
                if email.lower() in ln.lower() or name.lower() in ln.lower():
                    if email not in found:
                        found.add(email)
                        people.append({'name': name, 'email': email, 'line': ln})
        return people

    winners = extract_people(winner_lines)
    runnerups = extract_people(runnerup_lines)

    return winners, runnerups


def check_timestamp_method(text):
    # Check that text contains timestamp and method info
    # We allow variations of:
    # selection timestamp: 2024-03-15 14:32:18 UTC
    # selection method: cryptographically random
    ts_keywords = ["timestamp", "utc", "202"]
    method_keywords = ["cryptographically", "random"]

    ts_ok = case_insensitive_search(text, ts_keywords)
    method_ok = case_insensitive_search(text, method_keywords)

    return ts_ok, method_ok


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Missing workspace argument"}]}))
        return

    workspace = sys.argv[1]

    # Read output file exactly winners_and_runnerups.txt
    out_fp = os.path.join(workspace, "winners_and_runnerups.txt")
    content = ""
    if os.path.isfile(out_fp):
        content = read_text_file(out_fp)

    checks = []

    # Check file existence
    exists = os.path.isfile(out_fp)
    checks.append({"name": "output_file_exists", "passed": exists, "detail": f"File 'winners_and_runnerups.txt' existence: {exists}"})

    if not exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Check header indicating number of winners and runner-ups
    winners, runnerups = extract_winners_and_runnerups(content)

    # Check winner count
    count_winners = len(winners)
    passed_winners = (count_winners == 4)
    checks.append({"name": "correct_number_of_winners", "passed": passed_winners, "detail": f"Found {count_winners} winners, expected 4"})

    # Check runner-up count
    count_runnerups = len(runnerups)
    passed_runnerups = (count_runnerups == 2)
    checks.append({"name": "correct_number_of_runnerups", "passed": passed_runnerups, "detail": f"Found {count_runnerups} runner-ups, expected 2"})

    # Check uniqueness of all winners and runner-ups combined
    all_emails = {w.get('email', '').lower() for w in winners} | {r.get('email', '').lower() for r in runnerups}
    passed_unique = (len(all_emails) == count_winners + count_runnerups)
    checks.append({"name": "unique_winners_and_runnerups", "passed": passed_unique, "detail": "No overlapping winners and runner-ups" if passed_unique else "Duplicate participant found in winners and runner-ups"})

    # Check all columns are present for each winner and runner-up in text
    # Since prompt requires 'all their columns', at least check lines mention ID, Name, Email, Entries
    cols_needed_keywords = ["id", "name", "email", "entries"]

    def lines_contain_all_columns(people):
        for p in people:
            line = p.get('line', '').lower()
            if not all(k in line for k in cols_needed_keywords):
                return False
        return True

    winners_cols = lines_contain_all_columns(winners)
    runnerups_cols = lines_contain_all_columns(runnerups)
    checks.append({"name": "winners_all_columns", "passed": winners_cols, "detail": "All winner lines include columns id, name, email, entries" if winners_cols else "Missing some columns in winner info"})
    checks.append({"name": "runnerups_all_columns", "passed": runnerups_cols, "detail": "All runner-up lines include columns id, name, email, entries" if runnerups_cols else "Missing some columns in runner-up info"})

    # Check for timestamp and selection method
    ts_ok, method_ok = check_timestamp_method(content)
    checks.append({"name": "selection_timestamp_present", "passed": ts_ok, "detail": "Found selection timestamp" if ts_ok else "Missing selection timestamp"})
    checks.append({"name": "selection_method_present", "passed": method_ok, "detail": "Found selection method info" if method_ok else "Missing selection method info"})

    # Compute score
    passed_checks = sum(1 for c in checks if c.get('passed', False))
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks else 0.0
    passed = score == 1.0

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))


if __name__ == "__main__":
    main()
