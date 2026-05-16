import os
import random
import json
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "club_notes/2024",
    "club_notes/2025",
    "club_notes/archive",
    "member_lists",
    "meeting_minutes",
    "reading_schedules",
    "exports",
    "exports/old",
    "assets",
    "assets/covers",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "club_notes/2024/january_picks.txt": "Book picks for January 2024:\n- Atomic Habits\n- The Midnight Library",
    "club_notes/2024/february_notes.md": "# February Meeting\nAttendees: Alice, Bob, Carol\nDiscussion: Loved the pacing.",
    "club_notes/2025/q1_schedule.csv": "Month,Book,Author\nJan,Deep Work,Cal Newport\nFeb,Educated,Tara Westover",
    "club_notes/archive/2023_titles.json": json.dumps([{"title": "Sapiens", "author": "Harari"}, {"title": "1984", "author": "Orwell"}]),
    "member_lists/active_members.txt": "\n".join(["Alice Wang", "Bob Smith", "Carol Davis", "David Lee", "Eva Martinez"]),
    "member_lists/inactive.txt": "Frank Thompson\nGrace Kim",
    "meeting_minutes/2025_01_15.md": "# Meeting 2025-01-15\nQuorum achieved. Voted to read 'The Name of the Wind' next.",
    "reading_schedules/spring_2025.txt": "Week 1-2: Part I\nWeek 3-4: Part II\nWeek 5: Discussion",
    "assets/covers/placeholder.txt": "Cover images would go here.",
    "exports/old/2023_library.csv": "id,title,author,format\n1,Sapiens,Harari,epub\n2,1984,Orwell,pdf",
    "tmp/scratch.txt": "rough notes: need to catalog new acquisitions before next meeting",
    "tmp/book_ideas.txt": "Possible additions:\n- Project Hail Mary\n- The Thursday Murder Club",
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content)

# ── THE REAL SKILL TOOL: scripts/script.sh ──────────────────────────────────
# We write the actual ebook management script
script_path = workspace / "scripts" / "script.sh"

