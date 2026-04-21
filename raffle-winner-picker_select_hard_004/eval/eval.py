import sys
import os
import json
import re
from datetime import datetime
import pandas as pd


def extract_winners(text, label):
    # Extract blocks of text under Winner or Runner-up sections
    # Returns a list of dicts with keys: ID, Name, Email, Entries, Status (all str)
    entries = []
    # A robust pattern to find all entries: look for rows with all columns
    lines = text.splitlines()
    in_section = False
    for i, line in enumerate(lines):
        if re.search(label, line, re.IGNORECASE):
            in_section = True
            continue
        # End section on empty line or next block
        if in_section and (line.strip() == '' or re.search('winner|runner[- ]?up', line, re.IGNORECASE)):
            if entries:
                break
            else:
                continue
        if in_section:
            # Try to parse a row: expect columns separated by tabs, commas, or multiple spaces
            # Example line:  "ID: 142, Name: Sarah Johnson, Email: sarah.j@email.com, Entries: 5, Status: Eligible"
            # Or: "142\tSarah Johnson\tsarah.j@email.com\t5\tEligible"
            # Use regex to find key: value pairs ignoring order
            # Flexible splitting on commas or tabs
            # We tolerate varied spelling for keys
            pattern = re.compile(r'(id|name|email|entries|status)[:=]\s*([^,\t\n]+)', re.IGNORECASE)
            found = dict((m.group(1).strip().lower(), m.group(2).strip()) for m in pattern.finditer(line))
            if found:
                # Normalize keys
                entry = {
                    'id': found.get('id',''),
                    'name': found.get('name',''),
                    'email': found.get('email',''),
                    'entries': found.get('entries',''),
                    'status': found.get('status','')
                }
                if all(entry.values()):
                    entries.append(entry)
    return entries


def check_timestamp(text):
    # Check for a valid timestamp in ISO-like format, case insensitive
    patterns = [r'(timestamp|time)\s*[:\-]?\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}:\d{2}',
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}(:\d{2})?']
    text_low = text.lower()
    for p in patterns:
        if re.search(p, text_low):
            return True
    return False


def check_method(text):
    # Look for 'cryptographically random' or similar phrase
    return 'cryptographically random' in text.lower()


