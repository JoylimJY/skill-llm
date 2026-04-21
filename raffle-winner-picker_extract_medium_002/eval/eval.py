import json
import os
import re
import sys
from datetime import datetime


PID_RE = re.compile(r"PID\d{3}", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
ENTRIES_RE = re.compile(r"Entries?\s*:\s*(\d+)", re.IGNORECASE)
WINNER_HEADER_RE = re.compile(r"^\s*Winner\s+\d+\s*:\s*$", re.IGNORECASE | re.MULTILINE)


def try_parse_int(s):
    try:
        return int(s)
    except Exception:
        return None


def parse_multiline_winners(content):
    winners = []
    matches = list(WINNER_HEADER_RE.finditer(content))
    for idx, match in enumerate(matches):
        block_start = match.end()
        block_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        block = content[block_start:block_end]

        pid_match = re.search(r"^\s*Participant ID\s*:\s*(PID\d{3})\s*$", block, re.IGNORECASE | re.MULTILINE)
        name_match = re.search(r"^\s*Name\s*:\s*(.+?)\s*$", block, re.IGNORECASE | re.MULTILINE)
        email_match = re.search(r"^\s*Email\s*:\s*([\w.+-]+@[\w-]+\.[\w.-]+)\s*$", block, re.IGNORECASE | re.MULTILINE)
        entries_match = re.search(r"^\s*Entries\s*:\s*(\d+)\s*$", block, re.IGNORECASE | re.MULTILINE)

        if pid_match and email_match:
            winners.append(
                {
                    "Participant ID": pid_match.group(1).upper(),
                    "Name": name_match.group(1).strip() if name_match else "",
                    "Email": email_match.group(1).lower(),
                    "Entries": try_parse_int(entries_match.group(1)) if entries_match else None,
                }
            )
    return winners


def parse_single_line_winners(lines):
    winners = []
    for line in lines:
        pid_match = PID_RE.search(line)
        email_match = EMAIL_RE.search(line)
        if not (pid_match and email_match):
            continue

        pid = pid_match.group(0).upper()
        email = email_match.group(0).lower()
        entries_match = ENTRIES_RE.search(line)
        entries = try_parse_int(entries_match.group(1)) if entries_match else None

        line_without_labels = re.sub(r"Participant ID\s*:\s*", "", line, flags=re.IGNORECASE)
        line_without_labels = re.sub(r"Email\s*:\s*", "", line_without_labels, flags=re.IGNORECASE)
        line_without_labels = re.sub(r"Entries?\s*:\s*\d+", "", line_without_labels, flags=re.IGNORECASE)
        parts = line_without_labels.split()
        try:
            pid_index = next(i for i, part in enumerate(parts) if part.upper() == pid)
        except StopIteration:
            pid_index = -1
        try:
            email_index = next(i for i, part in enumerate(parts) if part.lower() == email)
        except StopIteration:
            email_index = -1

        name = ""
        if pid_index != -1 and email_index != -1 and email_index > pid_index + 1:
            name = " ".join(parts[pid_index + 1:email_index]).strip()

        winners.append(
            {
                "Participant ID": pid,
                "Name": name,
                "Email": email,
                "Entries": entries,
            }
        )
    return winners


def dedupe_winners(candidates):
    winners = []
    seen = set()
    for winner in candidates:
        key = (winner.get("Participant ID", "").lower(), winner.get("Email", "").lower())
        if key in seen:
            continue
        seen.add(key)
        winners.append(winner)
    return winners


def parse_winners_summary(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines)
    data["content"] = content

    for line in lines:
        if "timestamp" in line.lower():
            match = re.search(r"\d{4}-\d{2}-\d{2}.*", line)
            if match:
                data["timestamp"] = match.group(0).strip()
                break

    for line in lines:
        if "cryptographically" in line.lower() and "random" in line.lower():
            data["method"] = line.strip()
            break

    multiline_winners = parse_multiline_winners(content)
    single_line_winners = parse_single_line_winners(lines)
    data["winners"] = dedupe_winners(multiline_winners + single_line_winners)
    return data


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Arguments", "passed": False, "detail": "Expected exactly one argument: workspace directory."}]}))
        return

    workspace = sys.argv[1]
    marker_path = os.path.join(workspace, "marker.txt")
    if not os.path.isfile(marker_path):
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Input file presence", "passed": False, "detail": "marker.txt not found in workspace."}]}))
        return

    with open(marker_path, "r", encoding="utf-8") as f:
        marker_content = f.read()

    passed_marker = "[marker-weighted-contest-entries-100]" in marker_content.lower()
    winners_file = os.path.join(workspace, "winners_summary.txt")
    checks = []

    if not os.path.isfile(winners_file):
        checks.append({
            "name": "Output file presence",
            "passed": False,
            "detail": "winners_summary.txt not found in workspace",
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    data = parse_winners_summary(winners_file)

    method_pass = "method" in data and "cryptographically" in data.get("method", "").lower()
    checks.append({
        "name": "Cryptographically secure method mentioned",
        "passed": method_pass,
        "detail": "Found mention of cryptographically random selection method" if method_pass else "Missing cryptographically random method mention",
    })

    timestamp_pass = False
    ts = data.get("timestamp", "")
    if ts:
        try:
            datetime.fromisoformat(ts.split()[0])
            timestamp_pass = True
        except Exception:
            timestamp_pass = False
    checks.append({
        "name": "Timestamp included and valid",
        "passed": timestamp_pass,
        "detail": f"Timestamp found: {ts}" if timestamp_pass else "Missing or invalid timestamp",
    })

    winners = data.get("winners", [])
    winners_count_pass = len(winners) == 4
    checks.append({
        "name": "Exactly 4 winners selected",
        "passed": winners_count_pass,
        "detail": f"Found {len(winners)} winners" if winners_count_pass else f"Incorrect number of winners (found {len(winners)})",
    })

    cols = ["Participant ID", "Name", "Email", "Entries"]
    cols_pass = len(winners) == 4
    if cols_pass:
        for winner in winners:
            for col in cols:
                if col not in winner or winner[col] in (None, ""):
                    cols_pass = False
                    break
            if not isinstance(winner.get("Entries"), int) or winner.get("Entries") < 1:
                cols_pass = False
            if not cols_pass:
                break
    checks.append({
        "name": "Each winner has complete participant details",
        "passed": cols_pass,
        "detail": "All winners have ID, Name, Email, and positive Entries" if cols_pass else "Missing or invalid winner detail",
    })

    unique_pass = len(winners) == 4
    pids = set()
    emails = set()
    if unique_pass:
        for winner in winners:
            pid = winner.get("Participant ID", "").lower()
            email = winner.get("Email", "").lower()
            if pid in pids or email in emails:
                unique_pass = False
                break
            pids.add(pid)
            emails.add(email)
    checks.append({
        "name": "No duplicate winners",
        "passed": unique_pass,
        "detail": "All winners are unique by Participant ID and Email" if unique_pass else "Duplicates found in winners",
    })

    entries_vals_pass = len(winners) == 4
    if entries_vals_pass:
        for winner in winners:
            entries = winner.get("Entries")
            if not isinstance(entries, int) or entries < 1 or entries > 10:
                entries_vals_pass = False
                break
    checks.append({
        "name": "Winners entries values valid (1-10)",
        "passed": entries_vals_pass,
        "detail": "Entries values within expected range (1-10)" if entries_vals_pass else "Entries values out of range or winners missing",
    })

    marker_in_output = "[marker-weighted-contest-entries-100]" in data.get("content", "").lower()
    checks.append({
        "name": "Output file includes marker content (or marker.txt present)",
        "passed": passed_marker or marker_in_output,
        "detail": "Marker found in inputs or output" if passed_marker or marker_in_output else "Marker missing in inputs and output",
    })

    score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0
    passed = score == 1.0
    print(json.dumps({"passed": passed, "score": score, "checks": checks}))


if __name__ == "__main__":
    main()