script_content = r'''#!/usr/bin/env bash
# Ebook — Digital Book Collection & Reading Tracker v1.0.0
# Author: BytesAgain

DATA_DIR="$HOME/.ebook"
DATA_FILE="$DATA_DIR/data.jsonl"
mkdir -p "$DATA_DIR"
touch "$DATA_FILE"

VERSION="1.0.0"

generate_id() {
    python3 -c "import random, string; print(''.join(random.choices('0123456789abcdef', k=8)))"
}

now_iso() {
    python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())"
}

cmd_add() {
    local title="" author="" format="" pages="" tags=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --title) title="$2"; shift 2 ;;
            --author) author="$2"; shift 2 ;;
            --format) format="$2"; shift 2 ;;
            --pages) pages="$2"; shift 2 ;;
            --tags) tags="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    local valid_formats="epub pdf mobi azw3 txt djvu"
    if [[ -z "$title" || -z "$author" || -z "$format" || -z "$pages" ]]; then
        echo "Error: --title, --author, --format, and --pages are required." >&2; exit 1
    fi
    if ! echo "$valid_formats" | grep -qw "$format"; then
        echo "Error: Invalid format '$format'. Supported: $valid_formats" >&2; exit 1
    fi
    local id
    id=$(generate_id)
    local created
    created=$(now_iso)
    local record
    record=$(python3 -c "
import json, sys
r = {'id': sys.argv[1], 'type': 'book', 'title': sys.argv[2], 'author': sys.argv[3],
     'format': sys.argv[4], 'pages': int(sys.argv[5]), 'tags': sys.argv[6].split(',') if sys.argv[6] else [],
     'status': 'unread', 'progress': 0, 'created_at': sys.argv[7]}
print(json.dumps(r))
" "$id" "$title" "$author" "$format" "$pages" "$tags" "$created")
    echo "$record" >> "$DATA_FILE"
    echo "$record"
}

cmd_list() {
    local filter_author="" filter_format="" filter_status=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --author) filter_author="$2"; shift 2 ;;
            --format) filter_format="$2"; shift 2 ;;
            --status) filter_status="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    python3 - "$DATA_FILE" "$filter_author" "$filter_format" "$filter_status" <<'PYEOF'
import json, sys
datafile, fa, ff, fs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
books = []
with open(datafile) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r.get('type') != 'book': continue
        if fa and fa.lower() not in r.get('author','').lower(): continue
        if ff and ff != r.get('format',''): continue
        if fs and fs != r.get('status',''): continue
        books.append(r)
if not books:
    print("No books found.")
    sys.exit(0)
print(f"{'ID':<10} {'Title':<35} {'Author':<25} {'Format':<8} {'Status':<12} {'Progress':>8}")
print("-" * 102)
for b in books:
    print(f"{b['id']:<10} {b['title'][:34]:<35} {b['author'][:24]:<25} {b['format']:<8} {b['status']:<12} {b['progress']:>7}%")
PYEOF
}

cmd_search() {
    local query="" search_author="" search_tag=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --query) query="$2"; shift 2 ;;
            --author) search_author="$2"; shift 2 ;;
            --tag) search_tag="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    python3 - "$DATA_FILE" "$query" "$search_author" "$search_tag" <<'PYEOF'
import json, sys
datafile, q, sa, st = sys.argv[1], sys.argv[2].lower(), sys.argv[3].lower(), sys.argv[4].lower()
with open(datafile) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r.get('type') != 'book': continue
        blob = json.dumps(r).lower()
        if q and q not in blob: continue
        if sa and sa not in r.get('author','').lower(): continue
        if st and st not in [t.lower() for t in r.get('tags',[])]: continue
        print(json.dumps(r))
PYEOF
}

cmd_update() {
    local id="" status="" tags="" title="" author=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) id="$2"; shift 2 ;;
            --status) status="$2"; shift 2 ;;
            --tags) tags="$2"; shift 2 ;;
            --title) title="$2"; shift 2 ;;
            --author) author="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    local valid_statuses="unread reading finished abandoned wishlist"
    if [[ -n "$status" ]] && ! echo "$valid_statuses" | grep -qw "$status"; then
        echo "Error: Invalid status '$status'. Supported: $valid_statuses" >&2; exit 1
    fi
    python3 - "$DATA_FILE" "$id" "$status" "$tags" "$title" "$author" <<'PYEOF'
import json, sys
datafile, bid, status, tags, title, author = sys.argv[1:7]
lines = open(datafile).readlines()
updated = False
out = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if r.get('id') == bid and r.get('type') == 'book':
        if status: r['status'] = status
        if tags: r['tags'] = tags.split(',')
        if title: r['title'] = title
        if author: r['author'] = author
        updated = True
    out.append(json.dumps(r))
if not updated:
    print(f"Error: Book ID '{bid}' not found.", file=sys.stderr)
    sys.exit(1)
with open(datafile, 'w') as f:
    f.write('\n'.join(out) + '\n')
print(f"Updated book {bid}")
PYEOF
}

cmd_delete() {
    local id=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) id="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    python3 - "$DATA_FILE" "$id" <<'PYEOF'
import json, sys
datafile, bid = sys.argv[1], sys.argv[2]
lines = open(datafile).readlines()
out = [l.strip() for l in lines if l.strip() and json.loads(l.strip()).get('id') != bid]
with open(datafile, 'w') as f:
    f.write('\n'.join(out) + '\n')
print(f"Deleted record(s) with ID {bid}")
PYEOF
}

cmd_read() {
    local id="" start_page="" end_page="" duration=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) id="$2"; shift 2 ;;
            --start-page) start_page="$2"; shift 2 ;;
            --end-page) end_page="$2"; shift 2 ;;
            --duration) duration="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    if [[ -z "$id" || -z "$start_page" || -z "$end_page" || -z "$duration" ]]; then
        echo "Error: --id, --start-page, --end-page, --duration required." >&2; exit 1
    fi
    local sid
    sid=$(generate_id)
    local created
    created=$(now_iso)
    python3 - "$DATA_FILE" "$id" "$sid" "$start_page" "$end_page" "$duration" "$created" <<'PYEOF'
import json, sys
datafile, bid, sid, sp, ep, dur, created = sys.argv[1:8]
sp, ep, dur = int(sp), int(ep), int(dur)
# find book total pages
total_pages = None
lines = open(datafile).readlines()
for line in lines:
    line = line.strip()
    if not line: continue
    r = json.loads(line)
    if r.get('id') == bid and r.get('type') == 'book':
        total_pages = r['pages']
        break
if total_pages is None:
    print(f"Error: Book '{bid}' not found.", file=sys.stderr)
    sys.exit(1)
# create session record
session = {'id': sid, 'type': 'session', 'book_id': bid,
           'start_page': sp, 'end_page': ep, 'duration': dur,
           'pages_read': ep - sp, 'created_at': created}
# update book progress
out = []
for line in open(datafile).readlines():
    line = line.strip()
    if not line: continue
    r = json.loads(line)
    if r.get('id') == bid and r.get('type') == 'book':
        progress = round((ep / r['pages']) * 100)
        r['progress'] = min(progress, 100)
        if r['status'] == 'unread':
            r['status'] = 'reading'
    out.append(json.dumps(r))
out.append(json.dumps(session))
with open(datafile, 'w') as f:
    f.write('\n'.join(out) + '\n')
print(json.dumps(session))
PYEOF
}

cmd_progress() {
    local id=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) id="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    python3 - "$DATA_FILE" "$id" <<'PYEOF'
import json, sys
datafile, bid = sys.argv[1], sys.argv[2]
books = {}
sessions = []
with open(datafile) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r.get('type') == 'book':
            if bid and r['id'] != bid: continue
            books[r['id']] = r
        elif r.get('type') == 'session':
            if bid and r.get('book_id') != bid: continue
            sessions.append(r)
for book_id, book in books.items():
    prog = book.get('progress', 0)
    bar = '█' * (prog // 5) + '░' * (20 - prog // 5)
    print(f"\n{book['title']} by {book['author']}")
    print(f"  Progress: [{bar}] {prog}%  ({book['pages']} pages total)")
    book_sessions = [s for s in sessions if s.get('book_id') == book_id]
    total_pages = sum(s.get('pages_read', 0) for s in book_sessions)
    total_time = sum(s.get('duration', 0) for s in book_sessions)
    print(f"  Sessions: {len(book_sessions)}, Pages read: {total_pages}, Time: {total_time} min")
PYEOF
}

cmd_highlight() {
    local id="" page="" text="" color=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) id="$2"; shift 2 ;;
            --page) page="$2"; shift 2 ;;
            --text) text="$2"; shift 2 ;;
            --color) color="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    if [[ -z "$id" || -z "$page" || -z "$text" ]]; then
        echo "Error: --id, --page, --text required." >&2; exit 1
    fi
    local hid
    hid=$(generate_id)
    local created
    created=$(now_iso)
    local record
    record=$(python3 -c "
import json, sys
r = {'id': sys.argv[1], 'type': 'highlight', 'book_id': sys.argv[2],
     'page': int(sys.argv[3]), 'text': sys.argv[4], 'color': sys.argv[5],
     'created_at': sys.argv[6]}
print(json.dumps(r))
" "$hid" "$id" "$page" "$text" "$color" "$created")
    echo "$record" >> "$DATA_FILE"
    echo "$record"
}

cmd_review() {
    local id="" rating="" text=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) id="$2"; shift 2 ;;
            --rating) rating="$2"; shift 2 ;;
            --text) text="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    if [[ -z "$id" || -z "$rating" ]]; then
        echo "Error: --id and --rating required." >&2; exit 1
    fi
    if ! [[ "$rating" =~ ^[1-5]$ ]]; then
        echo "Error: Rating must be 1-5." >&2; exit 1
    fi
    local rid
    rid=$(generate_id)
    local created
    created=$(now_iso)
    local record
    record=$(python3 -c "
import json, sys
r = {'id': sys.argv[1], 'type': 'review', 'book_id': sys.argv[2],
     'rating': int(sys.argv[3]), 'text': sys.argv[4], 'created_at': sys.argv[5]}
print(json.dumps(r))
" "$rid" "$id" "$rating" "$text" "$created")
    echo "$record" >> "$DATA_FILE"
    echo "$record"
}

cmd_stats() {
    python3 - "$DATA_FILE" <<'PYEOF'
import json, sys
datafile = sys.argv[1]
books = []
sessions = []
highlights = []
reviews = []
with open(datafile) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        t = r.get('type')
        if t == 'book': books.append(r)
        elif t == 'session': sessions.append(r)
        elif t == 'highlight': highlights.append(r)
        elif t == 'review': reviews.append(r)
status_counts = {}
for b in books:
    s = b.get('status','unread')
    status_counts[s] = status_counts.get(s, 0) + 1
total_pages = sum(s.get('pages_read', 0) for s in sessions)
total_time = sum(s.get('duration', 0) for s in sessions)
avg_pages = total_pages / len(sessions) if sessions else 0
print(f"=== Reading Statistics ===")
print(f"Total books: {len(books)}")
for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")
print(f"Total sessions: {len(sessions)}")
print(f"Total pages read: {total_pages}")
print(f"Total reading time: {total_time} minutes")
print(f"Avg pages per session: {avg_pages:.1f}")
print(f"Total highlights: {len(highlights)}")
print(f"Total reviews: {len(reviews)}")
PYEOF
}

cmd_export() {
    local format="" output="" type="library"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --format) format="$2"; shift 2 ;;
            --output) output="$2"; shift 2 ;;
            --type) type="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    if [[ -z "$format" || -z "$output" ]]; then
        echo "Error: --format and --output are required." >&2; exit 1
    fi
    python3 - "$DATA_FILE" "$format" "$output" "$type" <<'PYEOF'
import json, sys, csv
from pathlib import Path

datafile, fmt, outfile, etype = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

books = {}
sessions = []
highlights = []
reviews = []
with open(datafile) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        t = r.get('type')
        if t == 'book': books[r['id']] = r
        elif t == 'session': sessions.append(r)
        elif t == 'highlight': highlights.append(r)
        elif t == 'review': reviews.append(r)

out = Path(outfile)

if etype == 'highlights':
    data = highlights
elif etype == 'library':
    data = list(books.values())
else:
    data = list(books.values())

if fmt == 'json':
    out.write_text(json.dumps(data, indent=2))
elif fmt == 'csv':
    if not data:
        out.write_text("")
    else:
        keys = list(data[0].keys())
        with open(out, 'w', newline='') as cf:
            writer = csv.DictWriter(cf, fieldnames=keys)
            writer.writeheader()
            for row in data:
                writer.writerow({k: row.get(k, '') for k in keys})
elif fmt == 'md':
    lines = ["# My Ebook Library\n"]
    if etype == 'highlights':
        lines.append("## Highlights\n")
        for h in highlights:
            book_title = books.get(h.get('book_id', ''), {}).get('title', 'Unknown')
            lines.append(f"### {book_title} — Page {h.get('page','?')}\n")
            lines.append(f"> {h.get('text','')}\n\n")
    else:
        lines.append("## Books\n")
        for b in books.values():
            lines.append(f"### {b['title']}\n")
            lines.append(f"- **Author:** {b['author']}\n")
            lines.append(f"- **Format:** {b['format']}\n")
            lines.append(f"- **Pages:** {b['pages']}\n")
            lines.append(f"- **Status:** {b['status']}\n")
            lines.append(f"- **Progress:** {b['progress']}%\n")
            if b.get('tags'):
                lines.append(f"- **Tags:** {', '.join(b['tags'])}\n")
            lines.append("\n")
    out.write_text(''.join(lines))

print(f"Exported {len(data)} record(s) to {out.resolve()}")
PYEOF
}

cmd_version() {
    echo "ebook v$VERSION"
}

cmd_help() {
    echo "Usage: bash scripts/script.sh <command> [options]"
    echo "Commands: add, list, search, update, delete, read, progress, highlight, review, stats, export, help, version"
}

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    add)       cmd_add "$@" ;;
    list)      cmd_list "$@" ;;
    search)    cmd_search "$@" ;;
    update)    cmd_update "$@" ;;
    delete)    cmd_delete "$@" ;;
    read)      cmd_read "$@" ;;
    progress)  cmd_progress "$@" ;;
    highlight) cmd_highlight "$@" ;;
    review)    cmd_review "$@" ;;
    stats)     cmd_stats "$@" ;;
    export)    cmd_export "$@" ;;
    version)   cmd_version ;;
    help)      cmd_help ;;
    *)         echo "Unknown command: $COMMAND"; cmd_help; exit 1 ;;
esac
'''