def load_excel(path):
    try:
        df = pd.read_excel(path, engine='openpyxl')
        cols = {c.lower():c for c in df.columns}
        # Normalize columns
        if 'id' in cols and 'name' in cols and 'email' in cols and 'entries' in cols and 'status' in cols:
            # Return df with lower col names
            df.columns = ['id', 'name', 'email', 'entries', 'status']
            return df
        else:
            return None
    except Exception:
        return None


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument", "passed": False, "detail": "Expected one argument: workspace path."}]}))
        return
    workspace = sys.argv[1]

    # Check the input Excel
    excel_path = os.path.join(workspace, "contest-entries.xlsx")
    df = load_excel(excel_path)
    checks = []

    if df is None:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "input_file", "passed": False, "detail": "contest-entries.xlsx is missing or invalid."}]}))
        return

    # Confirm it has 500 rows (including header -> 500 data rows)
    checks.append({
        "name": "input_row_count",
        "passed": df.shape[0] == 500,
        "detail": f"Found {df.shape[0]} data rows, expected 500."
    })

    # Read user output files - assume user printed to stdout or created a file listing winners?
    # We'll look for any .txt or .md files in workspace that mention 'winner', 'runner-up', or look for output in .txt or .md

    candidate_files = [f for f in os.listdir(workspace) if f.endswith(('.txt', '.md', '.out', '.result'))]
    best_score = 0.0
    best_details = None
    all_checks = []

    # Read all candidate files to find best scoring
    for fname in candidate_files:
        path = os.path.join(workspace, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        # Extract winners and runner-ups
        winners = extract_winners(content, 'winner')
        runnerups = extract_winners(content, 'runner[- ]?up')

        # Checks:
        cks = []

        # Check number of winners (should be 3)
        cks.append({
            "name": "num_winners",
            "passed": len(winners) == 3,
            "detail": f"Found {len(winners)} winners, expected 3."
        })

        # Check number of runner-ups (should be 2)
        cks.append({
            "name": "num_runnerups",
            "passed": len(runnerups) == 2,
            "detail": f"Found {len(runnerups)} runner-ups, expected 2."
        })

        # Check no duplicate between winners and runner-ups (by email)
        winner_emails = {w.get('email','').lower() for w in winners}
        runner_emails = {r.get('email','').lower() for r in runnerups}
        duplicates = winner_emails.intersection(runner_emails)
        cks.append({
            "name": "unique_across_groups",
            "passed": len(duplicates) == 0,
            "detail": f"Duplicate winners and runner-ups emails: {', '.join(duplicates) if duplicates else 'None'}."
        })

        # Check all participants exist in input and are Eligible
        emails_in_input = set(df['email'].str.lower())
        eligible_emails = set(df.loc[df['status'].str.lower() == 'eligible', 'email'].str.lower())

        # All winners' and runner-ups' emails must be in eligible_emails
        invalid_winners = [w['email'] for w in winners if w.get('email','').lower() not in eligible_emails]
        invalid_runnerups = [r['email'] for r in runnerups if r.get('email','').lower() not in eligible_emails]

        cks.append({
            "name": "eligibility_check_winners",
            "passed": len(invalid_winners) == 0,
            "detail": f"Winners not eligible or missing in input: {', '.join(invalid_winners) if invalid_winners else 'None'}."
        })

        cks.append({
            "name": "eligibility_check_runnerups",
            "passed": len(invalid_runnerups) == 0,
            "detail": f"Runner-ups not eligible or missing in input: {', '.join(invalid_runnerups) if invalid_runnerups else 'None'}."
        })

        # Verify details for each winner and runner-up correct and consistent with input
        # e.g., check that Entries is a positive integer and consistent with input
        def check_details(lst, group_name):
            passed = True
            wrongs = []
            for p in lst:
                em = p.get('email','').lower()
                in_df = df[df['email'].str.lower() == em]
                if in_df.empty:
                    passed = False
                    wrongs.append(f"{em} not found in input")
                    continue
                row = in_df.iloc[0]
                # Check ID
                id_str = str(p.get('id','')).strip()
                id_ok = str(row['id']) == id_str

                # Check Name
                name_ok = p.get('name','').strip().lower() == row['name'].strip().lower()

                # Check Entries (integer)
                try:
                    ent_val = int(p.get('entries',''))
                    entries_ok = ent_val == int(row['entries'])
                except Exception:
                    entries_ok = False

                # Check Status
                status_ok = p.get('status','').strip().lower() == row['status'].strip().lower()

                if not all([id_ok, name_ok, entries_ok, status_ok]):
                    passed = False
                    wrongs.append(f"Mismatch for {em}: ID ok={id_ok}, Name ok={name_ok}, Entries ok={entries_ok}, Status ok={status_ok}")
            return passed, wrongs

        pw, wrong_w = check_details(winners, "Winners")
        pr, wrong_r = check_details(runnerups, "Runner-ups")

        cks.append({"name": "winner_details_consistency",
                    "passed": pw,
                    "detail": "; ".join(wrong_w) if wrong_w else "All winner details consistent."})

        cks.append({"name": "runnerup_details_consistency",
                    "passed": pr,
                    "detail": "; ".join(wrong_r) if wrong_r else "All runner-up details consistent."})

        # Check presence of timestamp
        ts_ok = check_timestamp(content)
        cks.append({"name": "timestamp_presence",
                    "passed": ts_ok,
                    "detail": "Timestamp found." if ts_ok else "Timestamp missing or invalid."})

        # Check for mention of cryptographically random selection
        method_ok = check_method(content)
        cks.append({"name": "selection_method",
                    "passed": method_ok,
                    "detail": "Method mentions cryptographically random." if method_ok else "Method missing or incorrect."})

        score = sum(1 for c in cks if c['passed']) / len(cks) if cks else 0
        if score > best_score:
            best_score = score
            best_details = cks

    # Compose final report
    passed = best_score >= 0.8
    print(json.dumps({
        "passed": passed,
        "score": best_score,
        "checks": best_details if best_details else [{"name": "output_file_presence", "passed": False, "detail": "No suitable output file found containing winners."}]
    }))


if __name__ == "__main__":
    main()
