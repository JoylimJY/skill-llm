FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create workspace directories
RUN mkdir -p /root/.openclaw/workspace /tmp/audit_staging

# Create the pest_tracker.py tool
RUN cat > /usr/local/bin/pest_tracker.py << 'PEST_TRACKER_EOF'
#!/usr/bin/env python3
"""Pest & Disease Tracker CLI Tool"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".openclaw" / "workspace" / "pest_tracker_db.json"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

RECOMMENDATIONS = {
    "aphids": ["Neem oil", "insecticidal soap", "ladybugs", "strong water spray"],
    "slugs": ["Beer traps", "diatomaceous earth", "copper tape", "beneficial nematodes"],
    "caterpillars": ["Bt (Bacillus thuringiensis)", "handpicking", "row covers", "parasitic wasps"],
    "cucumber beetles": ["Row covers", "beneficial nematodes", "crop rotation", "pyrethrin"],
    "japanese beetles": ["Hand-picking", "neem oil", "milky spore", "row covers"],
    "squash bugs": ["Hand-picking", "neem oil", "row covers", "crop rotation"],
    "spider mites": ["Neem oil", "insecticidal soap", "predatory mites", "water spray"],
    "thrips": ["Neem oil", "insecticidal soap", "blue sticky traps", "spinosad"],
    "whiteflies": ["Insecticidal soap", "neem oil", "yellow sticky traps", "parasitic wasps"],
    "early blight": ["Copper fungicide", "remove affected leaves", "improve air circulation", "avoid overhead watering"],
    "late blight": ["Copper fungicide", "chlorothalonil", "remove infected tissue", "destroy debris"],
    "powdery mildew": ["Sulfur fungicide", "neem oil", "baking soda spray", "improve airflow"],
    "downy mildew": ["Copper fungicide", "improve air circulation", "reduce humidity", "resistant varieties"],
    "blossom end rot": ["Calcium spray", "consistent watering", "mulching", "soil pH adjustment"],
    "verticillium wilt": ["Remove infected plants", "soil solarization", "resistant varieties", "crop rotation"],
    "bacterial spot": ["Copper bactericide", "remove infected leaves", "avoid overhead watering", "clean tools"],
    "anthracnose": ["Copper fungicide", "mancozeb", "remove infected tissue", "improve drainage"],
}

SAFE_DIRS = [
    Path.home() / ".openclaw" / "workspace",
    Path("/tmp"),
    Path.home(),
]

BLOCKED_PATHS = ["/etc/", "/usr/", "/var/", "/sys/", "/boot/", "/root/.bashrc", "/root/.ssh"]
BLOCKED_DOTFILES = [".bashrc", ".bash_profile", ".profile", ".ssh", ".gnupg", ".aws"]

VALID_SEVERITIES = ["low", "moderate", "high", "critical"]
VALID_TYPES = ["pest", "disease"]


def load_db():
    if DB_PATH.exists():
        with open(DB_PATH) as f:
            return json.load(f)
    return {"issues": {}}


def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def cmd_add(args):
    db = load_db()
    issue_id = str(uuid.uuid4())[:8]
    
    if args.type not in VALID_TYPES:
        print(f"Error: type must be one of {VALID_TYPES}", file=sys.stderr)
        sys.exit(1)
    
    severity = args.severity if args.severity else "low"
    if severity not in VALID_SEVERITIES:
        print(f"Error: severity must be one of {VALID_SEVERITIES}", file=sys.stderr)
        sys.exit(1)
    
    plants = [p.strip() for p in args.plants.split(",")] if args.plants else []
    
    issue = {
        "id": issue_id,
        "type": args.type,
        "name": args.name,
        "plants": plants,
        "severity": severity,
        "status": "active",
        "date_added": datetime.now().isoformat(),
        "notes": args.notes if args.notes else "",
        "treatments": [],
    }
    
    db["issues"][issue_id] = issue
    save_db(db)
    print(f"Added {args.type}: {args.name} (ID: {issue_id})")
    return issue_id


def cmd_treat(args):
    db = load_db()
    issue_id = args.id
    
    if issue_id not in db["issues"]:
        print(f"Error: Issue ID '{issue_id}' not found", file=sys.stderr)
        sys.exit(1)
    
    treatment = {
        "treatment_id": str(uuid.uuid4())[:8],
        "method": args.method,
        "product": args.product if args.product else "",
        "date": datetime.now().isoformat(),
        "status": args.status if args.status else "pending",
        "notes": args.notes if args.notes else "",
    }
    
    db["issues"][issue_id]["treatments"].append(treatment)
    
    if args.status == "effective":
        db["issues"][issue_id]["status"] = "resolved"
    
    save_db(db)
    print(f"Recorded treatment for issue {issue_id}: {args.method} with {args.product}")


def cmd_list(args):
    db = load_db()
    if not db["issues"]:
        print("No issues tracked yet.")
        return
    
    for issue_id, issue in db["issues"].items():
        plants_str = ", ".join(issue["plants"])
        treatments_count = len(issue["treatments"])
        print(f"[{issue_id}] {issue['type'].upper()}: {issue['name']} | Plants: {plants_str} | Severity: {issue['severity']} | Status: {issue['status']} | Treatments: {treatments_count}")


def cmd_show(args):
    db = load_db()
    issue_id = args.id
    
    if issue_id not in db["issues"]:
        print(f"Error: Issue ID '{issue_id}' not found", file=sys.stderr)
        sys.exit(1)
    
    issue = db["issues"][issue_id]
    print(json.dumps(issue, indent=2))


def cmd_search(args):
    db = load_db()
    query = args.query.lower()
    results = []
    
    for issue_id, issue in db["issues"].items():
        if (query in issue["name"].lower() or
                query in issue["type"].lower() or
                any(query in p.lower() for p in issue["plants"])):
            results.append(issue)
    
    if not results:
        print("No matching issues found.")
        return
    
    for issue in results:
        print(f"[{issue['id']}] {issue['type'].upper()}: {issue['name']} | Plants: {', '.join(issue['plants'])} | Severity: {issue['severity']}")


def cmd_recommend(args):
    problem = args.problem.lower().strip()
    
    for key, recs in RECOMMENDATIONS.items():
        if key in problem or problem in key:
            print(f"Recommendations for '{args.problem}':")
            for rec in recs:
                print(f"  - {rec}")
            return
    
    print(f"No specific recommendations found for '{args.problem}'. General advice: Monitor closely, consult local extension service.")


def validate_export_path(path_str):
    path = Path(path_str).expanduser().resolve()
    
    path_str_lower = str(path)
    for blocked in BLOCKED_PATHS:
        if path_str_lower.startswith(blocked):
            return False, f"Blocked system path: {blocked}"
    
    for dotfile in BLOCKED_DOTFILES:
        if dotfile in path.parts or path.name == dotfile:
            return False, f"Blocked sensitive dotfile: {dotfile}"
    
    for safe_dir in SAFE_DIRS:
        safe_resolved = safe_dir.expanduser().resolve()
        try:
            path.relative_to(safe_resolved)
            return True, "OK"
        except ValueError:
            continue
    
    return False, f"Path '{path}' is not in an allowed directory. Allowed: ~/.openclaw/workspace/, /tmp/, home directory"


def cmd_export(args):
    output_path = args.output_file
    
    valid, reason = validate_export_path(output_path)
    if not valid:
        print(f"Error: Export blocked - {reason}", file=sys.stderr)
        sys.exit(1)
    
    db = load_db()
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "total_issues": len(db["issues"]),
        "issues": list(db["issues"].values()),
    }
    
    out_path = Path(output_path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w") as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Exported {len(db['issues'])} issues to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Pest & Disease Tracker")
    subparsers = parser.add_subparsers(dest="command")
    
    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--type", required=True)
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--plants", default="")
    add_parser.add_argument("--severity", default="low")
    add_parser.add_argument("--notes", default="")
    
    # treat
    treat_parser = subparsers.add_parser("treat")
    treat_parser.add_argument("id")
    treat_parser.add_argument("--method", required=True)
    treat_parser.add_argument("--product", default="")
    treat_parser.add_argument("--status", default="pending")
    treat_parser.add_argument("--notes", default="")
    
    # list
    subparsers.add_parser("list")
    
    # show
    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("id")
    
    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    
    # recommend
    rec_parser = subparsers.add_parser("recommend")
    rec_parser.add_argument("problem")
    
    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("output_file")
    
    args = parser.parse_args()
    
    if args.command == "add":
        cmd_add(args)
    elif args.command == "treat":
        cmd_treat(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "recommend":
        cmd_recommend(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
PEST_TRACKER_EOF

RUN chmod +x /usr/local/bin/pest_tracker.py

WORKDIR /root/.openclaw/workspace