script_path.write_text(script_content)
os.chmod(script_path, 0o755)

# ── task brief (non-technical framing) ─────────────────────────────────────
brief_path = workspace / "club_notes" / "2025" / "cataloging_task.txt"
brief_path.write_text(
    "Book Club Tech Setup — Spring 2025\n"
    "===================================\n"
    "We need to get our digital reading tracker set up before the April meeting.\n"
    "Specific books to add:\n"
    "  1. 'The Pragmatic Programmer' by David Thomas & Andrew Hunt\n"
    "     - Digital format: pdf, 352 pages\n"
    "     - Tags: programming, career\n"
    "  2. 'A Pattern Language' by Christopher Alexander\n"
    "     - Digital format: epub, 1171 pages\n"
    "     - Tags: architecture, design\n"
    "Reading activity to log:\n"
    "  - For 'The Pragmatic Programmer': session from page 1 to 88, lasted 45 minutes\n"
    "  - For 'A Pattern Language': session from page 1 to 60, lasted 40 minutes\n"
    "Highlights to record:\n"
    "  - 'The Pragmatic Programmer', page 14: 'Care about your craft.'\n"
    "  - 'A Pattern Language', page 32: 'Each pattern describes a problem which occurs over and over again in our environment.'\n"
    "Reviews:\n"
    "  - 'The Pragmatic Programmer': 5 stars, 'A must-read for every software developer.'\n"
    "  - 'A Pattern Language': 4 stars, 'Dense but foundational.'\n"
    "Exports needed:\n"
    "  - Full library as Markdown → file named: library_spring2025.md\n"
    "  - All highlights as CSV → file named: highlights_spring2025.csv\n"
)

print("Workspace setup complete.")
print(f"Script at: {script_path}")
print(f"Brief at: {brief_path}")