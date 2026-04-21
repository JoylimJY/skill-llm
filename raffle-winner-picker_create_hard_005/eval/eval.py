import json
import os
import re
import sys
from datetime import datetime


PID_RE = re.compile(r"P\d{4}", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SECTION_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s*(.+?)\s*$", re.MULTILINE)


def find_file(dir_path, extensions=None, name_contains=None):
    candidates = []
    for root, _, files in os.walk(dir_path):
        for filename in files:
            if extensions and not any(filename.lower().endswith(ext) for ext in extensions):
                continue
            if name_contains and name_contains.lower() not in filename.lower():
                continue
            candidates.append(os.path.join(root, filename))
    return candidates


def load_text(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def check_section_header(text, keywords):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def check_utc_iso_timestamp(text):
    patterns = [
        r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?",
        r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2} UTC",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def normalize_header(cell):
    return re.sub(r"[^a-z0-9]", "", cell.lower())


def split_sections(content):
    matches = list(SECTION_HEADER_RE.finditer(content))
    sections = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[title] = content[start:end].strip()
    return sections


def get_named_section(content, names):
    sections = split_sections(content)
    for title, body in sections.items():
        for name in names:
            if name in title:
                return body
    return ""


def parse_markdown_table(section_text):
    records = []
    lines = [line.rstrip() for line in section_text.splitlines()]
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not (line.startswith("|") and line.endswith("|")):
            idx += 1
            continue

        header_cells = [cell.strip() for cell in line.strip("|").split("|")]
        normalized = [normalize_header(cell) for cell in header_cells]
        required = {"participantid", "name", "email", "entries"}
        if not required.issubset(set(normalized)):
            idx += 1
            continue

        if idx + 1 >= len(lines):
            break
        separator = lines[idx + 1].strip()
        if not separator.startswith("|"):
            idx += 1
            continue

        col_index = {name: normalized.index(name) for name in required}
        row_idx = idx + 2
        while row_idx < len(lines):
            row = lines[row_idx].strip()
            if not (row.startswith("|") and row.endswith("|")):
                break
            if set(row.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                row_idx += 1
                continue
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) != len(header_cells):
                break
            record = {
                "ParticipantID": cells[col_index["participantid"]].upper(),
                "Name": cells[col_index["name"]].strip(),
                "Email": cells[col_index["email"]].lower(),
                "Entries": cells[col_index["entries"]].strip(),
            }
            prev_idx = normalized.index("previouswinner") if "previouswinner" in normalized else None
            if prev_idx is not None:
                record["PreviousWinner"] = cells[prev_idx].strip()
            records.append(record)
            row_idx += 1

        idx = row_idx
    return records


def parse_block_records(section_text):
    records = []
    pattern = re.compile(
        r"(?:^|\n)\s*(?:\d+\.|Winner\s+\d+:|Runner-?up\s+\d+:)?\s*"
        r"(?:\n|.)*?ParticipantID\s*:\s*(P\d{4}).*?"
        r"Name\s*:\s*(.+?).*?"
        r"Email\s*:\s*([\w.+-]+@[\w-]+\.[\w.-]+).*?"
        r"Entries\s*:\s*(\d+)"
        r"(?:.*?PreviousWinner\s*:\s*(True|False))?",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(section_text):
        records.append(
            {
                "ParticipantID": match.group(1).upper(),
                "Name": match.group(2).strip(),
                "Email": match.group(3).lower(),
                "Entries": match.group(4).strip(),
                "PreviousWinner": (match.group(5) or "False").strip(),
            }
        )
    return records


def parse_section_records(section_text):
    records = parse_markdown_table(section_text)
    if not records:
        records = parse_block_records(section_text)
    deduped = []
    seen = set()
    for record in records:
        key = (record.get("ParticipantID", "").lower(), record.get("Email", "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def valid_participant(record):
    pid = record.get("ParticipantID", "")
    name = record.get("Name", "")
    email = record.get("Email", "")
    try:
        entries = int(record.get("Entries", ""))
    except Exception:
        return False
    return bool(PID_RE.fullmatch(pid)) and bool(name) and bool(EMAIL_RE.fullmatch(email)) and 1 <= entries


def evaluate_results(file_content):
    checks = []

    has_method = ("cryptographically" in file_content.lower() and "weighted random" in file_content.lower())
    checks.append({"name": "Selection method documented", "passed": has_method, "detail": f"Documented method found? {has_method}"})

    has_timestamp = check_utc_iso_timestamp(file_content)
    checks.append({"name": "UTC ISO 8601 timestamp", "passed": has_timestamp, "detail": f"Timestamp found? {has_timestamp}"})

    winners_present = check_section_header(file_content, ["winner"])
    checks.append({"name": "Winners section present", "passed": winners_present, "detail": f"Winners section found? {winners_present}"})

    runner_up_present = check_section_header(file_content, ["runner-up", "runner ups", "runners up"])
    checks.append({"name": "Runner-ups section present", "passed": runner_up_present, "detail": f"Runner-ups section found? {runner_up_present}"})

    winners_section = get_named_section(file_content, ["winners"])
    runner_section = get_named_section(file_content, ["runner-ups", "runner-up", "runner ups", "runners up"])
    winners = parse_section_records(winners_section)
    runner_ups = parse_section_records(runner_section)

    winners_count = len(winners)
    runner_ups_count = len(runner_ups)
    checks.append({"name": "Exactly 7 unique winners", "passed": winners_count == 7, "detail": f"Winners counted: {winners_count}"})
    checks.append({"name": "Exactly 3 runner-ups", "passed": runner_ups_count == 3, "detail": f"Runner-ups counted: {runner_ups_count}"})

    all_records = winners + runner_ups
    unique_pids = len(all_records) == 10 and len({record["ParticipantID"].lower() for record in all_records}) == len(all_records)
    unique_emails = len(all_records) == 10 and len({record["Email"].lower() for record in all_records}) == len(all_records)
    checks.append({"name": "No duplicate ParticipantIDs", "passed": unique_pids, "detail": f"Unique ParticipantIDs? {unique_pids}"})
    checks.append({"name": "No duplicate Emails", "passed": unique_emails, "detail": f"Unique Emails? {unique_emails}"})

    no_previous_winners = len(all_records) == 10 and all(str(record.get("PreviousWinner", "False")).strip().lower() != "true" for record in all_records)
    checks.append({"name": "No Previous winners selected", "passed": no_previous_winners, "detail": f"PreviousWinner present? {not no_previous_winners}"})

    well_formed = len(all_records) == 10 and all(valid_participant(record) for record in all_records)
    checks.append({"name": "Participant details parse cleanly", "passed": well_formed, "detail": f"Parsed participant rows: {len(all_records)}"})

    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    passed = score == 1.0
    return {"passed": passed, "score": score, "checks": checks}


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Argument check", "passed": False, "detail": "Expected exactly one argument: workspace directory"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    candidates = find_file(workspace, extensions=[".md"], name_contains="raffle-results")
    if not candidates:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Output file presence", "passed": False, "detail": "raffle-results.md not found"}]}))
        sys.exit(1)

    best_result = None
    best_score = -1.0
    for candidate in candidates:
        content = load_text(candidate)
        if not content.strip():
            continue
        result = evaluate_results(content)
        if result.get("score", 0.0) > best_score:
            best_score = result["score"]
            best_result = result

    if best_result is None:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Evaluation", "passed": False, "detail": "Could not evaluate output file correctly"}]}))
        sys.exit(1)

    print(json.dumps(best_result))


if __name__ == "__main__":
    main()
